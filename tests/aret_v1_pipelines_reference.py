"""Le catalogue de pipelines d'ARET, chargé pour être **exécuté**.

`C06` porte sur ce que chaque moteur accepte de recevoir avant de faire quoi que ce soit : un nom
de capability, des paramètres, un timeout, une policy. Ce sont des comportements, pas des
déclarations, et `C13` puis `C14` ont établi la méthode — la référence tourne.

`pipelines.py` importe `core.repository`, c'est-à-dire le dépôt déjà versionné et chargeable par
`tests/aret_v1_repository_reference.py`. Il est présenté sous ce nom avant l'import, si bien que
l'adaptateur s'exécute contre le vrai `MemoryStore` d'ARET et son vrai DDL, pas contre un double.

`PROJECT_ROOT` y est déclaré et n'est utilisé nulle part — vérifié sur la source entière — donc le
déplacement du fichier dans l'arborescence des fixtures ne change rien à son comportement.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

from tests.aret_v1_repository_reference import aret_repository

REFERENCE = Path(__file__).resolve().parent / "fixtures" / "aret_v1" / "source" / "pipelines_reference.py"
#: SHA-256 de `aret-memory/evidence/adapters/pipelines.py` au commit épinglé par le README.
REFERENCE_SHA256 = "0133cec5f39295238a8aee3c243f0b7901bc1b578716368845e78f7672683b28"

_module: ModuleType | None = None


def reference_digest() -> str:
    return sha256(REFERENCE.read_bytes()).hexdigest()


def aret_pipelines() -> ModuleType:
    """Charger l'adaptateur de pipelines, une seule fois, sur le dépôt ARET réel."""
    global _module
    if _module is None:
        sys.modules["core.repository"] = aret_repository()
        specification = importlib.util.spec_from_file_location("aret_v1_pipelines", REFERENCE)
        if specification is None or specification.loader is None:
            raise AssertionError("La référence de pipelines ARET n’est pas chargeable")
        module = importlib.util.module_from_spec(specification)
        sys.modules["aret_v1_pipelines"] = module
        specification.loader.exec_module(module)
        _module = module
    return _module


def repository_stub(root: Path) -> Path:
    """Un dépôt ARET minimal : de quoi résoudre les chemins d'un plan, rien à exécuter.

    `C06` mesure ce qui se décide **avant** l'exécution — le nom, les paramètres, le timeout, la
    policy. Un dry-run résout ses chemins sans lancer de processus, et c'est précisément le
    périmètre du couplage ; `C07` et `C08`, qui demandent Wine et MinGW, portent l'exécution réelle.
    """
    (root / "target" / "release").mkdir(parents=True, exist_ok=True)
    (root / "bench").mkdir(exist_ok=True)
    (root / "tools").mkdir(exist_ok=True)
    return root
