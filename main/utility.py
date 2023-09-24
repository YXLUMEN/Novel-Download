import os
import random
import time

import requests
from anti_useragent import UserAgent


def get_html(url: str, rand_user_agent=True, retry_times=5, timeout=60, params=None, referer=''):
    if referer == '':
        referer = url
    headers = {
        'referer': referer,
    }
    if not rand_user_agent:
        headers['User-agent'] = \
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.200'
    else:
        ua = UserAgent(platform='windows')
        headers['User-agent'] = ua.random

    i = 0
    while i < retry_times:
        try:
            if params is None:
                r = requests.get(url, headers=headers, timeout=timeout)
            else:
                r = requests.get(url, params=params, headers=headers, timeout=timeout)
            r.raise_for_status()
            r.encoding = 'utf-8'

            return r.text

        except Exception as e:
            if i >= retry_times + 1 or retry_times <= 0:
                print(f'\033[31m网页获取:\033[0m {e}')
                return
            # 错误重试
            print(f'\033[33m尝试重连... \033[0m{i + 1}/{retry_times}')
        finally:
            time.sleep(random.uniform(0.2, 1.5))
            i += 1


def selection(tips: str, option=('y', 'n'), warning='无此选项'):
    while True:
        select = input(tips)
        if select.lower() in option:
            return select
        print(warning)
        continue


def website_select():
    # Choose target website
    if not os.system('ping -n 2 www.ibiquzw.com'):
        url = 'https://www.ibiquzw.com'
        search_url = 'https://www.ibiquzw.com/search.html'
        key = 'name'
        w_selection = 1
    elif not os.system('ping -n 2 m.ibiquge.org'):
        url = 'https://m.ibiquge.org'
        search_url = 'https://m.ibiquge.org/SearchBook.php'
        key = 'keyword'
        w_selection = 0
    else:
        raise ConnectionError('Can ont connect to any targets!')
    os.system('cls')

    return url, search_url, key, w_selection
