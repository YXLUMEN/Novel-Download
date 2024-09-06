import re
from typing import Generator

from bs4 import BeautifulSoup, ResultSet, Tag

from NovelModel import GetNovel
from utility import *


class GetFromBQ2(GetNovel):
    # 列出搜索结果,将小说网址加入列表
    def search_novel(self, html_page: str) -> bool:
        try:
            search_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(f'\033[31m分析初始化出错:\033[0m {repr(e)} ')
            return False

        print('序号  -  小说名称  -  作者')

        search_result_list: ResultSet = search_soup_object.find_all(attrs={'class': 'hot_sale'})
        self.search_results_count = len(search_result_list[1:])

        for novel_index, title_li in enumerate(search_result_list, 1):
            try:
                novel_name_tag: ResultSet[Tag] = title_li.select("a p[class='title']")
                novel_author_tag: ResultSet[Tag] = title_li.select("p[class='author'] a")

                # Url
                if title_li.select("a")[0].get('href') is None:
                    self.search_results_list.append('')
                else:
                    self.search_results_list.append(title_li.select("a")[0].get('href'))
                # Title
                novel_name: str = novel_name_tag[0].get_text() if novel_name_tag[0] is not None else 'None'
                # Author
                novel_author: str = novel_author_tag[0].get_text() if novel_author_tag is not None else 'None'

                # 格式化信息
                novel_name = re.sub(r'\s+\s', '', novel_name)
                novel_author = re.sub(r'\s+\s', '', novel_author)

                print(f'{novel_index} - {novel_name} - {novel_author}')
            except Exception as e:
                print(f'\033[31m分析出错:\033[0m {e}')
                return False

        return True

    def novel_homepage(self, novel_name_index: int) -> Generator | None:
        url: str = f'{self.url}{self.search_results_list[novel_name_index]}'

        try:
            novel_page_html: str = html_request(url)
        except Exception as e:
            print(e)
            return

        novel_page_soup_object = BeautifulSoup(novel_page_html, 'lxml')

        self.novel_title = novel_page_soup_object.select("header span[class='title']")[0].get_text()

        chapter_list: ResultSet[Tag] = novel_page_soup_object.select("div[id='chapterlist']")[0].select("p a")[1:]

        for tag in chapter_list:
            href: str = tag.get('href')
            title: str = tag.get_text()

            yield href, title

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
            with open(f'{self.download_dir}/{self.novel_title}/{index}.txt', 'w', encoding='utf-8') as f:
                f.write(text)
        self.bar.update(1)

        return text
