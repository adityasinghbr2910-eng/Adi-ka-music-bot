# -----------------------------------------------
# 🔸 KanhaMusic Project
# 🔹 Developed & Maintained by: Anu Bots (https://github.com/TEAM-KANHA-OP)
# 📅 Copyright © 2025 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by TEAM-KANHA-OP
# -----------------------------------------------


import os
import re

from pykeyboard import InlineKeyboard
from pyrogram import enums, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaVideo,
    Message,
)

from config import BANNED_USERS, SONG_DOWNLOAD_DURATION, SONG_DOWNLOAD_DURATION_LIMIT
from KanhaMusic import YouTube, app
from KanhaMusic.utils.decorators.language import language, languageCB
from KanhaMusic.utils.formatters import convert_bytes
from KanhaMusic.utils.inline.song import song_markup


# ──────────────────────────────────────────────
# /song in group → redirect to PM
# ──────────────────────────────────────────────

@app.on_message(filters.command(["song"]) & filters.group & ~BANNED_USERS)
@language
async def song_command_group(client, message: Message, _):
    upl = InlineKeyboardMarkup(
        [[\n            InlineKeyboardButton(
                text=_["MUST_BE_ADMIN_BUTTON"],
                url=f"https://t.me/{app.username}?start=song",
            )\n        ]]
    )
    await message.reply_text(_["song_1"], reply_markup=upl)


# ──────────────────────────────────────────────
# /song in PM or via start command
# ──────────────────────────────────────────────

@app.on_message(filters.command(["song"]) & filters.private & ~BANNED_USERS)
@language
async def song_command_private(client, message: Message, _):
    await message.delete()
    url = "".join(message.text.split(None, 1)[1:])
    if not url:
        return await message.reply_text(_["song_2"])
    
    mystic = await message.reply_text(_["song_3"])
    try:
        title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(url)
    except Exception as e:
        print(f"[SONG] Details error: {e}")
        return await mystic.edit_text(_["song_4"])

    if duration_sec > SONG_DOWNLOAD_DURATION_LIMIT:
        return await mystic.edit_text(
            _["song_5"].format(SONG_DOWNLOAD_DURATION, duration_min)
        )

    reply_markup = song_markup(_, vidid)
    await mystic.delete()
    await message.reply_photo(
        thumbnail,
        caption=_["song_6"].format(title, duration_min),
        reply_markup=reply_markup,
    )


# ──────────────────────────────────────────────
# Callback Queries for Song Downloading
# ──────────────────────────────────────────────

@app.on_callback_query(filters.regex(r"song_(download|video)_format\|(.*?)") & ~BANNED_USERS)
@languageCB
async def song_download_formats(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    command, vidid = CallbackQuery.data.split("|")
    mystic = await CallbackQuery.message.edit_text(_["song_7"])
    
    try:
        formats, title = await YouTube.formats(vidid, format_type=command)
    except Exception as e:
        print(f"[SONG] Formats error: {e}")
        return await mystic.edit_text(_["song_4"])

    keyboard = InlineKeyboard(row_width=2)
    for fmt in formats:
        # Expected format: [quality, size, format_id]
        quality, size, format_id = fmt
        if command == "song_download":
            button_text = f"🎵 {quality} ({size})"
            callback_data = f"song_dl|audio|{format_id}|{vidid}"
        else:
            button_text = f"🎥 {quality} ({size})"
            callback_data = f"song_dl|video|{format_id}|{vidid}"
            
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        
    keyboard.row(InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close"))
    await mystic.edit_text(_["song_8"].format(title), reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"song_dl\|(.*?)") & ~BANNED_USERS)
@languageCB
async def song_download_perform(client, CallbackQuery, _):
    data = CallbackQuery.data.split("|")
    file_type = data[1]
    format_id = data[2]
    vidid = data[3]

    mystic = await CallbackQuery.message.edit_text(_["song_7"])
    yturl = f"https://www.youtube.com/watch?v={vidid}"

    file_path = None
    thumb_image_path = None

    try:
        # Get details again for safe metadata processing
        raw_title, duration_min, duration, thumb_url, _ = await YouTube.details(yturl)
        thumb_image_path = await YouTube.download(thumb_url, mystic, video=True)

        if file_type == "audio":
            file_path = await YouTube.download(
                yturl,
                mystic,
                songaudio=True,
                format_id=format_id,
                title=raw_title,
            )
            if not file_path:
                return await mystic.edit_text(_["song_10"])

            med = InputMediaAudio(
                media=file_path,
                thumb=thumb_image_path,
                caption=raw_title,
                title=raw_title,
                duration=duration,
            )
            await mystic.edit_text(_["song_11"])
            await app.send_chat_action(
                chat_id=CallbackQuery.message.chat.id,
                action=enums.ChatAction.UPLOAD_AUDIO,
            )
            try:
                await CallbackQuery.edit_message_media(media=med)
            except Exception as e:
                print(f"[SONG] send audio error: {e}")
                return await mystic.edit_text(_["song_10"])

        elif file_type == "video":
            width = CallbackQuery.message.photo.width
            height = CallbackQuery.message.photo.height

            file_path = await YouTube.download(
                yturl,
                mystic,
                songvideo=True,
                format_id=format_id,
                title=raw_title,
            )
            if not file_path:
                return await mystic.edit_text(_["song_10"])

            med = InputMediaVideo(
                media=file_path,
                duration=duration,
                width=width,
                height=height,
                thumb=thumb_image_path,
                caption=raw_title,
                supports_streaming=True,
            )

            await mystic.edit_text(_["song_11"])
            await app.send_chat_action(
                chat_id=CallbackQuery.message.chat.id,
                action=enums.ChatAction.UPLOAD_VIDEO,
            )
            try:
                await CallbackQuery.edit_message_media(media=med)
            except Exception as e:
                print(f"[SONG] send video error: {e}")
                return await mystic.edit_text(_["song_10"])

    except Exception as err:
        print(f"[SONG] download error: {err}")
        await mystic.edit_text(_["song_9"].format(err))

    finally:
        # Cleanup downloaded files
        for path in [file_path, thumb_image_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"[SONG] cleanup error: {e}")
      
