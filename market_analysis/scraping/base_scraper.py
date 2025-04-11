# market_analysis/scraping/base_scraper.py
import abc # Abstract Base Class

class BaseScraper(abc.ABC):
    def __init__(self, source_name, base_url):
        self.source_name = source_name
        self.base_url = base_url
        # Common headers can be defined here if needed
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
