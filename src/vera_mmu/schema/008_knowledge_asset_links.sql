CREATE TABLE IF NOT EXISTS knowledge_asset_link (
    knowledge_id TEXT NOT NULL REFERENCES knowledge(id) ON DELETE RESTRICT,
    asset_id TEXT NOT NULL REFERENCES asset(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    PRIMARY KEY (knowledge_id, asset_id)
) STRICT;

CREATE TRIGGER IF NOT EXISTS reject_knowledge_asset_link_rewrite
BEFORE UPDATE ON knowledge_asset_link
BEGIN
    SELECT RAISE(ABORT, 'knowledge asset link is append-only; rewriting is forbidden');
END;

CREATE TRIGGER IF NOT EXISTS reject_knowledge_asset_link_delete
BEFORE DELETE ON knowledge_asset_link
BEGIN
    SELECT RAISE(ABORT, 'knowledge asset link is append-only; deletion is forbidden');
END;
