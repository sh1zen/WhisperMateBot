from workers.Database.Database import Database


class DBSchedules(Database):
    tableName = 'schedules'

    schema = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
        "chat_id": "TEXT",
        "name": "TEXT NOT NULL UNIQUE",
        "timestamp": "INTEGER NOT NULL",
        "reminder": "TEXT",
        "handler": "TEXT"
    }

    @staticmethod
    def check_tables():
        columns = Database.schema_to_columns(DBSchedules.schema)
        Database.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {DBSchedules.tableName} ({columns}, UNIQUE(chat_id, name, timestamp, handler) ON CONFLICT REPLACE)"
        )
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_id ON schedules(id)")
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_chat_id ON schedules(chat_id)")
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_speeder ON schedules(chat_id, timestamp, name, handler)")
