import json
import requests
import time

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


API_ENDPOINT = 'https://app.neuronwriter.com/neuron-api/0.5/writer'

headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

payload = json.dumps({
    "query": "f4261578dbe5be9f",
    "html": '''<h1>Best Trail Running Shoes in 2024: A Complete Guide</h1>
<p>As a trail runner, choosing the right pair of trail running shoes is crucial for a successful and enjoyable running experience. With the wide range of trail running shoes available in 2024, it can be overwhelming to find the best shoe that suits your running style and preferences. In this guide, we will explore what makes a great trail running shoe, discuss the top trail running shoe brands, compare the best trail running shoes of 2024, delve into the technology behind trail-running shoes, and help you choose the best overall trail running shoe.</p>
<h2>What makes a great trail running shoe?</h2>
<p>When looking for the perfect trail running shoe, there are several key features to consider that can significantly impact your performance on the trails. A good trail running shoe should provide adequate support, cushioning, and protection while being durable enough to withstand the rigors of varied terrains.</p>
<h3>Key features to look for in trail running shoes</h3>
<p>Key features to look for in a trail running shoe include a durable outsole with lugs for traction, a protective rock plate to shield your feet from sharp objects, a roomy and protective toe box, and a comfortable and supportive midsole for underfoot cushioning.</p>
<h3>Importance of traction in trail running shoes</h3>
<p>The traction of a trail running shoe is essential for maintaining grip on varied terrains such as technical trails, muddy paths, and rocky surfaces. Lugs on the outsole provide the necessary traction to help you navigate challenging terrain and prevent slips and falls.</p>''',
    "title": "Best Trail Running Shoes in 2024: A Complete Guide",
    "description": "Discover the top trail running shoes of 2024, including models from Altra, Hoka, Nike, and more. Find your perfect pair with our complete guide.",
})

response = requests.request(
    "POST", API_ENDPOINT + "/import-content", headers=headers, data=payload)
response_json = response.json()
print(response_json)
