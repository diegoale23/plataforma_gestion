# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import SignUpForm # Necesitas crear este formulario
from .models import Role

# Vista simple para el registro (necesita el SignUpForm)
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Asignar rol por defecto (Colaborador)
            try:
                default_role = Role.objects.get(name='Colaborador')
                user.profile.role = default_role
                user.profile.save()
            except Role.DoesNotExist:
                # Manejar el caso en que el rol no exista
                pass
            login(request, user)
            return redirect('dashboard') # Redirigir al dashboard después del registro
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

# Login view (usa la vista integrada de Django o una personalizada)
# Logout view (usa la vista integrada de Django)

# Decoradores para control de roles
def is_admin(user):
    return user.is_authenticated and user.profile.role and user.profile.role.name == 'Administrador'

def is_manager(user):
    return user.is_authenticated and user.profile.role and user.profile.role.name == 'Gestor de Proyectos'

@login_required
@user_passes_test(is_admin) # Solo admins pueden acceder
def manage_users_view(request):
    # Lógica para listar y gestionar usuarios
    pass

@login_required
def user_dashboard(request):
    # Lógica de tu dashboard
    return render(request, 'users/dashboard.html') # Asegúrate de que la plantilla exista