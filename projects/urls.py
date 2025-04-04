from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    # path('<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'), # Si las creas
    # path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'), # Si las creas
    # Aquí puedes agregar URLs para las tareas (Task) si las creas
    # path('tasks/', views.TaskListView.as_view(), name='task_list'),
    # path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    # path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
]