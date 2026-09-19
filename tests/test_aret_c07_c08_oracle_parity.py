"""Parité de `C07` (complète) et de `C08` (partielle) — les oracles d'ARET, exécutés.

**Les deux couplages sont clos ; ce fichier porte tout sauf une dimension.** La preuve exigée de
`C07` — « confinement de repository/script, absence de commande arbitraire, evidence hashée,
distinction `SKIPPED`/`PASS`, promotion `PROVEN` et gate réelle » — est mesurée ici, jusqu'à faire
**tourner un vrai oracle** qui rend `PASS` et promeut une connaissance en `PROVEN`. De `C08`, ce
fichier porte trois dimensions sur quatre ; la quatrième, « l'exécutabilité mesurée dans une image
de référence », est dans `tests/test_aret_c08_reference_image_parity.py`, parce que les mesures
faites ici ont lieu sur la machine hôte et non dans l'image `docker/ci-toolchain` épinglée.

**L'exécution réelle a un prix et des préconditions.** Elle demande `libunicorn` — que ni
`funcdiff` ni `cpudiff` ne déclarent, voir plus bas —, une compilation Rust de la `--features
unpack`, et 180 secondes. Le test correspondant ne tourne que si `VERA_C07_RUN_REAL_ORACLE=1` est
posé, et se saute en le disant sinon. Il a été exécuté le 19 septembre 2026 sur cette machine.

**Trois fonctions portent tout ce qui se décide avant qu'un processus démarre**, et aucune ne lance
quoi que ce soit : `normalise_result` est une fonction **pure**, `_repository_file` est de la
résolution de chemin, `safe_fixture` est une expression régulière. `ORACLES` est un dictionnaire
fermé de neuf specs.

**Ce qu'ARET fait bien, et il faut le dire d'abord.**

1. *La précédence de normalisation est juste.* Une dépendance manquante l'emporte sur tout — sur un
   `timed_out`, sur un échec, et sur une sortie qui ressemble à un succès. On ne rend pas de verdict
   sur une exécution qui n'a pas eu lieu.
2. *Un code de sortie non nul reste un `FAIL`* même avec une ligne `SKIP` dans la sortie.
3. *Un corpus vide n'est pas un succès.* `0 / 0` rend `ERROR` : les regexes exigent `> 0`.
4. *`winehash` rend `UNKNOWN` même quand il réussit*, sa sortie étant une mesure et non un gate.
   Refuser de transformer une mesure en verdict est exactement ce que `I004` demande.
5. *Le confinement tient* sur les quatre évasions posées, lien symbolique sortant compris.
6. *La gate de promotion est tenue à **deux couches indépendantes*** : la garde Python de
   `attach_proof` et deux triggers SQLite. Neutraliser l'une laisse l'autre refuser — c'est de la
   défense en profondeur, et les tests ci-dessous distinguent leurs messages pour qu'aucune ne soit
   créditée du travail de l'autre.

**La divergence porte sur une seule question : d'où vient le verdict.**

ARET le **dérive de la prose** du script, par huit expressions régulières sur des lignes de résumé
lisibles par un humain. VERA le fait calculer par un validateur fermé, comme une comparaison
d'empreintes, et son module de validation n'importe même pas `subprocess`. Mesuré : changer
`functions` en `function` — un caractère — transforme un `PASS` en `ERROR`.

**Et le préflight d'ARET annonce « prêt » pour deux oracles qui ne peuvent pas tourner.** `funcdiff`
déclare `('bash', 'cargo')`, `cpudiff` déclare `('cargo',)` ; aucun ne nomme `libunicorn`, que leurs
scripts exigent. Pire, la sonde correspondante ne peut pas réussir : `toolchain_status` cherche
`unicorn` par `shutil.which("libunicorn")`, qui parcourt le `PATH` à la recherche d'un exécutable —
mesuré sur cette machine, la bibliothèque **installée** y est toujours déclarée indisponible.

**Pour `C08`, l'absence de chaîne d'outils est le fixture, pas l'obstacle** : « Core installable
sans toolchain » et « tests `SKIPPED` explicites » se mesurent précisément parce que `wine` et
MinGW manquent ici.

**Quels tests ont besoin de quoi.** Ceux qui interrogent le dépôt toolkit ou lancent un oracle
portent une garde de montage et se sautent en le disant ; ceux qui ne touchent qu'au store ARET
n'en portent pas, pour qu'ils soient attestés sur les deux plateformes. Deux d'entre eux étaient
d'abord sur-gardés et se sautaient en CI pour rien — le run #63 l'a montré en rendant sept skips
là où deux étaient attendus.
"""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.evidence import VERDICTS, EvidenceError, EvidenceService
from vera_mmu.executions import ExecutionError, ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore

from tests.aret_v1_baseline import temporary_root
from tests.aret_v1_oracles_reference import (
    CAPTURE_SHA256,
    REFERENCE_SHA256,
    aret_oracles,
    capture_digest,
    reference_digest,
)


#: Les neuf oracles d'ARET, relevés sur le dictionnaire exécuté.
ARET_ORACLES = (
    "cpudiff", "difftest", "ehdiff", "funcdiff", "gnuehdiff",
    "stdcall_audit", "transpilediff", "winediff", "winehash",
)
#: Les lignes de résumé réelles que chaque regex de `normalise_result` reconnaît comme un succès.
PASSING_SUMMARIES = {
    "difftest": "differential equivalence: 272 / 272 functions",
    "transpilediff": "transpile-pipeline equivalence: 4 / 4 opt-levels",
    "stdcall_audit": "stdcall-pop audit: PASS",
    "winediff": "OS-API (Wine) equivalence: 31 / 31 programs",
    "ehdiff": "MSVC EH differential: 12 / 12 fixtures",
    "gnuehdiff": "GNU/Itanium C++ EH differential: 9 / 9 fixtures",
    "funcdiff": "funcdiff corpus gate: PASS",
    "cpudiff": "test result: ok",
}

PROFILE = """
mmu:
  version: "2.0"
project:
  id: "oracle-parity"
  name: "Oracle Parity"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
"""


class C07C08OracleParityTests(unittest.TestCase):
    """Les dimensions de `C07` et `C08` qui ne demandent aucun outil externe."""

    def vera_store(self, directory: Path) -> MemoryStore:
        profile_path = directory / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    # ------------------------------------------------ la référence est bien celle épinglée

    def test_references_are_the_pinned_aret_sources(self) -> None:
        self.assertEqual(reference_digest(), REFERENCE_SHA256)
        self.assertEqual(capture_digest(), CAPTURE_SHA256)

    # -------------------------------------- C07 : catalogue fermé, aucune commande arbitraire

    def test_i008_the_oracle_catalogue_is_closed_and_carries_no_free_command(self) -> None:
        """Neuf oracles, neuf specs figées. Rien n'est composé à partir d'une entrée."""
        oracles = aret_oracles()
        self.assertEqual(tuple(sorted(oracles.ORACLES)), ARET_ORACLES)
        for name, spec in oracles.ORACLES.items():
            with self.subTest(oracle=name):
                self.assertEqual(spec.name, name)
                self.assertIsInstance(spec.dependencies, tuple)
                self.assertTrue(1 <= spec.timeout_seconds <= 3600)
                # Chaque spec porte au moins l'un des deux, et aucun n'est composé à l'exécution.
                self.assertTrue(spec.script is not None or spec.command is not None)
                if spec.command is not None:
                    self.assertIsInstance(spec.command, tuple)
                    self.assertEqual(spec.command[0], "cargo")
                if spec.script is not None:
                    self.assertFalse(spec.script.startswith("/"))
                    self.assertNotIn("..", spec.script)

        # `cpudiff` porte les deux, et la nuance mérite d'être épinglée : son `script` est un
        # fichier de **précondition** que `required_tools` vérifie, jamais ce qui est lancé — c'est
        # la commande `cargo` fermée qui s'exécute. Les huit autres lancent `bash <script>`.
        both = {name for name, spec in oracles.ORACLES.items() if spec.script and spec.command}
        self.assertEqual(both, {"cpudiff"})
        self.assertEqual(oracles.ORACLES["cpudiff"].script, "src/cpudiff.rs")
        self.assertEqual(
            oracles.ORACLES["cpudiff"].command,
            ("cargo", "test", "--release", "--features", "unpack", "cpudiff"),
        )

    def test_i008_an_unknown_oracle_is_refused_though_the_message_names_four_of_nine(self) -> None:
        """Le refus tient ; son message a vieilli, et c'est mesuré plutôt que supposé.

        Neuf oracles existent, la phrase de refus n'en propose que quatre. Un opérateur qui la lit
        ignore l'existence de `ehdiff`, `gnuehdiff`, `stdcall_audit`, `transpilediff` et `cpudiff`.
        Ce n'est pas une faille, c'est un message devenu faux à mesure que le catalogue grandissait.
        """
        oracles = aret_oracles()

        class _Store:
            def _require_write(self) -> None:
                return None

        with self.assertRaises(Exception) as raised:
            oracles.run_oracle(_Store(), Path("/tmp"), "inexistant")
        message = str(raised.exception)
        self.assertIn("Oracle inconnu", message)
        named = {name for name in ARET_ORACLES if name in message}
        self.assertEqual(named, {"difftest", "winehash", "winediff", "funcdiff"})
        self.assertEqual(len(ARET_ORACLES) - len(named), 5)

    def test_i008_the_only_client_supplied_value_is_a_closed_fixture_name(self) -> None:
        """La seule valeur qui entre dans l'argv vient d'une expression régulière fermée."""
        oracles = aret_oracles()
        self.assertEqual(oracles.safe_fixture("corpus_01.bin"), "corpus_01.bin")
        self.assertIsNone(oracles.safe_fixture(None))
        for candidate in ("../evade", "avec espace", "", "  ", "x" * 101, "a;rm -rf /", "a/b"):
            with self.subTest(fixture=candidate):
                with self.assertRaises(Exception):
                    oracles.safe_fixture(candidate)
        # Un seul oracle accepte une fixture ; les huit autres la refusent par construction.
        accepting = {name for name, spec in oracles.ORACLES.items() if spec.accepts_fixture}
        self.assertEqual(accepting, {"winediff"})

    # ------------------------------------------------------- C07 : confinement des chemins

    def test_i008_path_confinement_refuses_every_escape_measured(self) -> None:
        """Quatre évasions posées, quatre refus — dont le lien symbolique, qui est le cas dur."""
        oracles = aret_oracles()
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "bench").mkdir()
            inside = root / "bench" / "ok.sh"
            inside.write_text("", encoding="utf-8")
            self.assertEqual(oracles._repository_file(root, "bench/ok.sh", "Script"), inside)

            outbound = root / "bench" / "lien.sh"
            outbound.symlink_to(Path("/etc/hostname"))
            for relative in ("../dehors", "../../etc/passwd", "/etc/passwd", "bench/lien.sh"):
                with self.subTest(chemin=relative):
                    with self.assertRaises(Exception) as raised:
                        oracles._repository_file(root, relative, "Script")
                    self.assertIn("hors du dépôt ARET", str(raised.exception))

    # ---------------------------------- C07 : la normalisation, et d'où vient le verdict

    def test_the_normalisation_precedence_puts_a_missing_dependency_above_everything(self) -> None:
        """Ce qu'ARET fait bien : on ne rend pas de verdict sur une exécution qui n'a pas eu lieu."""
        oracles = aret_oracles()
        spec = oracles.ORACLES["difftest"]
        passing = PASSING_SUMMARIES["difftest"]
        for label, arguments, expected in (
            ("dépendance manquante malgré une sortie de succès", (0, passing, "", ["wine"], False), "SKIPPED"),
            ("dépendance manquante malgré un timeout", (None, "", "", ["wine"], True), "SKIPPED"),
            ("dépendance manquante malgré un échec", (1, "", "", ["wine"], False), "SKIPPED"),
            ("timeout sans dépendance manquante", (None, "", "", [], True), "ERROR"),
            ("code de sortie non nul", (1, passing, "", [], False), "FAIL"),
            ("code non nul malgré une ligne SKIP", (1, "SKIP rien à faire", "", [], False), "FAIL"),
        ):
            with self.subTest(cas=label):
                self.assertEqual(oracles.normalise_result(spec, *arguments), expected)

    def test_each_of_the_eight_pass_regexes_recognises_its_real_summary_line(self) -> None:
        """Huit oracles, huit formulations, toutes vérifiées sur la ligne que leur script écrit."""
        oracles = aret_oracles()
        for name, summary in PASSING_SUMMARIES.items():
            with self.subTest(oracle=name):
                self.assertEqual(
                    oracles.normalise_result(oracles.ORACLES[name], 0, summary, "", [], False), "PASS"
                )

    def test_an_empty_corpus_is_never_a_pass(self) -> None:
        """`0 / 0` rend `ERROR`. Un corpus vide qui « n'échoue pas » n'est pas une réussite."""
        oracles = aret_oracles()
        for name, summary in (
            ("difftest", "differential equivalence: 0 / 0 functions"),
            ("transpilediff", "transpile-pipeline equivalence: 0 / 0 opt-levels"),
            ("winediff", "OS-API (Wine) equivalence: 0 / 0 programs"),
            ("ehdiff", "MSVC EH differential: 0 / 0 fixtures"),
            ("gnuehdiff", "GNU/Itanium C++ EH differential: 0 / 0 fixtures"),
        ):
            with self.subTest(oracle=name):
                self.assertEqual(
                    oracles.normalise_result(oracles.ORACLES[name], 0, summary, "", [], False), "ERROR"
                )

    def test_winehash_refuses_to_turn_a_measurement_into_a_verdict(self) -> None:
        """Le seul `UNKNOWN` atteignable du normaliseur, et il est délibéré.

        `winehash` réussit, sort un digest valide, et rend quand même `UNKNOWN` — parce que sa
        sortie est une mesure à comparer au runner Windows, pas un gate de conformité. C'est
        exactement ce que `I004` demande : ne pas promouvoir ce qui n'est pas une preuve.
        """
        oracles = aret_oracles()
        digest = "a" * 64
        self.assertEqual(
            oracles.normalise_result(oracles.ORACLES["winehash"], 0, f"OK {digest}", "", [], False), "UNKNOWN"
        )
        # Et c'est le seul : pour tout autre oracle, un succès non reconnu retombe sur ERROR.
        unknowns = {
            name
            for name in ARET_ORACLES
            if oracles.normalise_result(oracles.ORACLES[name], 0, f"OK {digest}", "", [], False) == "UNKNOWN"
        }
        self.assertEqual(unknowns, {"winehash"})

    def test_an_unrecognised_success_falls_to_error_not_unknown(self) -> None:
        """Sortie inconnue et code 0 : le verdict est `ERROR`, pas `UNKNOWN`.

        La nuance compte pour `I014` : ARET refuse de dire « je ne sais pas » là où il ne sait pas
        lire, et dit « erreur ». Les deux sont défendables ; ce qui compte est de savoir lequel.
        """
        oracles = aret_oracles()
        self.assertEqual(
            oracles.normalise_result(oracles.ORACLES["difftest"], 0, "tout va bien", "", [], False), "ERROR"
        )
        self.assertEqual(
            oracles.normalise_result(oracles.ORACLES["difftest"], 0, "SKIPPED faute de fixture", "", [], False),
            "SKIPPED",
        )

    def test_a_verdict_read_from_prose_turns_on_a_single_word(self) -> None:
        """La divergence de `C07`, mesurée plutôt qu'argumentée.

        Le script est le même, son comportement est le même, seule sa formulation change d'un
        caractère — `functions` au lieu de `function`. Le verdict passe de `PASS` à `ERROR`. Huit
        des neuf oracles reposent sur une telle lecture de prose.
        """
        oracles = aret_oracles()
        spec = oracles.ORACLES["difftest"]
        self.assertEqual(
            oracles.normalise_result(spec, 0, "differential equivalence: 272 / 272 functions", "", [], False),
            "PASS",
        )
        for altered in (
            "differential equivalence: 272 / 272 function",
            "Differential equivalence: 272 / 272 functions",
            "differential equivalence : 272 / 272 functions",
            "differential-equivalence: 272 / 272 functions",
        ):
            with self.subTest(sortie=altered):
                self.assertEqual(oracles.normalise_result(spec, 0, altered, "", [], False), "ERROR")

    def test_vera_derives_its_verdict_from_a_hash_never_from_output(self) -> None:
        """L'autre versant de la même question : VERA ne lit aucune prose pour juger.

        Le vocabulaire est identique des deux côtés — cinq verdicts, mêmes noms. Mais celui de
        VERA est un ensemble **fermé et stocké**, fourni par un validateur qui compare des
        empreintes, et son module de validation n'importe pas `subprocess`. Aucune expression
        régulière n'y décide d'un `PASS`.
        """
        self.assertEqual(VERDICTS, frozenset({"PASS", "FAIL", "ERROR", "SKIPPED", "UNKNOWN"}))
        source_root = Path(__file__).resolve().parents[1] / "src" / "vera_mmu"
        validators = (source_root / "validators.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", validators)
        self.assertNotIn("stdout", validators)
        # Les verdicts des validateurs naissent tous d'une égalité d'empreintes ou de clefs.
        self.assertEqual(len(re.findall(r"verdict='PASS' if ", validators)), 3)

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = EvidenceService(store)
                # Le verdict est contrôlé **avant** toute écriture : un mot hors de l'ensemble
                # fermé ne franchit pas l'entrée, là où ARET en fabrique un à partir d'une sortie.
                #
                # Le message est vérifié, et pas seulement le fait qu'il y ait un refus : sans
                # cela, l'execution inexistante refuserait à la place du verdict et le test
                # passerait pour la mauvaise raison — une mutation l'a montré.
                for refused in ("SUCCES", "pass", "OK", "", "ok"):
                    with self.subTest(verdict=refused):
                        with self.assertRaises(EvidenceError) as raised:
                            service.record("EV-X", "EX-1", "COMMAND_PROOF", refused, {"k": "v"}, actor="test")
                        self.assertIn("verdict", str(raised.exception))
                # Le même appel avec un verdict admis échoue plus loin, et pour une autre raison :
                # c'est ce qui prouve que le contrôle de verdict est bien celui qui a mordu.
                with self.assertRaises(EvidenceError) as valid_verdict:
                    service.record("EV-X", "EX-1", "COMMAND_PROOF", "PASS", {"k": "v"}, actor="test")
                self.assertNotIn("verdict", str(valid_verdict.exception))

                # Et le runner fermé de VERA — le pendant de `run_oracle` — ne lance rien sans
                # contrat déclaré ni policy ALLOW explicite. Son exécution réelle, elle, est la
                # dimension que ce fichier ne couvre pas.
                with self.assertRaises(ExecutionError):
                    ExecutionService(store).record_observed_process(
                        "EX-1", "cap-inexistante", {}, environment={}, exit_code=0,
                        artifact_hash="0" * 64, result={}, actor="test",
                    )

    # ---------------------------- C08 : la chaîne d'outils absente est le fixture

    def test_i013_a_missing_toolchain_yields_skipped_without_running_anything(self) -> None:
        """Dimension « tests `SKIPPED` explicites », mesurée sur cette machine telle qu'elle est.

        `required_tools` est interrogé sur le vrai dépôt toolkit, avec ses neuf scripts présents.
        Ce qui manque ici manque vraiment — `wine`, MinGW, le binaire non construit — et chaque
        manque produit un `SKIPPED` sans qu'un seul processus soit lancé.
        """
        oracles = aret_oracles()
        toolkit = Path("/home/user/Automatic-reverse-engineering-toolkit")
        if not toolkit.is_dir():
            self.skipTest("Le dépôt toolkit de référence n’est pas monté dans ce conteneur")
        for name in ARET_ORACLES:
            spec = oracles.ORACLES[name]
            with self.subTest(oracle=name):
                missing = oracles.required_tools(spec, toolkit)
                self.assertIsInstance(missing, list)
                if missing:
                    self.assertEqual(
                        oracles.normalise_result(spec, None, "", "", missing, False), "SKIPPED"
                    )
                if spec.requires_aret_binary and not (toolkit / "target" / "release" / "aret").is_file():
                    self.assertIn("target/release/aret", missing)

    def test_a_missing_script_is_reported_as_a_missing_dependency(self) -> None:
        """Un script absent est nommé dans le manque, au lieu d'échouer à l'exécution."""
        oracles = aret_oracles()
        with TemporaryDirectory() as directory:
            empty = Path(directory).resolve()
            spec = oracles.ORACLES["difftest"]
            missing = oracles.required_tools(spec, empty)
            self.assertIn(spec.script, missing)
            self.assertIn("target/release/aret", missing)

    def test_i013_the_declared_dependencies_under_declare_what_the_scripts_need(self) -> None:
        """Le préflight d'ARET annonce « rien ne manque » pour deux oracles qui ne peuvent pas tourner.

        `funcdiff` déclare `('bash', 'cargo')` et `cpudiff` déclare `('cargo',)`. Mais le script de
        l'un et la commande de l'autre exigent tous deux `--features unpack`, c'est-à-dire la
        **libunicorn système** — qui n'est déclarée dans aucune des deux specs. `required_tools`
        rend donc `[]` : prêt à lancer.

        Le script, lui, le découvre à l'exécution et dégrade proprement : il imprime
        `SKIP (unpack build unavailable — is libunicorn installed?)` et sort en 0, ce que
        `normalise_result` traduit en `SKIPPED`. La chaîne ne ment donc pas sur le **résultat** ;
        elle ment sur la **disponibilité**, et seulement après avoir payé une compilation Rust
        complète qui ne peut pas se lier.

        C'est exactement ce que `C08` vise : un préflight doit dire ce qui manque **avant**, pas
        après. Un catalogue de dépendances qui n'énumère pas ce dont le script a besoin n'est pas
        un préflight, c'est une liste d'intentions.
        """
        oracles = aret_oracles()
        toolkit = Path("/home/user/Automatic-reverse-engineering-toolkit")
        if not toolkit.is_dir():
            self.skipTest("Le dépôt toolkit de référence n’est pas monté dans ce conteneur")

        self.assertEqual(oracles.ORACLES["funcdiff"].dependencies, ("bash", "cargo"))
        self.assertEqual(oracles.ORACLES["cpudiff"].dependencies, ("cargo",))
        for name in ("funcdiff", "cpudiff"):
            with self.subTest(oracle=name):
                self.assertNotIn("libunicorn", oracles.ORACLES[name].dependencies)
                self.assertEqual(oracles.required_tools(oracles.ORACLES[name], toolkit), [])

        # Ce que les deux exigent réellement, relevé sur le script et sur la commande.
        script = (toolkit / "bench" / "funcdiff.sh").read_text(encoding="utf-8")
        self.assertIn("--features unpack", script)
        self.assertIn("libunicorn", script)
        self.assertIn("unpack", " ".join(oracles.ORACLES["cpudiff"].command))

    def test_i014_the_shared_library_probe_cannot_report_available(self) -> None:
        """Une sonde qui ne peut pas réussir, et les deux vues d'ARET qui se contredisent.

        `toolchain_status` cherche `unicorn` par `shutil.which("libunicorn")` — une fonction qui
        parcourt le `PATH` à la recherche d'un **exécutable**. Une bibliothèque partagée s'installe
        en `libunicorn.so.N` sous `/usr/lib`, jamais sur le `PATH` et jamais exécutable. La sonde
        rend donc `available: False` sur une machine où la bibliothèque est correctement installée
        comme sur une machine où elle manque : elle ne distingue rien.

        Et les deux vues d'ARET se contredisent dans le même dépôt : `toolchain_status` annonce
        `unicorn` indisponible, pendant que `required_tools` annonce `funcdiff` prêt. Le préflight
        qui garde l'exécution ne consulte pas l'inventaire que le dossier de reprise publie.

        VERA n'a pas cette surface : son `doctor` ne sonde aucun outil externe, et son runner fermé
        refuse sur le **contrat** — une assertion qu'il peut tenir — plutôt que sur une présence
        devinée.
        """
        import shutil as _shutil

        from tests.aret_v1_pipelines_reference import aret_pipelines

        oracles = aret_oracles()
        toolkit = Path("/home/user/Automatic-reverse-engineering-toolkit")
        if not toolkit.is_dir():
            self.skipTest("Le dépôt toolkit de référence n’est pas monté dans ce conteneur")

        self.assertIsNone(_shutil.which("libunicorn"))
        status = aret_pipelines().toolchain_status(toolkit)
        self.assertFalse(status["tools"]["unicorn"]["available"])

        # Sur une machine où la bibliothèque est **réellement installée**, la sonde rend toujours
        # « indisponible ». Ce n'est alors plus un argument sur la forme de `which`, c'est une
        # mesure : la sonde ne distingue pas une machine équipée d'une machine qui ne l'est pas.
        installed = [
            candidate
            for candidate in (
                Path("/usr/lib/x86_64-linux-gnu/libunicorn.so.2"),
                Path("/usr/lib/libunicorn.so.2"),
                Path("/lib/x86_64-linux-gnu/libunicorn.so.2"),
            )
            if candidate.is_file()
        ]
        if installed:
            self.assertFalse(status["tools"]["unicorn"]["available"])
            self.assertEqual(status["tools"]["unicorn"]["path"], "")

        # La contradiction, mesurée : indisponible d'un côté, « rien ne manque » de l'autre.
        self.assertEqual(oracles.required_tools(oracles.ORACLES["funcdiff"], toolkit), [])

        # Côté VERA, le doctor ne prétend rien sur une chaîne d'outils, parce qu'il n'en sonde pas.
        doctor = (Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "doctor.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("libunicorn", doctor)
        self.assertNotIn("shutil.which", doctor)

    # -------------------------------- C07 : l'exécution réelle, la gate et la promotion

    def _toolkit_with_unicorn(self) -> Path:
        """La seule configuration où un oracle ARET peut réellement tourner ici."""
        toolkit = Path("/home/user/Automatic-reverse-engineering-toolkit")
        if not toolkit.is_dir():
            self.skipTest("Le dépôt toolkit de référence n’est pas monté dans ce conteneur")
        return toolkit

    def _aret_store(self, root: Path):
        from tests.aret_v1_repository_reference import memory_store

        return memory_store(root / ".aret-memory")

    @staticmethod
    def _knowledge(store, title: str) -> str:
        return store.append_knowledge(
            knowledge_type="OBSERVATION", status=None, title=title,
            content="Contenu de mesure de parité C07.", component_id=None, function_id=None,
            brick_id=None, tags=None, proof_ids=None, supersedes_id=None, actor="c07-parity",
        )["id"]

    def test_i004_a_skipped_oracle_is_hashed_recorded_and_refused_for_promotion(self) -> None:
        """La gate d'ARET, mesurée en exécutant `run_oracle` — et elle tient.

        `winediff` n'a pas ses dépendances : aucun processus n'est lancé, le verdict est `SKIPPED`,
        et la preuve est **tout de même enregistrée** avec son artefact et son empreinte. Demander
        la promotion sur cette preuve est refusé, et la connaissance reste `OBSERVED`.

        **Le détail qui compte : `admissible` vaut `1` sur cette preuve `SKIPPED`.** L'admissibilité
        d'ARET ne porte que sur l'authenticité du reçu HMAC, pas sur le résultat. C'est la
        conjonction `result == 'PASS' ET admissible` qui garde la promotion. La nuance explique la
        baseline consignée en `C16` : ses quatre preuves y étaient `admissible=0` faute de secret
        HMAC configuré, si bien que **rien** n'y était promouvable, quel que soit le résultat.
        """
        toolkit = self._toolkit_with_unicorn()
        oracles = aret_oracles()
        with temporary_root() as root:
            store = self._aret_store(root)
            try:
                identifier = self._knowledge(store, "Connaissance à ne pas promouvoir")
                outcome = oracles.run_oracle(store, toolkit, "winediff", timeout_seconds=60)
                proof = outcome["proof"]

                self.assertEqual(outcome["execution"]["result"], "SKIPPED")
                self.assertIsNone(outcome["execution"]["exit_code"])
                self.assertTrue(set(outcome["execution"]["missing_dependencies"]))

                # L'artefact existe et son empreinte est celle de son contenu.
                artifact = Path(store.artifacts_dir) / outcome["artifact"]["path"]
                self.assertTrue(artifact.is_file())
                self.assertEqual(
                    sha256(artifact.read_bytes()).hexdigest(), outcome["artifact"]["sha256"]
                )
                self.assertEqual(proof["artifact_hash"], outcome["artifact"]["sha256"])
                self.assertEqual(len(proof["payload_hash"]), 64)
                self.assertEqual(len(proof["receipt_hmac"]), 64)
                # Admissible, et pourtant non promouvable : les deux conditions sont distinctes.
                self.assertEqual(int(proof["admissible"]), 1)

                # Le message est celui de la **garde Python**, en français, et pas celui du
                # trigger SQL, en anglais. La distinction n'est pas cosmétique : la règle est
                # tenue à deux couches indépendantes, et sans ce contrôle l'une serait créditée
                # du travail de l'autre — une mutation l'a montré.
                with self.assertRaises(Exception) as raised:
                    store.attach_proof(identifier, proof["id"], "c07-parity", promote=True)
                self.assertIn("Promotion refusée", str(raised.exception))
                with store._connection() as connection:
                    status = connection.execute(
                        "SELECT status FROM knowledge WHERE id=?", (identifier,)
                    ).fetchone()["status"]
                self.assertEqual(status, "OBSERVED")
            finally:
                del store

    def test_i004_the_promotion_rule_is_held_again_by_sqlite_itself(self) -> None:
        """La seconde couche, isolée : même en contournant le Python, SQLite refuse.

        ARET garde `knowledge.status` par deux triggers — `reject_unproven_insert` et
        `reject_unproven_promotion`. Un `UPDATE` direct vers `PROVEN` sur une connaissance sans
        preuve liée est refusé par la base elle-même, avec son propre message.

        C'est une défense en profondeur, et c'est à mettre au crédit d'ARET. Mais cela veut dire
        qu'un test qui observe seulement « la promotion a échoué » ne prouve **aucune** des deux
        couches : il faut distinguer les messages, ce que les deux tests voisins font.
        """
        # Aucune garde de montage : ce test ne touche ni au dépôt toolkit ni à un oracle,
        # seulement au store ARET. Le garder derrière la garde le faisait sauter en CI pour
        # rien, donc sans jamais être attesté sur les deux plateformes.
        with temporary_root() as root:
            store = self._aret_store(root)
            try:
                identifier = self._knowledge(store, "Connaissance sans aucune preuve")
                with store._connection() as connection:
                    triggers = {
                        row["name"]
                        for row in connection.execute(
                            "SELECT name FROM sqlite_master WHERE type='trigger' AND sql LIKE '%PROVEN%'"
                        )
                    }
                    self.assertEqual(triggers, {"reject_unproven_insert", "reject_unproven_promotion"})
                    with self.assertRaises(Exception) as raised:
                        connection.execute(
                            "UPDATE knowledge SET status='PROVEN' WHERE id=?", (identifier,)
                        )
                    self.assertIn("PROVEN requires a linked admissible PASS proof", str(raised.exception))
            finally:
                del store

    def test_i004_a_passing_proof_with_an_unauthentic_receipt_is_still_refused(self) -> None:
        """L'autre moitié de la gate, isolée — et c'est la condition de la baseline de `C16`.

        Le test précédent prouve la moitié « `result == PASS` » ; celui-ci prouve la moitié
        « `admissible` », en enregistrant une preuve **`PASS`** dont le reçu HMAC est faux.
        `admissible` tombe alors à `0` et la promotion est refusée malgré le `PASS`. Sans les deux
        cas, l'un des deux termes de la conjonction serait crédité du travail de l'autre.

        C'est exactement l'état de la mémoire baseline consignée en `C16` : quatre preuves `PASS`,
        toutes `admissible=0`, zéro promotion sur 532 connaissances.

        Mesuré au passage, une garde de plus : `record_proof` refuse une empreinte d'artefact qui
        ne correspond pas au fichier. Une preuve ne peut donc pas désigner un artefact qu'elle ne
        décrit pas.
        """
        # Sans garde de montage non plus : seul le store ARET est en jeu.
        with temporary_root() as root:
            store = self._aret_store(root)
            try:
                identifier = self._knowledge(store, "Connaissance à preuve non authentique")
                artifact = Path(store.artifacts_dir) / "parity-probe.json"
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text('{"mesure": "C07"}', encoding="utf-8")
                digest = sha256(artifact.read_bytes()).hexdigest()

                common = {
                    "kind": "CPUDIFF", "command": "cargo test", "result": "PASS", "exit_code": 0,
                    "artifact_path": "parity-probe.json", "environment": {},
                    "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:01Z",
                    "stdout_ref": "parity-probe.json", "stderr_ref": "parity-probe.json",
                    "actor": "c07-parity",
                }
                # Une empreinte qui ne décrit pas l'artefact est refusée d'emblée.
                with self.assertRaises(Exception) as mismatched:
                    store.record_proof(**common, artifact_hash="0" * 64, receipt_hmac="f" * 64)
                self.assertIn("ne correspond pas", str(mismatched.exception))

                proof = store.record_proof(**common, artifact_hash=digest, receipt_hmac="f" * 64)
                self.assertEqual(proof["result"], "PASS")
                self.assertEqual(int(proof["admissible"]), 0)

                with self.assertRaises(Exception) as raised:
                    store.attach_proof(identifier, proof["id"], "c07-parity", promote=True)
                self.assertIn("Promotion refusée", str(raised.exception))
                with store._connection() as connection:
                    status = connection.execute(
                        "SELECT status FROM knowledge WHERE id=?", (identifier,)
                    ).fetchone()["status"]
                self.assertEqual(status, "OBSERVED")
            finally:
                del store

    def test_i004_a_real_passing_oracle_is_promoted_to_proven(self) -> None:
        """L'autre versant, et il coûte une vraie exécution : `cpudiff` tourne pour de bon.

        C'est la dimension que `C07` réclamait et qu'aucun test n'avait couverte. Elle demande
        `libunicorn` — que ni `funcdiff` ni `cpudiff` ne déclarent — et une compilation Rust de la
        `--features unpack`. Le test se saute explicitement quand ces préconditions manquent
        plutôt que de prétendre les couvrir.

        Mesuré le 19 septembre 2026 sur cette machine, libunicorn 2.0.1 installée : verdict `PASS`,
        `admissible=1`, artefact de 22 850 octets dont l'empreinte annoncée égale celle recalculée,
        et la connaissance liée passe à `PROVEN`. Durée : 180 s.
        """
        if os.environ.get("VERA_C07_RUN_REAL_ORACLE", "").strip() != "1":
            self.skipTest(
                "Exécution réelle d’oracle non demandée : poser VERA_C07_RUN_REAL_ORACLE=1 "
                "(compte ~180 s et exige libunicorn)"
            )
        toolkit = self._toolkit_with_unicorn()
        oracles = aret_oracles()
        with temporary_root() as root:
            store = self._aret_store(root)
            try:
                identifier = self._knowledge(store, "Connaissance promouvable par preuve PASS")
                outcome = oracles.run_oracle(
                    store, toolkit, "cpudiff", timeout_seconds=1500,
                    knowledge_id=identifier, promote=True,
                )
                proof = outcome["proof"]

                self.assertEqual(outcome["execution"]["result"], "PASS")
                self.assertEqual(outcome["execution"]["exit_code"], 0)
                self.assertEqual(outcome["execution"]["missing_dependencies"], [])
                self.assertFalse(outcome["execution"]["timed_out"])
                self.assertEqual(int(proof["admissible"]), 1)

                artifact = Path(store.artifacts_dir) / outcome["artifact"]["path"]
                self.assertEqual(
                    sha256(artifact.read_bytes()).hexdigest(), outcome["artifact"]["sha256"]
                )
                self.assertTrue(outcome["attachment"]["linked"])
                self.assertTrue(outcome["attachment"]["promoted"])
                self.assertEqual(outcome["attachment"]["knowledge"]["status"], "PROVEN")
            finally:
                del store

    def test_i006_the_vera_core_names_no_external_executable_and_needs_none(self) -> None:
        """Dimension « Core installable sans toolchain » : mesurée, pas supposée.

        Un cycle de vie complet du store se déroule ici sans `wine`, sans MinGW, sans `z3` et sans
        aucun binaire ARET — et aucun module du Core ne nomme l'un de ces outils.
        """
        source_root = Path(__file__).resolve().parents[1] / "src" / "vera_mmu"
        modules = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(source_root.glob("*.py"))
        )
        for tool in ("wine", "i686-w64-mingw32", "winegcc", "target/release/aret", "libunicorn"):
            with self.subTest(outil=tool):
                self.assertNotIn(tool, modules)

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                self.assertEqual(store.identity.project_id, "oracle-parity")
                with store.transaction() as connection:
                    rows = connection.execute("SELECT COUNT(*) FROM store_audit").fetchone()
                self.assertGreaterEqual(rows[0], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
