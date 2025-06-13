import aiofiles
import os
import re

from typing import Optional
from bs4 import BeautifulSoup
from config.config import PATH_TO_RESULTS_HTML, OUTPUT_HTML_NAME
from config.logging_config import setup_logger

logger = setup_logger('html_processor')


class HTMLProcessor:
    @staticmethod
    def extract_answer(text: str) -> str:
        """
        Извлекает текст внутри тегов <answer> и </answer> из переданного текста.

        Args:
            text: Исходный текст, содержащий ответ в тегах <answer>

        Returns:
            Текст внутри тегов answer или пустая строка, если теги не найдены
        """
        try:

            match = re.search(r'<answer>(.*?)</answer>', text, re.DOTALL)
            return match.group(1).strip() if match else ""
        except Exception as e:
            logger.error(f"Ошибка в фунции extract_answer: {e}")
            logger.debug(f"Аргумент переданный в фунцию extract_answer: {text}")
            raise

    @staticmethod
    def save_html(soup: BeautifulSoup) -> None:
        """Сохраняет HTML в файл"""
        try:
            with open(os.path.join(PATH_TO_RESULTS_HTML, f"{OUTPUT_HTML_NAME}.html"), 'w', encoding='utf-8') as file:
                file.write(str(soup))
        except Exception as e:
            logger.error(f"Ошибка в фунции save_html: {e}")
            logger.debug(f"Аргумент переданный в фунцию save_html: {soup}")
            raise

    @staticmethod
    async def read_file(path: str, encoding: str = "utf-8") -> str:
        """Читает содержимое файла"""
        try:
            async with aiofiles.open(path, 'r', encoding=encoding) as file:
                return await file.read()
        except Exception as e:
            logger.error(f"Ошибка в фунции read_file: {e}")
            logger.debug(
                f"Аргументы переданный в фунцию read_file, первый аргумент path: {path}\n Второй аргумент encoding: {encoding}")
            # return ""
            raise

    @staticmethod
    async def insert_h1(filepath: str, h1_text: str) -> Optional[str]:
        """Вставляет H1 тег в HTML файл"""
        try:
            html = await HTMLProcessor.read_file(filepath)

            body_index = html.lower().find("<body")
            if body_index == -1:
                # logger.warning("Тег <body> не найден.")
                return None

            body_end = html.find(">", body_index)
            if body_end == -1:
                # logger.warning("Некорректный тег <body>.")
                return None

            insert_position = body_end + 1
            h1_tag = f"<h1>{h1_text}</h1>\n"
            result_html = html[:insert_position] + \
                h1_tag + html[insert_position:]

            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(result_html)

            return result_html
        except Exception as e:
            logger.error(f"Ошибка в фунции insert_h1: {e}")
            logger.debug(
                f"Аргументы переданный в фунцию insert_h1, первый аргумент filepath: {filepath}\n Второй аргумент h1_text: {h1_text}")
            # return None
            raise