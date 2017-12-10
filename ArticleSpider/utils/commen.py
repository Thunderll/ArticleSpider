# -*- coding:utf-8 -*-
import hashlib
import re


def get_md5(url):
    if isinstance(url, str):
        url = url.encode('utf-8')
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


def extract_nums(value):
    # 提取字符串中的数字
    match_re = re.match(r".*(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums


if __name__ == '__main__':
    print(get_md5('http://jobbole.com'))