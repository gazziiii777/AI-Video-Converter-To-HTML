import json
import requests
import time
from config import NEUROWRITER_BASE_URL
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

class NeuroWriter:
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
            "keyword": "keyword",
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
                print(response_json)
                return response_json["query"]

    async def import_content(self):
        query = await self._create_query()
        payload = json.dumps({
            "query": query,
            "html": '''<h1>Best Trail Running Shoes in 2024: A Complete Guide</h1>
                <p>As a trail runner, choosing the right pair of trail running shoes is crucial...</p>''',
            "title": "Best Trail Running Shoes in 2024: A Complete Guide",
            "description": "Discover the top trail running shoes of 2024, including models from Altra, Hoka, Nike, and more.",
        })

        for attempt in range(5):  # до 5 попыток
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    "POST",
                    self.base_url + "/import-content",
                    headers=self.headers,
                    data=payload
                ) as response:
                    response_json = await response.json()
                    print(f"Attempt {attempt + 1}: {response_json}")

                    if response_json is not None:
                        return response_json

            print("Response was None, retrying after delay...")
            await asyncio.sleep(100)

        print("Failed after 5 attempts.")
        return None
