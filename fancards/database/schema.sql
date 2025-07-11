CREATE SCHEMA IF NOT EXISTS user_data;
CREATE SCHEMA IF NOT EXISTS guild_data;
CREATE SCHEMA IF NOT EXISTS bot_data;

CREATE TABLE IF NOT EXISTS user_data.user (
    id SERIAL PRIMARY KEY,
    discord_user_id BIGINT,
    registered_at TIMESTAMP WITH TIME ZONE,
    backpack_level INTEGER DEFAULT 1,
    UNIQUE (discord_user_id)
);

CREATE TABLE IF NOT EXISTS user_data.balance (
    fk_user_id INTEGER REFERENCES user_data.user(id) ON DELETE CASCADE,
    silver BIGINT DEFAULT 0,
    star BIGINT DEFAULT 0,
    gem BIGINT DEFAULT 0,
    voucher BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_data.level (
    fk_user_id INTEGER REFERENCES user_data.user(id) ON DELETE CASCADE,
    current_level INTEGER DEFAULT 1,
    current_xp INTEGER DEFAULT 0,
    required_xp INTEGER DEFAULT 42
);

CREATE TABLE IF NOT EXISTS user_data.card (
    card_id VARCHAR(6) PRIMARY KEY,
    fk_user_id INTEGER REFERENCES user_data.user(id) ON DELETE CASCADE,
    rarity TEXT,
    condition TEXT,
    character_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    is_shiny BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    in_sleeve BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS user_data.item (
    fk_user_id INTEGER REFERENCES user_data.user(id) ON DELETE CASCADE,
    item_name TEXT,
    item_quantity INTEGER,
    UNIQUE (item_name, fk_user_id)
);

CREATE TABLE IF NOT EXISTS user_data.rewards_daily (
    fk_user_id INTEGER REFERENCES user_data.user(id) ON DELETE CASCADE,
    streak INTEGER DEFAULT 0,
    claimed_at TIMESTAMP WITH TIME ZONE,
    reset_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS user_data.rewards_vote (
    fk_user_id INTEGER REFERENCES user_data.user(id) ON DELETE CASCADE,
    streak INTEGER DEFAULT 0,
    voted_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS guild_data.config (
    discord_guild_id BIGINT PRIMARY KEY,
    toggle_notification_level_up BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS bot_data.blacklist (
    discord_user_id BIGINT PRIMARY KEY,
    reason VARCHAR(255)
);