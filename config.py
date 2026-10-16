import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Путь к базе данных
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "archive.db")

# Состояния пользователей (в памяти)
user_states = {}