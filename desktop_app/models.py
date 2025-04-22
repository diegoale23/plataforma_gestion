# desktop_app/models.py
'''from django.db import models
from django.contrib.auth.models import User

# Tabla: auth_group
class Group(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name

# Tabla: users_skill
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Tabla: users_userprofile
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='desktop_profile'  # Cambiado para evitar conflicto con 'users.UserProfile.user'
    )
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    skills = models.ManyToManyField(Skill, related_name='desktop_user_profiles', blank=True)

    def __str__(self):
        return self.user.username

# Tabla: projects_project
class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='desktop_managed_projects'  # Cambiado para evitar conflicto con 'projects.Project.manager'
    )

    def __str__(self):
        return self.name

# Tabla: projects_task
class Task(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    priority = models.IntegerField()
    deadline = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='desktop_tasks')
    assigned_to = models.ManyToManyField(User, related_name='desktop_tasks', blank=True)

    def __str__(self):
        return self.title'''