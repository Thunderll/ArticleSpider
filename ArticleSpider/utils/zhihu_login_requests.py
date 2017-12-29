# -*- coding:utf-8 -*-
"""
使用requests模块实验模拟登陆知乎,并保存cookie
使用zheye模块对知乎倒立汉字验证码进行分析
"""

import requests
import re
import time
import shutil
from utils.zheye import zheye

try:
    import cookielib
except:
    import http.cookiejar as cookielib


HEADER = {
    'HOST': 'www.zhihu.com',
    'Referer': 'https://www.zhihu.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
}
CAPTCHA_URL_CN = 'https://www.zhihu.com/captcha.gif?r={0}&type=login&lang=cn'

session = requests.session()
session.headers = HEADER

session.cookies = cookielib.LWPCookieJar(filename='cookie.txt')
try:
    session.cookies.load(ignore_discard=True)
except:
    print("cookie未能加载")


def get_xsrf(response):
    # 获取xsrf code
    match_obj = re.search(r'.*?name="_xsrf"\svalue="(.*?)"', response.text)
    if match_obj:
        return match_obj.group(1)
    else:
        return ''


def captcha_parse(session):
    # 倒立问题验证码分析
    z = zheye()
    randomNum = str(int(time.time() * 1000))
    response = session.get(CAPTCHA_URL_CN.format(randomNum), headers=HEADER, stream=True)
    if response.status_code == 200:
        with open('pic_captcha.gif', 'wb') as f:
            # response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)

        positions = z.Recognize('pic_captcha.gif')
        print(positions)

        pos = sorted(positions, key=lambda x:x[1]) #TODO 根据x轴坐标大小排序
        captcha = {'input_points': []}
        tmp = []
        for poss in pos:
            tmp.append(float(int(poss[1]/2)+0.2969))  #TODO 2017.12.3 知乎倒立汉字验证码规则:汉字坐标只取整数部分,小数补0.2969或0.297
            tmp.append(int(poss[0]/2))
            captcha["input_points"].append(tmp)
            tmp = []
        return captcha
    else:
        return []


def is_login():
    inbox_url = 'https://www.zhihu.com/inbox'
    response = session.get(inbox_url, headers=HEADER, allow_redirects=False)
    if response.status_code != 200:
        return False
    else:
        return True


def get_index():
    # 检查cookie是否可用
    response = session.get('https://www.zhihu.com')
    with open('indexl_page.html', 'wb') as f:
        f.write(response.text.encode('utf-8'))
    print('OK')


def zhihu_login(account, password):
    # 知乎登录
    response = session.get('https://www.zhihu.com')

    if re.match('.+?@.+?\.com', account):
        print('邮箱登录')
        post_url = 'https://www.zhihu.com/login/email'
        captcha = captcha_parse(session)
        xsrf = get_xsrf(response)
        post_data = {
            '_xsrf': xsrf,
            'email': account,
            'password': password,
            'captcha_type': 'cn',
            'captcha': '{{"img_size":[200,44],"input_points":{0}}}'.format(captcha['input_points']),
        }
        response_text = session.post(post_url, data=post_data)
        session.cookies.save()
        pass


if __name__ == '__main__':
    # is_login()
    # get_index()
    zhihu_login('1735464886@qq.com', 'lf1222')
    pass
