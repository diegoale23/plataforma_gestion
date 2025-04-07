# market_analysis/scraping/infojobs_api_client.py
import requests
import time
from django.conf import settings
from urllib.parse import urlencode
from .base_scraper import BaseScraper # Mantenemos la interfaz base

class InfojobsAPIClient(BaseScraper):
    """Cliente para interactuar con la API de InfoJobs."""

    API_BASE_URL = "https://api.infojobs.net/api/"
    MAX_RESULTS_PER_PAGE = 50 # InfoJobs suele limitar a 50 o 100

    def __init__(self):
        super().__init__("InfoJobs", "https://www.infojobs.net")
        self.access_token = settings.INFOJOBS_ACCESS_TOKEN
        if not self.access_token:
            raise ValueError("Token de acceso de InfoJobs no configurado en settings.py / .env")
        # La autenticación Basic suele ser el client_id: (vacío) codificado en Base64
        # o a veces un Bearer token. Verifica la documentación de InfoJobs actual.
        # Asumiremos Bearer Token por simplicidad aquí.
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': 'PlataformaGestionLaboral/1.0 (Python Client)', # Un User-Agent descriptivo
        }

    def _make_request(self, endpoint, params=None):
        """Realiza una petición GET a la API de InfoJobs."""
        url = f"{self.API_BASE_URL}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status() # Lanza excepción para errores HTTP (4xx, 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error en la petición a InfoJobs ({url}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  -> Status Code: {e.response.status_code}")
                try:
                    print(f"  -> Body: {e.response.json()}")
                except ValueError: # Si el body no es JSON
                    print(f"  -> Body: {e.response.text}")
            return None
        except ValueError: # Si la respuesta no es JSON válido
            print(f"Error: La respuesta de InfoJobs ({url}) no es JSON válido.")
            return None

    def fetch_offers(self, query="desarrollador", location="Madrid", max_offers=100):
        """
        Busca ofertas de empleo usando la API.

        Args:
            query: Término de búsqueda (ej: "Python", "Django React").
            location: Nombre de la provincia o región (se intentará mapear).
            max_offers: Número máximo de ofertas a intentar obtener.

        Returns:
            Una lista de diccionarios, cada uno representando una oferta básica
            (suficiente para luego obtener detalles si es necesario, o a veces ya
             contiene bastante información).
        """
        print(f"Buscando ofertas en InfoJobs API: query='{query}', location='{location}'")
        endpoint = "7/offer" # Endpoint de búsqueda (versión 7 es común)
        all_offers_data = []
        page = 1

        # Mapeo simple de ejemplo (¡necesita ser más robusto!)
        # InfoJobs usa códigos específicos para provincias.
        # Ver https://developer.infojobs.net/listados-valores/listado-de-provincias/page.html
        # Tendrías que crear un diccionario de mapeo más completo.
        location_mapping = {
            "madrid": "madrid",
            "barcelona": "barcelona",
            "asturias": "asturias",
            "valencia": "valencia",
            "sevilla": "sevilla",
            # ... añadir más provincias/códigos ...
        }
        province_key = location_mapping.get(location.lower(), location) # Usa el input si no hay mapeo

        while len(all_offers_data) < max_offers:
            params = {
                'q': query,
                'province': province_key,
                'page': page,
                'maxResults': min(self.MAX_RESULTS_PER_PAGE, max_offers - len(all_offers_data)),
                # Otros parámetros útiles: 'category', 'contractType', 'salaryMin', 'salaryMax', 'order'
            }
            print(f"  -> Solicitando página {page}...")
            data = self._make_request(endpoint, params)

            if not data or not data.get('items'):
                print(f"  -> No se obtuvieron más ofertas (página {page}) o hubo un error.")
                break # Salir si no hay datos o error

            offers_in_page = data.get('items', [])
            total_results = data.get('totalResults', 0)
            print(f"  -> Página {page}: {len(offers_in_page)} ofertas encontradas (Total: {total_results})")

            for offer_item in offers_in_page:
                # Extraer y formatear los datos necesarios para guardar en BD
                # La API de búsqueda ya puede devolver muchos detalles útiles
                formatted_offer = self._format_offer_data(offer_item)
                if formatted_offer:
                     all_offers_data.append(formatted_offer)

            # Comprobar si hay más páginas
            current_results = data.get('currentResults', len(offers_in_page))
            total_pages = data.get('totalPages', page) # A veces la API devuelve esto
            if page >= total_pages or len(all_offers_data) >= max_offers or current_results < params['maxResults']:
                print("  -> Última página alcanzada o límite de ofertas.")
                break

            page += 1
            time.sleep(0.5) # Pausa corta entre páginas para ser respetuoso con la API

        print(f"Búsqueda en InfoJobs finalizada. Total ofertas formateadas: {len(all_offers_data)}")
        return all_offers_data

    def _format_offer_data(self, offer_data):
        """Formatea los datos de una oferta de la API al formato esperado."""
        try:
            # Mapear campos de la API a los campos de nuestro modelo JobOffer
            # Los nombres exactos de los campos pueden variar ligeramente entre versiones de la API
            formatted = {
                'title': offer_data.get('title'),
                'company': offer_data.get('author', {}).get('name'), # A veces está en 'author'
                'location': offer_data.get('province', {}).get('value'),
                'description': offer_data.get('description', offer_data.get('detail',{}).get('description')), # Descripción puede variar
                'salary_range': offer_data.get('salaryDescription'),
                'publication_date': offer_data.get('published', '').split('T')[0] if offer_data.get('published') else None, # Formato YYYY-MM-DD
                'url': offer_data.get('link'), # URL de la oferta en InfoJobs
                'source_name': self.source_name,
                'applicants_count': offer_data.get('applications'), # Número de inscritos si está disponible
                'required_skills': [skill.get('skill') for skill in offer_data.get('skillsList', []) if skill.get('skill')],
                'contract_type': offer_data.get('contractType', {}).get('value'),
                'workday': offer_data.get('workDay', {}).get('value'),
                'experience_min': offer_data.get('experienceMin', {}).get('value'),
                'raw_data': offer_data # Guardar los datos originales por si acaso
            }
            # Validar datos mínimos
            if not formatted['title'] or not formatted['url']:
                print(f"Advertencia: Oferta de InfoJobs descartada por faltar título o URL. ID: {offer_data.get('id')}")
                return None
            return formatted
        except Exception as e:
            print(f"Error formateando datos de oferta de InfoJobs (ID: {offer_data.get('id', 'N/A')}): {e}")
            return None

    def parse_offer_detail(self, url):
        """
        Normalmente no necesitamos obtener detalles adicionales si la búsqueda ya es rica.
        Si fuera necesario, aquí se haría una petición al endpoint de detalle /offer/{id}.
        """
        print(f"INFO: La API de búsqueda de InfoJobs ya suele proporcionar suficientes detalles. No se solicitará detalle para {url}")
        # Si necesitaras detalles, extraerías el ID de la URL o del item de búsqueda
        # y harías una petición a `7/offer/{offer_id}`
        return None # Devolvemos None porque la lógica principal está en fetch_offers

    def run(self, query="desarrollador", location="Madrid", max_offers=100):
        """Ejecuta la obtención de ofertas desde la API."""
        return self.fetch_offers(query, location, max_offers)