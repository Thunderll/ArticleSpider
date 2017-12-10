# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import datetime
import re

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from scrapy.loader import ItemLoader

from utils.commen import extract_nums
from settings import SQL_DATE_FORMAT, SQL_DATETIME_FORMAT


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def date_convert(value):
    # 格式化日期字符串为datetime对象
    try:
        create_date = datetime.datetime.strptime(value, '%Y/%m/%d')
    except Exception as e:
        create_date = datetime.datetime.now()
    return create_date



def remove_comment_tags(value):
    # 去掉tag中提取的评论
    if '评论' in value:
        return ''
    return value


class ArticleItemLoader(ItemLoader):
    # 自定义ItemLoader
    default_output_processor = TakeFirst()


class JobboleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor=lambda x:x,
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field()
    comment_nums = scrapy.Field(
        input_processor=MapCompose(extract_nums),
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(extract_nums),
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(','),
    )
    # content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            INSERT INTO jobbole_article(title, url, url_object_id,
             create_date, fav_nums)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (self['title'], self['url'],self['url_object_id'],
                  self['create_date'],self['fav_nums'])
        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题 item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    # content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    # click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            INSERT INTO zhihu_question(zhihu_id, topics, url, title, 
            answer_num, comments_num, watch_user_num, click_num, 
            crawl_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        zhihu_id = int(''.join(self['zhihu_id']))
        topics = ','.join(self['topics'])
        url = self['url'][0]
        title = ''.join(self['title'])
        # content = ''.join(self['content'])
        answer_num = extract_nums(''.join(self['answer_num']))
        comments_num = extract_nums(''.join(self['comments_num']))
        if len(self['watch_user_num']) == 2:
            watch_user_num = int(self['watch_user_num'][0])
            click_num = int(self['watch_user_num'][1])
        else:
            watch_user_num = int(self['watch_user_num'][0])
            click_num = 0
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, answer_num, comments_num,
                  watch_user_num, click_num, crawl_time)
        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    # 知乎问题的回答 Item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    created_time = scrapy.Field()
    updated_time = scrapy.Field()
    crawl_time = scrapy.Field()

