import os
from pyrogram import Client
from dotenv import load_dotenv
load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")

if not (API_ID and API_HASH):
    raise SystemExit("Set API_ID and API_HASH in environment before running.")

with Client(name=":memory:", api_id=API_ID, api_hash=API_HASH) as app:
    print("SESSION_STRING=" + app.export_session_string())
