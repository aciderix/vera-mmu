CREATE TABLE IF NOT EXISTS work_lifecycle_event (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    work_item_id TEXT NOT NULL REFERENCES work_item(id) ON DELETE RESTRICT,
    sequence INTEGER NOT NULL CHECK (sequence >= 1),
    event TEXT NOT NULL CHECK (event IN ('START', 'COMPLETE', 'CANCEL')),
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 1 AND 4096),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    UNIQUE (work_item_id, sequence)
) STRICT;
CREATE TRIGGER IF NOT EXISTS work_lifecycle_event_no_update BEFORE UPDATE ON work_lifecycle_event BEGIN SELECT RAISE(ABORT, 'work lifecycle events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS work_lifecycle_event_no_delete BEFORE DELETE ON work_lifecycle_event BEGIN SELECT RAISE(ABORT, 'work lifecycle events are append-only'); END;
