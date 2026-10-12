from datetime import datetime

from app.database import models
from app.services.achievements import ACHIEVEMENTS, Achievement


class AchievementService:
    def _build_ctx(self, user_id: int, chat_id: int, user: dict, now: datetime, last_message_at) -> dict:
        first_seen_at = user.get("first_seen_at") if user else now
        already_unlocked = models.get_unlocked_achievements(user_id, chat_id)

        return {
            "message_count": user["message_count"],
            "level": user["level"],
            "now": now,
            "chat_rank": models.get_chat_rank(user_id, chat_id),
            "chat_user_rank_by_join": models.get_chat_join_rank(user_id, chat_id),
            "distinct_active_days": models.get_distinct_active_days(user_id, chat_id),
            "active_both_weekend_days_this_week": models.has_active_weekend_days_this_week(
                user_id, chat_id, now.date()
            ),
            "days_since_first_seen": (now - first_seen_at).days if first_seen_at else 0,
            "days_since_last_message": (now - last_message_at).days if last_message_at else None,
            "chat_count": models.get_user_chat_count(user_id),
            "unlocked_count_excluding_this": len(already_unlocked),
        }, already_unlocked

    def _unlock_new(self, user_id: int, chat_id: int, ctx: dict, already_unlocked: set[str]) -> list[Achievement]:
        newly_unlocked = []
        for achievement in ACHIEVEMENTS:
            if achievement.key in already_unlocked:
                continue
            if achievement.check(ctx):
                models.unlock_achievement(user_id, chat_id, achievement.key)
                newly_unlocked.append(achievement)
        return newly_unlocked

    def check_and_unlock(
        self, user_id: int, chat_id: int, user: dict, now: datetime,
        previous_last_message_at: datetime | None = None,
    ) -> list[Achievement]:
        models.record_active_day(user_id, chat_id, now.date())
        ctx, already_unlocked = self._build_ctx(user_id, chat_id, user, now, previous_last_message_at)
        return self._unlock_new(user_id, chat_id, ctx, already_unlocked)

    def backfill_all(self, now: datetime) -> int:
        """Retroactively unlock achievements already earned by existing users,
        based on their current tracked stats. Safe to re-run (idempotent)."""
        total_unlocked = 0
        for user in models.get_all_users():
            user_id, chat_id = user["user_id"], user["chat_id"]
            ctx, already_unlocked = self._build_ctx(user_id, chat_id, user, now, user.get("last_message_at"))
            total_unlocked += len(self._unlock_new(user_id, chat_id, ctx, already_unlocked))
        return total_unlocked
