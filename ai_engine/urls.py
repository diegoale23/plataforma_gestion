from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('skill-trends/', views.skill_trends_view, name='skill_trends'),
    # path('other_ai_view/', views.other_ai_view, name='other_ai_view'), # Si necesitas otras vistas
]