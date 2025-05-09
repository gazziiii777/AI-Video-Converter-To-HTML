import httpx
from anthropic import AsyncAnthropic, APIError, RateLimitError, InternalServerError
# Добавьте ANTHROPIC_API_KEY в config.py
from core.config import settings
import time

# Настройка прокси (аналогично вашему текущему коду)
proxies = settings.PROXY
transport = httpx.AsyncHTTPTransport(proxy=proxies)
http_client = httpx.AsyncClient(transport=transport)

# Инициализация клиента Anthropic
anthropic_client = AsyncAnthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    # http_client=http_client
)


class ClaudeClient:
    async def ask_claude(self, max_tokens, messages, file_name=None, model="claude-3-7-sonnet-20250219"):
        """Запрашивает ответ у Claude с историей диалога с автоматическими повторами при ошибках"""
        max_retries = 10
        claude_messages = self._convert_to_claude_format(messages)
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                response = await anthropic_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=claude_messages,
                )

                answer = response.content[0].text
                # print(answer)

                if file_name is not None:
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write(answer)

                return answer

            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = 70
                    print(
                        f"Attempt {attempt}/{max_retries} failed. Error: {str(e)}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                continue

            except Exception as e:
                print(f"Unexpected error calling Claude API: {str(e)}")
                raise

        print(
            f"All {max_retries} attempts failed. Last error: {str(last_exception)}")
        raise last_exception if last_exception else Exception(
            "Unknown error after retries")

    async def ask_claude_with_stream(self, max_tokens: int, messages: list[dict]) -> str:
        response = await anthropic_client.messages.create(
            model="claude-3-opus-20240229",  # замени на нужную тебе модель
            messages=messages,
            max_tokens=max_tokens,
            stream=True
        )

        result = ""
        async for chunk in response:
            if chunk.type == "content_block_delta":
                result += chunk.delta.text
        return result

    def _convert_to_claude_format(self, messages):
        """Конвертирует сообщения из формата OpenAI в формат Claude"""
        claude_messages = []

        for msg in messages:
            # Claude не использует system-роли, преобразуем их в user
            role = "user" if msg["role"] == "system" else msg["role"]
            claude_messages.append({"role": role, "content": msg["content"]})

        return claude_messages
