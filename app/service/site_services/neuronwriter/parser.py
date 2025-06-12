import asyncio
from playwright.async_api import async_playwright
import re


class ParserNeuronwriter:
    def __init__(self):
        self.cookies = [
            {
                "name": "contai_session_id",
                "value": "86a4012b1052492796af45f1759d6ef3",
                "domain": "app.neuronwriter.com",
                "path": "/",
                "httpOnly": False,
                "secure": True,
                "sameSite": "None"
            }
        ]
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.viewport = {"width": 1280, "height": 800}
        self.url = "https://app.neuronwriter.com/analysis/view/"

    async def analyze_terms_article(self, term: str, query: str) -> list:
        """
        Анализирует H1 terms на странице NeuronWriter

        :param term: Термин для поиска (например "H1 terms")
        :return: Список найденных текстов кнопок
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=self.user_agent,
                viewport=self.viewport
            )
            await context.add_cookies(self.cookies)

            page = await context.new_page()
            await page.goto(self.url + query, wait_until="domcontentloaded")
            await page.wait_for_timeout(15000)
            await asyncio.sleep(70)

            results = await self._extract_h1_terms_data(page, term)
            results = await self._extract_text(results)
            await browser.close()
            return results

    async def analyze_terms(self, term: str, query: str) -> list:
        """
        Анализирует H1 terms на странице NeuronWriter

        :param term: Термин для поиска (например "H1 terms")
        :return: Список найденных текстов кнопок
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=self.user_agent,
                viewport=self.viewport
            )
            await context.add_cookies(self.cookies)

            page = await context.new_page()
            await self._navigate_to_analysis_page(page, query)

            results = await self._extract_h1_terms_data(page, term)

            await browser.close()
            return results

    async def _extract_text(self, text):
        # Регулярное выражение для извлечения названий перед "число / число" или "число / число-число"
        pattern = r'^(.+?)\s+\d+\s*/\s*\d+(?:-\d+)?$'
        matches = re.findall(pattern, text, re.MULTILINE)
        return "\n".join(matches)

    async def _navigate_to_analysis_page(self, page, query):
        """Выполняет навигацию по странице анализа"""
        await page.goto(self.url + query, wait_until="domcontentloaded")
        await page.click('button.first-action-button')
        await page.click("#editor-sidebar-toggle")
        await page.click("#terms-in-headers-tab")
        await page.wait_for_timeout(10000)

    async def _extract_h1_terms_data(self, page, term: str) -> list:
        """Извлекает данные H1 terms со страницы"""
        h1_card = await page.query_selector(f"h4.h4-small:has-text('{term}')")

        if not h1_card:
            print("❌ Не найден блок с H1 terms")
            return []

        card_container = await h1_card.evaluate_handle("el => el.closest('.card')")
        buttons = await card_container.query_selector_all(".btn-outline-secondary")

        results = []
        for btn in buttons:
            text = await btn.inner_text()
            results.append(text.strip())

        cleaned_results = []
        for text in results:
            cleaned_text = re.sub(r"\s*\d+%", "", text).strip()
            cleaned_results.append(cleaned_text)

        return "\n".join(cleaned_results)


# # Пример использования
# if __name__ == "__main__":
#     analyzer = ParserNeuronWriter()
#     asyncio.run(analyzer.analyze_terms("H1 terms", "0c64fd823bf9ba6c"))
