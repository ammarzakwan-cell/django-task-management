from components.image_component import ImageComponent
from components.storage_component import StorageComponent
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from modules.media.models import Media
from modules.task.models import Task, Locking 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# Create your views here.

# Landing page for task, showing list in datatable format
@login_required(login_url="/login")
def task_index(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    return render(request, 'task_index.html', {'user_groups': user_groups})

# Creating task 
@login_required(login_url="/login")
@permission_required("task.add_task", login_url="/login", raise_exception=True)
def task_create(request):
    try:
        if request.method == 'POST':
                
            task = Task.objects.create(
                title=request.POST.get('title'),
                source=request.POST.get('source'),
                content=request.POST.get('content'),
                published=make_aware(datetime.strptime(request.POST.get('date'), "%Y-%m-%d")) if request.POST.get('date') else None
            )

            try:
                if 'file' in request.FILES:
                    file = request.FILES['file']
                    storage = StorageComponent()
                    storage.disk('s3').upload_file(file, model_instance=task, collection_name="data_entry_task")
            except Exception as exception:
                messages.error(request, str(exception))
                return redirect('task_index')

            messages.success(request, "Task created successfully.")
            return redirect('task_index')
        
        return render(request, 'task_create.html')
    except Exception as exception:
        messages.error(request, f"An unexpected error occurred: {str(exception)}")
        return redirect('task_index')

# Updating task
@login_required(login_url="/login")
def task_update(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id)

        locking = Locking.objects.filter(task_id=task.id).first()
        if locking and locking.is_locked and locking.locked_by != request.user:
            messages.warning(request, "This task is currently being edited by another user.")
            return redirect('task_index')

        Locking.lock_task(request.user, task)

        storage = StorageComponent().disk('s3')
        existing_file = Media.objects.filter(
            content_type=ContentType.objects.get_for_model(Task),
            object_id=task.id
        ).first()

        if request.method == 'POST':
            task.title = request.POST.get('title', task.title)
            task.source = request.POST.get('source', task.source)
            task.content = request.POST.get('content', task.content)
            
            try:
                published_date = request.POST.get('date')
                task.published = make_aware(datetime.strptime(published_date, "%Y-%m-%d")) if published_date else task.published
            except ValueError:
                messages.error(request, "Invalid date format.")
                return redirect('task_update', task_id=task_id)

            task.save()

            try:
                if 'file' in request.FILES:
                    file = request.FILES['file']
                    storage.upload_file(file, model_instance=task, collection_name="data_entry_task")
                    if existing_file and storage.is_exist(existing_file.file_path):
                        storage.remove(existing_file.file_path)

                    
            except Exception as exception:
                messages.error(request, str(exception))
                return redirect('task_update', task_id=task_id)

            Locking.objects.filter(task_id=task_id).delete()
            messages.success(request, "Task updated successfully.")
            return redirect('task_index')

        else:
            user_groups = request.user.groups.values_list('name', flat=True)
            image_url = None
            image_to_text = None

            if existing_file:
                image_url = storage.generate_signed_url(existing_file.file_path)
                image_to_text = ImageComponent.image_to_text(image_url=image_url)

            return render(request, 'task_update.html', {
                'task': task,
                'image_url': image_url,
                'image_to_text': image_to_text,
                'existing_file': existing_file,
                'user_groups': user_groups
            })

    except Exception as exception:
        messages.error(request, f"An unexpected error occurred: {str(exception)}")
        return redirect('task_index')
    

# Deleting taks
@permission_required("task.delete_task", login_url="/login", raise_exception=True)
@login_required(login_url="/login")
def task_delete(request, task_id):
    try:
        existing_file = Media.objects.filter(
            content_type=ContentType.objects.get_for_model(Task),
            object_id=task_id
        ).first()

        task = get_object_or_404(Task, id=task_id)
        task.delete()

        storage = StorageComponent().disk('s3')
        if existing_file and storage.is_exist(existing_file.file_path):
            storage.remove(existing_file.file_path)
            existing_file.delete()

        messages.success(request, "Task and associated files deleted successfully.")
        return redirect("task_index")

    except Exception as exception:
        messages.error(request, f"An error occurred: {str(exception)}")
        return redirect("task_index")


# Deleting locking_task object
@login_required(login_url="/login")
@csrf_exempt
def unlock_task(request):
    """
    Javascript asynchronously sends an HTTP POST request once user leave the page. 
    This function is for locking task, when user leave it will delete the locking object 
    so that other users can open the task
    """
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        if task_id:
            Locking.objects.filter(task_id=task_id).delete()
            return JsonResponse({"status": "success", "message": "Task unlocked."})
        return JsonResponse({"status": "error", "message": "Task ID not provided."}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


# Using rest framework API to datatable
class DataTableTaskList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        # Parameter from datatable
        search_value = request.GET.get('search[value]', '')
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        order_column_index = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['title', 'source', 'content']

        queryset = Task.objects.all()

        # Q search filter
        if search_value:
            queryset = queryset.filter(
                Q(title__icontains=search_value) | 
                Q(source__icontains=search_value)
            )

        # Total filtered records
        records_filtered = queryset.count()

        # Apply ordering
        if order_column_index < len(columns):
            column_name = columns[order_column_index]
            if order_dir == 'asc':
                queryset = queryset.order_by(column_name)
            else:
                queryset = queryset.order_by(f"-{column_name}")
        else:
            queryset = queryset.order_by('-id')

        # Apply pagination
        queryset = queryset[start:start + length]

        # Total record count
        records_total = Task.objects.count()

        data = [
            {
                'title': obj.title,
                'source': obj.source,
                'content': obj.content,
                'id': obj.id,
                'edit_url': '/task/task_update/' + str(obj.id),
                'delete_url': '/task/task_delete/' + str(obj.id),
                'is_locked': Locking.objects.filter(task_id=str(obj.id)).exists(),
                'user_groups': request.user.groups.values_list('name', flat=True),
            }
            for obj in queryset
        ]

        # Return JSON
        return Response({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })
