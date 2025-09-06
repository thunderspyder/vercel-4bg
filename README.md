# Telegram Leech Bot (4 GB via Userbot) — Railway/Render Ready

    A small Python bot that downloads a direct-link file and uploads it back to Telegram.
    - **4 GB uploads** use a **userbot** (your own Telegram account via Pyrogram session string).
    - A **bot token** is used to receive `/leech` commands. The upload is performed by the userbot when provided.
    - If no session string is provided, the bot will upload itself but is subject to Bot API limits.

    > ⚠️ **Vercel is not suitable** for leeching: serverless timeouts, no background/long-running tasks, and limited disk make large downloads impossible. Use Railway, Render, Fly.io, Replit, or a VPS.

    ## Features
    - `/leech <url>`: downloads file and uploads to current chat
    - Streams download to disk (no full buffering in RAM)
    - Auto-picks **userbot** for upload when available (up to 4 GB+ supported by Telegram clients)
    - Size check + progress updates

    ## Quick Start (Local)
    1. Python 3.10+
    2. `cp .env.example .env` and fill values.
    3. `pip install -r requirements.txt`
    4. Generate a Pyrogram session string (only needed for 4GB uploads):
       ```bash
       python tools/gen_session.py
       ```
       Paste the output into `SESSION_STRING` in `.env`.
    5. Run: `python app.py`

    ## Deploy (Railway)
    1. Create a new service from this repo.
    2. Add environment variables (see below).
    3. Set Start Command: `python app.py`
    4. Ensure your plan has enough disk (>= 6–8 GB recommended for big files).

    ## Environment Variables
    | Key | Required | Description |
    |-----|----------|-------------|
    | `BOT_TOKEN` | yes | Telegram Bot API token from @BotFather |
    | `API_ID` | yes | Telegram API ID from https://my.telegram.org |
    | `API_HASH` | yes | Telegram API hash from https://my.telegram.org |
    | `SESSION_STRING` | no* | Pyrogram user session (needed for 4 GB uploads) |
    | `ALLOWED_CHATS` | no | Comma-separated chat IDs allowed to use the bot (empty = allow all) |
    | `MAX_SIZE_MB` | no | Max download size in MB (default 5120 = 5 GB) |
    | `DOWNLOAD_DIR` | no | Where to store temp files (default `/tmp/leech`) |


*Without `SESSION_STRING`, uploads use the bot and are subject to Bot API file size limits.


    ## Usage
    - In a chat with your bot: `/leech https://example.com/bigfile.iso`
    - The bot replies with progress, then the userbot (if configured) uploads the file back.

    ## Legal & Safety
    This tool is for personal/admin file logistics. **Do not use to infringe copyrights or site terms.**

    ## Notes
    - Telegram raised max file size to **4 GB** for regular clients (user accounts). Bot API upload limits are lower; therefore 4 GB requires the **userbot**.
    - Railway/Render timeout-less workers are fine; Vercel serverless is not.