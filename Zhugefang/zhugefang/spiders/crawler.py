import re
from typing import List, Iterator

import pymysql
from pymysql import MySQLError
from pymysql.connections import Connection
from pymysql.cursors import DictCursor
import scrapy
from bs4 import BeautifulSoup as Soup
from scrapy import Item
from scrapy import Request
from scrapy.http import HtmlResponse
from ..helper import Helper, Filter
from ..items import ZhugefangOldItem
from ..settings import ALIYUN_TEST_DB_SETTING
from ..settings import PLATFORM_CODE


class ZhugeCrawler(scrapy.Spider):
    """
    参考: https://docs.scrapy.org/en/latest/intro/tutorial.html#our-first-spider
    也可以采用https://docs.scrapy.org/en/latest/intro/tutorial.html
    #a-shortcut-to-the-start-requests-method这种方式实现,但是这种方式要重写框架默认的parse(),
    然后由框架自动回调,以上太过magical or tricky,简单说太过炫技不利于团队合作,更倾向于自定义parser
    然后手动回调, 此外这种方式也不符合Python推崇的哲学显胜于隐.
    """
    name: str = 'zhugefang'
    old_item: Item = ZhugefangOldItem()
    helper: Helper = Helper()
    conn: Connection = pymysql.connect(**ALIYUN_TEST_DB_SETTING)
    cursor: DictCursor = conn.cursor()

    def start_requests(self) -> Iterator[Request]:
        try:
            filter_: Filter = Filter(self.cursor, PLATFORM_CODE)
            start_urls = list(filter_.waiting_2_crawl_selector())
        except MySQLError:
            import traceback
            traceback.print_exc()
            self.cursor.close()
            self.conn.close()
            self.log('The DB connection has closed!')

        if not start_urls:
            self.log('All urls from project table have crawled!')
            exit(0)
        for url in start_urls:
            # 注意callback要赋值的是函数对象的引用而不是其本身
            yield scrapy.Request(url, callback=self.detail_page_parser)

    @classmethod
    def detail_page_parser(cls, response: HtmlResponse):
        """
        python正则提取中文参考
        https://blog.csdn.net/gatieme/article/details/43235791
        :param response:
        :return:
        """
        def basic_info_extracting_helper(field_name: str) -> str:
            # 基础信息列表为空的时候,说明该楼盘没有填写基础信息,直接返回''
            if not all_basics_list:
                return ''
            for basic in all_basics_list:
                field_name_on_page: str = basic.select_one('label').get_text().replace('：', '')
                field_corresponding_value: str = basic.select_one('div').get_text().strip()
                if field_name_on_page == field_name:
                    if field_corresponding_value == '--':
                        return ''
                    return field_corresponding_value
            # 说明该字段在当前楼盘不存在
            return ''

        def imgs_url_parser(urls_soup: List[Soup]) -> List[str]:
            """
            按照框架强制要求返回列表数据结构
            :param urls_soup:
            :return:
            """
            # 该小区暂未上传图片
            if not urls_soup:
                return []
            imgs_url: List[str] = []
            urls_soup_from_gaode: List[Soup] = urls_soup[0:3]
            urls_soup_from_fangtx: List[Soup] = urls_soup[4:]
            for gaode in urls_soup_from_gaode:
                url = gaode.get('style')

        soup_god: Soup = Soup(response.text, 'lxml')

        # ---------------------------楼盘详情通用部分-------------------------
        cls.old_item['comm_name'] = soup_god.select_one('h1.header_title').get_text()
        comm_addr_raw: str = soup_god.select_one('li.area_city').get_text()
        comm_addr_processed: str = ' '.join(re.findall(r'[\d\u4e00-\u9fff]+', comm_addr_raw))
        cls.old_item['comm_addr'] = comm_addr_processed
        cls.old_item['comm_price'] = soup_god.select_one('div.infor_total span').get_text()
        # image_urls为框架默认指定字段
        cls.old_item['image_urls'] = imgs_url_parser(soup_god.select('div.swiper-wrapper div.swiper-slide'))

        # ---------------------------楼盘详情基础信息-------------------------
        all_basics_list: List[Soup] = soup_god.select('ul.basic_list li')
        cls.old_item['const_era'] = basic_info_extracting_helper('建造年代')
        cls.old_item['property_desc'] = basic_info_extracting_helper('产权描述')
        cls.old_item['plot_ratio'] = basic_info_extracting_helper('容积率')
        cls.old_item['greening_ratio'] = basic_info_extracting_helper('绿化率')
        cls.old_item['buildings_amount'] = basic_info_extracting_helper('楼栋总数')
        cls.old_item['houses_amount'] = basic_info_extracting_helper('房屋总数')
        cls.old_item['property_fee'] = basic_info_extracting_helper('物业费用')
        cls.old_item['property_comp'] = basic_info_extracting_helper('物业公司')
        cls.old_item['dev_comp'] = basic_info_extracting_helper('开发商')
        cls.old_item['const_area'] = basic_info_extracting_helper('建筑面积')
        cls.old_item['const_type'] = basic_info_extracting_helper('建筑类型')

        # ---------------------------数据库必要部分-------------------------
        cls.old_item['comm_from'] = 4  # 诸葛房
        cls.old_item['comm_url'] = response.url
        cls.old_item['city_id'] = cls.helper.get_city_id_by_url(response.url)
        cls.old_item['is_new'] = 0
        cls.old_item['commit_time'] = cls.helper.date_getter()
        yield cls.old_item
