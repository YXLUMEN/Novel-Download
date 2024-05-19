from func_selection import main
from NovelServices import GetFromBQ1
from NovelServices import GetFromBQ2
from utility import *

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
        '正式版2.0'
    )
    time.sleep(0.5)

    while True:
        if ping_result:
            getNovelPage: GetFromBQ1 = GetFromBQ1(Url, './Download')
        else:
            print('\033[33m当前网站无法访问,将切换至备用网站\033[0m')
            getNovelPage: GetFromBQ2 = GetFromBQ2(Url, './Download')

        if not main(getNovelPage, searchUrl, Key):
            print('\033[31mSomething wrong...\033[0m')

        choice: str = selection('\n\033[32mEnd the progres? (y/n)\033[0m\n')
        if choice == 'y':
            break

        time.sleep(0.5)
        os.system('cls')

    print('Exit')
    os.system('pause')
