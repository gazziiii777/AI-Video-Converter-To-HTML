import asyncio
import aiohttp
import os
import requests

from typing import List, Optional, Tuple
from config.logging_config import setup_logger
from app.client.claude import ClaudeClient
from app.service.site_services.prompt_manager import PromptManager
from urllib.parse import unquote
from app.service.site_services.html_processor import HTMLProcessor

logger = setup_logger('dataforseo')
dataforseo_logger = setup_logger('DataForSeo')


class AsyncGoogleImagesScraper:
    def __init__(self, login: str = "fb@top3dshop.com", password: str = "d3d7ee4bd7fe2808"):
        """Инициализация с дефолтными значениями для удобства"""
        self.login = login
        self.password = password
        self.base_url = "https://api.dataforseo.com"
        self.max_attempts = 20
        self.base_delay = 15
        self.timeout = aiohttp.ClientTimeout(total=300)

    # def _format_prompt(self, prompt_info: dict = None,
    #                    url_list: str = None) -> str:
    #     """Форматирует промпт с подстановкой переменных"""
    #     try:
    #         format_args = {
    #             "url_list": url_list,
    #             "PRODUCT_NAME": product_name,
    #         }
    #         return prompt_info["text"].format(
    #             **{k: v for k, v in format_args.items() if k in prompt_info["text"]}
    #         )
    #     except Exception as e:
    #         dataforseo_logger.error(f"Ошибка в фунции _format_prompt: {e}")
    #         dataforseo_logger.debug(
    #             f"Аргументы переданный в фунцию _format_prompt, первый аргумент prompt_info: {prompt_info}\n Второй аргумент url_list: {url_list}")
    #         raise


    async def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Улучшенный запрос с таймаутами и логированием"""
        url = f"{self.base_url}{endpoint}"
        auth = aiohttp.BasicAuth(self.login, self.password)

        try:
            async with aiohttp.ClientSession(auth=auth, timeout=self.timeout) as session:
                async with session.request(method, url, json=data) as response:
                    response_data = await response.json()
                    dataforseo_logger.debug(
                        f"Response from {url}: {response.status} {response_data}")
                    return response_data
        except Exception as e:
            dataforseo_logger.error(f"Request failed to {url}: {str(e)}")
            return {"status_code": 500, "status_message": str(e)}

    async def create_task(self, keyword: str) -> Optional[str]:
        """Создание задачи с улучшенной обработкой ошибок"""
        post_data = {
            "keyword": keyword,
            "language_code": "en",
            "location_code": 2840,  # США
            "depth": 20,  # Увеличили для большего охвата
            "device": "desktop",  # Вернули десктоп
            "priority": 2,
            "tag": "image_scraping"
        }

        try:
            response = await self._make_request("POST", "/v3/serp/google/images/task_post", {0: post_data})

            if response.get("status_code") == 20000:
                task_id = response["tasks"][0]["id"]
                dataforseo_logger.info(
                    f"Successfully created task for '{keyword}': {task_id}")
                return task_id

            dataforseo_logger.warning(
                f"Failed to create task for '{keyword}': {response.get('status_message')}")
            return None

        except Exception as e:
            dataforseo_logger.error(
                f"Exception in create_task for '{keyword}': {str(e)}")
            return None

    async def check_task_status(self, task_id: str) -> Tuple[str, Optional[dict]]:
        """Проверка статуса с улучшенным логированием"""
        try:
            await asyncio.sleep(10)  # Уменьшили задержку
            response = await self._make_request("GET", f"/v3/serp/google/images/task_get/advanced/{task_id}")

            if response.get("status_code") == 20000:
                task = response["tasks"][0]
                status_code = task["status_code"]

                if status_code == 20000:
                    dataforseo_logger.info(
                        f"Task {task_id} completed successfully")
                    return "completed", response
                elif status_code in [20100, 20200, 20300, 40601, 40602]:
                    dataforseo_logger.debug(
                        f"Task {task_id} still processing (status {status_code})")
                    return "processing", None
                else:
                    dataforseo_logger.warning(
                        f"Unknown status code {status_code} for task {task_id}")
                    return f"unknown_{status_code}", None

            dataforseo_logger.warning(
                f"API error for task {task_id}: {response.get('status_message')}")
            return "api_error", None

        except Exception as e:
            dataforseo_logger.error(
                f"Exception in check_task_status for {task_id}: {str(e)}")
            return "connection_error", None

    async def wait_for_completion(self, task_id: str) -> Optional[dict]:
        """Ожидание с экспоненциальной задержкой"""
        for attempt in range(1, self.max_attempts + 1):
            status, result = await self.check_task_status(task_id)

            if status == "completed":
                return result
            elif status == "processing":
                wait_time = min(self.base_delay * (attempt ** 0.5), 60)
                dataforseo_logger.info(
                    f"Waiting {wait_time:.1f}s for task {task_id} (attempt {attempt}/{self.max_attempts})")
                await asyncio.sleep(wait_time)
            else:
                dataforseo_logger.error(
                    f"Critical error for task {task_id}: {status}")
                return None

        dataforseo_logger.error(
            f"Task {task_id} timed out after {self.max_attempts} attempts")
        return None

    async def scrape_images(self, keyword: str) -> List[str]:
        """Полный процесс сбора изображений с улучшенным логированием"""
        dataforseo_logger.info(f"Starting image scraping for: '{keyword}'")

        task_id = await self.create_task(keyword)
        if not task_id:
            dataforseo_logger.warning(f"No task ID received for '{keyword}'")
            return []

        dataforseo_logger.info(
            f"Created task {task_id} for '{keyword}', waiting for completion...")
        result = await self.wait_for_completion(task_id)

        if not result:
            dataforseo_logger.warning(
                f"No results for task {task_id} ('{keyword}')")
            return []

        try:
            items = result["tasks"][0]["result"][0].get("items", [])
            urls = [item.get("source_url")
                    for item in items if item.get("source_url")]
            dataforseo_logger.info(f"Found {len(urls)} images for '{keyword}'")
            return urls[:5]  # Возвращаем максимум 5 URL

        except Exception as e:
            dataforseo_logger.error(
                f"Error processing results for {task_id}: {str(e)}")
            return []

    async def process_keyword(self, keyword: str) -> List[str]:
        """Обработка одного ключевого слова"""
        return await self.scrape_images(keyword)

    def _array_of_arrays_to_string(self, arrays):
        # Сначала объединяем все подмассивы в один плоский список
        flat_list = [url for sublist in arrays for url in sublist]
        # Затем объединяем все ссылки через пробел
        # return '\n'.join(flat_list)
        return flat_list

    async def save_images_from_urls(self, urls, save_dir="data/img"):
        # Создаем папку, если её нет
        os.makedirs(save_dir, exist_ok=True)

        for url in urls:
            try:
                # Получаем последнюю часть URL (после последнего '/')
                filename = unquote(url.split('/')[-1])

                # Удаляем параметры после '?' (если есть, например, 'image.jpg?width=200')
                filename = filename.split('?')[0]

                # Проверяем, что имя файла не пустое
                if not filename:
                    filename = f"image_{urls.index(url)}.jpg"

                # Полный путь для сохранения
                save_path = os.path.join(save_dir, filename)

                # Загружаем и сохраняем изображение
                response = requests.get(url, stream=True)
                response.raise_for_status()  # Проверка ошибок

                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)

                dataforseo_logger.info(f"✅ Успешно: {filename}")
            except Exception as e:
                dataforseo_logger.error(f"❌ Ошибка ({url}): {e}")

    async def scrape_keywords(self, keywords: List[str]) -> List[List[str]]:
        """Основная функция с параллельной обработкой ключевых слов"""
        dataforseo_logger.info(
            f"Starting scraping for {len(keywords)} keywords")

        # Создаем задачи для всех ключевых слов
        tasks = [self.process_keyword(keyword) for keyword in keywords]

        # Запускаем все задачи параллельно
        results = await asyncio.gather(*tasks)

        clear_result = self._array_of_arrays_to_string(results)

        dataforseo_logger.info("Scraping completed")
        return clear_result

    @staticmethod
    async def get_product_images(product_name: str) -> List[List[str]]:
        logger.info("Начало работы фукции get_product_images")
        # client = ClaudeClient()
        scraper = AsyncGoogleImagesScraper()
        # prompt_manager = PromptManager("solo_prompts.json")
        # html_processor = HTMLProcessor()
        # prompt_info = await prompt_manager.get_prompt_by_id(0)
        """Статический метод для получения изображений по продукту"""
        keywords = [
            f"{product_name}",
            f"{product_name} Print Quality",
            f"{product_name} Samples",
            f"{product_name} Build Volume",
            f"{product_name} Printer Controls",
            f"{product_name} Connectivity Options",
            f"{product_name} Slicing Software",
            f"{product_name} Frame Design",
            f"{product_name} What is in the box",
            f"{product_name} Main Accessory"           
        ]

        # Создаем экземпляр с дефолтными учетными данными

        result = await scraper.scrape_keywords(keywords)
        # formatted_prompt = scraper._format_prompt(prompt_info, result)
        # print(formatted_prompt)
        # messages = [{"role": "user", "content": formatted_prompt}]
        # answer = await client.ask_claude(
        #     max_tokens=prompt_info["max_tokens"],
        #     messages=messages,
        # )
        # answer = html_processor.extract_answer(answer).lstrip().split()
        await scraper.save_images_from_urls(result)
        logger.info("Функция get_product_images завершина без ошибок")
