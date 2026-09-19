"""Test de parité du couplage `C03` — table `component` ARET V1 contre entités génériques VERA.

Le registre exige, pour promouvoir `C03` : « import de composant, unicité, liens de connaissance,
intégrité référentielle, export/import bundle et absence de `component` dans le Core ».

Les tests de composant existants bâtissent leur source avec un `CREATE TABLE component` **écrit à la
main dans la fixture**, et la conformité de schéma se vérifie contre `aret_v1_schema_manifest()` —
une déclaration VERA de ce qu'est le schéma ARET. Rien n'avait jamais comparé cette déclaration au
vrai fichier de schéma. C'est le même défaut qu'en `C01`, un cran plus profond : non plus un module
comparé à ses propres attentes, mais une **fixture** écrite d'après elles. Un contrat faux passerait
partout, puisque la source de test le satisferait par construction.

Ici la source est construite en exécutant **le DDL réel d'ARET** — les six fichiers `schema/*.sql`
versionnés sous `fixtures/aret_v1/schema/` avec leurs SHA-256 épinglés — puis peuplée des **vraies
lignes** de la mémoire baseline : dix-sept composants, leurs cinq cent vingt liens de connaissance et
leurs neuf symboles. Si le DDL versionné dérive de l'amont, le test échoue plutôt que de valider VERA
contre un schéma qu'ARET n'a jamais eu.

La mémoire baseline elle-même n'est pas versionnée : onze mégaoctets pour dix-sept lignes serait payer
cher ce qu'une empreinte atteste aussi bien. Ce qui est versionné, c'est le schéma qui les produit et
les lignes elles-mêmes.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import unittest

from vera_mmu.domain_packs.aret.component_reader import read_aret_v1_component_page
from vera_mmu.domain_packs.aret.component_schema_conformance import _EXPECTED_COMPONENT_COLUMNS
from vera_mmu.domain_packs.aret.schema import aret_v1_schema_manifest

from tests.aret_v1_baseline import (
    BASELINE,
    schema_inspection,
    FIXTURES,
    SCHEMA_DIR,
    FTS_MARKER,
    build_source,
    bundle_round_trip,
    import_real_components,
    temporary_root,
)


class AretC03ComponentParityTests(unittest.TestCase):
    # --- la référence elle-même --------------------------------------------

    def test_the_vendored_schema_is_the_pinned_aret_ddl(self) -> None:
        """Sans cela, la parité serait mesurée contre un schéma dont plus personne ne sait l'âge."""
        declared = BASELINE["provenance"]["schema_sha256"]
        actual = {path.name: sha256(path.read_bytes()).hexdigest() for path in sorted(SCHEMA_DIR.glob("*.sql"))}
        self.assertEqual(actual, declared)
        self.assertEqual(len(actual), 6)

    def test_the_vendored_rows_declare_the_memory_they_came_from(self) -> None:
        provenance = BASELINE["provenance"]
        self.assertEqual(provenance["memory_bytes"], 11280384)
        self.assertEqual(
            provenance["memory_sha256"],
            "85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5",
        )
        self.assertEqual(len(BASELINE["components"]), 17)
        self.assertEqual(sum(BASELINE["knowledge_links"].values()), 520)

    # --- ce que VERA déclare du schéma ARET, confronté au schéma ARET -------

    def test_the_declared_table_inventory_matches_the_schema_aret_actually_applies(self) -> None:
        """`aret_v1_schema_manifest()` n'avait jamais été comparé au DDL qu'il prétend décrire."""
        with sqlite3.connect(":memory:") as connection:
            for migration in sorted(SCHEMA_DIR.glob("*.sql")):
                connection.executescript(migration.read_text(encoding="utf-8"))
            applied = tuple(sorted(
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                if FTS_MARKER not in row[0]
            ))
        manifest = aret_v1_schema_manifest()
        self.assertEqual(manifest.application_tables, applied)
        self.assertEqual(list(manifest.migration_versions), BASELINE["schema_migrations"])
        self.assertEqual(len(applied), 18)

    def test_the_declared_component_contract_matches_the_real_column_metadata(self) -> None:
        """Le contrat porte `description TEXT NOT NULL DEFAULT ''` ; le vrai schéma aussi.

        Il était exact par soin d'écriture, jamais par vérification. La différence compte : une
        colonne ajoutée ou un défaut retiré côté ARET passerait aujourd'hui inaperçu.
        """
        observed = tuple(tuple(column) for column in BASELINE["component_columns"])
        expected = tuple(
            (name, kind, notnull, primary, default)
            for name, kind, notnull, primary, default in _EXPECTED_COMPONENT_COLUMNS
        )
        self.assertEqual(observed, expected)

    def test_the_component_table_is_strict_as_aret_declares_it(self) -> None:
        """`STRICT` n'est pas décoratif : il refuse une valeur de type divergent à l'écriture.

        Les fixtures existantes écrivent une table non stricte, donc aucun test n'exerçait cette
        contrainte. Une source réelle refuse ce qu'elles auraient accepté.
        """
        source = SCHEMA_DIR / "001_initial.sql"
        text = source.read_text(encoding="utf-8")
        head = text[text.index("CREATE TABLE IF NOT EXISTS component") :]
        self.assertIn("STRICT", head[: head.index(";")])

    # --- la source réelle, lue par VERA ------------------------------------

    def test_the_real_components_are_read_back_exactly(self) -> None:

        with temporary_root() as directory:
            path = Path(directory) / "aret_memory.sqlite"
            connection = build_source(path)
            try:
                rows = [
                    dict(zip(("id", "title", "description", "created_at", "created_by"), row))
                    for row in connection.execute(
                        "SELECT id, title, description, created_at, created_by FROM component ORDER BY id"
                    )
                ]
            finally:
                connection.close()
        self.assertEqual(rows, BASELINE["components"])
        self.assertEqual([item["id"] for item in rows][:3], ["ABI", "ARCH", "CORE"])

    def test_component_identifiers_are_unique_and_the_real_schema_enforces_it(self) -> None:
        """Unicité : le registre l'exige, et c'est la clé primaire d'ARET qui la tient."""

        identifiers = [item["id"] for item in BASELINE["components"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        with temporary_root() as directory:
            path = Path(directory) / "aret_memory.sqlite"
            connection = build_source(path)
            try:
                first = BASELINE["components"][0]
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "INSERT INTO component(id, title, description, created_at, created_by) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (first["id"], "collision", "", first["created_at"], first["created_by"]),
                    )
            finally:
                connection.close()

    def test_the_knowledge_links_of_the_real_memory_carry_no_orphan(self) -> None:
        """Intégrité référentielle : 520 liens, zéro orphelin, et chaque cible est déclarée.

        Mesuré sur la mémoire réelle, pas supposé : un import qui perdrait un composant lié
        rendrait orphelines les connaissances qui le citent, et c'est le nombre à conserver.
        """
        declared = {item["id"] for item in BASELINE["components"]}
        links = BASELINE["knowledge_links"]
        self.assertEqual(BASELINE["knowledge_orphans"], 0)
        self.assertEqual(sorted(set(links) - declared), [])
        self.assertEqual(sum(links.values()) + BASELINE["knowledge_unlinked"], 532)
        self.assertEqual(sorted(set(BASELINE["function_symbols"]) - declared), [])
        self.assertEqual(sum(BASELINE["function_symbols"].values()), 9)

    def test_veras_own_reader_returns_the_real_components_exactly(self) -> None:
        """La dimension qui compte : ce n'est pas la fixture qu'on éprouve, c'est le lecteur.

        Les fixtures existantes fabriquaient trois composants inventés sur un schéma réécrit. Ici le
        lecteur de VERA parcourt une source bâtie par le DDL d'ARET et peuplée de ses vraies lignes,
        et doit rendre les dix-sept, dans l'ordre, sans en perdre ni en inventer.
        """

        with temporary_root() as directory:
            root = (Path(directory) / "aret-memory").resolve()
            path = root / ".aret-memory" / "aret_memory.sqlite"
            path.parent.mkdir(parents=True)
            build_source(path).close()

            inspection = schema_inspection(path)
            collected: list[str] = []
            cursor: str | None = None
            for _ in range(20):  # borne de sûreté : une pagination qui boucle doit échouer, pas tourner
                page = read_aret_v1_component_page(
                    source_root=root, schema_inspection=inspection, after_id=cursor, limit=5
                )
                collected.extend(record.source_id for record in page.records)
                cursor = page.next_after_id
                if cursor is None:
                    break

        self.assertIsNone(cursor, "la pagination du lecteur ne s’est pas terminée")
        self.assertEqual(collected, [item["id"] for item in BASELINE["components"]])
        self.assertEqual(len(collected), 17)

    def test_the_real_components_import_into_a_vera_store_as_generic_entities(self) -> None:
        """La chaîne d'import entière, pilotée depuis la source réelle.

        Les tests existants fabriquent le préflight, la projection et le contrôle de collision à la
        main, avec un hash de source inventé (`"a" * 64`) et deux composants imaginaires. La chaîne
        n'avait donc jamais été pilotée bout en bout depuis une vraie page lue. Ici elle l'est :
        lecture, préparation, préflight, projection, contrôle de cible, autorisation, import.
        """

        with temporary_root() as directory:
            entities, result = import_real_components(Path(directory))

        self.assertEqual(result.imported_entity_count, 17)
        self.assertEqual(result.import_state, "IMPORTED_NO_PROMOTION")
        expected = [(f"aret-component--{item['id']}", item["title"], item["description"])
                    for item in BASELINE["components"]]
        self.assertEqual([(row[0], row[2], row[3]) for row in entities], expected)
        self.assertEqual({row[1] for row in entities}, {"component"})

    def test_imported_components_survive_abundle_round_trip(self) -> None:
        """Sixième dimension exigée par le registre : export puis import de bundle.

        Une mémoire qui perdrait ses entités importées au passage d'un bundle rendrait l'import
        réversible par accident — et l'identité du projet le garantit, pas l'espoir.
        """

        with temporary_root() as directory:
            root = Path(directory)
            before, _ = import_real_components(root)
            after = bundle_round_trip(root)

        self.assertEqual(len(after), 17)
        self.assertEqual(before, after)

    # --- ce que la promotion de C03 exige en plus ---------------------------

    def test_the_core_knows_no_component_table_and_no_reference_fixture(self) -> None:
        """I015 : aucun concept métier d'un pack n'est requis pour installer le Core."""
        core = Path(__file__).resolve().parents[1] / "src" / "vera_mmu"
        offenders = []
        for path in core.rglob("*.py"):
            if "domain_packs" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if "FROM component" in text or "aret_v1" in text or "domain_packs.aret" in text:
                offenders.append(str(path.relative_to(core)))
        self.assertEqual(sorted(offenders), [], f"Le Core connaît `component` ou ARET : {offenders}")


if __name__ == "__main__":
    unittest.main()
