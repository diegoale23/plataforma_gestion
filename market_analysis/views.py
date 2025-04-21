from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from market_analysis.models import JobOffer, JobSource, MarketTrend
from users.models import Skill
from .scraping.tecnoempleo_scraper import TecnoempleoScraper
from .scraping.infojobs_scraper import InfojobsScraper
from .scraping.linkedin_scraper import LinkedinScraper
from ai_engine.logic.predictions import get_future_skills_predictions
from django.conf import settings
import matplotlib.pyplot as plt
import io
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def market_dashboard(request):
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

@login_required
def autocomplete_skills(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)

    # Buscar habilidades en Skill
    skill_matches = Skill.objects.filter(name__icontains=query).values_list('name', flat=True)

    # Buscar en tendencias de habilidades
    trend_matches = []
    skill_trends = get_future_skills_predictions()
    for skill in skill_trends.keys():
        if query.lower() in skill.lower():
            trend_matches.append(skill)

    # Combinar y eliminar duplicados
    results = list(set(list(skill_matches) + trend_matches))[:10]
    return JsonResponse(results, safe=False)

@login_required
def run_scraping(request):
    logger.info("Iniciando run_scraping")
    if request.method != 'POST':
        logger.error("Método no permitido: %s", request.method)
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        # Loguear el contenido crudo de request.body para depuración
        logger.debug("Contenido de request.body: %s", request.body)
        
        # Manejar el caso de cuerpo vacío
        if not request.body:
            logger.error("Cuerpo de la solicitud vacío")
            return JsonResponse({'error': 'Cuerpo de la solicitud vacío'}, status=400)

        # Intentar parsear como JSON primero
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            # Si falla, intentar procesar como form-urlencoded
            logger.warning("No es JSON, intentando parsear como form-urlencoded")
            try:
                # Parsear datos de formulario (application/x-www-form-urlencoded)
                form_data = request.POST
                keywords_str = form_data.get('keywords', '[]')
                try:
                    keywords = json.loads(keywords_str) if keywords_str else []
                except json.JSONDecodeError:
                    logger.error("El campo 'keywords' no es un JSON válido: %s", keywords_str)
                    return JsonResponse({'error': 'El campo keywords debe ser un JSON válido'}, status=400)
                data = {
                    'keywords': keywords,
                    'location': form_data.get('location', 'España'),
                    'max_offers': int(form_data.get('max_offers', 30))
                }
            except Exception as e:
                logger.error("Error al parsear datos de formulario: %s", str(e))
                return JsonResponse({'error': f'Formato de datos inválido: {str(e)}'}, status=400)

        # Validar los datos recibidos
        keywords = data.get('keywords', [])
        location = data.get('location', 'España')
        max_offers = int(data.get('max_offers', 30))

        if not keywords:
            logger.error("No se proporcionaron palabras clave")
            return JsonResponse({'error': 'Se requiere al menos una palabra clave'}, status=400)

        logger.info("Parámetros recibidos: keywords=%s, location=%s, max_offers=%s", keywords, location, max_offers)

        # Ejecutar scrapers
        total_offers = 0
        errors = []

        # Tecnoempleo
        try:
            tecnoempleo_scraper = TecnoempleoScraper()
            for keyword in keywords:
                offers = tecnoempleo_scraper.run(query=keyword, location=location, max_offers=max_offers)
                total_offers += len(offers)
                logger.info("Tecnoempleo: %d ofertas obtenidas para '%s'", len(offers), keyword)
        except Exception as e:
            errors.append(f"Tecnoempleo: {str(e)}")
            logger.error("Error en TecnoempleoScraper: %s", str(e))

        # InfoJobs
        try:
            infojobs_scraper = InfojobsScraper()
            for keyword in keywords:
                offers = infojobs_scraper.run(query=keyword, location=location, max_offers=max_offers)
                total_offers += len(offers)
                logger.info("InfoJobs: %d ofertas obtenidas para '%s'", len(offers), keyword)
        except Exception as e:
            errors.append(f"InfoJobs: {str(e)}")
            logger.error("Error en InfojobsScraper: %s", str(e))

        # LinkedIn
        linkedin_username = getattr(settings, 'LINKEDIN_USERNAME', None)
        linkedin_password = getattr(settings, 'LINKEDIN_PASSWORD', None)
        if linkedin_username and linkedin_password:
            try:
                linkedin_scraper = LinkedinScraper()
                for keyword in keywords:
                    offers = linkedin_scraper.run(query=keyword, location=location, max_offers=10)
                    total_offers += len(offers)
                    logger.info("LinkedIn: %d ofertas obtenidas para '%s'", len(offers), keyword)
            except Exception as e:
                errors.append(f"LinkedIn: {str(e)}")
                logger.error("Error en LinkedinScraper: %s", str(e))
        else:
            errors.append("LinkedIn: Credenciales no configuradas")
            logger.warning("Credenciales de LinkedIn no configuradas")

        message = f"Se procesaron {total_offers} ofertas exitosamente."
        if errors:
            message += f" Advertencias: {'; '.join(errors)}"
        logger.info("Resultado: %s", message)
        return JsonResponse({'message': message})

    except Exception as e:
        logger.error("Error crítico en run_scraping: %s", str(e), exc_info=True)
        return JsonResponse({'error': f'Error al procesar la solicitud: {str(e)}'}, status=500)