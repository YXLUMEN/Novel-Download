import argparse
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

import alternateAddress
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

parsers = argparse.ArgumentParser()
parsers.add_argument(
    '-MT', '--thread', default=32, type=int, required=False,
    help='最大线程数,根据计算机性能决定,不建议太大'
)


def main(get_novel_page, search_url: str, key: str):
    # search the novel by its title and author's name
    while True:
        search_char = input('\033[36;1m请输入查询的小说名称:\033[0m ')
        print('\033[32m开始查找...\033[0m')
        html = get_html(search_url, params={key: search_char})
        search_result = get_novel_page.search_page_analysis(html)

        if not search_result:
            print('\033[31mError\033[0m')
            return False

        if not get_novel_page.search_results_len:
            print('\n搜索结果为空,换一个关键词吧~')
            time.sleep(1)
            continue
        # end the search
        select = selection('\033[34;1m是否结束查询? (y/n)\033[0m \n')
        if select.lower() == 'y':
            break
    del html

    while True:
        select = input('\033[36;1m请选择小说序号:\033[0m ')
        if select.isdigit():
            select = int(select) - 1
            if 0 <= select < get_novel_page.search_results_len:
                break
            print('\033[31m请输入整数,且不小于0不大于搜索结果数\033[0m')
        else:
            print('\033[31m请输入整数\033[0m')

    chapter_list = get_novel_page.chapter_page_analysis(select)
    if not chapter_list:
        print('\033[31mError\033[0m')
        return False

    pages = get_novel_page.chapter_href_list_len
    print(f'\033[32;1m当前共{pages}章\033[0m')

    for outPageNums, titleValue in enumerate(chapter_list.values(), 1):
        print(f'{titleValue}')
        if outPageNums % 10 == 0:
            select = selection('\033[36;1m是否显示接下来的章节名?\033[0m (y/n)\n')
            if select.lower() == 'y':
                pass
            else:
                break

    select = selection('\033[36;1m是否下载?\033[0m (y/n)\n')
    if select.lower() == 'n':
        return True
    chapter_list = list(chapter_list)
    while True:
        time.sleep(0.5)
        start = input('\033[36;1m选择起始章节,如需要全部,输入all,否则输入整数:\033[0m ')
        # break the loop
        if start.lower() == 'all':
            break
        # "start" will be defined as an int
        if not start.isdigit():
            print('\033[33;1m章节目录必须是整数!\033[0m')
            continue
        start = int(start)
        if start < 0 or start > pages:
            print('\033[33;1m选择不能小于0或大于最大章节数\033[0m')
            continue

        end = input('\033[36;1m选择终止章节,如不输入默认选择最后一章,否则输入整数:\033[0m ')
        if end == '':
            chapter_list = chapter_list[start:]
            get_novel_page.chapter_href_list_len = pages - start
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
        chapter_list = chapter_list[start:end]
        get_novel_page.chapter_href_list_len = end - start
        break

    arg = parsers.parse_args()
    if not os.access('./Download', os.W_OK):
        os.mkdir('./Download')

    download_pool = ThreadPoolExecutor(max_workers=arg.thread)

    select = selection('\033[36;1m是否输出单个文件,即所有章节包含在一个文本文档中?(y/n)\033[0m\n')
    print('Start processing...')
    get_novel_page.bar = tqdm(total=get_novel_page.chapter_href_list_len)
    get_novel_page.bar.set_description('DownLoad')
    if select == 'y':
        frp = open(f'./Download/{get_novel_page.novel_title}.txt', 'w', encoding='utf-8')
        result = download_pool.map(get_novel_page.novel_text_analysis, chapter_list)
        for each in result:
            frp.write(each)
        frp.close()
    else:
        get_novel_page.mode = 1
        if not os.access(f'./Download/{get_novel_page.novel_title}', os.W_OK):
            os.mkdir(f'./Download/{get_novel_page.novel_title}')
        for i, each in enumerate(chapter_list):
            download_pool.submit(get_novel_page.novel_text_analysis, each, i)
    download_pool.shutdown(wait=True)
    get_novel_page.bar.close()

    return True


if __name__ == '__main__':
    print('\033[32;4m测试网站连通性...\033[0m')
    try:
        Url, searchUrl, Key, ping_result = website_select()
    except ConnectionError as e:
        print(e)
        os.system('pause')
        exit()

    print(
        '\n\033[34;1m使用说明:\033[0m\n'
        '在下载时请不要中断程序,除非不再需要下载内容;\n'
        '\033[32m在选择下载内容时,请查看网站是否更新了内容,本程序暂未提供内容检测;\033[0m\n'
        '可以手动增加线程数,这一般会提高下载速度,在程序所在目录打开CMD窗口,输入 NovelDown --thread <num> 使得下载线程更改为<num>;\n'
        '\033[33m重构完成,正在测试\033[0m\n'
        '测试版2.2'
    )
    time.sleep(0.5)

    while True:
        if ping_result:
            getNovelPage = primaryAddress.HTTPRequest(Url, './Download')
        else:
            print('\033[33m当前网站无法访问,将切换至备用网站\033[0m')
            getNovelPage = alternateAddress.HTTPRequest(Url, './Download')

        if not main(getNovelPage, searchUrl, Key):
            print('\033[31mSomething wrong...\033[0m')

        choice = selection('\n\033[32mEnd the progres? (y/n)\033[0m\n')
        if choice == 'y':
            break
        time.sleep(1)
        os.system('cls')

    print('Exit')
    os.system('pause')
