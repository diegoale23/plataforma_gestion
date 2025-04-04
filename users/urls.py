from django.urls import path
from . import views

urlpatterns = [
    # Aquí puedes agregar URLs específicas para la aplicación 'users'
    path('manage/', views.manage_users_view, name='manage_users'),
    # path('profile/', views.profile_view, name='profile'), # Ejemplo
]