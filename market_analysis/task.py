# market_analysis/tasks.py
from celery import shared_task
from .scraper import fetch_infojobs_offers

@shared_task
def update_job_offers():
    fetch_infojobs_offers()