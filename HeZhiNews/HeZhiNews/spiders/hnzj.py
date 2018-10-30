# -*- coding: utf-8 -*-
import re
from typing import List

import scrapy
from bs4 import BeautifulSoup

from HeZhiNews.items import HezhinewsItem


class HnzjSpider(scrapy.Spider):
    name = 'hnzj'
    news_item = HezhinewsItem()

    @staticmethod
    def render_next_page_url(page_num):
        return 'http://www.hnzj.edu.cn/xyxw/{}.htm'.format(page_num)

    @staticmethod
    def render_news_page_url(news_page_href):
        broken_href = 'http://www.hnzj.edu.cn/' + news_page_href
        return broken_href.replace('/..', '')

    def start_requests(self):
        urls = ['http://www.hnzj.edu.cn/xyxw.htm']
        for url in urls:
            yield scrapy.Request(url, callback=self.list_page_parser)

    def list_page_parser(self, response):
        entire_page_soup = BeautifulSoup(response.text, 'lxml')
        all_news_tr_soup = entire_page_soup.find_all(id=re.compile('line\d*_\d+'))
        # 跟进新闻详情页
        for news in all_news_tr_soup:
            href = news.select_one('a').get('href')
            yield scrapy.Request(self.render_news_page_url(href),
                                 callback=self.detail_page_parser)

        # find_all('a','Next')同时返回两个BeautifulSoup类型的a Tag
        next_page: List[BeautifulSoup] = entire_page_soup.find_all('a', 'Next')
        if next_page:
            next_page_href = next_page[0].get('href')
            next_page_num_regx = re.search('(\d+)', next_page_href)
            next_page_num = next_page_num_regx.group(1)
            next_page_abs_url = self.render_next_page_url(next_page_num)
            yield scrapy.Request(next_page_abs_url,
                                 callback=self.list_page_parser)

    def detail_page_parser(self, response):
        news_content_page_source = response.text
        news_content_page_soup = BeautifulSoup(news_content_page_source, 'lxml')
        yield {
            'news_title': news_content_page_soup.select_one('td.titlestyle68794').get_text(),
            'news_date': news_content_page_soup.select_one('span.timestyle68794').get_text(),
            'news_author': news_content_page_soup.select_one('span.authorstyle68794').get_text()
        }
