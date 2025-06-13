import config.config as config

from bs4 import BeautifulSoup
from app.service.site_services.html_processor import HTMLProcessor
from app.service.export.markdown_to_html import MarkdownToHTMLConverter
from typing import List, Dict
from config.logging_config import setup_logger

logger = setup_logger("HTML_modifier")


class HTMLModifier:

    @staticmethod
    async def replace_in_file(html: str, replacements: List[Dict]) -> str:
        """Заменяет H2 заголовки в HTML"""
        for item in replacements:
            normalized_html = ' '.join(html.split())
            normalized_old = ' '.join(item.get("old", "").split())

            if normalized_old in normalized_html:
                normalized_html = normalized_html.replace(
                    item.get("old"), item.get("new"))
                logger.info(
                    f"Заменен '{item.get('old')}' -> '{item.get('new')}'")
            else:
                logger.error(f"'{item.get('old')}' не найден в файле")

        HTMLProcessor.save_html(BeautifulSoup(normalized_html, 'html.parser'))
        return normalized_html

    @staticmethod
    async def process_html_with_h3(html: str) -> None:
        """Добавляет H3 и контент в HTML на основе H3_DATA"""
        soup = BeautifulSoup(html, 'html.parser')
        converter = MarkdownToHTMLConverter()

        for item in config.H3_DATA:
            h2_value = item.get('H2_Before')
            if not h2_value:
                continue

            h3_value = item.get('H3')
            p_value = converter.convert_md_to_html(
                item.get('P')) if item.get('P') else None

            for h2_tag in soup.find_all('h2', string=h2_value):
                new_elements = []

                if h3_value:
                    h3_tag = soup.new_tag('h3')
                    h3_tag.string = h3_value
                    new_elements.append(h3_tag)

                if p_value:
                    p_html = BeautifulSoup(p_value, 'html.parser')
                    new_elements.append(p_html)

                for element in new_elements:
                    h2_tag.insert_before(element)

        HTMLProcessor.save_html(soup)
