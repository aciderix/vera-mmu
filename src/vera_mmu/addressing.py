"""Strict, transport-neutral VERA resource addressing (M1, C01).

Only canonical ``vera://<project>/<resource>/<identifier>`` addresses are accepted.
The module does not resolve resources or infer identifiers; it only validates and
normalizes a small Core-owned address contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, unquote

from .identity import PROJECT_ID_RE


CORE_RESOURCE_TYPES = frozenset(
    {
        "asset",
        "capability",
        "entity",
        "evidence",
        "execution",
        "front",
        "handoff",
        "knowledge",
        "profile",
        "relation",
        "symbol",
        "work-item",
    }
)


class AddressError(ValueError):
    """Raised when an address is invalid, unsafe, or non-canonical."""


def _validate_resource_type(resource_type: str) -> str:
    if not isinstance(resource_type, str) or resource_type not in CORE_RESOURCE_TYPES:
        raise AddressError("Type de ressource VERA inconnu ou non autorisé.")
    return resource_type


def _validate_identifier(identifier: str) -> str:
    if not isinstance(identifier, str) or not identifier:
        raise AddressError("Identifiant de ressource VERA requis.")
    if len(identifier) > 256 or "/" in identifier or "\\" in identifier or "\x00" in identifier:
        raise AddressError("Identifiant de ressource VERA invalide.")
    if identifier in {".", ".."} or ".." in identifier.split("/"):
        raise AddressError("Identifiant de ressource VERA traversant interdit.")
    return identifier


@dataclass(frozen=True)
class Address:
    """One validated VERA resource address."""

    project_id: str
    resource_type: str
    identifier: str

    @property
    def canonical(self) -> str:
        return make_address(self.project_id, self.resource_type, self.identifier)


def make_address(project_id: str, resource_type: str, identifier: str) -> str:
    """Build one canonical VERA address without accepting ambiguous components."""
    if not isinstance(project_id, str) or not PROJECT_ID_RE.fullmatch(project_id):
        raise AddressError("Identifiant de projet VERA invalide.")
    resource = _validate_resource_type(resource_type)
    value = _validate_identifier(identifier)
    return f"vera://{project_id}/{resource}/{quote(value, safe='!._~-')}"


def parse_address(address: str) -> Address:
    """Parse exactly one canonical VERA address and reject aliases or heuristics."""
    if not isinstance(address, str) or not address.startswith("vera://"):
        raise AddressError("Adresse invalide : le préfixe vera:// est requis.")
    parts = address[len("vera://") :].split("/", 2)
    if len(parts) != 3:
        raise AddressError("Adresse VERA invalide : projet, ressource et identifiant sont requis.")
    project_id, resource_type, encoded_identifier = parts
    if not PROJECT_ID_RE.fullmatch(project_id):
        raise AddressError("Identifiant de projet VERA invalide.")
    if not encoded_identifier:
        raise AddressError("Identifiant de ressource VERA requis.")
    try:
        identifier = unquote(encoded_identifier, encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AddressError("Encodage d’identifiant VERA invalide.") from exc
    canonical = make_address(project_id, resource_type, identifier)
    if address != canonical:
        raise AddressError("Adresse VERA non canonique.")
    return Address(project_id=project_id, resource_type=resource_type, identifier=identifier)


def parse_compat_address(address: str) -> Address:
    """Accept one strict `mmu://` transition alias and normalize it to canonical VERA.

    The alias is input-only: persistent identities and every returned address remain `vera://`
    until an explicit storage/address migration exists. No historical or domain scheme is parsed.
    """
    if not isinstance(address, str):
        raise AddressError("Adresse de compatibilité VERA invalide.")
    if address.startswith("vera://"):
        return parse_address(address)
    if address.startswith("mmu://"):
        return parse_address("vera://" + address[len("mmu://") :])
    raise AddressError("Adresse de compatibilité invalide : vera:// ou mmu:// requis.")
