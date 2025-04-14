# market_analysis/scraping/infojobs_scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import time
from django.utils import timezone
from market_analysis.models import JobOffer, JobSource
from users.models import Skill
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class InfojobsScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="InfoJobs", base_url="https://www.infojobs.net")
        self.headers = {
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Referer': 'https://www.infojobs.net/'
        }

    def fetch_offers(self, query="desarrollador", location="España", max_offers=50):
        offers = []
        # Mapa de provincias para provinceIds
        province_map = {
            "españa": "",
            "madrid": "28",
            "barcelona": "8",
            "asturias": "33",
            # Añade más según necesidad
        }
        province_id = province_map.get(location.lower(), "")
        normalized_location = location.lower().replace(" ", "-")
        search_url = f"{self.base_url}/jobsearch/search-results/list.xhtml?keyword={query}&provinceIds={province_id}&normalizedLocation={normalized_location}&sortBy=RELEVANCE"

        # Configurar Selenium
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", False)
        chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        chrome_options.add_argument('--headless')  # Opcional: sin interfaz
        driver = webdriver.Chrome(options=chrome_options)

        try:
            logger.info(f"Obteniendo ofertas para query='{query}', location='{location}'")
            driver.get(search_url)
            
            # Manejar banner de cookies
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
                ).click()
                logger.debug("Banner de cookies aceptado.")
            except:
                logger.debug("No se encontró banner de cookies.")

            # Scroll para cargar más ofertas
            time.sleep(5)
            for _ in range(5):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                try:
                    show_more = driver.find_element(By.CLASS_NAME, "ij-ShowMoreResults-button")
                    show_more.click()
                    logger.debug("Clic en 'Mostrar más'.")
                    time.sleep(3)
                except:
                    logger.debug("No se encontró botón 'Mostrar más'.")
                    break

            # Procesar HTML
            soup = BeautifulSoup(driver.page_source, "html.parser")
            job_cards = soup.find_all("div", class_="ij-OfferList-item")
            if not job_cards:
                logger.warning("No se encontraron ofertas. Guardando HTML para depuración.")
                with open('debug_search.html', 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                return offers

            one_month_ago = timezone.now().date() - timedelta(days=30)
            for job in job_cards[:max_offers]:
                title_elem = job.find("a", class_="ij-OfferList-title")
                company_elem = job.find("span", class_="ij-OfferList-company")
                location_elem = job.find("span", class_="ij-OfferList-location")
                date_elem = job.find("span", class_="ij-OfferList-date")
                skills_elems = job.find_all("span", class_="ij-OfferList-skill")[:10]
                url_elem = title_elem.get('href') if title_elem else None

                title_text = title_elem.text.strip() if title_elem else "Sin título"
                company_text = company_elem.text.strip() if company_elem else "Sin compañía"
                location_text = location_elem.text.strip() if location_elem else "Sin ubicación"
                url = f"{self.base_url}{url_elem}" if url_elem and not url_elem.startswith('http') else url_elem

                try:
                    pub_date = datetime.strptime(date_elem.text.strip(), '%d/%m/%Y').date() if date_elem else one_month_ago
                except (ValueError, TypeError):
                    pub_date = one_month_ago

                if pub_date < one_month_ago:
                    logger.debug(f"Oferta descartada por antigüedad: {title_text}")
                    continue

                offer_data = {
                    'url': url,
                    'title': title_text,
                    'company': company_text,
                    'location': location_text,
                    'publication_date': pub_date,
                    'salary_range': None,
                    'description': '',
                    'skills': [skill.text.strip() for skill in skills_elems],
                    'raw_data': {'html_snippet': str(job)[:1000]}
                }
                offers.append(offer_data)
                logger.debug(f"Encontrada oferta: {title_text}, URL: {url}")

        except Exception as e:
            logger.error(f"Error al obtener lista de ofertas de InfoJobs: {e}")
            with open('debug_search.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
        finally:
            driver.quit()

        return offers[:max_offers]

    def parse_offer_detail(self, url_or_data):
        # Tu código extrae todo desde la lista, así que devolvemos los datos directamente
        offer_data = url_or_data if isinstance(url_or_data, dict) else {'url': url_or_data}
        return offer_data

    def run(self, query="desarrollador", location="España", max_offers=50):
        logger.info(f"Iniciando scraping de InfoJobs: query='{query}', location='{location}', max_offers={max_offers}")
        source, _ = JobSource.objects.get_or_create(
            name=self.source_name,
            defaults={'url': self.base_url}
        )

        source.last_scraped = timezone.now()
        source.save()

        offers_data = self.fetch_offers(query, location, max_offers)
        results = []

        for data in offers_data:
            offer_details = self.parse_offer_detail(data)
            if not offer_details or not offer_details.get('url'):
                continue

            try:
                offer, created = JobOffer.objects.get_or_create(
                    url=offer_details['url'],
                    defaults={
                        'title': offer_details.get('title', 'Sin título'),
                        'company': offer_details.get('company'),
                        'location': offer_details.get('location'),
                        'description': offer_details.get('description', ''),
                        'salary_range': offer_details.get('salary_range'),
                        'publication_date': offer_details.get('publication_date'),
                        'source': source,
                        'applicants_count': offer_details.get('applicants_count'),
                        'raw_data': offer_details.get('raw_data', {}),
                        'is_active': True
                    }
                )

                if created:
                    logger.info(f"Nueva oferta guardada: {offer.title}")
                    for skill_name in offer_details.get('skills', []):
                        if skill_name:
                            skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
                            offer.required_skills.add(skill)
                else:
                    logger.debug(f"Oferta ya existente: {offer.title}")

                results.append(offer)

            except Exception as e:
                logger.error(f"Error al guardar oferta {offer_details.get('url')}: {e}")

        logger.info(f"Scraping de InfoJobs completado: {len(results)} ofertas procesadas.")
        return results