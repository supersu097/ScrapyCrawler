# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
from openpyxl import Workbook

class YellowpagesPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWriterPipeline(object):
    """
    参考: https://docs.scrapy.org/en/latest/topics/
    item-pipeline.html#write-items-to-a-json-file
    """

    def open_spider(self, spider):
        self.file = open('yellowpages.jl', 'w+', encoding='utf-8')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item


class ExcelWriterPipeline(object):
    def __init__(self):
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(['Company Name', 'Company Phone Number', 'Company Website'])

    def process_item(self, item, spider):
        """
        重写框架方法
        :param item: 由框架自动传入
        :param spider: 由框架自动传入
        :return:
        """
        self.ws.append([item['company_name'], item['phone_number'], item['website']])
        self.wb.save('yellowpages.xlsx')
        return item