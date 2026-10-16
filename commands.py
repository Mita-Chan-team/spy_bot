from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import user_states, ADMIN_ID
from utils.helpers import get_weather, get_crypto, generate_password, get_time, PODKATS, GAY_PHRASES, LOVE_FRAMES, SECRET_FRAMES
from utils.database import get_recent_messages, get_chat_list, get_chat_history, count_messages
import random
import asyncio
import urllib.parse

router = Router()

def get_user_state(user_id: int) -> dict:
    if user_id not in user_states:
        user_states[user_id] = {
            "online": False, "bold": False, "italic": False,
            "underline": False, "monospace": False, "kawaii": False,
            "troll": False, "autoai": False, "language": None,
        }
    return user_states[user_id]


@router.message(F.text.startswith("."))
async def handle_dot_commands(message: Message):
    if not message.text:
        return

    text = message.text.strip()
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    user_id = message.from_user.id
    state = get_user_state(user_id)

    # ==================== HELP ====================
    if cmd == ".help":
        help_text = (
            "<b>📋 Список команд</b>\n\n"
            "<b>🔹 Информация</b>\n"
            ".help — этот список\n"
            ".info / .who — профиль\n"
            ".online — постоянный онлайн\n"
            ".archive — последние сообщения\n"
            ".archive chats — список всех чатов\n"
            ".archive <chat_id> [N] — история конкретного чата\n\n"
            "<b>🔹 Утилиты</b>\n"
            ".calc 2+2*2\n"
            ".weather Киев\n"
            ".time Киев\n"
            ".password 16\n"
            ".crypto btc\n"
            ".qr текст\n\n"
            "<b>🔹 Развлечения</b>\n"
            ".fuck .love .gay .secret .type .podkat .troll\n\n"
            "<b>🔹 Оформление</b>\n"
            ".bold .italic .underline .monospace .kawaii\n\n"
            "<b>🔹 Игры</b>\n"
            ".dice .casino .xo .tod\n\n"
            "<b>🔹 Модерация</b>\n"
            ".pin .unpin .del .mute .unmute\n\n"
            "<i>Spy-функции работают автоматически после подключения Business-бота.\n"
            "Все уведомления о удалении/редактировании и одноразовые медиа приходят вам в личку с ботом.</i>"
        )
        await message.answer(help_text, parse_mode="HTML")
        return

    # ==================== ARCHIVE ====================
    if cmd == ".archive":
        # .archive chats — список чатов
        if args.lower() == "chats":
            chats = await get_chat_list()
            total = await count_messages()
            if not chats:
                await message.answer("Архив пуст. Пока нет сохранённых сообщений.")
                return
            lines = [f"<b>📂 Чаты в архиве</b> (всего сообщений: {total})\n"]
            for c in chats:
                lines.append(
                    f"• <code>{c['chat_id']}</code> — {c['last_name'] or 'Unknown'}\n"
                    f"  сообщений: {c['msg_count']} | последнее: {c['last_date'] or '—'}"
                )
            await message.answer("\n".join(lines), parse_mode="HTML")
            return

        # .archive <chat_id> [limit]
        parts_args = args.split()
        chat_id = None
        limit = 30

        if parts_args:
            try:
                chat_id = int(parts_args[0])
                if len(parts_args) > 1:
                    limit = max(1, min(int(parts_args[1]), 100))
            except ValueError:
                try:
                    limit = max(1, min(int(parts_args[0]), 100))
                except ValueError:
                    limit = 30

        if chat_id:
            total = await count_messages(chat_id)
            rows = await get_chat_history(chat_id, limit=limit)
            if not rows:
                await message.answer(f"В чате <code>{chat_id}</code> ничего не найдено.", parse_mode="HTML")
                return
            lines = [f"<b>📜 История чата {chat_id}</b> (показано {len(rows)} из {total})\n"]
            for r in rows:
                media = f" [{r['media_type']}]" if r['media_type'] else ""
                lines.append(
                    f"<b>{r['full_name']}</b>{media}\n"
                    f"<code>{(r['text'] or '')[:200]}</code>"
                )
            # Разбиваем на части, если слишком длинно
            text = "\n\n".join(lines)
            if len(text) > 4000:
                for i in range(0, len(text), 4000):
                    await message.answer(text[i:i+4000], parse_mode="HTML")
            else:
                await message.answer(text, parse_mode="HTML")
            return

        # Просто .archive [limit] — последние сообщения
        rows = await get_recent_messages(limit=limit)
        total = await count_messages()
        if not rows:
            await message.answer("Архив пуст")
            return
        lines = [f"<b>Последние сообщения</b> (всего в архиве: {total})\n"]
        for r in rows:
            lines.append(
                f"#{r['id']} | {r['full_name']} | chat:<code>{r['chat_id']}</code>\n"
                f"<code>{(r['text'] or '')[:120]}</code>"
            )
        await message.answer("\n\n".join(lines), parse_mode="HTML")
        return

    # ==================== ONLINE ====================
    if cmd == ".online":
        state["online"] = not state["online"]
        status = "включён ✅" if state["online"] else "выключен ❌"
        await message.answer(f"Постоянный онлайн {status}")
        return

    # ==================== INFO / WHO ====================
    if cmd in [".info", ".who"]:
        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        is_premium = getattr(target, "is_premium", False)
        text_out = (
            f"<b>👤 Профиль</b>\n\n"
            f"ID: <code>{target.id}</code>\n"
            f"Имя: <b>{target.full_name}</b>\n"
            f"Username: @{target.username or 'нет'}\n"
            f"Язык: {target.language_code or '—'}\n"
            f"Premium: {'да ✅' if is_premium else 'нет'}"
        )
        await message.answer(text_out, parse_mode="HTML")
        return

    # ==================== CALC ====================
    if cmd == ".calc":
        if not args:
            await message.answer("Использование: <code>.calc 2+2*2</code>", parse_mode="HTML")
            return
        try:
            result = eval(args, {"__builtins__": {}}, {})
            await message.answer(f"🧮 <b>Результат:</b> <code>{result}</code>", parse_mode="HTML")
        except Exception:
            await message.answer("❌ Ошибка в выражении")
        return

    # ==================== WEATHER ====================
    if cmd == ".weather":
        city = args or "Киев"
        result = await get_weather(city)
        await message.answer(f"🌤 {result}")
        return

    # ==================== TIME ====================
    if cmd == ".time":
        city = args or "Киев"
        await message.answer(get_time(city), parse_mode="HTML")
        return

    # ==================== PASSWORD ====================
    if cmd == ".password":
        try:
            length = int(args) if args else 12
            length = max(6, min(length, 64))
        except ValueError:
            length = 12
        pwd = generate_password(length)
        await message.answer(f"🔑 Пароль ({length}): <code>{pwd}</code>", parse_mode="HTML")
        return

    # ==================== CRYPTO ====================
    if cmd == ".crypto":
        symbol = args or "btc"
        result = await get_crypto(symbol)
        await message.answer(result, parse_mode="HTML")
        return

    # ==================== QR ====================
    if cmd == ".qr":
        if not args:
            await message.answer("Использование: <code>.qr текст или ссылка</code>", parse_mode="HTML")
            return
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={urllib.parse.quote(args)}"
        await message.answer_photo(url, caption=f"QR-код для:\n<code>{args}</code>", parse_mode="HTML")
        return

    # ==================== FUCK ====================
    if cmd == ".fuck":
        msg = await message.answer("⬛")
        frames = ["⬛", "💀", "☠️", "🔥", "пошёл нахуй", "пошёл нахуй 💀", "🖤 пошёл нахуй 🖤"]
        for frame in frames:
            await asyncio.sleep(0.45)
            try:
                await msg.edit_text(frame)
            except Exception:
                break
        return

    # ==================== LOVE ====================
    if cmd == ".love":
        msg = await message.answer("❤️")
        for _ in range(8):
            await asyncio.sleep(0.35)
            try:
                await msg.edit_text(random.choice(LOVE_FRAMES))
            except Exception:
                break
        try:
            await msg.edit_text("💖 Люблю 💖")
        except Exception:
            pass
        return

    # ==================== GAY ====================
    if cmd == ".gay":
        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        percent = random.randint(0, 100)
        phrase = random.choice(GAY_PHRASES).format(percent=percent)
        await message.answer(f"🏳️‍🌈 {target.first_name} {phrase}")
        return

    # ==================== SECRET ====================
    if cmd == ".secret":
        msg = await message.answer(SECRET_FRAMES[0])
        for frame in SECRET_FRAMES[1:]:
            await asyncio.sleep(0.35)
            try:
                await msg.edit_text(frame)
            except Exception:
                break
        return

    # ==================== TYPE ====================
    if cmd == ".type":
        if not args:
            await message.answer("Использование: <code>.type любой текст</code>", parse_mode="HTML")
            return
        msg = await message.answer("▌")
        current = ""
        for char in args:
            current += char
            try:
                await msg.edit_text(current + "▌")
                await asyncio.sleep(0.07)
            except Exception:
                break
        try:
            await msg.edit_text(current)
        except Exception:
            pass
        return

    # ==================== PODKAT ====================
    if cmd == ".podkat":
        await message.answer(random.choice(PODKATS))
        return

    # ==================== TROLL ====================
    if cmd == ".troll":
        state["troll"] = not state["troll"]
        status = "включён 😈" if state["troll"] else "выключен 🙂"
        await message.answer(f"Режим троллинга {status}")
        return

    # ==================== FORMATTING ====================
    if cmd in [".bold", ".italic", ".underline", ".monospace", ".kawaii"]:
        key = cmd[1:]
        state[key] = not state[key]
        status = "включён ✅" if state[key] else "выключен ❌"
        await message.answer(f"Режим <b>{key}</b> {status}", parse_mode="HTML")
        return

    # ==================== LANGUAGE ====================
    if cmd == ".language":
        if not args or args.lower() == "off":
            state["language"] = None
            await message.answer("Перевод выключен")
        else:
            state["language"] = args.lower()[:5]
            await message.answer(f"Язык перевода: <b>{state['language']}</b>", parse_mode="HTML")
        return

    # ==================== AUTOAI ====================
    if cmd == ".autoai":
        state["autoai"] = not state["autoai"]
        status = "включён 🤖" if state["autoai"] else "выключен"
        await message.answer(f"Авто-AI {status}", parse_mode="HTML")
        return

    # ==================== DICE / CASINO ====================
    if cmd == ".dice":
        await message.answer_dice(emoji="🎲")
        return
    if cmd == ".casino":
        await message.answer_dice(emoji="🎰")
        return

    # ==================== XO ====================
    if cmd == ".xo":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬜", callback_data="xo_0"),
             InlineKeyboardButton(text="⬜", callback_data="xo_1"),
             InlineKeyboardButton(text="⬜", callback_data="xo_2")],
            [InlineKeyboardButton(text="⬜", callback_data="xo_3"),
             InlineKeyboardButton(text="⬜", callback_data="xo_4"),
             InlineKeyboardButton(text="⬜", callback_data="xo_5")],
            [InlineKeyboardButton(text="⬜", callback_data="xo_6"),
             InlineKeyboardButton(text="⬜", callback_data="xo_7"),
             InlineKeyboardButton(text="⬜", callback_data="xo_8")],
        ])
        await message.answer("🎮 Крестики-нолики\nХод: ❌", reply_markup=keyboard)
        return

    # ==================== TOD ====================
    if cmd == ".tod":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Правда 🗣", callback_data="tod_truth"),
             InlineKeyboardButton(text="Действие 🎯", callback_data="tod_dare")],
            [InlineKeyboardButton(text="Случайно 🎲", callback_data="tod_random")],
        ])
        await message.answer("🔥 Правда или Действие?", reply_markup=keyboard)
        return

    # ==================== PIN / UNPIN / DEL / MUTE ====================
    if cmd == ".pin":
        if not message.reply_to_message:
            await message.answer("Ответь на сообщение")
            return
        try:
            await message.bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
            await message.answer("📌 Закреплено")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
        return

    if cmd == ".unpin":
        try:
            if message.reply_to_message:
                await message.bot.unpin_chat_message(message.chat.id, message.reply_to_message.message_id)
            else:
                await message.bot.unpin_chat_message(message.chat.id)
            await message.answer("📍 Закрепление снято")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
        return

    if cmd == ".del":
        try:
            count = int(args) if args else 1
            count = max(1, min(count, 30))
        except ValueError:
            count = 1
        await message.answer(f"🗑 Запрошено удаление {count} сообщений (ограничено правами)")
        try:
            await message.delete()
        except Exception:
            pass
        return

    if cmd in [".mute", ".unmute"]:
        if not message.reply_to_message:
            await message.answer("Ответь на сообщение пользователя")
            return
        action = "замутить" if cmd == ".mute" else "размутить"
        await message.answer(f"Попытка {action} (нужны права админа)")
        return

    # Заглушки
    if cmd in [".tts", ".translate", ".voicefx", ".watermark", ".story",
               ".circle", ".round", ".tt", ".inst", ".yt", ".music",
               ".copytg", ".clone", ".ai", ".spam", ".stop", ".mins"]:
        await message.answer(f"⚙️ Команда <code>{cmd}</code> пока в разработке", parse_mode="HTML")
        return


@router.callback_query(F.data.startswith("xo_"))
async def xo_callback(callback: CallbackQuery):
    await callback.answer("Игра в разработке")

@router.callback_query(F.data.startswith("tod_"))
async def tod_callback(callback: CallbackQuery):
    truths = [
        "Какой самый стыдный поступок ты совершал?",
        "В кого ты сейчас тайно влюблён?",
        "Какую тайну ты никогда никому не рассказывал?",
        "Что тебя больше всего бесит в людях?",
    ]
    dares = [
        "Напиши бывшему/бывшей «я скучаю».",
        "Сделай 10 приседаний прямо сейчас.",
        "Расскажи анекдот голосом ребёнка.",
        "Поставь на 5 минут странный статус.",
    ]
    data = callback.data
    if data == "tod_truth":
        text = f"🗣 Правда:\n\n{random.choice(truths)}"
    elif data == "tod_dare":
        text = f"🎯 Действие:\n\n{random.choice(dares)}"
    else:
        text = f"{'🗣 Правда' if random.random() > 0.5 else '🎯 Действие'}:\n\n{random.choice(truths if random.random() > 0.5 else dares)}"
    await callback.message.edit_text(text)
    await callback.answer()