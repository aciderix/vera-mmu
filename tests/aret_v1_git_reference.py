"""La source Git d'ARET, chargée pour être **exécutée** et non seulement lue.

`C02` avait ouvert ce fichier dans un arbre syntaxique pour épingler ce que son checkpoint WAL
contrôle. `C13` va un cran plus loin : il fait tourner les vraies fonctions d'ARET sur de vrais
dépôts Git, à côté de celles de VERA sur les leurs, et compare les deux verdicts sur la même
situation. Lire un code dit ce qu'il prétend faire ; l'exécuter dit ce qu'il fait — et c'est cette
différence qui a fait tomber le défaut consigné dans `test_aret_c13_git_sync_parity.py`.

Le module est chargé depuis la copie versionnée, jamais depuis un dépôt voisin : la référence doit
être celle dont le hash est épinglé, sinon la mesure porterait sur autre chose que ce qu'on croit.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sqlite3
import subprocess
from types import ModuleType

REFERENCE = Path(__file__).resolve().parent / "fixtures" / "aret_v1" / "source" / "git_memory_reference.py"
#: SHA-256 de `aret-memory/ops/git_memory.py` dans `aciderix/ARET-MMU` au commit épinglé par le README.
REFERENCE_SHA256 = "7dce3aa46678f7a2fb1db354ff7d4ed0433a916b1a935295b464dcd8cda8f810"

#: L'emplacement mémoire qu'ARET impose par défaut, tel que son propre code l'écrit.
ARET_MEMORY_DIR = "aret-memory/.aret-memory"
ARET_DATABASE = "aret_memory.sqlite"

_module: ModuleType | None = None


def reference_digest() -> str:
    return sha256(REFERENCE.read_bytes()).hexdigest()


def aret_git() -> ModuleType:
    """Charger la référence ARET comme module exécutable, une seule fois par session de test."""
    global _module
    if _module is None:
        specification = importlib.util.spec_from_file_location("aret_v1_git_memory", REFERENCE)
        if specification is None or specification.loader is None:
            raise AssertionError("La référence Git ARET n’est pas chargeable")
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        _module = module
    return _module


def git(root: Path, *arguments: str) -> str:
    """Appeler Git sans passer par `invoke()` d'ARET, dont on mesure justement le comportement."""
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments], check=False, text=True, capture_output=True
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout


def build_repository(root: Path, *, policy: str | None = None) -> Path:
    """Monter un dépôt à la forme qu'ARET attend, et rendre son répertoire mémoire.

    La base est une vraie base SQLite en WAL : le checkpoint d'ARET doit avoir quelque chose à
    consolider, faute de quoi il rendrait `database_absent` et la mesure ne porterait sur rien.
    """
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "VERA parity tests")
    git(root, "config", "user.email", "vera-tests@example.invalid")
    memory = root / ARET_MEMORY_DIR
    memory.mkdir(parents=True)
    connection = sqlite3.connect(memory / ARET_DATABASE)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE probe (value TEXT)")
        connection.commit()
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        connection.close()
    if policy is not None:
        (memory / "sync_policy.json").write_text(policy, encoding="utf-8")
    git(root, "add", "--all")
    git(root, "commit", "-m", "ARET memory baseline")
    return memory


def touch_memory(memory: Path) -> None:
    """Modifier la base mémoire en place, sans rien stager — le cas ordinaire d'une mutation."""
    database = memory / ARET_DATABASE
    database.write_bytes(database.read_bytes() + b"\0" * 8)
