import random
from datetime import datetime, timedelta

from app.database import models

ROUND_INTERVAL_SECONDS = 600  # TESTING value — change to 7 * 24 * 3600 for production
MAX_POLL_OPTIONS = 10


def pick_winner_index(vote_counts: list[int]) -> int | None:
    """Pure winner-selection logic: majority index, random tie-break, None if no votes."""
    total = sum(vote_counts)
    if total == 0:
        return None
    top = max(vote_counts)
    tied_indices = [i for i, c in enumerate(vote_counts) if c == top]
    return random.choice(tied_indices)


def _display_name(member: dict) -> str:
    return member["username"] or str(member["user_id"])


async def post_round(bot, job_queue, chat_id: int) -> None:
    members = models.get_active_chat_members(chat_id, limit=MAX_POLL_OPTIONS)
    if len(members) < 2:
        await bot.send_message(
            chat_id=chat_id,
            text="Not enough active members yet to run Superlatives — need at least 2 people who've sent a message."
        )
        models.stop_superlative_game(chat_id)
        return

    question = models.get_next_superlative_question(chat_id)
    if question is None:
        await bot.send_message(chat_id=chat_id, text="No superlative questions available right now.")
        models.stop_superlative_game(chat_id)
        return

    option_names = [_display_name(m) for m in members]
    option_user_ids = [m["user_id"] for m in members]

    poll_message = await bot.send_poll(
        chat_id=chat_id,
        question=f"Most likely to {question['text']}?",
        options=option_names,
        is_anonymous=True,
    )

    resolve_at = datetime.now() + timedelta(seconds=ROUND_INTERVAL_SECONDS)
    round_id = models.create_superlative_round(
        chat_id, question["id"], poll_message.message_id, option_user_ids, resolve_at
    )
    schedule_resolve(job_queue, chat_id, round_id, ROUND_INTERVAL_SECONDS)


def schedule_resolve(job_queue, chat_id: int, round_id: int, delay_seconds: float) -> None:
    job_queue.run_once(_resolve_round_job, max(delay_seconds, 0), data=(chat_id, round_id))


async def _resolve_round_job(context) -> None:
    chat_id, round_id = context.job.data
    await resolve_round(context.bot, context.job_queue, chat_id, round_id)


async def resolve_round(bot, job_queue, chat_id: int, round_id: int) -> None:
    round_row = models.get_superlative_round(round_id)
    if round_row is None or round_row["resolved_at"] is not None:
        return

    try:
        poll = await bot.stop_poll(chat_id=chat_id, message_id=round_row["poll_message_id"])
        vote_counts = [opt.voter_count for opt in poll.options]
    except Exception:
        vote_counts = []

    option_user_ids = round_row["option_user_ids"]
    winner_index = pick_winner_index(vote_counts) if vote_counts else None

    if winner_index is None:
        models.resolve_superlative_round(round_id, None)
        await bot.send_message(chat_id=chat_id, text="Nobody voted this round, skipping! 🤷")
    else:
        winner_user_id = option_user_ids[winner_index]
        members = {m["user_id"]: m["username"] for m in models.get_active_chat_members(chat_id, limit=MAX_POLL_OPTIONS)}
        winner_name = members.get(winner_user_id) or str(winner_user_id)
        models.resolve_superlative_round(round_id, winner_user_id)
        await bot.send_message(
            chat_id=chat_id,
            text=f"🏆 *{winner_name}* is Most Likely To {round_row['question_text']}!",
            parse_mode="Markdown"
        )

    if models.is_superlative_game_active(chat_id):
        await post_round(bot, job_queue, chat_id)
