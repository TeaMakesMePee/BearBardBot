from datetime import datetime

from app.services.achievements import ACHIEVEMENTS_BY_KEY


def base_ctx(**overrides):
    ctx = {
        "message_count": 0,
        "level": 1,
        "now": datetime(2026, 10, 12, 12, 0, 0),
        "now_local": datetime(2026, 10, 12, 12, 0, 0),
        "chat_rank": None,
        "chat_user_rank_by_join": 99,
        "distinct_active_days": 0,
        "active_both_weekend_days_this_week": False,
        "days_since_first_seen": 0,
        "days_since_last_message": None,
        "chat_count": 1,
        "unlocked_count_excluding_this": 0,
    }
    ctx.update(overrides)
    return ctx


def test_first_words():
    assert ACHIEVEMENTS_BY_KEY["first_words"].check(base_ctx(message_count=1))
    assert not ACHIEVEMENTS_BY_KEY["first_words"].check(base_ctx(message_count=0))


def test_century_club():
    assert ACHIEVEMENTS_BY_KEY["century_club"].check(base_ctx(message_count=100))
    assert not ACHIEVEMENTS_BY_KEY["century_club"].check(base_ctx(message_count=99))


def test_level_milestones():
    assert ACHIEVEMENTS_BY_KEY["level_10"].check(base_ctx(level=10))
    assert not ACHIEVEMENTS_BY_KEY["level_10"].check(base_ctx(level=9))


def test_top_dog_and_podium():
    assert ACHIEVEMENTS_BY_KEY["top_dog"].check(base_ctx(chat_rank=1))
    assert not ACHIEVEMENTS_BY_KEY["top_dog"].check(base_ctx(chat_rank=2))
    assert ACHIEVEMENTS_BY_KEY["podium_finish"].check(base_ctx(chat_rank=3))
    assert not ACHIEVEMENTS_BY_KEY["podium_finish"].check(base_ctx(chat_rank=4))


def test_early_bird():
    assert ACHIEVEMENTS_BY_KEY["early_bird"].check(base_ctx(chat_user_rank_by_join=10))
    assert not ACHIEVEMENTS_BY_KEY["early_bird"].check(base_ctx(chat_user_rank_by_join=11))


def test_night_owl():
    assert ACHIEVEMENTS_BY_KEY["night_owl"].check(base_ctx(now_local=datetime(2026, 10, 12, 3, 30)))
    assert not ACHIEVEMENTS_BY_KEY["night_owl"].check(base_ctx(now_local=datetime(2026, 10, 12, 9, 0)))


def test_consistency_and_dedicated():
    assert ACHIEVEMENTS_BY_KEY["consistency"].check(base_ctx(distinct_active_days=7))
    assert not ACHIEVEMENTS_BY_KEY["consistency"].check(base_ctx(distinct_active_days=6))
    assert ACHIEVEMENTS_BY_KEY["dedicated"].check(base_ctx(distinct_active_days=30))


def test_weekend_warrior():
    assert ACHIEVEMENTS_BY_KEY["weekend_warrior"].check(base_ctx(active_both_weekend_days_this_week=True))
    assert not ACHIEVEMENTS_BY_KEY["weekend_warrior"].check(base_ctx(active_both_weekend_days_this_week=False))


def test_veteran():
    assert ACHIEVEMENTS_BY_KEY["veteran"].check(base_ctx(days_since_first_seen=90))
    assert not ACHIEVEMENTS_BY_KEY["veteran"].check(base_ctx(days_since_first_seen=89))


def test_comeback():
    assert ACHIEVEMENTS_BY_KEY["comeback"].check(base_ctx(days_since_last_message=14))
    assert not ACHIEVEMENTS_BY_KEY["comeback"].check(base_ctx(days_since_last_message=None))
    assert not ACHIEVEMENTS_BY_KEY["comeback"].check(base_ctx(days_since_last_message=5))


def test_social_butterfly():
    assert ACHIEVEMENTS_BY_KEY["social_butterfly"].check(base_ctx(chat_count=3))
    assert not ACHIEVEMENTS_BY_KEY["social_butterfly"].check(base_ctx(chat_count=2))


def test_overachiever():
    assert ACHIEVEMENTS_BY_KEY["overachiever"].check(base_ctx(unlocked_count_excluding_this=19))
    assert not ACHIEVEMENTS_BY_KEY["overachiever"].check(base_ctx(unlocked_count_excluding_this=18))


def test_all_achievements_have_unique_keys_and_icons():
    assert len(ACHIEVEMENTS_BY_KEY) == 20
    for achievement in ACHIEVEMENTS_BY_KEY.values():
        assert achievement.icon_path.endswith(".svg")
