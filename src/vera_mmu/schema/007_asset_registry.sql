CREATE TABLE IF NOT EXISTS asset (
    id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE CHECK (
        length(content_hash) = 64
        AND content_hash NOT GLOB '*[^0123456789abcdef]*'
    ),
    byte_length INTEGER NOT NULL CHECK (byte_length BETWEEN 1 AND 1048576),
    media_type TEXT NOT NULL CHECK (length(media_type) BETWEEN 3 AND 255),
    content BLOB NOT NULL CHECK (length(content) = byte_length),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;

CREATE TRIGGER IF NOT EXISTS reject_asset_rewrite
BEFORE UPDATE ON asset
BEGIN
    SELECT RAISE(ABORT, 'asset is append-only; rewriting is forbidden');
END;

CREATE TRIGGER IF NOT EXISTS reject_asset_delete
BEFORE DELETE ON asset
BEGIN
    SELECT RAISE(ABORT, 'asset is append-only; deletion is forbidden');
END;
