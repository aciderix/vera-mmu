CREATE TABLE import_batch (
    id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_snapshot_sha256 TEXT NOT NULL,
    mapping_id TEXT NOT NULL,
    target_type_id TEXT NOT NULL REFERENCES entity_type(id),
    fingerprint_sha256 TEXT NOT NULL,
    committed_at TEXT NOT NULL,
    committed_by TEXT NOT NULL,
    CHECK (length(source_system) BETWEEN 1 AND 128),
    CHECK (length(source_snapshot_sha256) = 64),
    CHECK (length(mapping_id) BETWEEN 1 AND 128),
    CHECK (length(fingerprint_sha256) = 64)
) STRICT;

CREATE TABLE import_batch_entity (
    batch_id TEXT NOT NULL REFERENCES import_batch(id) ON DELETE RESTRICT,
    source_identifier TEXT NOT NULL,
    entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE RESTRICT,
    PRIMARY KEY (batch_id, source_identifier),
    UNIQUE(batch_id, entity_id),
    UNIQUE(source_identifier, entity_id),
    CHECK (length(source_identifier) BETWEEN 1 AND 512)
) STRICT;

CREATE INDEX idx_import_batch_source ON import_batch(source_system, source_snapshot_sha256, mapping_id);
CREATE INDEX idx_import_batch_entity_entity ON import_batch_entity(entity_id);

CREATE TRIGGER reject_import_batch_update
BEFORE UPDATE ON import_batch
BEGIN
    SELECT RAISE(ABORT, 'import_batch is immutable');
END;

CREATE TRIGGER reject_import_batch_delete
BEFORE DELETE ON import_batch
BEGIN
    SELECT RAISE(ABORT, 'import_batch is append-only');
END;

CREATE TRIGGER reject_import_batch_entity_update
BEFORE UPDATE ON import_batch_entity
BEGIN
    SELECT RAISE(ABORT, 'import_batch_entity is immutable');
END;

CREATE TRIGGER reject_import_batch_entity_delete
BEFORE DELETE ON import_batch_entity
BEGIN
    SELECT RAISE(ABORT, 'import_batch_entity is append-only');
END;
