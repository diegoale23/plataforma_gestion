# market_analysis/scraping/infojobs_scraper.py
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlencode
from datetime import datetime
import re
import json
import sys
import os

# Ajustar sys.path para incluir el directorio raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

class InfoJobsScraper:
    def __init__(self):
        self.source_name = "InfoJobs"
        self.base_url = "https://www.infojobs.net"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        }

    def fetch_offers(self, query="desarrollador", location="Madrid", max_offers=30):
        print(f"Buscando ofertas en InfoJobs: query='{query}', location='{location}'")
        offer_urls = []
        page = 1
        base_search_url = urljoin(self.base_url, "/ofertas-trabajo")

        while len(offer_urls) < max_offers:
            search_params = {
                'keyword': query,
                'provincia': location.lower(),
                'page': page
            }
            current_search_url = f"{base_search_url}?{urlencode(search_params)}"
            print(f"  -> Solicitando página {page}: {current_search_url}")

            try:
                response = requests.get(current_search_url, headers=self.headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'lxml')

                # Selector genérico para enlaces de ofertas
                offer_containers = soup.select('a[href*="/oferta-"]')
                print(f"  -> Contenedores encontrados: {len(offer_containers)}")
                if not offer_containers:
                    print("  -> No se encontraron contenedores con ofertas. Revisar HTML.")
                    print("  -> HTML parcial obtenido:", soup.prettify()[:500])
                    break

                found_in_page = 0
                for container in offer_containers:
                    href = container.get('href', '')
                    if '/oferta-' in href:  # Filtrar enlaces que parecen ser ofertas
                        absolute_url = urljoin(self.base_url, href)
                        if absolute_url not in offer_urls:
                            offer_urls.append(absolute_url)
                            found_in_page += 1
                            print(f"    -> URL encontrada: {absolute_url}")
                            if len(offer_urls) >= max_offers:
                                break

                print(f"  -> Encontradas {found_in_page} nuevas URLs en página {page}")
                if found_in_page == 0:
                    print("  -> No se encontraron enlaces válidos en esta página.")
                    break

                next_page = soup.select_one('a[rel="next"]')
                if not next_page or len(offer_urls) >= max_offers:
                    print("  -> No hay más páginas o límite alcanzado.")
                    break

                page += 1
                time.sleep(2)

            except requests.RequestException as e:
                print(f"  -> Error al solicitar página: {e}")
                break

        print(f"Total URLs recolectadas: {len(offer_urls)}")
        return offer_urls

    def parse_offer_detail(self, url):
        from market_analysis.models import JobOffer, MarketTrend, JobSource
        from users.models import Skill
        from django.utils import timezone

        print(f"  -> Parseando detalle: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            print(f"    -> Respuesta HTTP recibida: {response.status_code}")
            time.sleep(1)
            soup = BeautifulSoup(response.text, 'lxml')

            source, _ = JobSource.objects.get_or_create(name=self.source_name, defaults={'url': self.base_url})
            source.last_scraped = timezone.now()
            source.save()

            data = {'url': url, 'source': source}

            # Título
            title_tag = soup.select_one('h1.job-detail-title')
            data['title'] = title_tag.get_text(strip=True) if title_tag else 'Sin título'
            print(f"    -> Título: {data['title']}")

            # Empresa
            company_tag = soup.select_one('span.company-name a')
            data['company'] = company_tag.get_text(strip=True) if company_tag else 'Desconocida'
            print(f"    -> Empresa: {data['company']}")

            # Ubicación y modalidad
            location_tag = soup.select_one('span.location')
            location_text = location_tag.get_text(strip=True) if location_tag else 'Desconocida'
            data['location'] = location_text
            data['modality'] = 'Presencial'
            if 'teletrabajo' in location_text.lower() or 'remoto' in location_text.lower():
                data['modality'] = '100% remoto'
            elif 'híbrido' in location_text.lower():
                data['modality'] = 'Híbrido'
            print(f"    -> Ubicación: {data['location']} ({data['modality']})")

            # Descripción
            description_tag = soup.select_one('div.ij-Box.mb-xl.mt-l')
            data['description'] = description_tag.get_text(strip=True) if description_tag else 'No especificada'
            print(f"    -> Descripción: {data['description'][:100]}...")

            # Habilidades
            skills_list = []
            valid_skills = {
                'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue', 'node.js', 'django', 'flask',
                'spring', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'docker', 'kubernetes', 'aws', 'azure',
                'gcp', 'git', 'ci/cd', 'scrum', 'agile', 'linux', 'bash', 'php', 'ruby', 'go', 'c++', 'c#', '.net',
                'html', 'css', 'sass', 'graphql', 'rest', 'terraform', 'ansible', 'jenkins', 'flutter', 'kotlin', 'swift',
                'hibernate', 'phpunit', 'ajax', 'composer', 'redis', 'pandas', 'numpy', 'zapier', 'chatgpt', 'jquery', 'php7'
            }
            invalid_terms = {
                'desarrollador', 'programador', 'senior', 'junior', 'madrid', 'barcelona', 'españa', 'remoto', 'híbrido',
                'presencial', 'oferta', 'empleo', 'trabajo', 'empresa', 'consultora', 'it', 'software', 'tecnología',
                'developer', 'engineer', 'fullstack', 'backend', 'frontend', 'ingeniero', 'especialista', 'consultoría',
                'proyecto', 'nueva', 'urgente', 'buscamos', 'manager', 'docente', 'online', 'inteligencia', 'artificial'
            }

            # Extraer desde descripción
            if data['description']:
                text = data['description'].lower()
                print(f"    -> Buscando habilidades en descripción...")
                for skill in valid_skills:
                    if skill == 'go':
                        if not re.search(r'\bgo\b|\bgolang\b', text):
                            continue
                    if skill == 'php7':
                        skill = 'php'
                    if skill in text and skill not in invalid_terms and skill not in skills_list:
                        skills_list.append(skill)
                        print(f"    -> Habilidad añadida desde descripción: {skill}")

            # Extraer desde URL
            url_skills = url.split('/')[-1].replace('chat-gpt', 'chatgpt').split('-')
            print(f"    -> Buscando habilidades en URL: {url_skills}")
            for skill in url_skills:
                skill = skill.lower()
                if skill == 'php7':
                    skill = 'php'
                if skill in valid_skills and skill not in invalid_terms and skill not in skills_list:
                    skills_list.append(skill)
                    print(f"    -> Habilidad añadida desde URL: {skill}")

            print(f"    -> Habilidades crudas extraídas: {skills_list}")
            skill_objects = []
            for skill_name in set(skills_list):
                if len(skill_name) > 2:
                    skill_obj, _ = Skill.objects.get_or_create(name=skill_name)
                    skill_objects.append(skill_obj)
            print(f"    -> Habilidades finales: {[skill.name for skill in skill_objects]}")

            # Fecha de publicación
            date_tag = soup.select_one('span.date')
            data['publication_date'] = datetime.now().date()
            if date_tag:
                date_text = date_tag.get_text(strip=True).lower()
                match = re.search(r'hace (\d+) días', date_text)
                if match:
                    days_ago = int(match.group(1))
                    data['publication_date'] = datetime.now().date() - timezone.timedelta(days=days_ago)
            print(f"    -> Fecha: {data['publication_date']}")

            # Salario
            salary_tag = soup.select_one('dd.ij-ca-DescriptionList-item p:contains("Bruto/año")')
            data['salary_range'] = salary_tag.get_text(strip=True) if salary_tag else 'No especificado'
            print(f"    -> Salario: {data['salary_range']}")

            if not data.get('title') or not data.get('url'):
                print(f"    * Advertencia: Oferta descartada por faltar título o URL: {url}")
                return None

            try:
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
                print(f"    -> Guardado en JobOffer: {job_offer.title} {'(nueva)' if created else '(actualizada)'}")
            except Exception as e:
                print(f"    -> Error al guardar en JobOffer: {e}")
                return None

            try:
                skill_trends = {skill.name: {'score': 1} for skill in skill_objects}
                market_trend, _ = MarketTrend.objects.get_or_create(
                    analysis_date=timezone.now().date(),
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
                            market_trend.skill_trends[skill]['score'] += 1
                        else:
                            market_trend.skill_trends[skill] = trend
                    market_trend.save()
                print(f"    -> Actualizado MarketTrend: {len(skill_trends)} habilidades")
            except Exception as e:
                print(f"    -> Error al actualizar MarketTrend: {e}")

            data['required_skills'] = [skill.name for skill in skill_objects]
            return data

        except requests.RequestException as e:
            print(f"  -> Error al solicitar detalle: {e}")
            return None

    def run(self, query="desarrollador", location="Madrid", max_offers=30):
        try:
            offer_urls = self.fetch_offers(query, location, max_offers)
            all_offer_data = []
            for url in offer_urls:
                detail_data = self.parse_offer_detail(url)
                if detail_data:
                    all_offer_data.append(detail_data)
            print(f"Total ofertas extraídas: {len(all_offer_data)}")
            return all_offer_data
        except Exception as e:
            print(f"Error crítico en la ejecución: {e}")
            return []

if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main_project.settings')
    django.setup()
    scraper = InfoJobsScraper()
    offers = scraper.run(query="desarrollador", location="Madrid", max_offers=30)
    print(f"Total ofertas extraídas: {len(offers)}")
    for offer in offers:
        print(f"Oferta: {offer['title']}")
        print(f"  Habilidades: {offer.get('required_skills', [])}")
        print(f"  URL: {offer['url']}")
        print("-" * 50)