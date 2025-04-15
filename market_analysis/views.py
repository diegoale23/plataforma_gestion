from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q  # Añadimos Count
from market_analysis.models import JobOffer, JobSource
from users.models import Skill
from .scraping.tecnoempleo_scraper import TecnoempleoScraper
from .scraping.linkedin_scraper import LinkedinScraper
from .scraping.infojobs_scraper import InfojobsScraper
from ai_engine.logic.predictions import get_future_skills_predictions
from django.conf import settings
from django.http import HttpResponse
import matplotlib.pyplot as plt
import io

@login_required
def market_dashboard(request):
    if request.GET.get('refresh', False):
        try:
            infojobs_scraper = InfojobsScraper()
            infojobs_offers = infojobs_scraper.run(query="desarrollador", location="España", max_offers=50)
            messages.success(request, f"Se scrapearon {len(infojobs_offers)} ofertas de InfoJobs.")
        except Exception as e:
            messages.error(request, f"Error al scrapear InfoJobs: {e}")

        try:
            tecnoempleo_scraper = TecnoempleoScraper()
            tecnoempleo_offers = tecnoempleo_scraper.run(query="desarrollador", location="Madrid", max_offers=50)
            messages.success(request, f"Se scrapearon {len(tecnoempleo_offers)} ofertas de Tecnoempleo.")
        except Exception as e:
            messages.error(request, f"Error al scrapear Tecnoempleo: {e}")

        linkedin_username = getattr(settings, 'LINKEDIN_USERNAME', None)
        linkedin_password = getattr(settings, 'LINKEDIN_PASSWORD', None)
        if linkedin_username and linkedin_password:
            try:
                linkedin_scraper = LinkedinScraper()
                linkedin_offers = linkedin_scraper.run(query="desarrollador", location="España", max_offers=50)
                messages.success(request, f"Se scrapearon {len(linkedin_offers)} ofertas de LinkedIn.")
            except Exception as e:
                messages.error(request, f"Error al scrapear LinkedIn: {e}")
        else:
            messages.warning(request, "Credenciales de LinkedIn no configuradas en settings.py")

    # Estadísticas generales
    total_offers = JobOffer.objects.count()
    active_offers = JobOffer.objects.filter(is_active=True).count()
    last_scraped = JobSource.objects.filter(last_scraped__isnull=False).order_by('-last_scraped').first()
    last_scraped_date = last_scraped.last_scraped if last_scraped else None

    # Habilidades más demandadas (general)
    top_skills = (
        Skill.objects.filter(job_offers__is_active=True)
        .annotate(num_offers=Count('job_offers'))
        .order_by('-num_offers')[:10]
    )

    # Habilidades por región
    skills_by_region = (
        JobOffer.objects.filter(is_active=True)
        .values('location')
        .annotate(
            skill_count=Count('required_skills'),
            skill_names=Count('required_skills__name')
        )
        .filter(skill_count__gt=0)
        .order_by('-skill_count')[:5]
    )
    for region in skills_by_region:
        region['skills'] = (
            JobOffer.objects.filter(is_active=True, location=region['location'])
            .values('required_skills__name')
            .annotate(count=Count('required_skills'))
            .order_by('-count')[:5]
        )

    # Habilidades por fuente
    skills_by_source = (
        JobOffer.objects.filter(is_active=True)
        .values('source__name')
        .annotate(
            skill_count=Count('required_skills'),
            skill_names=Count('required_skills__name')
        )
        .filter(skill_count__gt=0)
        .order_by('-skill_count')
    )
    for source in skills_by_source:
        source['skills'] = (
            JobOffer.objects.filter(is_active=True, source__name=source['source__name'])
            .values('required_skills__name')
            .annotate(count=Count('required_skills'))
            .order_by('-count')[:5]
        )

    # Applicants count por habilidad
    applicants_by_skill = (
        Skill.objects.filter(job_offers__is_active=True, job_offers__applicants_count__isnull=False)
        .annotate(
            total_applicants=Count('job_offers__applicants_count'),
            avg_applicants=Count('job_offers__applicants_count') / Count('job_offers')
        )
        .order_by('-total_applicants')[:10]
    )

    # Tendencias de habilidades
    skill_trends = get_future_skills_predictions()
    sorted_trends = dict(sorted(skill_trends.items(), key=lambda item: item[1]['predicted_score'], reverse=True))

    context = {
        'total_offers': total_offers,
        'active_offers': active_offers,
        'last_scraped': last_scraped_date,
        'top_skills': top_skills,
        'skills_by_region': skills_by_region,
        'skills_by_source': skills_by_source,
        'applicants_by_skill': applicants_by_skill,
        'skill_trends': sorted_trends,
    }
    return render(request, 'market_analysis/dashboard.html', context)

@login_required
def job_offer_list(request):
    query = request.GET.get('query', '').strip()
    offers = JobOffer.objects.filter(is_active=True)

    if query:
        offers = offers.filter(
            Q(title__icontains=query) |
            Q(company__icontains=query) |
            Q(location__icontains=query) |
            Q(publication_date__icontains=query)
        )

    offers = offers.order_by('-publication_date')
    context = {
        'offers': offers,
        'query': query,
    }
    return render(request, 'market_analysis/job_offer_list.html', context)

@login_required
def export_skills_report(request):
    top_skills = (
        Skill.objects.filter(job_offers__is_active=True)
        .annotate(num_offers=Count('job_offers'))
        .order_by('-num_offers')[:10]
    )
    skills = [skill.name for skill in top_skills]
    counts = [skill.num_offers for skill in top_skills]
    plt.figure(figsize=(10, 6))
    plt.bar(skills, counts, color='teal')
    plt.title('Habilidades Más Demandadas')
    plt.xlabel('Habilidades')
    plt.ylabel('Número de Ofertas')
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    response = HttpResponse(buf, content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="skills_report.png"'
    return response