from workers.Database.Database import Database


class DBUsers(Database):
    tableName = 'users'

    schema = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
        "user_id": "INTEGER NOT NULL",
        "chat_id": "INTEGER NOT NULL",
        "lang": "TEXT",
        "gender": "TEXT DEFAULT 'none'",
        "bio": "TEXT",
        "birthday": "TEXT",
        "location": "BLOB",
        "is_bot": "INTEGER NOT NULL DEFAULT 0",
        "reported": "INTEGER NOT NULL DEFAULT 0"
    }

    @classmethod
    def get_value(cls, where, key, default=None):
        if not isinstance(where, dict):
            where = {'user_id': where}

        return super().get_value(where, key, default)

    @classmethod
    def update_value(cls, where, key, new_value):
        if not isinstance(where, dict):
            where = {'user_id': where}

        return super().update_value(where, key, new_value)

    @classmethod
    def get_row(cls, where=None):
        if not isinstance(where, dict):
            where = {'user_id': where}

        return super().get_row(where)

    @classmethod
    def delete(cls, where=None):
        if not isinstance(where, dict):
            where = {'user_id': where}

        return super().delete(where)

    @staticmethod
    def check_tables():
        columns = Database.schema_to_columns(DBUsers.schema)
        Database.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {DBUsers.tableName} ({columns}, UNIQUE(user_id, chat_id) ON CONFLICT REPLACE)"
        )
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON users(id)")
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_user_chat ON users(user_id, chat_id)")
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_speeder ON users(gender, lang, user_id)")
