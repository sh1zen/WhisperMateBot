from sqlite3 import Cursor

from utils.QueueCache import QueueCache
from utils.utility import maybe_unserialize, maybe_serialize
from workers.Database.Database import Database


class DBMeta(Database):
    tableName = 'metadata'

    schema = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL',
        'object_id': 'INTEGER NOT NULL',
        'meta_key': 'TEXT NOT NULL',
        'meta_value': 'TEXT NOT NULL'
    }

    @classmethod
    def get_metadata_raw(cls, where) -> None | Cursor:
        fields, values = cls.parse_where(where)
        return Database.cursor.execute(
            f"SELECT * FROM {cls.tableName} WHERE {' AND '.join(fields)}",
            values
        )

    @classmethod
    def get_meta(cls, object_id, meta_key, default=None):

        cache_key = QueueCache.key(object_id, meta_key, cls.tableName)

        cached = cls.queueCache.has(cache_key)

        if cached is not None:
            return cached

        fetched = cls.get_metadata_raw(
            {'object_id': object_id, 'meta_key': meta_key}
        ).fetchone()

        if not isinstance(fetched, tuple):
            return default

        if fetched[4] is not None:
            value = maybe_unserialize(fetched[4])

            cls.queueCache.add(cache_key, value)
            return value

        return default

    @classmethod
    def get_meta_all(cls, object_id):
        rows = cls.get_metadata_raw({'object_id': object_id}).fetchall()
        return {row[3]: row[4] for row in rows} if isinstance(rows, list) else {}

    @classmethod
    def set_meta(cls, object_id, option, value):

        value = maybe_serialize(value)

        cls.queueCache.update(QueueCache.key(object_id, option, cls.tableName), value)

        return Database.cursor.execute(
            f"INSERT INTO {cls.tableName} (object_id, meta_key, meta_value) VALUES (?, ?, ?)",
            (object_id, option, value)
        )

    @classmethod
    def delete_meta(cls, object_id, meta_key=None):

        where = {'object_id': object_id}

        if meta_key is not None:
            where.update({'meta_key': meta_key})
            cls.queueCache.remove(QueueCache.key(object_id, meta_key, cls.tableName))
        else:
            cls.queueCache.clear()

        fields, values = cls.parse_where(where)
        return Database.cursor.execute(
            f"DELETE FROM {cls.tableName} WHERE {' AND '.join(fields)}",
            values
        )

    @staticmethod
    def check_tables():
        columns = Database.schema_to_columns(DBMeta.schema)
        Database.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {DBMeta.tableName} ({columns}, UNIQUE(object_id, meta_key) ON CONFLICT REPLACE)"
        )
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_id ON metadata(id)")
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_key ON metadata(meta_key)")
        Database.cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_speeder ON metadata(meta_key, meta_value, object_id)")

