import json
import requests
import time
from config.config import NEUROWRITER_BASE_URL
import aiohttp
import asyncio

API_KEY = "n-0ab7267fbad2c7d1e45869c257b79464"
BASE_URL = "https://app.neuronwriter.com/neuron-api/0.5/writer"


# def analyze_text(text, keyword="The Prusa CORE One"):
#     # 1. Получаем список проектов
#     projects = requests.post(
#         f"{BASE_URL}/list-projects",
#         headers={"X-API-KEY": API_KEY}
#     ).json()

#     if not projects:
#         raise Exception(
#             "Нет доступных проектов. Создайте хотя бы один вручную.")

#     # 2. Берём первый попавшийся проект
#     project_id = projects[0]["project"]

#     # 3. Всегда создаём новый запрос /new-query
#     new_query = requests.post(
#         f"{BASE_URL}/new-query",
#         headers={"X-API-KEY": API_KEY},
#         json={
#             "project": project_id,
#             "keyword": keyword,
#             "language": "English",
#             "engine": "google.com"
#         }
#     ).json()

#     query_id = new_query["query"]

#     print(query_id)
#     # 4. Загружаем текст в новый query
#     # print(text)
#     a = requests.post(
#         f"{BASE_URL}/import-content",
#         headers={"X-API-KEY": API_KEY},
#         json={
#             "query": query_id,
#             "html": text,
#             "title": "Временный анализ",
#         }
#     )

#     print(a.status_code)
#     # 5. Ждём готовности анализа
#     while True:
#         analysis = requests.post(
#             f"{BASE_URL}/get-query",
#             headers={"X-API-KEY": API_KEY},
#             json={"query": query_id}
#         ).json()

#         if analysis.get("status") == "ready":
#             return analysis.get("terms")
#         time.sleep(5)


# # Пример использования
# with open("combined.html", "r", encoding="utf-8") as file:
#     text = file.read()

# result = analyze_text(text, keyword="The Prusa CORE One")
# print(f"SEO-рекомендации: {result}")
# coding=utf-8

class Neuronwriter:
    def __init__(self):
        self.base_url = NEUROWRITER_BASE_URL
        self.headers = {
            "X-API-KEY": API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get_project(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url + "/list-projects",
                headers=self.headers,
            ) as response:
                response_json = await response.json()
                print(response_json)
                return response_json[0]["project"]

    async def _create_query(self):
        payload = json.dumps({
            "project": await self._get_project(),
            "keyword": "prusa core one",
            "language": "English",
            "engine": "google.com"
        })
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url + "/new-query",
                headers=self.headers,
                data=payload
            ) as response:
                response_json = await response.json()
                return response_json["query"]

    async def import_content(self, text):
        # query = await self._create_query()
        # query = "a867d7cf1877391c"
        query = "f694bb391e88d30c"
        payload = json.dumps({
            "query": query,
            "html": text,
        })
        async with aiohttp.ClientSession() as session:
            for attempt in range(5):
                try:
                    # await asyncio.sleep(40)
                    async with session.post(
                        self.base_url + "/import-content",
                        headers=self.headers,
                        data=payload
                    ) as response:
                        if response.status != 200:
                            print(
                                f"Attempt {attempt + 1}: HTTP {response.status}")
                            continue

                        response_json = await response.json()
                        print(f"Attempt {attempt + 1}: {response_json}")

                        if response_json and response_json.get("status") == "ok":
                            break

                except Exception as e:
                    print(f"Attempt {attempt + 1} failed with error: {e}")
            # Проверяем статус запроса
            async with session.post(
                self.base_url + "/get-query",
                headers=self.headers,
                data=json.dumps({
                    "query": query,
                })
            ) as response:
                if response.status == 200:
                    response_json = await response.json()
                    if response_json.get("status") == "ready":
                        return response_json, query
        print("Failed after 5 attempts.")
        return None

    async def import_title_and_desc(self, text, title, desc, query):
        payload = json.dumps({
            "query": query,
            "html": text,
            "title": title,
            "description": desc,
        })
        async with aiohttp.ClientSession() as session:
            # Первый запрос (import-content)
            for attempt in range(5):
                try:
                    async with session.post(
                        self.base_url + "/import-content",
                        headers=self.headers,
                        data=payload
                    ) as response:
                        response_json = await response.json()
                        if response_json.get("status") == 'ok':
                            break
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed with error: {e}")

            # Второй запрос (get-query) — в той же сессии
            async with session.post(
                self.base_url + "/get-query",
                headers=self.headers,
                data=json.dumps({"query": query})
            ) as response:
                if response.status == 200:
                    response_json = await response.json()
                    if response_json.get("status") == "ready":
                        return response_json


# async def main():
#     # Инициализация клиента
#     writer = NeuroWriter()

#     # Пример текста для импорта
#     sample_text = """
#     <p>This is a test content that will be imported to NeuroWriter.</p>
#     <p>It contains HTML tags and some sample text.</p>
#     """

#     # Вызов функции импорта
#     result = await writer.import_content(sample_text)
#     print("Final result:", result)

# if __name__ == "__main__":
#     asyncio.run(main())
