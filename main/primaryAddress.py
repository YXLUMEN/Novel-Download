import re

from bs4 import BeautifulSoup

from utility import *


class HTTPRequest:

    def __init__(self, url: str, download_dir: str):
        self.download_dir = download_dir
        self.mode = 0

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

        self.bar = None

    # 列出搜索结果,将小说网址加入列表
    def search_page_analysis(self, html_page: str):
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
                novel_index = title_li.select("span[class='s1 wid2']")
                novel_name = title_li.select("span[class='s2 wid'] a")
                novel_author = title_li.select("span[class='s4 wid'] a")
                latest_update_chapter = title_li.select("span[class='s3 wid3'] a")
                update_time = title_li.select("span[class='s6 wid6']")

                if novel_name[0].get('href') is None:
                    self.novel_text_href_list.append('')
                else:
                    self.novel_text_href_list.append(novel_name[0].get('href'))

                novel_index = novel_index[0].get_text() if novel_index[0] is not None else 'None'
                novel_name = novel_name[0].get_text() if novel_name[0] is not None else 'None'
                novel_author = novel_author[0].get_text() if novel_author is not None else 'None'

                if latest_update_chapter[0] is not None:
                    latest_update_chapter = latest_update_chapter[0].get_text()
                else:
                    latest_update_chapter = 'None'
                update_time = update_time[0].get_text() if update_time[0] is not None else 'None'

                print(f'{novel_index}  {novel_name}  {novel_author}  {latest_update_chapter}  {update_time}')
            except Exception as e:
                print(f'\033[31m分析出错:\033[0m {e}')
                return False

        self.search_results_len = len(search_result_list[1:])
        return True

    def chapter_page_analysis(self, novel_name_index: int):
        """

        :param novel_name_index:
        :return: If work correctly,
        it will return the chapter list and title of the selected novel
        """
        url = f'{self.url}{self.novel_text_href_list[novel_name_index]}'

        try:
            novel_page_html = get_html(url)
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

    def novel_text_analysis_exe(self, href_key):
        html_page = get_html(f'{self.url}{href_key}')
        try:
            text_soup_object = BeautifulSoup(html_page, 'lxml')
        except Exception as e:
            print(e)
            return False

        title = text_soup_object.select("div[class='bookname'] h1")[0].get_text()
        original_text = text_soup_object.select("div[id='content']")[0]

        [s.extract() for s in text_soup_object.find_all(['p', 'div'])]
        text = str(original_text)
        text = text.replace('<br/><br/>', '\n').replace(' ', '')
        text = re.sub(r'</?div.*>|\s+\s', '', text)

        return title, text

    def novel_text_analysis(self, href_key: str, index=0):
        title, text = self.novel_text_analysis_exe(href_key)

        text = f'{title}\n\n{text}\n\n'
        if self.mode:
            f_open = open(f'{self.download_dir}/{self.novel_title}/{index} {title}.txt', 'w', encoding='utf-8')
            f_open.write(text)
            f_open.close()
        self.bar.update(1)

        return text
