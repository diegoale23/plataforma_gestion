# market_analysis/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import JobOffer, Skill, MarketTrend
from django.db.models import Count
import json # Para los gráficos

@login_required
def market_dashboard_view(request):
    # 1. Obtener datos para gráficos
    # Habilidades más demandadas (Top 10)
    top_skills = Skill.objects.annotate(
        num_offers=Count('job_offers')
    ).order_by('-num_offers')[:10]

    skills_labels = [skill.name for skill in top_skills]
    skills_data = [skill.num_offers for skill in top_skills]

    # Número de ofertas por fuente
    offers_by_source = JobOffer.objects.values('source__name').annotate(
        count=Count('id')
    ).order_by('-count')

    source_labels = [item['source__name'] or 'Desconocida' for item in offers_by_source]
    source_data = [item['count'] for item in offers_by_source]

    # Tendencias históricas (si tienes el modelo MarketTrend poblado)
    trends = MarketTrend.objects.order_by('analysis_date') # Obtener datos de tendencias

    context = {
        'skills_labels_json': json.dumps(skills_labels),
        'skills_data_json': json.dumps(skills_data),
        'source_labels_json': json.dumps(source_labels),
        'source_data_json': json.dumps(source_data),
        'trends': trends, # Pasar datos de tendencias a la plantilla
        'total_offers': JobOffer.objects.count(),
    }
    return render(request, 'market_analysis/dashboard.html', context) # Crear plantilla