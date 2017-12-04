# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json
import MySQLdb
import MySQLdb.cursors

from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline():
    # 自定义导出json文件
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()



class JsonExporterPipeline():
    # 调用scrapy提供的json exporter导出json文件
    def __init__(self):
        self.file = open('article_exporter.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class MysqlPipeline():
    # 采用同步机制写入mysql
    def __init__(self):
        self.conn = MySQLdb.connect('127.0.0.1', 'root', 'lf1222', 'article_spider',
                                    charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            INSERT INTO jobbole_article(title, url, url_object_id, create_date, fav_nums)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql, (item['title'],
                                         item['url'],
                                         item['url_object_id'],
                                         item['create_date'],
                                         item['fav_nums']))
        self.conn.commit()
        return item


class MysqlTwistedPipeline():
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        """
        该类方法类似下面的from_crawler,但是仅提供了范围settings的钩子
        """
        dbparms = dict(
                host = settings['MYSQL_HOST'],
                db = settings['MYSQL_DBNAME'],
                user = settings['MYSQL_USER'],
                password = settings['MYSQL_PASSWORD'],
                charset = 'utf8',
                cursorclass = MySQLdb.cursors.DictCursor,
                use_unicode = True,
            )
        dbpool = adbapi.ConnectionPool('MySQLdb', **dbparms)    # 使用Twisted创建一个数据库连接池
        return cls(dbpool)

    # @classmethod
    # def from_crawler(cls, crawler):
    #     """
    #     该类方法从Crawler创建一个pipeline实例.其中Crawler对象提供了访问所有Scrapy核心组件的
    #     钩子(如settings,signals).
    #     """
    #     settings = crawler.settings
    #     dbparms = dict(
    #             host = settings['MYSQL_HOST'],
    #             db = settings['MYSQL_DBNAME'],
    #             user = settings['MYSQL_USER'],
    #             password = settings['MYSQL_PASSWORD'],
    #             charset = 'utf8',
    #             cursorclass = MySQLdb.cursors.DictCursor,
    #             use_unicode = True,
    #         )
    #     dbpool = adbapi.ConnectionPool('MySQLdb', **dbparms)    # 使用Twisted创建一个数据库连接池
    #     return cls(dbpool)

    def process_item(self, item, spider):
        # 使用Twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)    # 处理异常
        return item

    def do_insert(self, cursor, item):
        # 执行具体的插入
        insert_sql = """
            INSERT INTO jobbole_article(title, url, url_object_id, create_date, fav_nums)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (item['title'],
                                    item['url'],
                                    item['url_object_id'],
                                    item['create_date'],
                                    item['fav_nums']))

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print(failure)


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'front_image_url' in item:
            ok, value = results[0]
            image_file_path = value['path']
            item['front_image_path'] = image_file_path
        return item
