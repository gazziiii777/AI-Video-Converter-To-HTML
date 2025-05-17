import os
import json
from typing import List, Dict
from app.client.neurowriter import NeuroWriter
from text import TITLE_PROMPT, DESC_PROMPT, H1_PROMPT
from typing import Any
import re
from bs4 import BeautifulSoup
from typing import Optional
import aiofiles


class AppLogic:
    def __init__(self, transcriber, client):
        self.transcriber = transcriber
        self.client = client

    async def process_videos(self, folder_path: str, output_prefix: str) -> str:
        """Обрабатывает видео и возвращает объединённый текст"""
        # self.transcriber.process_folder(
        #     folder_path=folder_path,
        #     output_prefix=output_prefix
        # )
        return self.transcriber.merge_txt_files(folder_path='data/txt_output')

    async def run_dialogue(self, initial_text: str, json_file_path: str) -> None:
        """Выполняет диалог на основе prompt.json"""
        messages = [
            {"role": "user", "content": f"Context: {initial_text}\n\nAnswer only based on the context provided. The context definitely contains the answer. Don't quote the text"}
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

                    if prompt_counter in [10, 25, 26, 28, 31, 34]:
                        answer = await self.client.ask_claude_web(
                            max_tokens=step["max_tokens"],
                            messages=messages,
                            file_name=f"data/prompts_out/output_prompt_{prompt_counter}.txt"
                        )
                    else:
                        answer = await self.client.ask_claude(
                            max_tokens=step["max_tokens"],
                            messages=messages,
                            file_name=f"data/prompts_out/output_prompt_{prompt_counter}.txt"
                        )
                    # messages_remove_quotes = [
                    #     {"role": "user",
                    #         "content": f"Context: {answer}\n\nRemove all quotes from this text (you can rewrite it in other words, but without quotes!)"}
                    # ]
                    # answer_without_quotes = await self.client.ask_claude(
                    #     max_tokens=step["max_tokens"],
                    #     messages=messages_remove_quotes,
                    #     file_name=f"data/prompts_out/output_prompt_{prompt_counter}.txt"
                    # )
                    prompt_counter += 1

                    messages.append(
                        {"role": "assistant", "content": answer})

    async def read_file(path: str, encoding: str = "utf-8") -> str:
        try:
            with open("data/combined.html", "r", encoding="utf-8") as file:
                sample_text = file.read()
            return sample_text
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            return ""

    async def insert_h1_raw(self, filepath: str, h1_text: str) -> Optional[str]:
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            html: str = await f.read()

        body_index = html.lower().find("<body")
        if body_index == -1:
            print("Тег <body> не найден.")
            return None

        # Найти конец тега <body>
        body_end = html.find(">", body_index)
        if body_end == -1:
            print("Некорректный тег <body>.")
            return None

        insert_position = body_end + 1
        h1_tag = f"<h1>{h1_text}</h1>\n"
        result_html = html[:insert_position] + h1_tag + html[insert_position:]

        if filepath:
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(result_html)
 
        return result_html

    async def format_and_ask(self, client: Any, prompt_template: str, values: str, label: str) -> None:
        messages = [
            {"role": "user", "content": f"Context: {prompt_template.format(**{label: values})}"}]
        try:
            answer = await client.ask_claude(max_tokens=2000, messages=messages)
            answer = answer.lstrip()
            cleaned_answer = re.sub(
                rf"^{label}:\s*", "", answer, flags=re.IGNORECASE)
            print(f"{label}:", cleaned_answer)
            return cleaned_answer

        except Exception as e:
            print(f"Error querying Claude for {label}: {e}")

    async def remove_hash_prefix(self, line):
        return line.lstrip('#') if line.startswith('#') else line

    async def neurowriter_logic(self) -> None:
        writer = NeuroWriter()
        sample_text = await self.read_file()

        if not sample_text:
            return

        try:
            content, query = await writer.import_content(sample_text)
            terms = content.get("terms", {})
            titles = '\n'.join(item['t'] for item in terms.get("title", []))
            desc = '\n'.join(item['t'] for item in terms.get("desc", []))
            h1 = '\n'.join(item['t'] for item in terms.get("h1", []))

            title = await self.format_and_ask(self.client, TITLE_PROMPT, titles, "titles")
            desc = await self.format_and_ask(self.client, DESC_PROMPT, desc, "desc")
            h1 = await self.format_and_ask(self.client, H1_PROMPT, h1, "h1")
            h1 = await self.remove_hash_prefix(h1)
            sample_text = await self.insert_h1_raw("data/combined.html", h1)
            await writer.import_title_and_desc(sample_text, title, desc, query)
        except Exception as e:
            print(f"Error in neurowriter_logic: {e}")
