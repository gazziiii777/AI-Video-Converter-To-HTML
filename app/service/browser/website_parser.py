from datetime import datetime
import os
import aiohttp
import aiofiles
from urllib.parse import urlparse
import hashlib
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image
import asyncio
import re
from config.logging_config import setup_logger
from config.config import PATH_TO_IMG, PATH_TO_TXT


logger = setup_logger('website_parser')


class WebsiteParser:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None
        self.folder_path_img = PATH_TO_IMG
        self.folder_path_txt = PATH_TO_TXT

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    async def download_images(self, url: str) -> list:
        """
        Скачивает все изображения с веб-страницы

        :param url: URL страницы для парсинга
        :param output_dir: Папка для сохранения изображений
        :return: Список словарей с информацией о скачанных изображениях
        """
        Path(self.folder_path_img).mkdir(parents=True, exist_ok=True)
        self.page = await self.browser.new_page()

        try:
            import time
            await self.page.goto(url, wait_until="domcontentloaded")
            time.sleep(10)
            images = await self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('img')).map(img => ({
                    src: img.src,
                    currentSrc: img.currentSrc,
                    alt: img.alt,
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    title: img.title
                }));
            }""")

            valid_images = [img for img in images if img['src']
                            and img['src'].startswith(('http:', 'https:'))]
            downloaded_images = []

            async with aiohttp.ClientSession() as session:
                for img in valid_images:
                    try:
                        img_url = img['currentSrc'] if img['currentSrc'] else img['src']
                        parsed_url = urlparse(img_url)

                        # Получаем имя файла из URL
                        original_filename = os.path.basename(parsed_url.path)
                        if not original_filename:
                            original_filename = "image"  # Дефолтное имя, если не удалось извлечь

                        # Удаляем параметры запроса, если они есть
                        original_filename = original_filename.split('?')[0]
                        original_filename = original_filename.split('#')[0]

                        # Получаем расширение файла
                        ext = os.path.splitext(original_filename)[1]
                        if not ext or len(ext) > 5:
                            ext = '.jpg'

                        # Если имя файла без расширения, добавляем его
                        if not os.path.splitext(original_filename)[1]:
                            original_filename = f"{os.path.splitext(original_filename)[0]}{ext}"

                        # Заменяем недопустимые символы в имени файла
                        original_filename = re.sub(
                            r'[\\/*?:"<>|]', "_", original_filename)

                        # Если имя слишком длинное, укорачиваем его
                        if len(original_filename) > 100:
                            name, ext = os.path.splitext(original_filename)
                            original_filename = f"{name[:95]}{ext}"

                        # Проверяем, не существует ли уже файл с таким именем
                        counter = 1
                        base_name, ext = os.path.splitext(original_filename)
                        filepath = os.path.join(
                            self.folder_path_img, original_filename)
                        while os.path.exists(filepath):
                            original_filename = f"{base_name}_{counter}{ext}"
                            filepath = os.path.join(
                                self.folder_path_img, original_filename)
                            counter += 1

                        async with session.get(img_url) as response:
                            if response.status == 200:
                                async with aiofiles.open(filepath, 'wb') as f:
                                    await f.write(await response.read())

                                img_info = {
                                    'original_url': img_url,
                                    'local_path': filepath,
                                    'alt': img['alt'],
                                    'dimensions': f"{img['width']}x{img['height']}",
                                    'title': img['title'],
                                    'download_status': 'success'
                                }
                                downloaded_images.append(img_info)
                            else:
                                img['download_status'] = f'failed (HTTP {response.status})'
                                downloaded_images.append(img)
                    except Exception as e:
                        img['download_status'] = f'failed ({str(e)})'
                        downloaded_images.append(img)

            logger.info(downloaded_images)
            return downloaded_images
        finally:
            if self.page:
                await self.page.close()

    async def save_clean_page_content(self, url: str, query: str) -> dict:
        """
        Сохраняет очищенные HTML и текстовое содержимое страницы

        :param url: URL страницы
        :param output_dir: Директория для сохранения
        :return: {'html_file': путь, 'text_file': путь, 'url': url}
        """
        # Подготовка директории
        Path(self.folder_path_txt).mkdir(parents=True, exist_ok=True)

        # Генерация имен файлов
        domain = re.sub(r'\W+', '_', url.split('//')[-1].split('/')[0])
        base_name = f"{domain}_{query}"

        result = {
            'text_file': os.path.join(self.folder_path_txt, f"{base_name}.txt"),
            'url': url
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded")

                # Получаем и очищаем текст
                clean_text = await page.evaluate("""() => {
                        // Удаляем ненужные элементы
                        const removals = ['script', 'style', 'nav', 'footer',
                                        'iframe', 'head', 'noscript'];
                        removals.forEach(selector => {
                            document.querySelectorAll(selector).forEach(el => el.remove());
                        });

                        // Получаем текст со всей страницы
                        return document.body.textContent;
                    }""")

                # Дополнительная очистка в Python
                clean_text = "\n".join(
                    line.strip() for line in clean_text.splitlines()
                    if line.strip()
                )

                # Сохраняем очищенный текст
                with open(result['text_file'], 'w', encoding='utf-8') as f:
                    f.write(clean_text)

                return result

            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                # Удаляем частично созданные файлы при ошибке
                if result['text_file'] and os.path.exists(f):
                    os.remove(f)
                return {'error': str(e), 'url': url}

            finally:
                await browser.close()

    async def filter_images_by_size(
        self,
        min_width: int,
        min_height: int,
        verbose: bool = True
    ) -> dict:
        """
        Фильтрует изображения по минимальному размеру

        :param min_width: Минимальная ширина
        :param min_height: Минимальная высота
        :param verbose: Выводить информацию о процессе
        :return: Результаты фильтрации
        """
        results = {
            'total': 0,
            'deleted': 0,
            'remaining': 0,
            'resized': 0,
            'errors': 0
        }

        if not os.path.exists(self.folder_path_img):
            logger.error(f"Папка {self.folder_path_img} не существует")
            raise ValueError(f"Папка {self.folder_path_img} не существует")

        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')

        for filename in os.listdir(self.folder_path_img):
            file_path = os.path.join(self.folder_path_img, filename)

            if not os.path.isfile(file_path):
                continue
            if not filename.lower().endswith(valid_extensions):
                continue

            results['total'] += 1

            try:
                with Image.open(file_path) as img:
                    width, height = img.size

                    if width < min_width or height < min_height:
                        os.remove(file_path)
                        results['deleted'] += 1
                        if verbose:
                            logger.info(
                                f"Удалено: {filename} ({width}x{height})")
                    else:
                        results['remaining'] += 1

                        # Увеличиваем изображение, если ширина < 300
                        if width > 800 or height > 800:
                            new_size = (int(width / 1.5), int(height / 1.5))
                            resized_img = img.resize(new_size, Image.LANCZOS)
                            resized_img.save(file_path)
                            results['resized'] += 1
                            if verbose:
                                logger.info(
                                    f"Уменьшенно: {filename} → {new_size}")

            except Exception as e:
                results['errors'] += 1
                if verbose:
                    logger.error(f"Ошибка при обработке {filename}: {str(e)}")

        if verbose:
            logger.info("\nРезультаты фильтрации:")
            logger.info(f"Всего проверено: {results['total']}")
            logger.info(f"Удалено: {results['deleted']}")
            logger.info(f"Оставлено: {results['remaining']}")
            logger.info(f"Увеличено: {results['resized']}")
            logger.info(f"Ошибок: {results['errors']}")

        return results


async def main():
    async with WebsiteParser() as downloader:
        # Скачиваем изображения
        images = await downloader.download_images(
            "https://www.prusa3d.com/product/prusa-core-one/",
            "prusa_images"
        )
        print(f"Скачано {len(images)} изображений")

        # Фильтруем по размеру
        results = WebsiteParser.filter_images_by_size(
            "prusa_images",
            min_width=100,
            min_height=100
        )


if __name__ == "__main__":
    asyncio.run(main())
