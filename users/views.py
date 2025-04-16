# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .forms import SignUpForm
from .models import Role, UserProfile
from ai_engine.logic.recommendations import get_task_recommendations

# Funciones de verificación de roles
def is_admin(user):
    return user.is_authenticated and user.profile.role and user.profile.role.name == 'Administrador'

def is_manager(user):
    return user.is_authenticated and user.profile.role and user.profile.role.name == 'Gestor de Proyectos'

# Registro
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                default_role = Role.objects.get(name='Colaborador')
                user.profile.role = default_role
                user.profile.save()
            except Role.DoesNotExist:
                pass
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

# Dashboard dinámico según rol
@login_required
def user_dashboard(request):
    user_role = request.user.profile.role.name if request.user.profile.role else 'Colaborador'
    recommendations = get_task_recommendations(request.user) if user_role == 'Colaborador' else []
    context = {
        'user_role': user_role,
        'recommendations': recommendations,
    }
    return render(request, 'users/dashboard.html', context)

# Gestión de usuarios (solo para Administradores)
@login_required
@user_passes_test(is_admin)
def manage_users_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        if action == 'delete' and user_id:
            return redirect('confirm_delete_user', user_id=user_id)
        elif action == 'update_role' and user_id:
            user = User.objects.get(id=user_id)
            new_role_id = request.POST.get('new_role')
            new_role = Role.objects.get(id=new_role_id)
            user.profile.role = new_role
            user.profile.save()

    users = User.objects.all()
    roles = Role.objects.all()
    return render(request, 'users/manage_users.html', {'users': users, 'roles': roles})

# Confirmación de eliminación de usuario
@login_required
@user_passes_test(is_admin)
def confirm_delete_user(request, user_id):
    user_to_delete = User.objects.get(id=user_id)
    if request.method == 'POST':
        if request.POST.get('confirm') == 'yes':
            user_to_delete.delete()
        return redirect('manage_users')
    return render(request, 'users/confirm_delete_user.html', {'user_to_delete': user_to_delete})

# Creación de usuario por el Administrador
@login_required
@user_passes_test(is_admin)
def create_user_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Guardar el usuario
            user = form.save(commit=False)
            user.save()

            # Guardar el perfil del usuario
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.skills.set(form.cleaned_data['skills'])  # Asignar habilidades
            profile.bio = form.cleaned_data['bio']
            profile.location = form.cleaned_data['location']
            profile.save()

            return redirect('manage_users')
    else:
        form = SignUpForm()
    return render(request, 'users/create_user.html', {'form': form})