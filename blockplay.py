"""
blockplay.py — Owner Commands Plugin (MongoDB)
════════════════════════════════════════════════════════════════════
Commands (Bot PM mein):
  /blockplayword <word>       → word globally block karo (sab GC)
  /unblockplayword <word>     → word unblock karo
  /blockplaywords             → blocked words + users ki list
  /blockplayuser <user_id>    → user ko play se ban karo
  /unblockplayuser <user_id>  → user unban karo

Jab koi blocked word play kare:
  → Owner ko PM alert (clickable user + group link)
  → Us GC ke saare admins ko bhi tag karo same message mein
════════════════════════════════════════════════════════════════════
"""

import html
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import filters
from pyrogram.types import Message

import config
from KanhaMusic import app

# ── MongoDB Setup ─────────────────────────────────────────────────────────────
_mongo_client = AsyncIOMotorClient(config.MONGO_DB_URI)
_db = _mongo_client["KanhaMusic"]
_col = _db["blocked_play"]

# In-memory cache
_cache = {"blocked_words": None, "blocked_users": None}


# ── Core DB Helpers ───────────────────────────────────────────────────────────

async def _get_list(doc_id: str) -> list:
    if _cache[doc_id] is not None:
        return _cache[doc_id]
    doc = await _col.find_one({"_id": doc_id})
    result = doc["list"] if doc else []
    _cache[doc_id] = result
    return result


async def _set_list(doc_id: str, lst: list):
    await _col.update_one({"_id": doc_id}, {"$set": {"list": lst}}, upsert=True)
    _cache[doc_id] = lst


# ── Public helpers ────────────────────────────────────────────────────────────

async def get_blocked_words() -> list:
    return await _get_list("blocked_words")


async def get_blocked_users() -> list:
    return [int(u) for u in await _get_list("blocked_users")]


async def is_user_play_blocked(user_id: int) -> bool:
    return user_id in await get_blocked_users()


# ── Owner check ───────────────────────────────────────────────────────────────

def _is_owner(user_id: int) -> bool:
    owner = config.OWNER_ID
    if isinstance(owner, int):
        return user_id == owner
    return user_id in owner


# ── Notify: Owner PM + GC Admins Tag ─────────────────────────────────────────

async def notify_blocked_play(chat_id: int, user_id: int, user_mention: str,
                               query: str, matched_word: str):
    """
    Blocked word play hone par:
    1. Owner ko PM mein detailed alert
    2. Us GC mein admins ko tag karo
    """
    safe_query   = html.escape(str(query)[:300])
    safe_word    = html.escape(str(matched_word))
    # user_mention is Pyrogram HTML mention - use directly
    safe_mention = str(user_mention)

    # Group info
    try:
        chat_info = await app.get_chat(chat_id)
        chat_title = html.escape(chat_info.title or str(chat_id))
        if getattr(chat_info, "username", None):
            g_link = f"https://t.me/{chat_info.username}"
            group_part = f'<a href="{g_link}">{chat_title}</a> (<code>{chat_id}</code>)'
        else:
            try:
                inv = await app.export_chat_invite_link(chat_id)
                group_part = f'<a href="{inv}">{chat_title}</a> (<code>{chat_id}</code>)'
            except Exception:
                group_part = f"{chat_title} (<code>{chat_id}</code>)"
    except Exception:
        chat_title = str(chat_id)
        group_part = f"<code>{chat_id}</code>"

    alert_text = (
        f"🚨 <b>Blocked Play Word — Alert!</b>\n\n"
        f"👤 <b>User:</b> "
        f'<a href="tg://user?id={user_id}">{safe_mention}</a> '
        f"(ID: <code>{user_id}</code>)\n"
        f"💬 <b>Group:</b> {group_part}\n"
        f"🚫 <b>Blocked Word:</b> <code>{safe_word}</code>\n"
        f"🎵 <b>Query:</b> <code>{safe_query}</code>\n\n"
        f"⚠️ <i>Content blocked. User notified.</i>"
    )

    # 1. Owner ko PM
    try:
        owner_ids = config.OWNER_ID
        if isinstance(owner_ids, int):
            owner_ids = [owner_ids]
        for oid in owner_ids:
            await app.send_message(chat_id=oid, text=alert_text)
    except Exception:
        pass

    # 2. GC ke admins fetch karo aur tag karo
    try:
        admin_mentions = []
        async for member in app.get_chat_members(
            chat_id, filter="administrators"
        ):
            # Bot ko skip karo
            if member.user.is_bot:
                continue
            admin_mentions.append(
                f'<a href="tg://user?id={member.user.id}">'
                f'{html.escape(member.user.first_name)}</a>'
            )

        if admin_mentions:
            tag_line = " ".join(admin_mentions)
            gc_msg = (
                f"🚨 <b>Blocked Content Attempt!</b>\n\n"
                f"👤 <b>User:</b> "
                f'<a href="tg://user?id={user_id}">{safe_mention}</a>\n'
                f"🚫 <b>Blocked Word:</b> <code>{safe_word}</code>\n"
                f"🎵 <b>Query:</b> <code>{safe_query}</code>\n\n"
                f"📢 <b>Admins:</b> {tag_line}"
            )
            await app.send_message(chat_id=chat_id, text=gc_msg)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# /blockplayword <word>
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(
    filters.command(["blockplayword", "blockplay"], prefixes=["/", "!", "."]) & filters.private
)
async def cmd_blockplayword(client, message: Message):
    if not _is_owner(message.from_user.id):
        return await message.reply_text("❌ <b>Sirf Owner yeh command use kar sakta hai.</b>")

    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ <b>Usage:</b> <code>/blockplayword &lt;word or phrase&gt;</code>\n\n"
            "Example: <code>/blockplayword bad song name</code>\n\n"
            "<b>Note:</b> Yeh word globally block hoga — sab groups mein.\n"
            "Koi bhi play kare to Owner + GC Admins ko alert jayega."
        )

    word = message.text.split(None, 1)[1].strip().lower()

    if len(word) < 2:
        return await message.reply_text("❌ Word bahut chota hai. Min 2 characters.")
    if len(word) > 100:
        return await message.reply_text("❌ Word bahut lamba hai. Max 100 characters.")

    words = await get_blocked_words()
    if word in words:
        return await message.reply_text(
            f"⚠️ <code>{html.escape(word)}</code> pehle se block list mein hai."
        )

    words.append(word)
    await _set_list("blocked_words", words)

    await message.reply_text(
        f"✅ <b>Word Block Ho Gaya!</b>\n\n"
        f"🚫 <b>Word:</b> <code>{html.escape(word)}</code>\n"
        f"📊 <b>Total Blocked:</b> {len(words)}\n"
        f"💾 MongoDB mein save.\n\n"
        f"<i>Koi bhi play kare to Owner + GC Admins ko alert jayega.</i>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /unblockplayword <word>
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(
    filters.command(["unblockplayword", "unblockplay"], prefixes=["/", "!", "."]) & filters.private
)
async def cmd_unblockplayword(client, message: Message):
    if not _is_owner(message.from_user.id):
        return await message.reply_text("❌ <b>Sirf Owner yeh command use kar sakta hai.</b>")

    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ <b>Usage:</b> <code>/unblockplayword &lt;word&gt;</code>"
        )

    word = message.text.split(None, 1)[1].strip().lower()
    words = await get_blocked_words()

    if word not in words:
        return await message.reply_text(
            f"⚠️ <code>{html.escape(word)}</code> block list mein nahi hai."
        )

    words.remove(word)
    await _set_list("blocked_words", words)

    await message.reply_text(
        f"✅ <code>{html.escape(word)}</code> unblock ho gaya!\n"
        f"📊 Remaining: {len(words)} blocked words."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /blockplaywords — list
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(
    filters.command(["blockplaywords", "blockplaylist"], prefixes=["/", "!", "."]) & filters.private
)
async def cmd_blockplaywords(client, message: Message):
    if not _is_owner(message.from_user.id):
        return await message.reply_text("❌ <b>Sirf Owner yeh command use kar sakta hai.</b>")

    words = await get_blocked_words()
    users = await get_blocked_users()

    text = "📋 <b>Blocked Play List</b>\n\n"

    if words:
        text += f"🚫 <b>Blocked Words ({len(words)}):</b>\n"
        for i, w in enumerate(words, 1):
            text += f"  {i}. <code>{html.escape(w)}</code>\n"
    else:
        text += "🚫 <b>Blocked Words:</b> <i>Koi nahi</i>\n"

    text += "\n"

    if users:
        text += f"👤 <b>Blocked Users ({len(users)}):</b>\n"
        for i, u in enumerate(users, 1):
            text += f"  {i}. <code>{u}</code>\n"
    else:
        text += "👤 <b>Blocked Users:</b> <i>Koi nahi</i>\n"

    text += (
        "\n\n<b>Commands:</b>\n"
        "<code>/blockplayword &lt;word&gt;</code>\n"
        "<code>/unblockplayword &lt;word&gt;</code>\n"
        "<code>/blockplayuser &lt;id&gt;</code>\n"
        "<code>/unblockplayuser &lt;id&gt;</code>"
    )
    await message.reply_text(text)


# ═══════════════════════════════════════════════════════════════════════════════
# /blockplayuser <user_id>
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(
    filters.command(["blockplayuser"], prefixes=["/", "!", "."]) & filters.private
)
async def cmd_blockplayuser(client, message: Message):
    if not _is_owner(message.from_user.id):
        return await message.reply_text("❌ <b>Sirf Owner yeh command use kar sakta hai.</b>")

    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ <b>Usage:</b> <code>/blockplayuser &lt;user_id&gt;</code>"
        )

    try:
        uid = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ User ID sirf number hona chahiye.")

    users = await get_blocked_users()
    if uid in users:
        return await message.reply_text(f"⚠️ User <code>{uid}</code> pehle se blocked hai.")

    users.append(uid)
    await _set_list("blocked_users", [str(u) for u in users])

    try:
        user_obj = await app.get_users(uid)
        user_info = f"{html.escape(user_obj.first_name)} (@{user_obj.username or 'N/A'})"
    except Exception:
        user_info = str(uid)

    await message.reply_text(
        f"✅ <b>User Block Ho Gaya!</b>\n\n"
        f"👤 {user_info}\n"
        f"🆔 <code>{uid}</code>\n"
        f"<i>Yeh user ab play nahi kar sakta.</i>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /unblockplayuser <user_id>
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(
    filters.command(["unblockplayuser"], prefixes=["/", "!", "."]) & filters.private
)
async def cmd_unblockplayuser(client, message: Message):
    if not _is_owner(message.from_user.id):
        return await message.reply_text("❌ <b>Sirf Owner yeh command use kar sakta hai.</b>")

    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ <b>Usage:</b> <code>/unblockplayuser &lt;user_id&gt;</code>"
        )

    try:
        uid = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ User ID sirf number hona chahiye.")

    users = await get_blocked_users()
    if uid not in users:
        return await message.reply_text(f"⚠️ User <code>{uid}</code> blocked nahi hai.")

    users.remove(uid)
    await _set_list("blocked_users", [str(u) for u in users])
    await message.reply_text(f"✅ User <code>{uid}</code> unblock ho gaya!")