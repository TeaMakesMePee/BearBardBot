CREATE TABLE IF NOT EXISTS user_levels (
    user_id      BIGINT NOT NULL,
    chat_id      BIGINT NOT NULL,
    username     TEXT,
    exp           INTEGER NOT NULL DEFAULT 0,
    level        INTEGER NOT NULL DEFAULT 1,
    message_count INTEGER NOT NULL DEFAULT 0,
    last_message_at TIMESTAMP DEFAULT NOW(),
    first_seen_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, chat_id)
);

-- Needed for deployments where user_levels already existed before first_seen_at was added.
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMP;
UPDATE user_levels SET first_seen_at = last_message_at WHERE first_seen_at IS NULL;
ALTER TABLE user_levels ALTER COLUMN first_seen_at SET DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_chat_exp ON user_levels (chat_id, exp DESC);

CREATE TABLE IF NOT EXISTS user_active_days (
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    active_date DATE NOT NULL,
    PRIMARY KEY (user_id, chat_id, active_date)
);

CREATE TABLE IF NOT EXISTS achievements (
    key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    icon_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_achievements (
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    achievement_key TEXT NOT NULL REFERENCES achievements(key),
    unlocked_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, chat_id, achievement_key)
);
