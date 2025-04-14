# market_analysis/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from market_analysis.models import JobOffer, JobSource
from users.models import Skill
from django.db.models import Count
from .scraping.tecnoempleo_scraper import TecnoempleoScraper
from .scraping.linkedin_scraper import LinkedinScraper
from .scraping.infojobs_scraper import InfojobsScraper
from ai_engine.logic.predictions import get_future_skills_predictions
from django.conf import settings

@login_required
def market_dashboard(request):
    # Si se solicita actualizar los datos
    if request.GET.get('refresh', False):
        # Scraper de InfoJobs
        infojobs_scraper = InfojobsScraper()
        infojobs_scraper.run(query="desarrollador", location="España", max_offers=50)
        
        # Scraper de Tecnoempleo
        tecnoempleo_scraper = TecnoempleoScraper()
        tecnoempleo_scraper.run(query="desarrollador", location="Madrid", max_offers=50)

        # Scraper de LinkedIn
        linkedin_username = getattr(settings, 'LINKEDIN_USERNAME', None)
        linkedin_password = getattr(settings, 'LINKEDIN_PASSWORD', None)

        if linkedin_username and linkedin_password:
            linkedin_scraper = LinkedinScraper()
            linkedin_scraper.run(
                query="desarrollador",
                location="España",
                max_offers=50
            )
        else:
            print("Credenciales de LinkedIn no configuradas en settings.py")

    # Estadísticas del dashboard
    total_offers = JobOffer.objects.count()
    active_offers = JobOffer.objects.filter(is_active=True).count()

    # Última actualización
    last_scraped = JobSource.objects.filter(last_scraped__isnull=False).order_by('-last_scraped').first()
    last_scraped_date = last_scraped.last_scraped if last_scraped else None

    # Habilidades más demandadas
    top_skills = (
        Skill.objects.filter(job_offers__is_active=True)
        .annotate(num_offers=Count('job_offers'))
        .order_by('-num_offers')[:10]
    )

    # Tendencias de habilidades
    skill_trends = get_future_skills_predictions()
    sorted_trends = dict(sorted(skill_trends.items(), key=lambda item: item[1]['predicted_score'], reverse=True))

    context = {
        'total_offers': total_offers,
        'active_offers': active_offers,
        'last_scraped': last_scraped_date,
        'top_skills': top_skills,
        'skill_trends': sorted_trends,
    }
    return render(request, 'market_analysis/dashboard.html', context)

@login_required
def job_offer_list(request):
    offers = JobOffer.objects.filter(is_active=True).order_by('-publication_date')
    return render(request, 'market_analysis/job_offer_list.html', {'offers': offers})