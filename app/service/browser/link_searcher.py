import requests
from core.config import settings
from config import SERPAPI_BASE_URL


async def get_google_links(query):
    params = {
        "q": query,
        "api_key": settings.SERPAPI_API_KEY,
        "num": 10,  # Запрашиваем 5 результатов
        "location": "New York, United States"
    }

    try:
        response = requests.get(SERPAPI_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Ошибка при получении результатов: {str(e)}")
        return []

    links = []
    organic_results = data.get("organic_results", [])

    print(f"\nТоп результатов для запроса '{query}':")
    for i, result in enumerate(organic_results[:5], 1):
        title = result.get("title", "Без названия")
        link = result.get("link", "")

        if link:  # Добавляем только если есть URL
            links.append(link)
            print(f"{i}. {title} | {link}")
        else:
            print(f"{i}. {title} | [URL отсутствует]")

    if len(links) < 5:
        print(f"\nПримечание: найдено только {len(links)} из 5 результатов")

    return links
