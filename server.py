import os
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import islice, tee

from tqdm import tqdm

from NovelModel import GetNovel
from config import logger
from exceptions.custom_exception import NoResultsError, AnalysisFailed
from util import fetch_html, user_select


def server_forever(model: GetNovel, search_url: str, key: str) -> None:
    while True:
        search_string: str = input('\033[36;1m请输入查询的小说名称:  \033[0m')
        print('\033[32m开始查找...\033[0m')

        html: str = fetch_html(search_url, params={key: search_string})
        search_result: bool = model.search_index(html)

        if not search_result:
            logger.warning('未找到结果')
            raise NoResultsError

        if model.search_results_count == 0:
            print('\n搜索结果为空,换一个关键词吧~')
            time.sleep(0.5)
            continue

        if user_select('\033[34;1m是否结束查询? (y/n)\033[0m \n').lower() == 'y':
            break

    del html

    # 选择查询结果
    while True:
        select: str = input('\033[36;1m请选择小说序号:\033[0m ')

        if not select.isdigit():
            print('\033[31m请输入整数\033[0m')
            continue

        select: int = int(select) - 1
        if 0 <= select < model.search_results_count:
            break

        print('\033[31m请输入整数,且不小于0不大于搜索结果数\033[0m')

    url: str = model.url + model.search_results_list[select]

    if user_select('是否打开浏览器确认?(y/n)\n') == 'y':
        os.system(f'start {url}')

    print('正在获取...')
    time.sleep(0.5)

    del url

    chapter_generator, chapter_generator_back = tee(model.novel_homepage(select))
    chapter_url_generator = (url[0] for url in chapter_generator_back)

    if not chapter_generator:
        logger.error('章节分析失败')
        raise AnalysisFailed

    temp_counting: int = 0
    for outPageNums, item in enumerate(chapter_generator, 1):
        print(f'{item[1]}')

        temp_counting += 1
        if outPageNums % 10 != 0:
            continue

        if user_select('\033[36;1m是否显示接下来的章节名?\033[0m (y/n)\n') != 'y':
            break

    max_pages: int = sum(1 for _ in chapter_generator) + temp_counting
    model.chapters_count = max_pages
    print(f'\033[32;1m当前共{max_pages}章\033[0m')

    del temp_counting, chapter_generator, chapter_generator_back

    if user_select('\033[36;1m是否下载?\033[0m (y/n)\n') == 'n':
        return

    start_page, end_page = page_slice(max_pages, model)

    threads: int = min(32, end_page - start_page)

    if user_select(f'\033[36;1m将启动{threads}条线程,是否更改?\033[0m (y/n)\n ') == 'y':
        while True:
            threads: str = input('请输入线程数: ')
            if threads.isdigit():
                threads = int(threads)
                break

            logger.warning('只能是整数!')

    if not os.access('./Download', os.W_OK):
        os.mkdir('./Download')

    start_thread(model, threads, islice(chapter_url_generator, start_page, end_page))

    return


def start_thread(model: GetNovel, threads: int, slices: islice) -> None:
    download_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=int(threads))

    select: str = user_select('\033[36;1m是否输出单个文件,即所有章节包含在一个文本文档中? (Y/n)\033[0m\n')

    print('开始处理...')

    # Create progress bar
    model.bar = tqdm(total=model.chapters_count, colour='#39c6f9')
    model.bar.set_description('DownLoad')

    if select == 'y':
        # Use "map" to output one file
        result = download_pool.map(
            model.write_novel_text,
            slices)

        with open(f'./Download/{model.novel_title}.txt', 'w', encoding='utf-8') as f:
            for each in result:
                f.write(each)
    else:
        # Output each page as a file
        model.mode = 1
        if not os.access(f'./Download/{model.novel_title}', os.W_OK):
            os.mkdir(f'./Download/{model.novel_title}')

        for i, each in enumerate(slices):
            download_pool.submit(model.write_novel_text, each, i)

    # End download thread
    download_pool.shutdown()
    model.bar.close()


def page_slice(max_pages: int, model: GetNovel) -> tuple[int, int]:
    while True:
        time.sleep(0.5)

        start_page: int = 0
        end_page: int = max_pages

        start_page_str: str = input('\033[36;1m选择起始章节,如需要全部,输入all,否则输入整数:\033[0m ')

        # download all, break the loop
        if start_page_str == 'all':
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
            model.chapters_count = max_pages - start_page
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

        model.chapters_count = end_page - start_page
        break

    return start_page, end_page
