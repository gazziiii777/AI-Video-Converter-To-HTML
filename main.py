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
from app.service.site_services.neuronwriter.logic import NeuronwriterLogic
import config.config
from config.config import PATH_TO_IMG, PATH_TO_ANALYSIS_RESULTS
from app.service.browser.youtube_downloader import YouTubeDownloader
from app.service.site_services.dataforseo.logic import AsyncGoogleImagesScraper


async def retry_async_function(
    async_func,
    max_retries: int = 3,
    delay: float = 1.0
):
    """
    Повторяет вызов async_func при ошибке.

    :param async_func: Асинхронная функция (без вызова, просто передать `converter.process_files`)
    :param max_retries: Сколько всего попыток (включая первую)
    :param delay: Задержка между попытками (секунды)
    """
    for attempt in range(1, max_retries + 1):
        try:
            return await async_func()
        except Exception:
            if attempt == max_retries:
                raise  # Если попытки кончились — пробрасываем ошибку
            await asyncio.sleep(delay)


async def main():
    start_time = perf_counter()  # Засекаем время начала

    # # # # Инициализация компонентов
    transcriber = MediaTranscriber(

        model_name="base",
        language="en"
    )
    client = ClaudeClient()
    app = AppLogic(transcriber, client)
    # # # # # # downloader_video = YouTubeDownloader()
    # # # # # await downloader_video.search_and_download("Prusa Core One review")

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
    #         await downloader.save_clean_page_content(url, "Prusa CORE One")

    #     print(first_url)
    #     # Скачиваем и фильтруем изображения только с первого сайта
    #     await downloader.download_images(first_url)

    #     await downloader.filter_images_by_size(
    #         min_width=600,
    #         min_height=400,
    #         verbose=True
    #     )

    urls = await get_google_links("Prusa Core One review")
    async with WebsiteParser(headless=True) as downloader:
        # Скачиваем текст с каждого сайта
        for url in urls:
            url = url.strip()  # Убираем лишние пробелы и символы новой строки
            print(f"Скачиваем контент с сайта: {url}")
            await downloader.save_clean_page_content(url, "Prusa Core One in-depth review")

        # print(first_url)
        # # Скачиваем и фильтруем изображения только с первого сайта
        # await downloader.download_images(first_url)

    # await downloader.filter_images_by_size(
    #     min_width=350,
    #     min_height=350,
    #     verbose=True
    # )

    a = AsyncGoogleImagesScraper()
    b = await a.get_product_images("prusa core one")

    # async with WebsiteParser(headless=True) as downloader:
    #     # Скачиваем текст с каждого сайта
    #     for url in b:
    #         url = url.strip()  # Убираем лишние пробелы и символы новой строки
    #         # print(f"Скачиваем контент с сайта: {url}")
    #         # await downloader.save_clean_page_content(url, "Prusa Core One in-depth review")

    #         # Скачиваем и фильтруем изображения только с первого сайта
    #         await downloader.download_images(url)

    async with WebsiteParser(headless=True) as downloader:
        await downloader.filter_images_by_size(
            min_width=600,
            min_height=400,
            verbose=True
        )

    llm_client = GPTClient()
    processor = ImageProcessor(llm_client)
    await processor.delete_duplicates()
    await processor.process_directory(
        image_dir=PATH_TO_IMG,
        output_file=PATH_TO_ANALYSIS_RESULTS
    )

    # Обработка видео
    text = await app.process_videos(
        folder_path="data/videos",
        output_prefix="result_"
    )

    # Выполнение диалога
    await app.run_dialogue(
        initial_text=text,
        json_file_path="prompts.json"
    )

    converter = MarkdownToHTMLConverter()
    await converter.process_files()
    # converter = MarkdownToHTMLConverter()
    # await converter.process_files()
    # print(config.TOTAL_PRICE)
    # end_time = perf_counter()  # Засекаем время окончания
    # print(f"Программа выполнилась за {end_time - start_time:.2f} секунд")
    neuronwriter = NeuronwriterLogic(client)
    await neuronwriter.neuronwriter_logic()

    # b = await YouTubeDownloader().parse_channel_videos()
    # c = await YouTubeDownloader().search("Prusa CORE One Review", True)
    # # c = await YouTubeDownloader().search_and_download("Prusa CORE One Review")
    # print(b)
    # print(c)


if __name__ == "__main__":
    asyncio.run(main())
