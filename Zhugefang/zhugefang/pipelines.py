# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json

import pymysql
from pymysql import MySQLError
from pymysql.connections import Connection
from scrapy import Item, Spider

from .items import ZhugefangOldItem
from .items import ZhugefangDetailUrlsItem
from .settings import ALIYUN_TEST_DB_SETTING


class ZhugefangPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWriterPipeline(object):
    """
    参考: https://docs.scrapy.org/en/latest/topics/
    item-pipeline.html#write-items-to-a-json-file
    """

    def open_spider(self, spider):
        self.file = open('zhugefang.jl', 'w+', encoding='utf-8')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item


class MysqlCleanerPipeline(object):
    @staticmethod
    def process_item(item: Item, spider: Spider):
        for key in item:
            if key == 'const_era' and not item['const_era']:
                item['const_era'] = '0001-01-01'
            elif key == 'property_fee' and not item['property_fee']:
                item['property_fee'] = 0.0
            elif key == 'const_area' and not item['const_area']:
                item['const_area'] = 0
            elif key == 'houses_amount' and not item['houses_amount']:
                item['houses_amount'] = 0
            elif key == 'buildings_amount' and not item['buildings_amount']:
                item['buildings_amount'] = 0
            # 后面的字段类型本身为varchar的可以不用处理了
        return item


class MysqlBackendPipeline(object):
    """
    参考: https://blog.csdn.net/yancey_blog/article/details/53895821
    """

    def __init__(self):
        self.conn: Connection = pymysql.connect(**ALIYUN_TEST_DB_SETTING)
        self.cursor = self.conn.cursor()

    def process_item(self, item: Item, spider: Spider):
        """
        重写框架方法
        :param item: 由框架自动传入
        :param spider: 由框架自动传入
        :return:
        """
        if item.__class__ == ZhugefangDetailUrlsItem:
            insert_sql: str = """
            INSERT INTO python_detail_urls
            (building_url, city_id,
            building_from, is_new, commit_time)
            values 
            ('{building_url}','{city_id}',
            '{building_from}','{is_new}','{commit_time}')
            """.format(building_url=item['comm_url'],
                       city_id=item['city_id'],
                       building_from=item['comm_from'],
                       is_new=item['is_new'],
                       commit_time=item['commit_time'])
            try:
                spider.log('SQL Prepared: ' + insert_sql)
                self.cursor.execute(insert_sql)
            except MySQLError:
                import traceback
                traceback.print_exc()
                self.cursor.close()
                self.conn.close()
                spider.log('The DB connection has closed!')
            else:
                self.conn.commit()
            return item
        elif item.__class__ == ZhugefangOldItem:
            insert_sql: str = """INSERT INTO python_project 
            (pj_name, addr, avg_price,
            
            const_era, property_desc,
            plot_ratio, greening,
            buildings_amount, houses_amount, 
            property_price, property,
            develop, const_area, building_type,

            city_id, building_from,
            building_url, is_new, commit_time)
            VALUES 
            ('{pj_name}', '{addr}', '{avg_price}',

            '{const_era}','{property_desc}',
            '{plot_ratio}','{greening}',
            '{buildings_amount}','{houses_amount}',
            '{property_price}','{property}',
            '{develop}','{const_area}','{building_type}',
            
            '{city_id}','{building_from}',
            '{building_url}','{is_new}','{commit_time}')""".format(
                pj_name=item['comm_name'],
                addr=item['comm_addr'],
                avg_price=item['comm_price'],

                const_era=item['const_era'],
                property_desc=item['property_desc'],
                plot_ratio=item['plot_ratio'],
                greening=item['greening_ratio'],
                buildings_amount=item['buildings_amount'],
                houses_amount=item['houses_amount'],
                property_price=item['property_fee'],
                property=item['property_comp'],
                develop=item['dev_comp'],
                const_area=item['const_area'],
                building_type=item['const_type'],

                city_id=item['city_id'],
                building_from=item['comm_from'],
                building_url=item['comm_url'],
                is_new=item['is_new'],
                commit_time=item['commit_time'])

            try:
                spider.log('SQL Prepared: ' + insert_sql)
                self.cursor.execute(insert_sql)
            except MySQLError:
                import traceback
                traceback.print_exc()
                self.cursor.close()
                self.conn.close()
                spider.log('The DB connection has closed!')
            else:
                self.conn.commit()
            return item

    def close_spider(self, spider):
        """
        重写框架方法
        :param spider:
        :return:
        """
        self.conn.commit()
