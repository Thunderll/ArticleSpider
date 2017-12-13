# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb'\
            'Kit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
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
        i = {}
        #i['domain_id'] = response.xpath('//input[@id="sid"]/@value').extract()
        #i['name'] = response.xpath('//div[@id="name"]').extract()
        #i['description'] = response.xpath('//div[@id="description"]').extract()
        return i

