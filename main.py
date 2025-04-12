import asyncio

from services.media_transcriber import MediaTranscriber
from ai_clients.claude_client import ClaudeClient

from config import PROMPT_1, PROMPT_2, PROMPT_3, PROMPT_4
import time
import json
import os


async def main():
    # Транскрибация видео
    transcriber = MediaTranscriber(
        model_name="base",
        language="en"
    )

    transcriber.process_folder(
        folder_path="videos",
        output_prefix="result_"
    )

    text = transcriber.merge_txt_files()
    client = ClaudeClient()  # Замените на ваш клиент для Claude

    # Инициализация диалога
    messages = [
        {"role": "user", "content": f"Context: {text}\n\nAnswer only based on the context provided. The context definitely contains the answer."}
    ]

    # Путь к JSON-файлу (можно вынести в параметры)
    json_file_path = "prompt.json"  # или любой другой путь

    # Проверяем существование файла
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"JSON файл не найден: {json_file_path}")

    # Читаем JSON из файла
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Проверяем наличие нужной структуры
    if not data.get("prompts"):
        raise ValueError("JSON не содержит ожидаемой структуры с 'prompts'")

    prompt_counter = 1

    # Итерируемся по всем prompts в JSON
    for prompt_group in data["prompts"]:
        if not prompt_group.get("content", {}).get("steps"):
            continue

        # Итерируемся по steps внутри каждого prompt
        for step in prompt_group["content"]["steps"]:
            if step.get("isEnabled", False) and step.get("type") == "message":
                # Добавляем новый запрос пользователя
                messages.append({"role": "user", "content": step["text"]})

                # Отправляем весь history диалога в Claude
                answer = await client.ask_claude(
                    messages=messages,
                    file_name=f"prompts_out/output_prompt_{prompt_counter}.txt"
                )
                prompt_counter += 1

                # Добавляем ответ ассистента в history
                messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    asyncio.run(main())
