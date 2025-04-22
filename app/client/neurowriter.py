import requests
import time

API_KEY = "n-0ab7267fbad2c7d1e45869c257b79464"
BASE_URL = "https://app.neuronwriter.com/neuron-api/0.5/writer"


def analyze_text(text, keyword="The Prusa CORE One"):
    # 1. Получаем список проектов
    projects = requests.post(
        f"{BASE_URL}/list-projects",
        headers={"X-API-KEY": API_KEY}
    ).json()

    if not projects:
        raise Exception(
            "Нет доступных проектов. Создайте хотя бы один вручную.")

    # 2. Берём первый попавшийся проект
    project_id = projects[0]["project"]

    # 3. Всегда создаём новый запрос /new-query
    new_query = requests.post(
        f"{BASE_URL}/new-query",
        headers={"X-API-KEY": API_KEY},
        json={
            "project": project_id,
            "keyword": keyword,
            "language": "English",
            "engine": "google.com"
        }
    ).json()

    query_id = new_query["query"]

    # 4. Загружаем текст в новый query
    print(text)
    requests.post(
        f"{BASE_URL}/import-content",
        headers={"X-API-KEY": API_KEY},
        json={
            "query": query_id,
            "html": text,
            "title": "Временный анализ"
        }
    )

    # 5. Ждём готовности анализа
    while True:
        analysis = requests.post(
            f"{BASE_URL}/get-query",
            headers={"X-API-KEY": API_KEY},
            json={"query": query_id}
        ).json()

        if analysis.get("status") == "ready":
            return analysis.get("terms")
        time.sleep(5)


# Пример использования
with open("combined.html", "r", encoding="utf-8") as file:
    text = file.read()

result = analyze_text(text, keyword="The Prusa CORE One")
print(f"SEO-рекомендации: {result}")
