"""Test de parité du couplage `C02` — résolution du store ARET V1 contre le workspace VERA.

Le registre exige, pour promouvoir `C02` : « initialisation VERA, override borné, no-Git,
multi-repo, traversal, WAL checkpoint et doctor ».

**Deux resserrements délibérés portent ce couplage, et il faut les prouver plutôt que les
affirmer.** ARET résout son runtime en lisant `os.environ["ARET_MEMORY_DIR"]` et **crée** les
répertoires manquants ; VERA exige un mapping fourni explicitement et refuse un runtime absent. Un
resolver qui consulte l'environnement global décide d'un chemin que l'appelant n'a pas vu passer, et
un resolver qui crée transforme une faute de frappe en nouveau projet vide.

**Le troisième est une correction, pas un choix de style.** Le checkpoint WAL d'ARET ne contrôle que
`busy`. Or déclarer `journal_mode=WAL` n'ouvre pas le WAL : tant que la connexion n'a pas lu la base,
le pager n'en tient aucun, et `wal_checkpoint` répond `(0, -1, -1)` — un succès sur rien,
indiscernable d'un vrai repli pour qui ne regarde que `busy`. VERA lit d'abord, puis exige
`busy == 0` **et** `log == 0`. Ce n'est pas une précaution théorique : le mode de défaillance a été
mesuré sur un runner Linux de la CI, au run #47.

Les faits ARET ne sont pas transcrits ici : ils sont **extraits du code réel** par analyse
syntaxique de `core/repository.py`, versionné sous `fixtures/aret_v1/source/` avec son SHA-256
épinglé. Une déclaration de layout comparée à une transcription ne prouverait rien de plus qu'un
copier-coller fidèle.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from vera_mmu.doctor import diagnose_project
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore, checkpoint_wal
from vera_mmu.domain_packs.aret.runtime import legacy_runtime_layout
from vera_mmu.domain_packs.aret.runtime_resolution import (
    AretRuntimeResolutionError,
    resolve_aret_v1_runtime,
)

from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization

from tests.aret_v1_baseline import build_source


def _named_project(root: Path, project_id: str) -> Path:
    """Un projet VERA complet sous un identifiant choisi, pour éprouver le multi-repo."""
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root, template="software", project_id=project_id, project_name=project_id
    )
    apply_project_initialization(root, preview, confirm=True)
    return root / ".vera-mmu" / "project.yaml"


SOURCE_DIR = Path(__file__).resolve().parent / "fixtures" / "aret_v1" / "source"
REPOSITORY_REFERENCE = SOURCE_DIR / "repository_reference.py"
GIT_MEMORY_REFERENCE = SOURCE_DIR / "git_memory_reference.py"

#: SHA-256 des deux sources ARET que `C02` cite, au commit épinglé par le README des fixtures.
REPOSITORY_SHA256 = "18031bbe94ccadc41eefaf7c7bd36630bb2dad20f2ffaccdbef533eb73e48bcc"
GIT_MEMORY_SHA256 = "7dce3aa46678f7a2fb1db354ff7d4ed0433a916b1a935295b464dcd8cda8f810"


def _memory_store_init() -> ast.FunctionDef:
    """Extraire `MemoryStore.__init__` du code ARET réel, sans le transcrire."""
    tree = ast.parse(REPOSITORY_REFERENCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "MemoryStore":
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == "__init__":
                    return member
    raise AssertionError("`MemoryStore.__init__` introuvable dans la référence ARET")


def _strings(node: ast.AST) -> set[str]:
    return {item.value for item in ast.walk(node) if isinstance(item, ast.Constant) and isinstance(item.value, str)}


class AretC02RuntimeParityTests(unittest.TestCase):
    # --- la référence elle-même --------------------------------------------

    def test_the_vendored_sources_are_the_pinned_aret_files(self) -> None:
        self.assertEqual(sha256(REPOSITORY_REFERENCE.read_bytes()).hexdigest(), REPOSITORY_SHA256)
        self.assertEqual(sha256(GIT_MEMORY_REFERENCE.read_bytes()).hexdigest(), GIT_MEMORY_SHA256)

    def test_the_declared_layout_is_the_one_arets_own_constructor_uses(self) -> None:
        """`legacy_runtime_layout()` n'avait jamais été confronté au code qu'il prétend décrire."""
        constants = _strings(_memory_store_init())
        layout = legacy_runtime_layout()
        for value in (
            layout.environment_override,
            layout.default_runtime_dir,
            layout.sqlite_filename,
            layout.artifacts_dirname,
            layout.exports_dirname,
        ):
            self.assertIn(value, constants, f"`{value}` absent du constructeur ARET réel")

    # --- premier resserrement : l'environnement global -----------------------

    def test_aret_reads_the_global_environment_and_vera_refuses_to(self) -> None:
        """Un resolver qui consulte l'environnement décide d'un chemin que l'appelant n'a pas vu.

        Le fait ARET est extrait du code, pas supposé : son constructeur appelle `os.environ.get`.
        """
        init = _memory_store_init()
        reads_environment = any(
            isinstance(node, ast.Attribute) and node.attr == "environ"
            for node in ast.walk(init)
        )
        self.assertTrue(reads_environment, "la référence ARET ne lit plus l’environnement")
        self.assertNotIn("os.environ", Path(resolve_aret_v1_runtime.__globals__["__file__"]).read_text(encoding="utf-8"))

    def test_setting_the_environment_variable_does_not_move_veras_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "aret-memory"
            runtime = source / ".aret-memory"
            runtime.mkdir(parents=True)
            build_source(runtime / "aret_memory.sqlite").close()
            elsewhere = root / "ailleurs" / ".aret-memory"
            elsewhere.mkdir(parents=True)
            build_source(elsewhere / "aret_memory.sqlite").close()

            previous = os.environ.get(legacy_runtime_layout().environment_override)
            os.environ[legacy_runtime_layout().environment_override] = str(elsewhere)
            try:
                resolved = resolve_aret_v1_runtime(source_root=source.resolve(), environment={})
            finally:
                if previous is None:
                    os.environ.pop(legacy_runtime_layout().environment_override, None)
                else:
                    os.environ[legacy_runtime_layout().environment_override] = previous

        self.assertEqual(resolved.runtime_dir, runtime.resolve())
        self.assertEqual(resolved.resolution_basis, "DEFAULT_RUNTIME_LAYOUT")

    def test_the_override_is_honoured_only_when_supplied_explicitly(self) -> None:
        """« Override borné » : le mapping fourni décide, et lui seul."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "aret-memory"
            (source / ".aret-memory").mkdir(parents=True)
            build_source(source / ".aret-memory" / "aret_memory.sqlite").close()
            elsewhere = root / "ailleurs" / ".aret-memory"
            elsewhere.mkdir(parents=True)
            build_source(elsewhere / "aret_memory.sqlite").close()

            override = legacy_runtime_layout().environment_override
            resolved = resolve_aret_v1_runtime(
                source_root=source.resolve(), environment={override: str(elsewhere)}
            )

        self.assertEqual(resolved.runtime_dir, elsewhere.resolve())
        self.assertEqual(resolved.resolution_basis, "ARET_MEMORY_DIR_OVERRIDE")

    # --- deuxième resserrement : ne rien créer -------------------------------

    def test_aret_creates_its_runtime_and_vera_refuses_an_absent_one(self) -> None:
        """Un resolver qui crée transforme une faute de frappe en projet vide.

        Le fait ARET est extrait du code : son constructeur appelle `mkdir` sur les trois
        répertoires. VERA refuse plutôt, et ne laisse rien derrière lui.
        """
        init = _memory_store_init()
        creates = [
            node for node in ast.walk(init)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "mkdir"
        ]
        self.assertGreaterEqual(len(creates), 3, "la référence ARET ne crée plus ses répertoires")

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "aret-memory"
            source.mkdir()
            with self.assertRaises(AretRuntimeResolutionError):
                resolve_aret_v1_runtime(source_root=source.resolve(), environment={})
            self.assertEqual(sorted(item.name for item in source.iterdir()), [])

    # --- traversal et liens --------------------------------------------------

    def test_a_traversing_or_symlinked_root_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "aret-memory"
            (source / ".aret-memory").mkdir(parents=True)
            build_source(source / ".aret-memory" / "aret_memory.sqlite").close()
            linked = root / "lien"
            linked.symlink_to(source, target_is_directory=True)

            for candidate in (source / ".." / "aret-memory", linked, Path("aret-memory"), source / "absent"):
                with self.subTest(str(candidate)):
                    with self.assertRaises(AretRuntimeResolutionError):
                        resolve_aret_v1_runtime(source_root=candidate, environment={})

    # --- WAL : le resserrement qui vient d'une mesure ------------------------

    def test_arets_checkpoint_only_inspects_busy_while_vera_also_requires_log(self) -> None:
        """Le fait ARET est lu dans son code ; le comportement VERA est exécuté.

        `(0, -1, -1)` est la réponse de SQLite quand le pager ne tient aucun WAL : un succès sur
        rien. Un appelant qui ne regarde que `busy` versionne alors une base dont le journal n'a
        jamais été replié.
        """
        reference = GIT_MEMORY_REFERENCE.read_text(encoding="utf-8")
        body = reference[reference.index("def checkpoint_wal") :]
        body = body[: body.index("\ndef ", 1)] if "\ndef " in body[1:] else body
        self.assertIn("if busy:", body, "la référence ARET ne contrôle plus busy")
        self.assertNotIn("log_frames ==", body, "la référence ARET contrôle désormais aussi le journal")

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "memory.sqlite"
            connection = sqlite3.connect(database)
            try:
                connection.execute("PRAGMA journal_mode = WAL").fetchone()
                connection.execute("CREATE TABLE t(id INTEGER PRIMARY KEY)")
                connection.execute("INSERT INTO t(id) VALUES (1)")
                connection.commit()
                verdict = checkpoint_wal(connection)
            finally:
                connection.close()

        self.assertIsNotNone(verdict)
        busy, log, folded = verdict
        self.assertEqual(busy, 0)
        self.assertGreaterEqual(log, 0, "le journal n’a pas été ouvert avant le checkpoint")
        self.assertEqual(log, folded, "un repli partiel serait accepté par un contrôle sur busy seul")

    def test_veras_checkpoint_reads_before_folding(self) -> None:
        """La lecture préalable est la correction elle-même ; sans elle le verdict porte sur rien."""
        source = Path(checkpoint_wal.__globals__["__file__"]).read_text(encoding="utf-8")
        body = source[source.index("def checkpoint_wal") :]
        body = body[: body.index('"""', body.index('"""') + 3) + 3 + 400]
        self.assertLess(
            body.index("SELECT count(*) FROM sqlite_master"),
            body.index("PRAGMA wal_checkpoint"),
            "le checkpoint s’exécute avant d’avoir ouvert le WAL",
        )

    # --- no-Git, multi-repo et doctor ---------------------------------------

    def test_a_project_without_git_is_valid_and_the_doctor_says_so(self) -> None:
        """« No-Git » : l'absence de dépôt est une configuration, pas une panne."""
        with tempfile.TemporaryDirectory() as directory:
            profile_path = _named_project(Path(directory) / "sans-git", "sans-git")
            with MemoryStore.open(load_profile(profile_path), profile_path):
                pass
            report = diagnose_project(profile_path)

        rows = {check.name: check for check in report.checks}
        self.assertFalse((Path(rows["workspace"].detail.split(": ")[-1]) / ".git").exists())
        self.assertEqual(rows["vcs"].status, "INFO")
        self.assertEqual(rows["runtime"].status, "PASS")
        self.assertEqual(rows["wal"].status, "PASS")
        self.assertEqual(report.status, "PASS")

    def test_two_distinct_projects_never_share_an_identity(self) -> None:
        """« Multi-repo » : deux projets déclarés différemment restent distincts."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _named_project(root / "un", "projet-un")
            second = _named_project(root / "deux", "projet-deux")
            with MemoryStore.open(load_profile(first), first) as store:
                left, left_runtime = store.identity, store.workspace.runtime_dir
            with MemoryStore.open(load_profile(second), second) as store:
                right, right_runtime = store.identity, store.workspace.runtime_dir

        self.assertNotEqual(left.project_id, right.project_id)
        self.assertNotEqual(left.profile_hash, right.profile_hash)
        self.assertNotEqual(left.project_hash, right.project_hash)
        self.assertNotEqual(left_runtime, right_runtime)

    def test_one_project_keeps_its_identity_when_it_moves(self) -> None:
        """Le pendant, et c'est lui qui distingue VERA d'ARET.

        `_workspace_hash` hache une topologie **relative à la racine du projet** — la portabilité
        est délibérée, et c'est elle qui rend un bundle restaurable dans un autre checkout, comme
        `C03` l'exerce. ARET liait son store à un chemin absolu tiré de `ARET_MEMORY_DIR` : la même
        mémoire déplacée n'était plus tout à fait la même.

        Épingler les deux faces compte : un test qui n'exigerait que la distinction ferait de cette
        portabilité un défaut, et un qui n'exigerait que la portabilité laisserait deux projets se
        confondre.
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            here = _named_project(root / "ici", "projet-mobile")
            there = _named_project(root / "la-bas", "projet-mobile")
            with MemoryStore.open(load_profile(here), here) as store:
                left = store.identity
            with MemoryStore.open(load_profile(there), there) as store:
                right = store.identity

        self.assertEqual(left.as_dict(), right.as_dict(), "l’identité doit survivre au déplacement")


if __name__ == "__main__":
    unittest.main()
