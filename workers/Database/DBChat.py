from workers.Database.Database import Database


class DBChat(Database):
    tableName = 'chat_queue'

    schema = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
        "user_id": "TEXT NOT NULL",
        "chat_id": "TEXT",
        "gender": "TEXT DEFAULT 'none'",
        "min_age": "INTEGER NOT NULL DEFAULT 0",
        "max_age": "INTEGER NOT NULL DEFAULT 100",
        "distance": "INTEGER NOT NULL DEFAULT 0",
        "media_enabled": "INTEGER NOT NULL DEFAULT 1",
        "reopen": "INTEGER NOT NULL DEFAULT 1",
        "status": "INTEGER NOT NULL DEFAULT 0"
    }

    @classmethod
    def update_value(cls, where, key, new_value):
        if not isinstance(where, dict):
            where = {'user_id': where}

        return super().update_value(where, key, new_value)

    @staticmethod
    def check_tables():
        columns = Database.schema_to_columns(DBChat.schema)
        Database.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {DBChat.tableName} ({columns}, UNIQUE(user_id, chat_id) ON CONFLICT REPLACE)"
        )
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_id ON chat_queue(id)")
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat_queue(user_id, chat_id)")
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_speeder ON chat_queue(status, gender, user_id)")
