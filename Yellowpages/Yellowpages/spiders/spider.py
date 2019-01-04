# -*- coding: utf-8 -*-
import scrapy
from bs4 import BeautifulSoup
from ..items import YellowpagesItem

class Yellowpages(scrapy.Spider):
    name = 'yellowpages'
    allowed_domains = ['yellowpages.com']
    item = YellowpagesItem()

    def start_requests(self):
        url = 'https://www.yellowpages.com/search?search_terms' \
              '=mortgage%20lender&geo_location_terms=Miami%2C%20FL&page='
        urls = [url + str(_) for _ in range(2, 22)]
        for url in urls:
            yield scrapy.Request(url, callback=self.list_page_parser)

    def get_website(self, company):
        website = company.select_one('a.track-visit-website')
        if website is None:
            return ''
        else:
            return website.get('href')

    def list_page_parser(self, response):
        entire_page_soup = BeautifulSoup(response.text, 'lxml')
        company_list = entire_page_soup.select('div.v-card')
        for company in company_list:
            self.item['company_name'] = company.select_one('a.business-name span').get_text()
            self.item['phone_number'] = company.select_one('div.phones.phone.primary').get_text()
            self.item['website'] = self.get_website(company)
            yield self.item
