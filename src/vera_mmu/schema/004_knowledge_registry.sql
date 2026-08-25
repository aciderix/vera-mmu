CREATE TABLE IF NOT EXISTS knowledge_type (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 64),
    label TEXT NOT NULL CHECK (length(label) BETWEEN 1 AND 256),
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;

CREATE TABLE IF NOT EXISTS knowledge (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    type_id TEXT NOT NULL REFERENCES knowledge_type(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'OBSERVED', 'HYPOTHESIS', 'CONFLICTING')),
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 512),
    content TEXT NOT NULL CHECK (length(content) BETWEEN 1 AND 1048576),
    content_hash TEXT NOT NULL CHECK (length(content_hash) = 64),
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json) AND json_type(metadata_json) = 'object'),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_knowledge_type_status ON knowledge(type_id, status, id);

CREATE TRIGGER IF NOT EXISTS reject_knowledge_type_rewrite
BEFORE UPDATE ON knowledge_type
BEGIN
    SELECT RAISE(ABORT, 'knowledge_type is append-only; register a new type instead');
END;

CREATE TRIGGER IF NOT EXISTS reject_knowledge_type_delete
BEFORE DELETE ON knowledge_type
BEGIN
    SELECT RAISE(ABORT, 'knowledge_type is append-only; deletion is forbidden');
END;

CREATE TRIGGER IF NOT EXISTS reject_knowledge_rewrite
BEFORE UPDATE ON knowledge
BEGIN
    SELECT RAISE(ABORT, 'knowledge is append-only; append a new knowledge record instead');
END;

CREATE TRIGGER IF NOT EXISTS reject_knowledge_delete
BEFORE DELETE ON knowledge
BEGIN
    SELECT RAISE(ABORT, 'knowledge is append-only; deletion is forbidden');
END;
