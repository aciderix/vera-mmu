CREATE TABLE IF NOT EXISTS relation_type (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 64),
    label TEXT NOT NULL CHECK (length(label) BETWEEN 1 AND 256),
    description TEXT NOT NULL DEFAULT '',
    from_types_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(from_types_json) AND json_type(from_types_json) = 'array'),
    to_types_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(to_types_json) AND json_type(to_types_json) = 'array'),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;

CREATE TABLE IF NOT EXISTS relation (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    relation_type_id TEXT NOT NULL REFERENCES relation_type(id) ON DELETE RESTRICT,
    from_entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE RESTRICT,
    to_entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    UNIQUE(from_entity_id, relation_type_id, to_entity_id)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_relation_from_type ON relation(from_entity_id, relation_type_id, id);
CREATE INDEX IF NOT EXISTS idx_relation_to_type ON relation(to_entity_id, relation_type_id, id);

CREATE TRIGGER IF NOT EXISTS reject_relation_type_rewrite
BEFORE UPDATE ON relation_type
BEGIN
    SELECT RAISE(ABORT, 'relation_type is append-only; register a new type instead');
END;

CREATE TRIGGER IF NOT EXISTS reject_relation_type_delete
BEFORE DELETE ON relation_type
BEGIN
    SELECT RAISE(ABORT, 'relation_type is append-only; deletion is forbidden');
END;

CREATE TRIGGER IF NOT EXISTS reject_relation_rewrite
BEFORE UPDATE ON relation
BEGIN
    SELECT RAISE(ABORT, 'relation is append-only; create a new relation instead');
END;

CREATE TRIGGER IF NOT EXISTS reject_relation_delete
BEFORE DELETE ON relation
BEGIN
    SELECT RAISE(ABORT, 'relation is append-only; deletion is forbidden');
END;
