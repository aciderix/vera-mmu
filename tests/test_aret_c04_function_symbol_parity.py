"""Test de parité du couplage `C04` — `function_symbol` ARET V1 contre `symbol` générique VERA.

Le registre exige, pour promouvoir `C04` : « import exact, unicité configurable, relations vers
entité, lecteur V1, rollback de migration de données ».

**L'unicité est la dimension qui a mordu.** ARET garantit `UNIQUE(component_id, module, symbol)`.
La projection fabriquait son identifiant en joignant les trois par `-`, or `-` est admis *dans* les
composantes : trois familles de triplets distincts produisaient donc le même identifiant VERA, et la
garantie d'ARET ne franchissait pas la frontière. Le défaut était latent — aucune des neuf lignes
réelles ne le déclenche — mais `module` vaut `''` par défaut **dans le schéma ARET lui-même**, ce qui
rend la deuxième famille tout sauf théorique.

Les trois familles sont épinglées ici, et la projection échappe désormais le séparateur. Sur le
corpus réel les identifiants sont inchangés : la correction ne déplace que les cas ambigus.

Comme en `C03`, la source est bâtie en exécutant **le DDL réel d'ARET** puis peuplée des vraies
lignes — dix-sept composants et leurs neuf symboles — plutôt qu'avec un schéma réécrit à la main.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import unittest

from vera_mmu.domain_packs.aret.function_symbol_projection import (
    _ESCAPED_SEPARATOR,
    _SAFE,
    _SEPARATOR,
    AretFunctionSymbolProjectionError,
    project_aret_v1_function_symbol_page,
)
from vera_mmu.domain_packs.aret.function_symbol_reader import (
    AretV1FunctionSymbolSourcePage,
    AretV1FunctionSymbolSourceRecord,
    read_aret_v1_function_symbol_page,
)
from vera_mmu.domain_packs.aret.schema import aret_v1_schema_manifest
from vera_mmu.domain_packs.aret.sqlite_schema import AretV1SchemaSnapshotInspection
from vera_mmu.identity import ProjectIdentity, load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.symbols import SymbolService

from vera_mmu.domain_packs.aret.authorized_structural_import import (
    AretAuthorizedStructuralImportError,
)

from tests.aret_v1_baseline import (
    import_real_components,
    import_real_symbols,
    symbols as stored_symbols,
    temporary_root,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "aret_v1"
SCHEMA_DIR = FIXTURES / "schema"
BASELINE = json.loads((FIXTURES / "baseline_components.json").read_text(encoding="utf-8"))

IDENTITY = ProjectIdentity(
    project_id="c04-parity",
    profile_version="2.0",
    profile_hash="a" * 64,
    workspace_hash="b" * 64,
    project_hash="c" * 64,
)

#: Trois couples de triplets distincts qu'ARET admet simultanément — la contrainte `UNIQUE` porte sur
#: le triplet, pas sur sa concaténation — et qui se confondaient dans l'ancien identifiant.
COLLISION_PAIRS = (
    ("séparateur dans le module puis dans le symbole", ("EH", "a-b", "c"), ("EH", "a", "b-c")),
    ("module vide contre module nommé `root`", ("EH", "", "x"), ("EH", "root", "x")),
    ("séparateur dans le composant puis dans le module", ("A-B", "m", "s"), ("A", "B-m", "s")),
)


def _build_source(path: Path) -> None:
    """Bâtir la source avec le DDL réel d'ARET, composants compris : la clé étrangère l'exige."""
    connection = sqlite3.connect(path)
    try:
        for migration in sorted(SCHEMA_DIR.glob("*.sql")):
            connection.executescript(migration.read_text(encoding="utf-8"))
        connection.executemany(
            "INSERT INTO component(id, title, description, created_at, created_by) VALUES (?, ?, ?, ?, ?)",
            [
                (item["id"], item["title"], item["description"], item["created_at"], item["created_by"])
                for item in BASELINE["components"]
            ],
        )
        connection.executemany(
            "INSERT INTO function_symbol(id, component_id, module, symbol, calling_convention, "
            "created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    item["id"], item["component_id"], item["module"], item["symbol"],
                    item["calling_convention"], item["created_at"], item["created_by"],
                )
                for item in BASELINE["function_symbol_rows"]
            ],
        )
        connection.commit()
    finally:
        connection.close()


def _insert_real_symbols(database: Path) -> None:
    """Ajouter les neuf symboles réels à une source dont les composants existent déjà."""
    connection = sqlite3.connect(database)
    try:
        connection.executemany(
            "INSERT INTO function_symbol(id, component_id, module, symbol, calling_convention, "
            "created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["id"], row["component_id"], row["module"], row["symbol"],
                    row["calling_convention"], row["created_at"], row["created_by"],
                )
                for row in BASELINE["function_symbol_rows"]
            ],
        )
        connection.commit()
    finally:
        connection.close()


def _project(triples: tuple[tuple[str, str, str], ...]) -> list[str]:
    """Projeter des triplets bruts et rendre les identifiants produits."""
    records = tuple(
        AretV1FunctionSymbolSourceRecord(
            source_id=f"{component}:{module}!{symbol}",
            component_id=component,
            module=module,
            symbol=symbol,
            calling_convention="cdecl",
            created_at="2026-01-01T00:00:00Z",
            created_by="parity",
        )
        for component, module, symbol in triples
    )
    page = AretV1FunctionSymbolSourcePage(
        source_path=Path("/nonexistent"),
        source_snapshot_sha256="d" * 64,
        records=records,
        next_after_id=None,
    )
    projection = project_aret_v1_function_symbol_page(
        target_identity=IDENTITY, source_page=page, request_id="c04-parity"
    )
    return [draft.target_identifier for draft in projection.drafts]


class AretC04FunctionSymbolParityTests(unittest.TestCase):
    # --- ce que VERA déclare du schéma, confronté au schéma ------------------

    def test_the_declared_columns_match_the_real_function_symbol_table(self) -> None:
        """Sept colonnes, deux défauts `''`, une clé primaire — mesurées, pas supposées."""
        observed = [tuple(column) for column in BASELINE["function_symbol_columns"]]
        self.assertEqual(
            observed,
            [
                ("id", "TEXT", True, True, None),
                ("component_id", "TEXT", True, False, None),
                ("module", "TEXT", True, False, "''"),
                ("symbol", "TEXT", True, False, None),
                ("calling_convention", "TEXT", True, False, "''"),
                ("created_at", "TEXT", True, False, None),
                ("created_by", "TEXT", True, False, None),
            ],
        )

    def test_the_real_schema_declares_the_triple_unique_and_the_parent_foreign_key(self) -> None:
        """Les deux contraintes que la projection doit transporter, lues dans le DDL d'ARET."""
        text = (SCHEMA_DIR / "001_initial.sql").read_text(encoding="utf-8")
        body = text[text.index("CREATE TABLE IF NOT EXISTS function_symbol") :]
        body = body[: body.index(";")]
        self.assertIn("UNIQUE(component_id, module, symbol)", body)
        self.assertIn("REFERENCES component(id)", body)
        self.assertIn("STRICT", body)

    # --- unicité : la dimension qui a mordu ---------------------------------

    def test_distinct_aret_triples_never_share_a_vera_identifier(self) -> None:
        """L'unicité d'ARET doit franchir la frontière, pas s'arrêter à elle.

        Chaque couple ci-dessous est admis simultanément par `UNIQUE(component_id, module, symbol)`,
        et produisait pourtant un identifiant unique côté VERA. L'import aurait alors soit échoué sur
        une collision, soit écrasé une ligne par l'autre.
        """
        for label, left, right in COLLISION_PAIRS:
            with self.subTest(label):
                identifiers = _project((left, right))
                self.assertEqual(len(set(identifiers)), 2, f"{label} : {identifiers}")

    def test_the_identifier_stays_decodable_into_its_three_parts(self) -> None:
        """L'injectivité se démontre : le séparateur est absent des composantes échappées."""
        for _, left, right in COLLISION_PAIRS:
            for triple in (left, right):
                identifier = _project((triple,))[0]
                parts = identifier[len("aret-symbol--") :].split("-")
                self.assertEqual(len(parts), 3, identifier)
                decoded = tuple(part.replace(_ESCAPED_SEPARATOR, _SEPARATOR) for part in parts)
                self.assertEqual(decoded, triple)

    def test_the_escape_marker_can_never_appear_in_a_source_component(self) -> None:
        """L'injectivité repose sur une dépendance qu'il faut rendre visible.

        Le séparateur est échappé en `%2D`, et le marqueur `%` n'est pas lui-même échappé parce que
        `_SAFE` l'interdit dans une composante. Élargir `_SAFE` à `%` rouvrirait la collision sans
        qu'aucune autre règle ne bronche : ce test est la porte de cette serrure.
        """
        self.assertTrue(_ESCAPED_SEPARATOR.startswith("%"))
        for value in ("%", "a%b", "%2D", "a%2Db"):
            self.assertFalse(_SAFE.fullmatch(value), f"`_SAFE` admet `{value}`")
        self.assertFalse(_SAFE.fullmatch(""), "une composante vide ne doit pas être `_SAFE`")

    def test_the_real_corpus_identifiers_are_unchanged_by_the_escape(self) -> None:
        """Une correction d'unicité ne doit pas renommer ce qui n'était pas ambigu."""
        for row in BASELINE["function_symbol_rows"]:
            identifier = _project(((row["component_id"], row["module"], row["symbol"]),))[0]
            self.assertEqual(
                identifier,
                f"aret-symbol--{row['component_id']}-{row['module']}-{row['symbol']}",
            )
            self.assertNotIn("%", identifier)

    # --- lecteur V1, import exact et relations vers entité -------------------

    def test_veras_reader_returns_the_nine_real_symbols_exactly(self) -> None:
        with temporary_root() as directory:
            root = (Path(directory) / "aret-memory").resolve()
            path = root / ".aret-memory" / "aret_memory.sqlite"
            path.parent.mkdir(parents=True)
            _build_source(path)

            manifest = aret_v1_schema_manifest()
            inspection = AretV1SchemaSnapshotInspection(
                source_path=path,
                source_snapshot_sha256=sha256(path.read_bytes()).hexdigest(),
                migration_versions=manifest.migration_versions,
                application_tables=manifest.application_tables,
            )
            collected: list[AretV1FunctionSymbolSourceRecord] = []
            cursor: str | None = None
            for _ in range(20):
                page = read_aret_v1_function_symbol_page(
                    source_root=root, schema_inspection=inspection, after_id=cursor, limit=4
                )
                collected.extend(page.records)
                cursor = page.next_after_id
                if cursor is None:
                    break

        self.assertIsNone(cursor, "la pagination du lecteur ne s’est pas terminée")
        self.assertEqual(
            [
                {
                    "id": record.source_id,
                    "component_id": record.component_id,
                    "module": record.module,
                    "symbol": record.symbol,
                    "calling_convention": record.calling_convention,
                    "created_at": record.created_at,
                    "created_by": record.created_by,
                }
                for record in collected
            ],
            BASELINE["function_symbol_rows"],
        )
        self.assertEqual(len(collected), 9)

    def test_every_projected_symbol_points_at_a_declared_component_entity(self) -> None:
        """« Relations vers entité » : le parent projeté doit exister comme entité importable."""
        declared = {f"aret-component--{item['id']}" for item in BASELINE["components"]}
        rows = BASELINE["function_symbol_rows"]
        page = AretV1FunctionSymbolSourcePage(
            source_path=Path("/nonexistent"),
            source_snapshot_sha256="d" * 64,
            records=tuple(
                AretV1FunctionSymbolSourceRecord(
                    source_id=row["id"],
                    component_id=row["component_id"],
                    module=row["module"],
                    symbol=row["symbol"],
                    calling_convention=row["calling_convention"],
                    created_at=row["created_at"],
                    created_by=row["created_by"],
                )
                for row in rows
            ),
            next_after_id=None,
        )
        projection = project_aret_v1_function_symbol_page(
            target_identity=IDENTITY, source_page=page, request_id="c04-parity"
        )
        self.assertEqual(len(projection.drafts), 9)
        self.assertEqual({draft.owner_entity_id for draft in projection.drafts} - declared, set())
        self.assertEqual({draft.kind for draft in projection.drafts}, {"FUNCTION"})
        for draft, row in zip(projection.drafts, rows):
            self.assertEqual(draft.path, row["module"])
            self.assertEqual(draft.identifier, row["symbol"])
            self.assertEqual(draft.metadata["source"]["calling_convention"], row["calling_convention"])

    # --- import exact et rollback, contre un vrai store ---------------------

    def test_the_nine_real_symbols_import_exactly_after_their_components(self) -> None:
        """« Import exact » : la chaîne structurelle entière, pilotée depuis la source réelle.

        Les symboles portent une clé étrangère vers `component`, donc les dix-sept composants sont
        importés d'abord : un symbole dont l'entité propriétaire n'existe pas n'est pas un import
        partiel, c'est un import faux.
        """
        with temporary_root() as directory:
            root = Path(directory)
            entities, _ = import_real_components(root)
            self.assertEqual(len(entities), 17)
            source = root / "aret-memory"
            database = source / ".aret-memory" / "aret_memory.sqlite"
            _insert_real_symbols(database)
            profile_path = root / "project" / ".vera-mmu" / "project.yaml"
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                preflight, projection, authorization, write = import_real_symbols(
                    root, store, database, source
                )
                result = write(
                    preflight=preflight,
                    projection=projection,
                    authorization=authorization,
                    target_store=store,
                )
                rows = stored_symbols(store)

        self.assertEqual(len(result.resources), 9)
        self.assertEqual(len(rows), 9)
        expected = [
            (
                f"aret-symbol--{row['component_id']}-{row['module']}-{row['symbol']}",
                f"aret-component--{row['component_id']}",
                "FUNCTION",
                row["module"],
                row["symbol"],
            )
            for row in BASELINE["function_symbol_rows"]
        ]
        self.assertEqual(rows, expected)

    def test_a_collision_appearing_after_authorization_rolls_the_whole_page_back(self) -> None:
        """« Rollback de migration de données » : une page s'écrit entière, ou pas du tout.

        La collision est introduite **après** l'autorisation, ce qu'aucun contrôle préalable ne peut
        voir. Neuf symboles moins un écrit d'avance ne doivent pas donner huit lignes de plus : une
        migration à moitié faite est pire qu'une migration refusée, parce qu'elle a l'air d'avoir
        réussi.
        """
        with temporary_root() as directory:
            root = Path(directory)
            import_real_components(root)
            source = root / "aret-memory"
            database = source / ".aret-memory" / "aret_memory.sqlite"
            _insert_real_symbols(database)
            profile_path = root / "project" / ".vera-mmu" / "project.yaml"
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                preflight, projection, authorization, write = import_real_symbols(
                    root, store, database, source
                )
                intruder = projection.drafts[0]
                SymbolService(store).create(
                    intruder.target_identifier,
                    intruder.owner_entity_id,
                    intruder.kind,
                    intruder.path,
                    intruder.identifier,
                    actor="race",
                )
                before = stored_symbols(store)
                with self.assertRaises(AretAuthorizedStructuralImportError):
                    write(
                        preflight=preflight,
                        projection=projection,
                        authorization=authorization,
                        target_store=store,
                    )
                after = stored_symbols(store)

        self.assertEqual(len(before), 1)
        self.assertEqual(after, before, "la page s’est écrite partiellement")

    def test_a_row_that_cannot_be_mapped_deterministically_is_refused(self) -> None:
        """I014 : une ligne non projetable échoue bruyamment au lieu d'être approximée."""
        for triple in (("EH", "m", "a b"), ("EH", "m", "a/b"), ("", "m", "s")):
            with self.subTest(triple):
                with self.assertRaises(AretFunctionSymbolProjectionError):
                    _project((triple,))


if __name__ == "__main__":
    unittest.main()
