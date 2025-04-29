import requests
from core.config import settings
from config import SERPAPI_BASE_URL, NUMBER_OF_LINKS_to_ANALYZE


async def get_google_links(query):
    params = {
        "q": query,
        "api_key": settings.SERPAPI_API_KEY,
        "num": NUMBER_OF_LINKS_to_ANALYZE,
        "location": "Moscow, Russia"  # <-- вот здесь указываешь нужный город/страну
    }
    response = requests.get(SERPAPI_BASE_URL, params=params)
    data = response.json()

    links = []
    for result in data.get("organic_results", [])[:NUMBER_OF_LINKS_to_ANALYZE]:
        links.append(result.get("link"))

    return links
