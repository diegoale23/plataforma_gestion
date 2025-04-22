# market_analysis/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.market_dashboard, name='market_dashboard'),
    path('offers/', views.job_offer_list, name='job_offer_list'),
    path('export-skills-report/', views.export_skills_report, name='export_skills_report'),
    path('autocomplete-skills/', views.autocomplete_skills, name='autocomplete_skills'),
    path('run-scraping/', views.run_scraping, name='run_scraping'),
]