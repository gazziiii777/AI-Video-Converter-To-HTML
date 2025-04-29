import requests

def get_google_links(query):
    params = {
        "q": query,
        "api_key": "625f9e3bb726af130350e2198a35644e820472f345e5cd423bb11ef9cb2ae2a0",
        "num": 5,
        "location": "Moscow, Russia"  # <-- вот здесь указываешь нужный город/страну
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()
    
    links = []
    for result in data.get("organic_results", [])[:5]:
        links.append(result.get("link"))
    
    return links

print(get_google_links("как сделать парсер на питоне"))
