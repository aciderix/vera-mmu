"""Test de parité du couplage `C05` — `brick` ARET V1 contre `work_item` générique VERA.

Le registre exige, pour promouvoir `C05` : « cycle de vie, Front actif, ordre roadmap, liens, ajout
de dépendance/cycle et import V1 ».

**Le cycle de vie est la dimension qu'il ne faut pas mal lire.** `brick.state` est contraint par un
`CHECK` à cinq valeurs, et il serait tentant d'exiger que le `work_item` importé porte cet état. Ce
serait contredire le dessin que le registre énonce : « importer les briques avec leur métadonnée
sous namespace ARET » et « le Core peut enregistrer un batch générique `WORK_ITEM`, sans décider de
la sémantique legacy ». Le registre `work_item` fixe d'ailleurs `status = 'PLANNED'` par `CHECK` :
le cycle de vie VERA est **événementiel**, porté par `work_lifecycle_event`, pas par une colonne.

La parité tient donc en deux claims séparés, et les mélanger serait inventer un défaut : l'état ARET
doit être **conservé sans perte** dans la métadonnée, et le cycle de vie **de VERA** doit fonctionner
sur un item importé. Les deux sont mesurés ici.

La brique que le Front d'ARET désigne — `RECOV-SPIRVCROSS-0X0`, la seule `ACTIVE` des treize — sert
de fil : c'est elle qu'on importe, qu'on démarre, et qu'on nomme dans le Front de VERA.

Comme en `C03` et `C04`, la source est bâtie en exécutant le DDL réel d'ARET.
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from vera_mmu.front import FrontService
from vera_mmu.gates import GateError, GateService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.work_lifecycle import WorkLifecycleError, WorkLifecycleService
from vera_mmu.domain_packs.aret.brick_projection import (
    AretBrickProjectionError,
    project_aret_v1_brick_page,
)
from vera_mmu.domain_packs.aret.brick_reader import read_aret_v1_brick_page
from vera_mmu.domain_packs.aret.structural_schema_conformance import inspect_aret_v1_brick_schema

from tests.aret_v1_baseline import (
    BASELINE,
    SCHEMA_DIR,
    import_real_bricks,
    import_real_components,
    insert_real_bricks,
    schema_inspection,
    work_items,
)


#: Les cinq états que le `CHECK` d'ARET admet, et les trois que la baseline porte réellement.
ARET_STATES = ("PLANNED", "ACTIVE", "BLOCKED", "DONE", "OBSOLETE")
#: Les champs de Front que le gabarit déclare ; un Front exact les exige tous.
FRONT_FIELDS = ("active_goal", "current_work", "validated_facts", "blockers", "risks", "next_action")


def _prepared(root: Path) -> tuple[Path, Path, Path]:
    """Importer les composants, ajouter les briques réelles, et rendre les chemins utiles."""
    import_real_components(root)
    source = root / "aret-memory"
    database = source / ".aret-memory" / "aret_memory.sqlite"
    insert_real_bricks(database)
    return source, database, root / "project" / ".vera-mmu" / "project.yaml"


class AretC05BrickParityTests(unittest.TestCase):
    # --- ce que VERA déclare du schéma, confronté au schéma ------------------

    def test_the_declared_brick_columns_match_the_real_table_after_migration_005(self) -> None:
        """Dix colonnes : sept de `001`, trois ajoutées par l'`ALTER TABLE` de `005`."""
        observed = [tuple(column) for column in BASELINE["brick_columns"]]
        self.assertEqual(
            observed,
            [
                ("id", "TEXT", True, True, None),
                ("component_id", "TEXT", False, False, None),
                ("title", "TEXT", True, False, None),
                ("state", "TEXT", True, False, None),
                ("description", "TEXT", True, False, "''"),
                ("created_at", "TEXT", True, False, None),
                ("created_by", "TEXT", True, False, None),
                ("milestone", "TEXT", False, False, None),
                ("target_platform", "TEXT", False, False, None),
                ("priority", "INTEGER", True, False, "3"),
            ],
        )
        self.assertFalse(observed[1][2], "`component_id` est nullable, contrairement à function_symbol")

    def test_veras_conformance_passes_against_the_schema_aret_actually_applies(self) -> None:
        """La conformité n'avait jamais vu le vrai schéma, seulement des `CREATE TABLE` réécrits.

        La différence n'est pas cosmétique : le `brick` réel naît de `001` **plus** un `ALTER TABLE`
        de la migration `005`, et SQLite stocke alors un texte que personne n'écrirait à la main.
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, database, _ = _prepared(root)
            stored = sqlite3.connect(database).execute(
                "SELECT sql FROM sqlite_master WHERE name='brick'"
            ).fetchone()[0]
            conformance = inspect_aret_v1_brick_schema(inspection=schema_inspection(database))

        self.assertIn(", milestone TEXT, target_platform TEXT", stored, "l’ALTER n’a pas été appliqué")
        self.assertIsNotNone(conformance)

    def test_the_real_ddl_closes_the_state_set_and_the_priority_range(self) -> None:
        text = (SCHEMA_DIR / "001_initial.sql").read_text(encoding="utf-8")
        body = text[text.index("CREATE TABLE IF NOT EXISTS brick") :]
        body = body[: body.index(";")]
        for state in ARET_STATES:
            self.assertIn(f"'{state}'", body)
        self.assertIn("REFERENCES component(id)", body)
        migration = (SCHEMA_DIR / "005_roadmap_bricks.sql").read_text(encoding="utf-8")
        self.assertIn("CHECK (priority BETWEEN 1 AND 5)", migration)
        self.assertIn("idx_brick_roadmap", migration)

    # --- cycle de vie : deux claims, jamais confondus ------------------------

    def test_the_aret_state_of_every_brick_survives_the_import_without_loss(self) -> None:
        """Premier claim : la sémantique legacy est conservée, pas interprétée."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, database, profile_path = _prepared(root)
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                import_real_bricks(store, database, source)
                imported = {
                    row[0]: json.loads(row[1])["source"]
                    for row in store.connection.execute("SELECT id, metadata_json FROM work_item")
                }
                registry_states = {
                    row[0] for row in store.connection.execute("SELECT DISTINCT status FROM work_item")
                }

        counted: dict[str, int] = {}
        for row in BASELINE["brick_rows"]:
            source_metadata = imported[f"aret-brick--{row['id']}"]
            self.assertEqual(source_metadata["state"], row["state"], row["id"])
            self.assertEqual(source_metadata["milestone"], row["milestone"], row["id"])
            self.assertEqual(source_metadata["target_platform"], row["target_platform"], row["id"])
            self.assertEqual(source_metadata["component_id"], row["component_id"], row["id"])
            counted[row["state"]] = counted.get(row["state"], 0) + 1
        self.assertEqual(counted, BASELINE["brick_states_present"])
        # Second claim, et la raison pour laquelle le premier ne suffit pas : le registre VERA ne
        # porte pas l'état legacy, son `CHECK` le fixe à `PLANNED`. Le cycle de vie est ailleurs.
        self.assertEqual(registry_states, {"PLANNED"})

    def test_veras_own_lifecycle_runs_on_an_imported_brick(self) -> None:
        """Second claim : l'item importé entre bien dans le cycle de vie événementiel du Core."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, database, profile_path = _prepared(root)
            identifier = f"aret-brick--{BASELINE['front_state']['brick']}"
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                import_real_bricks(store, database, source)
                lifecycle = WorkLifecycleService(store)
                self.assertEqual(lifecycle.get_state(identifier).status, "PLANNED")
                lifecycle.transition("c05-start", identifier, "START", "parité C05", actor="parity")
                started = lifecycle.get_state(identifier).status
                lifecycle.transition("c05-done", identifier, "COMPLETE", "parité C05", actor="parity")
                completed = lifecycle.get_state(identifier).status
                with self.assertRaises(WorkLifecycleError):
                    lifecycle.transition("c05-again", identifier, "START", "hors séquence", actor="parity")

        self.assertEqual((started, completed), ("ACTIVE", "COMPLETED"))

    # --- Front actif ---------------------------------------------------------

    def test_the_brick_the_aret_front_points_at_can_be_named_in_veras_front(self) -> None:
        """« Front actif » : la brique en tête côté ARET reste désignable côté VERA.

        `RECOV-SPIRVCROSS-0X0` est la seule des treize à l'état `ACTIVE`, et c'est bien elle que le
        `front_state` d'ARET porte. Une parité qui perdrait ce fil rendrait la reprise muette sur ce
        que le projet était en train de faire.
        """
        active = [row["id"] for row in BASELINE["brick_rows"] if row["state"] == "ACTIVE"]
        self.assertEqual(active, [BASELINE["front_state"]["brick"]])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, database, profile_path = _prepared(root)
            identifier = f"aret-brick--{BASELINE['front_state']['brick']}"
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                import_real_bricks(store, database, source)
                fields = {name: "—" for name in FRONT_FIELDS}
                fields["current_work"] = identifier
                FrontService(store).replace("c05-front", fields, actor="parity", confirm=True)
                current = FrontService(store).current()

        self.assertIsNotNone(current)
        self.assertEqual(current.fields["current_work"], identifier)

    # --- ordre roadmap, liens et import V1 -----------------------------------

    def test_the_roadmap_order_of_the_real_index_is_reproducible(self) -> None:
        """L'index `idx_brick_roadmap` déclare un ordre ; il doit rester calculable après import."""
        expected = BASELINE["brick_roadmap_order"]
        rows = {row["id"]: row for row in BASELINE["brick_rows"]}
        recomputed = sorted(
            rows,
            key=lambda item: (
                rows[item]["milestone"] or "",
                rows[item]["target_platform"] or "",
                rows[item]["priority"],
                rows[item]["state"],
                rows[item]["component_id"] or "",
                item,
            ),
        )
        # SQLite trie les NULL avant toute valeur ; la clé ci-dessus les rend par la chaîne vide,
        # ce qui donne le même ordre puisque aucune valeur présente n'est vide.
        self.assertEqual(recomputed, expected)
        self.assertEqual(expected[0], BASELINE["front_state"]["brick"], "la brique active est en tête")

    def test_the_optional_component_link_is_preserved_including_its_absence(self) -> None:
        """« Liens » : `component_id` est nullable, et cinq briques sur treize n'en portent pas."""
        declared = {item["id"] for item in BASELINE["components"]}
        linked = [row for row in BASELINE["brick_rows"] if row["component_id"] is not None]
        unlinked = [row for row in BASELINE["brick_rows"] if row["component_id"] is None]
        self.assertEqual(len(linked), 8)
        self.assertEqual(len(unlinked), 5)
        self.assertEqual({row["component_id"] for row in linked} - declared, set())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, database, profile_path = _prepared(root)
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                import_real_bricks(store, database, source)
                absent = [
                    json.loads(row[0])["source"]["component_id"]
                    for row in store.connection.execute("SELECT metadata_json FROM work_item")
                ]

        self.assertEqual(sum(1 for value in absent if value is None), 5, "l’absence de lien s’est perdue")

    def test_the_thirteen_real_bricks_import_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, database, profile_path = _prepared(root)
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                result = import_real_bricks(store, database, source)
                rows = work_items(store)

        self.assertEqual(len(result.resources), 13)
        self.assertEqual(
            rows,
            [
                (f"aret-brick--{row['id']}", "WORK_ITEM", row["title"], row["priority"])
                for row in BASELINE["brick_rows"]
            ],
        )

    def test_veras_reader_returns_the_thirteen_real_bricks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, database, _ = _prepared(root)
            inspection = schema_inspection(database)
            collected: list[str] = []
            cursor: str | None = None
            for _ in range(20):
                page = read_aret_v1_brick_page(
                    source_root=source, schema_inspection=inspection, after_id=cursor, limit=5
                )
                collected.extend(record.source_id for record in page.records)
                cursor = page.next_after_id
                if cursor is None:
                    break

        self.assertIsNone(cursor, "la pagination du lecteur ne s’est pas terminée")
        self.assertEqual(collected, [row["id"] for row in BASELINE["brick_rows"]])

    # --- dépendance et cycle -------------------------------------------------

    def test_a_prerequisite_is_accepted_and_a_cycle_is_refused(self) -> None:
        """« Ajout de dépendance/cycle » : l'arête utile passe, la boucle et l'auto-arête non."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, database, profile_path = _prepared(root)
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                import_real_bricks(store, database, source)
                first, second = (row[0] for row in work_items(store)[:2])
                GateService(store).add_dependency(first, second, actor="parity")
                declared = store.connection.execute(
                    "SELECT COUNT(*) FROM work_dependency WHERE dependent_id = ? AND prerequisite_id = ?",
                    (first, second),
                ).fetchone()[0]
                with self.assertRaises(GateError):
                    GateService(store).add_dependency(second, first, actor="parity")
                with self.assertRaises(GateError):
                    GateService(store).add_dependency(first, first, actor="parity")
                remaining = store.connection.execute("SELECT COUNT(*) FROM work_dependency").fetchone()[0]

        self.assertEqual(declared, 1)
        self.assertEqual(remaining, 1, "un refus a laissé une arête derrière lui")

    def test_both_layers_refuse_a_self_edge(self) -> None:
        """L'auto-arête est refusée deux fois, et il faut le dire plutôt que de le supposer.

        `GateService` la refuse explicitement, et le schéma porte aussi `CHECK(dependent_id !=
        prerequisite_id)`. Un test qui n'attrape que `GateError` ne distingue pas les deux : retirer
        la garde Python le laisserait vert, parce que SQLite prendrait le relais. Nommer la couche
        basse ici évite de croire qu'une seule règle tient, et de la retirer un jour sans le voir.
        """
        schema = (
            Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "schema" / "019_work_graph_gates.sql"
        ).read_text(encoding="utf-8")
        body = schema[schema.index("CREATE TABLE IF NOT EXISTS work_dependency") :]
        self.assertIn("CHECK(dependent_id != prerequisite_id)", body[: body.index(";")])

    # --- ce que la projection refuse ----------------------------------------

    def test_a_state_or_priority_outside_arets_own_checks_is_refused(self) -> None:
        """I014 : une brique hors du catalogue fermé échoue bruyamment, elle n'est pas rabotée."""
        from vera_mmu.domain_packs.aret.brick_reader import (
            AretV1BrickSourcePage,
            AretV1BrickSourceRecord,
        )
        from vera_mmu.identity import ProjectIdentity

        identity = ProjectIdentity(
            project_id="c05-parity", profile_version="2.0",
            profile_hash="a" * 64, workspace_hash="b" * 64, project_hash="c" * 64,
        )
        for state, priority in (("INVENTED", 3), ("PLANNED", 0), ("PLANNED", 6)):
            with self.subTest(state=state, priority=priority):
                page = AretV1BrickSourcePage(
                    source_path=Path("/nonexistent"),
                    source_snapshot_sha256="d" * 64,
                    records=(
                        AretV1BrickSourceRecord(
                            source_id="X-1", component_id=None, title="t", state=state,
                            description="", created_at="2026-01-01T00:00:00Z", created_by="parity",
                            milestone=None, target_platform=None, priority=priority,
                        ),
                    ),
                    next_after_id=None,
                )
                with self.assertRaises(AretBrickProjectionError):
                    project_aret_v1_brick_page(
                        target_identity=identity, source_page=page, request_id="c05-parity"
                    )


if __name__ == "__main__":
    unittest.main()
