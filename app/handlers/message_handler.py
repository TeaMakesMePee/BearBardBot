from telegram import Update
from telegram.ext import ContextTypes
from app.services.leveling_service import LevelingService

leveling_service = LevelingService()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return

    if update.effective_chat.type not in ("group", "supergroup"):
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    username = update.effective_user.username or update.effective_user.first_name

    level_up = leveling_service.award_exp(user_id, chat_id, username)

    if level_up:
        await update.message.reply_text(
            f"🎉 *{level_up['username']}* leveled up!\n"
            f"Level {level_up['old_level']} → *Level {level_up['new_level']}*",
            parse_mode="Markdown"
        )
