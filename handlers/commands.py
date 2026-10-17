from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import user_states, ADMIN_ID
from utils.helpers import get_weather, get_crypto, generate_password, get_time, PODKATS, GAY_PHRASES, LOVE_FRAMES, SECRET_FRAMES
from utils.database import get_recent_messages, get_chat_list, get_chat_history, count_messages
import random
import asyncio
import urllib.parse
import aiohttp

router = Router()

def get_user_state(user_id: int) -> dict:
    if user_id not in user_states:
        user_states[user_id] = {
            "online": False, "bold": False, "italic": False,
            "underline": False, "monospace": False, "kawaii": False,
            "troll": False, "autoai": False, "language": None,
            "clone": False, "spam_active": False,
        }
    return user_states[user_id]


async def reply_edit(message: Message, text: str, **kwargs):
    """Редактирует исходное сообщение с командой. Если не получается — отправляет новое."""
    try:
        await message.edit_text(text, **kwargs)
    except Exception:
        try:
            await message.answer(text, **kwargs)
        except Exception:
            pass


@router.message(F.text.startswith("."))
@router.business_message(F.text.startswith("."))
async def handle_dot_commands(message: Message):
    if not message.text:
        return

    text = message.text.strip()
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    user_id = message.from_user.id if message.from_user else 0
    state = get_user_state(user_id)

    # ==================== HELP ====================
    if cmd == ".help":
        help_text = (
            "<b>📋 Список команд</b>\n\n"
            "<b>▫️ Информация</b>\n"
            ".help .online .info .who .calc .weather .time\n"
            ".password .crypto .id .archive\n\n"
            "<b>▫️ Развлечения</b>\n"
            ".fuck .love .gay .secret .type .podkat .troll\n"
            ".chance .choose .flip .ship .say\n\n"
            "<b>▫️ Оформление</b>\n"
            ".kawaii .bold .italic .underline .monospace\n"
            ".clone .language\n\n"
            "<b>▫️ Игры</b>\n"
            ".xo .mins .dice .casino .tod\n\n"
            "<b>▫️ Голос / Текст</b>\n"
            ".tts .translate (.tr) .voicefx\n\n"
            "<b>▫️ Медиа</b>\n"
            ".watermark .story .circle .round .qr\n"
            ".tt .inst .yt .music\n\n"
            "<b>▫️ Профиль / AI</b>\n"
            ".copytg .who .ai .autoai\n\n"
            "<b>▫️ Модерация</b>\n"
            ".mute .unmute .pin .unpin .spam .stop .del\n\n"
            "<i>Spy: уведомления об удалении/редактировании + сохранение одноразовых медиа приходят в личку с ботом.</i>"
        )
        await reply_edit(message, help_text, parse_mode="HTML")
        return

    # ==================== ARCHIVE ====================
    if cmd == ".archive":
        # .archive chats — список чатов
        if args.lower() == "chats":
            chats = await get_chat_list()
            total = await count_messages()
            if not chats:
                await reply_edit(message, "Архив пуст. Пока нет сохранённых сообщений.")
                return
            lines = [f"<b>📂 Чаты в архиве</b> (всего сообщений: {total})\n"]
            for c in chats:
                lines.append(
                    f"• <code>{c['chat_id']}</code> — {c['last_name'] or 'Unknown'}\n"
                    f"  сообщений: {c['msg_count']} | последнее: {c['last_date'] or '—'}"
                )
            await reply_edit(message, "\n".join(lines), parse_mode="HTML")
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
                await reply_edit(message, f"В чате <code>{chat_id}</code> ничего не найдено.", parse_mode="HTML")
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
            await reply_edit(message, "Архив пуст")
            return
        lines = [f"<b>Последние сообщения</b> (всего в архиве: {total})\n"]
        for r in rows:
            lines.append(
                f"#{r['id']} | {r['full_name']} | chat:<code>{r['chat_id']}</code>\n"
                f"<code>{(r['text'] or '')[:120]}</code>"
            )
        await reply_edit(message, "\n\n".join(lines), parse_mode="HTML")
        return

    # ==================== ONLINE ====================
    if cmd == ".online":
        state["online"] = not state["online"]
        status = "включён ✅" if state["online"] else "выключен ❌"
        await reply_edit(message, f"Постоянный онлайн {status}")
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
        await reply_edit(message, text_out, parse_mode="HTML")
        return

    # ==================== CALC ====================
    if cmd == ".calc":
        if not args:
            await reply_edit(message, "Использование: <code>.calc 2+2*2</code>", parse_mode="HTML")
            return
        try:
            result = eval(args, {"__builtins__": {}}, {})
            await reply_edit(message, f"🧮 <b>Результат:</b> <code>{result}</code>", parse_mode="HTML")
        except Exception:
            await reply_edit(message, "❌ Ошибка в выражении")
        return

    # ==================== WEATHER ====================
    if cmd == ".weather":
        city = args or "Киев"
        result = await get_weather(city)
        await reply_edit(message, f"🌤 {result}")
        return

    # ==================== TIME ====================
    if cmd == ".time":
        city = args or "Киев"
        await reply_edit(message, get_time(city), parse_mode="HTML")
        return

    # ==================== PASSWORD ====================
    if cmd == ".password":
        try:
            length = int(args) if args else 12
            length = max(6, min(length, 64))
        except ValueError:
            length = 12
        pwd = generate_password(length)
        await reply_edit(message, f"🔑 Пароль ({length}): <code>{pwd}</code>", parse_mode="HTML")
        return

    # ==================== CRYPTO ====================
    if cmd == ".crypto":
        symbol = args or "btc"
        result = await get_crypto(symbol)
        await reply_edit(message, result, parse_mode="HTML")
        return

    # ==================== QR ====================
    if cmd == ".qr":
        if not args:
            await reply_edit(message, "Использование: <code>.qr текст или ссылка</code>", parse_mode="HTML")
            return
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={urllib.parse.quote(args)}"
        await message.answer_photo(url, caption=f"QR-код для:\n<code>{args}</code>", parse_mode="HTML")
        return

    # ==================== FUCK ====================
    if cmd == ".fuck":
        frames = ["⬛", "💀", "☠️", "🔥", "пошёл нахуй", "пошёл нахуй 💀", "🖤 пошёл нахуй 🖤"]
        for frame in frames:
            try:
                await message.edit_text(frame)
            except Exception:
                break
            await asyncio.sleep(0.45)
        return

    # ==================== LOVE ====================
    if cmd == ".love":
        for _ in range(8):
            try:
                await message.edit_text(random.choice(LOVE_FRAMES))
            except Exception:
                break
            await asyncio.sleep(0.35)
        try:
            await message.edit_text("💖 Люблю 💖")
        except Exception:
            pass
        return

    # ==================== GAY ====================
    if cmd == ".gay":
        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        percent = random.randint(0, 100)
        phrase = random.choice(GAY_PHRASES).format(percent=percent)
        await reply_edit(message, f"🏳️‍🌈 {target.first_name} {phrase}")
        return

    # ==================== SECRET ====================
    if cmd == ".secret":
        for frame in SECRET_FRAMES:
            try:
                await message.edit_text(frame)
            except Exception:
                break
            await asyncio.sleep(0.35)
        return

    # ==================== TYPE ====================
    if cmd == ".type":
        if not args:
            await reply_edit(message, "Использование: <code>.type любой текст</code>", parse_mode="HTML")
            return
        current = ""
        for char in args:
            current += char
            try:
                await message.edit_text(current + "▌")
            except Exception:
                break
            await asyncio.sleep(0.07)
        try:
            await message.edit_text(current)
        except Exception:
            pass
        return

    # ==================== PODKAT ====================
    if cmd == ".podkat":
        await reply_edit(message, random.choice(PODKATS))
        return

    # ==================== TROLL ====================
    if cmd == ".troll":
        state["troll"] = not state["troll"]
        status = "включён 😈" if state["troll"] else "выключен 🙂"
        await reply_edit(message, f"Режим троллинга {status}")
        return

    # ==================== FORMATTING ====================
    if cmd in [".bold", ".italic", ".underline", ".monospace", ".kawaii"]:
        key = cmd[1:]
        state[key] = not state[key]
        status = "включён ✅" if state[key] else "выключен ❌"
        await reply_edit(message, f"Режим <b>{key}</b> {status}", parse_mode="HTML")
        return

    # ==================== LANGUAGE ====================
    if cmd == ".language":
        if not args or args.lower() == "off":
            state["language"] = None
            await reply_edit(message, "Перевод выключен")
        else:
            state["language"] = args.lower()[:5]
            await reply_edit(message, f"Язык перевода: <b>{state['language']}</b>", parse_mode="HTML")
        return

    # ==================== AUTOAI ====================
    if cmd == ".autoai":
        state["autoai"] = not state["autoai"]
        status = "включён 🤖" if state["autoai"] else "выключен"
        await reply_edit(message, f"Авто-AI {status}", parse_mode="HTML")
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

    # ==================== TRANSLATE ====================
    if cmd == ".translate" or cmd == ".tr":
        if not args and not message.reply_to_message:
            await message.answer("Использование:\n<code>.tr en текст</code>\nили ответом на сообщение", parse_mode="HTML")
            return
        try:
            if message.reply_to_message and not args:
                text_to_tr = message.reply_to_message.text or message.reply_to_message.caption or ""
                lang = "en"
            else:
                parts_tr = args.split(maxsplit=1)
                if len(parts_tr) == 1:
                    lang = "en"
                    text_to_tr = parts_tr[0]
                else:
                    lang = parts_tr[0]
                    text_to_tr = parts_tr[1]
            if not text_to_tr:
                await message.answer("Нет текста для перевода")
                return
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text_to_tr)}&langpair=auto|{lang}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    translated = data.get("responseData", {}).get("translatedText", "Ошибка перевода")
            await reply_edit(message, f"🌐 <b>Перевод ({lang}):</b>\n{translated}", parse_mode="HTML")
        except Exception as e:
            await message.answer(f"Ошибка перевода: {e}")
        return

    # ==================== AI (простой) ====================
    if cmd == ".ai":
        if not args and not message.reply_to_message:
            await message.answer("Использование: <code>.ai твой вопрос</code>", parse_mode="HTML")
            return
        question = args or (message.reply_to_message.text if message.reply_to_message else "")
        await message.answer("🤖 Думаю...")
        try:
            # Простой ответ через публичный API (можно потом заменить на свой ключ)
            prompt = f"Ответь коротко и полезно на русском: {question}"
            url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as resp:
                    answer = await resp.text()
            await reply_edit(message, f"🤖 {answer[:3000]}")
        except Exception as e:
            await message.answer(f"Ошибка AI: {e}")
        return

    # ==================== SPAM ====================
    if cmd == ".spam":
        if not args:
            await message.answer("Использование: <code>.spam 5 Привет</code>", parse_mode="HTML")
            return
        try:
            parts_spam = args.split(maxsplit=1)
            count = int(parts_spam[0])
            text_spam = parts_spam[1] if len(parts_spam) > 1 else "spam"
            count = max(1, min(count, 20))
        except Exception:
            await message.answer("Неверный формат")
            return
        state["spam_active"] = True
        for i in range(count):
            if not state.get("spam_active"):
                break
            await message.answer(text_spam)
            await asyncio.sleep(0.4)
        state["spam_active"] = False
        return

    if cmd == ".stop":
        state["spam_active"] = False
        await reply_edit(message, "⏹ Спам остановлен")
        return

    # ==================== ID ====================
    if cmd == ".id":
        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        chat = message.chat
        await message.answer(
            f"👤 User ID: <code>{target.id}</code>\n"
            f"💬 Chat ID: <code>{chat.id}</code>",
            parse_mode="HTML"
        )
        return

    # ==================== CHANCE / RANDOM ====================
    if cmd == ".chance" or cmd == ".random":
        percent = random.randint(0, 100)
        text_q = args or "этого"
        await reply_edit(message, f"🎲 Вероятность {text_q}: <b>{percent}%</b>", parse_mode="HTML")
        return

    # ==================== CHOOSE ====================
    if cmd == ".choose" or cmd == ".or":
        if not args or "|" not in args:
            await message.answer("Использование: <code>.choose вариант1 | вариант2 | вариант3</code>", parse_mode="HTML")
            return
        options = [x.strip() for x in args.split("|") if x.strip()]
        if len(options) < 2:
            await message.answer("Нужно минимум 2 варианта")
            return
        await reply_edit(message, f"🎯 Я выбираю: <b>{random.choice(options)}</b>", parse_mode="HTML")
        return

    # ==================== FLIP ====================
    if cmd == ".flip" or cmd == ".coin":
        await reply_edit(message, "🪙 " + random.choice(["Орёл", "Решка"]))
        return

    # ==================== SHIP ====================
    if cmd == ".ship":
        if not message.reply_to_message:
            await message.answer("Ответь на сообщение человека")
            return
        p1 = message.from_user.first_name
        p2 = message.reply_to_message.from_user.first_name
        percent = random.randint(0, 100)
        await reply_edit(message, f"💘 Совместимость {p1} + {p2}: <b>{percent}%</b>", parse_mode="HTML")
        return

    # ==================== SAY ====================
    if cmd == ".say":
        if not args:
            await message.answer("Напиши текст после команды")
            return
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(args)
        return

    # ==================== STICKER ID ====================
    if cmd == ".sid":
        if not message.reply_to_message or not message.reply_to_message.sticker:
            await message.answer("Ответь на стикер")
            return
        st = message.reply_to_message.sticker
        await reply_edit(message, f"Sticker ID:\n<code>{st.file_id}</code>", parse_mode="HTML")
        return

    # ==================== CLONE ====================
    if cmd == ".clone":
        state["clone"] = not state.get("clone", False)
        status = "включён 🪞" if state["clone"] else "выключен"
        await message.answer(f"Режим клонирования сообщений {status}")
        return

    # ==================== TTS (простой) ====================
    if cmd == ".tts":
        if not args:
            await message.answer("Использование: <code>.tts текст</code>", parse_mode="HTML")
            return
        try:
            # Используем Google TTS через публичный endpoint
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(args)}&tl=ru&client=tw-ob"
            await message.answer_voice(url, caption="🗣 TTS")
        except Exception as e:
            await message.answer(f"Ошибка TTS: {e}")
        return

    # ==================== WATERMARK (простой текст) ====================
    if cmd == ".watermark":
        if not message.reply_to_message or not message.reply_to_message.photo:
            await message.answer("Ответь на фото + укажи текст: <code>.watermark текст</code>", parse_mode="HTML")
            return
        text_wm = args or "©"
        await message.answer(f"🖼 Watermark «{text_wm}» — полная обработка будет в следующей версии (нужен PIL + скачивание). Пока просто отмечено.")
        return

    # ==================== ROUND / CIRCLE ====================
    if cmd in [".round", ".circle"]:
        if not message.reply_to_message:
            await message.answer("Ответь на видео / GIF / кружок")
            return
        await message.answer("⚙️ Обработка кружка будет доступна после добавления ffmpeg на сервер.")
        return

    # ==================== DOWNLOADERS ====================
    if cmd in [".yt", ".tt", ".inst", ".music"]:
        if not args:
            await message.answer(f"Использование: <code>{cmd} ссылка или запрос</code>", parse_mode="HTML")
            return
        await message.answer(
            f"📥 Скачивание ({cmd}) пока в разработке.\n"
            "На бесплатном Render сложно поставить yt-dlp + ffmpeg.\n"
            "Могу добавить позже, если перейдём на VPS."
        )
        return

    # ==================== COPYTG ====================
    if cmd == ".copytg":
        if not message.reply_to_message:
            await message.answer("Ответь на сообщение пользователя")
            return
        user = message.reply_to_message.from_user
        await message.answer(
            f"📋 Копирование профиля:\n"
            f"Имя: {user.full_name}\n"
            f"Username: @{user.username or 'нет'}\n"
            f"ID: <code>{user.id}</code>\n\n"
            f"<i>Полное копирование аватара/описания в Business API ограничено.</i>",
            parse_mode="HTML"
        )
        return

    # ==================== MINS ====================
    if cmd == ".mins":
        await message.answer("💣 Игра «Мины» пока в разработке. Скоро добавлю.")
        return

    # ==================== STORY ====================
    if cmd == ".story":
        if not message.reply_to_message or not message.reply_to_message.photo:
            await message.answer("Ответь на фото")
            return
        await message.answer("📱 Разделение фото на 3×3 истории — в следующей версии.")
        return

    # ==================== VOICEFX ====================
    if cmd == ".voicefx":
        await message.answer("🎙 Эффекты голоса требуют ffmpeg. Будет на VPS.")
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
