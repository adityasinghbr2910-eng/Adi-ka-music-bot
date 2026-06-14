import os
import zipfile
import subprocess
import shutil
import time
from pyrogram import filters
from KanhaMusic import app
from github import Github
from config import OWNER_ID  

TEMP_DIR = "temp_repos"
os.makedirs(TEMP_DIR, exist_ok=True)

TEMP_CONFIG = {}

def run(cmd, cwd):
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc.stdout

def safe_rm(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass

def config_valid():
    if not TEMP_CONFIG:
        return False
    if time.time() - TEMP_CONFIG.get("timestamp", 0) > 300:
        TEMP_CONFIG.clear()
        return False
    return True


@app.on_message(filters.command("gitconfig") & filters.user(OWNER_ID))
async def gitconfig(client, message):
    if len(message.command) < 4:
        return await message.reply(
            "**» ᴜsᴀɢᴇ :-** `/gitconfig username email token`"
        )
    name = message.command[1]
    email = message.command[2]
    token = message.command[3]

    TEMP_CONFIG.update({
        "name": name,
        "email": email,
        "token": token,
        "timestamp": time.time()
    })
    await message.reply("**» ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ sᴀᴠᴇᴅ ғᴏʀ 5 ᴍɪɴᴜᴛᴇs !**\n\n**ɴᴏᴡ sᴇɴᴅ ᴢɪᴘ ғɪʟᴇ ᴡɪᴛʜ ᴄᴀᴘᴛɪᴏɴ** `/uploadrepo repo_name` \n**ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴢɪᴘ ғɪʟᴇ ᴡɪᴛʜ** `/uploadrepo repo_name` .")


@app.on_message(filters.command("uploadrepo") & filters.user(OWNER_ID))
async def uploadrepo(client, message):
    if not config_valid():
        return await message.reply("**» ᴘʟᴇᴀsᴇ sᴇᴛ ᴄᴏɴғɪɢ ғɪʀsᴛ ᴜsɪɴɢ** `/gitconfig` !")

    if len(message.command) < 2:
        return await message.reply("**» ᴜsᴀɢᴇ :-** `/uploadrepo repo_name` (Reply to zip file or send with caption)")

    repo_name = message.command[1]
    reply = message.reply_to_message
    doc = None

    if reply and reply.document and reply.document.file_name.endswith(".zip"):
        doc = reply.document
    elif message.document and message.document.file_name.endswith(".zip"):
        doc = message.document

    if not doc:
        return await message.reply("**» ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴠᴀʟɪᴅ `.zip` ғɪʟᴇ ᴏʀ sᴇɴᴅ ᴡɪᴛʜ ᴄᴀᴘᴛɪᴏɴ.**")

    status = await message.reply("**📥 ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴢɪᴘ ғɪʟᴇ...**")
    session_id = str(int(time.time()))
    zip_path = os.path.join(TEMP_DIR, f"{session_id}.zip")
    extract_root = os.path.join(TEMP_DIR, f"ext_{session_id}")
    final_path = os.path.join(TEMP_DIR, f"repo_{session_id}")

    try:
        await client.download_media(doc, file_name=zip_path)
        await status.edit("**📦 ᴇxᴛʀᴀᴄᴛɪɴɢ ᴢɪᴘ ғɪʟᴇ...**")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_root)

        items = os.listdir(extract_root)
        if len(items) == 1 and os.path.isdir(os.path.join(extract_root, items[0])):
            shutil.move(os.path.join(extract_root, items[0]), final_path)
            shutil.rmtree(extract_root, ignore_errors=True)
        else:
            os.rename(extract_root, final_path)

        await status.edit("**🚀 ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ɢɪᴛʜᴜʙ...**")
        GITHUB_TOKEN = TEMP_CONFIG["token"]
        GITHUB_NAME = TEMP_CONFIG["name"]
        GITHUB_EMAIL = TEMP_CONFIG["email"]

        g = Github(GITHUB_TOKEN)
        g_user = g.get_user()

        try:
            repo = g_user.get_repo(repo_name)
            await status.edit(f"**📂 ʀᴇᴘᴏsɪᴛᴏʀʏ `{repo_name}` ғᴏᴜɴᴅ. ᴜᴘʟᴏᴀᴅɪɴɢ...**")
        except Exception:
            await status.edit(f"**➕ ᴄʀᴇᴀᴛɪɴɢ ɴᴇᴡ ᴘʀɪᴠᴀᴛᴇ ʀᴇᴘᴏsɪᴛᴏʀʏ `{repo_name}`...**")
            repo = g_user.create_repo(repo_name, private=True)

        branch_name = "main"
        await status.edit("**📤 ᴘᴜsʜɪɴɢ ᴄᴏᴍᴍɪᴛs ᴛᴏ ɢɪᴛʜᴜʙ...**")

        # Create a hidden dummy file to enforce unique styling or trace credits if needed
        hidden_dir = os.path.join(final_path, ".kanha")
        os.makedirs(hidden_dir, exist_ok=True)
        with open(os.path.join(hidden_dir, "credit.txt"), "w", encoding="utf-8") as f:
            f.write("⚡ sᴏᴜʀᴄʜ ᴄᴏᴅᴇ ᴜᴘʟᴏᴀᴅ ʙʏ :- 𝗞𝗔𝗡𝗛𝗔 🌺")


        run(["git", "init"], cwd=final_path)
        run(["git", "config", "user.email", GITHUB_EMAIL], cwd=final_path)
        run(["git", "config", "user.name", GITHUB_NAME], cwd=final_path)
        remote_url = repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")
        run(["git", "remote", "add", "origin", remote_url], cwd=final_path)
        run(["git", "add", "."], cwd=final_path)

        status_out = subprocess.run(["git", "status", "--porcelain"], cwd=final_path, text=True, capture_output=True)
        if status_out.stdout.strip():
            run(["git", "commit", "-m", "ᴋᴀɴʜᴀ ʙᴏᴛs !!"], cwd=final_path)
        else:
            run(["git", "commit", "--allow-empty", "-m", "📂 𝐊𝐀𝐍𝐇𝐀 !! "], cwd=final_path)

        run(["git", "branch", "-M", branch_name], cwd=final_path)
        run(["git", "push", "-u", "origin", branch_name], cwd=final_path)

        await status.edit(f"**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘʟᴏᴀᴅᴇᴅ !**\n\n**🔗 ʀᴇᴘᴏ ʟɪɴᴋ :-** {repo.html_url}")

    except Exception as e:
        await message.reply(f"**❌ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ:**\n`{str(e)}`")
    finally:
        safe_rm(zip_path)
        safe_rm(extract_root)
        safe_rm(final_path)
  
