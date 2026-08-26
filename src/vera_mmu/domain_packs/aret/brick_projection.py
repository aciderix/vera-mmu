from __future__ import annotations

from dataclasses import dataclass

from vera_mmu.identity import ProjectIdentity

from .brick_reader import AretV1BrickSourcePage


_STATES = frozenset({"PLANNED", "ACTIVE", "BLOCKED", "DONE", "OBSOLETE"})


class AretBrickProjectionError(ValueError):
    """Raised when a raw ARET brick cannot be projected deterministically without writing."""


@dataclass(frozen=True)
class AretV1WorkItemDraft:
    target_identifier: str
    item_type: str
    title: str
    description: str
    priority: int
    metadata: dict[str, object]


@dataclass(frozen=True)
class AretV1BrickProjection:
    target_identity: ProjectIdentity
    request_id: str
    source_snapshot_sha256: str
    drafts: tuple[AretV1WorkItemDraft, ...]
    projection_state: str = "PROJECTED_NOT_WRITABLE"


def project_aret_v1_brick_page(*, target_identity: ProjectIdentity, source_page: AretV1BrickSourcePage, request_id: str) -> AretV1BrickProjection:
    if not isinstance(target_identity, ProjectIdentity) or not isinstance(source_page, AretV1BrickSourcePage) or not isinstance(request_id, str) or not request_id:
        raise AretBrickProjectionError("Projection brick invalide.")
    drafts = []
    for row in source_page.records:
        if (not isinstance(row.source_id, str) or not row.source_id or "/" in row.source_id or "\\" in row.source_id or row.state not in _STATES or isinstance(row.priority, bool) or not isinstance(row.priority, int) or not 1 <= row.priority <= 5):
            raise AretBrickProjectionError("Ligne brick ARET non projetable de manière déterministe.")
        drafts.append(AretV1WorkItemDraft(f"aret-brick--{row.source_id}", "WORK_ITEM", row.title, row.description, row.priority, {"source": {"domain_pack": "aret-v1", "legacy_table": "brick", "source_id": row.source_id, "source_snapshot_sha256": source_page.source_snapshot_sha256, "component_id": row.component_id, "state": row.state, "milestone": row.milestone, "target_platform": row.target_platform, "priority": row.priority, "source_created_at": row.created_at, "source_created_by": row.created_by}}))
    return AretV1BrickProjection(target_identity, request_id, source_page.source_snapshot_sha256, tuple(drafts))
