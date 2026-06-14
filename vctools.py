from pyrogram.enums import ButtonStyle

from pyrogram import Client, filters
from pyrogram.types import Message
from KanhaMusic import app
from config import OWNER_ID
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatType, ChatMemberStatus, ParseMode
from strings import get_string
from KanhaMusic.utils import AnuBin
from KanhaMusic.utils.database import get_assistant, get_lang
from KanhaMusic.core.call import Anu


async def is_admin(_, __, message):
    try:
        chat_member = await message.chat.get_member(message.from_user.id)
        return chat_member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except:
        return False


@app.on_message(filters.video_chat_started)
async def brah(_, msg):
    text = (
        "<tg-emoji emoji-id='5042328396193864923'>🛡</tg-emoji> <b>ᴠɪᴅᴇᴏ ᴄʜᴀᴛ sᴛᴀʀᴛᴇᴅ</b> <tg-emoji emoji-id='5042328396193864923'>🛡</tg-emoji>\n\n"
        "<tg-emoji emoji-id='5039928501612839813'>🟢</tg-emoji> ʟɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ɪs ɴᴏᴡ <b>ᴀᴄᴛɪᴠᴇ!</b>\n\n"
        "<tg-emoji emoji-id='6026256492619895014'>🎵</tg-emoji> ᴜsᴇ /play <b>﹤ sᴏɴɢ ɴᴀᴍᴇ ﹥</b> ᴛᴏ sᴛᴀʀᴛ ᴍᴜsɪᴄ\n"
        "<tg-emoji emoji-id='5424729550967807644'>🎧</tg-emoji> <i>ᴊᴏɪɴ ᴛʜᴇ ᴠᴄ ᴀɴᴅ ᴠɪʙᴇ ᴡɪᴛʜ ᴜs!</i>"
    )
    add_link = f"https://t.me/AnuuMusic_Bot?startgroup=true&admin=invite_users+delete_messages+manage_video_chats+pin_messages+manage_chat+ban_users+manage_topics+change_info"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="ᴊᴏɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ", url=add_link,icon_custom_emoji_id=5422699019279283099,
                style=ButtonStyle.SUCCESS,)]
    ])
    try:
        await msg.reply(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except Exception:
        pass


@app.on_message(filters.video_chat_ended)
async def brah2(_, msg: Message):
    text = (
        "<tg-emoji emoji-id='5197288647275071607'>🛡</tg-emoji> <b>ᴠɪᴅᴇᴏ ᴄʜᴀᴛ ᴇɴᴅᴇᴅ</b> <tg-emoji emoji-id='5197288647275071607'>🛡</tg-emoji>\n\n"
        "<tg-emoji emoji-id='5388632425314140043'>🔈</tg-emoji> ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ʜᴀs ʙᴇᴇɴ <b>ᴄʟᴏsᴇᴅ</b>\n"
        "<tg-emoji emoji-id='5332586662629227075'>🗂</tg-emoji> <b>ᴀʟʟ Qᴜᴇᴜᴇs ᴄʟᴇᴀʀᴇᴅ</b>\n\n"
        "<tg-emoji emoji-id='6026256492619895014'>🎵</tg-emoji> ᴛʜᴀɴᴋs ꜰᴏʀ ʟɪsᴛᴇɴɪɴɢ ᴡɪᴛʜ ᴜs\n"
        "<tg-emoji emoji-id='6089028758205897441'>❤️‍🔥</tg-emoji> <i>sᴛᴀʀᴛ ᴀ ɴᴇᴡ ᴠᴄ ᴀɴʏᴛɪᴍᴇ — ᴡᴇ'ʟʟ ʙᴇ ʙᴀᴄᴋ!</i>"
    )
    add_link = f"https://t.me/AnuuMusic_Bot?startgroup=true&admin=invite_users+delete_messages+manage_video_chats+pin_messages+manage_chat+ban_users+manage_topics+change_info"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=" ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url=add_link,icon_custom_emoji_id=5422699019279283099,
                style=ButtonStyle.SUCCESS,)]
    ])
    try:
        await msg.reply(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except Exception:
        pass


@app.on_message(filters.video_chat_members_invited)
async def brah3(app: app, message: Message):
    invited_users = ""
    for user in message.video_chat_members_invited.users:
        try:
            mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
            invited_users += (
                f"  <tg-emoji emoji-id='5316992572680320646'>👤</tg-emoji> {mention}\n"
            )
        except Exception:
            pass

    text = (
        "<tg-emoji emoji-id='5042328396193864923'>🛡</tg-emoji> <b>ᴠᴄ ɪɴᴠɪᴛᴀᴛɪᴏɴ</b>\n\n"
        f"<tg-emoji emoji-id='5359719332542718652'>💎</tg-emoji> <b>ɪɴᴠɪᴛᴇᴅ ʙʏ:</b> {message.from_user.mention}\n\n"
        f"<tg-emoji emoji-id='5321505140199418151'>🎥</tg-emoji> <b>ɪɴᴠɪᴛɪɴɢ ᴛᴏ ᴠᴄ:</b>\n"
        f"{invited_users}\n"
        "<tg-emoji emoji-id='6026256492619895014'>🎵</tg-emoji> ᴇɴᴊᴏʏ ᴛʜᴇ ᴍᴜsɪᴄ ᴛᴏɢᴇᴛʜᴇʀ\n"
        "<tg-emoji emoji-id='6089028758205897441'>❤️‍🔥</tg-emoji> <i>ʜᴀᴠᴇ ᴀ ɢʀᴇᴀᴛ ᴛɪᴍᴇ ɪɴ ᴛʜᴇ ᴄᴀʟʟ!</i>"
    )

    try:
        add_link = f"https://t.me/AnuuMusic_Bot?startgroup=true&admin=invite_users+delete_messages+manage_video_chats+pin_messages+manage_chat+ban_users+manage_topics+change_info"
        await message.reply(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="🎤 ᴊᴏɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ", url=add_link,icon_custom_emoji_id=5422699019279283099,
                style=ButtonStyle.SUCCESS,)],
        ]))
    except Exception as e:
        print(f"Error: {e}")


@app.on_message(
    filters.command(
        ["vcuser", "vcusers", "vcmember", "vcmembers", "cu", "cm"],
        prefixes=["/", "!", ".", "V", "v"]
    ) & filters.create(is_admin)
)
async def vc_members(client, message):
    try:
        language = await get_lang(message.chat.id)
        _ = get_string(language)
    except:
        _ = get_string("en")

    msg = await message.reply_text(_["V_C_1"])
    userbot = await get_assistant(message.chat.id)
    TEXT = ""

    try:
        async for m in userbot.get_call_members(message.chat.id):
            chat_id = m.chat.id
            username = m.chat.username
            is_hand_raised = m.is_hand_raised
            is_video_enabled = m.is_video_enabled
            is_left = m.is_left
            is_screen_sharing_enabled = m.is_screen_sharing_enabled
            is_muted = bool(m.is_muted and not m.can_self_unmute)
            is_speaking = not m.is_muted

            if m.chat.type != ChatType.PRIVATE:
                title = m.chat.title
            else:
                try:
                    title = (await client.get_users(chat_id)).mention
                except:
                    title = m.chat.first_name

            TEXT += _["V_C_2"].format(
                title,
                chat_id,
                username,
                is_video_enabled,
                is_screen_sharing_enabled,
                is_hand_raised,
                is_muted,
                is_speaking,
                is_left,
            )
            TEXT += "\n\n"

        if len(TEXT) < 4000:
            await msg.edit(TEXT or _["V_C_3"])
        else:
            link = await AnuBin(TEXT)
            await msg.edit(
                _["V_C_4"].format(link),
                disable_web_page_preview=True,
            )
    except ValueError:
        await msg.edit(_["V_C_5"])