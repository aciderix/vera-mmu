"""Validated, project-local declarative catalogs for a VERA Project Profile (M11-A)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Any, Mapping

import yaml
from yaml.resolver import BaseResolver

from .agent_profiles import AgentProfileError, validate_agent_profile
from .identity import ProfileError, canonical_json, load_profile
from .parameter_validation import ParameterValidationError, validate_parameter_schema
from .policy_catalog import SECTIONS as POLICY_SECTIONS, PolicyCatalogError, validate_policy_values
from .workspace import Workspace, WorkspaceError, resolve_workspace


class ProjectCatalogError(ValueError):
    """Raised when a profile-referenced catalog is absent, unsafe, or malformed."""


CAPABILITY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
CAPABILITY_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,2}$")
GATE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
FIELD_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
CAPABILITY_KEYS = frozenset({"id", "name", "description", "kind", "version", "runner", "network_policy", "timeout_seconds", "parameter_schema", "yields_proof", "policy", "inputs", "outputs", "validator", "artifacts", "confirmation_required"})
GATE_KEYS = frozenset({"id", "name", "capability_id", "required", "expected"})
CAPABILITY_KINDS = frozenset({"ACTION", "CHECK", "ORACLE", "COLLECTOR", "GENERATOR", "QUERY"})
RUNNER_PROFILES = frozenset({"NOOP", "EVIDENCE_HASH", "EVIDENCE_FIELDS", "OBSERVED_PROCESS"})
# The two runners that consume a validator at execution, and that the Core pairs by kind.
VALIDATOR_RUNNERS = frozenset({"EVIDENCE_HASH", "EVIDENCE_FIELDS"})
NETWORK_POLICIES = frozenset({"DENY_NETWORK"})
PROJECT_POLICIES = frozenset({"READ_ONLY", "GENERATE", "NETWORK", "SENSITIVE"})
VALIDATORS = frozenset({"EVIDENCE_HASH", "EVIDENCE_FIELDS"})
# What a gate reads from the capability it is declared on, per §33's `expected: {verdict: ...}`.
GATE_OUTPUT = "verdict"


class _CatalogYamlLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses duplicate mapping keys."""


def _unique_mapping(loader: _CatalogYamlLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ProjectCatalogError("Clé YAML dupliquée dans un catalogue VERA.")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_CatalogYamlLoader.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


@dataclass(frozen=True)
class ProjectCatalogs:
    """Validated project catalog snapshots and their canonical hashes."""

    capabilities: dict[str, Any]
    gates: dict[str, Any]
    policies: dict[str, Any]
    agent_profiles: dict[str, dict[str, Any]]
    capability_catalog_hash: str
    gate_catalog_hash: str
    policy_hash: str
    agent_profiles_hash: str


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise ProjectCatalogError(f"{label} doit être un objet YAML à clés textuelles.")
    return dict(value)


def _catalog_path(workspace: Workspace, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ProjectCatalogError(f"Chemin {label} invalide.")
    path = workspace.project_root / relative
    try:
        path.relative_to(workspace.runtime_dir)
    except ValueError as exc:
        raise ProjectCatalogError(f"{label} doit rester sous le runtime VERA.") from exc
    current = workspace.project_root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ProjectCatalogError(f"{label} symlinké refusé.")
    if not path.is_file():
        raise ProjectCatalogError(f"Catalogue {label} introuvable ou non régulier.")
    return path


def _load_yaml(workspace: Workspace, relative: Any, label: str) -> dict[str, Any]:
    path = _catalog_path(workspace, relative, label)
    try:
        if path.stat().st_size > 256_000:
            raise ProjectCatalogError(f"Catalogue {label} trop volumineux.")
        decoded = yaml.load(path.read_text(encoding="utf-8"), Loader=_CatalogYamlLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ProjectCatalogError(f"Lecture YAML du catalogue {label} impossible.") from exc
    return _mapping(decoded, f"catalogue {label}")


def _exact_catalog(value: dict[str, Any], label: str, expected_format: str, collection: str) -> dict[str, Any]:
    if set(value) != {"format", collection}:
        raise ProjectCatalogError(f"Catalogue {label} doit contenir exactement format et {collection}.")
    if value.get("format") != expected_format or not isinstance(value.get(collection), list):
        raise ProjectCatalogError(f"Format ou collection du catalogue {label} invalide.")
    return value


def _nonempty_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value or len(value) > 4096:
        raise ProjectCatalogError(f"{label} doit être une chaîne canonique non vide.")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item == item.strip() and item and "\x00" not in item for item in value):
        raise ProjectCatalogError(f"{label} doit être une liste de chaînes canoniques.")
    if len(value) != len(set(value)):
        raise ProjectCatalogError(f"{label} ne doit pas contenir de doublon.")
    return list(value)


def _field_names(value: Any, label: str) -> list[str]:
    """Field names, not paths: a name carrying a separator is a path wearing a field's clothes."""
    names = _string_list(value, label)
    for name in names:
        if FIELD_NAME_RE.fullmatch(name) is None:
            raise ProjectCatalogError(f"{label} doit ne contenir que des noms de champ minuscules, pas `{name}`.")
    return names


def confined_relative_path(value: Any, label: str) -> str:
    """Accept one relative, traversal-free POSIX path; every escape from the project is refused.

    The check is lexical on purpose. An artifact path is declared before anything produces it, so
    there is nothing on disk to resolve, and a declaration that could escape the project's roots
    must be refused when it is written rather than when it is followed.
    """
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value or len(value) > 512:
        raise ProjectCatalogError(f"{label} doit être un chemin relatif canonique non vide.")
    candidate = PurePosixPath(value)
    if (
        value.startswith("/")
        or value.startswith("~")
        or "\\" in value
        or PureWindowsPath(value).drive
        or candidate.is_absolute()
        or ".." in candidate.parts
        or any(part in ("", ".") for part in candidate.parts)
    ):
        raise ProjectCatalogError(f"{label} sort des racines du projet ou n’est pas relatif : `{value}`.")
    return value


def _validate_capabilities(value: dict[str, Any]) -> dict[str, Any]:
    identifiers: set[str] = set()
    for index, item in enumerate(value["capabilities"]):
        capability = _mapping(item, f"capabilities[{index}]")
        if set(capability) != CAPABILITY_KEYS:
            raise ProjectCatalogError(f"capabilities[{index}] doit respecter le schéma fermé VERA.")
        identifier = _nonempty_text(capability.get("id"), f"capabilities[{index}].id")
        if CAPABILITY_ID_RE.fullmatch(identifier) is None or identifier in identifiers:
            raise ProjectCatalogError(f"capabilities[{index}].id invalide ou dupliqué.")
        identifiers.add(identifier)
        _nonempty_text(capability.get("name"), f"capabilities[{index}].name")
        _nonempty_text(capability.get("description"), f"capabilities[{index}].description")
        version = capability.get("version")
        if not isinstance(version, str) or CAPABILITY_VERSION_RE.fullmatch(version) is None:
            raise ProjectCatalogError(f"capabilities[{index}].version invalide.")
        runner = capability.get("runner")
        if capability.get("kind") not in CAPABILITY_KINDS or runner not in RUNNER_PROFILES or capability.get("network_policy") not in NETWORK_POLICIES:
            raise ProjectCatalogError(f"capabilities[{index}] référence une kind, runner ou policy réseau inconnue.")
        validator = capability.get("validator")
        if capability.get("policy") not in PROJECT_POLICIES or validator not in VALIDATORS:
            raise ProjectCatalogError(f"capabilities[{index}] référence une policy ou validator inconnu.")
        if capability.get("policy") == "NETWORK":
            # The only network policy the Core admits is DENY_NETWORK, so nothing would bound a
            # network capability: declaring one claims a permission the engine never grants.
            raise ProjectCatalogError(
                f"capabilities[{index}].policy NETWORK refusée : la seule policy réseau déclarable est DENY_NETWORK."
            )
        timeout = capability.get("timeout_seconds")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 3600:
            raise ProjectCatalogError(f"capabilities[{index}].timeout_seconds hors borne.")
        if not isinstance(capability.get("yields_proof"), bool) or not isinstance(capability.get("confirmation_required"), bool):
            raise ProjectCatalogError(f"capabilities[{index}] exige des indicateurs booléens explicites.")
        if capability.get("yields_proof") is True:
            # Every runner refuses a contract that claims it. A proof is derived from an admitted
            # PASS evidence, never emitted by the capability itself (I004, I006).
            raise ProjectCatalogError(
                f"capabilities[{index}].yields_proof refusé : aucun runner du Core ne produit de preuve directement."
            )
        try:
            validate_parameter_schema(_mapping(capability.get("parameter_schema"), f"capabilities[{index}].parameter_schema"))
        except ParameterValidationError as exc:
            raise ProjectCatalogError(f"capabilities[{index}].parameter_schema hors contrat fermé.") from exc
        inputs = _field_names(capability.get("inputs"), f"capabilities[{index}].inputs")
        _field_names(capability.get("outputs"), f"capabilities[{index}].outputs")
        for artifact in _string_list(capability.get("artifacts"), f"capabilities[{index}].artifacts"):
            confined_relative_path(artifact, f"capabilities[{index}].artifacts")
        if runner in VALIDATOR_RUNNERS and validator != runner:
            # `ensure_runner_validator_compatibility` pairs these by kind at execution, so such a
            # capability depends on a validator that will never exist for it.
            raise ProjectCatalogError(
                f"capabilities[{index}] : le runner {runner} exige un validator {runner}, pas {validator}."
            )
        if validator == "EVIDENCE_FIELDS" and not inputs:
            # The declared inputs become the validator's required keys, and a field validator
            # without a single required key is refused by the store when it is registered.
            raise ProjectCatalogError(
                f"capabilities[{index}] : un validator EVIDENCE_FIELDS exige au moins une entrée déclarée."
            )
    return value


def validate_capability_catalog(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one capability catalog document exactly as `load_project_catalogs` would."""
    return _validate_capabilities(
        _exact_catalog(_mapping(document, "catalogue capabilities"), "capabilities", "vera-capability-catalog/v1", "capabilities")
    )


def _validate_gates(value: dict[str, Any], capabilities: Mapping[str, Any]) -> dict[str, Any]:
    capability_ids = {str(item["id"]) for item in capabilities["capabilities"]}
    outputs_by_capability = {str(item["id"]): set(item["outputs"]) for item in capabilities["capabilities"]}
    identifiers: set[str] = set()
    for index, item in enumerate(value["gates"]):
        gate = _mapping(item, f"gates[{index}]")
        if set(gate) != GATE_KEYS:
            raise ProjectCatalogError(f"gates[{index}] doit respecter le schéma fermé VERA.")
        identifier = _nonempty_text(gate.get("id"), f"gates[{index}].id")
        if GATE_ID_RE.fullmatch(identifier) is None or identifier in identifiers:
            raise ProjectCatalogError(f"gates[{index}].id invalide ou dupliqué.")
        identifiers.add(identifier)
        _nonempty_text(gate.get("name"), f"gates[{index}].name")
        if gate.get("capability_id") not in capability_ids:
            raise ProjectCatalogError(f"gates[{index}].capability_id doit référencer une capability déclarée.")
        if not isinstance(gate.get("required"), bool):
            raise ProjectCatalogError(f"gates[{index}].required doit être booléen.")
        expected = _mapping(gate.get("expected"), f"gates[{index}].expected")
        if set(expected) != {"verdict"} or expected.get("verdict") not in {"PASS", "FAIL", "ERROR", "SKIPPED", "UNKNOWN"}:
            raise ProjectCatalogError(f"gates[{index}].expected doit déclarer un verdict VERA unique.")
        if GATE_OUTPUT not in outputs_by_capability[str(gate["capability_id"])]:
            # A gate reads a verdict. A capability that declares no readable verdict leaves it
            # nothing to read, so the gate would render an opinion rather than an observation.
            raise ProjectCatalogError(
                f"gates[{index}] : la capability `{gate['capability_id']}` ne déclare pas de sortie `{GATE_OUTPUT}`, "
                "sa sortie n’est donc pas interprétable comme gate."
            )
    return value


def _validate_agent_profiles(value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if set(value) != {"format", "profiles"} or value.get("format") != "vera-agent-profiles/v1" or not isinstance(value.get("profiles"), list):
        raise ProjectCatalogError("Format ou clés du catalogue agent-profiles invalides.")
    profiles: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value["profiles"]):
        profile = _mapping(item, f"agent-profiles.profiles[{index}]")
        if profile.get("format") != "vera-agent-profile/v1":
            raise ProjectCatalogError(f"agent-profiles.profiles[{index}].format invalide.")
        raw = {key: item_value for key, item_value in profile.items() if key != "format"}
        try:
            validated = validate_agent_profile(raw)
        except AgentProfileError as exc:
            raise ProjectCatalogError(f"agent-profiles.profiles[{index}] invalide.") from exc
        if validated.id in profiles:
            raise ProjectCatalogError("agent-profiles contient un identifiant dupliqué.")
        profiles[validated.id] = validated.as_dict()
    return profiles


def _policy_catalog(value: dict[str, Any]) -> dict[str, Any]:
    """Validate the shape **and** the values: a policy the Core cannot honour is refused here."""
    allowed = {"format", *POLICY_SECTIONS}
    if set(value) != allowed or value.get("format") != "vera-policy-catalog/v1":
        raise ProjectCatalogError("Format ou clés du catalogue policies invalides.")
    for key in POLICY_SECTIONS:
        _mapping(value.get(key), f"policies.{key}")
    try:
        validate_policy_values(value, runners=frozenset(RUNNER_PROFILES))
    except PolicyCatalogError as exc:
        raise ProjectCatalogError(str(exc)) from exc
    return value


def _validate_declared_runners(capabilities: Mapping[str, Any], policies: Mapping[str, Any]) -> None:
    """Refuse a capability whose runner the project's own process policy does not allow.

    Until now `process.allowed_runners` was decoration: every project shipped it empty while its
    capabilities declared runners, and nothing compared the two. A policy nobody cross-checks is
    not a policy.
    """
    allowed = set(policies["process"]["allowed_runners"])
    used = {str(item["runner"]) for item in capabilities["capabilities"]}
    forbidden = sorted(used - allowed)
    if forbidden:
        raise ProjectCatalogError(
            "policies.process.allowed_runners n’autorise pas le(s) runner(s) déclaré(s) par le catalogue de "
            f"capabilities : {', '.join(forbidden)}."
        )


def _hash(value: Mapping[str, Any]) -> str:
    try:
        return sha256(canonical_json(value).encode("utf-8")).hexdigest()
    except ProfileError as exc:
        raise ProjectCatalogError("Catalogue non sérialisable de façon canonique.") from exc


def load_project_catalogs(profile_path: str | Path) -> ProjectCatalogs:
    """Load all profile-referenced catalog files without executing any declaration."""
    try:
        profile = load_profile(profile_path)
        workspace = resolve_workspace(profile, profile_path)
    except (ProfileError, WorkspaceError) as exc:
        raise ProjectCatalogError("Profile ou workspace invalide pour les catalogues.") from exc
    capabilities = _validate_capabilities(
        _exact_catalog(
            _load_yaml(workspace, profile["capabilities"]["catalog"], "capabilities"),
            "capabilities",
            "vera-capability-catalog/v1",
            "capabilities",
        )
    )
    gates = _validate_gates(
        _exact_catalog(
            _load_yaml(workspace, profile["gates"]["catalog"], "gates"),
            "gates",
            "vera-gate-catalog/v1",
            "gates",
        ),
        capabilities,
    )
    policies = _policy_catalog(_load_yaml(workspace, profile["policies"]["file"], "policies"))
    _validate_declared_runners(capabilities, policies)
    agent_profiles_source = _load_yaml(workspace, profile["integrations"]["agent_profiles"], "agent-profiles")
    agent_profiles = _validate_agent_profiles(agent_profiles_source)
    for integration_id in profile["integrations"]["enabled"]:
        if integration_id not in agent_profiles:
            raise ProjectCatalogError("integrations.enabled référence un Agent Profile absent du catalogue.")
    return ProjectCatalogs(
        capabilities=capabilities,
        gates=gates,
        policies=policies,
        agent_profiles=agent_profiles,
        capability_catalog_hash=_hash(capabilities),
        gate_catalog_hash=_hash(gates),
        policy_hash=_hash(policies),
        agent_profiles_hash=_hash(agent_profiles_source),
    )
