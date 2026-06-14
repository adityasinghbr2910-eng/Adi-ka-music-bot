from pyrogram.enums import ButtonStyle
import asyncio
from logging import getLogger
from typing import Dict, Set

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message
from pyrogram.raw import functions

from KanhaMusic import app
from KanhaMusic.utils.database import get_assistant
from KanhaMusic.core.mongo import mongodb

LOGGER = getLogger(__name__)

vc_active_users: Dict[int, Set[int]] = {}
active_vc_chats: Set[int] = set()

vcloggerdb = mongodb.vclogger


async def is_vclogger_enabled(chat_id: int) -> bool:
    doc = await vcloggerdb.find_one({"chat_id": chat_id})
    return bool(doc.get("enabled", False)) if doc else False


async def set_vclogger_status(chat_id: int, enabled: bool) -> None:
    await vcloggerdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": enabled}},
        upsert=True
    )


async def remove_vclogger_chat(chat_id: int) -> None:
    await vcloggerdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": False}},
        upsert=True
    )
    active_vc_chats.discard(chat_id)
    vc_active_users.pop(chat_id, None)
    LOGGER.info(f"Removed invalid chat {chat_id} from VC logger DB")


async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            return True
    except Exception:
        pass
    try:
        userbot = await get_assistant(chat_id)
        if userbot:
            member = await userbot.get_chat_member(chat_id, user_id)
            if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
                return True
    except Exception as e:
        LOGGER.warning(f"Admin check failed for {user_id} in {chat_id}: {e}")
    return False


async def restore_vclogger_sessions():
    async for doc in vcloggerdb.find({"enabled": True}):
        chat_id = doc["chat_id"]
        if chat_id not in active_vc_chats:
            active_vc_chats.add(chat_id)
            asyncio.create_task(monitor_vc_chat(chat_id))
            LOGGER.info(f"Restored VC logger for chat {chat_id}")


@app.on_message(
    filters.command("vclogger", prefixes=[".", "!", "/", "@", "?", "'"]) & filters.group
)
async def vclogger_command(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    args    = message.text.split()

    if not await is_admin(chat_id, user_id):
        return await message.reply(
            "<tg-emoji emoji-id='5197288647275071607'>🛡</tg-emoji> <b>ᴘᴇʀᴍɪssɪᴏɴ ᴅᴇɴɪᴇᴅ!</b>\n\n"
            "<tg-emoji emoji-id='5316992572680320646'>👤</tg-emoji> ᴏɴʟʏ <b>ᴀᴅᴍɪɴs</b> ᴏʀ <b>ᴏᴡɴᴇʀs</b> ᴄᴀɴ ᴜsᴇ ᴠᴄ ʟᴏɢɢᴇʀ.\n\n"
            "<tg-emoji emoji-id='5990276318925691338'>⚡️</tg-emoji> <i>ɪ ᴅᴏɴ'ᴛ ᴛᴀᴋᴇ ʀᴇᴠᴇɴɢᴇ — ɪ ᴅᴇʟᴇᴛᴇ ᴘᴇᴏᴘʟᴇ.</i>",
            parse_mode=ParseMode.HTML
        )

    if len(args) == 1:
        enabled = await is_vclogger_enabled(chat_id)
        state = (
            "<tg-emoji emoji-id='5039928501612839813'>🟢</tg-emoji> <b>ᴇɴᴀʙʟᴇᴅ</b>"
            if enabled else
            "<tg-emoji emoji-id='6195245116207143870'>🔒</tg-emoji> <b>ᴅɪsᴀʙʟᴇᴅ</b>"
        )
        return await message.reply(
            "<tg-emoji emoji-id='5321505140199418151'>🎥</tg-emoji> <b>ᴠᴄ ʟᴏɢɢᴇʀ sᴛᴀᴛᴜs</b>\n\n"
            f"<tg-emoji emoji-id='5258236805890710909'>⬅️</tg-emoji> <b>ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴇ :</b> {state}\n\n"
            "<tg-emoji emoji-id='5334544901428229844'>ℹ️</tg-emoji> <b>ᴜsᴀɢᴇ :</b> /vclogger [on / off]",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    arg = args[1].lower()

    if arg in ("on", "enable", "yes"):
        if chat_id in active_vc_chats:
            return await message.reply(
                "<tg-emoji emoji-id='5334544901428229844'>ℹ️</tg-emoji> <b>ᴠᴄ ʟᴏɢɢᴇʀ</b> ɪs ᴀʟʀᴇᴀᴅʏ <b>ᴀᴄᴛɪᴠᴇ</b> ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.",
                parse_mode=ParseMode.HTML
            )
        await set_vclogger_status(chat_id, True)
        active_vc_chats.add(chat_id)
        asyncio.create_task(monitor_vc_chat(chat_id))
        await message.reply(
            "<tg-emoji emoji-id='5039928501612839813'>🟢</tg-emoji> <b>ᴠᴄ ʟᴏɢɢᴇʀ ᴇɴᴀʙʟᴇᴅ!</b>\n\n"
            "<tg-emoji emoji-id='5321505140199418151'>🎥</tg-emoji> ɴᴏᴡ ᴍᴏɴɪᴛᴏʀɪɴɢ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴀᴄᴛɪᴠɪᴛʏ.",
            parse_mode=ParseMode.HTML
        )

    elif arg in ("off", "disable", "no"):
        await set_vclogger_status(chat_id, False)
        active_vc_chats.discard(chat_id)
        vc_active_users.pop(chat_id, None)
        await message.reply(
            "<tg-emoji emoji-id='6195245116207143870'>🔒</tg-emoji> <b>ᴠᴄ ʟᴏɢɢᴇʀ ᴅɪsᴀʙʟᴇᴅ!</b>\n\n"
            "<tg-emoji emoji-id='5388632425314140043'>🔈</tg-emoji> ᴠᴄ ᴍᴏɴɪᴛᴏʀɪɴɢ ʜᴀs ʙᴇᴇɴ <b>sᴛᴏᴘᴘᴇᴅ</b>.",
            parse_mode=ParseMode.HTML
        )

    else:
        await message.reply(
            "<tg-emoji emoji-id='5990276318925691338'>⚡️</tg-emoji> <b>ɪɴᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛ!</b>\n\n"
            "<tg-emoji emoji-id='5334544901428229844'>ℹ️</tg-emoji> <b>ᴜsᴀɢᴇ :</b> /vclogger [on / off]",
            parse_mode=ParseMode.HTML
        )


@app.on_message(
    filters.command(["vcstats", "vcstatus"], prefixes=[".", "!", "/", "@", "?", "'"]) & filters.group
)
async def vcstats_command(_, message: Message):
    chat_id = message.chat.id
    enabled = await is_vclogger_enabled(chat_id)
    running = chat_id in active_vc_chats
    count   = len(vc_active_users.get(chat_id, set()))

    logger_state = (
        "<tg-emoji emoji-id='5039928501612839813'>🟢</tg-emoji> <b>ᴇɴᴀʙʟᴇᴅ</b>"
        if enabled else
        "<tg-emoji emoji-id='6195245116207143870'>🔒</tg-emoji> <b>ᴅɪsᴀʙʟᴇᴅ</b>"
    )
    monitor_state = (
        "<tg-emoji emoji-id='5039928501612839813'>🟢</tg-emoji> <b>ʀᴜɴɴɪɴɢ</b>"
        if running else
        "<tg-emoji emoji-id='5388632425314140043'>🔈</tg-emoji> <b>sᴛᴏᴘᴘᴇᴅ</b>"
    )

    await message.reply(
        "<tg-emoji emoji-id='5321505140199418151'>🎥</tg-emoji> <b>ᴠᴄ ʟᴏɢɢᴇʀ sᴛᴀᴛs</b>\n\n"
        f"<tg-emoji emoji-id='5258236805890710909'>⬅️</tg-emoji> <b>ʟᴏɢɢᴇʀ  :</b> {logger_state}\n"
        f"<tg-emoji emoji-id='5258236805890710909'>⬅️</tg-emoji> <b>ᴍᴏɴɪᴛᴏʀ :</b> {monitor_state}\n"
        f"<tg-emoji emoji-id='5316992572680320646'>👤</tg-emoji> <b>ᴜsᴇʀs ɪɴ ᴠᴄ :</b> {count}",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )


async def monitor_vc_chat(chat_id: int) -> None:
    userbot = await get_assistant(chat_id)
    if not userbot:
        LOGGER.warning(f"No assistant for chat {chat_id}, monitor aborted.")
        active_vc_chats.discard(chat_id)
        return

    LOGGER.info(f"VC monitor started → chat {chat_id}")

    error_count = 0
    MAX_ERRORS  = 3

    try:
        while chat_id in active_vc_chats:
            try:
                peer      = await userbot.resolve_peer(chat_id)
                full_chat = await userbot.invoke(
                    functions.channels.GetFullChannel(channel=peer)
                )

                if not getattr(full_chat.full_chat, "call", None):
                    error_count = 0
                    await asyncio.sleep(5)
                    continue

                result = await userbot.invoke(
                    functions.phone.GetGroupParticipants(
                        call=full_chat.full_chat.call,
                        ids=[],
                        sources=[],
                        offset="",
                        limit=100
                    )
                )

                new_users = {
                    p.peer.user_id
                    for p in result.participants
                    if hasattr(p, "peer") and hasattr(p.peer, "user_id")
                }

                old_users = vc_active_users.get(chat_id, set())

                for uid in new_users - old_users:
                    await _send_vc_log(chat_id, uid, userbot, joined=True, total=len(new_users))

                for uid in old_users - new_users:
                    await _send_vc_log(chat_id, uid, userbot, joined=False, total=len(new_users))

                vc_active_users[chat_id] = new_users
                error_count = 0

            except MessageNotModified:
                pass

            except Exception as e:
                error_str = str(e)

                if "CHANNEL_INVALID" in error_str:
                    LOGGER.warning(f"Chat {chat_id} is invalid, removing from VC logger.")
                    await remove_vclogger_chat(chat_id)
                    return

                error_count += 1
                LOGGER.error(f"Monitor error (chat {chat_id}) [{error_count}/{MAX_ERRORS}]: {e}")

                if error_count >= MAX_ERRORS:
                    LOGGER.warning(f"Too many errors for chat {chat_id}, stopping monitor.")
                    await remove_vclogger_chat(chat_id)
                    return

            await asyncio.sleep(5)

    finally:
        active_vc_chats.discard(chat_id)
        vc_active_users.pop(chat_id, None)
        LOGGER.info(f"VC monitor stopped → chat {chat_id}")


async def _send_vc_log(
    chat_id: int,
    user_id: int,
    userbot,
    *,
    joined: bool,
    total: int
) -> None:
    try:
        user     = await userbot.get_users(user_id)
        name     = user.first_name or "Unknown"
        username = f"@{user.username}" if user.username else "ɴᴏ ᴜsᴇʀɴᴀᴍᴇ"

        if joined:
            icon = "<tg-emoji emoji-id='5039928501612839813'>🟢</tg-emoji>"
            tag  = "<b>ᴊᴏɪɴᴇᴅ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</b> #JoinVideoChat"
        else:
            icon = "<tg-emoji emoji-id='6195245116207143870'>🔒</tg-emoji>"
            tag  = "<b>ʟᴇꜰᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</b> #LeftVideoChat"

        text = (
            f"{icon} {tag}\n\n"
            f"<tg-emoji emoji-id='5316992572680320646'>👤</tg-emoji> <b>ɴᴀᴍᴇ →</b> {name}\n"
            f"<tg-emoji emoji-id='5334544901428229844'>ℹ️</tg-emoji> <b>ɪᴅ →</b> <code>{user_id}</code>\n"
            f"<tg-emoji emoji-id='5443038326535759644'>💬</tg-emoji> <b>ᴜsᴇʀɴᴀᴍᴇ →</b> {username}\n"
            f"<tg-emoji emoji-id='5316992572680320646'>👤</tg-emoji> <b>ᴛᴏᴛᴀʟ ᴠᴄ ᴍᴇᴍʙᴇʀs →</b> {total}"
        )

        sent = await app.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(3)
        await sent.delete()

    except Exception as e:
        LOGGER.warning(f"_send_vc_log failed (user {user_id}, chat {chat_id}): {e}")


# ── Backward-compat aliases ───────────────────────────────────────────────────
enabled_chats = active_vc_chats
is_vc_logger  = is_vclogger_enabled

async def send_join_notification(chat_id: int, user_id: int) -> None:
    try:
        userbot = await get_assistant(chat_id)
        if userbot:
            total = len(vc_active_users.get(chat_id, set()))
            await _send_vc_log(chat_id, user_id, userbot, joined=True, total=total)
    except Exception as e:
        LOGGER.warning(f"send_join_notification failed: {e}")