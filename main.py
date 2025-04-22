import asyncio
from app.app_logic import AppLogic
# Предполагается, что эти классы определены
from app.utils.transcriber import MediaTranscriber
from app.client.claude import ClaudeClient  # в других файлах
from app.client.gpt import GPTClient  # в других файлах
from app.utils.markdown_to_html import MarkdownToHTMLConverter
from app.utils.website_parser import WebsiteParser
from app.utils.image_analyzer import ImageProcessor
# from app.client.re1111 import ask


async def main():
    # # Инициализация компонентов
    # transcriber = MediaTranscriber(

    #     model_name="base",
    #     language="en"
    # )

    # client = ClaudeClient()
    # app = AppLogic(transcriber, client)

    # with open('links.txt', 'r') as file:
    #     urls = file.readlines()

    # # Применяем скачивание только к первому URL для изображений
    # # Убираем возможные лишние пробелы или символы новой строки
    # first_url = urls[0].strip()

    # async with WebsiteParser(headless=True) as downloader:
    #     # Скачиваем текст с каждого сайта
    #     for url in urls:
    #         url = url.strip()  # Убираем лишние пробелы и символы новой строки
    #         print(f"Скачиваем контент с сайта: {url}")
    #         await downloader.save_clean_page_content(url)

    #     # Скачиваем и фильтруем изображения только с первого сайта
    #     await downloader.download_images(first_url)
    #     filter_results = await downloader.filter_images_by_size(
    #         min_width=300,
    #         min_height=300,
    #         verbose=True
    #     )

    # llm_client = GPTClient()
    # processor = ImageProcessor(llm_client)

    # await processor.process_directory(
    #     image_dir="data/img",
    #     output_file="data/img/analysis_results.json"
    # )

    # Обработка видео
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
