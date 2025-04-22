from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    PROXY: str = os.getenv("PROXY")
    INSTAGRAM_LOGIN: str = os.getenv("INSTAGRAM_LOGIN")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD")
    RECRAFT_API_KEY: str = os.getenv("RECRAFT_API_KEY")

    class Config:
        env_file = ".env"


settings = Settings()
