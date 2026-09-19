"""L'adaptateur d'oracles d'ARET, chargé pour être **exécuté**.

`C07` porte sur ce qui décide d'un verdict : quel script est choisi, ce qui est refusé avant tout
lancement, et comment une sortie de processus devient `PASS`, `FAIL`, `ERROR`, `SKIPPED` ou
`UNKNOWN`. `C08` porte sur les préconditions — binaire, scripts, outils — et sur ce qui arrive
quand elles manquent.

**Une bonne part des deux se mesure sans aucune chaîne d'outils, et c'est le périmètre de ce
chargeur.** `normalise_result` est une fonction **pure** de `(spec, exit_code, stdout, stderr,
missing, timed_out)` ; `_repository_file` est de la résolution de chemin ; `safe_fixture` est une
expression régulière ; `ORACLES` est un dictionnaire fermé. Rien de tout cela ne lance de
processus, et tout cela porte les dimensions que le registre exige — confinement, absence de
commande arbitraire, distinction `SKIPPED`/`PASS`.

Ce qui reste hors de portée ici est nommé plutôt que masqué : `run_oracle` lance un vrai script,
donc l'evidence hashée et la gate réelle demandent Wine, MinGW et un binaire `target/release/aret`
construit. Aucun test de ce fichier ne prétend les couvrir.

**Pour `C08`, l'absence de chaîne d'outils est le fixture, pas l'obstacle.** Sa preuve exigée
demande « Core installable sans toolchain » et « tests `SKIPPED` explicites » : ces deux-là se
mesurent précisément parce que `wine` et MinGW manquent de cette machine.

`oracles.py` importe `core.repository` — satisfait par la référence de dépôt déjà chargeable pour
`C14` — et `evidence.capture`, versionné à côté de lui sous son propre nom et sa propre empreinte.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import types
from types import ModuleType

from tests.aret_v1_repository_reference import aret_repository

SOURCE = Path(__file__).resolve().parent / "fixtures" / "aret_v1" / "source"
REFERENCE = SOURCE / "oracles_reference.py"
CAPTURE = SOURCE / "capture_reference.py"

#: SHA-256 de `aret-memory/evidence/adapters/oracles.py` au commit épinglé par le README.
REFERENCE_SHA256 = "7e836e9eaaeeee4a977ba00ef15c975169dab13dbbf28c7504451df4caa033d2"
#: SHA-256 de `aret-memory/evidence/capture.py`, sa seule dépendance hors `core.repository`.
CAPTURE_SHA256 = "a2e0d1bfca2ad0e1bdb46df89245f655877ec893b1673d6ebcd7e614ef23f818"

_module: ModuleType | None = None


def reference_digest() -> str:
    return sha256(REFERENCE.read_bytes()).hexdigest()


def capture_digest() -> str:
    return sha256(CAPTURE.read_bytes()).hexdigest()


def _load(name: str, path: Path) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise AssertionError(f"La référence ARET {path.name} n’est pas chargeable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def aret_oracles() -> ModuleType:
    """Charger l'adaptateur d'oracles, une seule fois, sur le vrai dépôt ARET."""
    global _module
    if _module is None:
        sys.modules["core.repository"] = aret_repository()
        if "evidence" not in sys.modules:
            package = types.ModuleType("evidence")
            package.__path__ = []  # type: ignore[attr-defined]
            sys.modules["evidence"] = package
        sys.modules["evidence.capture"] = _load("aret_v1_capture", CAPTURE)
        _module = _load("aret_v1_oracles", REFERENCE)
    return _module
