# -*- coding: utf-8 -*-
import re
import json
import time
from zheye import zheye
import scrapy


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']

    headers = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': '''Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit
            /537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36''',
    }

    def parse(self, response):
        pass

    def parse_detail(self, response):
        pass

    def start_requests(self):
        # 这里包含爬虫用于爬取的第一个Request.
        return [scrapy.Request('https://www.zhihu.com/#signin',
                               callback=self.login,
                               headers=self.headers)]

    def login(self, response):
        # 模拟登陆,获取验证码图片
        match_obj = re.search(r'.*?name="_xsrf"\svalue="(.*?)"', response.text)
        if match_obj:
            xsrf = match_obj.group(1)

            post_data = {
                '_xsrf': xsrf,
                'email': '1735464886@qq.com',
                'password': 'lf1222',
                'captcha_type': 'cn',
                'captcha': ''
            }

            randomNum = str(int(time.time() * 1000))
            captcha_url_cn = 'https://www.zhihu.com/captcha.gif?r={0}&type=login&lang=cn'.format(randomNum)

            yield scrapy.Request(captcha_url_cn, headers=self.headers,
                                 meta={'post_data':post_data},
                                 callback=self.login_after_captcha)

    def login_after_captcha(self, response):
        # 分析验证码图片获得验证码坐标后请求登陆
        post_url = 'https://www.zhihu.com/login/email'
        post_data = response.meta.get('post_data')
        if response.status == 200:
            with open('captcha.gif', 'wb') as f:
                f.write(response.body)
                f.close()
            z = zheye()
            positions = z.Recognize('captcha.gif')
            pos = sorted(positions, key=lambda x: x[1])  # 根据x轴坐标大小排序
            captcha = {'input_points': []}
            tmp = []
            for poss in pos:
                tmp.append(float(int(poss[1] / 2) + 0.2969))  # 2017.12.3 知乎倒立汉字验证码规则:汉字坐标只取整数部分,小数补0.2969或0.297
                tmp.append(int(poss[0] / 2))
                captcha["input_points"].append(tmp)
                tmp = []
            captcha = '{{"img_size":[200,44],"input_points":{0}}}'.format(captcha['input_points'])
            post_data['captcha'] = captcha

        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login
        )]


    def check_login(self, response):
        # 验证服务器响应,判断是否登录成功
        text_json = json.loads(response.text)
        if 'msg' in text_json and text_json['msg'] == '登录成功':
            for url in self.start_urls:
                yield scrapy.Request(url, headers=self.headers, dont_filter=True) # dont_filter参数表明该请求不要被调度器过滤,用于对同一个请求执行多次
        pass
