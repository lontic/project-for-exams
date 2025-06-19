import requests
from bot.utils.config import Config


class AIService:
    def __init__(self, config: Config):
        self.config = config

    async def generate_books_recommendation(self, topic: str) -> str:

        pass