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


import asyncio
from datetime import datetime
from pyrogram.enums import ChatType
import config
from KanhaMusic import app
from KanhaMusic.core.call import Anu, autoend
from KanhaMusic.utils.database import get_client, is_active_chat, is_autoend


async def auto_leave():
    if config.AUTO_LEAVING_ASSISTANT:
        while not await asyncio.sleep(900):
            from KanhaMusic.core.userbot import assistants

            for num in assistants:
                client = await get_client(num)
                left = 0
                try:
                    async for i in client.get_dialogs():
                        if i.chat.type in [
                            ChatType.SUPERGROUP,
                            ChatType.GROUP,
                            ChatType.CHANNEL,
                        ]:
                            if (
                                i.chat.id != config.LOGGER_ID
                                and i.chat.id != -1001686672798
                                and i.chat.id != -1001549206010
                            ):
                                if left == 20:
                                    continue
                                if not await is_active_chat(i.chat.id):
                                    try:
                                        await client.leave_chat(i.chat.id)
                                        left += 1
                                    except:
                                        continue
                except:
                    pass


asyncio.create_task(auto_leave())


async def auto_end():
    while not await asyncio.sleep(5):
        if not autoend:
            continue
        # List copy — iteration ke beech dict change na ho
        for chat_id in list(autoend.keys()):
            timer = autoend.get(chat_id)
            # None = cancelled (koi wapis join ho gaya)
            if not timer:
                continue
            if datetime.now() > timer:
                if not await is_active_chat(chat_id):
                    autoend.pop(chat_id, None)
                    continue
                autoend.pop(chat_id, None)
                try:
                    await Anu.stop_stream(chat_id)
                except Exception:
                    pass
                try:
                    msg = "⏹ **ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴇɴᴅᴇᴅ**\n\nɴᴏ ᴏɴᴇ ᴡᴀs ʟɪsᴛᴇɴɪɴɢ ɪɴ ᴛʜᴇ ᴠᴄ, sᴏ ᴛʜᴇ sᴏɴɢ ᴡᴀs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ sᴛᴏᴩᴩᴇᴅ."
                    await app.send_message(chat_id, msg)
                except Exception:
                    pass


asyncio.create_task(auto_end())
