from playwright.async_api import async_playwright
import asyncio


async def get_full_page_content(url):
    async with async_playwright() as p:
        # Запускаем браузер (можно выбрать chromium, firefox или webkit)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Переходим на страницу и ждем загрузки
        # "networkidle" ждет завершения запросов
        await page.goto(url, wait_until="domcontentloaded")

        # Получаем весь HTML
        html = await page.content()

        # ИЛИ извлекаем только текст (без тегов)
        text = await page.evaluate("""() => {
            // Удаляем ненужные элементы (скрипты, стили и т.д.)
            const elements = document.querySelectorAll('script, style, nav, footer, iframe');
            elements.forEach(el => el.remove());
            
            // Возвращаем чистый текст
            return document.body.innerText;
        }""")

        await browser.close()
        return html, text  # Вернет и HTML, и чистый текст

# Пример использования
url = "https://www.prusa3d.com/product/prusa-core-one/"
html, text = asyncio.run(get_full_page_content(url))
print(text[:100000])  # Выведет первые 1000 символов текста
