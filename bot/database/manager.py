import sqlite3


class DatabaseManager:
    def init(self, db_name: str):
        self.db_name = db_name

    def _execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def init_db(self):
        pass

    def check_schema_version(self):
        cursor = self._execute("PRAGMA user_version")
        return cursor.fetchone()[0]