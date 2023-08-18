import re
from threading import Lock

from bs4 import BeautifulSoup

from utility import *


class HTTPRequest:
    down = 1
    Lock = Lock()

    def __init__(self, url: str):
        # Website's url
        self.mode = 0
        self.url = url
        # search results' num of novel
        self.search_results_len = 0
        # all chapters of the novel
        self.chapter_href_list_len = 0
        self.novel_title = ''
        # to the novel's main page
        self.novel_text_href_list = []
        self.chapter_href_dict = {}

    # 列出搜索结果,将小说网址加入列表
    def search_page_analysis(self, html_page: str):
        try:
            search_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(f'\033[31m分析初始化出错:\033[0m {e} ')
            return False
        #
        print('序号    小说名称    作者')
        search_result_list = search_soup_object.find_all(attrs={'class': 'hot_sale'})
        for novel_index, title_li in enumerate(search_result_list, 1):
            try:
                novel_name = title_li.select("a p[class='title']")
                novel_author = title_li.select("p[class='author'] a")

                if title_li.select("a")[0].get('href') is None:
                    self.novel_text_href_list.append('')
                else:
                    self.novel_text_href_list.append(title_li.select("a")[0].get('href'))

                novel_name = novel_name[0].get_text() if novel_name[0] is not None else 'None'
                novel_author = novel_author[0].get_text() if novel_author is not None else 'None'

                novel_name = re.sub(r'\s+\s', '', novel_name)
                novel_author = re.sub(r'\s+\s', '', novel_author)

                print(f'{novel_index}  {novel_name}  {novel_author}')
            except Exception as e:
                print(f'\033[31m分析出错:\033[0m {e}')
                return False

        self.search_results_len = len(search_result_list[1:])
        return True

    def chapter_page_analysis(self, novel_name_index: int):
        print('请确认小说内容是否存在,以避免无效工作')
        url = f'{self.url}{self.novel_text_href_list[novel_name_index]}'
        select = selection('是否打开浏览器确认?(y/n)\n')
        if select == 'y':
            os.system(f'start {url}')
        time.sleep(2)

        try:
            novel_page_html = get_html(url)
        except Exception as e:
            print(e)
            return False

        novel_page_soup_object = BeautifulSoup(novel_page_html, 'lxml')
        self.novel_title = novel_page_soup_object.select("header span[class='title']")[0].get_text()
        chapter_list = novel_page_soup_object.select("div[id='chapterlist']")[0]

        for tag in chapter_list.select("p a")[1:]:
            href = tag.get('href')
            title = tag.get_text()
            self.chapter_href_dict[href] = title

        self.chapter_href_list_len = len(self.chapter_href_dict)
        return self.chapter_href_dict

    def novel_text_analysis(self, href_key: str, index=0):
        html_page = get_html(f'{self.url}{href_key}')
        try:
            text_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(e)
            return False

        original_text = text_soup_object.select("div[id='chaptercontent']")[0]

        [s.extract() for s in text_soup_object.find_all(['p', 'div'])]
        text = str(original_text)
        text = text.replace('<br/><br/>', '\n').replace(' ', '')
        text = re.sub(r'</?div.*>|\s+\s', '', text)
        text = f'{text}\n\n'

        if self.mode:
            fopen = open(f'./Download/{self.novel_title}/{index}.txt', 'w', encoding='utf-8')
            fopen.write(text)
            fopen.close()
        with self.Lock:
            print(f'\r{self.down}/{self.chapter_href_list_len}', end='')
            self.down += 1

        return text
