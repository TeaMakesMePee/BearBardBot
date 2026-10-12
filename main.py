import logging
from datetime import datetime

from app.services.heartbeat import send_heartbeat
from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters
)

from app.config import BOT_TOKEN
from app.database.db import init_db
from app.database.models import sync_achievement_definitions, get_meta, set_meta, get_known_chat_ids
from app.version import VERSION, RELEASE_NOTES, ANNOUNCE
from app.handlers.message_handler import handle_message
from app.handlers.command_handler import (
    level_command, rank_command, help_command, profile_command, achievements_command
)
from app.services.achievements import ACHIEVEMENTS
from app.services.achievement_service import AchievementService

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def error_handler(update, context):
    logger.error(f"Update caused error: {context.error}")

async def heartbeat_job(context):
    send_heartbeat()

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("level", "Check your level and EXP"),
        BotCommand("rank", "Group leaderboard"),
        BotCommand("profile", "View a member's profile card (reply or @mention)"),
        BotCommand("achievements", "List every achievement"),
        BotCommand("help", "Show commands"),
    ])

    last_seen_version = get_meta("last_broadcast_version")
    if last_seen_version == VERSION:
        return

    if not ANNOUNCE:
        logger.info(f"v{VERSION} marked as not announce-worthy, skipping broadcast.")
        set_meta("last_broadcast_version", VERSION)
        return

    logger.info(f"Broadcasting update notice for v{VERSION}...")
    message = f"🐻 *BearBardBot updated to v{VERSION}*\n\n{RELEASE_NOTES}"

    for chat_id in get_known_chat_ids():
        try:
            await app.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception:
            logger.exception(f"Failed to broadcast update notice to chat {chat_id}")

    set_meta("last_broadcast_version", VERSION)

def main():
    logger.info("Initializing database...")
    init_db()

    logger.info("Syncing achievement definitions...")
    sync_achievement_definitions(ACHIEVEMENTS)

    logger.info("Backfilling achievements for existing users...")
    unlocked_count = AchievementService().backfill_all(datetime.now())
    logger.info(f"Backfill complete, {unlocked_count} achievements retroactively unlocked.")

    logger.info("Starting bot in polling mode...")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.job_queue.run_repeating(heartbeat_job, interval=60, first=10)

    app.add_handler(CommandHandler("level", level_command))
    app.add_handler(CommandHandler("rank", rank_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("achievements", achievements_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   handle_message))
    
    app.add_error_handler(error_handler)

    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

