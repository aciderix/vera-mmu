CREATE TABLE IF NOT EXISTS knowledge_source (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    knowledge_id TEXT NOT NULL REFERENCES knowledge(id) ON DELETE RESTRICT,
    source_repository TEXT NOT NULL CHECK (length(source_repository) BETWEEN 1 AND 512),
    source_revision TEXT NOT NULL CHECK (length(source_revision) BETWEEN 1 AND 512),
    source_path TEXT NOT NULL CHECK (length(source_path) BETWEEN 1 AND 4096),
    source_start_line INTEGER NOT NULL CHECK (source_start_line > 0),
    source_end_line INTEGER NOT NULL CHECK (source_end_line >= source_start_line),
    source_section TEXT NOT NULL CHECK (length(source_section) BETWEEN 1 AND 1024),
    source_hash TEXT NOT NULL CHECK (length(source_hash) = 64),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    UNIQUE(knowledge_id, source_repository, source_revision, source_path, source_start_line, source_end_line)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_knowledge_source_knowledge
ON knowledge_source(knowledge_id, source_path, source_start_line, source_end_line, id);

CREATE TRIGGER IF NOT EXISTS reject_knowledge_source_rewrite
BEFORE UPDATE ON knowledge_source
BEGIN
    SELECT RAISE(ABORT, 'knowledge_source is append-only; attach a new source instead');
END;

CREATE TRIGGER IF NOT EXISTS reject_knowledge_source_delete
BEFORE DELETE ON knowledge_source
BEGIN
    SELECT RAISE(ABORT, 'knowledge_source is append-only; deletion is forbidden');
END;
