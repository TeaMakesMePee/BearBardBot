import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment")

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "leveling")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "botuser")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")

EXP_PER_MESSAGE = 10
EXP_COOLDOWN_SECONDS = 5
