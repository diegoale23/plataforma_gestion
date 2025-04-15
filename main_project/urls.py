# main_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
    path('signup/', user_views.signup_view, name='signup'),
    path('users/', include('users.urls')),
    path('projects/', include('projects.urls')),
    path('market/', include('market_analysis.urls')),  # Incluye todas las URLs de market_analysis
    path('ai/', include('ai_engine.urls')),
    path('dashboard/', user_views.user_dashboard, name='dashboard'),
    path('', auth_views.LoginView.as_view(template_name='registration/login.html'), name='home'),
]