# import os
# import json
import re
from typing import List, Dict, Any, Optional
# import aiofiles
from app.client.neuronwriter import Neuronwriter
# from bs4 import BeautifulSoup
from icecream import ic
import config.config as config
from config.logging_config import setup_logger
from app.service.site_services.neuronwriter.parser import ParserNeuronwriter
# from app.service.export.markdown_to_html import MarkdownToHTMLConverter
# from config.config import PATH_TO_RESULTS_HTML, OUTPUT_HTML_NAME
from app.service.site_services.prompt_manager import PromptManager
from app.service.site_services.html_processor import HTMLProcessor
from app.service.site_services.neuronwriter.table_parser import TableParser
from app.service.site_services.neuronwriter.html_modifier import HTMLModifier


logger = setup_logger('Neuronwriter')
prompt_logger = setup_logger('Neuronwriter-Prompt')
answer_logger = setup_logger('Neuronwriter-Answer')


class NeuronwriterLogic:
    def __init__(self, client):
        self.prompt_manager = PromptManager()
        self.client = client
        self.html_processor = HTMLProcessor()
        self.table_parser = TableParser()
        self.html_modifier = HTMLModifier()

    async def format_and_ask(
        self,
        label: str,
        value: str,
        html: Optional[str] = None,
        product_name: Optional[str] = None
    ) -> Optional[str]:
        """Форматирует промпт и отправляет запрос к Claude API"""
        prompt_info = await self.prompt_manager.get_prompt_by_name(label)
        if not prompt_info:
            return None

        format_vars = {label: value}
        if html:
            format_vars["html"] = html
        if product_name:
            format_vars["PRODUCT_NAME"] = product_name

        formatted_prompt = prompt_info.get('text').format(**format_vars)
        messages = [
            {"role": "user", "content": f"Context: {formatted_prompt}"}]

        try:
            answer = await self.client.ask_claude(max_tokens=2000, messages=messages)
            answer = self.html_processor.extract_answer(answer).lstrip()
            answer = re.sub(rf"^{label}:\s*", "", answer, flags=re.IGNORECASE)
            answer = await self._remove_hash_prefix(answer)

            self._log_step_prompt_answer(prompt_info, formatted_prompt, answer)
            return answer
        except Exception as e:
            logger.error(f"Ошибка в фунции format_and_ask: {e}")
            logger.debug(
                f"Аргументы переданный в фунцию format_and_ask, первый аргумент label: {label}\n Второй аргумент value: {value}\n Третий аргумент html: {html}\n Четвертый аргумент product_name {product_name}")
            raise

    async def h2_dialogue(self, value: str, html: str, product_name: str) -> Optional[Any]:
        """Выполняет диалог на основе prompt.json, обрабатывая шаги 4-8"""
        try:
            messages = []
            last_answer = None

            # Обработка основных шагов диалога (4-7)
            last_answer = await self._process_main_steps(value, html, messages, [4, 5, 6, 7], product_name)

            # Обработка шага 8 (если есть данные из шага 7)
            if last_answer:
                html = await self.html_processor.read_file("data/combined.html")
                await self._process_step_8(html, last_answer, product_name)

            if config.H2_INCLUDED:
                html = await self.html_processor.read_file("data/combined.html")
                await self._process_main_steps(value, html, messages, [9], product_name)

            return last_answer
        except Exception as e:
            logger.error(f"Ошибка в фунции h2_dialogue: {e}")
            logger.debug(
                f"Аргументы переданный в фунцию h2_dialogue, первый аргумент value: {value}\n Второй аргумент html: {html}")
            raise

    async def basic_and_extended_dialogue(self, value: str, html: str, product_name:str) -> Optional[Any]:
        """Выполняет диалог на основе prompt.json, обрабатывая шаги 4-8"""
        try:
            messages = []
            last_answer = None
            html = await self.html_processor.read_file("data/combined.html")
            # Обработка основных шагов диалога (4-7)
            last_answer = await self._process_main_steps(value, html, messages, [10, 11, 12, 13, 14], product_name)

            # # Обработка шага 8 (если есть данные из шага 7)
            # if last_answer:
            #     await self._process_step_8(html, last_answer)

            # if config.H2_INCLUDED:
            #     await self._process_main_steps(value, html, messages, [9])

            # return last_answer
        except Exception as e:
            logger.error(f"Ошибка в фунции basic_and_extended_dialogue: {e}")
            logger.debug(
                f"Аргументы переданный в фунцию basic_and_extended_dialogue, первый аргумент value: {value}\n Второй аргумент html: {html}")
            raise

    async def _process_main_steps(self, value: str, html: str, messages: list, steps: list, product_name: str) -> Optional[Any]:
        """Обрабатывает основные шаги диалога"""
        try:
            last_answer = None
            messages = []
            for step_id in steps:
                prompt_info = await self.prompt_manager.get_prompt_by_id(step_id)
                if not prompt_info:
                    continue

                if step_id == 9:
                    formatted_prompt = self._format_prompt(
                        prompt_info, value, html, messages, KEYWORDS=config.H2_INCLUDED, product_name = product_name)
                elif step_id == 10:
                    formatted_prompt = self._format_prompt(
                        prompt_info=prompt_info, text=value, html=html, messages=messages, product_name = product_name)
                elif step_id == 14:
                    messages = []
                    formatted_prompt = self._format_prompt(
                        prompt_info=prompt_info, text=value, html=html, messages=messages, text_included=config.BASIC_INCLUDED, product_name = product_name)
                else:
                    formatted_prompt = self._format_prompt(
                        prompt_info, value, html, messages, product_name = product_name)

                messages.append({"role": "user", "content": formatted_prompt})

                logger.info(
                    f"Отправляем запрос в Claude для step_id: {step_id}")

                answer = await self._get_claude_response(step_id, prompt_info, messages)

                self._log_step_prompt_answer(
                    prompt_info, formatted_prompt, answer)

                logger.info(f"Получен ответ от Claude для step_id: {step_id}")

                if step_id == 4 and answer is None:
                    return None

                answer, _ = await self._process_special_steps(step_id, answer)
                if step_id in [9, 13, 14] and answer:
                    html = await self.html_modifier.replace_in_file(html, answer)

                if answer is None and step_id == 6:
                    return None

                logger.info(f"Обработан ответ для step_id: {step_id}")

                messages.append({"role": "assistant", "content": answer})

            return answer

        except Exception as e:
            logger.error(f"Ошибка в фунции _process_main_steps: {e}")
            logger.debug(
                f"Аргументы переданный в фунцию _process_main_steps, первый аргумент value: {value}\n Второй аргумент html: {html}\n Третий аргумент messages: {messages}\n Четвертый аргумент steps {steps}")
            raise

    async def _process_step_8(self, html: str, last_answer: List[Dict], product_name: str) -> None:
        """Обрабатывает финальный шаг диалога (8)"""
        try:
            prompt_info = await self.prompt_manager.get_prompt_by_id(8)
            if not prompt_info:
                return

            # answer_logger.info(last_answer)

            for index, product in enumerate(last_answer):
                formatted_prompt = self._format_prompt(
                    prompt_info, "", html, [], h3=product.get('Prompt', ''), product_name = product_name)
                logger.info(f"Отправляем запрос в Claude для step_id: 8")

                messages = [{"role": "user", "content": formatted_prompt}]
                answer = await self.client.ask_claude_web(max_tokens=7000, messages=messages)

                # answer = self.html_processor.extract_answer(answer)

                # messages.append({"role": "assistant", "content": answer})
                # answer = await self.client.ask_claude(max_tokens=7000, messages=messages)

                answer = self.html_processor.extract_answer(
                    answer).replace('#', '')
                config.H3_DATA[index]['P'] = answer
                self._log_step_prompt_answer(
                    prompt_info, formatted_prompt, answer)

                logger.info(f"Обработан ответ для step_id: 8")

            await self.html_modifier.process_html_with_h3(html)
            
        except Exception as e:
            logger.error(f"Ошибка в фунции _process_step_8: {e}")
            logger.debug(
                f"Аргументы переданный в фунцию _process_step_8, первый аргумент html: {html}\n Второй аргумент last_answer: {last_answer}")
            raise

    def _format_prompt(self, prompt_info: dict = None,
                       value: str = None,
                       html: str = None,
                       messages: list = None,
                       h3: str = "",
                       KEYWORDS: str = "",
                       text: str = "",
                       text_included: str = "",
                       product_name: str="") -> str:
        """Форматирует промпт с подстановкой переменных"""
        try:
            format_args = {
                "h2": value,
                "answer": messages[-1]["content"] if messages else "",
                "html": html,
                "h3": h3,
                "PRODUCT_NAME": product_name,
                "KEYWORDS": KEYWORDS,
                "text": text,
                "text_included": text_included
            }
            return prompt_info["text"].format(
                **{k: v for k, v in format_args.items() if k in prompt_info["text"]}
            )
        except Exception as e:
            logger.error(f"Ошибка в фунции _format_prompt: {e}")
            raise


    async def _get_claude_response(self, step_id: int, prompt_info: dict, messages: list) -> str:
        """Получает ответ от Claude API в зависимости от шага"""
        try:
            if step_id in [4, 5, 10, 11, 12, 14]:
                answer = await self.client.ask_claude(
                    max_tokens=prompt_info["max_tokens"],
                    messages=messages,
                )
            else:
                answer = await self.client.ask_claude_web(
                    max_tokens=prompt_info["max_tokens"],
                    messages=messages,
                )
            # if step_id == 14:
            #     return answer

            return self.html_processor.extract_answer(answer)
        except Exception as e:
            logger.error(f"Ошибка в фунции _get_claude_response: {e}")
            logger.debug(
                f"Аргументы переданный в фунцию _get_claude_response, первый аргумент step_id: {step_id}\n Второй аргумент prompt_info: {prompt_info}\n Третий аргумент messages: {messages}")
            raise

    def _log_step_prompt_answer(self, prompt_info: dict, prompt: str, answer: str) -> None:
        """Логирует запрос и ответ"""
        prompt_logger.info(f"{prompt_info.get('_comment')} PROMPT: {prompt}")
        answer_logger.info(f"{prompt_info.get('_comment')} ANSWER: {answer}")

    async def _process_special_steps(self, step_id: int, answer: str) -> tuple:
        """Обрабатывает специальные шаги, требующие дополнительной обработки"""
        if step_id in [6, 12]:
            return await self.table_parser.parse_keywords_table(answer, step_id)
        elif step_id == 7:
            return await self.table_parser.parse_h3_table(answer)
        elif step_id in [9, 13, 14]:
            return await self.table_parser.parse_replacement_table(answer)
        return answer, None

    @staticmethod
    async def _remove_hash_prefix(line: str) -> str:
        """Удаляет символ # из начала строки"""
        return line.lstrip('#') if line.startswith('#') else line

    async def neuronwriter_logic(self, product_name) -> None:
        """Основная логика работы с Neuronwriter"""
        logger.info(f"Начало работы функции neuronwriter_logic")

        writer = Neuronwriter(product_name)
        parser = ParserNeuronwriter()
        sample_text = await self.html_processor.read_file("data/combined.html")

        if not sample_text:
            return

        try:
            content, query = await writer.import_content(sample_text)

            terms = content.get("terms", {})

            # Получаем термины для разных частей контента
            titles_terms = '\n'.join(item['t']
                                     for item in terms.get("title", []))
            desc_terms = '\n'.join(item['t'] for item in terms.get("desc", []))
            h1_terms = '\n'.join(item['t'] for item in terms.get("h1", []))
            h2_terms = await parser.analyze_terms("H2 / H3 terms", query)
            # basic = '\n'.join(item['t']
            #                   for item in terms.get("content_basic", []))
            # basic += '\n'.join(item['t']
            #                    for item in terms.get("content_extended", []))
            basic = await parser.analyze_terms_article("basic:", query)

            # Генерируем контент с помощью Claude
            title = await self.format_and_ask("title", titles_terms, sample_text, product_name)

            desc = await self.format_and_ask("desc", desc_terms, sample_text, product_name)
            h1 = await self.format_and_ask("h1", h1_terms, sample_text, product_name)

            # # Обновляем HTML с новым H1
            await self.html_processor.insert_h1("data/combined.html", h1)

            # Обрабатываем H2 диалог
            await self.h2_dialogue(h2_terms, sample_text, product_name)

            sample_text = await self.html_processor.read_file("data/combined.html")

            await self.basic_and_extended_dialogue(basic, sample_text, product_name)
            # Импортируем финальные title и description
            sample_text = await self.html_processor.read_file("data/combined.html")
            await writer.import_title_and_desc(sample_text, title, desc, query)
            logger.info(f"Функция neuronwriter_logic завершина без ошибок")

        except Exception as e:
            logger.error(f"Ошибка в фунции neuronwriter_logic: {e}")
            raise
