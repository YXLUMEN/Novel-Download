from concurrent.futures import ThreadPoolExecutor
from typing import TextIO, Generator

from tqdm import tqdm

import primaryAddress
from utility import *

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


def main(get_novel_page, search_url: str, key: str):
    # search the novel by its title and author's name
    while True:
        search_char = input('\033[36;1m请输入查询的小说名称:\033[0m ')
        print('\033[32m开始查找...\033[0m')
        html: str = html_request(search_url, params={key: search_char})
        search_result: bool = get_novel_page.search_novel(html)

        if not search_result:
            print('\033[31mError\033[0m')
            return False

        if not get_novel_page.search_results_count:
            print('\n搜索结果为空,换一个关键词吧~')
            time.sleep(1)
            continue
        # end the search
        select = selection('\033[34;1m是否结束查询? (y/n)\033[0m \n')
        if select.lower() == 'y':
            break
    del html

    # 选择查询结果
    while True:
        select: str = input('\033[36;1m请选择小说序号:\033[0m ')
        if select.isdigit():
            select: int = int(select) - 1
            if 0 <= select < get_novel_page.search_results_count:
                break
            print('\033[31m请输入整数,且不小于0不大于搜索结果数\033[0m')
        else:
            print('\033[31m请输入整数\033[0m')

    url: str = get_novel_page.url + get_novel_page.novel_text_href_list[select]
    select_temp: str = selection('是否打开浏览器确认?(y/n)\n')

    if select_temp == 'y':
        os.system(f'start {url}')

    print('正在获取...')
    time.sleep(0.5)
    del url, select_temp

    chapter_dict: Generator = get_novel_page.novel_homepage(select)
    if not chapter_dict:
        print('\033[31mError\033[0m')
        return False

    for outPageNums, titleValue in enumerate(chapter_dict, 1):
        print(f'{titleValue}')
        if outPageNums % 10 == 0:
            select = selection('\033[36;1m是否显示接下来的章节名?\033[0m (y/n)\n')
            if select.lower() == 'y':
                pass
            else:
                break
    pages: int = get_novel_page.chapter_href_list_count
    print(f'\033[32;1m当前共{pages}章\033[0m')

    select: str = selection('\033[36;1m是否下载?\033[0m (y/n)\n')
    if select.lower() == 'n':
        return True

    chapter_list: list = list(chapter_dict)
    del chapter_dict

    # 处理选项
    while True:
        time.sleep(0.5)
        start_page: str = input('\033[36;1m选择起始章节,如需要全部,输入all,否则输入整数:\033[0m ')

        # download all, break the loop
        if start_page.lower() == 'all':
            break

        # "start" will be defined as an int
        if not start_page.isdigit():
            print('\033[33;1m章节目录必须是整数!\033[0m')
            continue

        start_page: int = int(start_page)
        if start_page < 0 or start_page > pages:
            print('\033[33;1m选择不能小于0或大于最大章节数\033[0m')
            continue

        end_page: str = input('\033[36;1m选择终止章节,如不输入默认选择最后一章,否则输入整数:\033[0m ')
        if end_page == '':
            chapter_list = chapter_list[start_page:]
            get_novel_page.chapter_href_list_count = pages - start_page
            break

        if not end_page.isdigit():
            print('\033[33;1m章节目录必须是整数!\033[0m')
            continue

        end_page: int = int(end_page)
        if end_page <= start_page:
            print('\033[33;1m终止章节数不能小于等于起始章节!\033[0m')
            continue

        if end_page > pages:
            print('\033[33;1m终止章节数不能大于最大章节!\033[0m')
            continue

        chapter_list = chapter_list[start_page:end_page]
        get_novel_page.chapter_href_list_count = end_page - start_page
        break

    threads: int = 32

    if selection(f'\033[36;1m将启动{threads}条线程,是否更改?\033[0m (y/n)\n ') == 'y':
        while True:
            threads: str = input('请输入线程数: ')
            if threads.isdigit():
                threads = int(threads)
                break
            print('只能是整数')

    if not os.access('./Download', os.W_OK):
        os.mkdir('./Download')

    download_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=int(threads))

    select: str = selection('\033[36;1m是否输出单个文件,即所有章节包含在一个文本文档中? (y/n)\033[0m\n')
    print('Start processing...')

    # Create progress bar
    get_novel_page.bar = tqdm(total=get_novel_page.chapter_href_list_count, colour='#39c6f9')
    get_novel_page.bar.set_description('DownLoad')

    if select == 'y':
        # Use "map" to output one file
        frp: TextIO = open(f'./Download/{get_novel_page.novel_title}.txt', 'w', encoding='utf-8')
        result = download_pool.map(get_novel_page.write_novel_text, chapter_list)

        for each in result:
            frp.write(each)
        frp.close()
    else:
        # Output each page as a file
        get_novel_page.mode = 1
        if not os.access(f'./Download/{get_novel_page.novel_title}', os.W_OK):
            os.mkdir(f'./Download/{get_novel_page.novel_title}')

        for i, each in enumerate(chapter_list):
            download_pool.submit(get_novel_page.write_novel_text, each, i)

    # End download thread
    download_pool.shutdown(wait=True)
    get_novel_page.bar.close()
    print('Complete.')

    return True


if __name__ == '__main__':
    print('\033[32;4m测试网站连通性...\033[0m')
    # Choose accessible websites
    try:
        Url, searchUrl, Key, ping_result = website_select()
    except ConnectionError as e:
        print(e)
        os.system('pause')
        exit()

    print(
        '\n\033[34;1m使用说明:\033[0m\n'
        '在下载时请不要中断程序,除非不再需要下载内容;\n'
        '\033[32m在选择下载内容时,请查看网站是否更新了内容,本程序暂未提供内容检测;\033[0m\n\n'
        '正式版1.3'
    )
    time.sleep(0.5)

    while True:
        if ping_result:
            getNovelPage = primaryAddress.GetFromBQ1(Url, './Download')
        else:
            print('\033[33m当前网站无法访问,将切换至备用网站\033[0m')
            getNovelPage = primaryAddress.GetFromBQ2(Url, './Download')

        if not main(getNovelPage, searchUrl, Key):
            print('\033[31mSomething wrong...\033[0m')

        choice: str = selection('\n\033[32mEnd the progres? (y/n)\033[0m\n')
        if choice == 'y':
            break
        time.sleep(0.5)
        os.system('cls')

    print('Exit')
    os.system('pause')
