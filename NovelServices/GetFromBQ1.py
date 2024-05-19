import re
from typing import Generator

from bs4 import BeautifulSoup, ResultSet, Tag

from NovelModel import GetNovel
from utility import *


class GetFromBQ1(GetNovel):
    """
    网站已停用
    """

    # 列出搜索结果,将小说网址加入列表
    def search_novel(self, html_page: str) -> bool:
        try:
            search_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(f'\033[31m分析初始化出错:\033[0m {e} ')
            return False

        print('序号  -  小说名称  -  作者  -  最新章节  -  更新时间')
        search_result_list: ResultSet[Tag] = search_soup_object.select("div[class='novelslist2'] ul li")[1:]
        for title_li in search_result_list:
            try:
                # 基本信息
                novel_index_tag: ResultSet[Tag] = title_li.select("span[class='s1 wid2']")
                novel_name_tag: ResultSet[Tag] = title_li.select("span[class='s2 wid'] a")
                novel_author_tag: ResultSet[Tag] = title_li.select("span[class='s4 wid'] a")
                # 时间信息
                latest_update_chapter_tag: ResultSet[Tag] = title_li.select("span[class='s3 wid3'] a")
                update_time_tag: ResultSet[Tag] = title_li.select("span[class='s6 wid6']")

                if novel_name_tag[0].get('href') is None:
                    self.search_results_list.append('')
                else:
                    self.search_results_list.append(novel_name_tag[0].get('href'))

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

        self.search_results_count = len(search_result_list)
        return True

    def novel_homepage(self, novel_name_index: int) -> Generator | None:
        """

        :param novel_name_index:
        :return: If work correctly,
        it will return the chapter list and title of the selected novel
        """
        url: str = f'{self.url}{self.search_results_list[novel_name_index]}'

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

        for tag in chapter_list.select('dd'):
            href: str = tag.a.get('href')
            title: str = tag.get_text()
            yield href, title

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
