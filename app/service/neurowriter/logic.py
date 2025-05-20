import os
import json
from typing import List, Dict
from app.client.neurowriter import NeuroWriter
from typing import Any
import re
from bs4 import BeautifulSoup
from typing import Optional
import aiofiles
from app.service.neurowriter.parser import ParserNeuronWriter


class NeurowriterLogic:
    def __init__(self, client):
        self.json_file_path = "neurowriter_promts.json"
        self.data = self._load_json_data()
        self.client = client

    def _load_json_data(self):
        """Загружает данные из JSON файла"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise Exception(f"Файл {self.json_file_path} не найден")
        except json.JSONDecodeError:
            raise Exception("Ошибка парсинга JSON")

    async def get_prompt_by_name(self, prompt_name):
        return next((p for p in self.data['prompts'] if p['name'] == prompt_name), None)

    async def get_prompt_by_id(self, prompt_id):
        return next((p for p in self.data['prompts'] if p['number'] == prompt_id), None)

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

    async def format_and_ask(
        self,
        client: Any,
        label: str,
        value: str,
        second_label: str | None = None,  # Новый параметр (опциональный)
        second_value: str | None = None   # Новый параметр (опциональный)
    ) -> None:
        prompt_info = await self.get_prompt_by_name(label)

        # Собираем переменные для форматирования
        format_vars = {label: value}
        if second_label and second_value:
            format_vars[second_label] = second_value

        messages = [
            {
                "role": "user",
                "content": f"Context: {prompt_info.get('text').format(**format_vars)}"
            }
        ]

        try:
            answer = await client.ask_claude(max_tokens=2000, messages=messages)
            answer = answer.lstrip()
            cleaned_answer = re.sub(
                rf"^{label}:\s*", "", answer, flags=re.IGNORECASE)
            cleaned_answer = await self.remove_hash_prefix(cleaned_answer)
            return cleaned_answer
        except Exception as e:
            print(f"Error querying Claude for {label}: {e}")

    async def get_not_included_keywords(self, text):
        lines = text.split('\n')
        not_included = []

        for line in lines:
            if '|' in line:  # Проверяем, что это строка таблицы
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3 and parts[1].strip() == 'Not Included':
                    not_included.append(parts[0].strip())

        return ", ".join(not_included)

    async def h2_dialogue(self, client: Any, value: str, html: str) -> None:
        """Выполняет диалог на основе prompt.json

        Args:
            h2: Заголовок для форматирования промпта
            value: Значение для подстановки в промпт
            html: HTML-контент для использования в диалоге
        """
        messages = []

        for step_id in [4, 5, 6, 7]:
            prompt_info = await self.get_prompt_by_id(step_id)
            if not prompt_info:
                continue

            # Подготовка контекста для промпта
            format_args = {
                "h2": value, "answer": messages[-1]["content"] if messages else "", "html": html}
            formatted_prompt = prompt_info["text"].format(
                **{k: v for k, v in format_args.items() if k in prompt_info["text"]})

            # Добавляем промпт в историю сообщений
            messages.append({"role": "user", "content": formatted_prompt})
            # Запрашиваем ответ у Claude
            answer = await client.ask_claude(
                max_tokens=prompt_info["max_tokens"],
                messages=messages,
            )

            if step_id == 6:
                answer = await self.get_not_included_keywords(answer)
            last_answer = answer

            messages.append({"role": "assistant", "content": answer})

        print(messages)
        return last_answer

    async def remove_hash_prefix(self, line):
        return line.lstrip('#') if line.startswith('#') else line

    async def neurowriter_logic(self) -> None:
        writer = NeuroWriter()
        parcer = ParserNeuronWriter()
        sample_text = await self.read_file()

        if not sample_text:
            return

        try:
            content, query = await writer.import_content(sample_text)
            terms = content.get("terms", {})
            titles_terms = '\n'.join(item['t']
                                     for item in terms.get("title", []))
            desc_terms = '\n'.join(item['t'] for item in terms.get("desc", []))
            h1_terms = '\n'.join(item['t'] for item in terms.get("h1", []))
            h2_terms = await parcer.analyze_terms("H2 / H3 terms", query)

            title = await self.format_and_ask(self.client, "title", titles_terms)
            desc = await self.format_and_ask(self.client, "desc", desc_terms)
            h1 = await self.format_and_ask(self.client, "h1", h1_terms)
            sample_text = await self.insert_h1_raw("data/combined.html", h1)

            await writer.import_title_and_desc(sample_text, title, desc, query)

            h2 = await self.h2_dialogue(self.client, h2_terms, sample_text)

            # print(h2)

        except Exception as e:
            print(f"Error in neurowriter_logic: {e}")
