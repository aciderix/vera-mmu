CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version > 0),
    name TEXT NOT NULL UNIQUE,
    checksum TEXT NOT NULL CHECK (length(checksum) = 64),
    applied_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS store_metadata (
    key TEXT PRIMARY KEY CHECK (length(key) BETWEEN 1 AND 128),
    value_json TEXT NOT NULL CHECK (json_valid(value_json)),
    updated_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS store_audit (
    id INTEGER PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    action TEXT NOT NULL CHECK (length(action) BETWEEN 1 AND 128),
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json))
) STRICT;

CREATE INDEX IF NOT EXISTS idx_store_audit_occurred_at ON store_audit(occurred_at, id);
