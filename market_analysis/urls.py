from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.market_dashboard_view, name='market_dashboard'),
    # path('other_market_view/', views.other_market_view, name='other_market_view'), # Si necesitas otras vistas
]