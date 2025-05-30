import config.config as config

from bs4 import BeautifulSoup
from app.service.neuronwriter.html_processor import HTMLProcessor
from app.service.export.markdown_to_html import MarkdownToHTMLConverter
from typing import List, Dict

class HTMLModifier:
    @staticmethod
    async def replace_h2_in_file(html: str, h2_replacements: List[Dict]) -> None:
        """Заменяет H2 заголовки в HTML"""
        for item in h2_replacements:
            if item.get("old_h2") in html:
                html = html.replace(item.get("old_h2"), item.get("new_h2"))
                # logger.info(f"Заменен H2: '{item.get('old_h2')}' -> '{item.get('new_h2')}'")
            else:
                # logger.warning(f"H2 '{item.get('old_h2')}' не найден в файле")
                pass
            
        HTMLProcessor.save_html(BeautifulSoup(html, 'html.parser'))

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
