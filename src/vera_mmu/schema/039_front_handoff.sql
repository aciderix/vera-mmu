CREATE TABLE front_revision (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 128),
    previous_front_id TEXT REFERENCES front_revision(id) ON DELETE RESTRICT,
    profile_hash TEXT NOT NULL CHECK (length(profile_hash) = 64),
    fields_json TEXT NOT NULL CHECK (json_valid(fields_json)),
    fields_hash TEXT NOT NULL CHECK (length(fields_hash) = 64),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE INDEX front_revision_latest_idx ON front_revision(created_at DESC, id DESC);
CREATE TRIGGER front_revision_no_update BEFORE UPDATE ON front_revision BEGIN SELECT RAISE(ABORT, 'front revisions are append-only'); END;
CREATE TRIGGER front_revision_no_delete BEFORE DELETE ON front_revision BEGIN SELECT RAISE(ABORT, 'front revisions are append-only'); END;

CREATE TABLE handoff (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 128),
    front_revision_id TEXT NOT NULL REFERENCES front_revision(id) ON DELETE RESTRICT,
    profile_hash TEXT NOT NULL CHECK (length(profile_hash) = 64),
    resume_contract_hash TEXT NOT NULL CHECK (length(resume_contract_hash) = 64),
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
    payload_hash TEXT NOT NULL CHECK (length(payload_hash) = 64),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE INDEX handoff_latest_idx ON handoff(created_at DESC, id DESC);
CREATE TRIGGER handoff_no_update BEFORE UPDATE ON handoff BEGIN SELECT RAISE(ABORT, 'handoffs are append-only'); END;
CREATE TRIGGER handoff_no_delete BEFORE DELETE ON handoff BEGIN SELECT RAISE(ABORT, 'handoffs are append-only'); END;
