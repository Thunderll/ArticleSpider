# -*- coding: utf-8 -*-
import re
import json
import time
import datetime
from urllib import parse

import scrapy
from scrapy.loader import ItemLoader
from scrapy.http.cookies import CookieJar
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError

from utils.zheye import zheye
from items import ZhihuAnswerItem, ZhihuQuestionItem

# 创建cookiejar对象
cookie_jar = CookieJar()


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com', 'zhihu.com']
    start_urls = ['https://www.zhihu.com/']
    # question的第一页answer的请求url
    start_answer_url = 'http://www.zhihu.com/api/v4/questions/{0}/answers?' \
                       'sort_by=default&include=data%5B%2A%5D.is_normal%2C' \
                       'admin_closed_comment%2Creward_info%2Cis_collapsed%' \
                       '2Cannotation_action%2Cannotation_detail%2Ccollapse' \
                       '_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%' \
                       '2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable' \
                       '_content%2Cvoteup_count%2Creshipment_settings%2Cco' \
                       'mment_permission%2Ccreated_time%2Cupdated_time%2Cr' \
                       'eview_info%2Cquestion%2Cexcerpt%2Crelationship.is_' \
                       'authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_' \
                       'nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.mark_i' \
                       'nfos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_' \
                       'count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.t' \
                       'opics&limit=20&offset={1}'

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'HOST': 'www.zhihu.com',
            'Referer': 'https://www.zhihu.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb'\
                          'Kit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
        }
    }

    def parse(self, response):
        """
        提取出HTML页面中的所有url, 并跟踪这些url进一步爬取,
        如果提取的url中格式为/question/xxxx 就下载之后直接进入解析函数
        """
        results = response.xpath("//a/@href").extract()
        all_urls = [parse.urljoin(response.url, url) for url in results]
        all_urls = filter(lambda x: True if x.startswith('https') else False,
                          all_urls)
        for url in all_urls:
            match_obj = re.match("(.*?zhihu.com/question/(\d+)(?:/|$).*?)", url)
            if match_obj:
                # 如果提取到question相关的页面则下载后交由提取函数进行提取
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)

                yield scrapy.Request(request_url,
                                     callback=self.parse_question,
                                     meta={'question_id':question_id,}
                                     )
                # break
            else:
                # 如果不是question页面则直接进一步跟踪
                yield scrapy.Request(url)

    def parse_question(self, response):
        # 处理question页面,从页面中提取出具体的question item
        question_id = response.meta.get('question_id')
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)

        item_loader.add_xpath('title', "//div[@class='QuestionHeader']//h1[@class='QuestionHeader-title']/text()")
        # item_loader.add_xpath('content', "//div[@class='QuestionHeader-detail']")
        item_loader.add_value('url', response.url)
        item_loader.add_value('zhihu_id', question_id)
        item_loader.add_xpath('answer_num', "//h4[@class='List-headerText']/span/text()")
        item_loader.add_xpath('comments_num', "//div[@class='QuestionHeader-Comment']/button/text()")
        item_loader.add_xpath('watch_user_num', "//div[@class='NumberBoard-value']/text()")
        item_loader.add_xpath('topics', "//a[@class='TopicLink']/div/div/text()")

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(question_id, 0),
                             callback=self.parse_answer
                             )
        yield question_item

    def parse_answer(self, response):
        # 处理question的answer
        answer_json = json.loads(response.text)
        is_end = answer_json['paging']['is_end']
        next_url = answer_json['paging']['next']

        # 提取answer的具体信息
        for answer in answer_json['data']:
            answer_item = ZhihuAnswerItem()

            answer_item['zhihu_id'] = answer['id']
            answer_item['url'] = answer['url']
            answer_item['question_id'] = answer['question']['id']
            answer_item['author_id'] = answer['author']['id'] if 'id' in answer['author'] else None
            # answer_item['content'] = answer['content'] if 'content' in answer else None
            answer_item['praise_num'] = answer['voteup_count']
            answer_item['comments_num'] = answer['comment_count']
            answer_item['updated_time'] = answer['updated_time']
            answer_item['created_time'] = answer['created_time']
            answer_item['crawl_time'] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url,
                                 callback=self.parse_answer
                                 )


    def start_requests(self):
        # 这里包含爬虫用于爬取的第一个Request.
        try:
            # 如果存在本地cookie,则直接使用
            with open('cookies_.txt', 'r') as f:
                cookiejar = f.read()
            p = re.compile(r'<Cookie (.*?) for .*?>')
            cookies = re.findall(p, cookiejar)
            cookies = (cookie.split('=', 1) for cookie in cookies)
            cookies = dict(cookies)
            return [scrapy.Request('https://www.zhihu.com/inbox',
                                   cookies=cookies,
                                   callback=self.check_cookie_usable,
                                   errback=self.handle_bad_request,
                                   )]
        except:
            # 如果本地没有cookie文件,则进行模拟登陆
            return [scrapy.Request('https://www.zhihu.com/#signin',
                                   callback=self.get_captcha,
                                   meta={'cookie': cookie_jar},
                                   )]

    def get_captcha(self, response):
        # 获取验证码图片
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

            # 提取cookie并向下传递
            cookie_jar = response.meta.get('cookie')
            cookie_jar.extract_cookies(response, response.request)
            return [scrapy.Request(captcha_url_cn,
                                 meta={'post_data':post_data, 'cookie': cookie_jar},
                                 callback=self.login_after_captcha)]

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
            # 根据x轴坐标大小排序
            pos = sorted(positions, key=lambda x: x[1])
            captcha = {'input_points': []}
            tmp = []
            for poss in pos:
                # 2017.12.3 知乎倒立汉字验证码规则:汉字坐标只取整数部分,小数补0.2969或0.297
                tmp.append(float(int(poss[1] / 2)+0.2969))
                tmp.append(int(poss[0] / 2))
                captcha["input_points"].append(tmp)
                tmp = []
            captcha = '{{"img_size":[200,44],"input_points":{0}}}'.format(captcha['input_points'])
            # post_data['captcha'] = captcha

        # 提取cookie并向下传递
        cookie_jar = response.meta.get('cookie')
        cookie_jar.extract_cookies(response, response.request)
        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            callback=self.check_login,
            meta={'cookie': cookie_jar},
            dont_filter=True
        )]


    def check_login(self, response):
        # 验证服务器响应,判断是否登录成功
        text_json = json.loads(response.text)
        if not ('msg' in text_json and text_json['msg'] == '登录成功'):
            print('登录失败')
            cookie_jar = CookieJar()
            # 这里使用yield而用return [..]是因为该函数中存在yield,返回值是一个generator对象,其中return的返回值会被
            # 放在StopIteration的信息中
            yield scrapy.Request('https://www.zhihu.com/#signin',
                                 callback=self.get_captcha,
                                 meta={'cookie': cookie_jar},
                                 dont_filter=True)
            raise StopIteration

        print('登录成功')
        # 模拟登陆成功,提取cookie并保存到本地
        cookies = response.meta['cookie']
        cookies.extract_cookies(response, response.request)
        with open('cookies.txt', 'w') as f:
            for cookie in cookies:
                f.write(str(cookie) + '\n')

        for url in self.start_urls:
            # dont_filter参数表明该请求不要被调度器过滤,用于对同一个请求执行多次
            yield scrapy.Request(url, dont_filter=True)

    def check_cookie_usable(self, response):
        # 检查本地cookie是否有效,若无效则获取验证码模拟登陆
        if  response.status != 200:
            self.handle_bad_request(response)
        else:
            for url in self.start_urls:
                # dont_filter参数表明该请求不要被调度器过滤,用于对同一个请求执行多次
                yield scrapy.Request(url, dont_filter=True)

    def handle_bad_request(self, failure):
        # 使用本地cookie发起初次请求出错时调用
        if failure.check(HttpError):
            response = failure.value.response
            print('HttpError on {}'.format(response.url))
        elif failure.check(DNSLookupError):
            request = failure.request
            print('DNSLookupError on {}'.format(request.url))
        elif failure.check(TimeoutError):
            request = failure.request
            print('TimeoutError on {}'.format(request.url))


