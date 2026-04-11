PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    contact_info TEXT NOT NULL,
    about_me TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1, -- bool
    CHECK (length(email) BETWEEN 1 AND 256),
    CHECK (length(name) BETWEEN 1 AND 256)
);

CREATE TABLE IF NOT EXISTS user_interests (
    id TEXT REFERENCES users ON DELETE CASCADE,
    interest_id INTEGER NOT NULL  -- to be defined in Python
);

CREATE TABLE IF NOT EXISTS pairings ( -- this table stores one row per pair
    pair_id TEXT PRIMARY KEY,
    id1 TEXT REFERENCES users,
    id2 TEXT REFERENCES users,
    created_at TEXT NOT NULL,
    meeting_happened INTEGER NOT NULL DEFAULT 0, -- bool
    CHECK (id1 != id2)
);

CREATE TABLE IF NOT EXISTS otps (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
