CREATE TABLE IF NOT EXISTS symbol (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE RESTRICT,
    kind TEXT NOT NULL CHECK (length(kind) BETWEEN 1 AND 64),
    path TEXT NOT NULL DEFAULT '' CHECK (length(path) <= 2048),
    identifier TEXT NOT NULL CHECK (length(identifier) BETWEEN 1 AND 512),
    signature TEXT NOT NULL DEFAULT '' CHECK (length(signature) <= 2048),
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    UNIQUE(entity_id, path, identifier)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_symbol_entity_id ON symbol(entity_id, id);

CREATE TRIGGER IF NOT EXISTS symbol_no_update
BEFORE UPDATE ON symbol
BEGIN
    SELECT RAISE(ABORT, 'symbol records are append-only');
END;

CREATE TRIGGER IF NOT EXISTS symbol_no_delete
BEFORE DELETE ON symbol
BEGIN
    SELECT RAISE(ABORT, 'symbol records are append-only');
END;
