CREATE TABLE IF NOT EXISTS knowledge_supersession (
    predecessor_id TEXT PRIMARY KEY REFERENCES knowledge(id) ON DELETE RESTRICT,
    successor_id TEXT NOT NULL UNIQUE REFERENCES knowledge(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    CHECK (predecessor_id <> successor_id)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_knowledge_supersession_successor
ON knowledge_supersession(successor_id);

CREATE TRIGGER IF NOT EXISTS reject_knowledge_supersession_rewrite
BEFORE UPDATE ON knowledge_supersession
BEGIN
    SELECT RAISE(ABORT, 'knowledge_supersession is append-only; rewriting is forbidden');
END;

CREATE TRIGGER IF NOT EXISTS reject_knowledge_supersession_delete
BEFORE DELETE ON knowledge_supersession
BEGIN
    SELECT RAISE(ABORT, 'knowledge_supersession is append-only; deletion is forbidden');
END;
