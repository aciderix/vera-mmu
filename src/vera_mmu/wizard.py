"""The eighteen-step configuration journey, derived from the project (§29.2).

The desktop console was a page of independent buttons: nothing declared what had to exist before
what, and nothing could say where a half-configured project stood. This module states the journey
once — its order, each step's entry criterion, and the evidence that makes a step done — so the
interface renders a state it did not invent.

Everything is derived from what the project carries on disk. No flag is kept anywhere, so closing
the application and reopening it lands on the same step, and asking where the journey stands
writes nothing. That is also why this module reads the declarative files defensively rather than
through the strict loaders: describing a half-configured project is its whole purpose, and it
must not fail on the very state it exists to report.

Six of the eighteen steps leave no trace — scanning, detecting, proposing, previewing the MCP,
validating and running the Doctor all change nothing on disk. They are reported `NOT_OBSERVABLE`
instead of guessed at. A journey that claimed a scan had happened would be inventing the one
thing it cannot see, which is precisely what this product exists to refuse.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import yaml

from .adapter_catalog import ADAPTER_CATALOG
from .store import StoreError


WIZARD_FORMAT = "vera-wizard-state/v1"
RUNTIME_DIR_NAME = ".vera-mmu"

BLOCKED = "BLOCKED"
AVAILABLE = "AVAILABLE"
COMPLETED = "COMPLETED"
NOT_OBSERVABLE = "NOT_OBSERVABLE"


class WizardError(StoreError):
    """Raised when a journey cannot be described for an unambiguous project root."""


@dataclass(frozen=True)
class WizardStep:
    """One step of the journey, its state, and why it is in that state."""

    id: str
    index: int
    label: str
    state: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {"id": self.id, "index": self.index, "label": self.label, "state": self.state, "reason": self.reason}


@dataclass(frozen=True)
class WizardState:
    """Where one project stands in the journey, read-only and derived."""

    format: str
    root: str
    steps: tuple[WizardStep, ...]
    next_step: str | None
    mutation: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "root": self.root,
            "steps": [step.as_dict() for step in self.steps],
            "next_step": self.next_step,
            "mutation": self.mutation,
        }


@dataclass(frozen=True)
class _StepRule:
    """One step's definition: what must exist before it, and what proves it was done."""

    id: str
    index: int
    label: str
    entry: Callable[["_Project"], str | None]
    evidence: Callable[["_Project"], str | None]
    observable: bool = True


@dataclass(frozen=True)
class _Project:
    """Everything the journey needs to read, gathered once and defensively."""

    root: Path
    runtime: Path
    profile: Mapping[str, Any] | None
    profile_error: str | None
    capabilities: int | None
    gates: int | None
    policies: int | None
    generated: int
    host_configuration: tuple[str, ...]

    def section(self, name: str, key: str) -> Any:
        if not isinstance(self.profile, Mapping):
            return None
        block = self.profile.get(name)
        return block.get(key) if isinstance(block, Mapping) else None


def _needs_root(project: _Project) -> str | None:
    return None


def _needs_profile(project: _Project) -> str | None:
    if project.profile is not None:
        return None
    return project.profile_error or "Le Project Profile n’existe pas encore : commencer par choisir un domaine."


def _needs_capability(project: _Project) -> str | None:
    blocked = _needs_profile(project)
    if blocked is not None:
        return blocked
    if not project.capabilities:
        return "Aucune capability déclarée : une gate ne peut porter sur rien."
    return None


def _needs_generated(project: _Project) -> str | None:
    blocked = _needs_capability(project)
    if blocked is not None:
        return blocked
    if project.generated == 0:
        return "Rien n’a encore été généré : installer n’aurait aucun contenu à écrire."
    return None


def _declared(name: str, key: str, message: str) -> Callable[[_Project], str | None]:
    """Completed when the profile declares a non-empty section."""
    def evidence(project: _Project) -> str | None:
        value = project.section(name, key)
        if isinstance(value, (list, tuple)) and value:
            return None
        if value is True:
            return None
        return message
    return evidence


def _counted(attribute: str, message: str) -> Callable[[_Project], str | None]:
    def evidence(project: _Project) -> str | None:
        value = getattr(project, attribute)
        if value is None:
            return f"{message} Le catalogue déclaré est illisible."
        return None if value > 0 else message
    return evidence


def _domain_declared(project: _Project) -> str | None:
    domain = project.section("project", "domain")
    if isinstance(domain, str) and domain.strip():
        return None
    return "Aucun domaine déclaré dans le Project Profile."


def _installed(project: _Project) -> str | None:
    if project.host_configuration:
        return None
    return "Aucune configuration hôte project-local observée."


def _never_observable(project: _Project) -> str | None:
    return "Cette étape ne laisse aucune trace : son exécution n’est pas observable."


WIZARD_STEPS: tuple[_StepRule, ...] = (
    _StepRule("scan-project", 1, "Scanner le projet", _needs_root, _never_observable, observable=False),
    _StepRule("detect-structure", 2, "Détecter la structure", _needs_root, _never_observable, observable=False),
    _StepRule("propose-profile", 3, "Proposer un profil", _needs_root, _never_observable, observable=False),
    _StepRule("choose-domain", 4, "Choisir le domaine", _needs_root, _domain_declared),
    _StepRule("edit-taxonomy", 5, "Modifier la taxonomie", _needs_profile,
              _declared("knowledge", "types", "Aucun type de connaissance déclaré.")),
    _StepRule("define-entities", 6, "Définir les entités", _needs_profile,
              _declared("entities", "types", "Aucun type d’entité déclaré.")),
    _StepRule("define-relations", 7, "Définir les relations", _needs_profile,
              _declared("relations", "types", "Aucun type de relation déclaré.")),
    _StepRule("configure-work-graph", 8, "Configurer le Work Graph", _needs_profile,
              _declared("work", "enabled", "Le Work Graph n’est pas activé par le Project Profile.")),
    _StepRule("declare-capabilities", 9, "Déclarer les capabilities", _needs_profile,
              _counted("capabilities", "Aucune capability déclarée.")),
    _StepRule("build-gates", 10, "Construire les gates", _needs_capability,
              _counted("gates", "Aucune gate déclarée.")),
    _StepRule("define-policies", 11, "Définir les policies", _needs_profile,
              _counted("policies", "Aucune policy déclarée.")),
    _StepRule("configure-resume", 12, "Configurer le Resume", _needs_profile,
              _declared("resume", "sections", "Aucune section de reprise déclarée.")),
    _StepRule("choose-integrations", 13, "Choisir les intégrations", _needs_profile,
              _declared("integrations", "enabled", "Aucune intégration activée par le Project Profile.")),
    _StepRule("preview-mcp", 14, "Prévisualiser le MCP", _needs_capability, _never_observable, observable=False),
    _StepRule("validate", 15, "Valider", _needs_profile, _never_observable, observable=False),
    _StepRule("generate", 16, "Générer", _needs_capability,
              _counted("generated", "Aucun artefact généré sous `.vera-mmu/generated/`.")),
    _StepRule("install", 17, "Installer", _needs_generated, _installed),
    _StepRule("run-doctor", 18, "Lancer Doctor", _needs_profile, _never_observable, observable=False),
)


def wizard_state(root: str | Path) -> WizardState:
    """Describe where one project stands in the journey, reading only, writing nothing."""
    source = Path(root).expanduser()
    if source.is_symlink():
        raise WizardError("Racine de projet symlinkée refusée.")
    try:
        resolved = source.resolve(strict=True)
    except OSError as exc:
        raise WizardError("Racine de projet introuvable.") from exc
    if not resolved.is_dir():
        raise WizardError("Racine de projet non répertoire.")

    project = _read(resolved)
    steps: list[WizardStep] = []
    for rule in WIZARD_STEPS:
        blocked = rule.entry(project)
        if blocked is not None:
            steps.append(WizardStep(rule.id, rule.index, rule.label, BLOCKED, blocked))
            continue
        missing = rule.evidence(project)
        if missing is None:
            steps.append(WizardStep(rule.id, rule.index, rule.label, COMPLETED, ""))
        elif rule.observable:
            steps.append(WizardStep(rule.id, rule.index, rule.label, AVAILABLE, missing))
        else:
            steps.append(WizardStep(rule.id, rule.index, rule.label, NOT_OBSERVABLE, missing))
    following = next((step.id for step in steps if step.state == AVAILABLE), None)
    return WizardState(WIZARD_FORMAT, str(resolved), tuple(steps), following)


def _read(root: Path) -> _Project:
    """Gather the project's declarations without ever failing on a broken one."""
    runtime = root / RUNTIME_DIR_NAME
    profile: Mapping[str, Any] | None = None
    profile_error: str | None = None
    profile_path = runtime / "project.yaml"
    if runtime.is_dir() and not runtime.is_symlink() and profile_path.is_file() and not profile_path.is_symlink():
        try:
            loaded = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            profile_error = f"Project Profile illisible : {exc.__class__.__name__}."
        else:
            if isinstance(loaded, Mapping) and isinstance(loaded.get("project"), Mapping):
                profile = loaded
            else:
                profile_error = "Project Profile présent mais incomplet : sa section `project` est absente."
    generated_dir = runtime / "generated"
    generated = 0
    if generated_dir.is_dir() and not generated_dir.is_symlink():
        generated = sum(1 for item in generated_dir.iterdir() if item.is_file() and not item.is_symlink())
    return _Project(
        root=root,
        runtime=runtime,
        profile=profile,
        profile_error=profile_error,
        capabilities=_count(runtime / "capabilities.yaml", "capabilities"),
        gates=_count(runtime / "gates.yaml", "gates"),
        policies=_count_policies(runtime / "policies.yaml"),
        generated=generated,
        host_configuration=_host_configuration(root),
    )


def _count(path: Path, key: str) -> int | None:
    """Count one catalog's declared entries; `None` means the file exists but cannot be read."""
    if not path.is_file() or path.is_symlink():
        return 0
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    if not isinstance(loaded, Mapping):
        return None
    entries = loaded.get(key)
    return len(entries) if isinstance(entries, (list, tuple)) else None


def _count_policies(path: Path) -> int | None:
    """Count the declared policy domains.

    The policy catalog is not a list under one key: each policy is its own top-level section —
    `filesystem`, `network`, `process` and so on — beside the format marker. Counting a
    `policies:` key that the format never had would have reported every healthy project as
    unreadable.
    """
    if not path.is_file() or path.is_symlink():
        return 0
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    if not isinstance(loaded, Mapping):
        return None
    return sum(1 for key in loaded if key != "format")


def _host_configuration(root: Path) -> tuple[str, ...]:
    """Name the declared host configuration files that exist, project-local only.

    The adapter catalog states each configuration in a readable form — one path, or several
    joined by `+`. Splitting it here keeps the catalog the single place where those paths live.
    """
    found: set[str] = set()
    for spec in ADAPTER_CATALOG.values():
        for candidate in str(spec.config).split("+"):
            relative = candidate.strip()
            if not relative:
                continue
            target = root / relative
            if target.is_file() and not target.is_symlink():
                found.add(relative)
    return tuple(sorted(found))
