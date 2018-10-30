# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import os
from os.path import join as os_join

from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.http.request import Request
from scrapy import Spider
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from user_agent import generate_user_agent

from .helper import SqliteDB, Helper


class ZhugefangSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ZhugefangDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ChromeDownloaderMiddleware(object):
    """
     实现参考：
     https://blog.csdn.net/JavaLixy/article/details/77874715
     https://intoli.com/blog/running-selenium-with-headless-chrome/
     https://sites.google.com/a/chromium.org/chromedriver/capabilities
     https://blog.csdn.net/showmax99/article/details/51063937
     """
    helper: Helper = Helper()
    CURR_PATH = os.path.abspath('.')
    LAST_PATH = os.path.abspath(os_join(CURR_PATH, os.pardir))
    CHROME_DRIVER_PATH: str = os_join(LAST_PATH, 'bin/chromedriver-2.38')
    IS_CHROME_RUNNING_IN_HEADLESS_MODE = False

    def __init__(self):
        self.options: ChromeOptions = ChromeOptions()
        # 实现禁止图片加载参考(headless模式下截粗的图还是会有图片):
        # https://stackoverflow.com/questions/28070315/
        # python-disable-images-in-selenium-google-chromedriver
        # https://www.zhihu.com/question/35547395
        chrome_prefs: dict = {'profile.default_content_setting_values': {'images': 2}}
        if self.IS_CHROME_RUNNING_IN_HEADLESS_MODE:
            self.options.add_argument('headless')
        else:
            # 参考: https://stackoverflow.com/questions/35343090/
            # how-to-keep-opened-developer-tools-while-running-a-selenium-nightwatch-js-test
            self.options.add_argument('auto-open-devtools-for-tabs')
            self.options.add_argument('start-maximized')
        self.options.add_experimental_option("prefs", chrome_prefs)
        self.custom_ua: str = generate_user_agent(os='win')
        self.options.add_argument('user-agent=' + self.custom_ua)
        self.options.add_argument('lang=zh-CN')
        self.sqlite = SqliteDB()
        self.proxy_ip = self.sqlite.fetch_one_proxy_ip()
        if self.proxy_ip is None:
            self.helper.logger.debug('All proxy ip in the pool is invalid.')
            # 所有代理ip均不可用时更新DB代理池
            self.sqlite.update_ip_pool_tb()
            self.proxy_ip = self.sqlite.fetch_one_proxy_ip()
        self.options.add_argument('--proxy-server=http://' + self.proxy_ip)
        self.driver = ChromeDriver(executable_path=self.CHROME_DRIVER_PATH,
                                   chrome_options=self.options)

    def __del__(self):
        self.driver.close()

    def process_request(self, request: Request, spider: Spider):
        """
         参考: https://www.jianshu.com/p/d64b13a2322b
         https://docs.scrapy.org/en/latest/topics/downloader-
         middleware.html#writing-your-own-downloader-middleware
        :param request:
        :param spider:
        :return:
        """
        try:
            spider.log('Chrome driver begin...')
            self.driver.implicitly_wait(3)
            self.driver.set_script_timeout(5)
            self.driver.set_page_load_timeout(5)
            self.driver.get(request.url)  # 获取网页链接内容
            return HtmlResponse(url=request.url, body=self.driver.page_source,
                                request=request, encoding='utf-8',
                                status=200)  # 返回HTML数据
        except TimeoutException:
            self.sqlite.update_retry_time_field(self.proxy_ip)
            retry_times: int = self.sqlite.fetch_value_of_retry_time(self.proxy_ip)
            # 该代理ip重试两次后依旧超时,标记为无效
            if retry_times >= 2:
                self.sqlite.update_is_ok_field(self.proxy_ip)

            spider.log('Chrome driver end...')
            return HtmlResponse(url=request.url, request=request,
                                encoding='utf-8', status=500)
