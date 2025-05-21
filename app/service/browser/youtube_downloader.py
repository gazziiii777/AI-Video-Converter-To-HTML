from yt_dlp import YoutubeDL
import os
import re
from config import PATH_TO_VIDEOS


class YouTubeDownloader:
    """
    Класс для поиска и загрузки видео с YouTube без шортсов.

    Параметры:
    max_results (int): максимальное число загружаемых видео.
    min_duration (int): минимальная длительность видео в секундах (чтобы исключить шортсы).
    output_template (str): шаблон имени сохраняемых файлов.
    format (str): формат загрузки видео и аудио.
    merge_format (str): формат объединённого файла.
    """

    def __init__(self,
                 max_results: int = 5,
                 min_duration: int = 60,
                 output_template: str = f'{PATH_TO_VIDEOS}/%(title)s.%(ext)s',
                 format: str = 'bestvideo+bestaudio/best',
                 merge_format: str = 'mp4'):
        self.max_results = max_results
        self.min_duration = min_duration
        self.output_template = output_template
        self.format = format
        self.merge_format = merge_format

    async def _search(self, query: str) -> list[str]:
        """
        Выполняет поиск по запросу и возвращает список ссылок на видео,
        исключая YouTube Shorts.
        """
        search_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': 'in_playlist',
            'force_generic_extractor': True,
            'noplaylist': True
        }
        with YoutubeDL(search_opts) as ydl:
            # Ищем в 2 раза больше, чтобы потом отфильтровать шортсы
            query_str = f"ytsearch{self.max_results * 2}:{query}"
            info = ydl.extract_info(query_str, download=False)
            entries = info.get('entries', []) or []

        links = []
        for entry in entries:
            url = entry.get('url', '')
            duration = entry.get('duration', 0)
            # Фильтруем шортсы по URL и длительности
            if 'shorts' not in url and duration >= self.min_duration:
                links.append(f"https://www.youtube.com/watch?v={entry['id']}")
            if len(links) >= self.max_results:
                break

        print(f"ЮТУБ ССЫЛКИ!! {links}")
        return links

    async def _download(self, links: list[str]) -> None:
        """
        Скачивает список видео по ссылкам.
        """
        folder = PATH_TO_VIDEOS
        dl_opts = {
            'outtmpl': self.output_template,
            'format': self.format,
            'merge_output_format': self.merge_format
        }
        with YoutubeDL(dl_opts) as ydl:
            ydl.download(links)

        for file in os.listdir(folder):
            full_path = os.path.join(folder, file)
            if os.path.isfile(full_path):
                name, ext = os.path.splitext(file)
                # Берем только буквы/цифры
                first_word = re.split(r'\W+', name)[0]
                if first_word:
                    new_filename = os.path.join(folder, f"{first_word}{ext}")
                    if full_path != new_filename:
                        os.rename(full_path, new_filename)

    async def search_and_download(self, query: str) -> None:
        """
        Полный процесс: поиск и загрузка видео по запросу.
        """
        links = await self._search(query)
        if not links:
            print("Видео не найдены.")
            return
        print(f"Найдено и будет загружено: {len(links)} видео.")
        for idx, link in enumerate(links, 1):
            print(f"{idx}. {link}")
        await self._download(links)


if __name__ == '__main__':
    query = input("Введите поисковый запрос: ")
    downloader = YouTubeDownloader()
    downloader.search_and_download(query)
