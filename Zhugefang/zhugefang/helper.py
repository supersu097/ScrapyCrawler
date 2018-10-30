import logging
import os.path
import random
import sqlite3
import time
from logging import Logger
from typing import List
from urllib.parse import urlparse

import requests
from pymysql.cursors import DictCursor
from requests import Response

from .settings import ZHUGEFANG_CITY_ABBR_2_ID_MAPPING


class Helper(object):
    @property
    def logger(self) -> Logger:
        logger = logging.getLogger()
        if not logger.handlers:
            logger.setLevel('DEBUG')
            formatter = logging.Formatter(
                "%(filename)s - %(asctime)s - %(funcName)s - %(levelname)s -%(message)s",
                datefmt='%Y-%m-%d %H:%M:%S')
            console_handler = logging.StreamHandler()
            console_handler.setLevel('DEBUG')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        return logger

    @staticmethod
    def date_getter(style: str = 'Ymd_HMS') -> str:
        def builder(specific_format: str) -> str:
            return time.strftime(specific_format, time.localtime())

        if style == 'Ymd':
            return builder("%Y-%m-%d")
        elif style == 'Ymd_HMS':
            return builder("%Y-%m-%d %H:%M:%S")
        else:
            raise ValueError('The style of {} you '
                             'specified is not predefined'.format(style))

    @staticmethod
    def avoid_anti_crawling(upper_limit_time: int, desc: str, spider_oj) -> None:
        """
        简单的方法来防止目标网站启用反爬策略
        :param upper_limit_time: sleep时间上限，单位为秒
        :param desc: log里面的具体描述信息
        :param spider_oj: 继承了框架Spider类的类的实例对象
        :return:
        """
        if upper_limit_time != 0:
            seconds = random.choice([i / 10 for i in range(10, upper_limit_time * 10)])
            spider_oj.log("Sleep for {time}s {desc}...".format(time=seconds, desc=desc))
            time.sleep(seconds)

    @staticmethod
    def get_city_id_by_url(url) -> int:
        """
        通过城市url得到其id
        :return:
        """
        city_abbr: str = urlparse(url).netloc.split('.')[0]
        city_id: int = ZHUGEFANG_CITY_ABBR_2_ID_MAPPING[city_abbr]
        return city_id


class Filter(object):
    def __init__(self, cur_: DictCursor, platform_code: int):
        self.cur_: DictCursor = cur_
        self.platform_code = platform_code

    def fetch_urls_from_detail_url_tb(self) -> List[str]:
        # TODO 测试完不要忘记移除limit限制  LIMIT 5
        original_rows_sql: str = """SELECT building_url
                                       FROM python_detail_urls
                                       WHERE building_from='{}';""".format(self.platform_code)
        self.cur_.execute(original_rows_sql)
        query_results: List[dict] = self.cur_.fetchall()
        return [_['building_url'] for _ in query_results]

    def fetch_urls_from_project_tb(self) -> List[str]:
        """
        从python_project表中读取已经成功爬过数据的楼盘的url
        :return:
        """
        # TODO 测试完不要忘记移除limit限制  LIMIT 5
        crawled_urls_sql: str = """SELECT building_url
                                       FROM python_project
                                       WHERE building_from ={};""".format(self.platform_code)
        self.cur_.execute(crawled_urls_sql)
        query_results: List[dict] = self.cur_.fetchall()
        return [_['building_url'] for _ in query_results]

    def waiting_2_crawl_selector(self):
        """
        如果list()该方法后返回空列表则说明所有楼盘均已爬完,
        本方法存在很隐蔽的状态,实在不符合Python显胜于隐的哲学,
        很容易给下游调用方挖坑,有待改进
        :return:
        """
        crawled_urls: List[str] = self.fetch_urls_from_project_tb()
        original_urls: List[str] = self.fetch_urls_from_detail_url_tb()
        if not crawled_urls:
            return original_urls
        else:
            for ori_one in original_urls:
                # 如果全部都不在相当于把original_urls最终返回了
                if ori_one not in crawled_urls:
                    yield ori_one


class Proxy(object):
    APP_ID: str = '160086177418212989776'
    ORDER_ID: str = 'BM3J1600861787349743'
    PROXY_API: str = 'http://proxy.horocn.com/api/free-proxy'

    def __init__(self, *,
                 ip_num_one_time: str = '10',
                 response_format: str = 'text',
                 loc_name: str = '中国'):
        self.final_proxy_api: str = (self.PROXY_API
                                     + '?app_id=' + self.APP_ID
                                     + '&num=' + ip_num_one_time
                                     + '&format=' + response_format
                                     + '&loc_name=' + loc_name)

    def build_proxy_ip_pool(self) -> List[str]:
        proxy_api_response: Response = requests.get(self.final_proxy_api)
        proxy_api_urls: List[str] = proxy_api_response.text.split('\n')
        return proxy_api_urls


class SqliteDB(object):
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    DB_PATH: str = os.path.join(BASE_DIR, 'proxy.db')
    proxy = Proxy()
    helper = Helper()

    def __init__(self):
        """
        参考:
        https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory
        """

        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        self.conn = sqlite3.connect(self.DB_PATH)
        self.conn.row_factory = dict_factory
        self.cur = self.conn.cursor()

    def create_ip_pool_table(self):
        create_sql: str = """CREATE TABLE ip_pool
        (id INTEGER PRIMARY KEY     AUTOINCREMENT,
        host_port      TEXT    NOT NULL,
        is_ok          INT(1)  DEFAULT 1,
        retry_time     INT(1)  DEFAULT 0);"""
        try:
            self.cur.execute(create_sql)
            self.conn.commit()
            self.helper.logger.debug('The table of ip_pool has created.')
        except sqlite3.Error as e:
            self.helper.logger.debug(str(e))
            self.cur.close()
            self.conn.close()
            self.helper.logger.debug('The db conn has closed.')
        finally:
            self.cur.close()
            self.conn.close()
            self.helper.logger.debug('The db conn has closed.')

    def validate_proxy_ip_by_baidu(self, proxy_ip_pool: List[str]):
        baidu_url: str = 'https://www.baidu.com/'
        for proxy_ip in proxy_ip_pool:
            response: Response = requests.get(baidu_url, timeout=3,
                                              proxies={'https': 'https://' + proxy_ip})
            if not response.ok:
                self.update_is_ok_field(proxy_ip)
                self.helper.logger.debug('''This proxy ip of {ip}
                 mostly can not use, marked as invalid.'''.format(ip=proxy_ip))

    def first_time_2_save_proxy_ip_into_db(self):
        ip_pool: List[str] = self.proxy.build_proxy_ip_pool()
        try:
            for ip in ip_pool:
                insert_sql: str = """
                INSERT INTO main.ip_pool (host_port)
                VALUES ('{host_port}');""".format(host_port=ip)
                self.helper.logger.debug('Insert sql prepared: ' + insert_sql)
                self.cur.execute(insert_sql)
            self.conn.commit()
            self.helper.logger.debug('Done for first time saving the proxy ip pool in DB.')
            self.validate_proxy_ip_by_baidu(ip_pool)
        except sqlite3.Error:
            self.cur.close()
            self.conn.close()

    def update_ip_pool_tb(self):
        new_ip_pool: List[str] = self.proxy.build_proxy_ip_pool()
        id_num: int = 1
        try:
            for ip in new_ip_pool:
                update_sql: str = """UPDATE main.ip_pool 
                                     SET host_port ='{ip}', is_ok=1 
                                     WHERE id ={id}""".format(ip=ip, id=id_num)
                self.helper.logger.debug('Update sql prepared: ' + update_sql)
                self.cur.execute(update_sql)
                id_num: int = id_num + 1
            self.conn.commit()
            self.helper.logger.debug('Done for updating ip pool table.')
            self.validate_proxy_ip_by_baidu(new_ip_pool)
        except sqlite3.Error as e:
            self.helper.logger.debug(str(e))
            self.conn.rollback()
            self.cur.close()
            self.conn.close()

    def update_is_ok_field(self, proxy_ip):
        """
        用于目标网站通过代理访问失败时更新代理ip为不可用状态
        :param proxy_ip:
        :return:
        """
        update_sql: str = """
        UPDATE main.ip_pool SET is_ok =0 WHERE host_port='{}';
        """.format(proxy_ip)
        try:
            self.helper.logger.debug('Update sql prepared: ' + update_sql)
            self.cur.execute(update_sql)
            self.conn.commit()
            self.helper.logger.debug('Done for updating the field of is_ok.')
        except sqlite3.Error:
            self.conn.rollback()
            self.cur.close()
            self.conn.close()

    def fetch_value_of_retry_time(self, proxy_ip: str) -> int:
        query_sql: str = """SELECT retry_time 
                            FROM main.ip_pool 
                            WHERE host_port='{}';""".format(proxy_ip)
        self.cur.execute(query_sql)
        retry_time: int = self.cur.fetchone()['retry_time']
        return retry_time

    def update_retry_time_field(self, proxy_ip: str):
        update_sql: str = """
                UPDATE main.ip_pool 
                SET retry_time ={retry_num} 
                WHERE host_port='{ip}';
                """.format(ip=proxy_ip,
                           retry_num=self.fetch_value_of_retry_time(proxy_ip) + 1)
        try:
            self.helper.logger.debug('Update sql prepared: ' + update_sql)
            self.cur.execute(update_sql)
            self.conn.commit()
            self.helper.logger.debug('Done for updating the field of retry_time.')
        except sqlite3.Error:
            self.conn.rollback()
            self.cur.close()
            self.conn.close()

    def fetch_one_proxy_ip(self) -> str:
        try:
            initial_query: str = """SELECT host_port FROM main.ip_pool;"""
            self.cur.execute(initial_query)
            one_query_result: List[str] = self.cur.fetchone()
            if one_query_result is None:
                # 第一次填充数据库
                self.first_time_2_save_proxy_ip_into_db()

            query_sql: str = """
            SELECT host_port, is_ok FROM main.ip_pool"""
            self.cur.execute(query_sql)
            query_results: List[dict] = self.cur.fetchall()
            for result in query_results:
                is_ok: str = result['is_ok']
                proxy_host_port: str = result['host_port']
                if is_ok == 1:
                    return proxy_host_port
        except sqlite3.Error:
            self.conn.rollback()
            self.cur.close()
            self.conn.close()
