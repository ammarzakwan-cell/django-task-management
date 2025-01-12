from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_index, name="task_index"),
    path('task_create', views.task_create, name='task_create'),
    path('task_update/<int:task_id>/', views.task_update, name='task_update'),
    path('dt_task', views.DataTableTaskList.as_view()),
]