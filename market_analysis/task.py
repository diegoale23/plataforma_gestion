# market_analysis/tasks.py
from celery import shared_task
from .scraping.tecnoempleo_scraper import TecnoempleoScraper
from .scraping.infojobs_scraper import InfojobsScraper

@shared_task
def update_job_offers():
    # Scraping de InfoJobs
    infojobs_scraper = InfojobsScraper()
    infojobs_scraper.run(query="desarrollador", location="España", max_offers=50)
    
    # Scraping de Tecnoempleo
    tecnoempleo_scraper = TecnoempleoScraper()
    tecnoempleo_scraper.run(query="desarrollador", location="Madrid", max_offers=50)

@shared_task
def scrape_tecnoempleo():
    scraper = TecnoempleoScraper()
    scraper.run(query="desarrollador", location="Madrid", max_offers=50)

@shared_task
def scrape_infojobs():
    scraper = InfojobsScraper()
    scraper.run(query="desarrollador", location="España", max_offers=50)