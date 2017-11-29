# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy.http import Request
from urllib import parse
import datetime

from ArticleSpider.items import JobboleArticleItem
from ArticleSpider.utils.commen import get_md5


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        """
        1. 获取文章列表页中的文章url并交给scrapy下载,并进行解析
        2. 获取下一页的url并交给scrapy进行下载,下载完成后交给parse
        """
        # 解析列表页中的所有文章url并交给scrapy下载后进行解析
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
            yield Request(url=parse.urljoin(response.url, next_url),
                          callback=self.parse)

    def parse_detail(self, response):
        # 提取文章的具体字段

        front_image_url = response.meta.get("front_image_url", "")  #文章封面图
        title = response.xpath("//div[@class='entry-header']/h1/text()").extract_first()

        create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract_first().replace("·", "").strip()
        try:
            create_date = datetime.datetime.strptime(create_date, '%Y/%m/%d')
        except Exception as e:
            create_date = datetime.datetime.now()

        praise_nums = int(response.xpath("//span[contains(@class,'vote-post-up')]/h10/text()").extract_first())

        fav_nums = response.xpath("//span[contains(@class,'bookmark-btn')]/text()").extract_first()
        match_re = re.match(r".*(\d+).*", fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0

        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract_first()
        match_re = re.match(r".*(\d+).*", comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0

        # content = response.xpath("//div[@class='entry']").extract_first()
        tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        tags = ",".join(tag_list)

        article_item = JobboleArticleItem()

        article_item['url_object_id'] = get_md5(response.url)
        article_item["title"] = title
        article_item["url"] = response.url
        article_item["create_date"] = create_date
        article_item["front_image_url"] = [front_image_url]
        article_item["praise_nums"] = praise_nums
        article_item["comment_nums"] = comment_nums
        article_item["fav_nums"] = fav_nums
        article_item["tags"] = tags
        # article_item["content"] = content

        yield article_item
