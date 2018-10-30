# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json

class HezhinewsPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWriterPipeline(object):
    """
    参考: https://docs.scrapy.org/en/latest/topics/
    item-pipeline.html#write-items-to-a-json-file
    """

    def open_spider(self, spider):
        self.file = open('hezhi_news.jl', 'w+', encoding='utf-8')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item