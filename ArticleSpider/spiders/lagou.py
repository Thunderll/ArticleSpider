# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.loader import ItemLoader

from items import LagouJobItem, LagouItemLoader
from utils.commen import get_md5


def get_cookies():
    # 由于第一次爬的时候没写headers导致被禁,所以手动提取了一个
    # cookie保存在本地
    with open('lagou_cookies.txt', 'r') as f:
        cookies = f.read()
        return str(cookies)


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']

    custom_settings = {
        'COOKIES_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': {
            'HOST': 'www.lagou.com',
            'Referer': 'https://www.lagou.com/',
            'Cookie': get_cookies(),
        }
    }

    rules = (
        Rule(LinkExtractor(allow=(r'zhaopin/.*',)), follow=True),
        Rule(LinkExtractor(allow=(r'gongsi/j\d+.html',)), follow=True),
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_job', follow=True),
    )

    def parse_job(self, response):
        # 解析拉钩网的职位
        item_loader = LagouItemLoader(item=LagouJobItem(), response=response)
        item_loader.add_xpath('title', "//div[@class='job-name']/@title")
        item_loader.add_value('url', response.url)
        item_loader.add_value('url_object_id', get_md5(response.url))
        item_loader.add_xpath('salary', "//dd[@class='job_request']//span[@class='salary']/text()")
        item_loader.add_xpath('job_city', "//dd[@class='job_request']/p/span[2]/text()")
        item_loader.add_xpath('work_years', "//dd[@class='job_request']/p/span[3]/text()")
        item_loader.add_xpath('degree_need', "//dd[@class='job_request']/p/span[4]/text()")
        item_loader.add_xpath('job_type', "//dd[@class='job_request']/p/span[5]/text()")
        item_loader.add_xpath('publish_time', "//p[@class='publish_time']/text()")
        item_loader.add_xpath('tags', "//ul[contains(@class,'position-label')]/li/text()")
        item_loader.add_xpath('job_advantage', "//span[@class='advantage']/following-sibling::p/text()")
        item_loader.add_xpath('job_desc', "string(//dd[@class='job_bt']/div)")
        item_loader.add_xpath('job_addr', "//div[@class='work_addr']")
        item_loader.add_xpath('company_name', "//dl[@id='job_company']/dt/a/img/@alt")
        item_loader.add_xpath('company_url', "//ul[@class='c_feature']/li[last()]/a/@href")
        item_loader.add_value('crawl_time', datetime.now())

        job_item = item_loader.load_item()
        return job_item

