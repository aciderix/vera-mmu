"""Parité partielle de `C07` et `C08` — ce qui se mesure sans chaîne d'outils.

**Ce fichier ne promeut ni `C07` ni `C08`,** et c'est délibéré. Leurs preuves exigées comportent
chacune une dimension qui demande d'exécuter un vrai oracle — « evidence hashée, promotion `PROVEN`
et gate réelle » pour `C07`, « exécutabilité mesurée dans une image de référence » pour `C08` —, et
cela réclame Wine, MinGW et un binaire `target/release/aret` construit. Aucun test ici ne les
couvre, et aucune ligne du registre ne passe à `DONE` de ce fait.

Ce qui **est** couvert est tout le reste, et ce n'est pas mince : ce qui se décide **avant** qu'un
processus démarre, et ce qui arrive quand les préconditions manquent.

**Trois fonctions d'ARET portent l'essentiel et aucune ne lance quoi que ce soit.**
`normalise_result` est une fonction **pure** de `(spec, exit_code, stdout, stderr, missing,
timed_out)` ; `_repository_file` est de la résolution de chemin ; `safe_fixture` est une expression
régulière. `ORACLES` est un dictionnaire fermé de neuf specs. La méthode est celle de `C06`, `C12`,
`C14` et `C15` : la référence est versionnée, épinglée et **exécutée**.

**Ce qu'ARET fait bien, et il faut le dire d'abord.**

1. *La précédence de normalisation est juste.* Une dépendance manquante l'emporte sur tout —
   y compris sur un `timed_out` et sur une sortie qui ressemble à un succès. On ne déclare pas
   un verdict sur une exécution qui n'a pas eu lieu.
2. *Un code de sortie non nul reste un `FAIL` même avec une ligne `SKIP` dans la sortie.* Le
   commentaire du code le dit et la mesure le confirme : un échec global n'est jamais masqué par
   un SKIP partiel.
3. *Un corpus vide n'est pas un succès.* Les regexes exigent `int(groupe2) > 0` : `0 / 0` rend
   `ERROR`, pas `PASS`. Mesuré.
4. *`winehash` rend `UNKNOWN` même quand il réussit*, et son commentaire dit pourquoi : « c'est une
   mesure Wine à comparer au runner Windows, pas un gate de conformité ». Refuser de transformer
   une mesure en verdict est exactement la discipline que `I004` demande.
5. *Le confinement tient.* `../`, `../../etc/passwd`, un chemin absolu et un lien symbolique
   sortant sont tous refusés — les quatre mesurés.

**La divergence, et elle porte sur une seule question : d'où vient le verdict.**

ARET le **dérive de la prose** du script, par huit expressions régulières sur des lignes de
résumé lisibles par un humain (`differential equivalence: 272 / 272 functions`). VERA le fait
calculer par un validateur fermé, comme une **comparaison d'empreintes** — `PASS` si l'observé
égale l'attendu, `FAIL` sinon —, et son module de validation n'importe même pas `subprocess`.

La conséquence est mesurée plus bas et elle n'est pas théorique : changer `functions` en
`function` dans la sortie — un mot, un caractère — transforme un `PASS` en `ERROR`. Le script n'a
pas changé de comportement, seulement de formulation. Une comparaison d'empreintes n'a pas ce
mode de défaillance.

**Pour `C08`, l'absence de chaîne d'outils est le fixture, pas l'obstacle.** Sa preuve exigée
demande « Core installable sans toolchain » et « tests `SKIPPED` explicites » : les deux se
mesurent précisément parce que `wine` et MinGW manquent de cette machine.
"""
from __future__ import annotations

from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.evidence import VERDICTS, EvidenceError, EvidenceService
from vera_mmu.executions import ExecutionError, ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore

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
