import openai
# import openai
from core.config import settings
from config import RECRAFT_BASE_URL
import httpx

proxies = settings.PROXY  # Replace with actual proxy
transport = httpx.HTTPTransport(proxy=proxies)

http_client = httpx.Client(transport=transport)

client = openai.AsyncOpenAI(base_url=settings.RECRAFT_BASE_URL,
                            api_key=settings.RECRAFT_API_KEY,
                            http_client=http_client)


class RecraftClient:
    def __init__(self):
        pass

    async def image_to_image(self):
        response = await client.post(
            path='/images/imageToImage',
            cast_to=object,
            options={'headers': {'Content-Type': 'multipart/form-data'}},
            files={
                'image': open('17.jpg', 'rb'),
            },
            body={
                'prompt': "Add a caption to the image, what you see on it, secretly, don't change anything",
                'strength': 0.01,
            },
        )
        return response['data'][0]['url']
