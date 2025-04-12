from playwright.sync_api import sync_playwright
from config import PROXY


def open_instagram_with_proxy():
    # Настройки прокси (пример из вашего запроса)

    # Разбираем прокси на составляющие
    proxy_parts = PROXY.split('://')[1].split('@')
    auth_part = proxy_parts[0].split(':')
    server_part = proxy_parts[1]

    proxy_settings = {
        'server': server_part,
        'username': auth_part[0],
        'password': auth_part[1]
    }

    with sync_playwright() as p:
        # Запускаем браузер с прокси
        browser = p.chromium.launch(
            headless=False,
            proxy={
                'server': f"http://{proxy_settings['server']}",
                'username': proxy_settings['username'],
                'password': proxy_settings['password']
            }
        )

        # Создаем контекст с настройками
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
            # Дополнительные настройки для обхода детекта
            java_script_enabled=True,
            bypass_csp=True
        )

        page = context.new_page()

        try:
            # Переходим на Instagram с таймаутом 60 сек
            print("🔄 Открываем Instagram через прокси...")
            page.goto('https://www.instagram.com/', timeout=60000)

            # Проверяем подключение
            if "instagram" in page.title().lower():
                print("✅ Instagram успешно загружен")
                print(f"Заголовок страницы: {page.title()}")
            else:
                print("❌ Не удалось загрузить Instagram")

            # Делаем скриншот
            page.screenshot(path='instagram_proxy.png')
            print("📸 Скриншот сохранен как 'instagram_proxy.png'")

            # Оставляем браузер открытым
            input("Нажмите Enter для закрытия браузера...")

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            # Делаем скриншот при ошибке
            page.screenshot(path='instagram_error.png')
            print("📸 Скриншот ошибки сохранен как 'instagram_error.png'")
        finally:
            browser.close()


if __name__ == "__main__":
    open_instagram_with_proxy()
