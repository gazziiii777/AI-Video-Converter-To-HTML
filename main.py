import asyncio
from app.app_logic import AppLogic
# Предполагается, что эти классы определены
from app.service.media.transcriber import MediaTranscriber
from app.client.claude import ClaudeClient  # в других файлах
from app.client.gpt import GPTClient  # в других файлах
from app.service.export.markdown_to_html import MarkdownToHTMLConverter
from app.service.browser.website_parser import WebsiteParser
from app.service.media.image_analyzer import ImageProcessor
# from app.client.re1111 import ask
from app.service.browser.youtube_downloader import YouTubeDownloader
from app.service.browser.link_searcher import get_google_links
from time import perf_counter
from app.app_logic import AppLogic
from app.service.neurowriter.logic import NeurowriterLogic


async def main():
    # start_time = perf_counter()  # Засекаем время начала

    # # # # Инициализация компонентов
    transcriber = MediaTranscriber(

        model_name="base",
        language="en"
    )

    client = ClaudeClient()
    app = AppLogic(transcriber, client)
    # # # # downloader_video = YouTubeDownloader()
    # # # # await downloader_video.search_and_download("Prusa Core One review")

    # urls = await get_google_links("Prusa CORE One")

    # with open('links.txt', 'r') as file:
    #     first_url = file.readlines()

    # # # # Применяем скачивание только к первому URL для изображений
    # # # # Убираем возможные лишние пробелы или символы новой строки
    # first_url = first_url[0].strip()
    # async with WebsiteParser(headless=True) as downloader:
    #     # Скачиваем текст с каждого сайта
    #     for url in urls:
    #         url = url.strip()  # Убираем лишние пробелы и символы новой строки
    #         print(f"Скачиваем контент с сайта: {url}")
    #         await downloader.save_clean_page_content(url, "Prusa CORE One")

    #     print(first_url)
    #     # Скачиваем и фильтруем изображения только с первого сайта
    #     await downloader.download_images(first_url)

    #     await downloader.filter_images_by_size(
    #         min_width=350,
    #         min_height=350,
    #         verbose=True
    #     )

    # urls = await get_google_links("Prusa Core One in-depth review")
    # async with WebsiteParser(headless=True) as downloader:
    #         # Скачиваем текст с каждого сайта
    #         for url in urls:
    #             url = url.strip()  # Убираем лишние пробелы и символы новой строки
    #             print(f"Скачиваем контент с сайта: {url}")
    #             await downloader.save_clean_page_content(url, "Prusa Core One in-depth review")

    #         # print(first_url)
    #         # # Скачиваем и фильтруем изображения только с первого сайта
    #         # await downloader.download_images(first_url)

    #         # await downloader.filter_images_by_size(
    #         #     min_width=350,
    #         #     min_height=350,
    #         #     verbose=True
    #         # )

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

    # converter = MarkdownToHTMLConverter()
    # await converter.process_files()

    # end_time = perf_counter()  # Засекаем время окончания
    # print(f"Программа выполнилась за {end_time - start_time:.2f} секунд")
    neruwriter = NeurowriterLogic(client)
    await neruwriter.neurowriter_logic()
if __name__ == "__main__":
    asyncio.run(main())
