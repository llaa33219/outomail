PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key TEXT NOT NULL UNIQUE,
    name TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    last_used_at INTEGER
);

CREATE TABLE IF NOT EXISTS mailboxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    uidvalidity INTEGER NOT NULL DEFAULT 1,
    uidnext INTEGER NOT NULL DEFAULT 1,
    special_use TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mailbox_id INTEGER NOT NULL REFERENCES mailboxes(id) ON DELETE CASCADE,
    uid INTEGER NOT NULL,
    message_id TEXT,
    subject TEXT,
    from_addr TEXT,
    to_addr TEXT,
    cc_addr TEXT,
    date INTEGER,
    size INTEGER,
    flags TEXT NOT NULL DEFAULT '',
    headers TEXT,
    body_text TEXT,
    body_html TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    filename TEXT,
    content_type TEXT,
    size INTEGER,
    storage_path TEXT,
    content_id TEXT,
    disposition TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_messages_mailbox_date ON messages(mailbox_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_messages_uid ON messages(mailbox_id, uid);
CREATE INDEX IF NOT EXISTS idx_messages_message_id ON messages(message_id);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    subject,
    body_text,
    from_addr,
    to_addr,
    content='messages',
    content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, subject, body_text, from_addr, to_addr)
    VALUES (new.id, new.subject, new.body_text, new.from_addr, new.to_addr);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, subject, body_text, from_addr, to_addr)
    VALUES ('delete', old.id, old.subject, old.body_text, old.from_addr, old.to_addr);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, subject, body_text, from_addr, to_addr)
    VALUES ('delete', old.id, old.subject, old.body_text, old.from_addr, old.to_addr);
    INSERT INTO messages_fts(rowid, subject, body_text, from_addr, to_addr)
    VALUES (new.id, new.subject, new.body_text, new.from_addr, new.to_addr);
END;
