import re
from typing import List, Iterator

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor
from pymysql import MySQLError
import scrapy
from bs4 import BeautifulSoup as Soup
from scrapy import Item
from scrapy import Request
from scrapy.http import HtmlResponse
from ..helper import Helper, Filter
from ..items import ZhugefangDetailUrlsItem
from ..settings import ALIYUN_TEST_DB_SETTING
from ..settings import PLATFORM_CODE
from ..settings import ZHUGEFANG_CITY_ABBR_2_ID_MAPPING


class ZhugeDetailUrlsCollector(scrapy.Spider):
    name: str = 'zhuge_urls'
    detail_item: Item = ZhugefangDetailUrlsItem()
    helper: Helper = Helper()
    conn: Connection = pymysql.connect(**ALIYUN_TEST_DB_SETTING)
    cursor: DictCursor = conn.cursor()

    def start_requests(self) -> Iterator[Request]:
        zhugefang_city_urls: List[str] = ['http://{}.house.zhuge.com/community'.format(_)
                                          for _ in ZHUGEFANG_CITY_ABBR_2_ID_MAPPING]
        for url in zhugefang_city_urls:
            # 注意callback要赋值的是函数对象的引用而不是其本身
            yield scrapy.Request(url, callback=self.se_res_parser)

    # 搜索结果页每个楼盘的解析器
    def se_res_parser(self, response: HtmlResponse):
        """
        参考: https://docs.scrapy.org/en/latest/intro/tutorial.html#more-examples-and-patterns
        :param response: 由框架请求完每一个url返回的response通过异步回调传入
        :return:
        """
        try:
            filter_: Filter = Filter(self.cursor, PLATFORM_CODE)
            all_ori_urls: List[str] = filter_.fetch_urls_from_detail_url_tb()
        except MySQLError:
            import traceback
            traceback.print_exc()
            self.cursor.close()
            self.conn.close()
            self.log('The DB connection has closed!')

        soup_god: Soup = Soup(response.text, 'lxml')
        # 搜索结果页所有的楼盘a标签soup类型集合
        all_comm_soup: List[Soup] = soup_god.select('p.house-name a')
        for comm in all_comm_soup:
            # 通过框架方法urljoin()生成完整url
            href: str = response.urljoin(comm.get('href'))
            if href in all_ori_urls:
                self.log('Hit the crawled community of {}!'.format(href))
                continue
            self.detail_item['comm_url'] = href
            self.detail_item['city_id'] = self.helper.get_city_id_by_url(href)
            self.detail_item['commit_time'] = self.helper.date_getter()
            self.detail_item['comm_from'] = PLATFORM_CODE
            self.detail_item['is_new'] = 0
            yield self.detail_item

        next_page_wrapper = re.search(r'尾页(.*)下一页', response.text)
        if next_page_wrapper is not None:
            next_page_wrapper_txt: str = next_page_wrapper.group().replace('&quot;', '')
            next_page_reg = re.search(r'href=(.+) class', next_page_wrapper_txt)
            if next_page_reg is not None:
                next_page: str = response.urljoin(next_page_reg.group(1))
                yield scrapy.Request(next_page, callback=self.se_res_parser)
                self.helper.avoid_anti_crawling(20, 'before the next searching page', self)
