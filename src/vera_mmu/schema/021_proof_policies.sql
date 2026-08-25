CREATE TABLE IF NOT EXISTS proof_policy (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    algorithm TEXT NOT NULL CHECK (algorithm = 'HMAC_SHA256'),
    hmac_required INTEGER NOT NULL CHECK (hmac_required IN (0, 1)),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE TRIGGER IF NOT EXISTS proof_policy_no_update BEFORE UPDATE ON proof_policy BEGIN SELECT RAISE(ABORT, 'proof policy is append-only'); END;
CREATE TRIGGER IF NOT EXISTS proof_policy_no_delete BEFORE DELETE ON proof_policy BEGIN SELECT RAISE(ABORT, 'proof policy is append-only'); END;
