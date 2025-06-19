from typing import List, Dict, Optional
from bot.database.manager import DatabaseManager


class BookRepository:
    def init(self):
        self.db = DatabaseManager("user_queries.db")

    def get_user_queries(self, user_id: int) -> List[str]:

        pass

    def save_query(self, user_id: int, query: str) -> None:

        pass