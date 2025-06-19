import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    TELEGRAM_TOKEN: str
    FOLDER_ID: str
    IAM_TOKEN: str
    DATABASE_NAME: str = "user_queries.db"
    CACHE_EXPIRE_HOURS: int = 24
    MAX_QUERY_LENGTH: int = 500

def load_config() -> Config:
    load_dotenv()
    return Config(
        TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN"),
        FOLDER_ID=os.getenv("FOLDER_ID"),
        IAM_TOKEN=os.getenv("IAM_TOKEN")
    )