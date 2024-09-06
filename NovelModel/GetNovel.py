from abc import abstractmethod


class GetNovel:
    __slots__ = (
        'url', 'download_dir', 'mode', 'search_results_count', 'chapters_count',
        'novel_title', 'search_results_list', 'chapter_href_dict', 'bar')

    def __init__(self, url: str, download_dir: str):
        self.download_dir: str = download_dir
        self.mode: int = 0

        # Website's url
        self.url: str = url
        # search results' num of novel
        self.search_results_count: int = 0
        # all chapters of the novel
        self.chapters_count: int = 0
        self.novel_title: str = ''
        # to the novel's main page
        # 根据网站,最大100条
        self.search_results_list: list = []

        self.bar = None

    @abstractmethod
    def search_novel(self, html_page: str) -> bool:
        pass

    @abstractmethod
    def novel_homepage(self, novel_name_index: int):
        pass

    @abstractmethod
    def novel_main_text(self, href_key: str) -> str:
        pass

    def write_novel_text(self, href_key: str, index: int = 0):
        title, text = self.novel_main_text(href_key)
        if not title:
            print(f'\033[31mWriteText\033[0m -> {href_key}')
            return ''

        text: str = f'{title}\n\n{text}\n\n'
        if self.mode:
            with open(f'{self.download_dir}/{self.novel_title}/{index} {title}.txt', 'w', encoding='utf-8') as f:
                f.write(text)
        self.bar.update(1)

        return text
