"""
Простой HTTP-сервер для Keep-Alive на Render (и подобных платформах).
Нужен, чтобы бесплатный инстанс не засыпал.
"""

from aiohttp import web
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

async def health(request):
    return web.Response(text="Bot is alive ✅")

async def start_keep_alive():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Keep-alive server started on port {port}")
    return runner