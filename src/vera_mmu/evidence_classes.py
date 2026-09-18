"""The three classes §33 requires a gate to distinguish, and what each one may do.

§33 asks the Dashboard to show clearly the difference between **technical validation**,
**semantic appreciation** and **simple observation**. A colour would not be that difference: a
rule an interface draws stops existing the moment the CLI, the MCP server or another agent writes.
So the distinction lives here, derived from `evidence.TYPES` — a closed, stored catalogue — and it
is enforced where a lie would otherwise be created: at promotion.

**The hole it closes.** Nothing in the promotion chain looked at what an evidence *was*. A
`HUMAN_ASSERTION` recorded `PASS` and admitted promoted a knowledge to `PROVEN` exactly like a
`TEST_PROOF`. That is an opinion filed as a proof, which is the single thing this product exists
to prevent (I004, I006).

**Why the class is derived rather than stored.** The evidence type is already persisted, already
closed, and already immutable. A second column holding the class could disagree with it — and
whichever of the two was read would decide whether an opinion counts as a proof. Deriving it
leaves nothing to drift.

**Why two classes share one consequence without being one class.** Neither an observation nor an
appreciation can create a proof, but they are refused for different reasons, and the difference is
what tells someone what to do next: an observation is a fact the Core never re-derived — add a
check; an appreciation is a judgment no rerun can reproduce — it is not a check at all. Collapsing
them would say « cannot promote » without saying which.
"""
from __future__ import annotations

from .evidence import TYPES as EVIDENCE_TYPES


TECHNICAL_VALIDATION = "TECHNICAL_VALIDATION"
SIMPLE_OBSERVATION = "SIMPLE_OBSERVATION"
SEMANTIC_APPRECIATION = "SEMANTIC_APPRECIATION"

EVIDENCE_CLASSES = (TECHNICAL_VALIDATION, SIMPLE_OBSERVATION, SEMANTIC_APPRECIATION)

# Every type of `evidence.TYPES`, classified by what the Core can say about its verdict.
#
# TECHNICAL_VALIDATION — the verdict follows from something checkable: an exit code, a hash, a
#   test run, a stored file. A rerun can contradict it.
# SIMPLE_OBSERVATION — something was recorded as it was seen. The number or the attestation may be
#   exact and still not decide anything; the Core never derived the verdict from it.
# SEMANTIC_APPRECIATION — a judgment, by a person or by a model. No rerun reproduces it.
CLASS_BY_EVIDENCE_TYPE: dict[str, str] = {
    "COMMAND_PROOF": TECHNICAL_VALIDATION,
    "TEST_PROOF": TECHNICAL_VALIDATION,
    "CI_PROOF": TECHNICAL_VALIDATION,
    "API_PROOF": TECHNICAL_VALIDATION,
    "HASH_PROOF": TECHNICAL_VALIDATION,
    "FILE_PROOF": TECHNICAL_VALIDATION,
    "METRIC_PROOF": SIMPLE_OBSERVATION,
    "EXTERNAL_ATTESTATION": SIMPLE_OBSERVATION,
    "HUMAN_ASSERTION": SEMANTIC_APPRECIATION,
    "MODEL_EVALUATION": SEMANTIC_APPRECIATION,
}

_REASONS = {
    TECHNICAL_VALIDATION: "Le verdict découle d’un contrôle rejouable : il peut fonder une preuve.",
    SIMPLE_OBSERVATION: (
        "Une observation enregistre ce qui a été vu ; le Core n’en a dérivé aucun verdict, "
        "donc elle ne peut pas fonder une preuve."
    ),
    SEMANTIC_APPRECIATION: (
        "Une appréciation est un jugement qu’aucune réexécution ne reproduit ; "
        "la ranger comme preuve ferait passer une opinion pour un fait vérifié."
    ),
}


class EvidenceClassError(ValueError):
    """Raised when an evidence type carries no class, which must never be silently allowed."""


def classify(evidence_type: str) -> str:
    """Return the §33 class of one evidence type, or refuse rather than guess."""
    if not isinstance(evidence_type, str) or evidence_type not in CLASS_BY_EVIDENCE_TYPE:
        raise EvidenceClassError(f"Type d’evidence non classé : {evidence_type!r}.")
    return CLASS_BY_EVIDENCE_TYPE[evidence_type]


def may_create_proof(evidence_type: str) -> bool:
    """Only a technical validation may back a promotion to `PROVEN` (I004, I006)."""
    return classify(evidence_type) == TECHNICAL_VALIDATION


def reason(evidence_class: str) -> str:
    """Say, in the Core's own words, what this class may found and why."""
    if evidence_class not in _REASONS:
        raise EvidenceClassError(f"Classe d’evidence inconnue : {evidence_class!r}.")
    return _REASONS[evidence_class]


def describe(evidence_type: str) -> dict[str, object]:
    """Report one evidence type as §33 displays it: its class, and what it may found."""
    evidence_class = classify(evidence_type)
    return {
        "evidence_type": evidence_type,
        "evidence_class": evidence_class,
        "may_create_proof": evidence_class == TECHNICAL_VALIDATION,
        "reason": _REASONS[evidence_class],
    }


def unclassified_types() -> tuple[str, ...]:
    """Evidence types the Core admits but this module does not classify. Must stay empty."""
    return tuple(sorted(EVIDENCE_TYPES - set(CLASS_BY_EVIDENCE_TYPE)))
