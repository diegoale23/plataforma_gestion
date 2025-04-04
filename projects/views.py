# projects/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Project, Task
from .forms import ProjectForm, TaskForm # Necesitas crear estos formularios

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html' # Necesitas crear esta plantilla
    context_object_name = 'projects'

    def get_queryset(self):
        # Filtrar para mostrar solo proyectos relevantes al usuario (ej: gestionados o donde participa)
        user = self.request.user
        if user.profile.role and user.profile.role.name == 'Administrador':
            return Project.objects.all()
        elif user.profile.role and user.profile.role.name == 'Gestor de Proyectos':
            return Project.objects.filter(manager=user)
        else: # Colaborador
            # Mostrar proyectos donde tiene tareas asignadas
            return Project.objects.filter(tasks__assigned_to=user).distinct()

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html' # Necesitas crear esta plantilla
    context_object_name = 'project'

# Solo Gestores o Admins pueden crear proyectos
class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html' # Necesitas crear esta plantilla
    success_url = reverse_lazy('project_list') # URL a la lista de proyectos

    def test_func(self):
        role = self.request.user.profile.role
        return role and (role.name == 'Administrador' or role.name == 'Gestor de Proyectos')

    def form_valid(self, form):
        form.instance.manager = self.request.user # Asignar manager automáticamente
        return super().form_valid(form)

# Similarmente, crear UpdateView y DeleteView con permisos adecuados
# Crear vistas CRUD para Task (TaskListView, TaskDetailView, TaskCreateView, etc.) con lógica de permisos