# market_analysis/scraping/linkedin_scraper.py
import re
import time
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from django.utils import timezone
from .base_scraper import BaseScraper  # Relativa dentro de scraping/
from market_analysis.models import JobOffer, MarketTrend, JobSource  # Absoluta
from users.models import Skill  # Absoluta
from concurrent.futures import ThreadPoolExecutor

class LinkedinScraper(BaseScraper):
    def __init__(self):
        super().__init__("LinkedIn", "https://www.linkedin.com")
        print("\n" + "*" * 70)
        print("ADVERTENCIA: Scraping de LinkedIn en curso.")
        print("Esto puede violar los Términos de Servicio de LinkedIn y resultar en bloqueos.")
        print("Usa este código bajo tu propio riesgo y con moderación.")
        print("*" * 70 + "\n")

        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Modo sin interfaz
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument("--disable-webrtc")  # Desactivar WebRTC para evitar errores STUN
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Evitar detección como bot
        chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'es,es-ES'})  # Configurar idioma español

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        time.sleep(5)  # Estabilizar el navegador

    def login(self, username, password):
        print("Iniciando sesión en LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(random.uniform(1, 3))
        
        email_field = self.driver.find_element(By.ID, "username")
        email_field.send_keys(username)
        
        password_field = self.driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(random.uniform(2, 4))
        
        print(f"URL después del login: {self.driver.current_url}")
        if "feed" in self.driver.current_url:
            print("Inicio de sesión exitoso.")
        else:
            print("Error al iniciar sesión. Puede haber CAPTCHA, 2FA o credenciales incorrectas.")
            self.driver.save_screenshot("login_error.png")
            with open("login_error.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise Exception("No se pudo iniciar sesión en LinkedIn.")

    def fetch_offers(self, query="desarrollador", location="España", max_offers=10):
        print(f"Buscando ofertas en LinkedIn: query='{query}', location='{location}'")
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&sort=date"
        self.driver.get(search_url)
        time.sleep(random.uniform(2, 5))

        print(f"URL actual: {self.driver.current_url}")
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        if "challenge" in self.driver.current_url or "verify" in self.driver.current_url or soup.select_one('input[id="captcha"]'):
            print("CAPTCHA o verificación detectada.")
            self.driver.save_screenshot("captcha_detected.png")
            with open("captcha_detected.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            return []

        try:
            # Esperar a que el cuerpo de la página esté presente
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("Cuerpo de la página cargado.")

            # Verificar que estamos en la página de búsqueda
            if "jobs/search" not in self.driver.current_url:
                print("Redirección detectada, no se cargó la página de búsqueda.")
                self.driver.save_screenshot("redirect_error.png")
                with open("redirect_error.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                return []

            # Esperar a que aparezcan las ofertas (ajustar selector si es necesario)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/jobs/view/']"))
            )
            print("Ofertas de búsqueda cargadas correctamente.")
            with open("linkedin_search_success.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)  # Guardar HTML para depuración
        except Exception as e:
            print(f"Error al cargar la página de búsqueda: {e}")
            self.driver.save_screenshot("search_error.png")
            with open("linkedin_search_error.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            return []

        offer_urls = []
        scroll_attempts = 0
        max_scrolls = 2

        while len(offer_urls) < max_offers and scroll_attempts < max_scrolls:
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            job_cards = soup.select('a[href*="/jobs/view/"]')
            for card in job_cards:
                href = card.get('href', '')
                if href and href not in offer_urls and "/jobs/view/" in href:
                    full_url = f"https://www.linkedin.com{href.split('?')[0]}"
                    offer_urls.append(full_url)
                    if len(offer_urls) >= max_offers:
                        break

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))  # Más tiempo para cargar contenido dinámico
            scroll_attempts += 1

        print(f"Total URLs recolectadas: {len(offer_urls)}")
        return offer_urls[:max_offers]

    def parse_offer_detail(self, url):
        print(f"  -> Parseando detalle: {url}")
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(random.uniform(1, 2))
            job_id = url.split('/jobs/view/')[1].split('/')[0]
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            source, _ = JobSource.objects.get_or_create(name=self.source_name, defaults={'url': self.base_url})
            source.last_scraped = timezone.now()
            source.save()

            data = {'url': url, 'source': source}

            title_tag = soup.select_one('h1.top-card-layout__title') or soup.select_one('.job-details-jobs-unified-top-card__job-title')
            data['title'] = title_tag.get_text(strip=True)[:255] if title_tag else "Sin título"
            print(f"    -> Título: {data['title']}")

            company_tag = soup.select_one('a.topcard__org-name-link') or soup.select_one('.job-details-jobs-unified-top-card__company-name a')
            data['company'] = company_tag.get_text(strip=True)[:255] if company_tag else None
            print(f"    -> Empresa: {data['company']}")

            location_tag = soup.select_one('.artdeco-entity-lockup__caption div[dir="ltr"]')
            if location_tag:
                location_text = location_tag.get_text(strip=True)
                if '(' in location_text and ')' in location_text:
                    data['location'] = location_text.split('(')[0].strip()[:255]
                    data['modality'] = location_text.split('(')[1].replace(')', '').strip()
                else:
                    data['location'] = location_text[:255]
                    data['modality'] = "No especificada"
            else:
                data['location'] = "Ubicación no especificada"
                data['modality'] = "No especificada"
            print(f"    -> Ubicación: {data['location']} ({data['modality']})")

            description_tag = soup.select_one('div.jobs-description__content') or soup.select_one('.jobs-box__html-content')
            data['description'] = description_tag.get_text(strip=True) if description_tag else "No especificada"
            print(f"    -> Descripción: {data['description'][:100]}...")

            skills_list = []
            text = data['description'].lower()
            known_skills = Skill.objects.values_list('name', flat=True)
            skills_list = [skill for skill in known_skills if skill.lower() in text and len(skill) > 2]
            skill_objects = [Skill.objects.get_or_create(name=skill_name)[0] for skill_name in set(skills_list)]
            print(f"    -> Habilidades: {skills_list}")

            date_tag = soup.select_one('time') or soup.select_one('span.jobs-unified-top-card__posted-date')
            if date_tag:
                date_text = date_tag.get_text(strip=True).lower()
                if "hace" in date_text:
                    match = re.search(r'(\d+)\s*(hora|día|semana|mes)', date_text)
                    if match:
                        value, unit = match.groups()
                        value = int(value)
                        now = datetime.now().date()
                        if "hora" in unit:
                            data['publication_date'] = now
                        elif "día" in unit:
                            data['publication_date'] = now - timedelta(days=value)
                        elif "semana" in unit:
                            data['publication_date'] = now - timedelta(weeks=value)
                        elif "mes" in unit:
                            data['publication_date'] = now - timedelta(days=value * 30)
                        else:
                            data['publication_date'] = now
                    else:
                        data['publication_date'] = datetime.now().date()
                else:
                    data['publication_date'] = datetime.now().date()
            else:
                data['publication_date'] = datetime.now().date()
            print(f"    -> Fecha: {data['publication_date']}")

            salary_tag = soup.select_one('#SALARY .jobs-details__salary-main-rail-card span') or soup.select_one('.jobs-unified-top-card__salary')
            data['salary_range'] = salary_tag.get_text(strip=True)[:255] if salary_tag else "No especificado"
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

            return data

        except Exception as e:
            print(f"  -> Error al parsear detalle: {e}")
            return None

    def run(self, username, password, query="desarrollador", location="España", max_offers=10):
        try:
            self.login(username, password)
            offer_urls = self.fetch_offers(query, location, max_offers)
            all_offer_data = []

            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_url = {executor.submit(self.parse_offer_detail, url): url for url in offer_urls}
                for future in future_to_url:
                    try:
                        detail_data = future.result()
                        if detail_data:
                            all_offer_data.append(detail_data)
                    except Exception as e:
                        print(f"Error al procesar {future_to_url[future]}: {e}")

            print(f"Total ofertas extraídas: {len(all_offer_data)}")
            return all_offer_data
        except Exception as e:
            print(f"Error crítico en la ejecución: {e}")
            return []
        finally:
            try:
                self.driver.quit()
                print("Navegador cerrado correctamente.")
            except Exception as e:
                print(f"Error al cerrar el navegador: {e}")

if __name__ == "__main__":
    import django
    import os
    import sys

    # Asegurarse de que el directorio raíz del proyecto esté en sys.path
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(BASE_DIR)

    # Configurar Django para ejecución standalone
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plataforma_gestion.settings')
    django.setup()

    scraper = LinkedinScraper()
    offers = scraper.run(
        username="diegoale23@yahoo.com",
        password="dacp18419361",
        query="desarrollador",
        location="España",
        max_offers=5
    )
    print(f"Total ofertas extraídas: {len(offers)}")
    for offer in offers:
        print(offer)