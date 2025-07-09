import os
import random
import time

import requests
from anti_useragent import UserAgent
from requests import Response

from config import logger


def fetch_html(
        url: str,
        rand_user_agent: bool = True,
        retry_times: int = 5,
        timeout: int = 60,
        params: dict = None,
        referer: str = None) -> str | None:
    referer = url if not referer else referer

    headers: dict[str, str] = {
        'referer': referer,
    }

    if not rand_user_agent:
        headers['User-agent'] = \
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.200'
    else:
        ua = UserAgent(platform='windows')
        headers['User-agent'] = ua.random

    for i in range(retry_times):
        try:
            if params is None:
                response: Response = requests.get(url, headers=headers, timeout=timeout)
            else:
                response: Response = requests.get(url, params=params, headers=headers, timeout=timeout)

            response.raise_for_status()
            response.encoding = 'utf-8'

            return response.text
        except Exception as e:
            if i >= retry_times + 1 or retry_times <= 0:
                logger.error('网页获取: {}', repr(e))
                return None

            logger.info(f'\033[33m尝试重连... \033[0m{i + 1}/{retry_times}')
            time.sleep(random.uniform(0.2, 1.5))


def user_select(tips: str, option=('y', 'n'), warning='\033[31m无此选项\033[0m') -> str | None:
    while True:
        raw_select: str = input(tips)
        if not raw_select:
            return warning

        select: str = raw_select.strip().lower()

        if select in option:
            return select

        print(warning)
        continue


def target_web_ping() -> tuple[str, str, str, int]:
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
