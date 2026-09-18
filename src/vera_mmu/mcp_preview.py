"""The MCP Preview §34 asks for before generation: the figures, the hashes and the alerts.

Everything here is **rendered**, never recomputed. The compiler already produces the package, its
hashes and its blocking static validation; the catalogs already hold the capabilities and gates;
`mcp_tool_classes` already says what each tool does. This module gathers them and adds nothing of
its own — a second computation would be a second opinion, and the screen would eventually show the
wrong one.

**Three of §34's four alerts describe a looser engine than the one VERA became, and the preview
says so rather than dropping them.** A capability without an objective validator, a NETWORK
capability behind a gate, an output path outside the project: each was possible when §34 was
written and each is now refused at declaration, by the Core, on the declarative file itself. An
alert that can never fire is not a reassurance to display quietly; it is a rule that moved, and the
preview names the rule that moved it. Only then is the count of raised alerts meaningful.

**The one that remains reachable is reported from the same place the Doctor reads it**, so the two
can never disagree about whether a promotion would be refused for want of a secret.
"""
from __future__ import annotations

from dataclasses import dataclass
import os

from .doctor import PROOF_HMAC_SECRET_VARIABLE
from .identity import canonical_json
from .mcp_compiler import MCPCompilerError, compile_mcp_package
from .mcp_tool_classes import (
    NETWORK_REASON,
    PROJECT_TOOL_REASON,
    SENSITIVE_REASONS,
    SENSITIVE_TOOLS,
    tool_counts,
)
from .store import MemoryStore, StoreError


MCP_PREVIEW_FORMAT = "vera-mcp-preview/v1"

RAISED = "RAISED"
CLEAR = "CLEAR"
NOT_APPLICABLE = "NOT_APPLICABLE"


class MCPPreviewError(StoreError):
    """Raised when the pre-generation preview cannot be compiled from the project."""


@dataclass(frozen=True)
class PreviewAlert:
    """One §34 alert: whether it fires, what fired it, or the rule that made it impossible."""

    id: str
    severity: str
    status: str
    message: str
    instances: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "severity": self.severity,
            "status": self.status,
            "message": self.message,
            "instances": list(self.instances),
        }


def compile_mcp_preview(store: MemoryStore, adapter: str) -> dict[str, object]:
    """Report what generation would produce, before it produces it. Writes nothing."""
    if not isinstance(store, MemoryStore):
        raise MCPPreviewError("Preview MCP impossible : store invalide.")
    try:
        package = compile_mcp_package(store, adapter=adapter)
    except MCPCompilerError as exc:
        raise MCPPreviewError(f"Preview MCP impossible : la compilation refuse le projet ({exc}).") from exc

    catalogs = package.catalogs
    capabilities = list(catalogs.capabilities["capabilities"])
    gates = list(catalogs.gates["gates"])
    counts = {
        **tool_counts(),
        "gates": len(gates),
        "capabilities": len(capabilities),
    }
    alerts = [
        _missing_validator_alert(store, capabilities),
        _network_gate_alert(),
        _output_path_alert(),
        _hmac_alert(store),
    ]
    return {
        "format": MCP_PREVIEW_FORMAT,
        "project_id": package.project_id,
        "adapter": package.adapter,
        "counts": counts,
        "notes": {
            "project_tools": PROJECT_TOOL_REASON,
            "network": NETWORK_REASON,
            "sensitive": [{"tool": name, "reason": SENSITIVE_REASONS[name]} for name in sorted(SENSITIVE_TOOLS)],
        },
        "hashes": {
            "profile_hash": package.profile_hash,
            "policy_hash": catalogs.policy_hash,
            "capability_catalog_hash": catalogs.capability_catalog_hash,
            "gate_catalog_hash": catalogs.gate_catalog_hash,
            "mcp_build_hash": package.manifest.mcp_build_hash,
            "package_hash": package.package_hash,
        },
        "alerts": [alert.as_dict() for alert in alerts],
        "raised": sorted(alert.id for alert in alerts if alert.status == RAISED),
        "mutation": "NONE",
    }


def _missing_validator_alert(store: MemoryStore, capabilities: list[dict[str, object]]) -> PreviewAlert:
    """§34: a capability with no objective validator.

    Reachable, and worth catching before generation: the catalogue declares a validator kind, but
    `sync-capabilities` is what registers it. Until then the façade would advertise a capability
    whose validator does not exist, and any execution of it would be refused.
    """
    try:
        registered = {
            str(row["kind"])
            for row in store.connection.execute("SELECT kind FROM validator").fetchall()
        }
    except StoreError as exc:  # pragma: no cover - a store that cannot be read has already failed
        raise MCPPreviewError("Validators illisibles pour le preview MCP.") from exc
    missing = sorted(
        str(item["id"]) for item in capabilities if str(item["validator"]) not in registered
    )
    if not missing:
        return PreviewAlert(
            "capability_without_objective_validator",
            "ERROR",
            CLEAR,
            "Chaque capability déclarée dispose d’un validator enregistré dans la mémoire.",
            (),
        )
    return PreviewAlert(
        "capability_without_objective_validator",
        "ERROR",
        RAISED,
        "Validator déclaré mais non enregistré dans la mémoire : exécuter `sync-capabilities` avant "
        "de générer, sinon la façade annoncera une capability qu’aucun validator ne peut qualifier.",
        tuple(missing),
    )


def _network_gate_alert() -> PreviewAlert:
    """§34: a gate depending on a NETWORK capability — no longer declarable."""
    return PreviewAlert(
        "gate_depends_on_network_capability",
        "WARNING",
        NOT_APPLICABLE,
        "Impossible par construction : `policies.process` n’admet que `DENY_NETWORK` et le catalogue "
        "refuse une capability déclarée `NETWORK`. Aucune gate ne peut donc en dépendre.",
        (),
    )


def _output_path_alert() -> PreviewAlert:
    """§34: an output path outside the project — refused when it is written, not when followed."""
    return PreviewAlert(
        "output_path_outside_scope",
        "ERROR",
        NOT_APPLICABLE,
        "Impossible par construction : le catalogue refuse tout artefact absolu, en `..`, avec lettre "
        "de lecteur ou barre inverse, et la configuration hôte reste project-local.",
        (),
    )


def _hmac_alert(store: MemoryStore) -> PreviewAlert:
    """§34: PROVEN enabled without an HMAC secret — read where the Doctor reads it."""
    row = store.connection.execute(
        "SELECT algorithm, hmac_required FROM proof_policy WHERE singleton=1"
    ).fetchone()
    if row is None:
        return PreviewAlert(
            "proven_without_hmac_secret",
            "WARNING",
            CLEAR,
            "Aucune policy de preuve déclarée : aucune promotion n’est possible pour l’instant.",
            (),
        )
    if not bool(row["hmac_required"]):
        return PreviewAlert(
            "proven_without_hmac_secret",
            "WARNING",
            CLEAR,
            f"Policy `{row['algorithm']}` déclarée sans signature requise.",
            (),
        )
    if os.environ.get(PROOF_HMAC_SECRET_VARIABLE, "").strip():
        return PreviewAlert(
            "proven_without_hmac_secret",
            "WARNING",
            CLEAR,
            f"Policy `{row['algorithm']}` exige HMAC ; le secret est présent dans l’environnement.",
            (),
        )
    return PreviewAlert(
        "proven_without_hmac_secret",
        "WARNING",
        RAISED,
        f"Policy `{row['algorithm']}` exige HMAC mais aucun secret n’est disponible : toute promotion "
        f"serait refusée. Définir {PROOF_HMAC_SECRET_VARIABLE} hors du dépôt.",
        (PROOF_HMAC_SECRET_VARIABLE,),
    )


def preview_hash(preview: dict[str, object]) -> str:
    """Hash one preview payload, so a screen can prove it is showing the build it reviewed."""
    from hashlib import sha256

    return sha256(canonical_json(preview).encode("utf-8")).hexdigest()
