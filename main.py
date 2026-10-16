import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers import spy_router, commands_router
from utils.database import init_db
from keep_alive import start_keep_alive

async def main():
    if not BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не указан в .env / переменных окружения")
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Инициализация базы данных
    await init_db()
    print("✅ База данных готова")

    # Запускаем keep-alive HTTP сервер (нужен для Render и подобных)
    try:
        await start_keep_alive()
        print("✅ Keep-alive сервер запущен")
    except Exception as e:
        print(f"⚠️ Keep-alive не запустился: {e}")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.include_router(spy_router)
    dp.include_router(commands_router)

    print("✅ Бот запущен и готов к работе!")
    print("📌 Не забудь подключить его как Business-бота + включить Secretary Mode в @BotFather")
    print("📂 Все уведомления и одноразовые медиа будут приходить тебе в личку с ботом")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹ Бот остановлен")