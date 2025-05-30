import httpx
from anthropic import AsyncAnthropic, APIError, RateLimitError, InternalServerError
# Добавьте ANTHROPIC_API_KEY в config.py
from core.settings import settings
import time
# import json
import config.config as config
import asyncio
from config.logging_config import setup_logger


logger = setup_logger('Claude')

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
                config.TOTAL_PRICE += (response.usage.input_tokens * 3 / 1_000_000) + \
                    (response.usage.output_tokens * 15 / 1_000_000)
                return answer

            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = 70
                    logger.error(
                        f"Attempt {attempt}/{max_retries} failed. Error: {str(e)}. Retrying in {wait_time} seconds...")

                    logger.debug(claude_messages)
                    time.sleep(wait_time)
                continue

            except Exception as e:
                print(f"Unexpected error calling Claude API: {str(e)}")
                raise

        print(
            f"All {max_retries} attempts failed. Last error: {str(last_exception)}")
        raise last_exception if last_exception else Exception(
            "Unknown error after retries")

    async def ask_claude_web(self, max_tokens, messages, file_name=None, param=None):
        """Запрашивает ответ у Claude с веб-поиском"""
        max_retries = 10
        claude_messages = self._convert_to_claude_format(messages)

        for attempt in range(1, max_retries + 1):
            try:
                response = await anthropic_client.messages.create(
                    model="claude-3-7-sonnet-latest",
                    messages=claude_messages,
                    max_tokens=max_tokens,
                    tools=[{
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": 3,
                        "user_location": {
                            "type": "approximate",
                            "city": "San Francisco",
                            "region": "California",
                            "country": "US",
                            "timezone": "America/Los_Angeles"
                        }
                    }],
                    system="Отвечай кратко без описания процесса поиска"
                )

                # Извлекаем только текстовые блоки с ответом
                answer_blocks = [
                    block.text for block in response.content
                    if block.type == 'text'
                ]
                answer = '\n'.join(answer_blocks)
                # answer = response.content[0].text
                # Расчет стоимости
                input_cost = response.usage.input_tokens * 3 / 1_000_000
                output_cost = response.usage.output_tokens * 15 / 1_000_000
                config.TOTAL_PRICE += input_cost + output_cost
                return answer

            except Exception as e:
                # Обработка ошибок и повторные попытки
                if attempt < max_retries:
                    print(f"Attempt {attempt} failed: {str(e)}")
                    await asyncio.sleep(70 ** attempt)
                else:
                    raise

        return None

    async def ask_claude_web_test(self, max_tokens: int, messages: list[dict], file_name=None) -> str:
        response = await anthropic_client.messages.create(
            model="claude-3-7-sonnet-latest",
            messages=messages,
            max_tokens=max_tokens,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 1
            }]
        )
        return response.content[4].text

    def _convert_to_claude_format(self, messages):
        """Конвертирует сообщения из формата OpenAI в формат Claude"""
        claude_messages = []

        for msg in messages:
            # Claude не использует system-роли, преобразуем их в user
            role = "user" if msg["role"] == "system" else msg["role"]
            claude_messages.append({"role": role, "content": msg["content"]})

        return claude_messages
