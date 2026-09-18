"""Test de parité du couplage `C01` — adressage ARET V1 contre lecteur de compatibilité VERA.

Le registre de découplage exige, pour promouvoir `C01`, des « fixtures de round-trip VERA et ARET,
encodage d'identifiants, rejet de schéma/type/injection non canoniques ». Un test de compatibilité
existait déjà — `test_aret_address_compatibility.py` — mais il compare la réimplémentation VERA à
**ses propres attentes**. Il passerait à l'identique si les deux modules divergeaient, parce qu'il
n'a jamais exécuté celui d'ARET. Ce n'est pas un test de parité : c'est un test de cohérence interne.

Celui-ci exécute **les deux implémentations** et compare leurs verdicts. La référence est une copie
octet pour octet de `core/addressing.py`, versionnée sous `fixtures/aret_v1/` avec son SHA-256
épinglé ici : si la copie dérive de l'amont, le test échoue plutôt que de comparer VERA à une
référence périmée en silence.

**La parité affirmée est dirigée, et c'est le cœur du lot.** Un lecteur de compatibilité doit relire
tout ce que l'original savait écrire — sinon une mémoire existante devient partiellement illisible.
Il ne doit **jamais** accepter ce que l'original refusait — sinon il élargit la surface V1 au lieu de
la lire. Les deux directions sont mesurées séparément, parce qu'elles n'ont pas la même gravité :
la première est une régression de lecture, la seconde est une invention.

Là où VERA est plus strict, il l'est sur des formes qu'`ARET.make_address` **ne peut pas produire** :
identifiants non encodés, séquences `%` non canoniques, caractères non ASCII bruts. Le test le
constate au lieu de l'affirmer, et vérifie que ces formes sont bien hors de l'image de l'écrivain V1.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import unittest

from vera_mmu.domain_packs.aret import addressing as pack


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "aret_v1"
REFERENCE = FIXTURES / "addressing_reference.py"

#: SHA-256 de `core/addressing.py` dans `aciderix/ARET-MMU` au commit épinglé par le README voisin.
REFERENCE_SHA256 = "ebd735929e0e81240b14bc37fb37a668d8532015a59a0b5fd93336cfeb2bbb68"
#: Empreinte et taille de la mémoire baseline dont proviennent les adresses réelles.
BASELINE_SHA256 = "85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5"
BASELINE_BYTES = 11280384

#: Identifiants couvrant le canonique, l'encodé, le non canonique, le traversant et le non ASCII.
IDENTIFIERS = (
    "KN-001", "comp.name", "sym!_-.42", "alpha beta", "alpha%20beta", "%41", "%ZZ", "100%",
    "a/b", "a%2fb", "a%2Fb", "", "..", "é", "日本", "a+b", "a~b", "a?b", "a#b", "a b c",
    "x" * 300, "a%00b",
)
#: Les huit types fermés d'ARET, plus `front`, un type inconnu et le type vide.
RESOURCE_TYPES = (
    "knowledge", "component", "function", "brick", "proof", "relation", "asset", "pipeline",
    "front", "unknown", "",
)
#: Formes brutes qu'aucun couple (type, identifiant) ne génère.
RAW_ADDRESSES = (
    "ARET://front/current", "ARET://front/current/extra", "ARET://", "ARET://knowledge",
    "aret://knowledge/x", "vera://p/knowledge/x", "ARET://knowledge/x/y", "ARET:///x",
    "ARET://knowledge//x", "ARET://KNOWLEDGE/x", "ARET://knowledge/../x",
)


def _load_reference():
    """Charger la référence ARET comme module isolé, sans l'ajouter aux dépendances du Core."""
    spec = importlib.util.spec_from_file_location("aret_v1_addressing_reference", REFERENCE)
    module = importlib.util.module_from_spec(spec)
    # Les dataclasses résolvent leurs annotations via `sys.modules`; sans cet enregistrement le
    # chargement échoue sur `@dataclass`, et le test se croirait incapable de lire sa référence.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ARET = _load_reference()


def _verdict(function, *arguments):
    """Réduire un appel à ce qui se compare : accepté avec quelle valeur, ou refusé.

    Les classes d'exception ne sont **pas** comparées. `AretAddressCompatibilityError` hérite de
    `ValueError`, donc exiger le même nom de classe ferait échouer deux refus identiques — une
    divergence de forme prise pour une divergence de comportement.
    """
    try:
        return ("ACCEPTE", function(*arguments))
    except ValueError:
        return ("REFUSE", None)


def _parsed(function, address):
    """Le verdict d'un parse, réduit au couple (type, identifiant) réellement retourné."""
    state, value = _verdict(function, address)
    if state != "ACCEPTE":
        return (state, None, None)
    return (state, value.resource_type, value.identifier)


class AretC01AddressingParityTests(unittest.TestCase):
    # --- la référence elle-même --------------------------------------------

    def test_the_reference_is_the_pinned_aret_source(self) -> None:
        """Sans cela, la parité serait mesurée contre une copie dont plus personne ne sait l'âge."""
        self.assertEqual(sha256(REFERENCE.read_bytes()).hexdigest(), REFERENCE_SHA256)
        self.assertEqual(sorted(ARET.SCHEMES), sorted(pack.ARET_RESOURCE_TYPES))

    def test_the_baseline_corpus_declares_the_memory_it_came_from(self) -> None:
        payload = json.loads((FIXTURES / "baseline_addresses.json").read_text(encoding="utf-8"))
        provenance = payload["provenance"]
        self.assertEqual(provenance["memory_sha256"], BASELINE_SHA256)
        self.assertEqual(provenance["memory_bytes"], BASELINE_BYTES)
        self.assertTrue(payload["addresses"])
        self.assertTrue(all(item.startswith("ARET://") for item in payload["addresses"]))

    # --- la parité, dans ses quatre dimensions ------------------------------

    def test_both_writers_accept_exactly_the_same_inputs_and_produce_the_same_address(self) -> None:
        """Première dimension : l'écrivain. Aucune divergence n'est tolérée ici."""
        divergences = [
            (resource, identifier, left, right)
            for resource, identifier in itertools.product(RESOURCE_TYPES, IDENTIFIERS)
            for left, right in [(
                _verdict(ARET.make_address, resource, identifier),
                _verdict(pack.make_aret_address, resource, identifier),
            )]
            if left != right
        ]
        self.assertEqual(divergences, [], f"{len(divergences)} divergence(s) d’écriture")

    def test_every_address_aret_can_write_is_read_back_identically_by_vera(self) -> None:
        """Deuxième dimension, la plus grave : une régression ici rend une mémoire illisible."""
        produced = 0
        failures = []
        for resource, identifier in itertools.product(RESOURCE_TYPES, IDENTIFIERS):
            state, address = _verdict(ARET.make_address, resource, identifier)
            if state != "ACCEPTE":
                continue
            produced += 1
            reference = _parsed(ARET.parse_address, address)
            compatibility = _parsed(pack.parse_aret_address, address)
            if reference != compatibility or compatibility[2] != identifier:
                failures.append((address, reference, compatibility))
        self.assertGreater(produced, 100, "corpus d’écriture trop pauvre pour conclure")
        self.assertEqual(failures, [], f"{len(failures)} adresse(s) V1 non relue(s) à l’identique")

    def test_the_real_baseline_addresses_are_read_identically(self) -> None:
        """Troisième dimension : les adresses que la mémoire ARET porte vraiment."""
        addresses = json.loads((FIXTURES / "baseline_addresses.json").read_text(encoding="utf-8"))["addresses"]
        divergences = [
            (address, reference, compatibility)
            for address in addresses
            for reference, compatibility in [(
                _parsed(ARET.parse_address, address),
                _parsed(pack.parse_aret_address, address),
            )]
            if reference != compatibility
        ]
        self.assertEqual(len(addresses), 22)
        self.assertEqual(divergences, [], f"{len(divergences)} adresse(s) réelle(s) divergente(s)")

    def test_vera_is_never_wider_than_aret(self) -> None:
        """Quatrième dimension : un lecteur de compatibilité n'invente pas de surface.

        Accepter ce qu'ARET refusait ne casserait aucune lecture — c'est précisément pourquoi cela
        passerait inaperçu, et pourquoi c'est épinglé séparément.
        """
        corpus = set(RAW_ADDRESSES) | {
            f"ARET://{resource}/{identifier}"
            for resource, identifier in itertools.product(RESOURCE_TYPES, IDENTIFIERS)
        }
        wider = []
        stricter = []
        for address in sorted(corpus):
            reference = _parsed(ARET.parse_address, address)
            compatibility = _parsed(pack.parse_aret_address, address)
            if reference == compatibility:
                continue
            if reference[0] == "REFUSE" or compatibility[0] == "ACCEPTE":
                wider.append((address, reference, compatibility))
            else:
                stricter.append(address)
        self.assertEqual(wider, [], f"{len(wider)} entrée(s) élargissant la surface V1")
        self.assertTrue(stricter, "aucun resserrement observé : le corpus ne teste pas la direction")

    def test_every_tightening_is_outside_what_aret_could_ever_write(self) -> None:
        """Un resserrement n'est défendable que sur une forme que l'écrivain V1 ne produit pas.

        Sinon VERA refuserait une adresse qu'ARET a pu écrire en mémoire, et le resserrement serait
        une régression de lecture déguisée en rigueur.
        """
        writable = {
            address
            for resource, identifier in itertools.product(RESOURCE_TYPES, IDENTIFIERS)
            for state, address in [_verdict(ARET.make_address, resource, identifier)]
            if state == "ACCEPTE"
        }
        corpus = set(RAW_ADDRESSES) | {
            f"ARET://{resource}/{identifier}"
            for resource, identifier in itertools.product(RESOURCE_TYPES, IDENTIFIERS)
        }
        for address in sorted(corpus):
            reference = _parsed(ARET.parse_address, address)
            compatibility = _parsed(pack.parse_aret_address, address)
            if reference != compatibility:
                self.assertNotIn(address, writable, f"`{address}` est écrivable par ARET et refusée par VERA")

    # --- ce que la promotion de C01 exige en plus ---------------------------

    def test_the_compatibility_reader_resolves_nothing_and_crosses_no_project(self) -> None:
        """I002 et I011 : lire une adresse n'est ni une recherche, ni un franchissement de projet.

        Un lecteur de compatibilité qui consulterait un store ferait de l'adressage une résolution
        (I002), et un qui produirait une adresse `vera://` ferait entrer une ressource ARET dans
        l'identité d'un projet VERA sans import explicite (I011). Les deux se constatent sur le
        module : il n'importe rien de persistant et ne construit aucune adresse VERA.
        """
        source = Path(pack.__file__).read_text(encoding="utf-8")
        for forbidden in ("sqlite3", "MemoryStore", "from .store", "vera://", "open("):
            self.assertNotIn(forbidden, source, f"le lecteur de compatibilité mentionne `{forbidden}`")
        for address in ("ARET://knowledge/KN-001", "ARET://front/current"):
            self.assertIsInstance(pack.parse_aret_address(address), pack.AretAddress)

    def test_every_refusal_is_raised_and_never_returned(self) -> None:
        """I014 : une adresse douteuse échoue bruyamment plutôt que de dégrader silencieusement."""
        quiet = []
        for address in sorted(set(RAW_ADDRESSES) | {"ARET://knowledge/alpha beta", "ARET://knowledge/%41"}):
            try:
                result = pack.parse_aret_address(address)
            except pack.AretAddressCompatibilityError:
                continue
            except ValueError:  # pragma: no cover - une autre ValueError serait déjà une anomalie
                quiet.append((address, "ValueError non typée"))
                continue
            if result is None or not isinstance(result, pack.AretAddress):
                quiet.append((address, result))
        self.assertEqual(quiet, [], f"{len(quiet)} refus silencieux ou verdict dégradé")
        self.assertTrue(issubclass(pack.AretAddressCompatibilityError, ValueError))

    def test_the_core_carries_no_aret_dependency_and_no_reference_fixture(self) -> None:
        """Le registre exige que le Core démontre son absence de dépendance ARET."""
        core = Path(__file__).resolve().parents[1] / "src" / "vera_mmu"
        offenders = sorted(
            str(path.relative_to(core))
            for path in core.rglob("*.py")
            if "domain_packs" not in path.parts and (
                "domain_packs.aret" in path.read_text(encoding="utf-8")
                or "aret_v1" in path.read_text(encoding="utf-8")
            )
        )
        self.assertEqual(offenders, [], f"Le Core référence ARET : {offenders}")
        self.assertEqual(pack.AretAddress.__module__, "vera_mmu.domain_packs.aret.addressing")


if __name__ == "__main__":
    unittest.main()
