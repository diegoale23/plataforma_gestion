# market_analysis/management/commands/scrape_tecnoempleo.py
from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from job_scraper.spiders.tecnoempleo_spider import TecnoempleoSpider

class Command(BaseCommand):
    help = 'Scrapea ofertas de Tecnoempleo'

    def handle(self, *args, **kwargs):
        process = CrawlerProcess()
        process.crawl(TecnoempleoSpider)
        process.start()