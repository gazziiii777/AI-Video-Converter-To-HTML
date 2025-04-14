import asyncio
from app.app_logic import AppLogic
# Предполагается, что эти классы определены
from app.services.media.transcriber import MediaTranscriber
from app.api.claude import ClaudeClient  # в других файлах
from app.services.parsing.instagram import Instagram


async def main():
    # # Инициализация компонентов
    # transcriber = MediaTranscriber(
    #     model_name="base",
    #     language="en"
    # )

    # client = ClaudeClient()
    # app = AppLogic(transcriber, client)

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

    instagram = Instagram()
    await instagram.open_and_auth()

if __name__ == "__main__":
    asyncio.run(main())
