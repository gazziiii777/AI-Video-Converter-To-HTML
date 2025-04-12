import asyncio
from app.services.app_logic import AppLogic
# Предполагается, что эти классы определены
from app.services.ai.media_transcriber import MediaTranscriber
from app.ai_clients.claude_client import ClaudeClient  # в других файлах


async def main():
    # Инициализация компонентов
    transcriber = MediaTranscriber(
        model_name="base",
        language="en"
    )

    client = ClaudeClient()
    app = AppLogic(transcriber, client)

    # Обработка видео
    text = await app.process_videos(
        folder_path="inputs/videos",
        output_prefix="result_"
    )

    # Выполнение диалога
    await app.run_dialogue(
        initial_text=text,
        json_file_path="prompts.json"
    )

if __name__ == "__main__":
    asyncio.run(main())
