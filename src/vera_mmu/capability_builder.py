"""Composing a complete capability contract (§32) — step 9 of the eighteen-step journey.

**What this module replaces, and why.** The previous builder wrote five fields — identifier,
name, kind, version, description — straight into the SQLite registry. A capability declared that
way carries **no contract and no policy**, so no runner will execute it (`capability_contract` is
absent), no policy decision covers it (`capability_policy` is absent), and no declarative hash
ever sees it: `capability_catalog_hash` is computed over `capabilities.yaml`, which that path
never touched. The screen reported a success; the engine held something it could never run. This
module closes that by composing the **whole** contract §32 lists, into the one file that holds it.

**Where a contract lives.** `.vera-mmu/capabilities.yaml` is the only place the full contract
exists — runner, project policy, timeout, inputs, outputs, artifacts, validator, proof
admissibility, confirmation. `load_project_catalogs` validates it, `capability_catalog_hash`
hashes it, and `sync-capabilities` materializes it into one capability, one contract and one
policy decision. Writing anywhere else would create a second, partial truth.

**The tension §32 raises, settled here rather than assumed.** §32 lists a « Commande / API » line;
I008 forbids a client from supplying a command. The Core does not merely bound a command — **it
has no command field at all.** `capability_contract` holds a runner *profile* chosen from four,
and not one of them spawns a process from a project-supplied string: `OBSERVED_PROCESS` records
that a process happened elsewhere, it does not run one. So the builder accepts no command, no
argv, no interpreter, no URL and no path, and the contract reports that line `NOT_APPLICABLE`
with its reason. Rendering an empty « Commande » field would invite someone to type one.

**The seven refusals §32 requires** are each carried by a stable code, so a screen can name the
reason rather than greying a button, and each is also refused by the Core on the declarative file
itself — `project_catalogs` — so bypassing this builder changes nothing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping

import yaml

from .capability_contracts import NETWORK_POLICIES, RUNNER_PROFILES
from .identity import ProfileError, canonical_json, load_profile
from .project_catalogs import (
    CAPABILITY_ID_RE,
    CAPABILITY_KINDS,
    CAPABILITY_VERSION_RE,
    FIELD_NAME_RE,
    PROJECT_POLICIES,
    VALIDATORS,
    VALIDATOR_RUNNERS,
    ProjectCatalogError,
    confined_relative_path,
    load_project_catalogs,
)
from .store import StoreError
from .workspace import WorkspaceError, resolve_workspace


CAPABILITY_CONTRACT_FORMAT = "vera-capability-contract/v1"
CAPABILITY_CATALOG_FORMAT = "vera-capability-catalog/v1"

# Exactly what a contract declaration may name. `gate_backed` is a question the builder asks —
# is this capability meant to satisfy a gate — and is never written to the catalog.
DECLARATION_KEYS = frozenset(
    {
        "id", "name", "description", "kind", "version", "runner", "policy", "timeout_seconds",
        "inputs", "outputs", "artifacts", "validator", "yields_proof", "confirmation_required",
        "gate_backed",
    }
)
# The one network policy the Core admits; a capability never chooses it.
FIXED_NETWORK_POLICY = "DENY_NETWORK"
# What a gate reads from a capability's outputs, per §33's `expected: {verdict: ...}`.
GATE_OUTPUT = "verdict"
# Words that dress an absent validator up as one. The closed set already refuses them; naming
# them lets the refusal say *why* rather than only that the value is unknown.
PLACEHOLDER_TOKENS = frozenset({"", "-", "n/a", "na", "none", "null", "tbd", "todo", "manual", "human", "placeholder", "xxx"})
TIMEOUT_BOUNDS = (1, 3600)


class CapabilityBuilderError(StoreError):
    """Raised when a capability contract cannot be planned or applied exactly as reviewed."""


@dataclass(frozen=True)
class ContractRefusal:
    """One reason a declaration is refused, with the code a screen can key on."""

    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class CapabilityContractPreview:
    """The §32 contract a declaration would add, reviewed before anything is written."""

    format: str
    catalog_path: str
    identifier: str
    contract: dict[str, Any]
    declaration: dict[str, Any]
    notes: tuple[str, ...]
    refusals: tuple[ContractRefusal, ...]
    status: str
    gate_backed: bool
    preview_hash: str
    mutation: str = "NONE"
    _content: str = field(default="", repr=False, compare=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "catalog_path": self.catalog_path,
            "identifier": self.identifier,
            "contract": self.contract,
            "declaration": self.declaration,
            "notes": list(self.notes),
            "refusals": [item.as_dict() for item in self.refusals],
            "blockers": [item.message for item in self.refusals],
            "status": self.status,
            "gate_backed": self.gate_backed,
            "preview_hash": self.preview_hash,
            "mutation": self.mutation,
        }


def capability_contract_options(profile_path: str | Path) -> dict[str, object]:
    """Report what a contract may be composed from. Writes nothing.

    The interface never invents a runner, a policy or a validator: it chooses among what the Core
    declares here. The absence of a command field is reported as a fact, not left to be inferred
    from an empty form.
    """
    path = _profile_path(profile_path)
    declared = tuple(str(item["id"]) for item in _catalog(path)["capabilities"])
    return {
        "format": CAPABILITY_CONTRACT_FORMAT,
        "kinds": sorted(CAPABILITY_KINDS),
        "runners": [
            {
                "id": runner,
                "consumes_validator": runner in VALIDATOR_RUNNERS,
                "required_validator": runner if runner in VALIDATOR_RUNNERS else None,
            }
            for runner in sorted(RUNNER_PROFILES)
        ],
        "policies": [
            {"id": policy, "declarable": policy != "NETWORK", "reason": _policy_reason(policy)}
            for policy in sorted(PROJECT_POLICIES)
        ],
        "validators": sorted(VALIDATORS),
        "network_policy": {"value": FIXED_NETWORK_POLICY, "editable": False, "available": sorted(NETWORK_POLICIES)},
        "command": {
            "status": "NOT_APPLICABLE",
            "reason": (
                "Le Core ne tient aucun champ de commande : un runner est choisi parmi les profils "
                "déclarés et ne reçoit que des paramètres typés (I008)."
            ),
        },
        "timeout_seconds": {"minimum": TIMEOUT_BOUNDS[0], "maximum": TIMEOUT_BOUNDS[1], "required": True},
        "gate_output": GATE_OUTPUT,
        "declared_capabilities": list(declared),
        "mutation": "NONE",
    }


def preview_capability_contract(profile_path: str | Path, declaration: Mapping[str, Any]) -> CapabilityContractPreview:
    """Plan one complete capability contract, naming every refusal §32 requires. Writes nothing."""
    if not isinstance(declaration, Mapping):
        raise CapabilityBuilderError("Déclaration de capability invalide : un objet est attendu.")
    path = _profile_path(profile_path)
    catalog = _catalog(path)
    catalog_path = _catalog_path(path)

    refusals: list[ContractRefusal] = []
    unknown = sorted(set(declaration) - DECLARATION_KEYS)
    if unknown:
        refusals.append(
            ContractRefusal(
                "COMMAND_NOT_BOUNDED",
                "Champ hors contrat fermé : "
                + ", ".join(f"`{name}`" for name in unknown)
                + ". Le Core ne tient aucune commande, API, argv ni interpréteur : un runner est "
                "choisi parmi les profils déclarés et ne reçoit que des paramètres typés (I008).",
            )
        )

    identifier = declaration.get("id")
    if not isinstance(identifier, str) or CAPABILITY_ID_RE.fullmatch(identifier) is None:
        raise CapabilityBuilderError("Identifiant de capability invalide : minuscules, chiffres et « - » attendus.")
    if any(str(item["id"]) == identifier for item in catalog["capabilities"]):
        raise CapabilityBuilderError(f"Capability `{identifier}` déjà déclarée dans le catalogue du projet.")

    name = _text(declaration.get("name"), "name", 256)
    description = _text(declaration.get("description"), "description", 4096)
    kind = declaration.get("kind")
    if kind not in CAPABILITY_KINDS:
        raise CapabilityBuilderError("Type de capability hors catalogue fermé.")
    version = declaration.get("version")
    if not isinstance(version, str) or CAPABILITY_VERSION_RE.fullmatch(version) is None:
        raise CapabilityBuilderError("Version de capability invalide.")

    runner = declaration.get("runner")
    if runner not in RUNNER_PROFILES:
        refusals.append(
            ContractRefusal(
                "COMMAND_NOT_BOUNDED",
                f"Runner `{runner}` hors catalogue fermé : le Core n’exécute que {', '.join(sorted(RUNNER_PROFILES))}, "
                "et aucun d’eux ne prend de commande.",
            )
        )

    policy = declaration.get("policy")
    if policy == "NETWORK":
        refusals.append(
            ContractRefusal(
                "NETWORK_WITHOUT_POLICY",
                "Policy `NETWORK` refusée : la seule policy réseau déclarable est `DENY_NETWORK`. "
                "Rien ne bornerait une capability réseau, donc elle ne peut pas être déclarée.",
            )
        )
    elif policy not in PROJECT_POLICIES:
        refusals.append(ContractRefusal("DECLARATION_INVALID", f"Policy projet `{policy}` hors catalogue fermé."))

    timeout = declaration.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not TIMEOUT_BOUNDS[0] <= timeout <= TIMEOUT_BOUNDS[1]:
        refusals.append(
            ContractRefusal(
                "MISSING_TIMEOUT",
                f"Timeout absent ou hors borne : un entier de {TIMEOUT_BOUNDS[0]} à {TIMEOUT_BOUNDS[1]} secondes est "
                "exigé, sans valeur par défaut — une capability sans timeout n’a pas de fin garantie.",
            )
        )

    inputs = _names(declaration.get("inputs"), "inputs", refusals)
    outputs = _names(declaration.get("outputs"), "outputs", refusals)
    artifacts = _artifacts(declaration.get("artifacts"), refusals)

    gate_backed = declaration.get("gate_backed", False)
    if not isinstance(gate_backed, bool):
        raise CapabilityBuilderError("`gate_backed` doit être booléen.")
    if gate_backed and GATE_OUTPUT not in outputs:
        refusals.append(
            ContractRefusal(
                "OUTPUT_NOT_INTERPRETABLE",
                f"Sortie non interprétable comme gate : une gate lit `expected.verdict`, et cette capability "
                f"ne déclare pas `{GATE_OUTPUT}` parmi ses sorties. Une gate adossée à elle n’aurait rien à lire.",
            )
        )

    validator = declaration.get("validator")
    if validator not in VALIDATORS:
        token = validator.strip().lower() if isinstance(validator, str) else ""
        refusals.append(
            ContractRefusal(
                "PLACEHOLDER_VALIDATOR",
                (
                    f"`{validator}` n’est pas un validator : c’est un marqueur d’attente présenté comme tel."
                    if token in PLACEHOLDER_TOKENS
                    else f"Validator `{validator}` hors catalogue fermé."
                )
                + f" Le Core n’enregistre que {', '.join(sorted(VALIDATORS))}.",
            )
        )
    elif runner in VALIDATOR_RUNNERS and validator != runner:
        refusals.append(
            ContractRefusal(
                "DEPENDENCY_MISSING",
                f"Le runner `{runner}` exige un validator `{runner}` ; la déclaration nomme `{validator}`. "
                "Le Core refuserait l’exécution : cette capability dépend d’un validator qui n’existera jamais pour elle.",
            )
        )
    elif validator == "EVIDENCE_FIELDS" and not inputs:
        refusals.append(
            ContractRefusal(
                "DEPENDENCY_MISSING",
                "Un validator `EVIDENCE_FIELDS` vérifie des champs déclarés : sans `inputs`, il n’aurait aucune clé "
                "requise et le Core refuserait de l’enregistrer.",
            )
        )

    yields_proof = declaration.get("yields_proof", False)
    if not isinstance(yields_proof, bool):
        raise CapabilityBuilderError("`yields_proof` doit être booléen.")
    if yields_proof:
        refusals.append(
            ContractRefusal(
                "PLACEHOLDER_VALIDATOR",
                "`yields_proof` refusé : aucun runner du Core ne produit de preuve, et tous refusent un contrat qui "
                "le prétend. Une preuve naît d’une evidence PASS validée puis admise, jamais de la capability "
                "elle-même (I004, I006).",
            )
        )

    confirmation_required = declaration.get("confirmation_required", False)
    if not isinstance(confirmation_required, bool):
        raise CapabilityBuilderError("`confirmation_required` doit être booléen.")

    entry = {
        "id": identifier,
        "name": name,
        "description": description,
        "kind": kind,
        "version": version,
        "runner": runner,
        "network_policy": FIXED_NETWORK_POLICY,
        "timeout_seconds": timeout,
        "parameter_schema": _parameter_schema(runner, inputs),
        "yields_proof": yields_proof,
        "policy": policy,
        "inputs": list(inputs),
        "outputs": list(outputs),
        "validator": validator,
        "artifacts": list(artifacts),
        "confirmation_required": confirmation_required,
    }

    notes = [
        "Le contrat est écrit dans le catalogue déclaratif, la seule source que le Core valide et hache. "
        "`sync-capabilities` le matérialise ensuite en une capability, un contrat et une décision de policy.",
        f"La policy réseau vaut `{FIXED_NETWORK_POLICY}` et n’est pas choisie : c’est la seule que le Core admette.",
        (
            "Le schéma de paramètres est dérivé par le Core, jamais composé par l’interface : "
            f"`{runner}` impose `validator_id` et `evidence_id`."
            if runner in VALIDATOR_RUNNERS
            else "Le schéma de paramètres est dérivé par le Core depuis les entrées déclarées, en chaînes requises."
        ),
    ]
    if confirmation_required:
        notes.append("`confirmation_required` fait déclarer la policy de capability en `CONFIRM` plutôt qu’en `ALLOW`.")

    if not refusals:
        # The declaration is also replayed through the Core's own catalog validation, so a preview
        # never promises a file the loader would then refuse.
        try:
            _validated_document(catalog, entry)
        except ProjectCatalogError as exc:
            refusals.append(ContractRefusal("DECLARATION_INVALID", f"Déclaration refusée par le Core : {exc}"))

    status = "REFUSED" if refusals else "PREVIEW"
    content = "" if refusals else yaml.safe_dump(
        _document(catalog, entry), allow_unicode=True, default_flow_style=False, sort_keys=False
    )
    payload = {
        "format": CAPABILITY_CONTRACT_FORMAT,
        "catalog_path": str(catalog_path),
        "current_catalog_sha256": sha256(catalog_path.read_bytes()).hexdigest(),
        "declaration": entry,
        "gate_backed": gate_backed,
        "refusals": [item.as_dict() for item in refusals],
        "status": status,
    }
    return CapabilityContractPreview(
        format=CAPABILITY_CONTRACT_FORMAT,
        catalog_path=str(catalog_path),
        identifier=identifier,
        contract=_contract_view(entry, gate_backed),
        declaration=entry,
        notes=tuple(notes),
        refusals=tuple(refusals),
        status=status,
        gate_backed=gate_backed,
        preview_hash=sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        _content=content,
    )


def apply_capability_contract(
    profile_path: str | Path, preview: CapabilityContractPreview, *, confirm: bool
) -> dict[str, object]:
    """Append exactly the contract the reviewed preview described, atomically."""
    if confirm is not True:
        raise CapabilityBuilderError("Déclaration de capability refusée sans confirmation explicite.")
    if not isinstance(preview, CapabilityContractPreview):
        raise CapabilityBuilderError("Preview de contrat de capability invalide.")
    if preview.status == "REFUSED":
        raise CapabilityBuilderError(
            "Déclaration refusée : " + " ".join(item.message for item in preview.refusals)
        )
    path = _profile_path(profile_path)
    if str(_catalog_path(path)) != preview.catalog_path:
        raise CapabilityBuilderError("Preview lié à un autre catalogue de capabilities.")

    current = preview_capability_contract(path, _replayable(preview))
    if current.preview_hash != preview.preview_hash:
        raise CapabilityBuilderError("Preview périmé : le catalogue a changé depuis sa relecture.")

    _write_atomic(Path(preview.catalog_path), preview._content)
    try:
        load_project_catalogs(path)
    except ProjectCatalogError as exc:
        raise CapabilityBuilderError(f"Catalogue écrit mais refusé par le Core : {exc}") from exc
    return {
        "format": CAPABILITY_CONTRACT_FORMAT,
        "status": "DECLARED",
        "catalog_path": preview.catalog_path,
        "identifier": preview.identifier,
        "declaration": preview.declaration,
        "materialization": {
            "status": "PENDING",
            "command": "sync-capabilities",
            "reason": "Le contrat est déclaré ; sa matérialisation dans le store reste une opération explicite.",
        },
        "preview_hash": preview.preview_hash,
    }


def _replayable(preview: CapabilityContractPreview) -> dict[str, Any]:
    """Rebuild the exact declaration the preview was planned from, to replay it unchanged."""
    entry = preview.declaration
    return {
        "id": entry["id"],
        "name": entry["name"],
        "description": entry["description"],
        "kind": entry["kind"],
        "version": entry["version"],
        "runner": entry["runner"],
        "policy": entry["policy"],
        "timeout_seconds": entry["timeout_seconds"],
        "inputs": list(entry["inputs"]),
        "outputs": list(entry["outputs"]),
        "artifacts": list(entry["artifacts"]),
        "validator": entry["validator"],
        "yields_proof": entry["yields_proof"],
        "confirmation_required": entry["confirmation_required"],
        "gate_backed": preview.gate_backed,
    }


def _contract_view(entry: Mapping[str, Any], gate_backed: bool) -> dict[str, Any]:
    """Render the contract in the order §32 displays it, including the line the Core does not hold."""
    return {
        "name": entry["name"],
        "type": entry["kind"],
        "runner": entry["runner"],
        "command": {
            "status": "NOT_APPLICABLE",
            "reason": "Le Core ne tient aucun champ de commande ; le runner est un profil déclaré (I008).",
        },
        "inputs": list(entry["inputs"]),
        "outputs": list(entry["outputs"]),
        "timeout_seconds": entry["timeout_seconds"],
        "policy": {
            "project": entry["policy"],
            "network": entry["network_policy"],
            "decision": "CONFIRM" if entry["confirmation_required"] else "ALLOW",
        },
        "artifacts": list(entry["artifacts"]),
        "validator": entry["validator"],
        "proof_admissible": {
            "direct": bool(entry["yields_proof"]),
            "path": "evidence PASS → validation → admission → promotion",
            "reason": "Une capability n’émet pas de preuve : elle produit une evidence qu’un validator et une admission qualifient (I004, I006).",
        },
        "confirmation_required": bool(entry["confirmation_required"]),
        "gate_backed": gate_backed,
    }


def _parameter_schema(runner: Any, inputs: tuple[str, ...]) -> dict[str, Any]:
    """Derive the bounded parameter schema the runner imposes; the interface never composes one."""
    names = ("validator_id", "evidence_id") if runner in VALIDATOR_RUNNERS else inputs
    return {
        "type": "object",
        "properties": {name: {"type": "string"} for name in names},
        "required": list(names),
        "additionalProperties": False,
    }


def _policy_reason(policy: str) -> str:
    if policy == "NETWORK":
        return "Non déclarable : la seule policy réseau du Core est `DENY_NETWORK`, rien ne bornerait une capability réseau."
    return "Déclarable."


def _names(value: Any, label: str, refusals: list[ContractRefusal]) -> tuple[str, ...]:
    """Accept a bounded list of field names; a path-shaped entry is a path, and is refused as one."""
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)) or len(value) > 64:
        raise CapabilityBuilderError(f"`{label}` doit être une liste bornée de noms de champ.")
    names: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise CapabilityBuilderError(f"`{label}` doit ne contenir que des noms de champ.")
        if "/" in item or "\\" in item or item.startswith("."):
            refusals.append(
                ContractRefusal(
                    "PATH_OUTSIDE_ROOTS",
                    f"`{label}` nomme des champs, pas des chemins : `{item}` est refusé.",
                )
            )
            continue
        if FIELD_NAME_RE.fullmatch(item) is None:
            raise CapabilityBuilderError(f"`{label}` : nom de champ invalide `{item}`.")
        if item in names:
            raise CapabilityBuilderError(f"`{label}` : nom de champ en double `{item}`.")
        names.append(item)
    return tuple(names)


def _artifacts(value: Any, refusals: list[ContractRefusal]) -> tuple[str, ...]:
    """Accept artifact paths confined to the project's artifact root, and refuse every escape."""
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)) or len(value) > 64:
        raise CapabilityBuilderError("`artifacts` doit être une liste bornée de chemins relatifs.")
    artifacts: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise CapabilityBuilderError("`artifacts` doit ne contenir que des chemins relatifs.")
        try:
            confined_relative_path(item, "artifacts")
        except ProjectCatalogError as exc:
            refusals.append(
                ContractRefusal(
                    "PATH_OUTSIDE_ROOTS",
                    f"Chemin d’artefact hors des racines du projet : `{item}` — {exc}",
                )
            )
            continue
        if item in artifacts:
            raise CapabilityBuilderError(f"`artifacts` : chemin en double `{item}`.")
        artifacts.append(item)
    return tuple(artifacts)


def _text(value: Any, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum or "\x00" in value:
        raise CapabilityBuilderError(f"`{label}` doit être une chaîne canonique non vide.")
    return value


def _document(catalog: Mapping[str, Any], entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "format": CAPABILITY_CATALOG_FORMAT,
        "capabilities": [*[dict(item) for item in catalog["capabilities"]], dict(entry)],
    }


def _validated_document(catalog: Mapping[str, Any], entry: Mapping[str, Any]) -> dict[str, Any]:
    from .project_catalogs import validate_capability_catalog

    return validate_capability_catalog(_document(catalog, entry))


def _profile_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_symlink() or not path.is_file() or path.parent.is_symlink():
        raise CapabilityBuilderError("Project Profile ou son répertoire est ambigu.")
    return path.resolve(strict=True)


def _catalog_path(profile_path: Path) -> Path:
    """Resolve the declared catalog, refusing anything outside the runtime or symlinked."""
    try:
        profile = load_profile(profile_path)
        workspace = resolve_workspace(profile, profile_path)
    except (ProfileError, WorkspaceError, OSError, ValueError) as exc:
        raise CapabilityBuilderError(f"Project Profile invalide : contrat de capability refusé ({exc}).") from exc
    relative = profile.get("capabilities", {}).get("catalog")
    if not isinstance(relative, str) or not relative:
        raise CapabilityBuilderError("Le Project Profile ne déclare aucun catalogue de capabilities.")
    path = workspace.project_root / relative
    try:
        path.relative_to(workspace.runtime_dir)
    except ValueError as exc:
        raise CapabilityBuilderError("Le catalogue de capabilities doit rester sous le runtime VERA.") from exc
    current = workspace.project_root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise CapabilityBuilderError("Catalogue de capabilities symlinké refusé.")
    if not path.is_file():
        raise CapabilityBuilderError("Catalogue de capabilities introuvable ou non régulier.")
    return path


def _catalog(profile_path: Path) -> dict[str, Any]:
    try:
        return load_project_catalogs(profile_path).capabilities
    except ProjectCatalogError as exc:
        raise CapabilityBuilderError(f"Catalogue de capabilities invalide : {exc}") from exc


def _write_atomic(path: Path, content: str) -> None:
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=".capability-", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise CapabilityBuilderError("Écriture atomique du catalogue de capabilities impossible.") from exc
