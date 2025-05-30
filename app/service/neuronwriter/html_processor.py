import aiofiles
import os
import re

from typing import Optional
from bs4 import BeautifulSoup
from config.config import PATH_TO_RESULTS_HTML, OUTPUT_HTML_NAME

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
        match = re.search(r'<answer>(.*?)</answer>', text, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def save_html(soup: BeautifulSoup) -> None:
        """Сохраняет HTML в файл"""
        with open(os.path.join(PATH_TO_RESULTS_HTML, f"{OUTPUT_HTML_NAME}.html"), 'w', encoding='utf-8') as file:
            file.write(str(soup))

    @staticmethod
    async def read_file(path: str, encoding: str = "utf-8") -> str:
        """Читает содержимое файла"""
        try:
            async with aiofiles.open(path, 'r', encoding=encoding) as file:
                return await file.read()
        except Exception as e:
            # logger.error(f"Error reading file {path}: {e}")
            return ""

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
            result_html = html[:insert_position] + h1_tag + html[insert_position:]

            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(result_html)

            return result_html
        except Exception as e:
            # logger.error(f"Error inserting H1: {e}")
            return None