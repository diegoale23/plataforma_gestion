# market_analysis/tasks.py
from celery import shared_task
from .scraper import fetch_infojobs_offers
from celery import shared_task
from .scraping.tecnoempleo_scraper import TecnoempleoScraper

@shared_task
def update_job_offers():
    fetch_infojobs_offers()
    

@shared_task
def scrape_tecnoempleo():
    scraper = TecnoempleoScraper()
    scraper.run(query="desarrollador", location="Madrid", max_offers=50)