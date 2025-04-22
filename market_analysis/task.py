# market_analysis/task.py
from celery import shared_task
from .scraping.tecnoempleo_scraper import TecnoempleoScraper
from .scraping.infojobs_scraper import InfojobsScraper

@shared_task
def update_job_offers():
    # Scraping de Tecnoempleo
    tecnoempleo_scraper = TecnoempleoScraper()
    tecnoempleo_scraper.run(query="desarrollador", location="Madrid", max_offers=50)

@shared_task
def scrape_tecnoempleo():
    scraper = TecnoempleoScraper()
    scraper.run(query="desarrollador", location="Madrid", max_offers=50)

