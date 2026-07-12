import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters
)

from app.config import BOT_TOKEN
from app.database.db import init_db
from app.handlers.message_handler import handle_message
from app.handlers.command_handler import (
    level_command, rank_command, help_command
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing database...")
    init_db()

    logger.info("Starting bot in polling mode...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("level", level_command))
    app.add_handler(CommandHandler("rank", rank_command))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   handle_message))

    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

