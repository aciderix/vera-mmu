from __future__ import annotations

from dataclasses import dataclass
import re

from vera_mmu.identity import ProjectIdentity

from .knowledge_reader import AretV1KnowledgeSourcePage


_SOURCE_TYPES = frozenset({"ARCHITECTURE", "DECISION", "DISCOVERY", "FORENSIC", "MEASUREMENT", "OBSERVATION", "RULE", "STATE"})
_SOURCE_STATUSES = frozenset({"ACTIVE", "OBSERVED", "SUPERSEDED"})
_TARGET_TYPE_ID = "aret-legacy-knowledge"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AretKnowledgeProjectionError(ValueError):
    """Raised when an ARET knowledge page cannot be projected deterministically without writing."""


@dataclass(frozen=True)
class AretV1KnowledgeDraft:
    """One immutable target knowledge draft; not an imported Core record."""

    target_identifier: str
    type_id: str
    status: str
    title: str
    content: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class AretV1KnowledgeProjection:
    """One immutable, non-writable projection of a bounded ARET V1 knowledge page."""

    target_identity: ProjectIdentity
    request_id: str
    source_snapshot_sha256: str
    drafts: tuple[AretV1KnowledgeDraft, ...]
    projection_state: str = "PROJECTED_NOT_WRITABLE"


def _core_status(legacy_status: str) -> str:
    if legacy_status == "ACTIVE":
        return "ACTIVE"
    if legacy_status in {"OBSERVED", "SUPERSEDED"}:
        return "OBSERVED"
    raise AretKnowledgeProjectionError("Statut knowledge ARET V1 hors mapping fermé.")


def project_aret_v1_knowledge_page(
    *,
    target_identity: ProjectIdentity,
    source_page: AretV1KnowledgeSourcePage,
    request_id: str,
) -> AretV1KnowledgeProjection:
    """Project one observed knowledge page while preserving legacy semantics as metadata only."""
    if not isinstance(target_identity, ProjectIdentity) or not isinstance(source_page, AretV1KnowledgeSourcePage):
        raise AretKnowledgeProjectionError("Projection knowledge invalide.")
    if not isinstance(request_id, str) or not request_id or len(request_id) > 128 or any(char in request_id for char in ("\x00", "\r", "\n")):
        raise AretKnowledgeProjectionError("request_id knowledge invalide.")
    if not _SHA256_RE.fullmatch(source_page.source_snapshot_sha256):
        raise AretKnowledgeProjectionError("Hash snapshot knowledge invalide.")
    drafts: list[AretV1KnowledgeDraft] = []
    for row in source_page.records:
        if (
            not isinstance(row.source_id, str)
            or not row.source_id
            or "/" in row.source_id
            or "\\" in row.source_id
            or row.source_type not in _SOURCE_TYPES
            or row.source_status not in _SOURCE_STATUSES
            or not isinstance(row.title, str)
            or not row.title.strip()
            or len(row.title) > 512
            or not isinstance(row.content, str)
            or not row.content.strip()
            or len(row.content) > 1048576
            or isinstance(row.version, bool)
            or not isinstance(row.version, int)
            or row.version < 1
            or not _SHA256_RE.fullmatch(row.content_hash)
        ):
            raise AretKnowledgeProjectionError("Ligne knowledge ARET V1 non projetable de manière déterministe.")
        metadata = {
            "source": {
                "domain_pack": "aret-v1",
                "legacy_table": "knowledge",
                "source_id": row.source_id,
                "source_snapshot_sha256": source_page.source_snapshot_sha256,
                "legacy_type": row.source_type,
                "legacy_status": row.source_status,
                "component_id": row.component_id,
                "function_id": row.function_id,
                "brick_id": row.brick_id,
                "supersedes_id": row.supersedes_id,
                "version": row.version,
                "content_hash": row.content_hash,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "created_by": row.created_by,
                "effective_at": row.effective_at,
            }
        }
        drafts.append(
            AretV1KnowledgeDraft(
                target_identifier=f"aret-knowledge--{row.source_id}",
                type_id=_TARGET_TYPE_ID,
                status=_core_status(row.source_status),
                title=row.title,
                content=row.content,
                metadata=metadata,
            )
        )
    identifiers = tuple(draft.target_identifier for draft in drafts)
    if len(set(identifiers)) != len(identifiers):
        raise AretKnowledgeProjectionError("Projection knowledge porte des identifiants cible ambigus.")
    return AretV1KnowledgeProjection(target_identity, request_id, source_page.source_snapshot_sha256, tuple(drafts))
