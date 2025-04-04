from django import forms
from .models import Project, Task, Skill

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']

class TaskForm(forms.ModelForm):
    assigned_to = forms.ModelMultipleChoiceField(
        queryset=None,  # Se establece en __init__
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Asignado a"
    )
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Habilidades Requeridas"
    )

    class Meta:
        model = Task
        fields = ['project', 'title', 'description', 'status', 'priority', 'assigned_to', 'required_skills', 'deadline']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.all()  # Establecer queryset aquí