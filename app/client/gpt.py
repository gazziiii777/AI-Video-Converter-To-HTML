import openai
from core.config import settings
import httpx
from typing import List, Dict, Any
import base64
import config

# proxies = settings.PROXY  # Replace with actual proxy
# transport = httpx.AsyncHTTPTransport(proxy=proxies)

# http_client = httpx.AsyncClient(transport=transport)

client = openai.AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    # http_client=http_client  # передаем кастомный HTTP-клиент
)


class GPTClient:
    def __init__(self):
        pass

    async def ask_openai(self, messages, file_name):
        """Запрашивает ответ у OpenAI с историей диалога"""

        response = await client.chat.completions.create(
            model="o1",
            messages=messages,
        )

        answer = response.choices[0].message.content
        print(answer)

        with open(file_name, "w", encoding="utf-8") as f:
            f.write(answer)

        return answer  # Возвращаем ответ, чтобы добавить в историю

    async def analyze_images_batch(self, image_paths: List[str], instruction: str) -> str:
        """Отправляет батч изображений на анализ в GPT-4 Vision"""
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                *[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{self._encode_image(path)}"}}
                  for path in image_paths]
            ]
        }]

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2000
        )
        config.TOTAL_PRICE += (response.usage.prompt_tokens * 2.5 / 1_000_000) + \
            (response.usage.completion_tokens * 10 / 1_000_000)

        return response.choices[0].message.content

    def _encode_image(self, path: str) -> str:
        """Кодирует изображение в base64"""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
