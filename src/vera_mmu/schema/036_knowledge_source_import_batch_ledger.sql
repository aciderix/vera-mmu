CREATE TABLE knowledge_source_import_batch (
    id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_snapshot_sha256 TEXT NOT NULL,
    mapping_id TEXT NOT NULL,
    fingerprint_sha256 TEXT NOT NULL,
    committed_at TEXT NOT NULL,
    committed_by TEXT NOT NULL,
    CHECK (length(source_system) BETWEEN 1 AND 128),
    CHECK (length(source_snapshot_sha256) = 64),
    CHECK (length(mapping_id) BETWEEN 1 AND 128),
    CHECK (length(fingerprint_sha256) = 64)
) STRICT;

CREATE TABLE knowledge_source_import_batch_record (
    batch_id TEXT NOT NULL REFERENCES knowledge_source_import_batch(id) ON DELETE RESTRICT,
    source_identifier TEXT NOT NULL,
    target_identifier TEXT NOT NULL,
    PRIMARY KEY (batch_id, source_identifier),
    UNIQUE(batch_id, target_identifier),
    CHECK (length(source_identifier) BETWEEN 1 AND 512),
    CHECK (length(target_identifier) BETWEEN 1 AND 512)
) STRICT;

CREATE INDEX idx_knowledge_source_import_batch_source ON knowledge_source_import_batch(source_system, source_snapshot_sha256, mapping_id);
CREATE INDEX idx_knowledge_source_import_batch_record_target ON knowledge_source_import_batch_record(target_identifier);

CREATE TRIGGER reject_knowledge_source_import_batch_update BEFORE UPDATE ON knowledge_source_import_batch BEGIN SELECT RAISE(ABORT, 'knowledge_source_import_batch is immutable'); END;
CREATE TRIGGER reject_knowledge_source_import_batch_delete BEFORE DELETE ON knowledge_source_import_batch BEGIN SELECT RAISE(ABORT, 'knowledge_source_import_batch is append-only'); END;
CREATE TRIGGER reject_knowledge_source_import_batch_record_update BEFORE UPDATE ON knowledge_source_import_batch_record BEGIN SELECT RAISE(ABORT, 'knowledge_source_import_batch_record is immutable'); END;
CREATE TRIGGER reject_knowledge_source_import_batch_record_delete BEFORE DELETE ON knowledge_source_import_batch_record BEGIN SELECT RAISE(ABORT, 'knowledge_source_import_batch_record is append-only'); END;
