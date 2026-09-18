"""The closed value set of `policies.yaml`, and what actually enforces each line (§21, §29.2 step 11).

**What the measurement showed.** The policy catalogue validated its *shape* — seven sections, each
a mapping — and almost none of its *values*. A project could write `network: {default: allow}`,
`destructive: {default: allow}` or `promotion: {proven_requires: []}`, the loader accepted it, the
Doctor reported « Catalogue de policies valide », and none of it meant anything. Worse than an
unenforced rule: a file stating a permission the engine never grants.

So this module does two things, and keeps them apart on purpose.

**It closes the values.** Every line may only hold something the Core can honour. `network.default`
may only be `deny`, because the Core holds no network path at all and `capability_contract`
constrains its network policy to `DENY_NETWORK` in SQL — offering `allow` would let a project
declare a permission nothing can grant. `destructive.default` may not be `allow`, because a
destructive write that announces itself as silently permitted is the one shape this product
refuses. `proven_requires` may not claim less than what promotion actually checks.

**It says which lines are enforced, and does not pretend about the rest.** Each line carries an
`enforcement` status naming the module that reads it, or `DECLARED_ONLY` saying plainly that
nothing does. Reporting `ENFORCED` everywhere would be the same lie in a new place; leaving the
distinction out would leave whoever edits the file unable to tell a rule from a wish.
"""
from __future__ import annotations

from typing import Any, Mapping


POLICY_CATALOG_FORMAT = "vera-policy-catalog/v1"

# The three-valued decision §21 uses, and I013 requires to be explicit.
DECISIONS = ("allow", "confirm", "deny")
# Conditions the Core actually checks before writing a `PROVEN` proof. A project may not declare
# fewer: `promote` enforces both unconditionally, and a shorter list would describe an engine that
# does not exist.
PROVEN_CONDITIONS = ("admissible_pass", "technical_validation")

ENFORCED = "ENFORCED"
DECLARED_ONLY = "DECLARED_ONLY"


class PolicyCatalogError(ValueError):
    """Raised when a declared policy value is outside what the Core can honour."""


# section → key → (allowed values or None for a list line, enforcement, who enforces it)
POLICY_LINES: dict[str, dict[str, dict[str, Any]]] = {
    "filesystem": {
        "read": {
            "values": DECISIONS,
            "enforcement": DECLARED_ONLY,
            "reason": "Aucun module ne consulte `filesystem.read` : la lecture project-local est déjà bornée par le workspace.",
        },
        "write": {
            "values": DECISIONS,
            "enforcement": ENFORCED,
            "reason": "`project_policy.require_project_write` refuse toute écriture projet si la valeur est `deny`.",
        },
    },
    "network": {
        "default": {
            "values": ("deny",),
            "enforcement": ENFORCED,
            "reason": (
                "Le Core ne tient aucun chemin réseau et `capability_contract` contraint sa policy réseau à "
                "`DENY_NETWORK` en SQL : `deny` est la seule valeur que le moteur puisse honorer."
            ),
        },
    },
    "process": {
        "allowed_runners": {
            "values": None,
            "enforcement": ENFORCED,
            "reason": "Une capability dont le runner n’est pas listé ici est refusée au chargement du catalogue.",
        },
    },
    "git": {
        "commit": {
            "values": DECISIONS,
            "enforcement": ENFORCED,
            "reason": (
                "`memory_sync` refuse de committer si la valeur est `deny`. Elle ne peut que restreindre : "
                "`sync-policy.json` décide séparément si la synchronisation est automatique."
            ),
        },
        "push": {
            "values": DECISIONS,
            "enforcement": ENFORCED,
            "reason": "`memory_sync` refuse de pousser si la valeur est `deny`, après un commit par ailleurs autorisé.",
        },
    },
    "destructive": {
        "default": {
            # `allow` is absent on purpose: a destructive operation that announces itself as
            # silently permitted is exactly what every write path here refuses.
            "values": ("confirm", "deny"),
            "enforcement": DECLARED_ONLY,
            "reason": (
                "Aucun module ne consulte `destructive.default` : chaque opération destructive exige déjà sa "
                "propre confirmation explicite. La valeur `allow` reste indéclarable."
            ),
        },
    },
    "promotion": {
        "proven_requires": {
            "values": None,
            "enforcement": ENFORCED,
            "reason": (
                "`ProofService.promote` exige une evidence PASS admise **et** une validation technique. "
                "La liste enregistre ce que le moteur garantit ; elle ne peut pas en déclarer moins."
            ),
        },
    },
}

SECTIONS = tuple(POLICY_LINES)


def validate_policy_values(catalog: Mapping[str, Any], *, runners: frozenset[str]) -> None:
    """Refuse any policy value the Core cannot honour. Raises on the first one."""
    for section, lines in POLICY_LINES.items():
        block = catalog.get(section)
        if not isinstance(block, Mapping):
            raise PolicyCatalogError(f"policies.{section} doit être un objet.")
        if set(block) != set(lines):
            raise PolicyCatalogError(f"policies.{section} doit déclarer exactement {', '.join(sorted(lines))}.")
        for key, rule in lines.items():
            value = block[key]
            if rule["values"] is not None:
                if value not in rule["values"]:
                    raise PolicyCatalogError(
                        f"policies.{section}.{key} = {value!r} hors catalogue fermé "
                        f"({', '.join(rule['values'])}). {rule['reason']}"
                    )
            elif section == "process":
                _validate_allowed_runners(value, runners)
            else:
                _validate_proven_requires(value)


def _validate_allowed_runners(value: Any, runners: frozenset[str]) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise PolicyCatalogError("policies.process.allowed_runners doit être une liste de chaînes.")
    if len(value) != len(set(value)):
        raise PolicyCatalogError("policies.process.allowed_runners ne doit pas contenir de doublon.")
    unknown = sorted(set(value) - runners)
    if unknown:
        raise PolicyCatalogError(
            f"policies.process.allowed_runners nomme un runner que le Core n’a pas : {', '.join(unknown)}."
        )


def _validate_proven_requires(value: Any) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise PolicyCatalogError("policies.promotion.proven_requires doit être une liste de chaînes.")
    declared = set(value)
    if len(value) != len(declared):
        raise PolicyCatalogError("policies.promotion.proven_requires ne doit pas contenir de doublon.")
    unknown = sorted(declared - set(PROVEN_CONDITIONS))
    if unknown:
        raise PolicyCatalogError(
            f"policies.promotion.proven_requires nomme une condition que le Core ne vérifie pas : {', '.join(unknown)}."
        )
    missing = sorted(set(PROVEN_CONDITIONS) - declared)
    if missing:
        # Omitting one would declare a looser engine than the one that runs, which is the exact
        # shape of lie §33 closed at promotion.
        raise PolicyCatalogError(
            f"policies.promotion.proven_requires ne peut pas déclarer moins que ce que la promotion exige : "
            f"{', '.join(missing)} manquant."
        )


def describe_policies(catalog: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Report every policy line with its value, its closed set and what enforces it."""
    described: list[dict[str, Any]] = []
    for section, lines in POLICY_LINES.items():
        block = catalog.get(section)
        for key, rule in lines.items():
            described.append(
                {
                    "section": section,
                    "key": key,
                    "value": block.get(key) if isinstance(block, Mapping) else None,
                    "values": list(rule["values"]) if rule["values"] is not None else None,
                    "editable": True,
                    "enforcement": rule["enforcement"],
                    "reason": rule["reason"],
                }
            )
    return described
