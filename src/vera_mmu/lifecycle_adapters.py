"""Attested, transport-neutral lifecycle adapter plans and runtime registry."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from types import MappingProxyType
from typing import Iterable, Mapping, Protocol

from .identity import canonical_json
from .mcp_manifest import MCPManifest, verify_mcp_manifest
from .store import MemoryStore, StoreError


LIFECYCLE_ADAPTER_PLAN_FORMAT = "vera-lifecycle-adapter-plan/v1"
_ADAPTER_ID_RE = re.compile(r"[a-z][a-z0-9-]{0,127}")
_VERSION_RE = re.compile(r"(?:0|[1-9][0-9]{0,7})\.(?:0|[1-9][0-9]{0,7})\.(?:0|[1-9][0-9]{0,7})")
_GUARD_MODES = frozenset({"HARD", "SOFT"})


class LifecycleAdapterPlanError(StoreError):
    """A lifecycle adapter declaration or plan is stale, foreign, or ambiguous."""


class LifecycleAdapterRegistryError(StoreError):
    """The trusted in-memory lifecycle adapter registry is incomplete or incompatible."""


class LifecycleSessionAdapter(Protocol):
    """Minimal host context supplied only by the process that owns the MCP server."""

    adapter_id: str
    adapter_version: str
    maximum_guard_mode: str

    def session_identity(self) -> str | None:
        """Return the server-owned current session identity, never a client parameter."""


@dataclass(frozen=True)
class LifecycleAdapterPlan:
    """Canonical declaration that binds one lifecycle adapter to a verified MCP manifest."""

    format: str
    project_identity: dict[str, str]
    mcp_build_hash: str
    adapter_id: str
    adapter_version: str
    maximum_guard_mode: str
    lifecycle_plan_hash: str
    canonical_json: str

    def as_dict(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "format": self.format,
            "lifecycle_plan_hash": self.lifecycle_plan_hash,
            "maximum_guard_mode": self.maximum_guard_mode,
            "mcp_build_hash": self.mcp_build_hash,
            "project_identity": dict(self.project_identity),
        }


def compile_lifecycle_adapter_plan(
    store: MemoryStore,
    manifest: MCPManifest,
    *,
    adapter_id: str,
    adapter_version: str,
    maximum_guard_mode: str,
) -> LifecycleAdapterPlan:
    """Compile a deterministic plan from a verified manifest and closed adapter declaration."""
    if not isinstance(store, MemoryStore):
        raise LifecycleAdapterPlanError("Store lifecycle invalide.")
    if not isinstance(manifest, MCPManifest):
        raise LifecycleAdapterPlanError("Manifeste MCP lifecycle invalide.")
    try:
        verify_mcp_manifest(store, manifest)
    except StoreError as exc:
        raise LifecycleAdapterPlanError("Manifeste MCP lifecycle périmé, altéré ou étranger.") from exc
    _validate_adapter_declaration(adapter_id, adapter_version, maximum_guard_mode)
    payload = {
        "adapter_id": adapter_id,
        "adapter_version": adapter_version,
        "format": LIFECYCLE_ADAPTER_PLAN_FORMAT,
        "maximum_guard_mode": maximum_guard_mode,
        "mcp_build_hash": manifest.mcp_build_hash,
        "project_identity": store.identity.as_dict(),
    }
    serialized = canonical_json(payload)
    return LifecycleAdapterPlan(
        format=LIFECYCLE_ADAPTER_PLAN_FORMAT,
        project_identity=store.identity.as_dict(),
        mcp_build_hash=manifest.mcp_build_hash,
        adapter_id=adapter_id,
        adapter_version=adapter_version,
        maximum_guard_mode=maximum_guard_mode,
        lifecycle_plan_hash=sha256(serialized.encode("utf-8")).hexdigest(),
        canonical_json=serialized,
    )


def verify_lifecycle_adapter_plan(
    store: MemoryStore,
    manifest: MCPManifest,
    plan: LifecycleAdapterPlan,
) -> LifecycleAdapterPlan:
    """Recompile and compare every relevant binding before a runtime adapter is resolved."""
    if not isinstance(plan, LifecycleAdapterPlan):
        raise LifecycleAdapterPlanError("Plan lifecycle invalide.")
    current = compile_lifecycle_adapter_plan(
        store,
        manifest,
        adapter_id=plan.adapter_id,
        adapter_version=plan.adapter_version,
        maximum_guard_mode=plan.maximum_guard_mode,
    )
    if current.canonical_json != plan.canonical_json or current.lifecycle_plan_hash != plan.lifecycle_plan_hash:
        raise LifecycleAdapterPlanError("Plan lifecycle périmé, altéré ou lié à un autre manifeste.")
    if current.as_dict() != plan.as_dict():
        raise LifecycleAdapterPlanError("Plan lifecycle incohérent avec sa forme canonique.")
    return current


class LifecycleAdapterRegistry:
    """Immutable registry of server-owned lifecycle adapters; no discovery or dynamic loading."""

    def __init__(self, adapters: Iterable[LifecycleSessionAdapter]) -> None:
        try:
            candidates = tuple(adapters)
        except TypeError as exc:
            raise LifecycleAdapterRegistryError("Les adapters lifecycle doivent former un itérable déclaré.") from exc
        if not candidates:
            raise LifecycleAdapterRegistryError("Le registry lifecycle ne peut pas être vide.")
        indexed: dict[str, LifecycleSessionAdapter] = {}
        for adapter in candidates:
            adapter_id = getattr(adapter, "adapter_id", None)
            adapter_version = getattr(adapter, "adapter_version", None)
            maximum_guard_mode = getattr(adapter, "maximum_guard_mode", None)
            _validate_adapter_declaration(adapter_id, adapter_version, maximum_guard_mode, error_type=LifecycleAdapterRegistryError)
            if not callable(getattr(adapter, "session_identity", None)):
                raise LifecycleAdapterRegistryError("Adapter lifecycle sans contexte de session déclaré.")
            if adapter_id in indexed:
                raise LifecycleAdapterRegistryError("Identifiant d’adapter lifecycle dupliqué.")
            indexed[adapter_id] = adapter
        self._adapters = MappingProxyType(dict(sorted(indexed.items())))

    @property
    def adapter_ids(self) -> tuple[str, ...]:
        """Return only declared identifiers, in deterministic order."""
        return tuple(self._adapters)

    def resolve_plan(
        self,
        store: MemoryStore,
        manifest: MCPManifest,
        plan: LifecycleAdapterPlan,
    ) -> LifecycleSessionAdapter:
        """Resolve exactly the verified adapter declared by the plan, or refuse."""
        verified = verify_lifecycle_adapter_plan(store, manifest, plan)
        adapter = self._adapters.get(verified.adapter_id)
        if adapter is None:
            raise LifecycleAdapterRegistryError("Adapter lifecycle attesté absent du processus hôte.")
        if getattr(adapter, "adapter_version", None) != verified.adapter_version:
            raise LifecycleAdapterRegistryError("Version d’adapter lifecycle incohérente avec le plan attesté.")
        if getattr(adapter, "maximum_guard_mode", None) != verified.maximum_guard_mode:
            raise LifecycleAdapterRegistryError("Capacité de garde lifecycle incohérente avec le plan attesté.")
        return adapter


def _validate_adapter_declaration(
    adapter_id: object,
    adapter_version: object,
    maximum_guard_mode: object,
    *,
    error_type: type[StoreError] = LifecycleAdapterPlanError,
) -> None:
    if not isinstance(adapter_id, str) or _ADAPTER_ID_RE.fullmatch(adapter_id) is None:
        raise error_type("Identifiant d’adapter lifecycle invalide : chemin ou commande interdits.")
    if not isinstance(adapter_version, str) or _VERSION_RE.fullmatch(adapter_version) is None:
        raise error_type("Version d’adapter lifecycle invalide.")
    if maximum_guard_mode not in _GUARD_MODES:
        raise error_type("Mode maximal de garde lifecycle invalide.")
