# job_scraper/spiders/tecnoempleo_spider.py
import scrapy
from ..items import JobItem

class TecnoempleoSpider(scrapy.Spider):
    name = 'tecnoempleo'
    start_urls = ['https://www.tecnoempleo.com/ofertas-empleo/?tecnologia=python']

    def parse(self, response):
        for offer in response.css('.offer'):
            item = JobItem()
            item['title'] = offer.css('h2::text').get()
            item['company'] = offer.css('.company::text').get()
            item['location'] = offer.css('.location::text').get()
            item['url'] = offer.css('a::attr(href)').get()
            yield item

        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)