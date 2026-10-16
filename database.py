import aiosqlite
import os
from config import DB_PATH

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                message_id INTEGER,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                text TEXT,
                media_type TEXT,
                media_file_id TEXT,
                is_view_once INTEGER DEFAULT 0,
                date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                message_id INTEGER,
                event_type TEXT,
                old_text TEXT,
                new_text TEXT,
                full_name TEXT,
                date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Индексы для быстрой выборки
        await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date)")
        await db.commit()

async def save_message(chat_id, message_id, user_id, username, full_name, text, media_type=None, media_file_id=None, is_view_once=False, date=None):
    async with aiosqlite.connect(DB_PATH) as db:
        # Чтобы не дублировать одно и то же сообщение
        await db.execute("""
            INSERT OR IGNORE INTO messages (chat_id, message_id, user_id, username, full_name, text, media_type, media_file_id, is_view_once, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (chat_id, message_id, user_id, username, full_name, text, media_type, media_file_id, int(is_view_once), date))
        await db.commit()

async def get_message(chat_id, message_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM messages WHERE chat_id = ? AND message_id = ? ORDER BY id DESC LIMIT 1",
            (chat_id, message_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

async def save_event(chat_id, message_id, event_type, old_text, new_text, full_name, date=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO events (chat_id, message_id, event_type, old_text, new_text, full_name, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chat_id, message_id, event_type, old_text, new_text, full_name, date))
        await db.commit()

async def get_recent_messages(chat_id=None, limit=20, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        if chat_id:
            query = "SELECT * FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ? OFFSET ?"
            params = (chat_id, limit, offset)
        else:
            query = "SELECT * FROM messages ORDER BY id DESC LIMIT ? OFFSET ?"
            params = (limit, offset)
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

async def get_chat_list():
    """Список всех чатов, которые бот записывал"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT chat_id, 
                   COUNT(*) as msg_count,
                   MAX(full_name) as last_name,
                   MAX(date) as last_date
            FROM messages 
            GROUP BY chat_id 
            ORDER BY last_date DESC
        """) as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

async def get_chat_history(chat_id, limit=50, offset=0):
    """Полная история конкретного чата (от старых к новым)"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT * FROM messages 
            WHERE chat_id = ? 
            ORDER BY id ASC 
            LIMIT ? OFFSET ?
        """, (chat_id, limit, offset)) as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

async def count_messages(chat_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        if chat_id:
            async with db.execute("SELECT COUNT(*) FROM messages WHERE chat_id = ?", (chat_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
        else:
            async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0