import random
import string
import aiohttp
from datetime import datetime
import pytz
import urllib.parse

async def get_weather(city: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3&lang=ru"
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()
                return "Не удалось получить погоду."
    except Exception:
        return "Ошибка при получении погоды."

async def get_crypto(symbol: str = "btc") -> str:
    mapping = {
        "btc": "bitcoin", "eth": "ethereum", "ton": "the-open-network",
        "sol": "solana", "usdt": "tether", "not": "notcoin", "trx": "tron",
        "xrp": "ripple", "doge": "dogecoin"
    }
    coin_id = mapping.get(symbol.lower(), symbol.lower())
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd,uah,rub"
            async with session.get(url) as resp:
                data = await resp.json()
                if coin_id in data:
                    usd = data[coin_id].get("usd", "—")
                    uah = data[coin_id].get("uah", "—")
                    rub = data[coin_id].get("rub", "—")
                    return (
                        f"💰 <b>{symbol.upper()}</b>\n"
                        f"USD: ${usd}\n"
                        f"UAH: {uah} ₴\n"
                        f"RUB: {rub} ₽"
                    )
                return "Монета не найдена."
    except Exception:
        return "Ошибка при получении курса."

def generate_password(length: int = 12) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))

def get_time(city: str = "Киев") -> str:
    tz_map = {
        "киев": "Europe/Kyiv", "київ": "Europe/Kyiv", "kyiv": "Europe/Kyiv",
        "львов": "Europe/Kyiv", "одесса": "Europe/Kyiv", "харьков": "Europe/Kyiv",
        "москва": "Europe/Moscow", "варшава": "Europe/Warsaw",
        "берлин": "Europe/Berlin", "лондон": "Europe/London",
        "нью-йорк": "America/New_York", "токио": "Asia/Tokyo",
        "минск": "Europe/Minsk", "алматы": "Asia/Almaty"
    }
    tz_name = tz_map.get(city.lower(), "Europe/Kyiv")
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        return f"🕐 <b>{city.title()}</b>: {now.strftime('%H:%M:%S %d.%m.%Y')}"
    except Exception:
        return "Не удалось определить время."

PODKATS = [
    "Ты случайно не Wi-Fi? Потому что я чувствую с тобой сильную связь 📶",
    "Если ты будешь звездой, то я стану твоим небом 🌌",
    "Ты как кофе — без тебя моё утро не начинается ☕",
    "У меня есть только один минус — минус тебя рядом 😔",
    "Ты случайно не Google? Потому что в тебе я нашёл всё, что искал 🔍",
    "Если красота была преступлением — тебя бы посадили навечно 😍",
    "Ты как зарядка — без тебя я быстро сажусь 🔋",
    "Можно я буду твоим любимым уведомлением? 🔔",
]

GAY_PHRASES = [
    "по шкале гейства сегодня {percent}% 💅",
    "гейметр показывает {percent}% 🏳️‍🌈",
    "вероятность быть геем: {percent}% ✨",
    "уровень гейства: {percent}% 💖",
]

LOVE_FRAMES = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "💖", "💗", "💓", "💕"]

SECRET_FRAMES = [
    "▒▒▒▒▒▒▒▒▒▒ 0%",
    "█▒▒▒▒▒▒▒▒▒ 10%",
    "██▒▒▒▒▒▒▒▒ 20%",
    "███▒▒▒▒▒▒▒ 30%",
    "████▒▒▒▒▒▒ 40%",
    "█████▒▒▒▒▒ 50%",
    "██████▒▒▒▒ 60%",
    "███████▒▒▒ 70%",
    "████████▒▒ 80%",
    "█████████▒ 90%",
    "██████████ 100%",
    "Готово 👀"
]
