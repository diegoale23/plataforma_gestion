# market_analysis/scraping/infojobs_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from django.utils import timezone
from market_analysis.models import JobOffer, JobSource
from users.models import Skill
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class InfojobsScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="InfoJobs", base_url="https://www.infojobs.net")
        self.headers.update({
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })

    def fetch_offers(self, query="desarrollador", location="España", max_offers=50):
        """
        Obtiene una lista de URLs de ofertas de empleo desde la página de búsqueda de InfoJobs.
        """
        offers = []
        search_url = f"{self.base_url}/jobsearch/search-results/list.xhtml"
        params = {
            'keyword': query,
            'location': location.lower().replace(' ', '-'),
            'sortBy': 'PUBLICATION_DATE',
            'page': 1
        }

        try:
            while len(offers) < max_offers:
                response = requests.get(search_url, headers=self.headers, params=params)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Seleccionar los enlaces de las ofertas
                job_cards = soup.select('a.js_offer_link')
                if not job_cards:
                    logger.info("No se encontraron más ofertas en la página.")
                    break

                for card in job_cards[:max_offers - len(offers)]:
                    offer_url = card.get('href')
                    if offer_url and not offer_url.startswith('http'):
                        offer_url = self.base_url + offer_url
                    offers.append({'url': offer_url})

                # Verificar si hay más páginas
                next_page = soup.select_one('a[title="Siguiente"]')
                if not next_page or len(offers) >= max_offers:
                    break
                params['page'] += 1

        except requests.RequestException as e:
            logger.error(f"Error al obtener lista de ofertas de InfoJobs: {e}")

        return offers[:max_offers]

    def parse_offer_detail(self, url_or_data):
        """
        Extrae los detalles de una oferta específica desde su página.
        """
        url = url_or_data.get('url') if isinstance(url_or_data, dict) else url_or_data
        offer_data = {'url': url}

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extraer título
            title = soup.select_one('h1')
            offer_data['title'] = title.get_text(strip=True) if title else ''

            # Extraer empresa
            company = soup.select_one('a.link[title*="empresa"]')
            offer_data['company'] = company.get_text(strip=True) if company else None

            # Extraer ubicación
            location = soup.select_one('span[data-test="offer-province"]')
            offer_data['location'] = location.get_text(strip=True) if location else None

            # Extraer descripción
            description = soup.select_one('div.description')
            offer_data['description'] = description.get_text(strip=True) if description else ''

            # Extraer rango salarial
            salary = soup.select_one('li[data-test="offer-salary"]')
            offer_data['salary_range'] = salary.get_text(strip=True) if salary else None

            # Extraer fecha de publicación
            date_elem = soup.select_one('li[data-test="offer-publication-date"]')
            if date_elem:
                date_str = date_elem.get_text(strip=True)
                try:
                    # Ajustar formato según InfoJobs (ejemplo: "Publicado el 12/04/2025")
                    if 'Publicado el' in date_str:
                        date_str = date_str.replace('Publicado el', '').strip()
                        offer_data['publication_date'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                    else:
                        offer_data['publication_date'] = None
                except ValueError:
                    offer_data['publication_date'] = None
            else:
                offer_data['publication_date'] = None

            # Extraer número de inscritos
            applicants = soup.select_one('li[data-test="offer-applications"]')
            offer_data['applicants_count'] = int(applicants.get_text(strip=True).split()[0]) if applicants and applicants.get_text(strip=True).split()[0].isdigit() else None

            # Extraer habilidades
            skills_list = soup.select('ul.skills-list li')
            offer_data['skills'] = [skill.get_text(strip=True) for skill in skills_list] if skills_list else []

            # Guardar datos crudos
            offer_data['raw_data'] = {'html': str(soup)}

        except requests.RequestException as e:
            logger.error(f"Error al scrapear detalles de la oferta {url}: {e}")
            return None

        return offer_data

    def run(self, query="desarrollador", location="España", max_offers=50):
        """
        Ejecuta el proceso completo de scraping y guarda las ofertas en la base de datos.
        """
        # Obtener o crear la fuente
        source, _ = JobSource.objects.get_or_create(
            name=self.source_name,
            defaults={'url': self.base_url}
        )

        # Actualizar última fecha de scraping
        source.last_scraped = timezone.now()
        source.save()

        # Obtener URLs de ofertas
        offers_data = self.fetch_offers(query, location, max_offers)
        results = []

        for data in offers_data:
            # Obtener detalles
            offer_details = self.parse_offer_detail(data)
            if not offer_details:
                continue

            try:
                # Crear o actualizar oferta en la base de datos
                offer, created = JobOffer.objects.get_or_create(
                    url=offer_details['url'],
                    defaults={
                        'title': offer_details.get('title', ''),
                        'company': offer_details.get('company'),
                        'location': offer_details.get('location'),
                        'description': offer_details.get('description', ''),
                        'salary_range': offer_details.get('salary_range'),
                        'publication_date': offer_details.get('publication_date'),
                        'source': source,
                        'applicants_count': offer_details.get('applicants_count'),
                        'raw_data': offer_details.get('raw_data'),
                        'is_active': True
                    }
                )

                # Asignar habilidades
                for skill_name in offer_details.get('skills', []):
                    if skill_name:
                        skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
                        offer.required_skills.add(skill)

                results.append(offer)

            except Exception as e:
                logger.error(f"Error al guardar oferta {offer_details.get('url')}: {e}")

        logger.info(f"Scraping de InfoJobs completado: {len(results)} ofertas procesadas.")
        return results