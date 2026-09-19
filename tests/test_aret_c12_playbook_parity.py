"""Test de parité du couplage `C12` — le playbook Markdown d'ARET contre celui de VERA.

Le registre exige, pour promouvoir `C12` : « Cinq sections ARET, taille, hash, injection de
reprise, changement du playbook sans mutation de l'état canonique ».

**ARET est exécuté.** Son chargeur de playbook tourne sur son **vrai** playbook, versionné sous
`fixtures/aret_v1/config/playbook.md` : le chemin par défaut qu'ARET calcule —
`Path(__file__).parents[1] / "config" / "playbook.md"` depuis `source/repository_reference.py` —
désigne exactement cette copie. Aucun double, aucune reconstitution.

**Le point d'accord est le plus important du couplage, et il est dit en premier.** Les deux
moteurs tiennent le playbook **hors** de la mémoire canonique : c'est un fichier autoré, lu et
jamais ingéré. Éditer le playbook ne mute pas SQLite, ni chez l'un ni chez l'autre. C'est mesuré
ici sur les deux, empreinte de base à l'appui, parce que c'est la propriété que `C12` protège.

**Les divergences portent sur ce qui arrive quand le playbook manque ou déborde.**

*Absence.* Le chargeur d'ARET rend une **liste vide** quand le fichier n'existe pas ; le contrat
de dossier signalera ensuite chaque domaine manquant. VERA refuse à la compilation, et son
commentaire dit pourquoi : « les instructions générées ne doivent jamais laisser tomber
silencieusement les règles qu'un projet a choisi d'imposer » (I014). Deux réponses défendables,
qui ne se ressemblent pas.

*Silence du parseur.* Mesuré en l'exécutant : un domaine **dupliqué** voit sa seconde occurrence
écartée sans un mot, et un titre `## PLAYBOOK_INVENTE` est écarté de même. L'auteur d'un playbook
ne peut pas savoir qu'une section qu'il a écrite n'est arrivée nulle part.

*Taille.* Les deux bornent, mais pas au même endroit. ARET borne le **dossier assemblé** à
12 500 octets, contrôlé après assemblage ; son fichier de playbook, lui, n'a aucune borne —
la mention « ≤ 12 500 octets » de son en-tête est un budget adressé à l'auteur, pas un contrôle.
VERA borne le **fichier** à 65 536 octets, refusé à la lecture. Borner l'entrée dit quel fichier
est fautif ; borner la sortie dit seulement que le total déborde.

*Hash.* ARET hache **chaque section** et n'a pas d'empreinte du fichier entier ; VERA hache le
fichier entier et n'a pas d'empreinte par section. Les deux servent, et ils ne répondent pas à la
même question : « cette section a-t-elle changé ? » contre « ce playbook est-il celui que j'ai
compilé ? ».
"""
from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import unittest

from vera_mmu.__main__ import main
from vera_mmu.identity import load_profile
from vera_mmu.playbook import (
    CORE_LAWS,
    MAX_PLAYBOOK_BYTES,
    PLAYBOOK_FILE_NAME,
    PlaybookError,
    compile_project_playbook,
)
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore

from tests.aret_v1_baseline import temporary_root
from tests.aret_v1_repository_reference import aret_repository, memory_store


PLAYBOOK = Path(__file__).resolve().parent / "fixtures" / "aret_v1" / "config" / "playbook.md"
#: SHA-256 de `aret-memory/config/playbook.md` au commit épinglé par le README des fixtures.
PLAYBOOK_SHA256 = "5f0acce14fbdfee6d0b3ef67cb40949e0581b9cf1d250650c49c8ea1a5dfbf27"

#: Les cinq domaines qu'ARET impose, dans leur ordre canonique déclaré.
ARET_DOMAINS = (
    "PLAYBOOK_FOUNDATION",
    "PLAYBOOK_METHOD",
    "PLAYBOOK_ARCHITECTURE",
    "PLAYBOOK_GATES",
    "PLAYBOOK_TOOLING",
)


def _vera_project(root: Path, project_id: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root, template="software", project_id=project_id, project_name=project_id
    )
    apply_project_initialization(root, preview, confirm=True)
    return root / ".vera-mmu" / "project.yaml"


def _instructions(profile_path: Path) -> str:
    """Compiler les instructions d'un projet prêt et rendre leur texte."""
    output = StringIO()
    with redirect_stdout(StringIO()):
        assert main(["init", str(profile_path)]) == 0
        assert main(["sync-capabilities", str(profile_path)]) == 0
    with redirect_stdout(output):
        assert main(["generate", str(profile_path), "--adapter", "generic-mcp"]) == 0
    return json.loads(output.getvalue())["generation"]["outputs"]["instructions"]


class AretC12PlaybookParityTests(unittest.TestCase):
    def setUp(self) -> None:
        # Le chargeur d'ARET consulte `ARET_PLAYBOOK_PATH` ; les cas qui s'en servent le
        # restaurent ici, pour qu'aucun test ne laisse une variable globale aux suivants.
        self.addCleanup(os.environ.pop, "ARET_PLAYBOOK_PATH", None)

    def test_the_vendored_playbook_is_the_pinned_aret_file(self) -> None:
        self.assertEqual(sha256(PLAYBOOK.read_bytes()).hexdigest(), PLAYBOOK_SHA256)

    # --- le point d'accord : hors mémoire canonique --------------------------

    def test_neither_engine_lets_the_playbook_touch_the_canonical_memory(self) -> None:
        """La propriété que `C12` protège, mesurée sur les deux par l'empreinte de la base.

        C'est le dessin commun, et il est bon : un fichier autoré qu'on édite librement ne doit
        pas pouvoir faire dériver la mémoire vivante. Chez ARET c'est écrit en toutes lettres dans
        le fichier lui-même — « il n'est jamais ingéré dans SQLite » — et chez VERA c'est la même
        règle. Les deux sont vérifiés en éditant le playbook puis en rehachant la base.
        """
        module = aret_repository()
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            before = sha256(store.db_path.read_bytes()).hexdigest()
            self.assertEqual(len(store._load_playbook_entries()), 5)
            edited = root / "edite.md"
            edited.write_text(
                "## PLAYBOOK_FOUNDATION — édité\n\nUne règle réécrite.\n", encoding="utf-8"
            )
            os.environ["ARET_PLAYBOOK_PATH"] = str(edited)
            self.assertEqual(len(store._load_playbook_entries()), 1)
            after = sha256(store.db_path.read_bytes()).hexdigest()
            del os.environ["ARET_PLAYBOOK_PATH"]

            profile_path = _vera_project(root / "projet", "c12-canonique")
            with MemoryStore.open(load_profile(profile_path), profile_path) as vera:
                database = vera.locator.sqlite_path
                compile_project_playbook(vera)
                vera_before = sha256(database.read_bytes()).hexdigest()
                playbook = vera.locator.runtime_dir / PLAYBOOK_FILE_NAME
                playbook.write_text(
                    playbook.read_text(encoding="utf-8") + "\n- Une règle ajoutée.\n",
                    encoding="utf-8",
                )
                recompiled = compile_project_playbook(vera)
                vera_after = sha256(database.read_bytes()).hexdigest()

        self.assertEqual(after, before, "ARET a muté sa mémoire en lisant son playbook")
        self.assertEqual(vera_after, vera_before, "VERA a muté sa mémoire en lisant son playbook")
        self.assertIn("Une règle ajoutée.", recompiled.text)
        self.assertEqual(module.CORE_PLAYBOOK_TAG, "CORE_PLAYBOOK")

    # --- cinq sections -------------------------------------------------------

    def test_the_five_aret_domains_load_in_their_canonical_order(self) -> None:
        """Les cinq sections sont chargées depuis le vrai playbook, pas décrites.

        L'ordre rendu est celui des domaines **déclarés**, pas celui du fichier : le chargeur trie
        explicitement, et c'est ce qui rend le dossier stable quand quelqu'un déplace une section.
        """
        module = aret_repository()
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            resolved = store._playbook_path()
            entries = store._load_playbook_entries()

        self.assertEqual(resolved, PLAYBOOK, "ARET ne lit pas la copie versionnée")
        self.assertEqual(module.PLAYBOOK_DOMAINS, ARET_DOMAINS)
        self.assertEqual(tuple(item["domains"][0] for item in entries), ARET_DOMAINS)
        for item in entries:
            with self.subTest(item["domains"][0]):
                domain = item["domains"][0]
                self.assertEqual(item["id"], f"PLAYBOOK-{domain}")
                self.assertEqual(item["address"], f"playbook.md#{domain}")
                self.assertEqual(item["type"], "PLAYBOOK")
                self.assertEqual(item["status"], "ACTIVE")
                self.assertEqual(len(item["content_hash"]), 64)
                self.assertGreater(len(item["content"]), 500, domain)

    def test_arets_parser_drops_a_duplicate_or_unknown_domain_without_a_word(self) -> None:
        """Trois silences mesurés, et c'est le défaut d'usage de ce dessin.

        Un domaine répété, un domaine inventé, un fichier absent : dans les trois cas la section
        disparaît sans diagnostic. L'auteur d'un playbook ne peut pas savoir qu'une règle qu'il a
        écrite n'est arrivée nulle part — et une règle qui n'arrive nulle part n'est pas une règle.
        """
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            cases = {
                "domaine dupliqué": (
                    "## PLAYBOOK_FOUNDATION — première\n\nA\n\n## PLAYBOOK_FOUNDATION — seconde\n\nB\n",
                    [("PLAYBOOK_FOUNDATION", "première", "A")],
                ),
                "domaine inventé": (
                    "## PLAYBOOK_INVENTE — ignorée\n\nA\n\n## PLAYBOOK_METHOD — retenue\n\nB\n",
                    [("PLAYBOOK_METHOD", "retenue", "B")],
                ),
            }
            for label, (text, expected) in cases.items():
                with self.subTest(label):
                    source = root / f"{label.replace(' ', '-')}.md"
                    source.write_text(text, encoding="utf-8")
                    os.environ["ARET_PLAYBOOK_PATH"] = str(source)
                    loaded = [
                        (item["domains"][0], item["title"], item["content"])
                        for item in store._load_playbook_entries()
                    ]
                    self.assertEqual(loaded, expected, label)

            os.environ["ARET_PLAYBOOK_PATH"] = str(root / "absent.md")
            self.assertEqual(store._load_playbook_entries(), [], "un fichier absent lève désormais")

    def test_vera_refuses_rather_than_returning_an_empty_playbook(self) -> None:
        """Le pendant : quatre situations, quatre refus nommés.

        Le commentaire du module le dit — un playbook absent ou hors borne est un refus « plutôt
        qu'une section vide », parce que les instructions générées ne doivent jamais laisser tomber
        en silence les règles qu'un projet a choisi d'imposer.
        """
        with temporary_root() as root:
            profile_path = _vera_project(root / "projet", "c12-refus")
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                playbook = store.locator.runtime_dir / PLAYBOOK_FILE_NAME
                original = playbook.read_bytes()

                cases = {
                    "vide": b"   \n",
                    "hors borne": b"#" * (MAX_PLAYBOOK_BYTES + 1),
                    "non UTF-8": b"\xff\xfe invalide",
                }
                for label, payload in cases.items():
                    with self.subTest(label):
                        playbook.write_bytes(payload)
                        with self.assertRaises(PlaybookError, msg=label):
                            compile_project_playbook(store)

                playbook.unlink()
                with self.subTest("absent"):
                    with self.assertRaises(PlaybookError) as absent:
                        compile_project_playbook(store)

                playbook.write_bytes(original)
                restored = compile_project_playbook(store)

        self.assertIn("absent", str(absent.exception))
        self.assertEqual(restored.playbook_hash, sha256(original).hexdigest())

    # --- taille --------------------------------------------------------------

    def test_the_two_size_bounds_are_not_placed_at_the_same_end(self) -> None:
        """ARET borne la sortie, VERA borne l'entrée, et les deux se mesurent.

        La borne d'ARET porte sur le **dossier assemblé**. Son fichier de playbook n'en a aucune :
        la mention « ≤ 12 500 octets » de son en-tête s'adresse à l'auteur. Le contenu réel de ses
        cinq sections occupe déjà une large part de ce budget avant qu'un seul handoff n'y entre,
        ce qui est relevé ici plutôt que supposé.
        """
        module = aret_repository()
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            sections = store._load_playbook_entries()
        content_bytes = sum(len(item["content"].encode("utf-8")) for item in sections)

        self.assertEqual(module.RESUME_DOSSIER_MAX_BYTES, 12_500)
        self.assertEqual(module.RESUME_DOSSIER_MIN_BYTES, 2_000)
        self.assertGreater(content_bytes, module.RESUME_DOSSIER_MAX_BYTES // 2)
        self.assertLess(content_bytes, module.RESUME_DOSSIER_MAX_BYTES)

        # Aucune borne sur le fichier lui-même : le chargeur ne mesure jamais sa taille.
        source = (
            Path(__file__).resolve().parent / "fixtures" / "aret_v1" / "source" / "repository_reference.py"
        ).read_text(encoding="utf-8")
        loader = source[source.index("def _load_playbook_entries") :]
        loader = loader[: loader.index("\n    def ", 1)]
        for marker in ("MAX_BYTES", "len(text)", "stat()"):
            self.assertNotIn(marker, loader, f"le chargeur ARET borne désormais son fichier ({marker})")

        self.assertEqual(MAX_PLAYBOOK_BYTES, 65_536)

    # --- hash ----------------------------------------------------------------

    def test_one_hashes_each_section_and_the_other_hashes_the_whole_file(self) -> None:
        """Deux empreintes qui ne répondent pas à la même question, et aucune ne remplace l'autre.

        ARET sait dire « cette section a changé » et ne sait pas dire « ce playbook est celui que
        j'ai compilé ». VERA sait l'inverse. Les deux faits sont épinglés, y compris l'absence de
        l'empreinte que chacun n'a pas.
        """
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            entries = store._load_playbook_entries()
            hashes = {item["domains"][0]: item["content_hash"] for item in entries}

            profile_path = _vera_project(root / "projet", "c12-hash")
            with MemoryStore.open(load_profile(profile_path), profile_path) as vera:
                playbook = vera.locator.runtime_dir / PLAYBOOK_FILE_NAME
                first = compile_project_playbook(vera)
                playbook.write_text(
                    playbook.read_text(encoding="utf-8") + "\n- Une règle de plus.\n", encoding="utf-8"
                )
                second = compile_project_playbook(vera)

        self.assertEqual(len(hashes), 5)
        self.assertEqual(len(set(hashes.values())), 5, "deux sections partagent une empreinte")
        # ARET n'expose aucune empreinte de fichier entier : les entrées n'en portent pas.
        self.assertFalse([key for key in entries[0] if key not in {
            "id", "type", "status", "title", "domains", "address", "content", "content_hash"
        }])

        self.assertNotEqual(first.playbook_hash, second.playbook_hash)
        self.assertEqual(len(first.playbook_hash), 64)
        self.assertEqual(first.core_laws, CORE_LAWS)
        self.assertEqual(len(CORE_LAWS), 8)

    # --- injection de reprise -------------------------------------------------

    def test_each_engine_carries_its_playbook_into_the_resumption_its_own_way(self) -> None:
        """ARET adresse ses sections ; VERA cite son texte verbatim.

        L'adresse `playbook.md#<DOMAIN>` permet de désigner une loi sans la recopier. VERA n'a pas
        d'adresse de section — elle n'a pas de sections — et cite le playbook mot pour mot dans les
        instructions compilées, ce qui est vérifié ici sur une ligne distinctive ajoutée exprès.
        """
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            addresses = [item["address"] for item in store._load_playbook_entries()]

            profile_path = _vera_project(root / "projet", "c12-reprise")
            playbook = profile_path.parent / PLAYBOOK_FILE_NAME
            marker = "Une loi de projet parfaitement reconnaissable."
            playbook.write_text(
                playbook.read_text(encoding="utf-8") + f"\n6. {marker}\n", encoding="utf-8"
            )
            instructions = _instructions(profile_path)

        self.assertEqual(addresses, [f"playbook.md#{domain}" for domain in ARET_DOMAINS])
        self.assertIn(marker, instructions, "le playbook n’est pas cité verbatim")
        for law in CORE_LAWS:
            with self.subTest(law):
                self.assertIn(law, instructions, law)


if __name__ == "__main__":
    unittest.main()
