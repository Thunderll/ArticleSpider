# -*- coding:utf-8 -*-

import requests
import time
from scrapy.selector import Selector
from lxml import etree
import MySQLdb


conn = MySQLdb.connect(host='127.0.0.1', user='root', password='lf1222',
                       database='article_spider', charset='utf8',
                       use_unicode=True)
cursor = conn.cursor()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Apple'
                         'WebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3'
                         '239.84 Safari/537.36', }


def crawl_ips():
    # 爬取西刺的免费代理ip

    insert_sql = '''
        INSERT INTO proxy_ip(ip, port, speed, proxy_type)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE port=VALUES(port), speed=VALUES(speed)
    '''
    check_ip = GetIp()

    for i in range(1000):
        response = requests.get(f'http://www.xicidaili.com/nn/{i}', headers=headers)
        time.sleep(5)
        result = etree.HTML(response.text)
        all_trs = result.xpath("//table[@id='ip_list']/tr")
        ip_list = []
        for tr in all_trs[1:]:
            speed_str = tr.xpath(".//div[@class='bar']/@title")[0]
            if speed_str:
                speed = float(speed_str.split('秒')[0])
            else:
                speed = 0
            all_texts = tr.xpath(".//td/text()")
            ip, port, proxy_type = all_texts[0], all_texts[1], all_texts[5].lower()

            if not proxy_type:
                ip_list.append((str(ip), str(port), str(proxy_type), speed))

        for ip_info in ip_list:
            cursor.execute(insert_sql, (ip_info[0], ip_info[1], ip_info[3], ip_info[2]))
            conn.commit()
            print('Get {0}:{1}'.format(ip_info[0], ip_info[1]))


class GetIp():

    http_url = 'http://www.w3school.com.cn/'
    https_url = 'https://www.baidu.com'

    def get_random_ip(self, proxy_type='http'):
        # 从数据控中随机获取一个可用ip
        random_sql = '''
            SELECT ip, port, proxy_type FROM proxy_ip WHERE proxy_type='{0}'
            ORDER BY  RAND()
            LIMIT 1
        '''.format(proxy_type)
        result = cursor.execute(random_sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]
            proxy_type = ip_info[2]

            judge_re = self.judge_ip(ip, port,proxy_type)
            if judge_re:
                return '{2}://{0}:{1}'.format(ip, port, proxy_type)
                print('Get a valid proxy {2}://{0}:{1}'.format(ip, port, proxy_type))
            else:
                time.sleep(5)
                self.get_random_ip()

    def judge_ip(self, ip, port, proxy_type):
        #判断ip是否可用

        proxy_url = '{2}://{0}:{1}'.format(ip, port, proxy_type)
        try:
            proxy_dict = {proxy_type: proxy_url,}
            response = requests.get(getattr(self, proxy_type),
                                    proxies=proxy_dict, headers=headers)
            return True
        except Exception as e:
            print('Invalid proxy ip and port!')
            self._delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print('Effective ip')
                return True
            else:
                print('Invalid proxy ip and port!')
                self._delete_ip(ip)
                return False

    def _delete_ip(self, ip):
        # 从数据库中删除无效的Ip
        delete_sql = '''
            DELETE FROM proxy_ip WHERE ip='{0}'
        '''.format(ip)
        cursor.execute(delete_sql)
        conn.commit()
        return True


if __name__ == '__main__':
    # ip = GetIp()
    # ip.get_random_ip()
    crawl_ips()
