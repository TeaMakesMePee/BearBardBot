from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from app.database.models import get_user
from app.services.leveling_service import LevelingService
from app.services.achievement_service import AchievementService

leveling_service = LevelingService()
achievement_service = AchievementService()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return

    if update.effective_chat.type not in ("group", "supergroup"):
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    username = update.effective_user.username or update.effective_user.first_name

    previous = get_user(user_id, chat_id)
    level_up = leveling_service.award_exp(user_id, chat_id, username)

    if level_up:
        await update.message.reply_text(
            f"🎉 *{level_up['username']}* leveled up!\n"
            f"Level {level_up['old_level']} → *Level {level_up['new_level']}*",
            parse_mode="Markdown"
        )

    user = get_user(user_id, chat_id)
    newly_unlocked = achievement_service.check_and_unlock(
        user_id, chat_id, user, datetime.now(), previous_last_message_at=previous["last_message_at"] if previous else None
    )

    for achievement in newly_unlocked:
        await update.message.reply_text(
            f"🏅 *{username}* unlocked an achievement!\n*{achievement.name}* — {achievement.description}",
            parse_mode="Markdown"
        )
