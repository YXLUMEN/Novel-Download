import os

import random
import re
import time
import argparse
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

try:
    import requests
except Exception as E:
    print(E)
    os.system("pip install requests")
try:
    from bs4 import BeautifulSoup
except Exception as E:
    print(E)
    os.system("pip install bs4")
try:
    from anti_useragent import UserAgent
except Exception as E:
    print(E)
    os.system("pip install anti-useragent")
try:
    import lxml
except Exception as E:
    print(E)
    os.system("pip install lxml")

parsers = argparse.ArgumentParser()
parsers.add_argument(
    '-MT', '--thread', default=32, type=int, required=False,
    help='最大线程数,根据计算机性能决定,不建议太大'
)


class HTTPRequest:
    down = 1
    Lock = Lock()

    def __init__(self, url: str):
        # Website's url
        self.url = url
        # search results' num of novel
        self.search_results_len = 0
        # all chapters of the novel
        self.chapter_href_list_len = 0
        self.novel_title = ''
        # to the novel's main page
        self.novel_text_href_list = []
        self.chapter_href_dict = {}

    @staticmethod
    def get_html(url: str, rand_user_agent=True, retry_times=5, timeout=60, params=None, referer=''):
        """

        :param url: Target website's url
        :param rand_user_agent: To use random user agent
        :param retry_times: When connect fail, reconnect times. Set 0 will not retry
        :param timeout:
        :param params:
        :param referer:
        :return:
        """
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
                    break
                # 错误重试
                print(f'\033[33m尝试重连... \033[0m{i + 1}/{retry_times}')
            finally:
                time.sleep(random.uniform(0.2, 1.5))
                i += 1

    # 列出搜索结果,将小说网址加入列表
    def search_page_analysis(self, html_page: str):
        """

        :param html_page:
        :return: When something go wrong it will return False
        """
        try:
            search_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(f'\033[31m分析初始化出错:\033[0m {e} ')
            return False

        print('序号    小说名称    作者    最新章节    更新时间')
        search_result_list = search_soup_object.select("div[class='novelslist2'] ul li")
        for title_li in search_result_list[1:]:
            try:
                novel_index = title_li.select("span[class='s1 wid2']")
                novel_name = title_li.select("span[class='s2 wid'] a")
                novel_author = title_li.select("span[class='s4 wid'] a")
                latest_update_chapter = title_li.select("span[class='s3 wid3'] a")
                update_time = title_li.select("span[class='s6 wid6']")

                if novel_name[0].get('href') is None:
                    self.novel_text_href_list.append('')
                else:
                    self.novel_text_href_list.append(novel_name[0].get('href'))

                novel_index = novel_index[0].get_text() if novel_index[0] is not None else '未找到结果'
                novel_name = novel_name[0].get_text() if novel_name[0] is not None else '未找到结果'
                novel_author = novel_author[0].get_text() if novel_author is not None else '未找到结果'

                if latest_update_chapter[0] is not None:
                    latest_update_chapter = latest_update_chapter[0].get_text()
                else:
                    latest_update_chapter = '未找到结果'
                update_time = update_time[0].get_text() if update_time[0] is not None else '未找到结果'

                print(f'{novel_index}  {novel_name}  {novel_author}  {latest_update_chapter}  {update_time}')
            except Exception as e:
                print(f'\033[31m分析出错:\033[0m {e}')
                return False

        self.search_results_len = len(search_result_list[1:])
        return True

    def chapter_page_analysis(self, novel_name_index: int):
        """

        :param novel_name_index:
        :return: If work correctly, it will return the chapter list and title of selected novel
        """
        try:
            novel_page_html = self.get_html(self.url + self.novel_text_href_list[novel_name_index])
        except Exception as e:
            print(e)
            return False

        novel_page_soup_object = BeautifulSoup(novel_page_html, 'lxml')
        self.novel_title = novel_page_soup_object.select("div[id='info'] h1")[0].get_text()
        chapter_list = novel_page_soup_object.select("div[id='list'] dl")[0]

        for i in chapter_list.find_all(['dd', 'dt'], limit=25):
            i.extract()
            if '正文' in i.get_text():
                break

        for tag in chapter_list.select('dd'):
            href = tag.a.get('href')
            title = tag.get_text()
            self.chapter_href_dict[href] = title
        self.chapter_href_list_len = len(self.chapter_href_dict)

        return self.chapter_href_dict

    def novel_text_analysis(self, href_key):
        html_page = self.get_html(self.url + href_key)
        try:
            text_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(e)
            return

        title = text_soup_object.select("div[class='bookname'] h1")[0].get_text()
        original_text = text_soup_object.select("div[id='content']")[0]

        [s.extract() for s in text_soup_object.find_all(['p', 'div'])]
        text = str(original_text)
        text = text.replace('<br/><br/>', '\n').replace(' ', '')
        text = re.sub(r'</?div.*>|\s+\s', '', text)

        with self.Lock:
            print(f'\r{self.down}/{self.chapter_href_list_len}', end='')
            self.down += 1

        text = title + '\n\n' + text + '\n\n'
        return text


if __name__ == '__main__':
    print('\033[32;4m测试网站连通性...\033[0m')
    if os.system('ping www.ibiquzw.com'):
        print('\033[33m当前网站无法访问,请稍后再试\033[0m')
        os.system('pause')
        exit()

    print(
        '使用说明: 在下载时请不要中断程序,除非不在需要下载内容; '
        '可以手动增加线程数,这一般会提高下载速度,在程序所在目录打开CMD窗口,输入 NovelDown --thread <num> 使得下载线程更改为<num>; '
        '目标网站近期不太稳定,此程序正在重构...'
    )
    time.sleep(1)

    getNovelPage = HTTPRequest('https://www.ibiquzw.com')
    while True:
        search_char = input('\033[36;1m请输入查询的小说名称:\033[0m ')
        print('\033[32m开始查找...\033[0m')
        html = getNovelPage.get_html('https://www.ibiquzw.com/search.html', params={'name': search_char})
        searchResult = getNovelPage.search_page_analysis(html)
        if not getNovelPage.search_results_len:
            print('搜索结果为空,换一个关键词吧~')
            continue
        break
    if not searchResult:
        print('\033[31mError\033[0m')
        os.system('pause')
        exit()
    del html

    while True:
        select = input('\033[36;1m请选择小说序号:\033[0m ')
        if select.isdigit():
            select = int(select) - 1
            if 0 <= select < getNovelPage.search_results_len:
                break
            print('\033[31m请输入整数,且不小于0不大于搜索结果数\033[0m')
        else:
            print('\033[31m请输入整数\033[0m')

    chapterList = getNovelPage.chapter_page_analysis(select)
    if not chapterList:
        print('\033[31mError\033[0m')
        os.system('pause')
        exit()

    pages = getNovelPage.chapter_href_list_len
    print(f'当前任务共{pages}条')

    # outPageNums = 1
    for outPageNums, titleValue in enumerate(chapterList.values(), 1):
        print(f'{titleValue}')
        if outPageNums % 10 == 0:
            temp = input('\033[36;1m是否显示接下来的章节名?\033[0m (y/n)\n')
            if temp.lower() == 'y':
                pass
            else:
                break

    while True:
        select = input('\033[36;1m是否下载?\033[0m (y/n)\n')
        if select.lower() not in ['y', 'n']:
            print('无此选项')
        else:
            break
    if select.lower() == 'y':

        chapterList = list(chapterList)
        while True:
            time.sleep(0.5)
            start = input('\033[36;1m选择起始章节,如需要全部,输入all,否则输入整数:\033[0m ')
            if start.lower() == 'all':
                start = 0
                break
            if not start.isdigit():
                print('\033[33;1m章节目录必须是整数!\033[0m')
                continue
            start = int(start)
            if start < 0 or start > pages:
                print('\033[33;1m选择不能小于0或大于最大章节数\033[0m')
                continue

            end = input('\033[36;1m选择终止章节,如不输入默认选择最后一章,否则输入整数:\033[0m ')
            if end == '':
                chapterList = chapterList[start:]
                getNovelPage.chapter_href_list_len = pages - start
                break
            if not end.isdigit():
                print('\033[33;1m章节目录必须是整数!\033[0m')
                continue
            end = int(end)
            if end <= start:
                print('\033[33;1m终止章节数不能小于等于起始章节!\033[0m')
                continue
            if end > pages:
                print('\033[33;1m终止章节数不能大于最大章节!\033[0m')
                continue
            chapterList = chapterList[start:end]
            getNovelPage.chapter_href_list_len = end - start
            break

        arg = parsers.parse_args()
        if not os.access('./Download', os.W_OK):
            os.mkdir('./Download')
        frp = open(f'./Download/{getNovelPage.novel_title}.txt', 'w+', encoding='utf-8')
        downloadPool = ThreadPoolExecutor(max_workers=arg.thread)

        print('Start processing...')
        result = downloadPool.map(getNovelPage.novel_text_analysis, chapterList)
        for each in result:
            frp.write(each)
        downloadPool.shutdown(wait=True)
        frp.close()

    print('\n\nExit')
    os.system('pause')
