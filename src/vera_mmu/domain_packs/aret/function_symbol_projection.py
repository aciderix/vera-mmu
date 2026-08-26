from __future__ import annotations

from dataclasses import dataclass
import re

from vera_mmu.identity import ProjectIdentity

from .function_symbol_reader import AretV1FunctionSymbolSourcePage


_SAFE = re.compile(r"^[A-Za-z0-9._-]+$")


class AretFunctionSymbolProjectionError(ValueError):
    """Raised when a raw function-symbol page cannot be mapped deterministically without writing."""


@dataclass(frozen=True)
class AretV1SymbolDraft:
    target_identifier: str
    owner_entity_id: str
    kind: str
    path: str
    identifier: str
    signature: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class AretV1FunctionSymbolProjection:
    target_identity: ProjectIdentity
    request_id: str
    source_snapshot_sha256: str
    drafts: tuple[AretV1SymbolDraft, ...]
    projection_state: str = "PROJECTED_NOT_WRITABLE"


def project_aret_v1_function_symbol_page(*, target_identity: ProjectIdentity, source_page: AretV1FunctionSymbolSourcePage, request_id: str) -> AretV1FunctionSymbolProjection:
    if not isinstance(target_identity, ProjectIdentity) or not isinstance(source_page, AretV1FunctionSymbolSourcePage) or not isinstance(request_id, str) or not request_id:
        raise AretFunctionSymbolProjectionError("Projection function_symbol invalide.")
    drafts = []
    for record in source_page.records:
        parts = (record.source_id, record.component_id, record.module, record.symbol, record.calling_convention, record.created_at, record.created_by)
        if not all(isinstance(value, str) and "\x00" not in value for value in parts) or "/" in record.source_id or "\\" in record.source_id or not _SAFE.fullmatch(record.component_id) or not _SAFE.fullmatch(record.symbol) or (record.module and not _SAFE.fullmatch(record.module)):
            raise AretFunctionSymbolProjectionError("Ligne function_symbol ARET non projetable de manière déterministe.")
        identifier = f"aret-symbol--{record.component_id}-{record.module or 'root'}-{record.symbol}"
        drafts.append(AretV1SymbolDraft(identifier, f"aret-component--{record.component_id}", "FUNCTION", record.module, record.symbol, "", {"source": {"domain_pack": "aret-v1", "legacy_table": "function_symbol", "source_id": record.source_id, "source_snapshot_sha256": source_page.source_snapshot_sha256, "component_id": record.component_id, "module": record.module, "symbol": record.symbol, "calling_convention": record.calling_convention, "source_created_at": record.created_at, "source_created_by": record.created_by}}))
    return AretV1FunctionSymbolProjection(target_identity, request_id, source_page.source_snapshot_sha256, tuple(drafts))
