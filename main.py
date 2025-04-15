import asyncio
from app.app_logic import AppLogic
# Предполагается, что эти классы определены
from app.services.transcriber import MediaTranscriber
from app.api.claude import ClaudeClient  # в других файлах
from app.services.markdown_to_HTML import MarkdownToHTMLConverter
from app.services.website_parser import WebsiteParser


async def main():
    # Инициализация компонентов
    # transcriber = MediaTranscriber(
    #     model_name="base",
    #     language="en"
    # )

    # client = ClaudeClient()
    # app = AppLogic(transcriber, client)

    async with WebsiteParser(headless=True) as downloader:
        # Пример URL для скачивания изображений
        await downloader.save_clean_page_content("https://www.prusa3d.com/product/prusa-core-one/")
        await downloader.download_images(
            "https://www.prusa3d.com/product/prusa-core-one/",
            "downloaded_images"
        )

        # 2. Фильтрация по размеру
        filter_results = WebsiteParser.filter_images_by_size(
            "downloaded_images",
            min_width=300,
            min_height=300,
            verbose=True
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
