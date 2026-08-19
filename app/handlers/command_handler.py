from telegram import Update
from telegram.ext import ContextTypes
from app.services.leveling_service import LevelingService

leveling_service = LevelingService()

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
        "📈 *Leveling Bot*\n\n"
        "Activity in the group chat earns you EXP!\n\n"
        "/level — Check your level and EXP\n"
        "/rank — Group leaderboard\n",
        parse_mode="Markdown",
        do_quote=False
    )

