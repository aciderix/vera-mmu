CREATE TABLE IF NOT EXISTS work_item (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    type TEXT NOT NULL CHECK (type IN ('GOAL', 'EPIC', 'WORK_ITEM', 'SUBTASK')),
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 1024),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 4096),
    status TEXT NOT NULL DEFAULT 'PLANNED' CHECK (status = 'PLANNED'),
    priority INTEGER,
    parent_id TEXT REFERENCES work_item(id) ON DELETE RESTRICT,
    assignee TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL CHECK (updated_at = created_at),
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    CHECK (parent_id IS NULL OR parent_id != id)
) STRICT;

CREATE TRIGGER IF NOT EXISTS work_item_no_update
BEFORE UPDATE ON work_item
BEGIN
    SELECT RAISE(ABORT, 'work item records are append-only');
END;

CREATE TRIGGER IF NOT EXISTS work_item_no_delete
BEFORE DELETE ON work_item
BEGIN
    SELECT RAISE(ABORT, 'work item records are append-only');
END;
