from openai import OpenAI
# import openai
from core.config import settings
import httpx

proxies = "http://8Cw1KE:ugaBoY@185.68.187.47:8000"  # Replace with actual proxy
transport = httpx.HTTPTransport(proxy=proxies)

http_client = httpx.Client(transport=transport)
# client = openai.AsyncOpenAI(
#     base_url='https://external.api.recraft.ai/v1/images/imageToImage',
#     api_key="KKPqDLvqMs1AXyU1B6Zv4cnY6UiH6LZrWILISo5PVHNjk5NGw269CllzEoyt325e",
#     http_client=http_client
# )


# async def ask():
#     response = await client.post(
#         path='data',
#         cast_to=object,
#         options={'headers': {'Content-Type': 'multipart/form-data'}},
#         files={
#             'image': open('data/img/17.png', 'rb'),
#         },
#         body={
#             'prompt': 'winter',
#             'strength': 0.2,
#         },
#     )

#     return (response['data'][0]['url'])


client = OpenAI(base_url='https://external.api.recraft.ai/v1',
                api_key=settings.RECRAFT_API_KEY,
                http_client=http_client)

response = client.post(
    path='/images/imageToImage',
    cast_to=object,
    options={'headers': {'Content-Type': 'multipart/form-data'}},
    files={
        'image': open('17.jpg', 'rb'),
    },
    body={
        'prompt': "Add a caption to the image, what you see on it, secretly, don't change anything",
        'strength': 0.2,
    },
)
print(response['data'][0]['url'])
