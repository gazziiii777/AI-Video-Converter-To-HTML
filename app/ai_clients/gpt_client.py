import openai
from config import OPENAI_API_KEY, PROXI
import httpx

proxies = PROXI  # Replace with actual proxy
transport = httpx.AsyncHTTPTransport(proxy=proxies)

http_client = httpx.AsyncClient(transport=transport)

client = openai.AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    http_client=http_client  # передаем кастомный HTTP-клиент
)


class GPTClient:
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
