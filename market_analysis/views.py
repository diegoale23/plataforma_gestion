# market_analysis/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from market_analysis.models import JobOffer, JobSource
from users.models import Skill
from django.db.models import Count  # Cambiamos a una importación específica
from ai_engine.logic.predictions import get_future_skills_predictions

@login_required
def market_dashboard(request):
    # Total de ofertas
    total_offers = JobOffer.objects.count()
    active_offers = JobOffer.objects.filter(is_active=True).count()
    
    # Última actualización (desde JobSource)
    tecnoempleo_source = JobSource.objects.filter(name="Tecnoempleo").first()
    last_scraped = tecnoempleo_source.last_scraped if tecnoempleo_source and tecnoempleo_source.last_scraped else None

    # Habilidades más demandadas
    top_skills = (
        Skill.objects.filter(job_offers__is_active=True)
        .annotate(num_offers=Count('job_offers'))
        .order_by('-num_offers')[:10]
    )

    # Tendencias de habilidades desde ai_engine
    skill_trends = get_future_skills_predictions()

    context = {
        'total_offers': total_offers,
        'active_offers': active_offers,
        'last_scraped': last_scraped,
        'top_skills': top_skills,
        'skill_trends': skill_trends,
    }
    return render(request, 'market_analysis/dashboard.html', context)

@login_required
def job_offer_list(request):
    offers = JobOffer.objects.filter(is_active=True).order_by('-publication_date')
    return render(request, 'market_analysis/job_offer_list.html', {'offers': offers})