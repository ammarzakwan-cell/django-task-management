from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Task, Locking 
from modules.media.models import Media
from components.storage_component import StorageComponent
from components.image_component import ImageComponent
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.utils.timezone import make_aware

# Create your views here.
@login_required(login_url="/login")
def task_index(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    return render(request, 'task_index.html', {'user_groups': user_groups})

@login_required(login_url="/login")
@permission_required("task.add_task", login_url="/login", raise_exception=True)
def task_create(request):
    if request.method == 'POST':
            
        # Save the Task instance
        task = Task.objects.create(
            title=request.POST.get('title'),
            source=request.POST.get('source'),
            content=request.POST.get('content'),
            published=make_aware(datetime.strptime(request.POST.get('date'), "%Y-%m-%d")) if request.POST.get('date') else None
        )


        # Upload the file and associate it with the Task
        # Check if a new file is uploaded
        if 'file' in request.FILES:
            file = request.FILES['file']
            storage = StorageComponent()
            storage.disk('s3').upload_file(file, model_instance=task, collection_name="data_entry_task")

        return redirect('task_index')  # Redirect to a task list page
    
    return render(request, 'task_create.html')


@login_required(login_url="/login")
def task_update(request, task_id):

    # Get the task instance to update
    task = get_object_or_404(Task, id=task_id)

    locking = Locking.objects.filter(task_id=task.id).first()

    if locking and locking.is_locked and locking.locked_by != request.user:
        messages.info(request, "This post is currently being edited by another user.")
        return redirect('task_index')
        

    Locking.lock_task(request.user, task)

    storage = StorageComponent().disk('s3')

    existing_file = Media.objects.filter(
        content_type=ContentType.objects.get_for_model(Task),
        object_id=task.id
    ).first()

    if request.method == 'POST':

        # Save updated Task instance
        task.title = request.POST.get('title')
        task.source = request.POST.get('source')
        task.content = request.POST.get('content')
        task.published = make_aware(datetime.strptime(request.POST.get('date'), "%Y-%m-%d"))
        task.save()

        # Check if a new file is uploaded
        if 'file' in request.FILES:
            file = request.FILES['file']

            # Delete the old file from S3
            if existing_file and storage.is_exist(existing_file.file_path):
                storage.remove(existing_file.file_path)

            storage.upload_file(
                file, model_instance=task, collection_name="data_entry_task"
            )

        return redirect('task_index')  # Redirect to a task list page
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


    


@login_required(login_url="/login")
@csrf_exempt
def unlock_task(request):
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        if task_id:
            Locking.objects.filter(task_id=task_id).delete()
            return JsonResponse({"status": "success", "message": "Task unlocked."})
        return JsonResponse({"status": "error", "message": "Task ID not provided."}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)



class DataTableTaskList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        # Retrieve request parameters
        search_value = request.GET.get('search[value]', '')
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        order_column_index = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        # Define columns mapping (DataTables column names)
        columns = ['title', 'source', 'content']  # Adjust to match your model fields

        # Base QuerySet
        queryset = Task.objects.all()

        # Apply search filter
        if search_value:
            queryset = queryset.filter(
                Q(title__icontains=search_value) | 
                Q(source__icontains=search_value)
            )

        # Calculate the filtered count before slicing
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

        # Prepare response data
        data = [
            {
                'title': obj.title,
                'source': obj.source,
                'content': obj.content,
                'id': obj.id,
                'edit_url': '/task/task_update/' + str(obj.id),
            }
            for obj in queryset
        ]

        # Return JSON response
        return Response({
            'draw': int(request.GET.get('draw', 1)),  # Pass-through value from DataTables
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })
