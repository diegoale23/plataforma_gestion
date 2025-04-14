# market_analysis/scraping/linkedin_scraper.py
import re
import time
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
from django.conf import settings  # Importar settings para las credenciales
from .base_scraper import BaseScraper
from market_analysis.models import JobOffer, MarketTrend, JobSource
from users.models import Skill

class LinkedinScraper(BaseScraper):
    def __init__(self):
        super().__init__("LinkedIn", "https://www.linkedin.com")
        print("\n" + "*" * 70)
        print("ADVERTENCIA: Scraping de LinkedIn en curso.")
        print("Esto puede violar los Términos de Servicio de LinkedIn y resultar en bloqueos.")
        print("Usa este código bajo tu propio riesgo y con moderación.")
        print("Ejecutando en modo headless (sin navegador visible).")
        print("*" * 70 + "\n")

        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ejecutar sin interfaz gráfica
        chrome_options.add_argument("--disable-gpu")  # Deshabilitar GPU
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def login(self, username, password):
        print("Iniciando sesión en LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)

        email_field = self.driver.find_element(By.ID, "username")
        email_field.send_keys(username)

        password_field = self.driver.find_element(By.ID, "password")
        password_field.send_keys(password)

        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)

        if "feed" in self.driver.current_url:
            print("Inicio de sesión exitoso.")
        else:
            print("Error al iniciar sesión. Puede haber CAPTCHA, 2FA o credenciales incorrectas.")
            self.driver.save_screenshot("login_error.png")
            raise Exception("No se pudo iniciar sesión en LinkedIn.")

    def fetch_offers(self, query="desarrollador", location="España", max_offers=10):
        print(f"Buscando ofertas en LinkedIn: query='{query}', location='{location}'")
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&sort=date"
        self.driver.get(search_url)
        time.sleep(5)

        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        max_attempts = 3
        attempt = 0

        while ("challenge" in self.driver.current_url or
               "verify" in self.driver.current_url or
               soup.select_one('input[id="captcha"]')):
            if attempt >= max_attempts:
                print("Demasiados intentos fallidos de CAPTCHA. Abortando...")
                return []
            print(f"Intento {attempt + 1}/{max_attempts}: CAPTCHA o verificación detectada.")
            print(f"URL actual: {self.driver.current_url}")
            print(f"Fragmento de página: {soup.text[:200]}...")
            self.driver.save_screenshot(f"captcha_detected_attempt_{attempt}.png")
            print("Modo headless activo: no se puede resolver CAPTCHA manualmente. Saltando...")
            break  # En modo headless, no se puede resolver CAPTCHA manualmente
            time.sleep(5)
            self.driver.get(search_url)
            time.sleep(5)
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            attempt += 1

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("Página básica cargada.")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/jobs/view/']"))
            )
            print("Ofertas de búsqueda cargadas correctamente.")
        except Exception as e:
            print(f"Error al cargar la página de búsqueda: {e}")
            self.driver.save_screenshot("search_error.png")
            with open("linkedin_search.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            return []

        offer_urls = []
        scroll_attempts = 0
        max_scrolls = 5

        while len(offer_urls) < max_offers and scroll_attempts < max_scrolls:
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            job_cards = soup.select('a[href*="/jobs/view/"]')
            for card in job_cards:
                href = card.get('href', '')
                if href and href not in offer_urls and "/jobs/view/" in href:
                    full_url = f"https://www.linkedin.com{href.split('?')[0]}"
                    offer_urls.append(full_url)
                    print(f"    -> URL encontrada: {full_url}")
                    if len(offer_urls) >= max_offers:
                        break

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            scroll_attempts += 1

        print(f"Total URLs recolectadas: {len(offer_urls)}")
        return offer_urls[:max_offers]

    def parse_offer_detail(self, url):
        print(f"  -> Parseando detalle: {url}")
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(10)
            job_id = url.split('/jobs/view/')[1].split('/')[0]
            html_filename = f"job_detail_{job_id}.html"
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"HTML de detalle guardado en '{html_filename}'.")
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            source, _ = JobSource.objects.get_or_create(name=self.source_name, defaults={'url': self.base_url})
            source.last_scraped = timezone.now()
            source.save()

            data = {'url': url, 'source': source}

            # Título
            title_tag = soup.select_one('h1.top-card-layout__title') or soup.select_one('.job-details-jobs-unified-top-card__job-title')
            data['title'] = title_tag.get_text(strip=True)[:255] if title_tag else "Sin título"
            print(f"    -> Título: {data['title']}")

            # Empresa
            company_tag = soup.select_one('a.topcard__org-name-link') or soup.select_one('.job-details-jobs-unified-top-card__company-name a')
            data['company'] = company_tag.get_text(strip=True)[:255] if company_tag else None
            print(f"    -> Empresa: {data['company']}")

            # Ubicación y Modalidad
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

            # Respaldo: extraer ubicación del título si no se encuentra en el HTML
            if data['location'] == "Ubicación no especificada" and '(' in data['title']:
                possible_location = data['title'].split('(')[-1].replace(')', '').strip()
                invalid_keywords = ['urgente', 'inmediata', 'contratación', 'remoto', 'híbrido', 'presencial']
                if len(possible_location) < 50 and not any(keyword.lower() in possible_location.lower() for keyword in invalid_keywords):
                    data['location'] = possible_location

            print(f"    -> Ubicación: {data['location']} ({data['modality']})")

            # Descripción
            description_tag = soup.select_one('div.jobs-description__content') or soup.select_one('.jobs-box__html-content')
            data['description'] = description_tag.get_text(strip=True) if description_tag else "No especificada"
            print(f"    -> Descripción: {data['description'][:100]}...")

            # Habilidades
            skills_list = []
            skills_link = soup.select_one('a[href*="#HYM"][data-test-app-aware-link]')
            skills_section = soup.select('ul span li')
            if skills_link and "Aptitudes:" in skills_link.get_text():
                skills_text = skills_link.get_text(strip=True).replace("Aptitudes:", "").split(" y ")[0].split(", ")
                skills_list = [skill.strip() for skill in skills_text if skill.strip()]
            elif skills_section:
                skills_list = [skill.get_text(strip=True) for skill in skills_section if skill.get_text(strip=True)]
            elif data['description']:
                text = data['description'].lower()
                known_skills = Skill.objects.values_list('name', flat=True)
                skills_list = [skill for skill in known_skills if skill.lower() in text and len(skill) > 2]
            skill_objects = [Skill.objects.get_or_create(name=skill_name)[0] for skill_name in set(skills_list)]
            print(f"    -> Habilidades: {skills_list}")

            # Fecha de publicación
            date_tag = soup.select_one('time') or soup.select_one('span.jobs-unified-top-card__posted-date')
            if date_tag:
                date_text = date_tag.get_text(strip=True).lower()
                print(f"    -> Texto de fecha crudo: '{date_text}'")
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

            # Salario
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

    def run(self, query="desarrollador", location="España", max_offers=10):
        try:
            # Obtener credenciales desde settings.py
            username = getattr(settings, 'LINKEDIN_USERNAME', None)
            password = getattr(settings, 'LINKEDIN_PASSWORD', None)

            if not username or not password:
                raise ValueError("Las credenciales de LinkedIn (LINKEDIN_USERNAME y LINKEDIN_PASSWORD) no están configuradas en settings.py")

            self.login(username, password)
            offer_urls = self.fetch_offers(query, location, max_offers)
            all_offer_data = []
            for url in offer_urls:
                try:
                    detail_data = self.parse_offer_detail(url)
                    if detail_data:
                        all_offer_data.append(detail_data)
                except Exception as e:
                    print(f"Error al procesar {url}: {e}")
                time.sleep(5)
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
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main_project.settings')  # Actualizado al nombre correcto
    django.setup()
    scraper = LinkedinScraper()
    offers = scraper.run(
        query="desarrollador",
        location="España",
        max_offers=30
    )
    print(f"Total ofertas extraídas: {len(offers)}")
    for offer in offers:
        print(offer)