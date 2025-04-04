# projects/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Importar Skill desde la app 'users'
from users.models import Skill

class Project(models.Model):
    """Representa un proyecto gestionado en la plataforma."""
    name = models.CharField(_("Nombre del Proyecto"), max_length=200)
    description = models.TextField(_("Descripción"), blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Si se borra el usuario, el proyecto queda sin gestor
        null=True,
        blank=True, # Puede haber proyectos sin gestor asignado temporalmente
        related_name='managed_projects',
        verbose_name=_("Gestor del Proyecto")
    )
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Última Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Proyecto")
        verbose_name_plural = _("Proyectos")
        ordering = ['name']

    def __str__(self):
        return self.name

class Task(models.Model):
    """Representa una tarea dentro de un proyecto."""

    # Constantes para choices
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pendiente')
        IN_PROGRESS = 'IN_PROGRESS', _('En Progreso')
        COMPLETED = 'COMPLETED', _('Completada')
        CANCELLED = 'CANCELLED', _('Cancelada')

    class Priority(models.IntegerChoices):
        LOW = 1, _('Baja')
        MEDIUM = 2, _('Media')
        HIGH = 3, _('Alta')
        URGENT = 4, _('Urgente')

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE, # Si se borra el proyecto, se borran sus tareas
        related_name='tasks',
        verbose_name=_("Proyecto")
    )
    title = models.CharField(_("Título de la Tarea"), max_length=255)
    description = models.TextField(_("Descripción Detallada"), blank=True)
    status = models.CharField(
        _("Estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True # Indexar para búsquedas rápidas por estado
    )
    priority = models.IntegerField(
        _("Prioridad"),
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    assigned_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_tasks',
        blank=True, # Una tarea puede no estar asignada aún
        verbose_name=_("Asignado a")
    )
    required_skills = models.ManyToManyField(
        Skill,
        blank=True, # Una tarea puede no requerir habilidades específicas
        related_name='required_by_tasks',
        verbose_name=_("Habilidades Requeridas")
    )
    deadline = models.DateField(
        _("Fecha Límite"),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Última Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Tarea")
        verbose_name_plural = _("Tareas")
        ordering = ['deadline', 'priority', 'title'] # Ordenar por fecha límite, luego prioridad, luego título

    def __str__(self):
        return f"{self.title} ({self.project.name})"

    @property
    def is_overdue(self):
        """Devuelve True si la tarea está vencida y no completada/cancelada."""
        if self.deadline and self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return timezone.now().date() > self.deadline
        return False