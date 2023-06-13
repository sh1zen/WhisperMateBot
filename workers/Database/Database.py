import sqlite3
from sqlite3 import Cursor

from utils.QueueCache import QueueCache
from utils.utility import maybe_serialize, maybe_unserialize


class Database:
    tableName = None
    queueCache = QueueCache(2000)

    __slots__ = ('conn', 'cursor', 'query')

    @staticmethod
    def setup(name):
        Database.query = ''
        # Connect to the database
        Database.conn = sqlite3.connect(name)

        # row_factory to create dictionary cursor
        Database.conn.row_factory = sqlite3.Row
        Database.cursor = Database.conn.cursor()

        # check database tables
        Database.check_tables()

    @classmethod
    def parse_where(cls, where):
        """Build query for select and delete
        {key: value},
        {key: {compare: ?, value: ?}},
        {key: [?,?,?]}
        {key: {...inner_query...}}
        """
        if not where:
            return '', ()

        fields = []
        values = []
        for key, value in where.items():
            compare = None
            inner_table = False
            raw = False

            if isinstance(value, dict):
                compare = value.get('compare')
                if 'raw' in value:
                    raw = True
                if compare in ('IN_TABLE', 'NOT_IN_TABLE'):
                    compare = str(compare).replace('_', ' ').replace('TABLE', '').strip()
                    inner_table = True
                else:
                    value = value.get('value')

            if value is None:
                continue

            if inner_table:
                inner_fields, inner_values = cls.compile(value)
                fields.append(f"{key} {compare} (" + inner_fields + ")")
                values.extend(inner_values)

            elif isinstance(value, list):
                compare = 'IN' if compare is None else compare
                if compare == 'BETWEEN':
                    fields.append(f"({key} {compare} ? AND ?)")
                    value = value[:2]
                else:
                    fields.append(f"{key} {compare} ({Database.placeholders(len(value))})")
                values.extend(value)

            else:
                compare = '=' if compare is None else compare
                if raw:
                    fields.append(f"{key} {compare} {value}")
                else:
                    fields.append(f"{key} {compare} ?")
                    values.append(value)

        return fields, tuple(values)

    @classmethod
    def parse_fields(cls, fields):
        if fields is None:
            return fields, (), []

        columns = []
        values = []

        for key, value in fields.items():
            columns.append(key)
            values.append(value)

        return columns, tuple(values), Database.placeholders(len(values))

    @classmethod
    def insert(cls, fields) -> None | Cursor:
        if cls.tableName is None:
            return None

        columns, values, placeholders = cls.parse_fields(fields)

        res = Database.cursor.execute(
            f"REPLACE INTO {cls.tableName} ({', '.join(columns)}) VALUES ({placeholders})",
            values
        )

        Database.commit()

        return res

    @classmethod
    def compile(cls, raw_query):
        query = {
            'action': 'SELECT',
            'fields': '*',
            'from': cls.tableName,
            'groupby': '',
            'orderby': '',
            'limit': '',
            'offset': '',
            'where': ''
        }
        query.update(raw_query)
        from_clause = where_clause = ''
        values = ()

        if query['groupby']:
            query.update({'groupby': f"GROUP BY {query['groupby']}"})

        if query['orderby']:
            if isinstance(query['orderby'], dict):
                query.update({
                    'groupby': "ORDER BY " + ', '.join(
                        [f'{field} {order}' for field, order in query['orderby'].items()]
                    )
                })
            else:
                query.update({'orderby': f"ORDER BY {query['orderby']}"})

        if query['limit']:
            query.update({'limit': f"LIMIT {query['limit']}"})

        if query['offset']:
            query.update({'offset': f"OFFSET {query['offset']}"})

        if query['where']:
            fields, values = Database.parse_where(query['where'])
            where_clause = f"WHERE {' AND '.join(fields)}"

        if query['from']:
            if isinstance(query['from'], dict):
                query['from'] = ', '.join(f'{key} AS {value}' for key, value in query['from'].items())
            from_clause = f"FROM {query['from']}"

        sql_query = f"""
            {query['action']} {query['fields']} {from_clause} {where_clause}
            {query['groupby']} {query['orderby']} {query['limit']} {query['offset']}
        """

        sql_query = sql_query.strip()

        return sql_query, values

    @classmethod
    def select(cls, raw_query) -> None | Cursor:
        sql_query, values = cls.compile(raw_query)
        print(sql_query.replace("?", "'{}'").format(*values))
        return Database.cursor.execute(sql_query, values)

    @classmethod
    def get_rows(cls, where):

        if 'where' not in where:
            where = {'where': where}

        # Fetch all rows and convert each row to a dictionary
        return [dict(row) for row in cls.select(where).fetchall()]

    @classmethod
    def get_row(cls, where):

        if 'where' not in where:
            where = {'where': where}

        return dict(cls.select(where).fetchone())

    @classmethod
    def update_value(cls, where, key, new_value):

        fields, values = Database.parse_where(where)

        new_value = maybe_serialize(new_value)

        res = Database.cursor.execute(
            f"UPDATE {cls.tableName} SET {key} = ? WHERE {' AND '.join(fields)}",
            (new_value,) + values
        )

        Database.commit()
        return res

    @classmethod
    def get_value(cls, where, key, default=None):

        if 'where' not in where:
            where = {'where': where}

        where.update({'fields': key})

        result = cls.select(where).fetchone()

        return maybe_unserialize(result[0] if result else default)

    @classmethod
    def delete(cls, where=None) -> None | Cursor:

        if cls.tableName is None:
            return None

        fields, values = Database.parse_where(where)
        res = Database.cursor.execute(f"DELETE FROM {cls.tableName} WHERE {' AND '.join(fields)}", values)

        Database.commit()
        return res

    @classmethod
    def count(cls):
        return Database.cursor.execute('SELECT COUNT(*) FROM {}'.format(cls.tableName)).fetchone()[0]

    @classmethod
    def has(cls, check_value):

        fields, values = Database.parse_where(check_value)

        result = Database.cursor.execute(
            f"SELECT EXISTS (SELECT 1 FROM {cls.tableName} WHERE {' AND '.join(fields)})",
            values
        ).fetchone()

        # Return True if the value exists, False otherwise
        return bool(result[0])

    @staticmethod
    def schema_to_columns(schema):
        return ', '.join([f'{key} {value}' for key, value in schema.items()])

    @staticmethod
    def check_tables():

        from workers.Database.DBChat import DBChat
        from workers.Database.DBFeedbacks import DBFeedbacks
        from workers.Database.DBSchedules import DBSchedules
        from workers.Database.DBUsers import DBUsers
        from workers.Database.DBMeta import DBMeta

        DBMeta.check_tables()
        DBUsers.check_tables()
        DBFeedbacks.check_tables()
        DBSchedules.check_tables()
        DBChat.check_tables()

        Database.conn.commit()

    @staticmethod
    def placeholders(num, join=','):
        return f' {join} '.join(['?' for _ in range(num)])

    @staticmethod
    def commit():
        Database.conn.commit()

    @staticmethod
    def close():
        Database.conn.commit()
        Database.conn.close()
