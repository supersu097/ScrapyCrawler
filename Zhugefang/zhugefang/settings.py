# -*- coding: utf-8 -*-

from pymysql.cursors import DictCursor

# Scrapy settings for zhugefang project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'zhugefang'

SPIDER_MODULES = ['zhugefang.spiders']
NEWSPIDER_MODULE = 'zhugefang.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = generate_user_agent(os='win')

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 200
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1
CONCURRENT_ITEMS = 1

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Accept-Encoding': 'gzip, deflate'
}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'zhugefang.middlewares.ZhugefangSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'zhugefang.middlewares.ChromeDownloaderMiddleware': 910,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # 'zhugefang.pipelines.JsonWriterPipeline': 300,
    'scrapy.pipelines.images.ImagesPipeline': 1,
    'zhugefang.pipelines.MysqlCleanerPipeline': 100,
    'zhugefang.pipelines.MysqlBackendPipeline': 200,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 30
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 90
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.1
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# FEED_FORMAT = 'jsonlines'
# FEED_EXPORT_ENCODING = 'utf-8'

ALIYUN_TEST_DB_SETTING = {'host': '',
                          'user': 'root',
                          'port': 3366,
                          'passwd': '',
                          'charset': 'utf8mb4',
                          'db': '',
                          'autocommit': False,
                          'cursorclass': DictCursor}

ZHUGEFANG_CITY_ABBR_2_ID_MAPPING = {
    # 'hf': 340100,  # he_fei
    'wh': 420100,  # wu_han
    # 'zz': 410100,  # zheng_zhou
    # 'cd': 510100,  # cheng_du
    # 'tj': 120000,  # tian_jin
    # 'jn': 370100,  # ji_nan
    # 'xz': 320300,  # xu_zhou
    # 'hz': 330100,  # hang_zhou
    # 'nj': 320100,  # nan_jing
    # 'cq': 500000,  # chong_qing
    # 'nc': 360100,  # nan_chang
    # 'cs': 430100,  # chang_sha
    # 'nn': 450100,  # nan_ning
    # 'gy': 520100,  # gui_yang
}

PLATFORM_CODE = 4  # 诸葛房

# RETRY_ENABLED = True
