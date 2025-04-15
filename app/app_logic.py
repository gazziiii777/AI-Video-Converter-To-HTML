import os
import json
from typing import List, Dict


class AppLogic:
    def __init__(self, transcriber, client):
        self.transcriber = transcriber
        self.client = client

    async def process_videos(self, folder_path: str, output_prefix: str) -> str:
        """Обрабатывает видео и возвращает объединённый текст"""
        self.transcriber.process_folder(
            folder_path=folder_path,
            output_prefix=output_prefix
        )
        return self.transcriber.merge_txt_files(folder_path='results/txt_output')

    async def run_dialogue(self, initial_text: str, json_file_path: str) -> None:
        """Выполняет диалог на основе prompt.json"""
        messages = [
            {"role": "user", "content": f"Context: {initial_text}\n\nAnswer only based on the context provided. The context definitely contains the answer."}
        ]

        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON файл не найден: {json_file_path}")

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data.get("prompts"):
            raise ValueError(
                "JSON не содержит ожидаемой структуры с 'prompts'")

        prompt_counter = 1

        for prompt_group in data["prompts"]:
            if not prompt_group.get("content", {}).get("steps"):
                continue

            for step in prompt_group["content"]["steps"]:
                if step.get("isEnabled", False) and step.get("type") == "message":
                    messages.append({"role": "user", "content": step["text"]})

                    answer = await self.client.ask_claude(
                        max_tokens=step["max_tokens"],
                        messages=messages,
                        file_name=f"data/results/prompts_out/output_prompt_{prompt_counter}.txt"
                    )
                    prompt_counter += 1

                    messages.append({"role": "assistant", "content": answer})
