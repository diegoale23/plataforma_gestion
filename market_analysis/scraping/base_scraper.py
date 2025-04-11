# market_analysis/scraping/base_scraper.py
import abc # Abstract Base Class

class BaseScraper(abc.ABC):
    def __init__(self, source_name, base_url):
        self.source_name = source_name
        self.base_url = base_url
        # Common headers can be defined here if needed
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    @abc.abstractmethod
    def fetch_offers(self, query="desarrollador", location="España", max_offers=50):
        """
        Método abstracto para buscar y extraer URLs/datos básicos de ofertas.
        Debería devolver una lista de URLs o una lista de diccionarios con datos básicos.
        """
        pass

    @abc.abstractmethod
    def parse_offer_detail(self, url_or_data):
        """
        Método abstracto para extraer detalles de una oferta específica.
        Puede recibir una URL o datos básicos de la fase fetch_offers.
        Debería devolver un diccionario con los datos detallados de la oferta o None si falla.
        """
        pass

    @abc.abstractmethod
    def run(self, query="desarrollador", location="España", max_offers=50):
        """
        Método abstracto para ejecutar el proceso completo de obtención de datos
        para esta fuente. Debería devolver una lista de diccionarios, donde
        cada diccionario representa una oferta formateada lista para guardar en la BD.
        """
        pass