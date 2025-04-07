# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.manage_users_view, name='manage_users'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('manage/delete/<int:user_id>/', views.confirm_delete_user, name='confirm_delete_user'),
    path('manage/create/', views.create_user_view, name='create_user'),
]