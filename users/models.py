# users/models.py
from django.db import models
from django.conf import settings # Mejor práctica para referenciar al User model
from django.db.models.signals import post_save
from django.dispatch import receiver
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
    """Define los roles dentro de la plataforma."""
    name = models.CharField(
        _("Nombre del Rol"),
        max_length=50,
        unique=True,
        help_text=_("Ej: Administrador, Gestor de Proyectos, Colaborador")
    )

    class Meta:
        verbose_name = _("Rol")
        verbose_name_plural = _("Roles")

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    """Extiende el modelo User de Django para añadir rol y habilidades."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_("Usuario")
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Permitir usuarios sin rol asignado inicialmente
        verbose_name=_("Rol"),
        help_text=_("Rol del usuario en la plataforma.")
    )
    skills = models.ManyToManyField(
        Skill,
        blank=True, # Un usuario puede no tener habilidades registradas
        related_name='user_profiles',
        verbose_name=_("Habilidades del Usuario")
    )
    bio = models.TextField(_("Biografía Corta"), blank=True, null=True)
    # Otros campos que puedas necesitar: teléfono, foto de perfil, etc.

    class Meta:
        verbose_name = _("Perfil de Usuario")
        verbose_name_plural = _("Perfiles de Usuario")

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