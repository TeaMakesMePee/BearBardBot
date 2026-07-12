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
                    (user_id, chat_id, username, exp, level, message_count, last_message_at)
                VALUES (%s, %s, %s, %s, 1, 1, NOW())
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



