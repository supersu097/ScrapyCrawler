# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class ZhugefangOldItem(scrapy.Item):
    # define the fields for your item here like:
    # name = Field()
    # 下面的字段前缀comm_为楼盘之意, 同此前爬虫中的building_前缀,
    # 此处效仿诸葛房域名本身的二级目录名 community/
    # ---------------------------楼盘详情通用部分-------------------------
    comm_name = Field()  # 楼盘名称
    comm_addr = Field()
    comm_price = Field()

    # ---------------------------楼盘详情基础信息-------------------------
    const_era = Field()  # 建造年代
    property_desc = Field()  # 产权描述
    plot_ratio = Field()  # 容积率
    greening_ratio = Field()  # 绿化率
    buildings_amount = Field()  # 楼栋总数
    houses_amount = Field()  # 房屋总数
    property_fee = Field()  # 物业费
    property_comp = Field()  # 物业公司
    dev_comp = Field()  # 开发商
    const_area = Field()  # 建筑面积
    const_type = Field()  # 建筑类型

    # ---------------------------数据库必要部分-------------------------
    city_id = Field()
    comm_from = Field()  # 诸葛房
    comm_url = Field()
    is_new = Field()  # 是二手房还是新房
    commit_time = Field()


class ZhugefangDetailUrlsItem(ZhugefangOldItem):
    pass
