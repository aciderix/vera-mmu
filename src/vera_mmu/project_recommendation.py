"""Propose a project profile from a scan report, and propose only (§31).

The specification is explicit: «l'utilisateur peut modifier chaque élément». So this module
argues, it does not decide. It reads one `ScanReport`, proposes a template, a set of capabilities
and the gates those capabilities could satisfy, attaches to each proposal the observations that
support it, and writes nothing anywhere.

Three boundaries hold it honest.

A proposal never carries a command, a path, a URL or a runner. Naming a `lint` capability is not
the same act as saying what lint runs: the first is an observation about the project's shape, the
second is a decision only its owner may take, and I008 forbids this side of the line from taking
it. The capability builder is where a runner gets bound, under preview and confirmation.

Nothing is inferred that the scanner did not observe. §31's own example proposes a `build`
capability for a tree whose build step lives inside a manifest's scripts — reading that manifest
is exactly what §30 forbids the scanner to do, so `build` is proposed here only when a build
marker was actually seen. The gap is recorded in `notes` rather than filled by a guess.

A template that could not be deduced is named as a default and says so. A fallback presented as
a deduction would be the fabrication the whole product exists to prevent.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .project_scan import ScanReport
from .store import StoreError


RECOMMENDATION_FORMAT = "vera-profile-recommendation/v1"

# `research` is deliberately absent: nothing in a file name distinguishes a research project from
# any other, and recommending it would be a guess dressed as an observation. It stays available
# to choose by hand.
_INFERABLE_TEMPLATES = ("hardware", "game", "data", "documentation", "software")


class RecommendationError(StoreError):
    """Raised when a recommendation cannot be derived from a valid scan report."""


@dataclass(frozen=True)
class CapabilityProposal:
    """One capability the project's shape suggests — declarative, never bound to a runner."""

    id: str
    label: str
    kind: str
    description: str
    rationale: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "description": self.description,
            "rationale": list(self.rationale),
            "editable": True,
        }


@dataclass(frozen=True)
class GateProposal:
    """One gate the proposed capability could satisfy, with the verdict it would require."""

    id: str
    label: str
    capability_id: str
    expected_verdict: str
    rationale: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "capability_id": self.capability_id,
            "expected_verdict": self.expected_verdict,
            "rationale": list(self.rationale),
            "editable": True,
        }


@dataclass(frozen=True)
class ProfileRecommendation:
    """What the scan suggests, bound to the report it read. Every element is modifiable."""

    format: str
    report_hash: str
    template: str
    template_rationale: tuple[str, ...]
    capabilities: tuple[CapabilityProposal, ...]
    gates: tuple[GateProposal, ...]
    notes: tuple[str, ...]
    recommendation_hash: str
    status: str = "PROPOSED"
    mutation: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "report_hash": self.report_hash,
            "template": self.template,
            "template_rationale": list(self.template_rationale),
            "capabilities": [item.as_dict() for item in self.capabilities],
            "gates": [item.as_dict() for item in self.gates],
            "notes": list(self.notes),
            "status": self.status,
            "mutation": self.mutation,
            "editable": True,
        }


# One capability per observable workflow, with the markers that would evidence it. `build` is
# bound to real build markers only, never inferred from a manifest nobody opened.
_CAPABILITY_RULES: tuple[tuple[str, str, str, str, tuple[str, ...], tuple[tuple[str, str], ...]], ...] = (
    ("install", "Installation des dépendances", "ACTION",
     "Installe les dépendances déclarées par le gestionnaire observé.",
     ("dependency-manager",), ()),
    ("build", "Construction du projet", "ACTION",
     "Construit le projet selon le script de build observé.",
     ("build-script",), (("framework", "vite"), ("framework", "next"), ("framework", "nuxt"), ("framework", "astro"))),
    ("test", "Suite de tests", "CHECK",
     "Exécute la suite de tests dont un marqueur a été observé.",
     ("tests",), ()),
    ("lint", "Analyse statique de style", "CHECK",
     "Applique la configuration de linter observée dans le projet.",
     ("linter",), ()),
    ("typecheck", "Vérification de types", "CHECK",
     "Vérifie les types du projet dans le langage typé observé.",
     (), (("language", "typescript"), ("linter", "mypy"), ("language", "kotlin"), ("language", "rust"))),
    ("e2e", "Tests de bout en bout", "CHECK",
     "Exécute le harnais de bout en bout dont un marqueur a été observé.",
     (), (("tests", "playwright"), ("tests", "cypress"), ("tests", "karma"))),
    ("package", "Empaquetage distribuable", "ACTION",
     "Produit l’artefact distribuable correspondant au format observé.",
     ("container",), ()),
)

_GATE_RULES: dict[str, tuple[str, str]] = {
    "install": ("INSTALL_OK", "Dépendances installées"),
    "build": ("BUILD_OK", "Construction réussie"),
    "test": ("UNIT_TESTS_OK", "Suite de tests au vert"),
    "lint": ("LINT_OK", "Analyse statique au vert"),
    "typecheck": ("TYPECHECK_OK", "Types vérifiés"),
    "e2e": ("E2E_OK", "Parcours de bout en bout au vert"),
    "package": ("PACKAGE_OK", "Artefact distribuable produit"),
}


def recommend_profile(report: ScanReport) -> ProfileRecommendation:
    """Derive one deterministic proposal from a scan report, writing nothing."""
    if not isinstance(report, ScanReport):
        raise RecommendationError("Recommandation impossible : rapport de scan invalide.")
    if report.format != "vera-scan-report/v2":
        raise RecommendationError(f"Format de rapport de scan non pris en charge : {report.format}.")

    markers = {(item.kind, item.marker) for item in report.observations}
    categories = {item.kind for item in report.observations}
    counts: dict[str, int] = {}
    for item in report.observations:
        counts[item.kind] = counts.get(item.kind, 0) + 1

    template, template_rationale, notes = _template(markers, categories, counts)
    capabilities = _capabilities(markers, categories)
    gates = tuple(
        GateProposal(_GATE_RULES[item.id][0], _GATE_RULES[item.id][1], item.id, "PASS", item.rationale)
        for item in capabilities
        if item.id in _GATE_RULES
    )
    if capabilities and not any(item.id == "build" for item in capabilities):
        notes = notes + (
            "Aucune capability `build` proposée : aucun marqueur de script de build n’a été observé, "
            "et déduire une étape de build du contenu d’un manifeste sortirait de ce que le scan lit.",
        )

    body = {
        "format": RECOMMENDATION_FORMAT,
        "report_hash": report.report_hash,
        "template": template,
        "template_rationale": list(template_rationale),
        "capabilities": [item.as_dict() for item in capabilities],
        "gates": [item.as_dict() for item in gates],
        "notes": list(notes),
    }
    digest = sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return ProfileRecommendation(
        format=RECOMMENDATION_FORMAT,
        report_hash=report.report_hash,
        template=template,
        template_rationale=template_rationale,
        capabilities=capabilities,
        gates=gates,
        notes=notes,
        recommendation_hash=digest,
    )


def _template(
    markers: set[tuple[str, str]], categories: set[str], counts: dict[str, int],
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    """Name a template and say on what, or name the default and say that it is one."""
    notes = (
        "Le template `research` n’est jamais recommandé automatiquement : aucun nom de fichier ne "
        "distingue un projet de recherche d’un autre. Il reste disponible au choix.",
    )
    for marker in (("framework", "platformio"), ("framework", "kicad"), ("language", "arduino")):
        if marker in markers:
            return "hardware", (f"marqueur `{marker[0]}:{marker[1]}` observé",), notes
    if ("framework", "godot") in markers:
        return "game", ("marqueur `framework:godot` observé",), notes
    if "dataset" in categories and (("framework", "jupyter") in markers or counts.get("dataset", 0) >= 3):
        reasons = [f"{counts['dataset']} marqueurs de dataset observés"]
        if ("framework", "jupyter") in markers:
            reasons.append("marqueur `framework:jupyter` observé")
        return "data", tuple(reasons), notes
    if "documentation" in categories and "language" not in categories:
        return "documentation", (
            f"{counts['documentation']} marqueurs de documentation observés, aucun langage source observé",
        ), notes
    if "language" in categories or "dependency-manager" in categories:
        reasons = []
        if "language" in categories:
            reasons.append(f"{counts['language']} langage(s) source observé(s)")
        if "dependency-manager" in categories:
            reasons.append(f"{counts['dependency-manager']} gestionnaire(s) de dépendances observé(s)")
        return "software", tuple(reasons), notes
    return "software", (
        "template `software` retenu par défaut : aucun marqueur observé ne permet de déduire un domaine",
    ), notes


def _capabilities(markers: set[tuple[str, str]], categories: set[str]) -> tuple[CapabilityProposal, ...]:
    """Propose one capability per workflow the tree actually evidences."""
    proposals: list[CapabilityProposal] = []
    for identifier, label, kind, description, required_categories, required_markers in _CAPABILITY_RULES:
        rationale = [f"catégorie `{name}` observée" for name in required_categories if name in categories]
        rationale += [f"marqueur `{kind_}:{marker}` observé" for kind_, marker in required_markers if (kind_, marker) in markers]
        if rationale:
            proposals.append(CapabilityProposal(identifier, label, kind, description, tuple(sorted(rationale))))
    return tuple(proposals)
