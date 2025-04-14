from playwright.async_api import async_playwright
from core.config import settings
import os
import json


class Instagram:
    def __init__(self):
        self.proxy_settings = self._parse_proxy(settings.PROXY)
        self.login = settings.INSTAGRAM_LOGIN
        self.password = settings.INSTAGRAM_PASSWORD
        self.cookies_file = f"ig.json"

    def _parse_proxy(self, proxy_str):
        """Парсим строку прокси на составляющие"""
        proxy_parts = proxy_str.split('://')[1].split('@')
        auth_part = proxy_parts[0].split(':')
        server_part = proxy_parts[1]

        return {
            'server': server_part,
            'username': auth_part[0],
            'password': auth_part[1]
        }

    async def _load_cookies(self, context):
        """Загружает куки из файла с преобразованием формата"""
        if not os.path.exists(self.cookies_file):
            return False

        with open(self.cookies_file, 'r') as f:
            cookies = json.load(f)

        # Преобразуем куки в формат, понятный Playwright
        playwright_cookies = []
        for cookie in cookies:
            # Обрабатываем поле sameSite
            same_site = cookie.get('sameSite')
            if same_site == 'no_restriction':
                same_site = 'None'
            elif same_site not in ['Strict', 'Lax', 'None']:
                same_site = 'Lax'  # Значение по умолчанию

            # Создаем cookie в правильном формате
            playwright_cookie = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', '.instagram.com'),
                'path': cookie.get('path', '/'),
                'expires': cookie.get('expirationDate') or cookie.get('expires'),
                'httpOnly': cookie.get('httpOnly', False),
                'secure': cookie.get('secure', True),
                'sameSite': same_site
            }

            # Удаляем None-значения
            playwright_cookie = {
                k: v for k, v in playwright_cookie.items() if v is not None}
            playwright_cookies.append(playwright_cookie)

        if not playwright_cookies:
            return False

        await context.add_cookies(playwright_cookies)
        print(f"✅ Куки загружены из {self.cookies_file}")
        return True

    async def _is_logged_in(self, page):
        """Проверяет, выполнен ли вход по наличию ссылки с логином"""
        try:
            selector = f'a[href="/{self.login}/"]'
            await page.wait_for_selector(selector, timeout=5000)
            return True
        except:
            return False

    async def open_and_auth(self):
        """Открывает Instagram через прокси и выполняет авторизацию при необходимости"""
        async with async_playwright() as p:
            # Запускаем браузер с прокси
            browser = await p.chromium.launch(
                headless=False,
                proxy={
                    'server': f"http://{self.proxy_settings['server']}",
                    'username': self.proxy_settings['username'],
                    'password': self.proxy_settings['password']
                }
            )

            # Создаем контекст с настройками
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                viewport={'width': 1280, 'height': 720},
                java_script_enabled=True,
                bypass_csp=True
            )

            # Пробуем загрузить куки
            cookies_loaded = await self._load_cookies(context)

            page = await context.new_page()

            try:
                # Переходим на Instagram
                print("🔄 Открываем Instagram через прокси...")
                await page.goto('https://www.instagram.com/', timeout=60000)

                # Обновляем страницу после загрузки
                await page.reload()
                print("🔄 Страница обновлена")

                # Проверяем подключение
                title = await page.title()
                if "instagram" not in title.lower():
                    print("❌ Не удалось загрузить Instagram")
                    return

                print("✅ Instagram успешно загружен")
                print(f"Заголовок страницы: {title}")

                # Если куки были загружены, проверяем авторизацию
                if cookies_loaded and await self._is_logged_in(page):
                    print("✅ Уже авторизованы (использованы сохраненные куки)")
                # Оставляем браузер открытым
                print("🚀 Браузер остается открытым...")
                while True:
                    # Бесконечное ожидание
                    await page.wait_for_timeout(3600000)

            except Exception as e:
                print(f"❌ Ошибка: {str(e)}")
                # Оставляем браузер открытым даже при ошибке
                print("🚀 Браузер остается открытым несмотря на ошибку...")
                while True:
                    await page.wait_for_timeout(3600000)


async def main():
    instagram = Instagram()
    await instagram.open_and_auth()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
