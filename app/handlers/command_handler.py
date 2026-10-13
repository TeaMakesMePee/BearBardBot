import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.database import models
from app.database.models import get_unlocked_achievements, get_user_by_username
from app.services.achievements import ACHIEVEMENTS
from app.services.leveling_service import LevelingService
from app.services.profile_image import render_profile_image
from app.services import superlative_service

logger = logging.getLogger(__name__)
leveling_service = LevelingService()

PROFILE_SELF_DESTRUCT_SECONDS = 60


def _resolve_profile_target_id(update: Update) -> int | None:
    """Returns the target user_id, or None.

    reply-to and @mentions of usernameless users give us a full User object
    directly from Telegram. A plain @username mention only gives us text
    (Telegram doesn't resolve it to a user for us), so we look it up against
    users we've already seen send a message in this chat.
    """
    message = update.message

    if message.reply_to_message is not None:
        return message.reply_to_message.from_user.id

    entities = message.parse_entities(types=["mention", "text_mention"])
    for entity, text in entities.items():
        if entity.type == "text_mention":
            return entity.user.id
        if entity.type == "mention":
            username = text.lstrip("@")
            row = get_user_by_username(update.effective_chat.id, username)
            if row is not None:
                return row["user_id"]

    return None


async def _get_display_name(context: ContextTypes.DEFAULT_TYPE, user_id: int, fallback: str) -> str:
    try:
        chat = await context.bot.get_chat(user_id)
        name = " ".join(filter(None, [chat.first_name, chat.last_name]))
        return name or fallback
    except Exception:
        return fallback


async def _get_avatar_bytes(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bytes | None:
    photos = await context.bot.get_user_profile_photos(user_id, limit=1)
    if not photos or not photos.photos:
        return None
    file = await photos.photos[0][-1].get_file()
    return bytes(await file.download_as_bytearray())


async def delete_profile_photo(context: ContextTypes.DEFAULT_TYPE):
    chat_id, message_id = context.job.data
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        logger.exception(f"Failed to self-destruct profile photo {message_id} in chat {chat_id}")


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_user_id = _resolve_profile_target_id(update)

    if target_user_id is None:
        await update.message.reply_text(
            "Reply to someone's message with /profile, or @mention them, to view their profile.\n"
            "(@username mentions only work for members who've already sent a message in this chat.)",
            do_quote=False
        )
        return

    chat_id = update.effective_chat.id
    stats = leveling_service.get_user_stats(target_user_id, chat_id)
    display_name = await _get_display_name(
        context, target_user_id, fallback=(stats["username"] if stats else "This user")
    )

    if stats is None:
        await update.message.reply_text(
            f"{display_name} hasn't earned any EXP yet!",
            do_quote=False
        )
        return

    unlocked_keys = get_unlocked_achievements(target_user_id, chat_id)
    avatar_bytes = await _get_avatar_bytes(context, target_user_id)

    image_buf = render_profile_image(
        display_name=display_name,
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
        "/profile (reply or @mention) — View a member's profile card\n"
        "/achievements — List every achievement\n"
        "/superlatives — \"Most Likely To\" group game (start/stop/suggest)\n",
        parse_mode="Markdown",
        do_quote=False
    )

async def achievements_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🏅 *Achievements*\n"]
    for achievement in ACHIEVEMENTS:
        lines.append(
            f"*{achievement.name}* (+{achievement.exp_reward} EXP)\n{achievement.description}"
        )

    await update.message.reply_text(
        "\n\n".join(lines),
        parse_mode="Markdown",
        do_quote=False
    )

async def superlatives_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args or []
    subcommand = args[0].lower() if args else ""

    if subcommand == "start":
        if models.is_superlative_game_active(chat_id):
            await update.message.reply_text("Superlatives is already running in this chat!", do_quote=False)
            return
        models.start_superlative_game(chat_id)
        await update.message.reply_text("🎉 Superlatives started! First round coming up...", do_quote=False)
        await superlative_service.post_round(context.bot, context.job_queue, chat_id)

    elif subcommand == "stop":
        models.stop_superlative_game(chat_id)
        await update.message.reply_text("Superlatives stopped for this chat.", do_quote=False)

    elif subcommand == "suggest":
        text = " ".join(args[1:]).strip()
        if not text:
            await update.message.reply_text(
                "Usage: /superlatives suggest <your superlative>\n"
                "e.g. /superlatives suggest forget their own birthday plans",
                do_quote=False
            )
            return
        if len(text) > 200:
            await update.message.reply_text("That's a bit long — keep it under 200 characters.", do_quote=False)
            return
        models.add_superlative_question(text, update.effective_user.id)
        await update.message.reply_text(f"Added: \"Most likely to {text}\" 🎉", do_quote=False)

    else:
        await update.message.reply_text(
            "📋 *Superlatives*\n\n"
            "/superlatives start — start the weekly \"Most Likely To\" game\n"
            "/superlatives stop — stop it\n"
            "/superlatives suggest <text> — add your own superlative\n",
            parse_mode="Markdown",
            do_quote=False
        )

