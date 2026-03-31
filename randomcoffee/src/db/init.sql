PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    contact_info TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1, -- bool
    CHECK (length(email) BETWEEN 1 AND 256),
    CHECK (length(name) BETWEEN 1 AND 256)
);

CREATE TABLE IF NOT EXISTS user_interests (
    email TEXT REFERENCES users ON DELETE CASCADE,
    interest_id INTEGER NOT NULL  -- to be defined in Python
);

CREATE TABLE IF NOT EXISTS pairings (
    email1 TEXT REFERENCES users,
    email2 TEXT REFERENCES users,
    meeting_happened INTEGER NOT NULL DEFAULT 0, -- bool
    CHECK (email1 != email2)
);
