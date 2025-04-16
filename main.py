import asyncio
from app.app_logic import AppLogic
# Предполагается, что эти классы определены
# from app.utils.transcriber import MediaTranscriber
from app.client.claude import ClaudeClient  # в других файлах
from app.client.gpt import GPTClient  # в других файлах
from app.utils.markdown_to_HTML import MarkdownToHTMLConverter
from app.utils.website_parser import WebsiteParser
from app.utils.image_analyzer import ImageProcessor


async def main():
    # Инициализация компонентов
    # transcriber = MediaTranscriber(
    #     model_name="base",
    #     language="en"
    # )

    # client = ClaudeClient()
    # app = AppLogic(transcriber, client)

    # async with WebsiteParser(headless=True) as downloader:
    #     # Пример URL для скачивания изображений
    #     await downloader.save_clean_page_content("https://www.prusa3d.com/product/prusa-core-one/")
    #     await downloader.download_images(
    #         "https://www.prusa3d.com/product/prusa-core-one/",
    #     )

    #     # 2. Фильтрация по размеру
    #     filter_results = await downloader.filter_images_by_size(
    #         min_width=300,
    #         min_height=300,
    #         verbose=True
    #     )

    llm_client = GPTClient()
    processor = ImageProcessor(llm_client)

    await processor.process_directory(
        image_dir="data/img",
        output_file="data/img/analysis_results.json"
    )

    # # Обработка видео
    # text = await app.process_videos(
    #     folder_path="inputs/videos",
    #     output_prefix="result_"
    # )

    # # Выполнение диалога
    # await app.run_dialogue(
    #     initial_text=text,
    #     json_file_path="prompts.json"
    # )

    # converter = MarkdownToHTMLConverter()
    # converter.process_files()

if __name__ == "__main__":
    asyncio.run(main())
