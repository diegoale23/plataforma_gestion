from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import time
import random
import os
import re
from django.utils import timezone
from django.conf import settings
from twocaptcha import TwoCaptcha
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
            'Referer': 'https://www.infojobs.net/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        try:
            api_key = getattr(settings, 'TWOCAPTCHA_API_KEY', '')
            if not api_key:
                logger.warning("TWOCAPTCHA_API_KEY no está configurada en .env. El CAPTCHA deberá resolverse manualmente.")
            self.captcha_solver = TwoCaptcha(api_key)
            logger.debug("2Captcha inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error al inicializar 2Captcha: {e}. Verifica que TWOCAPTCHA_API_KEY esté definida y correcta en .env (puedes obtener una en https://2captcha.com/).")
            self.captcha_solver = None

    def parse_relative_date(self, text):
        today = timezone.now().date()
        try:
            match = re.match(r'Hace (\d+)([dh])', text, re.IGNORECASE)
            if match:
                value, unit = int(match.group(1)), match.group(2).lower()
                if unit == 'd':
                    return today - timedelta(days=value)
                elif unit == 'h':
                    return today if value < 24 else today - timedelta(days=1)
            
            match = re.match(r'(\d{1,2})\s*(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)', text, re.IGNORECASE)
            if match:
                day, month_str = int(match.group(1)), match.group(2).lower()
                month_map = {
                    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
                }
                month = month_map.get(month_str)
                if month:
                    year = today.year
                    parsed_date = datetime(year, month, day).date()
                    if parsed_date > today:
                        parsed_date = datetime(year - 1, month, day).date()
                    return parsed_date
                logger.debug(f"Mes no reconocido en '{text}'")
        except Exception as e:
            logger.debug(f"Error al parsear fecha '{text}': {e}")
        return today - timedelta(days=30)

    def fetch_offers(self, query="desarrollador", location="España", max_offers=50):
        offers = []
        province_map = {
            "españa": "",
            "madrid": "28",
            "barcelona": "8",
            "asturias": "33",
        }
        province_id = province_map.get(location.lower(), "")
        normalized_location = location.lower().replace(" ", "-")
        search_url = f"{self.base_url}/jobsearch/search-results/list.xhtml?keyword={query}&provinceIds={province_id}&normalizedLocation={normalized_location}"

        chrome_options = Options()
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--start-maximized')
        profile_dir = os.path.join(os.getcwd(), "chrome_profile_infojobs")
        os.makedirs(profile_dir, exist_ok=True)
        chrome_options.add_argument(f'user-data-dir={profile_dir}')

        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("window.navigator.chrome = { runtime: {} };")
        driver.execute_script("window.navigator.permissions = { query: () => Promise.resolve({ state: 'granted' }) };")

        try:
            logger.info(f"Obteniendo ofertas para query='{query}', location='{location}'")
            driver.get(search_url)
            
            time.sleep(random.uniform(3, 5))
            ActionChains(driver).move_by_offset(random.randint(50, 200), random.randint(50, 200)).perform()
            
            max_captcha_attempts = 3
            for attempt in range(max_captcha_attempts):
                if "Eres humano o un robot" in driver.page_source:
                    logger.info(f"Detectado CAPTCHA de GeeTest (intento {attempt + 1}/{max_captcha_attempts}).")
                    if self.captcha_solver:
                        logger.info("Intentando resolver con 2Captcha.")
                        try:
                            soup = BeautifulSoup(driver.page_source, "html.parser")
                            script = soup.find("script", string=lambda x: x and "initGeetest" in x)
                            gt = None
                            challenge = None
                            if script:
                                script_text = script.text
                                logger.debug(f"Script de GeeTest encontrado: {script_text[:200]}...")
                                lines = script_text.splitlines()
                                for line in lines:
                                    line = line.strip()
                                    if "gt:" in line and not gt:
                                        try:
                                            gt = line.split('"')[1]
                                            logger.debug(f"gt: {gt}")
                                        except IndexError:
                                            logger.error("Error al parsear gt.")
                                    if "challenge:" in line and not challenge:
                                        try:
                                            challenge = line.split('"')[1]
                                            logger.debug(f"challenge: {challenge}")
                                        except IndexError:
                                            logger.error("Error al parsear challenge.")

                            if not gt or not challenge:
                                logger.error(f"No se encontraron gt o challenge (gt={gt}, challenge={challenge}). Guardando HTML para depuración.")
                                with open('debug_captcha.html', 'w', encoding='utf-8') as f:
                                    f.write(driver.page_source)
                                logger.warning("Pasando a resolución manual.")
                            else:
                                result = self.captcha_solver.geetest(
                                    gt=gt,
                                    challenge=challenge,
                                    url=search_url,
                                    timeout=60
                                )
                                logger.debug(f"CAPTCHA resuelto: {result}")
                                driver.execute_script(f'document.getElementsByName("geetest_challenge")[0].value = "{result["geetest_challenge"]}";')
                                driver.execute_script(f'document.getElementsByName("geetest_validate")[0].value = "{result["geetest_validate"]}";')
                                driver.execute_script(f'document.getElementsByName("geetest_seccode")[0].value = "{result["geetest_seccode"]}";')
                                logger.debug("Solución de CAPTCHA inyectada.")
                                driver.execute_script("solvedCaptcha({geetest_challenge: arguments[0], geetest_validate: arguments[1], geetest_seccode: arguments[2], data: ''});",
                                                      result["geetest_challenge"], result["geetest_validate"], result["geetest_seccode"])
                                time.sleep(random.uniform(5, 7))
                                if "Eres humano o un robot" not in driver.page_source:
                                    logger.info("CAPTCHA resuelto con 2Captcha.")
                                    break
                        except Exception as e:
                            logger.error(f"Error al resolver CAPTCHA con 2Captcha: {e}. Verifica que TWOCAPTCHA_API_KEY esté definida y correcta en .env (puedes obtener una en https://2captcha.com/).")
                            with open('debug_captcha.html', 'w', encoding='utf-8') as f:
                                f.write(driver.page_source)
                            logger.warning("Pasando a resolución manual.")

                    logger.warning(f"No se pudo resolver con 2Captcha o no configurado. Resuelve el CAPTCHA manualmente (intento {attempt + 1}).")
                    time.sleep(60)
                    if "Eres humano o un robot" not in driver.page_source:
                        logger.info("CAPTCHA resuelto manualmente.")
                        break
                else:
                    logger.info("No se detectó CAPTCHA.")
                    break

            if "Eres humano o un robot" in driver.page_source:
                logger.error("No se pudo resolver el CAPTCHA tras varios intentos. Guardando HTML para depuración.")
                with open('debug_captcha.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                return offers

            try:
                cookie_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
                )
                ActionChains(driver).move_to_element(cookie_button).pause(random.uniform(0.5, 1)).click().perform()
                logger.debug("Banner de cookies aceptado.")
            except:
                logger.debug("No se encontró banner de cookies.")

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.ij-List-item'))
                )
                logger.debug("Ofertas detectadas en la página.")
            except Exception as e:
                logger.error(f"Error esperando ofertas: {e}")
                with open('debug_search.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                return offers

            for _ in range(5):
                driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                time.sleep(random.uniform(2, 4))
                try:
                    show_more = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "ij-ShowMoreResults-button"))
                    )
                    ActionChains(driver).move_to_element(show_more).pause(random.uniform(0.5, 1)).click().perform()
                    logger.debug("Clic en 'Mostrar más'.")
                    time.sleep(random.uniform(2, 4))
                except:
                    logger.debug("No se encontró botón 'Mostrar más'.")
                    break

            ActionChains(driver).move_by_offset(random.randint(-100, 100), random.randint(-100, 100)).perform()
            
            try:
                job_cards = driver.find_elements(By.CSS_SELECTOR, 'li.ij-List-item:not(.ij-OfferList-banner):not(.ij-CampaignsLogosSimple)')
                logger.debug(f"Se encontraron {len(job_cards)} elementos li.ij-List-item")
                if not job_cards:
                    logger.warning("No se encontraron ofertas. Guardando HTML para depuración.")
                    with open('debug_search.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    return offers

                one_month_ago = timezone.now().date() - timedelta(days=30)
                valid_offer_found = False
                for job in job_cards[:max_offers]:
                    try:
                        title_text = "Sin título"
                        url = None
                        try:
                            title_elem = job.find_element(By.CSS_SELECTOR, 'a.ij-OfferCardContent-description-title-link')
                            title_text = title_elem.text.strip()
                            url = title_elem.get_attribute('href')
                            url = f"{self.base_url}{url}" if url and not url.startswith('http') else url
                        except:
                            logger.debug(f"No se encontró título. HTML de oferta: {job.get_attribute('outerHTML')[:500]}")
                            continue

                        description_text = ""
                        try:
                            description_elem = job.find_element(By.CSS_SELECTOR, 'p.ij-OfferCardContent-description-description')
                            description_text = description_elem.text.strip()
                            logger.debug(f"Descripción: {description_text[:200]}...")
                        except:
                            logger.debug("No se encontró descripción")

                        location_text = "Sin ubicación"
                        try:
                            location_elem = job.find_element(By.CSS_SELECTOR, 'span.ij-OfferCardContent-description-list-item-truncate')
                            location_text = location_elem.text.strip()
                            logger.debug(f"Ubicación extraída (HTML): {location_text}")
                        except:
                            location_match = re.search(r'(?:Ubicación|Ubicacion|Localidad):\s*([A-Za-z\s]+)', description_text, re.IGNORECASE)
                            if location_match:
                                location_text = location_match.group(1).strip()
                                logger.debug(f"Ubicación extraída (descripción): {location_text}")
                            else:
                                location_keywords = [
                                    'Valencia', 'Madrid', 'Barcelona', 'Sevilla', 'Bilbao', 'Remoto',
                                    'Teletrabajo', 'Málaga', 'Zaragoza', 'Alicante'
                                ]
                                for keyword in location_keywords:
                                    if keyword.lower() in description_text.lower():
                                        location_text = keyword
                                        logger.debug(f"Ubicación por palabra clave: {location_text}")
                                        break

                        company_text = "Sin compañía"
                        try:
                            company_elem = job.find_element(By.CSS_SELECTOR, 'a.ij-OfferCardContent-description-subtitle-link')
                            company_text = company_elem.text.strip()
                            logger.debug(f"Empresa extraída (HTML): {company_text}")
                        except:
                            logger.debug("No se encontró empresa en HTML (selector: a.ij-OfferCardContent-description-subtitle-link)")
                            company_match = re.search(r'(?:Acerca de|Empresa:|\bEn\s+)([A-Za-z0-9\s&-]+?)(?:\s+\w{3,}|\s*[,.\n])', description_text, re.IGNORECASE)
                            if company_match:
                                company_text = company_match.group(1).strip()
                                logger.debug(f"Empresa extraída (descripción): {company_text}")

                        salary_text = None
                        try:
                            salary_elem = job.find_element(By.CSS_SELECTOR, 'span[class*="salary"]')
                            salary_text = salary_elem.text.strip()
                            logger.debug(f"Salario extraído (HTML): {salary_text}")
                        except:
                            salary_match = re.search(r'(?:Salario|Sueldo):\s*([\d\s.k€-]+)', description_text, re.IGNORECASE)
                            if salary_match:
                                salary_text = salary_match.group(1).strip()
                                logger.debug(f"Salario extraído (descripción): {salary_text}")

                        pub_date = one_month_ago
                        try:
                            date_elem = job.find_element(By.CSS_SELECTOR, 'span.ij-FormatterSincedate')
                            date_text = date_elem.text.strip()
                            pub_date = self.parse_relative_date(date_text)
                            logger.debug(f"Fecha extraída: {pub_date} (texto: {date_text})")
                        except:
                            logger.debug("No se encontró fecha en HTML (selector: span.ij-FormatterSincedate)")

                        applicants_count = None
                        try:
                            applicants_elem = job.find_element(By.CSS_SELECTOR, 'span.ij-OfferCardContent-description-list-item')
                            applicants_text = applicants_elem.text.strip()
                            match = re.search(r'(\d+)\s*inscrito?s?', applicants_text, re.IGNORECASE)
                            if match:
                                applicants_count = int(match.group(1))
                                logger.debug(f"Inscritos extraídos: {applicants_count}")
                        except:
                            logger.debug("No se encontró número de inscritos")

                        skills = []
                        try:
                            skills_elems = job.find_elements(By.CSS_SELECTOR, 'span.sui-MoleculeTag-label')
                            skills.extend([skill.text.strip() for skill in skills_elems[:10] if skill.text.strip()])
                            logger.debug(f"Habilidades (etiquetas): {skills}")
                        except:
                            logger.debug("No se encontraron habilidades en etiquetas")

                        skill_keywords = [
                            '.NET', 'ASP.NET', 'Kubernetes', 'Docker', 'MongoDB', 'SQL Server',
                            'Redis', 'OAuth', 'JWT', 'OpenID', 'ETL', 'OpenAPI', 'Java',
                            'SpringBoot', 'Angular', 'Kotlin', 'Golang', 'Drupal'
                        ]
                        for skill in skill_keywords:
                            if skill.lower() in description_text.lower():
                                skills.append(skill)
                        logger.debug(f"Habilidades totales: {skills}")

                        offer_data = {
                            'url': url if url else f"no-url-{title_text[:50]}-{random.randint(1, 10000)}",
                            'title': title_text[:255],
                            'company': company_text[:255],
                            'location': location_text[:255],
                            'publication_date': pub_date,
                            'salary_range': salary_text[:255] if salary_text else None,
                            'description': description_text[:2000],
                            'skills': list(set(skills)),
                            'applicants_count': applicants_count,
                            'raw_data': {'html_snippet': job.get_attribute('outerHTML')[:1000]}
                        }
                        offers.append(offer_data)
                        logger.debug(f"Encontrada oferta: {title_text}, URL: {url}, Empresa: {company_text}, Ubicación: {location_text}, Salario: {salary_text}, Habilidades: {skills}, Fecha: {pub_date}, Inscritos: {applicants_count}")

                        if not valid_offer_found:
                            with open('debug_offer.html', 'w', encoding='utf-8') as f:
                                f.write(job.get_attribute('outerHTML'))
                            valid_offer_found = True

                    except Exception as e:
                        logger.error(f"Error al procesar oferta: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error al obtener lista de ofertas: {e}")
                with open('debug_search.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)

        finally:
            try:
                driver.quit()
                logger.info("Navegador cerrado correctamente.")
            except Exception as e:
                logger.error(f"Error al cerrar el navegador: {e}")

        return offers[:max_offers]

    def parse_offer_detail(self, url_or_data):
        offer_data = url_or_data if isinstance(url_or_data, dict) else {'url': url_or_data}
        return offer_data

    def run(self, query="desarrollador", location="España", max_offers=50):
        logger.info(f"Iniciando scraping de InfoJobs: query='{query}', location='{location}', max_offers={max_offers}")
        try:
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
                    logger.debug(f"Oferta ignorada por falta de URL: {offer_details.get('title', 'Sin título')}")
                    continue

                try:
                    defaults = {
                        'title': offer_details.get('title', 'Sin título')[:255],
                        'company': offer_details.get('company', 'Sin compañía')[:255],
                        'location': offer_details.get('location', 'Sin ubicación')[:255],
                        'description': offer_details.get('description', '')[:2000],
                        'salary_range': offer_details.get('salary_range')[:255] if offer_details.get('salary_range') else None,
                        'publication_date': offer_details.get('publication_date'),
                        'source': source,
                        'applicants_count': offer_details.get('applicants_count', None),
                        'raw_data': offer_details.get('raw_data', {}),
                        'is_active': True
                    }
                    offer, created = JobOffer.objects.get_or_create(
                        url=offer_details['url'],
                        defaults=defaults
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
        except Exception as e:
            logger.error(f"Error crítico en InfojobsScraper: {e}")
            return []