# users/management/commands/setup_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from users.models import Role

class Command(BaseCommand):
    help = 'Configura roles y permisos iniciales'

    def handle(self, *args, **kwargs):
        # Obtener el ContentType para el modelo Role, ya que los permisos están asociados a él
        content_type = ContentType.objects.get_for_model(Role)

        # Definir los permisos personalizados que deberían existir
        permissions_data = [
            ("can_manage_users", "Puede gestionar usuarios"),
            ("can_manage_projects", "Puede gestionar proyectos"),
            ("can_complete_tasks", "Puede completar tareas"),
        ]

        # Asegurarse de que los permisos existan en la base de datos
        for codename, name in permissions_data:
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )

        # Definir roles y sus permisos asociados
        roles = {
            'Administrador': ['can_manage_users', 'can_manage_projects', 'can_complete_tasks'],
            'Gestor de Proyectos': ['can_manage_projects', 'can_complete_tasks'],
            'Colaborador': ['can_complete_tasks'],
        }

        # Crear o actualizar roles y asignar permisos
        for role_name, perm_codenames in roles.items():
            role, created = Role.objects.get_or_create(name=role_name)
            for perm_codename in perm_codenames:
                perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                role.permissions.add(perm)
            role.save()
            action = "creado" if created else "actualizado"
            self.stdout.write(self.style.SUCCESS(f'Rol {role_name} {action} correctamente.'))