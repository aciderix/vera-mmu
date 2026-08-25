CREATE TABLE IF NOT EXISTS entity_type (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 64),
    label TEXT NOT NULL CHECK (length(label) BETWEEN 1 AND 256),
    description TEXT NOT NULL DEFAULT '',
    schema_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(schema_json)),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;

CREATE TABLE IF NOT EXISTS entity (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    type_id TEXT NOT NULL REFERENCES entity_type(id) ON DELETE RESTRICT,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 1024),
    description TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_entity_type_id ON entity(type_id, id);
