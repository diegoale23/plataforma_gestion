# users/models.py
from django.db import models
from django.conf import settings # Mejor práctica para referenciar al User model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils.translation import gettext_lazy as _ # Para verbose_name en español

class Skill(models.Model):
    """Representa una habilidad técnica o blanda."""
    name = models.CharField(
        _("Nombre de la Habilidad"),
        max_length=100,
        unique=True,
        help_text=_("Ej: Python, Django, Comunicación, Liderazgo")
    )

    class Meta:
        verbose_name = _("Habilidad")
        verbose_name_plural = _("Habilidades")
        ordering = ['name']

    def __str__(self):
        return self.name

class Role(models.Model):
    name = models.CharField(
        _("Nombre del Rol"),
        max_length=50,
        unique=True,
        help_text=_("Ej: Administrador, Gestor de Proyectos, Colaborador")
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        verbose_name=_("Permisos"),
        help_text=_("Permisos asociados al rol")
    )

    class Meta:
        verbose_name = _("Rol")
        verbose_name_plural = _("Roles")

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name='user_profiles')
    bio = models.TextField(_("Biografía Corta"), blank=True, null=True)
    location = models.CharField(_("Ubicación"), max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"
    
class Meta:
    permissions = [
        ("can_manage_users", "Puede gestionar usuarios"),
        ("can_manage_projects", "Puede gestionar proyectos"),
        ("can_complete_tasks", "Puede completar tareas"),
    ]
    
    def __str__(self):
        return f"Perfil de {self.user.username}"

# Señal para crear/actualizar UserProfile automáticamente
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Crea un UserProfile cuando se crea un User, o simplemente guarda
    el perfil existente cuando se actualiza un User.
    """
    if created:
        UserProfile.objects.create(user=instance)
    # Asegura que el perfil se guarde en cada actualización del User también
    # Puede ser útil si añades campos al User que deben reflejarse aquí,
    # aunque generalmente no es estrictamente necesario solo para guardar.
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
         # Caso raro donde el User existe pero el profile no fue creado (ej. datos importados)
         UserProfile.objects.create(user=instance)