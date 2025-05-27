import os
import json
from typing import List, Dict
from app.client.neuronwriter import Neuronwriter
from typing import Any
import re
from typing import Optional
import aiofiles
from app.service.neuronwriter.parser import ParserNeuronwriter
from icecream import ic
from config.logging_config import setup_logger
import config

logger = setup_logger('logic')
prompt_logger = setup_logger('Neuronwriter-Prompt')
answer_logger = setup_logger('Neuronwriter-Answer')


class NeuronwriterLogic:
    def __init__(self, client):
        self.json_file_path = "neuronwriter_prompts.json"
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
        formatted_prompt = prompt_info.get('text').format(**format_vars)
        messages = [
            {
                "role": "user",
                "content": f"Context: {formatted_prompt}"
            }
        ]

        try:
            answer = await client.ask_claude(max_tokens=2000, messages=messages)
            answer = answer.lstrip()
            cleaned_answer = re.sub(
                rf"^{label}:\s*", "", answer, flags=re.IGNORECASE)
            cleaned_answer = await self.remove_hash_prefix(cleaned_answer)
            self._log_step_prompt_answer(prompt_info, formatted_prompt, answer)
            return cleaned_answer
        except Exception as e:
            print(f"Error querying Claude for {label}: {e}")

    async def get_not_included_keywords(self, text):
        lines = text.split('\n')
        not_included = []
        h2_phrases = []

        for line in lines:
            if '|' in line:  # Если это строка таблицы
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3 and parts[1].strip() == 'Not Included':
                    phrase = parts[0].strip()
                    not_included.append(phrase)
                if len(parts) >= 3 and parts[1].strip() == 'Included':
                    phrase = parts[0].strip()
                    h2 = parts[2].strip()
                    not_included.append("phrase")

                    h2_phrases.append(f"{phrase} h2: {h2}")

        return ", ".join(not_included), h2_phrases

    async def parse_table_string(self, table_string):
        lines = table_string.split('\n')

        # Удаляем пустые строки и строки с разделителями
        data_lines = [line.strip() for line in lines
                      if line.strip() and not line.startswith('---')]

        result = []

        # Пропускаем строку с заголовками (первая строка после очистки)
        for line in data_lines[1:]:
            # Разделяем строку по символу |, убираем лишние пробелы и фильтруем пустые значения
            columns = [col.strip() for col in line.split('|') if col.strip()]

            # Создаем словарь для текущей строки
            row_dict = {
                'H3': columns[0] if len(columns) > 0 else '',
                'H2_Before': columns[1] if len(columns) > 1 else '',
                'H2_After': columns[2] if len(columns) > 2 else '',
                'Prompt': columns[3] if len(columns) > 3 else ''
            }

            result.append(row_dict)

        return result, None

    async def h2_dialogue(self, client: Any, value: str, html: str) -> Optional[Any]:
        """Выполняет диалог на основе prompt.json, обрабатывая шаги 4-8.

        Args:
            client: Клиент для взаимодействия с Claude API
            value: Заголовок h2 для подстановки в промпты
            html: HTML-контент страницы для анализа
        Returns:
            Результат обработки последнего шага или None в случае ошибки
        """
        messages = []
        last_answer = None

        # Обработка основных шагов диалога (4-7)
        last_answer = await self._process_main_steps(client, value, html, messages, [4, 5, 6, 7])

        # Обработка шага 8 (если есть данные из шага 7)
        if last_answer:
            await self._process_final_step(client, html, last_answer)

        return last_answer

    async def _process_main_steps(self, client: Any, value: str, html: str, messages: list, steps: list) -> Optional[Any]:
        """Обрабатывает основные шаги диалога (4-7)."""
        last_answer = None

        for step_id in steps:
            prompt_info = await self.get_prompt_by_id(step_id)
            if not prompt_info:
                continue

            formatted_prompt = self._format_prompt(
                prompt_info, value, html, messages)
            messages.append({"role": "user", "content": formatted_prompt})

            answer = await self._get_claude_response(client, step_id, prompt_info, messages)
            self._log_step_prompt_answer(prompt_info, formatted_prompt, answer)
            answer, config.H2 = await self._process_special_steps(step_id, answer)
            if answer == "" and step_id == 6:
                return None

            if step_id == 7:
                print(answer)
                last_answer = answer  # Сохраняем для использования в шаге 8

            # if config.H2 is not None and step_id == 8:
            #     pass

            messages.append({"role": "assistant", "content": answer})
        return last_answer

    async def _process_final_step(self, client: Any, html: str, last_answer: Any) -> None:
        """Обрабатывает финальный шаг диалога (8)."""
        prompt_info = await self.get_prompt_by_id(8)
        if not prompt_info:
            return

        for product in last_answer:
            formatted_prompt = self._format_prompt(
                prompt_info, "", html, [], h3=product.get('Prompt', ''))
            messages = [{"role": "user", "content": formatted_prompt}]
            answer = await client.ask_claude_web(max_tokens=2000, messages=messages)
            messages.append({"role": "assistant", "content": answer})
            messages.append({"role": "user", "content": formatted_prompt})
            answer = await client.ask_claude(max_tokens=2000, messages=messages)
            self._log_step_prompt_answer(prompt_info, formatted_prompt, answer)

    def _format_prompt(self, prompt_info: dict, value: str, html: str, messages: list, h3: str = "") -> str:
        """Форматирует промпт с подстановкой переменных."""
        format_args = {
            "h2": value,
            "answer": messages[-1]["content"] if messages else "",
            "html": html,
            "h3": h3
        }
        return prompt_info["text"].format(
            **{k: v for k, v in format_args.items() if k in prompt_info["text"]}
        )

    async def _get_claude_response(self, client: Any, step_id: int, prompt_info: dict, messages: list) -> str:
        """Получает ответ от Claude API в зависимости от шага."""
        if step_id in [4, 5]:
            return await client.ask_claude(
                max_tokens=prompt_info["max_tokens"],
                messages=messages,
            )
        return await client.ask_claude_web(
            max_tokens=2000,
            messages=messages,
        )

    def _log_step_prompt_answer(self, prompt_info: dict, prompt: str, answer: str) -> None:
        """Логирует запрос и ответ."""
        prompt_logger.info(f"{prompt_info.get('_comment')} PROMPT: {prompt}")
        answer_logger.info(f"{prompt_info.get('_comment')} ANSWER: {answer}")

    async def _process_special_steps(self, step_id: int, answer: str) -> Optional[Any]:
        """Обрабатывает специальные шаги, требующие дополнительной обработки."""
        if step_id == 6:
            return await self.get_not_included_keywords(answer)
        if step_id == 7:
            return await self.parse_table_string(answer)
        return answer, None

    async def remove_hash_prefix(self, line):
        return line.lstrip('#') if line.startswith('#') else line

    async def neuronwriter_logic(self) -> None:
        writer = Neuronwriter()
        parcer = ParserNeuronwriter()
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

            title = await self.format_and_ask(self.client, "title", titles_terms, "html", sample_text)
            desc = await self.format_and_ask(self.client, "desc", desc_terms, "html", sample_text)
            h1 = await self.format_and_ask(self.client, "h1", h1_terms, "html", sample_text)
            sample_text = await self.insert_h1_raw("data/combined.html", h1)

            await writer.import_title_and_desc(sample_text, title, desc, query)

            h2 = await self.h2_dialogue(self.client, h2_terms, sample_text)
            if h2 is not None:
                pass

            # print(h2)
        except Exception as e:
            print(f"Error in neurowriter_logic: {e}")
