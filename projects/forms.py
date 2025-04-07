# projects/forms.py
from django import forms
from .models import Project, Task
from users.models import Skill

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'name': 'Nombre del Proyecto',
            'description': 'Descripción',
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['project', 'title', 'description', 'status', 'priority', 'assigned_to', 'required_skills', 'deadline']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'required_skills': forms.CheckboxSelectMultiple(),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'project': 'Proyecto',
            'title': 'Título de la Tarea',
            'description': 'Descripción',
            'status': 'Estado',
            'priority': 'Prioridad',
            'assigned_to': 'Asignado a',
            'required_skills': 'Habilidades Requeridas',
            'deadline': 'Fecha Límite',
        }