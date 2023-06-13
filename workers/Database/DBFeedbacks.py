from workers.Database.Database import Database


class DBFeedbacks(Database):
    tableName = 'feedback'

    schema = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
        "user_id": "INTEGER NOT NULL",
        "message": "TEXT",
        "attachment": "TEXT"
    }

    @staticmethod
    def check_tables():
        Database.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {DBFeedbacks.tableName} ({Database.schema_to_columns(DBFeedbacks.schema)})"
        )
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_id ON feedback(id)")
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)")
