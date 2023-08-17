from NovelDown import HTTPRequest
from bs4 import BeautifulSoup


def search_page_analysis_ad(html_page: str):
    try:
        search_soup_object = BeautifulSoup(html_page, 'lxml')
    except Exception as e:
        print(f'\033[31m分析初始化出错:\033[0m {e} ')
        return False


def chapter_page_analysis_ad():
    pass


def novel_text_analysis_ad():
    pass


def main():
    html = HTTPRequest.get_html('')