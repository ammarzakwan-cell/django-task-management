from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_index, name="task_index"),
    path('task_create', views.task_create, name='task_create'),
    path('task_update/<int:task_id>/', views.task_update, name='task_update'),
    path('task_delete/<int:task_id>/', views.task_delete, name='task_delete'),
    path('task_unlock/', views.unlock_task, name='unlock_task'),
    path('dt_task', views.DataTableTaskList.as_view()),
]