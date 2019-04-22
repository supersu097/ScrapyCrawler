# -*- coding: utf-8 -*-
import scrapy


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['http://blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        pass

    def parse_detail(self, response):
        title = response.xpath('//*[@id="post-114666"]/div[1]/h1/text()').extract()[0]
        pub_date = response.xpath('//*[@id="post-114666"]/div[2]/p/text()').extract()[0].strip().replace(' ·','')
        

