# market_analysis/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from market_analysis.models import JobOffer, JobSource
from users.models import Skill
from django.db.models import Count
from .scraping.tecnoempleo_scraper import TecnoempleoScraper
from ai_engine.logic.predictions import get_future_skills_predictions  # Importamos la función

@login_required
def market_dashboard(request):
    if request.GET.get('refresh', False):
        scraper = TecnoempleoScraper()
        scraper.run(query="desarrollador", location="Madrid", max_offers=50)

    total_offers = JobOffer.objects.count()
    active_offers = JobOffer.objects.filter(is_active=True).count()
    tecnoempleo_source = JobSource.objects.filter(name="Tecnoempleo").first()
    last_scraped = tecnoempleo_source.last_scraped if tecnoempleo_source else None
    top_skills = (
        Skill.objects.filter(job_offers__is_active=True)
        .annotate(num_offers=Count('job_offers'))
        .order_by('-num_offers')[:10]
    )
    skill_trends = get_future_skills_predictions()  # Obtenemos las tendencias
    sorted_trends = dict(sorted(skill_trends.items(), key=lambda item: item[1]['predicted_score'], reverse=True))

    context = {
        'total_offers': total_offers,
        'active_offers': active_offers,
        'last_scraped': last_scraped,
        'top_skills': top_skills,
        'skill_trends': sorted_trends,  # Añadimos las tendencias ordenadas
    }
    return render(request, 'market_analysis/dashboard.html', context)

@login_required
def job_offer_list(request):
    offers = JobOffer.objects.filter(is_active=True).order_by('-publication_date')
    return render(request, 'market_analysis/job_offer_list.html', {'offers': offers})