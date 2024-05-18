import re
from abc import abstractmethod
from typing import TextIO, Generator

from bs4 import BeautifulSoup, ResultSet, Tag

from utility import *


class GetNovel:
    __slots__ = (
        'url', 'download_dir', 'mode', 'search_results_count', 'chapter_href_list_count',
        'novel_title', 'novel_text_href_list', 'chapter_href_dict', 'bar')

    def __init__(self, url: str, download_dir: str):
        self.download_dir: str = download_dir
        self.mode: int = 0

        # Website's url
        self.url: str = url
        # search results' num of novel
        self.search_results_count: int = 0
        # all chapters of the novel
        self.chapter_href_list_count: int = 0
        self.novel_title: str = ''
        # to the novel's main page
        self.novel_text_href_list: list = []

        self.bar = None

    @abstractmethod
    def search_novel(self, html_page: str) -> bool:
        pass

    @abstractmethod
    def novel_homepage(self, novel_name_index: int):
        pass

    @abstractmethod
    def novel_main_text(self, href_key: str) -> str:
        pass

    def write_novel_text(self, href_key: str, index: int = 0):
        title, text = self.novel_main_text(href_key)
        if not title:
            print(f'\033[31mWriteText\033[0m -> {href_key}')
            return ''

        text: str = f'{title}\n\n{text}\n\n'
        if self.mode:
            f_open = open(f'{self.download_dir}/{self.novel_title}/{index} {title}.txt', 'w', encoding='utf-8')
            f_open.write(text)
            f_open.close()
        self.bar.update(1)

        return text


class GetFromBQ1(GetNovel):
    # 列出搜索结果,将小说网址加入列表
    def search_novel(self, html_page: str) -> bool:
        """

        :param html_page:
        :return: When something goes wrong, it will return False
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
                # 基本信息
                novel_index_tag: ResultSet[Tag] = title_li.select("span[class='s1 wid2']")
                novel_name_tag: ResultSet[Tag] = title_li.select("span[class='s2 wid'] a")
                novel_author_tag: ResultSet[Tag] = title_li.select("span[class='s4 wid'] a")
                # 时间信息
                latest_update_chapter_tag: ResultSet[Tag] = title_li.select("span[class='s3 wid3'] a")
                update_time_tag: ResultSet[Tag] = title_li.select("span[class='s6 wid6']")

                if novel_name_tag[0].get('href') is None:
                    self.novel_text_href_list.append('')
                else:
                    self.novel_text_href_list.append(novel_name_tag[0].get('href'))

                novel_index: str = novel_index_tag[0].get_text() if novel_index_tag[0] is not None else 'None'
                novel_name: str = novel_name_tag[0].get_text() if novel_name_tag[0] is not None else 'None'
                novel_author: str = novel_author_tag[0].get_text() if novel_author_tag is not None else 'None'

                if latest_update_chapter_tag[0] is not None:
                    latest_update_chapter: str = latest_update_chapter_tag[0].get_text()
                else:
                    latest_update_chapter: str = 'None'
                update_time: str = update_time_tag[0].get_text() if update_time_tag[0] is not None else 'None'

                print(f'{novel_index} - {novel_name} - {novel_author} - {latest_update_chapter} - {update_time}')
            except Exception as e:
                print(f'\033[31m分析出错:\033[0m {e}')
                return False

        self.search_results_count = len(search_result_list[1:])
        return True

    def novel_homepage(self, novel_name_index: int):
        """

        :param novel_name_index:
        :return: If work correctly,
        it will return the chapter list and title of the selected novel
        """
        url: str = f'{self.url}{self.novel_text_href_list[novel_name_index]}'

        try:
            novel_page_html: str = html_request(url)
        except Exception as e:
            print(e)
            return

        novel_page_soup_object = BeautifulSoup(novel_page_html, 'lxml')
        self.novel_title = novel_page_soup_object.select("div[id='info'] h1")[0].get_text()
        chapter_list = novel_page_soup_object.select("div[id='list'] dl")[0]

        for i in chapter_list.find_all(['dd', 'dt'], limit=25):
            i.extract()
            if '正文' in i.get_text():
                break

        chapter_href_dict: dict = dict()

        for tag in chapter_list.select('dd'):
            href: str = tag.a.get('href')
            title: str = tag.get_text()
            chapter_href_dict[href] = title

        self.chapter_href_list_count = len(chapter_href_dict)
        return chapter_href_dict

    def novel_main_text(self, href_key) -> bool | tuple[str, str]:
        html_page: str = html_request(f'{self.url}{href_key}')
        try:
            text_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(e)
            return False

        title: str = text_soup_object.select("div[class='bookname'] h1")[0].get_text()
        original_text: Tag = text_soup_object.select("div[id='content']")[0]

        [s.extract() for s in text_soup_object.find_all(['p', 'div'])]
        text: str = str(original_text)
        text = text.replace('<br/><br/>', '\n').replace(' ', '')
        text = re.sub(r'</?div.*>|\s+\s', '', text)

        return title, text

    def write_novel_text(self, href_key: str, index=0):
        return super().write_novel_text(href_key, index)


class GetFromBQ2(GetNovel):
    # 列出搜索结果,将小说网址加入列表
    def search_novel(self, html_page: str) -> bool:
        try:
            search_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(f'\033[31m分析初始化出错:\033[0m {e} ')
            return False

        print('序号    小说名称    作者')
        search_result_list: ResultSet = search_soup_object.find_all(attrs={'class': 'hot_sale'})
        for novel_index, title_li in enumerate(search_result_list, 1):
            try:
                novel_name_tag: ResultSet[Tag] = title_li.select("a p[class='title']")
                novel_author_tag: ResultSet[Tag] = title_li.select("p[class='author'] a")

                if title_li.select("a")[0].get('href') is None:
                    self.novel_text_href_list.append('')
                else:
                    self.novel_text_href_list.append(title_li.select("a")[0].get('href'))

                novel_name: str = novel_name_tag[0].get_text() if novel_name_tag[0] is not None else 'None'
                novel_author: str = novel_author_tag[0].get_text() if novel_author_tag is not None else 'None'
                # 格式化信息
                novel_name = re.sub(r'\s+\s', '', novel_name)
                novel_author = re.sub(r'\s+\s', '', novel_author)

                print(f'{novel_index} - {novel_name} - {novel_author}')
            except Exception as e:
                print(f'\033[31m分析出错:\033[0m {e}')
                return False

        self.search_results_count = len(search_result_list[1:])
        return True

    def novel_homepage(self, novel_name_index: int) -> Generator | None:
        url: str = f'{self.url}{self.novel_text_href_list[novel_name_index]}'

        try:
            novel_page_html: str = html_request(url)
        except Exception as e:
            print(e)
            return

        novel_page_soup_object = BeautifulSoup(novel_page_html, 'lxml')

        self.novel_title = novel_page_soup_object.select("header span[class='title']")[0].get_text()
        chapter_list: Tag = novel_page_soup_object.select("div[id='chapterlist']")[0]

        # chapter_href_dict: dict = dict()

        """for tag in chapter_list.select("p a")[1:]:
            href: str = tag.get('href')
            title: str = tag.get_text()
            chapter_href_dict[href] = title

        self.chapter_href_list_count = len(chapter_href_dict)
        return chapter_href_dict"""
        href_count = 0
        for tag in chapter_list.select("p a")[1:]:
            href: str = tag.get('href')
            title: str = tag.get_text()
            href_count += 1
            yield href, title

        self.chapter_href_list_count = href_count

    def novel_main_text(self, href_key):
        html_page: str = html_request(f'{self.url}{href_key}')
        try:
            text_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(e)
            return False

        original_text: Tag = text_soup_object.select("div[id='chaptercontent']")[0]

        [s.extract() for s in text_soup_object.find_all(['p', 'div'])]
        text: str = str(original_text)
        text = text.replace('<br/><br/>', '\n').replace(' ', '')
        text = re.sub(r'</?div.*>|\s+\s', '', text)
        text = f'{text}\n\n'

        return text

    def write_novel_text(self, href_key: str, index: int = 0):
        text: str = self.novel_main_text(href_key)

        if not text:
            print(f'\033[31mWriteText\033[0m -> {href_key}')
            return False

        if self.mode:
            f_open: TextIO = open(f'{self.download_dir}/{self.novel_title}/{index}.txt', 'w', encoding='utf-8')
            f_open.write(text)
            f_open.close()
        self.bar.update(1)

        return text


