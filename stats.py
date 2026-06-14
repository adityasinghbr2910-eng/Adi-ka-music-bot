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


import platform
from sys import version as pyver
import psutil
from pyrogram import __version__ as pyrover
from pyrogram import filters
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls.__version__ import __version__ as pytgver
import config
from KanhaMusic import app
from KanhaMusic.core.userbot import assistants
from KanhaMusic.misc import SUDOERS, mongodb
from KanhaMusic.plugins import ALL_MODULES
from KanhaMusic.utils.database import get_served_chats, get_served_users, get_sudoers
from KanhaMusic.utils.decorators.language import language, languageCB
from KanhaMusic.utils.inline.stats import back_stats_buttons, stats_buttons
from config import BANNED_USERS


@app.on_message(filters.command(["stats", "gstats"]) & filters.group & ~BANNED_USERS)
@language
async def gstats_global(client, message: Message, _):
    mystic = await message.reply_text(_["gstats_1"])
    stats = stats_buttons(_, True if message.from_user.id in SUDOERS else False)
    await mystic.edit_text(_["gstats_2"].format(app.mention), reply_markup=stats)


@app.on_callback_query(filters.regex("GetStatsNow") & ~BANNED_USERS)
@languageCB
async def stats_Load(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    mystic = await CallbackQuery.message.edit_text(_["gstats_3"])
    try:
        total_memory = psutil.virtual_memory().total >> 20
        used_memory = psutil.virtual_memory().used >> 20
        ram = f"{used_memory} ᴍʙ / {total_memory} ᴍʙ"
    except:
        ram = "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ"
    try:
        p_core = psutil.cpu_count(logical=False)
        t_core = psutil.cpu_count(logical=True)
        if p_core is None:
            p_core = "ɴ/ᴀ"
        if t_core is None:
            t_core = "ɴ/ᴀ"
    except:
        p_core = "ɴ/ᴀ"
        t_core = "ɴ/ᴀ"
    try:
        cpu_freq = psutil.cpu_freq().current
        if cpu_freq >= 1000:
            cpu_freq = f"{round(cpu_freq / 1000, 2)}ɢʜᴢ"
        else:
            cpu_freq = f"{round(cpu_freq, 2)}ᴍʜᴢ"
    except:
        cpu_freq = "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ"
    hdd = psutil.disk_usage("/")
    total = hdd.total / (1024.0**3)
    used = hdd.used / (1024.0**3)
    free = hdd.free / (1024.0**3)
    call = await mongodb.command("dbstats")
    datasize = call["dataSize"] / 1024
    storage = call["storageSize"] / 1024
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    text = _["gstats_5"].format(
        app.mention,
        len(ALL_MODULES),
        platform.system(),
        ram,
        p_core,
        t_core,
        cpu_freq,
        pyver.split()[0],
        pyrover,
        pytgver,
        str(total)[:4],
        str(used)[:4],
        str(free)[:4],
        served_chats,
        served_users,
        str(datasize)[:4],
        str(storage)[:4],
    )
    med = InputMediaPhoto(media=config.STATS_IMG, caption=text)
    try:
        await CallbackQuery.message.edit_message_media(
            media=med, reply_markup=back_stats_buttons(_)
        )
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(
            photo=config.STATS_IMG, caption=text, reply_markup=back_stats_buttons(_)
        )


@app.on_callback_query(filters.regex("TopOverall") & ~BANNED_USERS)
@languageCB
async def stats_overall(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    mystic = await CallbackQuery.message.edit_text(_["gstats_3"])
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    text = _["gstats_4"].format(app.mention, served_chats, served_users)
    med = InputMediaPhoto(media=config.STATS_IMG, caption=text)
    try:
        await CallbackQuery.message.edit_message_media(
            media=med, reply_markup=back_stats_buttons(_)
        )
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(
            photo=config.STATS_IMG, caption=text, reply_markup=back_stats_buttons(_)
        )


@app.on_callback_query(filters.regex("MainStats") & ~BANNED_USERS)
@languageCB
async def main_stats(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    stats = stats_buttons(_, True if CallbackQuery.from_user.id in SUDOERS else False)
    text = _["gstats_2"].format(app.mention)
    med = InputMediaPhoto(media=config.STATS_IMG, caption=text)
    try:
        await CallbackQuery.message.edit_message_media(media=med, reply_markup=stats)
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(
            photo=config.STATS_IMG, caption=text, reply_markup=stats
  )
  
