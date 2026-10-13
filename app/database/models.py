from datetime import date, datetime
from app.database.db import get_connection

def get_meta(key: str) -> str | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM bot_meta WHERE key = %s", (key,))
            row = cur.fetchone()
            return row["value"] if row else None
    finally:
        conn.close()

def set_meta(key: str, value: str) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bot_meta (key, value) VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """,
                (key, value)
            )
        conn.commit()
    finally:
        conn.close()

def get_known_chat_ids() -> list[int]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT chat_id FROM user_levels")
            return [row["chat_id"] for row in cur.fetchall()]
    finally:
        conn.close()

def get_user(user_id: int, chat_id: int) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM user_levels WHERE user_id = %s AND chat_id = %s",
                (user_id, chat_id)
            )
            return cur.fetchone()
    finally:
        conn.close()

def upsert_user_exp(user_id: int, chat_id: int, username: str, new_exp: int, new_level: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_levels
                    (user_id, chat_id, username, exp, level, message_count, last_message_at, first_seen_at)
                VALUES (%s, %s, %s, %s, 1, 1, NOW(), NOW())
                ON CONFLICT (user_id, chat_id)
                DO UPDATE SET
                    exp = %s,
                    level = %s,
                    username = %s,
                    message_count = user_levels.message_count + 1,
                    last_message_at = NOW()
                """,
                (user_id, chat_id, username, new_exp, new_exp, new_level, username)
            )
        conn.commit()
    finally:
        conn.close()

def set_exp_and_level(user_id: int, chat_id: int, new_exp: int, new_level: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE user_levels SET exp = %s, level = %s WHERE user_id = %s AND chat_id = %s",
                (new_exp, new_level, user_id, chat_id)
            )
        conn.commit()
    finally:
        conn.close()

def record_active_day(user_id: int, chat_id: int, active_date: date) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_active_days (user_id, chat_id, active_date)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, chat_id, active_date) DO NOTHING
                """,
                (user_id, chat_id, active_date)
            )
        conn.commit()
    finally:
        conn.close()

def get_distinct_active_days(user_id: int, chat_id: int) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM user_active_days WHERE user_id = %s AND chat_id = %s",
                (user_id, chat_id)
            )
            return cur.fetchone()["n"]
    finally:
        conn.close()

def has_active_weekend_days_this_week(user_id: int, chat_id: int, today: date) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(DISTINCT EXTRACT(ISODOW FROM active_date)) AS n
                FROM user_active_days
                WHERE user_id = %s AND chat_id = %s
                  AND EXTRACT(ISODOW FROM active_date) IN (6, 7)
                  AND date_trunc('week', active_date) = date_trunc('week', %s::date)
                """,
                (user_id, chat_id, today)
            )
            return cur.fetchone()["n"] == 2
    finally:
        conn.close()

def get_user_chat_count(user_id: int) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(DISTINCT chat_id) AS n FROM user_levels WHERE user_id = %s",
                (user_id,)
            )
            return cur.fetchone()["n"]
    finally:
        conn.close()

def get_chat_rank(user_id: int, chat_id: int) -> int | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rank FROM (
                    SELECT user_id, RANK() OVER (ORDER BY exp DESC) AS rank
                    FROM user_levels WHERE chat_id = %s
                ) ranked WHERE user_id = %s
                """,
                (chat_id, user_id)
            )
            row = cur.fetchone()
            return row["rank"] if row else None
    finally:
        conn.close()

def get_chat_join_rank(user_id: int, chat_id: int) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rank FROM (
                    SELECT user_id, RANK() OVER (ORDER BY first_seen_at ASC) AS rank
                    FROM user_levels WHERE chat_id = %s
                ) ranked WHERE user_id = %s
                """,
                (chat_id, user_id)
            )
            row = cur.fetchone()
            return row["rank"] if row else 1
    finally:
        conn.close()

def sync_achievement_definitions(achievements: list) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for a in achievements:
                cur.execute(
                    """
                    INSERT INTO achievements (key, name, description, icon_path)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        icon_path = EXCLUDED.icon_path
                    """,
                    (a.key, a.name, a.description, a.icon_path)
                )
        conn.commit()
    finally:
        conn.close()

def get_unlocked_achievements(user_id: int, chat_id: int) -> set[str]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT achievement_key FROM user_achievements WHERE user_id = %s AND chat_id = %s",
                (user_id, chat_id)
            )
            return {row["achievement_key"] for row in cur.fetchall()}
    finally:
        conn.close()

def unlock_achievement(user_id: int, chat_id: int, key: str) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_achievements (user_id, chat_id, achievement_key)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, chat_id, achievement_key) DO NOTHING
                """,
                (user_id, chat_id, key)
            )
        conn.commit()
    finally:
        conn.close()

def get_user_by_username(chat_id: int, username: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM user_levels WHERE chat_id = %s AND LOWER(username) = LOWER(%s)",
                (chat_id, username)
            )
            return cur.fetchone()
    finally:
        conn.close()

def get_all_users() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_levels")
            return cur.fetchall()
    finally:
        conn.close()

def sync_superlative_questions(texts: list[str]) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for text in texts:
                cur.execute(
                    """
                    INSERT INTO superlative_questions (text)
                    SELECT %s
                    WHERE NOT EXISTS (SELECT 1 FROM superlative_questions WHERE text = %s)
                    """,
                    (text, text)
                )
        conn.commit()
    finally:
        conn.close()

def get_next_superlative_question(chat_id: int, recent_limit: int = 10_000) -> dict | None:
    """recent_limit effectively unbounded so each chat cycles through its
    whole active question bank before any repeat -- independent per chat
    since the exclusion subquery is scoped to this chat_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, text FROM superlative_questions
                WHERE active = TRUE
                  AND id NOT IN (
                      SELECT question_id FROM superlative_rounds
                      WHERE chat_id = %s
                      ORDER BY created_at DESC
                      LIMIT %s
                  )
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (chat_id, recent_limit)
            )
            row = cur.fetchone()
            if row:
                return row
            cur.execute("SELECT id, text FROM superlative_questions WHERE active = TRUE ORDER BY RANDOM() LIMIT 1")
            return cur.fetchone()
    finally:
        conn.close()

def get_active_chat_members(chat_id: int, limit: int = 10) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, username FROM user_levels
                WHERE chat_id = %s
                ORDER BY last_message_at DESC
                LIMIT %s
                """,
                (chat_id, limit)
            )
            return cur.fetchall()
    finally:
        conn.close()

def start_superlative_game(chat_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO superlative_games (chat_id, active) VALUES (%s, TRUE)
                ON CONFLICT (chat_id) DO UPDATE SET active = TRUE
                """,
                (chat_id,)
            )
        conn.commit()
    finally:
        conn.close()

def stop_superlative_game(chat_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE superlative_games SET active = FALSE WHERE chat_id = %s", (chat_id,))
        conn.commit()
    finally:
        conn.close()

def is_superlative_game_active(chat_id: int) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT active FROM superlative_games WHERE chat_id = %s", (chat_id,))
            row = cur.fetchone()
            return bool(row and row["active"])
    finally:
        conn.close()

def get_active_superlative_games() -> list[int]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT chat_id FROM superlative_games WHERE active = TRUE")
            return [row["chat_id"] for row in cur.fetchall()]
    finally:
        conn.close()

def ensure_superlative_game_row(chat_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO superlative_games (chat_id, active) VALUES (%s, FALSE) ON CONFLICT (chat_id) DO NOTHING",
                (chat_id,)
            )
        conn.commit()
    finally:
        conn.close()

def create_superlative_round(
    chat_id: int, poll_message_id: int, poll_id: str,
    option_user_ids: list[int], resolve_at: datetime,
    question_id: int | None = None, question_text: str | None = None,
) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO superlative_rounds
                    (chat_id, question_id, question_text, poll_message_id, poll_id, option_user_ids, resolve_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (chat_id, question_id, question_text, poll_message_id, poll_id, option_user_ids, resolve_at)
            )
            return cur.fetchone()["id"]
    finally:
        conn.close()

def get_superlative_round(round_id: int) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.*, COALESCE(r.question_text, q.text) AS resolved_question_text
                FROM superlative_rounds r
                LEFT JOIN superlative_questions q ON q.id = r.question_id
                WHERE r.id = %s
                """,
                (round_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()

def get_superlative_round_by_poll_id(poll_id: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM superlative_rounds WHERE poll_id = %s AND resolved_at IS NULL",
                (poll_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()

def record_superlative_vote(round_id: int, voter_user_id: int, option_index: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO superlative_votes (round_id, voter_user_id, option_index)
                VALUES (%s, %s, %s)
                ON CONFLICT (round_id, voter_user_id) DO UPDATE SET option_index = EXCLUDED.option_index
                """,
                (round_id, voter_user_id, option_index)
            )
        conn.commit()
    finally:
        conn.close()

def count_superlative_votes(round_id: int) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM superlative_votes WHERE round_id = %s", (round_id,))
            return cur.fetchone()["n"]
    finally:
        conn.close()

def get_active_round_count(chat_id: int) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM superlative_rounds WHERE chat_id = %s AND resolved_at IS NULL",
                (chat_id,)
            )
            return cur.fetchone()["n"]
    finally:
        conn.close()

def get_oldest_active_round(chat_id: int) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.*, COALESCE(r.question_text, q.text) AS resolved_question_text
                FROM superlative_rounds r
                LEFT JOIN superlative_questions q ON q.id = r.question_id
                WHERE r.chat_id = %s AND r.resolved_at IS NULL
                ORDER BY r.created_at ASC
                LIMIT 1
                """,
                (chat_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()

def get_pending_superlative_rounds() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.*, COALESCE(r.question_text, q.text) AS resolved_question_text
                FROM superlative_rounds r
                LEFT JOIN superlative_questions q ON q.id = r.question_id
                WHERE r.resolved_at IS NULL
                """
            )
            return cur.fetchall()
    finally:
        conn.close()

def resolve_superlative_round(round_id: int, winner_user_id: int | None) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE superlative_rounds SET resolved_at = NOW(), winner_user_id = %s WHERE id = %s",
                (winner_user_id, round_id)
            )
        conn.commit()
    finally:
        conn.close()

def get_leaderboard(chat_id: int, limit: int = 10) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, exp, level, message_count
                FROM user_levels
                WHERE chat_id = %s
                ORDER BY exp DESC
                LIMIT %s
                """,
                (chat_id, limit)
            )
            return cur.fetchall()
    finally:
        conn.close()



