"""Project Profile-driven Resume Dossier compilation (M11)."""

from __future__ import annotations

from typing import Mapping

from .identity import ProfileError, load_profile
from .session_lifecycle import LifecycleError, ResumeDossier, ResumeDossierService, ResumeSectionRequirement
from .store import MemoryStore, StoreError


class ProfileResumeError(StoreError):
    """Raised when the profile resume contract cannot safely produce a dossier."""


def _profile(store: MemoryStore) -> dict[str, object]:
    if not isinstance(store, MemoryStore):
        raise ProfileResumeError("Store invalide pour le Resume Dossier de profil.")
    try:
        return load_profile(store.workspace.profile_path)
    except ProfileError as exc:
        raise ProfileResumeError("Project Profile illisible pour le Resume Dossier.") from exc


def profile_resume_requirements(store: MemoryStore) -> tuple[ResumeSectionRequirement, ...]:
    """Derive bounded hard-guard requirements from required profile sections only."""
    profile = _profile(store)
    resume = profile.get("resume")
    storage = profile.get("storage")
    if not isinstance(resume, Mapping) or not isinstance(storage, Mapping):
        raise ProfileResumeError("Project Profile incomplet pour la reprise.")
    sections = resume.get("sections")
    maximum_total = storage.get("max_resume_bytes", 12_500)
    if not isinstance(sections, list) or not isinstance(maximum_total, int) or isinstance(maximum_total, bool):
        raise ProfileResumeError("Contrat de reprise du Project Profile invalide.")
    required = [section for section in sections if isinstance(section, Mapping) and section.get("required") is True]
    if not required:
        raise ProfileResumeError("Le Project Profile doit exiger au moins une section de reprise.")
    per_section = min(16_384, maximum_total // len(required))
    if per_section < 12:
        raise ProfileResumeError("Budget de reprise insuffisant pour les sections requises.")
    try:
        return tuple(ResumeSectionRequirement(str(section["id"]), 12, per_section) for section in required)
    except (KeyError, TypeError, LifecycleError) as exc:
        raise ProfileResumeError("Sections requises de reprise invalides.") from exc


def compile_profile_resume_dossier(store: MemoryStore, sections: Mapping[str, str]) -> ResumeDossier:
    """Compile the exact profile-required section set into the existing generic dossier."""
    requirements = profile_resume_requirements(store)
    try:
        dossier = ResumeDossierService(store).compile(requirements, sections)
    except LifecycleError as exc:
        raise ProfileResumeError("Resume Dossier incompatible avec le Project Profile.") from exc
    try:
        budget = int(_profile(store)["storage"].get("max_resume_bytes", 12_500))
    except (KeyError, AttributeError, TypeError, ValueError) as exc:
        raise ProfileResumeError("Budget de reprise du Project Profile illisible.") from exc
    if len(dossier.json_text.encode("utf-8")) > budget:
        raise ProfileResumeError("Resume Dossier excède storage.max_resume_bytes.")
    return dossier


def profile_resume_sections(store: MemoryStore, current_state: str) -> dict[str, str]:
    """Create bounded, generic text for exactly the profile-required resume sections."""
    if not isinstance(current_state, str) or current_state != current_state.strip() or len(current_state) < 12:
        raise ProfileResumeError("current_state de reprise invalide.")
    texts = {
        "working-rules": "Mesurer les faits, conserver la provenance et refuser toute conclusion non prouvée.",
        "current-state": current_state,
        "validated-facts": "Consulter uniquement les faits VERA validés et leurs preuves liées avant toute décision.",
        "risks": "Signaler les limites, refus, divergences et validations manquantes sans les masquer.",
        "next-action": "Choisir la prochaine action bornée, la prévisualiser si elle écrit puis confirmer explicitement.",
    }
    return {
        requirement.identifier: texts.get(
            requirement.identifier,
            f"La section {requirement.identifier} doit être revue dans le Project Profile avant la prochaine action.",
        )
        for requirement in profile_resume_requirements(store)
    }
