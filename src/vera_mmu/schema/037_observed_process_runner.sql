CREATE TABLE capability_contract_m4_037 (
    capability_id TEXT PRIMARY KEY REFERENCES capability(id) ON DELETE RESTRICT,
    runner_profile TEXT NOT NULL CHECK (runner_profile IN ('NOOP', 'EVIDENCE_HASH', 'EVIDENCE_FIELDS', 'OBSERVED_PROCESS')),
    network_policy TEXT NOT NULL CHECK (network_policy = 'DENY_NETWORK'),
    timeout_seconds INTEGER NOT NULL CHECK (timeout_seconds BETWEEN 1 AND 3600),
    parameter_schema_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(parameter_schema_json)),
    yields_proof INTEGER NOT NULL DEFAULT 0 CHECK (yields_proof IN (0, 1)),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;
INSERT INTO capability_contract_m4_037(capability_id, runner_profile, network_policy, timeout_seconds, parameter_schema_json, yields_proof, created_at, created_by)
SELECT capability_id, runner_profile, network_policy, timeout_seconds, parameter_schema_json, yields_proof, created_at, created_by FROM capability_contract;
DROP TRIGGER capability_contract_no_update;
DROP TRIGGER capability_contract_no_delete;
DROP TABLE capability_contract;
ALTER TABLE capability_contract_m4_037 RENAME TO capability_contract;
CREATE TRIGGER capability_contract_no_update BEFORE UPDATE ON capability_contract BEGIN SELECT RAISE(ABORT, 'capability contracts are append-only'); END;
CREATE TRIGGER capability_contract_no_delete BEFORE DELETE ON capability_contract BEGIN SELECT RAISE(ABORT, 'capability contracts are append-only'); END;
