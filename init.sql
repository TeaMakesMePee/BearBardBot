CREATE TABLE IF NOT EXISTS user_levels (
    user_id      BIGINT NOT NULL,
    chat_id      BIGINT NOT NULL,
    username     TEXT,
    exp           INTEGER NOT NULL DEFAULT 0,
    level        INTEGER NOT NULL DEFAULT 1,
    message_count INTEGER NOT NULL DEFAULT 0,
    last_message_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, chat_id)
);

CREATE INDEX IF NOT EXISTS idx_chat_exp ON user_levels (chat_id, exp DESC);
