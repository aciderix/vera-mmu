CREATE TABLE IF NOT EXISTS admission_gate_policy (
    gate_id TEXT PRIMARY KEY REFERENCES admission_gate(id) ON DELETE RESTRICT,
    mode TEXT NOT NULL CHECK (mode IN ('ALL', 'ANY', 'AT_LEAST')),
    minimum_admissions INTEGER CHECK (minimum_admissions IS NULL OR minimum_admissions >= 1),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    CHECK (
        (mode IN ('ALL', 'ANY') AND minimum_admissions IS NULL)
        OR (mode = 'AT_LEAST' AND minimum_admissions IS NOT NULL)
    )
) STRICT;
CREATE TRIGGER IF NOT EXISTS admission_gate_policy_no_update BEFORE UPDATE ON admission_gate_policy BEGIN SELECT RAISE(ABORT, 'admission gate policies are append-only'); END;
CREATE TRIGGER IF NOT EXISTS admission_gate_policy_no_delete BEFORE DELETE ON admission_gate_policy BEGIN SELECT RAISE(ABORT, 'admission gate policies are append-only'); END;
