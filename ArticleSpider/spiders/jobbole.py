# -*- coding: utf-8 -*-

import re
import scrapy
from urllib import parse
import datetime
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy.xlib.pydispatch import dispatcher   #分发器
from scrapy import signals
from selenium import webdriver

from ArticleSpider.items import JobboleArticleItem, ArticleItemLoader
from ArticleSpider.utils.commen import get_md5


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/dfgsdfg/']

    # def __init__(self):
    #     self.brower = webdriver.Chrome(executable_path='E:/projects/spider/ArticleSpider/chromedriver.exe')
    #     super().__init__()
    #     # 连接信号
    #     dispatcher.connect(self.spider_closed, signals.spider_closed)
    #
    # def spider_closed(self, spider):
    #     # 当爬虫退出时关闭chrome
    #     print('spider closed')
    #     self.brower.quit()

    # 收集伯乐在线所有404的url以及404的页面数
    handle_httpstatus_list = [404]   #指定不过滤的状态码

    def __init__(self):
        self.fail_urls = []
        dispatcher.connect(self.handle_spider_closed, signals.spider_closed)
        super().__init__()

    def handle_spider_closed(self):
        '''
        信号接收器
        当spider关闭时收集所有的fail_urls
        '''
        self.crawler.stats.set_value('fail_urls', ','.join(self.fail_urls))


    def parse(self, response):
        """
        1. 获取文章列表页中的文章url并交给scrapy下载,并进行解析
        2. 获取下一页的url并交给scrapy进行下载,下载完成后交给parse
        """
        # 解析列表页中的所有文章url并交给scrapy下载后进行解析
        if response.status == 404:
            self.fail_urls.append(response.url)
            self.crawler.stats.inc_value('failed_url')

        post_nodes = response.xpath("//div[@id='archive']/div[contains(@class,'floated-thumb')]/div[@class='post-thumb']/a")

        for post_node in post_nodes:
            image_url = post_node.xpath("img/@src").extract_first("")
            post_url = post_node.xpath("@href").extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url),
                          callback=self.parse_detail,
                          meta={"front_image_url": image_url})

        # 提取下一页并交给scrapy进行下载
        next_url = response.xpath("//a[@class='next page-numbers']/@href").extract_first()
        if next_url:
            yield Request(url = parse.urljoin(response.url, next_url),
                          callback = self.parse)

    def parse_detail(self, response):
        # 提取文章的具体字段

        # front_image_url = response.meta.get("front_image_url", "")  #文章封面图
        # title = response.xpath("//div[@class='entry-header']/h1/text()").extract_first()
        #
        # create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract_first().replace("·", "").strip()
        # try:
        #     create_date = datetime.datetime.strptime(create_date, '%Y/%m/%d')
        # except Exception as e:
        #     create_date = datetime.datetime.now()
        #
        # praise_nums = int(response.xpath("//span[contains(@class,'vote-post-up')]/h10/text()").extract_first())
        #
        # fav_nums = response.xpath("//span[contains(@class,'bookmark-btn')]/text()").extract_first()
        # match_re = re.match(r".*(\d+).*", fav_nums)
        # if match_re:
        #     fav_nums = int(match_re.group(1))
        # else:
        #     fav_nums = 0
        #
        # comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract_first()
        # match_re = re.match(r".*(\d+).*", comment_nums)
        # if match_re:
        #     comment_nums = int(match_re.group(1))
        # else:
        #     comment_nums = 0
        #
        # # content = response.xpath("//div[@class='entry']").extract_first()
        # tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        # tags = ",".join(tag_list)
        #
        # article_item = JobboleArticleItem()
        # article_item['url_object_id'] = get_md5(response.url)
        # article_item["title"] = title
        # article_item["url"] = response.url
        # article_item["create_date"] = create_date
        # article_item["front_image_url"] = [front_image_url]
        # article_item["praise_nums"] = praise_nums
        # article_item["comment_nums"] = comment_nums
        # article_item["fav_nums"] = fav_nums
        # article_item["tags"] = tags
        # article_item["content"] = content

        # 通过ItemLoader加载item
        front_image_url = response.meta.get("front_image_url", "")  #文章封面图

        item_loader = ArticleItemLoader(item=JobboleArticleItem(), response=response)
        item_loader.add_xpath('title', "//div[@class='entry-header']/h1/text()")
        item_loader.add_value('url', response.url)
        item_loader.add_value('url_object_id', get_md5(response.url))
        item_loader.add_xpath('create_date', "//p[@class='entry-meta-hide-on-mobile']/text()")
        item_loader.add_value('front_image_url', [front_image_url])
        item_loader.add_xpath('praise_nums', "//span[contains(@class,'vote-post-up')]/h10/text()")
        item_loader.add_xpath('comment_nums', "//a[@href='#article-comment']/span/text()")
        item_loader.add_xpath('fav_nums', "//span[contains(@class,'bookmark-btn')]/text()")
        item_loader.add_xpath('tags', "//p[@class='entry-meta-hide-on-mobile']/a/text()")
        # item_loader.add_xpath('content', "//div[@class='entry']")
        article_item = item_loader.load_item()

        yield article_item
