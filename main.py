import os
import time

from NovelModel import GetNovel
from NovelModel.models import GetFromBQ2, GetFromBQ1
from config import logger
from server import server_forever
from util import target_web_ping, user_select


def run(model: GetNovel, search_url: str, key: str) -> None:
    while True:
        try:
            server_forever(model, search_url, key)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f'Error in server: {e!r}')

        if user_select('\n\033[32m终止程序? (Y/n)\033[0m\n') == 'y':
            break

        time.sleep(0.5)
        os.system('cls')

    logger.info('程序退出')
    os.system('pause')


def main() -> None:
    logger.info('测试网站连通性...')

    try:
        url, search_url, key, ping_result = target_web_ping()
    except ConnectionError as e:
        logger.error(f'Can not check connection: {e!r}')
        os.system('pause')
        exit()

    print(
        '\n\033[34;1m使用说明:\033[0m\n'
        '在下载时请不要中断程序,除非不再需要下载内容;\n'
        '\033[32m在选择下载内容时,请查看网站是否更新了内容,本程序暂未提供内容检测;\033[0m\n\n'
    )

    time.sleep(0.5)

    if ping_result:
        getNovelPage = GetFromBQ1(url, './Download')
    else:
        getNovelPage = GetFromBQ2(url, './Download')

    run(getNovelPage, search_url, key)


if __name__ == '__main__':
    main()
