# Database

### database.db

### users:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
- `user_id` INTEGER NOT NULL,
- `chat_id` INTEGER NOT NULL,
- `lang` TEXT,
- `gender` TEXT DEFAULT 'none',
- `bio` TEXT,
- `birthday` TEXT,
- `location` BLOB,
- `is_bot` INTEGER NOT NULL DEFAULT 0,
- `reported` INTEGER NOT NULL DEFAULT 0
- UNIQUE(user_id, chat_id) ON CONFLICT REPLACE


### feedback:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
- `user_id` INTEGER NOT NULL,
- `message` TEXT,
- `attachment` TEXT


### schedules:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
- `chat_id` TEXT,
- `name` TEXT NOT NULL UNIQUE,
- `timestamp` INTEGER NOT NULL,
- `reminder` TEXT,
- `handler` TEXT,
- UNIQUE(chat_id, name, timestamp, handler) ON CONFLICT REPLACE


### metadata:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
- `object_id` INTEGER NOT NULL,
- `meta_key` TEXT NOT NULL,
- `meta_value` TEXT NOT NULL,
- UNIQUE(object_id, meta_key) ON CONFLICT REPLACE

# chat_queue
- `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
- `user_id` TEXT NOT NULL,
- `chat_id` TEXT,
- `gender` TEXT DEFAULT 'none',
- `min_age` INTEGER NOT NULL DEFAULT 0,
- `max_age` INTEGER NOT NULL DEFAULT 100,
- `distance` INTEGER NOT NULL DEFAULT 0,
- `media_enabled` INTEGER NOT NULL DEFAULT 1,
- `reopen` INTEGER NOT NULL DEFAULT 1,
- `status` INTEGER NOT NULL DEFAULT 0
- UNIQUE(user_id, chat_id) ON CONFLICT REPLACE)

Download [DB Browser for SQLite](https://sqlitebrowser.org) to see these databases. 
