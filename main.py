import asyncio
from app.app_logic import AppLogic
# Предполагается, что эти классы определены
from app.utils.media.transcriber import MediaTranscriber
from app.client.claude import ClaudeClient  # в других файлах
from app.client.gpt import GPTClient  # в других файлах
from app.utils.export.markdown_to_html import MarkdownToHTMLConverter
from app.utils.browser.website_parser import WebsiteParser
from app.utils.media.image_analyzer import ImageProcessor
# from app.client.re1111 import ask
from app.utils.browser.youtube_downloader import YouTubeDownloader
from app.utils.browser.link_searcher import get_google_links


async def main():
    # # Инициализация компонентов
    # transcriber = MediaTranscriber(

    #     model_name="base",
    #     language="en"
    # )

    # client = ClaudeClient()
    # app = AppLogic(transcriber, client)
    # # downloader_video = YouTubeDownloader()
    # # await downloader_video.search_and_download("Название принтера")

    # urls = await get_google_links("Prusa CORE One")
    # with open('links.txt', 'r') as file:
    #     first_url = file.readlines()

    # # # Применяем скачивание только к первому URL для изображений
    # # # Убираем возможные лишние пробелы или символы новой строки
    # first_url = first_url[0].strip()
    # async with WebsiteParser(headless=True) as downloader:
    #     # Скачиваем текст с каждого сайта
    #     for url in urls:
    #         url = url.strip()  # Убираем лишние пробелы и символы новой строки
    #         print(f"Скачиваем контент с сайта: {url}")
    #         await downloader.save_clean_page_content(url)

    #     print(first_url)
    #     # Скачиваем и фильтруем изображения только с первого сайта
    #     await downloader.download_images(first_url)

    #     filter_results = await downloader.filter_images_by_size(
    #         min_width=300,
    #         min_height=300,
    #         verbose=True
    #     )

    # llm_client = GPTClient()
    # processor = ImageProcessor(llm_client)
    # await processor.delete_duplicates()
    # await processor.process_directory(
    #     image_dir="data/img",
    #     output_file="data/img/analysis_results.json"
    # )

    # # Обработка видео
    # text = await app.process_videos(
    #     folder_path="data/videos",
    #     output_prefix="result_"
    # )

    # # Выполнение диалога
    # await app.run_dialogue(
    #     initial_text=text,
    #     json_file_path="prompts.json"
    # )

    converter = MarkdownToHTMLConverter()
    await converter.process_files()


if __name__ == "__main__":
    asyncio.run(main())
