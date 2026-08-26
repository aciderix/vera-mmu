CREATE TABLE IF NOT EXISTS admission_gate_requirement (
    gate_id TEXT NOT NULL REFERENCES admission_gate(id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    PRIMARY KEY (gate_id, evidence_id)
) STRICT;
CREATE TRIGGER IF NOT EXISTS admission_gate_requirement_no_update BEFORE UPDATE ON admission_gate_requirement BEGIN SELECT RAISE(ABORT, 'gate requirements are append-only'); END;
CREATE TRIGGER IF NOT EXISTS admission_gate_requirement_no_delete BEFORE DELETE ON admission_gate_requirement BEGIN SELECT RAISE(ABORT, 'gate requirements are append-only'); END;
