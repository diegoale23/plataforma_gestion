# market_analysis/scraping/tecnoempleo_scraper.py
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlencode
from datetime import datetime
import re
from .base_scraper import BaseScraper
from market_analysis.models import JobOffer, MarketTrend, JobSource
from users.models import Skill

class TecnoempleoScraper(BaseScraper):
    """Scraper para obtener ofertas reales de Tecnoempleo.com."""

    def __init__(self):
        super().__init__("Tecnoempleo", "https://www.tecnoempleo.com")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        # Opcional: Agrega proxies si te bloquean
        # self.proxies = {'http': 'http://tu_proxy', 'https': 'https://tu_proxy'}

    def fetch_offers(self, query="desarrollador", location="Madrid", max_offers=50):
        """Busca ofertas en Tecnoempleo y extrae las URLs de detalle."""
        print(f"Buscando ofertas en Tecnoempleo: query='{query}', location='{location}'")
        offer_urls = []
        page = 1
        search_params = {'k': query, 'p': location, 'pagina': page}
        base_search_url = urljoin(self.base_url, "/ofertas-trabajo/")

        while len(offer_urls) < max_offers:
            search_params['pagina'] = page
            current_search_url = f"{base_search_url}?{urlencode(search_params)}"
            print(f"  -> Solicitando página {page}: {current_search_url}")
            try:
                response = requests.get(current_search_url, headers=self.headers, timeout=15)  # Quita proxies= si no usas
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'lxml')

                # Selector ajustado tras inspeccionar Tecnoempleo (verificar con F12)
                offer_elements = soup.select('div.border-bottom.py-3')
                if not offer_elements:
                    print("  -> No se encontraron más elementos de oferta en la página.")
                    break

                found_in_page = 0
                for offer_elem in offer_elements:
                    link_tag = offer_elem.find('a', href=True)
                    if link_tag and '/oferta/' in link_tag['href']:
                        absolute_url = urljoin(self.base_url, link_tag['href'])
                        if absolute_url not in offer_urls:
                            offer_urls.append(absolute_url)
                            found_in_page += 1
                            if len(offer_urls) >= max_offers:
                                break

                print(f"  -> Encontradas {found_in_page} nuevas URLs de oferta en página {page}.")
                if found_in_page == 0 and page > 1:
                    print("  -> No se encontraron nuevas ofertas, deteniendo paginación.")
                    break

                # Verificar paginación (ajustar selector según el sitio real)
                next_page_link = soup.select_one('a.page-link[rel="next"]')
                if not next_page_link or len(offer_urls) >= max_offers:
                    print("  -> No hay enlace a página siguiente o límite alcanzado.")
                    break

                page += 1
                time.sleep(2)  # Pausa para evitar bloqueos

            except requests.RequestException as e:
                print(f"Error al solicitar la página de búsqueda de Tecnoempleo: {e}")
                break
            except Exception as e:
                print(f"Error al parsear la página de búsqueda de Tecnoempleo: {e}")
                break

        print(f"Búsqueda en Tecnoempleo finalizada. Total URLs encontradas: {len(offer_urls)}")
        return offer_urls

    def parse_offer_detail(self, url):
        """Extrae los detalles de una página de oferta específica de Tecnoempleo."""
        print(f"  -> Parseando detalle: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=15)  # Quita proxies= si no usas
            response.raise_for_status()
            time.sleep(1)  # Pausa corta entre detalles
            soup = BeautifulSoup(response.text, 'lxml')

            # Asegurarse de que la fuente existe
            source, _ = JobSource.objects.get_or_create(name=self.source_name, defaults={'url': self.base_url})
            source.last_scraped = datetime.now()
            source.save()

            # Datos básicos
            data = {'url': url, 'source': source}

            # Título (ajustado tras inspeccionar)
            title_tag = soup.find('h1', class_='h2')
            data['title'] = title_tag.get_text(strip=True) if title_tag else "Sin título"

            # Empresa
            company_tag = soup.select_one('p.text-muted a[href*="/empresa/"]')
            data['company'] = company_tag.get_text(strip=True) if company_tag else None

            # Ubicación
            location_tag = soup.select_one('i.bi-geo-alt-fill + span')
            data['location'] = location_tag.get_text(strip=True) if location_tag else None

            # Descripción
            description_div = soup.find('div', id='offer-description')
            data['description'] = '\n'.join(p.get_text(strip=True) for p in description_div.find_all(['p', 'li']) if p.get_text(strip=True)) if description_div else None

            # Habilidades requeridas
            skills_list = []
            skills_section = soup.select_one('ul.list-unstyled.text-muted')
            if skills_section:
                skill_tags = skills_section.find_all('li')
                skills_list = [tag.get_text(strip=True) for tag in skill_tags if tag.get_text(strip=True)]
            elif data['description']:
                text = data['description'].lower()
                known_skills = Skill.objects.values_list('name', flat=True)
                skills_list = [skill for skill in known_skills if skill.lower() in text]

            skill_objects = []
            for skill_name in set(skills_list):
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                skill_objects.append(skill)

            # Fecha de publicación
            date_tag = soup.select_one('span.text-muted:contains("Publicada")')
            if date_tag:
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', date_tag.get_text())
                data['publication_date'] = datetime.strptime(date_match.group(1), '%d/%m/%Y').date() if date_match else None
            else:
                data['publication_date'] = None

            # Salario
            salary_tag = soup.select_one('span.text-muted:contains("€")')
            data['salary_range'] = salary_tag.get_text(strip=True) if salary_tag else "No especificado"

            # Validar datos mínimos
            if not data.get('title') or not data.get('url'):
                print(f"    * Advertencia: Oferta de Tecnoempleo descartada por faltar título o URL: {url}")
                return None

            # Guardar en JobOffer
            job_offer, created = JobOffer.objects.update_or_create(
                url=data['url'],
                defaults={
                    'title': data['title'],
                    'company': data['company'],
                    'location': data['location'],
                    'description': data['description'],
                    'publication_date': data['publication_date'],
                    'salary_range': data['salary_range'],
                    'source': data['source'],
                    'is_active': True,
                }
            )
            if skill_objects:
                job_offer.required_skills.set(skill_objects)

            # Actualizar MarketTrend
            skill_trends = {}
            for skill in skill_objects:
                skill_trends[skill.name] = {'score': 1}

            market_trend, _ = MarketTrend.objects.get_or_create(
                analysis_date=datetime.now().date(),
                period="Mensual",
                region=data['location'] or "Desconocida",
                defaults={
                    'industry': "Tecnología",
                    'skill_trends': skill_trends,
                    'source_description': f"Datos scrapeados de {self.source_name}",
                }
            )
            if not created:
                for skill, trend in skill_trends.items():
                    if skill in market_trend.skill_trends:
                        market_trend.skill_trends[skill]['score'] = market_trend.skill_trends[skill].get('score', 0) + 1
                    else:
                        market_trend.skill_trends[skill] = trend
                market_trend.save()

            print(f"    -> Parseado: {data.get('title', 'N/A')} @ {data.get('company', 'N/A')}")
            return data

        except requests.RequestException as e:
            print(f"  -> Error al solicitar detalle de Tecnoempleo {url}: {e}")
            return None
        except Exception as e:
            print(f"  -> Error al parsear detalle de Tecnoempleo {url}: {e}")
            return None

    def run(self, query="desarrollador", location="Madrid", max_offers=50):
        """Ejecuta el proceso completo de scraping para Tecnoempleo."""
        offer_urls = self.fetch_offers(query, location, max_offers)
        all_offer_data = []
        print(f"Parseando detalles para {len(offer_urls)} ofertas de Tecnoempleo...")
        for url in offer_urls:
            detail_data = self.parse_offer_detail(url)
            if detail_data:
                all_offer_data.append(detail_data)
        return all_offer_data

if __name__ == "__main__":
    scraper = TecnoempleoScraper()
    offers = scraper.run(query="desarrollador", location="Madrid", max_offers=10)
    print(f"Total ofertas extraídas: {len(offers)}")