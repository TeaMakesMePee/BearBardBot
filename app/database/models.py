from datetime import date, datetime
from app.database.db import get_connection

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

def get_all_users() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_levels")
            return cur.fetchall()
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



