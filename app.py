import os
import asyncio
import aiohttp
import pathlib
import time
import humanize
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING", "").strip()
ALLOWED_CHATS = {int(x) for x in os.getenv("ALLOWED_CHATS", "").split(",") if x.strip().isdigit()}
MAX_SIZE_MB = int(os.getenv("MAX_SIZE_MB", "5120"))
DOWNLOAD_DIR = pathlib.Path(os.getenv("DOWNLOAD_DIR", "/tmp/leech"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

if not (BOT_TOKEN and API_ID and API_HASH):
    raise SystemExit("Missing BOT_TOKEN, API_ID or API_HASH in environment.")

# Bot client (receives commands)
bot = Client("leech-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Optional userbot for large uploads (4 GB support)
userbot = Client(name="leech-userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING) if SESSION_STRING else None

def allowed(chat_id: int) -> bool:
    return (not ALLOWED_CHATS) or (chat_id in ALLOWED_CHATS)

async def download_file(url: str, dest: pathlib.Path, edit_cb=None, max_size_bytes: int = None):
    chunk = 1 << 20  # 1 MB
    downloaded = 0
    last_edit = 0
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=1800)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length", "0"))
            if max_size_bytes and total and total > max_size_bytes:
                raise ValueError(f"File too large: {humanize.naturalsize(total)} > limit {humanize.naturalsize(max_size_bytes)}")
            with dest.open("wb") as f:
                async for part in resp.content.iter_chunked(chunk):
                    f.write(part)
                    downloaded += len(part)
                    if max_size_bytes and downloaded > max_size_bytes:
                        raise ValueError("Download exceeded configured size limit.")
                    now = time.time()
                    if edit_cb and (now - last_edit) > 2:
                        last_edit = now
                        await edit_cb(downloaded, total)
    return downloaded, total

@bot.on_message(filters.command("start"))
async def start(_, m: Message):
    if not allowed(m.chat.id):
        return await m.reply_text("Not authorized in this chat.")
    await m.reply_text("Send /leech <direct-file-url> to mirror a file.\n4 GB uploads require a configured userbot session.")

@bot.on_message(filters.command("leech"))
async def leech(_, m: Message):
    if not allowed(m.chat.id):
        return await m.reply_text("Not authorized in this chat.")
    if len(m.command) < 2:
        return await m.reply_text("Usage: /leech <direct-file-url>")
    url = m.command[1]
    status = await m.reply_text("Starting download…")
    tmp_path = DOWNLOAD_DIR / f"leech_{int(time.time())}"
    max_bytes = MAX_SIZE_MB * 1024 * 1024

    async def progress(downloaded, total):
        pct = (downloaded/total*100) if total else 0
        await status.edit_text(f"Downloading: {humanize.naturalsize(downloaded)} / {humanize.naturalsize(total) if total else '?'} ({pct:.1f}%)")

    try:
        downloaded, total = await download_file(url, tmp_path, edit_cb=progress, max_size_bytes=max_bytes)
    except Exception as e:
        await status.edit_text(f"Download failed: {e}")
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return

    await status.edit_text(f"Download complete: {humanize.naturalsize(downloaded)}. Preparing upload…")

    # Choose uploader
    uploader = userbot if userbot else bot

    # Determine filename
    filename = url.split("?")[0].rstrip("/").split("/")[-1] or "file.bin"
    file_path = tmp_path.rename(DOWNLOAD_DIR / filename)

    try:
        async with uploader:
            # Send via chosen client
            send_chat_id = m.chat.id
            caption = f"Leech: `{filename}` ({humanize.naturalsize(file_path.stat().st_size)})"
            # Use send_document for general files
            await uploader.send_document(
                chat_id=send_chat_id,
                document=str(file_path),
                caption=caption
            )
        await status.edit_text("Upload complete ✅")
    except Exception as e:
        await status.edit_text(f"Upload failed: {e}")
    finally:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    if userbot:
        # Warm up userbot session on start to speed up first upload
        loop.run_until_complete(userbot.start())
        loop.run_until_complete(userbot.stop())
    bot.run()