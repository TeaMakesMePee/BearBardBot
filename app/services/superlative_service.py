import random
from datetime import datetime, timedelta

from app.database import models
from app.services.leveling_service import LevelingService

POLL_TIMEOUT_SECONDS = 600  # TESTING value — change to 24 * 3600 for production
MAX_POLL_OPTIONS = 10
SUPERLATIVE_EXP_REWARD = 20
MAX_CONCURRENT_ROUNDS = 3

leveling_service = LevelingService()


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


async def post_round(bot, job_queue, chat_id: int, question_text: str | None = None) -> bool:
    """Starts a round. If question_text is given, it's an ad-hoc /suggest poll
    (never written to superlative_questions). Otherwise picks the next
    question from the bank, cycling through without repeats."""
    models.ensure_superlative_game_row(chat_id)

    if models.get_active_round_count(chat_id) >= MAX_CONCURRENT_ROUNDS:
        await bot.send_message(
            chat_id=chat_id,
            text=f"Already {MAX_CONCURRENT_ROUNDS} superlatives running at once — wait for one to finish first."
        )
        return False

    members = models.get_active_chat_members(chat_id, limit=MAX_POLL_OPTIONS)
    if len(members) < 2:
        await bot.send_message(
            chat_id=chat_id,
            text="Not enough active members yet to run Superlatives — need at least 2 people who've sent a message."
        )
        if question_text is None:
            models.stop_superlative_game(chat_id)
        return False

    question_id = None
    if question_text is None:
        question = models.get_next_superlative_question(chat_id)
        if question is None:
            await bot.send_message(chat_id=chat_id, text="No superlative questions available right now.")
            models.stop_superlative_game(chat_id)
            return False
        question_id = question["id"]
        question_text = question["text"]

    option_names = [_display_name(m) for m in members]
    option_user_ids = [m["user_id"] for m in members]

    poll_message = await bot.send_poll(
        chat_id=chat_id,
        question=f"Most likely to {question_text}?",
        options=option_names,
        is_anonymous=True,
    )

    resolve_at = datetime.now() + timedelta(seconds=POLL_TIMEOUT_SECONDS)
    round_id = models.create_superlative_round(
        chat_id, poll_message.message_id, poll_message.poll.id, option_user_ids, resolve_at,
        question_id=question_id, question_text=(question_text if question_id is None else None),
    )
    schedule_resolve(job_queue, chat_id, round_id, POLL_TIMEOUT_SECONDS)
    return True


def schedule_resolve(job_queue, chat_id: int, round_id: int, delay_seconds: float) -> None:
    job_queue.run_once(_resolve_round_job, max(delay_seconds, 0), data=(chat_id, round_id))


async def _resolve_round_job(context) -> None:
    chat_id, round_id = context.job.data
    await resolve_round(context.bot, context.job_queue, chat_id, round_id)


async def handle_poll_answer(bot, job_queue, poll_answer) -> None:
    """Early-closes a round once every chat member has voted."""
    round_row = models.get_superlative_round_by_poll_id(poll_answer.poll_id)
    if round_row is None:
        return

    voter_id = poll_answer.user.id
    if poll_answer.option_ids:
        models.record_superlative_vote(round_row["id"], voter_id, poll_answer.option_ids[0])

    try:
        member_count = await bot.get_chat_member_count(round_row["chat_id"])
        eligible_voters = max(member_count - 1, 1)  # exclude the bot itself
    except Exception:
        eligible_voters = len(round_row["option_user_ids"])

    if models.count_superlative_votes(round_row["id"]) >= eligible_voters:
        await resolve_round(bot, job_queue, round_row["chat_id"], round_row["id"])


async def cancel_oldest_round(bot, chat_id: int) -> bool:
    """Manually cancels the oldest active round in this chat (no winner, no EXP,
    doesn't chain into the next round). Testing-only control, slated for removal
    once rounds run on a fully automated schedule."""
    round_row = models.get_oldest_active_round(chat_id)
    if round_row is None:
        return False

    try:
        await bot.stop_poll(chat_id=chat_id, message_id=round_row["poll_message_id"])
    except Exception:
        pass

    models.resolve_superlative_round(round_row["id"], None)
    await bot.send_message(
        chat_id=chat_id,
        text=f"Cancelled: \"Most likely to {round_row['resolved_question_text']}\""
    )
    return True


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
    question_text = round_row["resolved_question_text"]

    if winner_index is None:
        models.resolve_superlative_round(round_id, None)
        await bot.send_message(chat_id=chat_id, text="Nobody voted this round, skipping! 🤷")
    else:
        winner_user_id = option_user_ids[winner_index]
        members = {m["user_id"]: m["username"] for m in models.get_active_chat_members(chat_id, limit=MAX_POLL_OPTIONS)}
        winner_name = members.get(winner_user_id) or str(winner_user_id)
        models.resolve_superlative_round(round_id, winner_user_id)

        level_up = leveling_service.award_bonus_exp(winner_user_id, chat_id, winner_name, SUPERLATIVE_EXP_REWARD)

        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"🏆 *{winner_name}* is Most Likely To {question_text}!\n"
                f"+{SUPERLATIVE_EXP_REWARD} EXP"
            ),
            parse_mode="Markdown"
        )
        if level_up:
            await bot.send_message(
                chat_id=chat_id,
                text=f"🎉 *{level_up['username']}* leveled up!\nLevel {level_up['old_level']} → *Level {level_up['new_level']}*",
                parse_mode="Markdown"
            )

    # Only auto-chain into the next round for the cycling game, not one-off /suggest polls.
    if round_row["question_id"] is not None and models.is_superlative_game_active(chat_id):
        await post_round(bot, job_queue, chat_id)
