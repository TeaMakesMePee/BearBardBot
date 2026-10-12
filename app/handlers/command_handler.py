from telegram import Update
from telegram.ext import ContextTypes

from app.database.models import get_unlocked_achievements
from app.services.leveling_service import LevelingService
from app.services.profile_image import render_profile_image

leveling_service = LevelingService()

PROFILE_SELF_DESTRUCT_SECONDS = 600


def _resolve_profile_target(update: Update):
    message = update.message
    if message.reply_to_message is not None:
        return message.reply_to_message.from_user

    entities = message.parse_entities(types=["mention", "text_mention"])
    for entity, text in entities.items():
        if entity.type == "text_mention":
            return entity.user
    return None


async def delete_profile_photo(context: ContextTypes.DEFAULT_TYPE):
    chat_id, message_id = context.job.data
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_user = _resolve_profile_target(update)

    if target_user is None:
        await update.message.reply_text(
            "Reply to someone's message with /profile, or @mention them, to view their profile.",
            do_quote=False
        )
        return

    chat_id = update.effective_chat.id
    stats = leveling_service.get_user_stats(target_user.id, chat_id)

    if stats is None:
        await update.message.reply_text(
            f"{target_user.first_name} hasn't earned any EXP yet!",
            do_quote=False
        )
        return

    unlocked_keys = get_unlocked_achievements(target_user.id, chat_id)

    avatar_bytes = None
    photos = await target_user.get_profile_photos()
    if photos and photos.photos:
        file = await photos.photos[0][-1].get_file()
        avatar_bytes = bytes(await file.download_as_bytearray())

    image_buf = render_profile_image(
        display_name=target_user.full_name,
        exp=stats["exp"],
        message_count=stats["message_count"],
        unlocked_keys=unlocked_keys,
        avatar_bytes=avatar_bytes,
    )

    sent_message = await update.message.reply_photo(photo=image_buf, do_quote=False)

    context.job_queue.run_once(
        delete_profile_photo,
        PROFILE_SELF_DESTRUCT_SECONDS,
        data=(sent_message.chat_id, sent_message.message_id),
    )

async def level_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    stats = leveling_service.get_user_stats(user_id, chat_id)

    if stats is None:
        await update.message.reply_text(
            "You haven't earned any EXP yet. Send some messages!",
            do_quote=False
        )
        return
    
    into_curr_level, from_next_level = stats['from_level'], stats['to_level']
    curr_level_exp = into_curr_level + from_next_level
    filled = int(10 * into_curr_level / curr_level_exp)
    bar = '#' * filled + ' ' * (10 - filled)

    await update.message.reply_text(
        f"📊 *{stats['username']}*\n\n"
        f"Level: *{stats['level']}*\n"
        f"EXP: {into_curr_level}/{curr_level_exp}\n"
        f"`[{bar}]`\n"
        f"Total messages: {stats['message_count']}",
        parse_mode="Markdown",
        do_quote=False
    )

async def rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    leaderboard = leveling_service.get_leaderboard(chat_id, limit=10)

    if not leaderboard:
        await update.message.reply_text(
            "No one has earned EXP yet!",
            do_quote=False                               
        )
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 *Leaderboard*\n"]

    for i, user in enumerate(leaderboard):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        name = user["username"] or "Unknown"
        lines.append(
            f"{prefix} {name} - Level {user['level']} ({user['exp']} EXP)"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        do_quote=False
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 *Bear Bard Bot*\n\n"
        "Activity in the group chat earns you EXP!\n\n"
        "/level — Check your level and EXP\n"
        "/rank — Group leaderboard\n"
        "/profile (reply or @mention) — View a member's profile card\n",
        parse_mode="Markdown",
        do_quote=False
    )

