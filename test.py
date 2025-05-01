# import requests

# def get_google_links(query):
#     params = {
#         "q": query,
#         "api_key": "625f9e3bb726af130350e2198a35644e820472f345e5cd423bb11ef9cb2ae2a0",
#         "num": 5,
#         "location": "Moscow, Russia"  # <-- вот здесь указываешь нужный город/страну
#     }
#     response = requests.get("https://serpapi.com/search", params=params)
#     data = response.json()

#     links = []
#     for result in data.get("organic_results", [])[:5]:
#         links.append(result.get("link"))

#     return links

# print(get_google_links("как сделать парсер на питоне"))

import asyncio
from app.client.claude import ClaudeClient


async def main():
    client = ClaudeClient()
    with open("data/combined.html", "r", encoding="utf-8") as f:
        content = f.read()
    messages = [
        {"role": "user",
            "content": f"Remove all quotes from this text (you can rewrite it in other words, but without quotes!) text:  {content}"}
    ]

    file_name_answer = await client.ask_claude(20000, messages)
    print(file_name_answer)

if __name__ == "__main__":
    asyncio.run(main())
