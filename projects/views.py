# projects/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Project, Task
from .forms import ProjectForm, TaskForm

# Vistas para Project
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        user = self.request.user
        if user.profile.role and user.profile.role.name == 'Administrador':
            return Project.objects.all()
        elif user.profile.role and user.profile.role.name == 'Gestor de Proyectos':
            return Project.objects.filter(manager=user)
        else:  # Colaborador
            return Project.objects.filter(tasks__assigned_to=user).distinct()

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project_list')

    def test_func(self):
        role = self.request.user.profile.role
        return role and role.permissions.filter(codename='can_manage_projects').exists()

    def form_valid(self, form):
        form.instance.manager = self.request.user
        return super().form_valid(form)

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project_list')

    def test_func(self):
        role = self.request.user.profile.role
        return role and role.permissions.filter(codename='can_manage_projects').exists()

class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('project_list')

    def test_func(self):
        role = self.request.user.profile.role
        return role and role.permissions.filter(codename='can_manage_projects').exists()

# Vistas para Task
class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'projects/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        user = self.request.user
        if user.profile.role and user.profile.role.name == 'Administrador':
            return Task.objects.all()
        elif user.profile.role and user.profile.role.name == 'Gestor de Proyectos':
            return Task.objects.filter(project__manager=user)
        return Task.objects.filter(assigned_to=user)

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'projects/task_detail.html'
    context_object_name = 'task'

class TaskCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'
    success_url = reverse_lazy('task_list')

    def test_func(self):
        role = self.request.user.profile.role
        return role and role.permissions.filter(codename='can_manage_projects').exists()

    def form_valid(self, form):
        if 'project_id' in self.kwargs:
            form.instance.project = Project.objects.get(id=self.kwargs['project_id'])
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.profile.role.name != 'Administrador':
            kwargs['queryset'] = Project.objects.filter(manager=self.request.user)
        return kwargs

class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'
    success_url = reverse_lazy('task_list')

    def test_func(self):
        role = self.request.user.profile.role
        return role and role.permissions.filter(codename='can_manage_projects').exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.profile.role.name != 'Administrador':
            kwargs['queryset'] = Project.objects.filter(manager=self.request.user)
        return kwargs

class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Task
    template_name = 'projects/task_confirm_delete.html'
    success_url = reverse_lazy('task_list')

    def test_func(self):
        role = self.request.user.profile.role
        return role and role.permissions.filter(codename='can_manage_projects').exists()