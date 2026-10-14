from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Achievement:
    key: str
    name: str
    description: str
    icon_path: str
    exp_reward: int
    check: Callable[[dict], bool]


def _message_count_at_least(n: int) -> Callable[[dict], bool]:
    return lambda ctx: ctx["message_count"] >= n


def _level_at_least(n: int) -> Callable[[dict], bool]:
    return lambda ctx: ctx["level"] >= n


ACHIEVEMENTS: list[Achievement] = [
    Achievement(
        "first_words", "First Words", "Send your first message.",
        "assets/achievements/first_words.svg", 10, _message_count_at_least(1),
    ),
    Achievement(
        "century_club", "Century Club", "Send 100 messages.",
        "assets/achievements/century_club.svg", 50, _message_count_at_least(100),
    ),
    Achievement(
        "chatterbox", "Chatterbox", "Send 500 messages.",
        "assets/achievements/chatterbox.svg", 100, _message_count_at_least(500),
    ),
    Achievement(
        "motormouth", "Motormouth", "Send 1,000 messages.",
        "assets/achievements/motormouth.svg", 200, _message_count_at_least(1000),
    ),
    Achievement(
        "legend_of_the_group", "Legend of the Group", "Send 5,000 messages.",
        "assets/achievements/legend_of_the_group.svg", 500, _message_count_at_least(5000),
    ),
    Achievement(
        "level_5", "Level 5", "Reach level 5.",
        "assets/achievements/level_5.svg", 30, _level_at_least(5),
    ),
    Achievement(
        "level_10", "Level 10", "Reach level 10.",
        "assets/achievements/level_10.svg", 60, _level_at_least(10),
    ),
    Achievement(
        "level_25", "Level 25", "Reach level 25.",
        "assets/achievements/level_25.svg", 150, _level_at_least(25),
    ),
    Achievement(
        "level_50", "Level 50", "Reach level 50.",
        "assets/achievements/level_50.svg", 300, _level_at_least(50),
    ),
    Achievement(
        "top_dog", "Top Dog", "Reach #1 on the leaderboard.",
        "assets/achievements/top_dog.svg", 150, lambda ctx: ctx["chat_rank"] == 1,
    ),
    Achievement(
        "podium_finish", "Podium Finish", "Reach the top 3 on the leaderboard.",
        "assets/achievements/podium_finish.svg", 80,
        lambda ctx: ctx["chat_rank"] is not None and ctx["chat_rank"] <= 3,
    ),
    Achievement(
        "early_bird", "Early Bird", "Be one of the first 10 to earn XP in the chat.",
        "assets/achievements/early_bird.svg", 50, lambda ctx: ctx["chat_user_rank_by_join"] <= 10,
    ),
    Achievement(
        "night_owl", "Night Owl", "Send a message between 2am and 5am.",
        "assets/achievements/night_owl.svg", 30, lambda ctx: 2 <= ctx["now_local"].hour < 5,
    ),
    Achievement(
        "consistency", "Consistency", "Be active on 7 different days.",
        "assets/achievements/consistency.svg", 60, lambda ctx: ctx["distinct_active_days"] >= 7,
    ),
    Achievement(
        "dedicated", "Dedicated", "Be active on 30 different days.",
        "assets/achievements/dedicated.svg", 200, lambda ctx: ctx["distinct_active_days"] >= 30,
    ),
    Achievement(
        "weekend_warrior", "Weekend Warrior", "Be active on both Saturday and Sunday in the same week.",
        "assets/achievements/weekend_warrior.svg", 40, lambda ctx: ctx["active_both_weekend_days_this_week"],
    ),
    Achievement(
        "veteran", "Veteran", "90 days since your first message.",
        "assets/achievements/veteran.svg", 150, lambda ctx: ctx["days_since_first_seen"] >= 90,
    ),
    Achievement(
        "comeback", "Comeback", "Return after 14+ days of inactivity.",
        "assets/achievements/comeback.svg", 40,
        lambda ctx: ctx["days_since_last_message"] is not None and ctx["days_since_last_message"] >= 14,
    ),
    Achievement(
        "social_butterfly", "Social Butterfly", "Active in 3 or more different chats.",
        "assets/achievements/social_butterfly.svg", 100, lambda ctx: ctx["chat_count"] >= 3,
    ),
    Achievement(
        "overachiever", "Overachiever", "Unlock every other achievement.",
        "assets/achievements/overachiever.svg", 500, lambda ctx: ctx["unlocked_count_excluding_this"] >= 19,
    ),
]

ACHIEVEMENTS_BY_KEY: dict[str, Achievement] = {a.key: a for a in ACHIEVEMENTS}
