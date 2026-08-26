from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from vera_mmu.identity import ProjectIdentity

from .knowledge_reader import AretV1KnowledgeSourcePage, _require_after_id, _require_inspection, _require_limit, _snapshot_hash
from .sqlite_schema import AretV1SchemaSnapshotInspection


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AretKnowledgeSourceReadError(ValueError):
    """Raised when a bounded ARET V1 knowledge_source page cannot be observed safely."""


class AretKnowledgeSourceProjectionError(ValueError):
    """Raised when an ARET knowledge-source page cannot be mapped without writing or inventing parents."""


@dataclass(frozen=True)
class AretV1KnowledgeSourceSourceRecord:
    """One raw legacy knowledge_source row; it is not a VERA provenance attachment."""

    source_id: str
    knowledge_id: str
    repository: str
    revision: str
    path: str
    start_line: int
    end_line: int
    section: str
    source_hash: str
    imported_at: str
    imported_by: str
    migration_batch_id: str | None


@dataclass(frozen=True)
class AretV1KnowledgeSourceSourcePage:
    """One stable-order bounded observation page from ARET V1 knowledge_source only."""

    source_path: Path
    source_snapshot_sha256: str
    records: tuple[AretV1KnowledgeSourceSourceRecord, ...]
    next_after_id: str | None
    read_state: str = "SOURCE_ROWS_OBSERVED"


@dataclass(frozen=True)
class AretV1KnowledgeSourceDraft:
    """One immutable Core provenance draft; not an attached VERA source."""

    target_identifier: str
    knowledge_identifier: str
    source_identifier: str
    payload: dict[str, object]
    legacy_import_metadata: dict[str, object]


@dataclass(frozen=True)
class AretV1KnowledgeSourceProjection:
    """One immutable non-writable projection of a bounded ARET V1 provenance page."""

    target_identity: ProjectIdentity
    request_id: str
    source_snapshot_sha256: str
    drafts: tuple[AretV1KnowledgeSourceDraft, ...]
    projection_state: str = "PROJECTED_NOT_WRITABLE"


def _read_rows(snapshot: Path, after_id: str, limit: int) -> tuple[AretV1KnowledgeSourceSourceRecord, ...]:
    try:
        connection = sqlite3.connect(f"{snapshot.as_uri()}?mode=ro&immutable=1", uri=True, isolation_level=None)
        connection.execute("PRAGMA query_only = ON")
        rows = tuple(
            connection.execute(
                "SELECT id, knowledge_id, source_repository, source_revision, source_path, source_start_line, source_end_line, "
                "source_section, source_hash, imported_at, imported_by, migration_batch_id "
                "FROM knowledge_source WHERE id > ? ORDER BY id LIMIT ?",
                (after_id, limit + 1),
            )
        )
    except sqlite3.Error as exc:
        raise AretKnowledgeSourceReadError("Lecture paginée de knowledge_source ARET V1 impossible.") from exc
    finally:
        try:
            connection.close()
        except UnboundLocalError:
            pass
    records: list[AretV1KnowledgeSourceSourceRecord] = []
    for row in rows:
        if (
            not all(isinstance(row[index], str) and row[index].strip() for index in (0, 1, 2, 3, 4, 7, 8, 9, 10))
            or row[11] is not None and (not isinstance(row[11], str) or not row[11].strip())
            or isinstance(row[5], bool)
            or isinstance(row[6], bool)
            or not isinstance(row[5], int)
            or not isinstance(row[6], int)
            or row[5] < 1
            or row[6] < row[5]
            or not _SHA256_RE.fullmatch(str(row[8]))
        ):
            raise AretKnowledgeSourceReadError("Une ligne knowledge_source ARET V1 est invalide ou non bornée.")
        records.append(AretV1KnowledgeSourceSourceRecord(*row))
    return tuple(records)


def read_aret_v1_knowledge_source_page(
    *,
    source_root: str | Path,
    schema_inspection: AretV1SchemaSnapshotInspection,
    after_id: str | None,
    limit: int,
) -> AretV1KnowledgeSourceSourcePage:
    """Observe one ARET V1 provenance page only; no target read, projection or write occurs."""
    try:
        snapshot, inspection = _require_inspection(source_root, schema_inspection)
        cursor = _require_after_id(after_id)
        bounded_limit = _require_limit(limit)
    except ValueError as exc:
        raise AretKnowledgeSourceReadError("Préconditions de lecture knowledge_source invalides.") from exc
    before_hash = _snapshot_hash(snapshot)
    if before_hash != inspection.source_snapshot_sha256:
        raise AretKnowledgeSourceReadError("Le snapshot knowledge_source ne correspond plus au hash de l’inspection vérifiée.")
    rows = _read_rows(snapshot, cursor, bounded_limit)
    if _snapshot_hash(snapshot) != before_hash:
        raise AretKnowledgeSourceReadError("Le snapshot a changé pendant la lecture knowledge_source.")
    records = rows[:bounded_limit]
    return AretV1KnowledgeSourceSourcePage(snapshot, before_hash, records, records[-1].source_id if len(rows) > bounded_limit else None)


def project_aret_v1_knowledge_source_page(
    *,
    target_identity: ProjectIdentity,
    knowledge_page: AretV1KnowledgeSourcePage,
    source_page: AretV1KnowledgeSourceSourcePage,
    request_id: str,
) -> AretV1KnowledgeSourceProjection:
    """Project one provenance page only when all its legacy parents are in the supplied attested knowledge set."""
    if (
        not isinstance(target_identity, ProjectIdentity)
        or not isinstance(knowledge_page, AretV1KnowledgeSourcePage)
        or not isinstance(source_page, AretV1KnowledgeSourceSourcePage)
        or knowledge_page.source_snapshot_sha256 != source_page.source_snapshot_sha256
        or not isinstance(request_id, str)
        or not request_id
        or len(request_id) > 128
        or any(char in request_id for char in ("\x00", "\r", "\n"))
    ):
        raise AretKnowledgeSourceProjectionError("Binding de projection knowledge_source invalide.")
    known_knowledge_ids = {record.source_id for record in knowledge_page.records}
    if not known_knowledge_ids:
        raise AretKnowledgeSourceProjectionError("Le jeu de parents knowledge attestés ne peut pas être vide.")
    drafts: list[AretV1KnowledgeSourceDraft] = []
    for record in source_page.records:
        if record.knowledge_id not in known_knowledge_ids:
            raise AretKnowledgeSourceProjectionError("Une provenance ARET référence une knowledge absente du jeu attesté.")
        if (
            not _SHA256_RE.fullmatch(record.source_hash)
            or not record.path
            or record.path.startswith(("/", "\\"))
            or "\\" in record.path
            or any(part in {"", ".", ".."} for part in record.path.split("/"))
        ):
            raise AretKnowledgeSourceProjectionError("Une provenance ARET n’est pas projetable vers le contrat Core fermé.")
        drafts.append(
            AretV1KnowledgeSourceDraft(
                target_identifier=f"aret-knowledge-source--{record.source_id}",
                knowledge_identifier=f"aret-knowledge--{record.knowledge_id}",
                source_identifier=record.source_id,
                payload={
                    "repository": record.repository,
                    "revision": record.revision,
                    "path": record.path,
                    "start_line": record.start_line,
                    "end_line": record.end_line,
                    "section": record.section,
                    "source_hash": record.source_hash,
                },
                legacy_import_metadata={
                    "imported_at": record.imported_at,
                    "imported_by": record.imported_by,
                    "migration_batch_id": record.migration_batch_id,
                },
            )
        )
    target_ids = tuple(draft.target_identifier for draft in drafts)
    source_ids = tuple(draft.source_identifier for draft in drafts)
    if not 1 <= len(drafts) <= 100 or len(set(target_ids)) != len(target_ids) or len(set(source_ids)) != len(source_ids):
        raise AretKnowledgeSourceProjectionError("La page de provenance projetée doit être bornée et sans identifiants ambigus.")
    return AretV1KnowledgeSourceProjection(target_identity, request_id, source_page.source_snapshot_sha256, tuple(drafts))
