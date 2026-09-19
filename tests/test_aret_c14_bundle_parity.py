"""Test de parité du couplage `C14` — bundle ARET V1 contre bundle VERA.

Le registre exige, pour promouvoir `C14` : « Manifest/hash chain, altération, import idempotent,
incompatibilité d'identité, non-fusion et restauration du bundle M0.1 ».

**ARET est exécuté, pas lu.** Comme en `C13`, la question porte sur un comportement — que fait ce
bundle devant une mémoire, une altération, une identité étrangère — et une lecture n'y répond pas.
Le `MemoryStore` réel d'ARET est chargé depuis la copie versionnée et tourne sur son propre DDL :
`_migrate` et `_bundle_migrations` cherchent leur schéma à `parents[1]/"schema"`, ce qui désigne
exactement les six migrations versionnées. Rien n'est reconstitué.

**La chaîne d'intégrité d'ARET est solide, et il faut le dire avant tout le reste.** Huit
altérations mesurées — snapshot, artefact, migration, artefact retiré, champ du manifeste,
snapshot retiré, chemin d'évasion — sont toutes refusées, et les comparaisons passent par
`hmac.compare_digest`. `C14` n'est pas un couplage où VERA serait simplement meilleur.

**La divergence est ailleurs, et elle porte sur deux choses que le registre nomme.**

*L'identité.* Le manifeste d'ARET ne contient **aucune identité de projet** — le mot « project »
est absent de ses 2677 lignes — et le `source_device_id` qu'il écrit n'est jamais relu : il
apparaît une seule fois dans toute la source, à l'écriture. Mesuré ci-dessous : un bundle exporté
d'une mémoire s'importe sans objection dans une mémoire qui n'a rien à voir. La seule garde est
« la cible doit être vide ». VERA lie le bundle à `project_identity` et refuse toute autre.

*L'idempotence.* Celle d'ARET est une entrée de registre — « j'ai déjà vu ce bundle » — pas un
constat d'état. Mesuré : après un import suivi d'une mutation, le ré-import annonce encore
`idempotent: True` alors que la mémoire ne vaut plus le bundle. VERA n'accorde `ALREADY_RESTORED`
que si l'empreinte de la mémoire **et** la configuration cible correspondent, et refuse sinon.

Le comportement propre de VERA est déjà éprouvé par `tests/test_m11b_bundle_project_import.py` —
altération, identité, cible non vide, rollback. Ces tests-là comparent VERA à ses propres
attentes ; celui-ci le confronte à ARET sur les mêmes situations. C'est la différence que toute
cette série existe pour établir.
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import unittest
import zipfile

from vera_mmu.bundles import BundleError, BundleService, project_bundle_path, restore_bundle
from vera_mmu.identity import canonical_json, load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore

from tests.aret_v1_baseline import BASELINE, temporary_root
from tests.aret_v1_repository_reference import (
    ADDRESSING_SHA256,
    REFERENCE,
    REFERENCE_SHA256,
    addressing_digest,
    aret_repository,
    memory_store,
    reference_digest,
)


#: Les clefs que le manifeste d'ARET porte réellement, relevées sur un export exécuté.
ARET_MANIFEST_KEYS = {
    "artifact_inventory", "bundle_version", "created_at", "db_hash", "manifest_hash",
    "memory_format_version", "migrations", "schema_version", "snapshot_sha256", "source_device_id",
}
#: Celles de VERA, dont `project_identity` — c'est tout l'écart de `C14`.
VERA_MANIFEST_KEYS = {
    "artifact_inventory", "bundle_id", "checkpoint", "files", "format", "memory_hash",
    "profile_hash", "project_identity", "schema_hash", "source_device_id",
}

BUNDLE_ID = "c14-parite"


def _aret_source(root: Path, *, artifact: bytes = b"artefact de parite") -> tuple[object, str]:
    """Une mémoire ARET réelle, peuplée du vrai corpus baseline, et son bundle exporté."""
    store = memory_store(root)
    with closing(sqlite3.connect(store.db_path)) as connection:
        connection.executemany(
            "INSERT INTO component(id, title, description, created_at, created_by) VALUES (?, ?, ?, ?, ?)",
            [
                (item["id"], item["title"], item["description"], item["created_at"], item["created_by"])
                for item in BASELINE["components"]
            ],
        )
        connection.commit()
    (store.artifacts_dir / "preuve.txt").write_bytes(artifact)
    return store, store.export_bundle("parite")["path"]


def _tampered(bundle: str, target: Path, change) -> Path:
    """Recopier un bundle en appliquant une transformation à ses membres."""
    with zipfile.ZipFile(bundle) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    members = change(members)
    with zipfile.ZipFile(target, "w") as output:
        for name, payload in members.items():
            output.writestr(name, payload)
    return target


def _vera_project(root: Path, project_id: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root, template="software", project_id=project_id, project_name=project_id
    )
    apply_project_initialization(root, preview, confirm=True)
    return root / ".vera-mmu" / "project.yaml"


def _vera_bundle(profile_path: Path) -> Path:
    with MemoryStore.open(load_profile(profile_path), profile_path) as store:
        BundleService(store).export(BUNDLE_ID, confirm=True)
        return project_bundle_path(store, BUNDLE_ID)


class AretC14BundleParityTests(unittest.TestCase):
    def test_the_vendored_sources_are_the_pinned_aret_files(self) -> None:
        """Les deux : le dépôt et l'adressage dont il dépend. Charger un autre adressage ferait
        tourner un ARET qui n'est pas celui qu'on croit mesurer."""
        self.assertEqual(reference_digest(), REFERENCE_SHA256)
        self.assertEqual(addressing_digest(), ADDRESSING_SHA256)

    # --- manifest et chaîne de hachage --------------------------------------

    def test_arets_manifest_chains_three_hashes_and_names_no_project(self) -> None:
        """Le manifeste est relevé sur un export **exécuté**, pas transcrit d'une lecture."""
        with temporary_root() as root:
            _, bundle = _aret_source(root / "source")
            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read("manifest.json"))

        self.assertEqual(set(manifest), ARET_MANIFEST_KEYS)
        self.assertEqual(manifest["bundle_version"], 3)
        for key in ("db_hash", "snapshot_sha256", "manifest_hash"):
            self.assertEqual(len(manifest[key]), 64, key)
        self.assertEqual(len(manifest["migrations"]), 6)
        self.assertTrue(all(len(item["sha256"]) == 64 for item in manifest["migrations"]))
        self.assertIn("manifest.json", names)
        self.assertIn("snapshot.json", names)
        self.assertEqual(sum(name.startswith("schema/") for name in names), 6)

        self.assertFalse(
            [key for key in manifest if "project" in key],
            "le manifeste ARET porterait désormais une identité de projet",
        )

    def test_arets_device_identifier_is_written_once_and_never_read_back(self) -> None:
        """Un champ d'identité qui n'est comparé nulle part n'atteste rien.

        Le fait est établi sur la source entière, pas sur la fonction d'export : une seule
        occurrence de `source_device_id` dans 2677 lignes, et c'est l'écriture. Si un contrôle
        apparaissait un jour à l'import, ce test tomberait et la parité devrait être revue.
        """
        source = REFERENCE.read_text(encoding="utf-8")
        self.assertEqual(source.count("source_device_id"), 1)
        self.assertIn('os.environ.get("ARET_SOURCE_DEVICE_ID", "UNSPECIFIED")', source)

        with temporary_root() as root:
            _, bundle = _aret_source(root / "source")
            with zipfile.ZipFile(bundle) as archive:
                manifest = json.loads(archive.read("manifest.json"))
        self.assertEqual(manifest["source_device_id"], "UNSPECIFIED")

    def test_veras_manifest_binds_the_bundle_to_a_project_identity(self) -> None:
        """Le pendant : cinq champs d'identité, dans un jeu de clefs fermé."""
        with temporary_root() as root:
            bundle = _vera_bundle(_vera_project(root / "projet", "c14-identite"))
            with zipfile.ZipFile(bundle) as archive:
                manifest = json.loads(archive.read("manifest.json"))

        self.assertEqual(set(manifest), VERA_MANIFEST_KEYS)
        self.assertEqual(
            set(manifest["project_identity"]),
            {"project_id", "profile_version", "profile_hash", "workspace_hash", "project_hash"},
        )
        self.assertEqual(manifest["project_identity"]["project_id"], "c14-identite")

    # --- altération ----------------------------------------------------------

    def test_every_link_of_arets_chain_refuses_its_own_tampering(self) -> None:
        """Huit altérations, huit refus : la chaîne d'ARET tient, et c'est mesuré.

        Ce test n'est pas là pour faire bonne mesure. Un couplage où l'on ne relèverait que les
        divergences serait un réquisitoire ; celui-ci établit d'abord ce qu'ARET fait bien, faute
        de quoi la conclusion sur l'identité n'aurait pas de contexte.
        """
        repository = aret_repository()
        alterations = {
            "snapshot": lambda m: {**m, "snapshot.json": m["snapshot.json"].replace(b"ABI", b"XYZ")},
            "artefact": lambda m: {**m, "artifacts/preuve.txt": b"contenu substitue!"},
            "migration": lambda m: {
                **m, "schema/001_initial.sql": m["schema/001_initial.sql"] + b"\n-- injection\n"
            },
            "artefact retiré": lambda m: {n: d for n, d in m.items() if n != "artifacts/preuve.txt"},
            "snapshot retiré": lambda m: {n: d for n, d in m.items() if n != "snapshot.json"},
            "champ du manifeste": lambda m: {
                **m, "manifest.json": m["manifest.json"].replace(b'"bundle_version":3', b'"bundle_version":9')
            },
            "chemin d’évasion": lambda m: {**m, "../evade.txt": b"sortie"},
            "manifeste vide": lambda m: {**m, "manifest.json": b"{}"},
        }
        with temporary_root() as root:
            _, bundle = _aret_source(root / "source")
            for index, (label, change) in enumerate(alterations.items()):
                with self.subTest(label):
                    altered = _tampered(bundle, root / f"altere-{index}.zip", change)
                    target = memory_store(root / f"cible-{index}")
                    with self.assertRaises(repository.AretError, msg=label):
                        target.import_bundle(altered)

    def test_vera_refuses_the_same_tampering_on_its_own_bundle(self) -> None:
        """La même main sur l'autre bundle, sur quatre maillons plutôt qu'un.

        Le premier essai n'altérait que la mémoire, et il passait encore lorsqu'on retirait la
        vérification d'inventaire : le hash de mémoire est contrôlé **une seconde fois** par sa
        propre règle. Une propriété satisfaite par deux routes n'en prouve aucune — même classe de
        défaut qu'en `C09`. L'artefact, lui, ne dépend que de l'inventaire.

        Le manifeste enrichi d'une clef inconnue est le cas qui manquait complètement : le contrat
        fermé est une règle **de lecture**, et un test qui n'inspecte que le manifeste produit à
        l'export ne la touche jamais.
        """
        with temporary_root() as root:
            profile_path = _vera_project(root / "projet", "c14-altere")
            artifacts = profile_path.parent / "artifacts"
            artifacts.mkdir(exist_ok=True)
            (artifacts / "preuve.txt").write_text("artefact de parite\n", encoding="utf-8")
            bundle = _vera_bundle(profile_path)

            with zipfile.ZipFile(bundle) as archive:
                names = archive.namelist()
            memory = next(name for name in names if name.endswith("memory.sqlite"))
            artifact = next(name for name in names if name.startswith("runtime/artifacts/"))

            def rewritten(members: dict[str, bytes], change) -> dict[str, bytes]:
                """Réécrire le manifeste **canoniquement**, sinon la garde de canonicité répond seule.

                Mesuré : un `json.dumps` ordinaire est refusé par « Manifest de bundle non
                canonique » avant même d'être examiné. C'est une garde plus forte que le contrat
                fermé — toute édition du manifeste est refusée, quel qu'en soit le contenu — mais
                elle masque les règles qui la suivent. Pour les atteindre, il faut produire des
                octets canoniques.
                """
                manifest = json.loads(members["manifest.json"])
                change(manifest)
                return {**members, "manifest.json": canonical_json(manifest).encode("utf-8")}

            def add_unknown_key(manifest: dict) -> None:
                manifest["clef_inconnue"] = "glissee"

            def move_profile_hash(manifest: dict) -> None:
                # `profile_hash` existe deux fois : au sommet et dans `project_identity`. Ne toucher
                # que le premier isole la garde redondante, que la comparaison d'identité ne voit pas.
                manifest["profile_hash"] = "0" * 64

            alterations = {
                "mémoire": lambda m: {**m, memory: m[memory] + b"\0octet"},
                "artefact": lambda m: {**m, artifact: b"contenu substitue\n"},
                "manifeste non canonique": lambda m: {
                    **m, "manifest.json": b" " + m["manifest.json"]
                },
                "clef inconnue au manifeste": lambda m: rewritten(m, add_unknown_key),
                "hash de profil divergent": lambda m: rewritten(m, move_profile_hash),
                "membre retiré": lambda m: {n: d for n, d in m.items() if n != artifact},
                "membre ajouté hors inventaire": lambda m: {
                    **m, "runtime/artifacts/clandestin.txt": b"absent de l inventaire\n"
                },
            }
            target = _vera_project(root / "cible", "c14-altere")
            for index, (label, change) in enumerate(alterations.items()):
                with self.subTest(label):
                    altered = _tampered(str(bundle), root / f"altere-{index}.zip", change)
                    with self.assertRaises(BundleError, msg=label):
                        restore_bundle(altered, target, confirm=True)

    # --- incompatibilité d'identité -----------------------------------------

    def test_an_aret_bundle_imports_into_a_memory_it_has_nothing_to_do_with(self) -> None:
        """Le cœur de `C14`, mesuré en l'exécutant plutôt qu'en le déduisant du code.

        Deux mémoires ARET sans aucun lien : la seconde accepte le bundle de la première sans une
        objection, parce qu'il n'y a rien dans le manifeste qui puisse la lui faire refuser. La
        seule garde est « la cible est vide », et une cible vide est le cas normal d'une restauration.
        """
        with temporary_root() as root:
            _, bundle = _aret_source(root / "source")
            etranger = memory_store(root / "sans-rapport")
            outcome = etranger.import_bundle(bundle)
            with closing(sqlite3.connect(etranger.db_path)) as connection:
                arrived = sorted(row[0] for row in connection.execute("SELECT id FROM component"))

        self.assertTrue(outcome["imported"])
        self.assertFalse(outcome["idempotent"])
        self.assertEqual(arrived, sorted(item["id"] for item in BASELINE["components"]))
        self.assertEqual(len(arrived), 17)

    def test_vera_refuses_a_bundle_belonging_to_another_project_identity(self) -> None:
        """Le refus porte sur l'identité, et il tombe **avant** toute écriture dans la cible."""
        with temporary_root() as root:
            bundle = _vera_bundle(_vera_project(root / "un", "c14-projet-un"))
            other = _vera_project(root / "deux", "c14-projet-deux")
            other_memory = other.parent / "memory.sqlite"
            before = other_memory.read_bytes() if other_memory.exists() else None

            with self.assertRaises(BundleError) as refused:
                restore_bundle(bundle, other, confirm=True)

            after = other_memory.read_bytes() if other_memory.exists() else None

        self.assertIn("autre identité de projet", str(refused.exception))
        self.assertEqual(after, before, "la cible a été touchée malgré le refus")

    # --- idempotence ---------------------------------------------------------

    def test_arets_idempotence_answers_for_the_ledger_and_veras_for_the_state(self) -> None:
        """Deux réponses au même mot, et l'écart se voit seulement après une divergence.

        ARET consigne le bundle importé dans `bundle_import` et répond d'après cette entrée. La
        mémoire peut avoir changé depuis : la réponse reste `idempotent: True`. Un opérateur qui
        la lit conclurait que la mémoire vaut le bundle. Elle ne le vaut plus.

        VERA n'accorde `ALREADY_RESTORED` que si l'empreinte de la mémoire **et** la configuration
        cible correspondent ; sinon elle refuse, plutôt que d'annoncer une équivalence fausse.
        """
        with temporary_root() as root:
            _, bundle = _aret_source(root / "source")
            target = memory_store(root / "cible")
            first = target.import_bundle(bundle)
            target.register_component("APRES", "Ajoute apres import", "divergence", "parite")
            again = target.import_bundle(bundle)
            with closing(sqlite3.connect(target.db_path)) as connection:
                present = {row[0] for row in connection.execute("SELECT id FROM component")}

        self.assertTrue(first["imported"])
        self.assertFalse(again["imported"])
        self.assertTrue(again["idempotent"], "ARET ne répond plus d’après son registre")
        self.assertIn("APRES", present, "la mémoire n’a pas divergé : la mesure ne porte sur rien")

        with temporary_root() as root:
            bundle = _vera_bundle(_vera_project(root / "source", "c14-idempotence"))
            # La cible porte la même identité et pas encore de mémoire : c'est le cas d'une
            # restauration. Restaurer sur la source elle-même ne mesurerait rien — sa mémoire
            # vivante ne vaut pas l'instantané pris par l'export, et le refus tomberait pour
            # une raison qui n'est pas celle qu'on veut établir.
            target = _vera_project(root / "cible", "c14-idempotence")
            restored = restore_bundle(bundle, target, confirm=True)
            exact = restore_bundle(bundle, target, confirm=True)
            with MemoryStore.open(load_profile(target), target) as store:
                with store.transaction() as connection:
                    store.append_audit(connection, "C14_DIVERGENCE", {"source": "parite"})
            with self.assertRaises(BundleError) as diverged:
                restore_bundle(bundle, target, confirm=True)

        self.assertEqual(restored.status, "RESTORED")
        self.assertEqual(exact.status, "ALREADY_RESTORED")
        self.assertIn("divergente", str(diverged.exception))

    # --- non-fusion ----------------------------------------------------------

    def test_neither_engine_merges_a_bundle_into_a_memory_that_already_holds_something(self) -> None:
        """Le point d'accord, dit aussi clairement que les divergences.

        Les deux refusent, et pour la même raison de fond : fusionner deux mémoires sans que
        personne ne l'ait demandé produirait un état dont aucune des deux ne répond.
        """
        repository = aret_repository()
        with temporary_root() as root:
            _, bundle = _aret_source(root / "source")
            occupied = memory_store(root / "occupee")
            occupied.register_component("AUTRE", "Deja la", "cible non vide", "parite")
            with self.assertRaises(repository.AretError) as aret_refused:
                occupied.import_bundle(bundle)

        with temporary_root() as root:
            profile_path = _vera_project(root / "projet", "c14-non-fusion")
            vera_bundle = _vera_bundle(profile_path)
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                with store.transaction() as connection:
                    store.append_audit(connection, "C14_OCCUPATION", {"source": "parite"})
            with self.assertRaises(BundleError) as vera_refused:
                restore_bundle(vera_bundle, profile_path, confirm=True)

        self.assertIn("aucune fusion implicite", str(aret_refused.exception))
        self.assertIn("fusion interdite", str(vera_refused.exception))

    # --- restauration du corpus réel ----------------------------------------

    def test_the_seventeen_real_components_survive_arets_own_bundle_round_trip(self) -> None:
        """« Restauration du bundle M0.1 », sur le vrai corpus et par le vrai bundle d'ARET.

        La mémoire baseline de onze mégaoctets n'est pas versionnée — son empreinte l'atteste — mais
        ses lignes le sont. Elles sont insérées dans un store ARET réel, exportées par son propre
        `export_bundle`, et relues après import : ce qui est mesuré est un aller-retour complet sur
        des données de production, pas sur un échantillon écrit pour l'occasion.
        """
        with temporary_root() as root:
            source, bundle = _aret_source(root / "source")
            with closing(sqlite3.connect(source.db_path)) as connection:
                connection.row_factory = sqlite3.Row
                departed = [
                    dict(row)
                    for row in connection.execute(
                        "SELECT id, title, description, created_at, created_by FROM component ORDER BY id"
                    )
                ]

            target = memory_store(root / "cible")
            outcome = target.import_bundle(bundle)
            with closing(sqlite3.connect(target.db_path)) as connection:
                connection.row_factory = sqlite3.Row
                arrived = [
                    dict(row)
                    for row in connection.execute(
                        "SELECT id, title, description, created_at, created_by FROM component ORDER BY id"
                    )
                ]
            restored_artifact = (target.artifacts_dir / "preuve.txt").read_bytes()

        self.assertEqual(departed, sorted(BASELINE["components"], key=lambda item: item["id"]))
        self.assertEqual(arrived, departed)
        self.assertEqual(len(arrived), 17)
        self.assertEqual(outcome["artifact_count"], 1)
        self.assertEqual(restored_artifact, b"artefact de parite")


if __name__ == "__main__":
    unittest.main()
