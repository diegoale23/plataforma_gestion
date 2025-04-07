# job_scraper/items.py
import scrapy

class JobItem(scrapy.Item):
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    url = scrapy.Field()