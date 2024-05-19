from concurrent.futures import ThreadPoolExecutor
from itertools import islice, tee
from typing import TextIO, Generator

from tqdm import tqdm

from NovelServices import GetFromBQ2
from utility import *


def main(get_novel_page: GetFromBQ2, search_url: str, key: str):
    while True:
        search_string: str = input('\033[36;1m请输入查询的小说名称:\033[0m ')
        print('\033[32m开始查找...\033[0m')

        html: str = html_request(search_url, params={key: search_string})
        search_result: bool = get_novel_page.search_novel(html)

        if not search_result:
            print('\033[31mError\033[0m')
            return False

        if not get_novel_page.search_results_count:
            print('\n搜索结果为空,换一个关键词吧~')
            time.sleep(1)
            continue

        select: str = selection('\033[34;1m是否结束查询? (y/n)\033[0m \n')
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

    url: str = get_novel_page.url + get_novel_page.search_results_list[select]
    select_temp: str = selection('是否打开浏览器确认?(y/n)\n')

    if select_temp == 'y':
        os.system(f'start {url}')

    print('正在获取...')
    time.sleep(0.5)
    del url, select_temp

    chapter_generator, chapter_generator_back = tee(get_novel_page.novel_homepage(select))
    chapter_url_generator: Generator = (url[0] for url in chapter_generator_back)

    if not chapter_generator:
        print('\033[31mError\033[0m')
        return False

    temp_counting: int = 0
    for outPageNums, item in enumerate(chapter_generator, 1):
        print(f'{item[1]}')
        temp_counting += 1
        if outPageNums % 10 == 0:
            select = selection('\033[36;1m是否显示接下来的章节名?\033[0m (y/n)\n')
            if select.lower() == 'y':
                pass
            else:
                break

    max_pages: int = sum(1 for _ in chapter_generator) + temp_counting
    get_novel_page.chapters_count = max_pages
    print(f'\033[32;1m当前共{max_pages}章\033[0m')

    del temp_counting, chapter_generator, chapter_generator_back

    select: str = selection('\033[36;1m是否下载?\033[0m (y/n)\n')
    if select.lower() == 'n':
        return True

    # 处理选项
    while True:
        time.sleep(0.5)
        start_page: int = 0
        end_page: int = max_pages

        start_page_str: str = input('\033[36;1m选择起始章节,如需要全部,输入all,否则输入整数:\033[0m ')

        # download all, break the loop
        if start_page_str.lower() == 'all':
            break

        # "start" will be defined as an int
        if not start_page_str.isdigit():
            print('\033[33;1m章节目录必须是整数!\033[0m')
            continue

        start_page = int(start_page_str)
        if start_page < 0 or start_page > max_pages:
            print('\033[33;1m选择不能小于0或大于最大章节数\033[0m')
            continue

        end_page_str: str = input('\033[36;1m选择终止章节,如不输入默认选择最后一章,否则输入整数:\033[0m ')
        if end_page_str == '':
            get_novel_page.chapters_count = max_pages - start_page
            break

        if not end_page_str.isdigit():
            print('\033[33;1m章节目录必须是整数!\033[0m')
            continue

        end_page = int(end_page_str)
        if end_page <= start_page:
            print('\033[33;1m终止章节数不能小于等于起始章节!\033[0m')
            continue

        if end_page > max_pages:
            print('\033[33;1m终止章节数不能大于最大章节!\033[0m')
            continue

        get_novel_page.chapters_count = end_page - start_page
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
    get_novel_page.bar = tqdm(total=get_novel_page.chapters_count, colour='#39c6f9')
    get_novel_page.bar.set_description('DownLoad')

    if select == 'y':
        # Use "map" to output one file
        frp: TextIO = open(f'./Download/{get_novel_page.novel_title}.txt', 'w', encoding='utf-8')

        result = download_pool.map(
            get_novel_page.write_novel_text,
            islice(chapter_url_generator, start_page, end_page))

        for each in result:
            frp.write(each)
        frp.close()
    else:
        # Output each page as a file
        get_novel_page.mode = 1
        if not os.access(f'./Download/{get_novel_page.novel_title}', os.W_OK):
            os.mkdir(f'./Download/{get_novel_page.novel_title}')

        for i, each in enumerate(islice(chapter_url_generator, start_page, end_page)):
            download_pool.submit(get_novel_page.write_novel_text, each, i)

    # End download thread
    download_pool.shutdown(wait=True)
    get_novel_page.bar.close()
    print('Complete.')

    return True
