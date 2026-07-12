from app.database.models import get_user, upsert_user_exp, get_leaderboard
from app.services.leveling_math import exp_to_level, user_progress
from app.config import EXP_PER_MESSAGE

class LevelingService:
    def award_exp(self, user_id: int, chat_id: int, username: str) -> dict | None:
        existing = get_user(user_id, chat_id)

        old_exp = existing["exp"] if existing else 0
        old_level = existing["level"] if existing else 1

        new_exp = old_exp + EXP_PER_MESSAGE
        new_level = exp_to_level(new_exp)

        upsert_user_exp(user_id, chat_id, username, new_exp, new_level)

        if new_level > old_level:
            return {
                "leveled_up": True,
                "old_level": old_level,
                "new_level": new_level,
                "username": username,
            }
        return None

    def get_user_stats(self, user_id: int, chat_id: int) -> dict | None:
        user = get_user(user_id, chat_id)
        
        if user is None: return user
        
        progress = user_progress(user["exp"])
        progress["username"] = user["username"]
        progress["message_count"] = user["message_count"]
        return progress

    def get_leaderboard(self, chat_id: int, limit: int = 10) -> list[dict]:
        return get_leaderboard(chat_id, limit)

