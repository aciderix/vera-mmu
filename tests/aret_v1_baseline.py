"""Aides partagées par les tests de parité ARET : bâtir une source réelle et l'importer.

Ce module n'est pas un test. Il existe pour que `C03`, `C04` et les couplages suivants partagent une
**seule** façon de fabriquer une source ARET V1 — en exécutant le DDL réel puis en la peuplant des
vraies lignes de la baseline. Dupliquer cette construction serait rouvrir le défaut que `C03` a
fermé : une fixture écrite d'après le contrat qu'elle sert à valider ne peut pas le réfuter, et deux
fixtures divergentes seraient pires qu'une.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tempfile

from vera_mmu.bundles import BundleService, project_bundle_path, restore_bundle
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore
from vera_mmu.domain_packs.aret.component_authorized_import import (
    authorize_aret_v1_component_import,
    import_authorized_aret_v1_component_entities,
)
from vera_mmu.domain_packs.aret.component_entity_projection import project_aret_v1_component_entities
from vera_mmu.domain_packs.aret.component_import_preflight import component_import_preflight
from vera_mmu.domain_packs.aret.component_reader import read_aret_v1_component_page
from vera_mmu.domain_packs.aret.component_target_collision import check_aret_v1_component_target_clear
from vera_mmu.domain_packs.aret.import_preparation import component_import_preparation
from vera_mmu.domain_packs.aret.schema import aret_v1_schema_manifest
from vera_mmu.domain_packs.aret.sqlite_schema import AretV1SchemaSnapshotInspection


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "aret_v1"
SCHEMA_DIR = FIXTURES / "schema"
BASELINE = json.loads((FIXTURES / "baseline_components.json").read_text(encoding="utf-8"))


def build_source(path: Path, *, with_symbols: bool = False) -> sqlite3.Connection:
    """Bâtir une source ARET V1 en exécutant son propre DDL, jamais un `CREATE TABLE` réécrit.

    C'est ce qui distingue une fixture d'une référence : le schéma vient d'ARET, pas de l'idée que
    VERA s'en fait. Les symboles sont optionnels parce que leur clé étrangère exige les composants.
    """
    connection = sqlite3.connect(path)
    for migration in sorted(SCHEMA_DIR.glob("*.sql")):
        connection.executescript(migration.read_text(encoding="utf-8"))
    connection.executemany(
        "INSERT INTO component(id, title, description, created_at, created_by) VALUES (?, ?, ?, ?, ?)",
        [
            (item["id"], item["title"], item["description"], item["created_at"], item["created_by"])
            for item in BASELINE["components"]
        ],
    )
    if with_symbols:
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
    return connection


def schema_inspection(database: Path) -> AretV1SchemaSnapshotInspection:
    """L'inspection que tout lecteur du pack exige, dérivée du fichier réellement bâti."""
    manifest = aret_v1_schema_manifest()
    return AretV1SchemaSnapshotInspection(
        source_path=database,
        source_snapshot_sha256=sha256(database.read_bytes()).hexdigest(),
        migration_versions=manifest.migration_versions,
        application_tables=manifest.application_tables,
    )


BUNDLE_ID = "aret-parity-bundle"
PROJECT_ID = "aret-parity"


@contextmanager
def temporary_root() -> Iterator[Path]:
    """Un répertoire temporaire dont le chemin est **canonique**, ce que les lecteurs exigent.

    Les lecteurs ARET refusent une racine non canonique, et ils ont raison : un chemin qui a deux
    écritures est ambigu, et c'est justement ce qu'un import ne doit pas avaler. Mais les tests
    leur remettaient le chemin brut de `TemporaryDirectory`, qui n'est canonique que par accident.

    Mesuré au run #50 : sur Windows ce chemin porte un nom court 8.3 — `C:\\Users\\RUNNER~1\\…` —
    et `resolve()` ne l'étend que pour un chemin **existant**, faute de poignée à ouvrir. Une
    racine résolue avant la création de ses répertoires restait donc non canonique, et onze tests
    de parité tombaient sur le refus. Résoudre le répertoire lui-même, qui existe, tranche sur
    toutes les plateformes ; sous Linux c'est un non-événement.
    """
    with tempfile.TemporaryDirectory() as directory:
        yield Path(directory).resolve(strict=True)


def source_root(root: Path, *, with_symbols: bool = False) -> Path:
    """Matérialiser une source ARET V1 complète sous une racine, prête pour le lecteur."""
    source = root / "aret-memory"
    database = source / ".aret-memory" / "aret_memory.sqlite"
    database.parent.mkdir(parents=True)
    # Résoudre **après** la création : voir `temporary_root`, un chemin inexistant ne se canonise
    # pas sur Windows. La racine rendue ici doit franchir le garde du lecteur.
    source = source.resolve(strict=True)
    build_source(source / ".aret-memory" / "aret_memory.sqlite", with_symbols=with_symbols).close()
    return source


def project(root: Path, name: str) -> Path:
    """Un projet VERA complet : le bundle exige un catalogue de policies, pas un profil minimal."""
    target = root / name
    target.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        target, template="software", project_id=PROJECT_ID, project_name="ARET parity"
    )
    apply_project_initialization(target, preview, confirm=True)
    return target / ".vera-mmu" / "project.yaml"


def entities(store: MemoryStore) -> list[tuple[str, str, str, str]]:
    return [tuple(row) for row in store.connection.execute(
        "SELECT id, type_id, title, description FROM entity ORDER BY id"
    )]


def import_real_components(root: Path):
    """Piloter la chaîne d'import entière depuis la source réelle, et rendre ce qu'elle a écrit."""
    source = source_root(root)
    database = source / ".aret-memory" / "aret_memory.sqlite"
    profile_path = project(root, "project")
    manifest = aret_v1_schema_manifest()
    inspection = AretV1SchemaSnapshotInspection(
        source_path=database,
        source_snapshot_sha256=sha256(database.read_bytes()).hexdigest(),
        migration_versions=manifest.migration_versions,
        application_tables=manifest.application_tables,
    )
    with MemoryStore.open(load_profile(profile_path), profile_path) as store:
        page = read_aret_v1_component_page(
            source_root=source, schema_inspection=inspection, after_id=None, limit=100
        )
        preparation = component_import_preparation(
            target_identity=store.identity,
            source_snapshot_sha256=inspection.source_snapshot_sha256,
            request_id="aret-parity-request",
            requested_by="parity",
        )
        preflight = component_import_preflight(
            preparation=preparation,
            schema_inspection=inspection,
            source_page=page,
            preflight_id="aret-parity-page",
            confirmed_by="parity",
        )
        projection = project_aret_v1_component_entities(preflight=preflight, source_page=page)
        clear = check_aret_v1_component_target_clear(projection=projection, target_store=store)
        authorization = authorize_aret_v1_component_import(
            preflight=preflight,
            projection=projection,
            target_clear_check=clear,
            authorization_id="aret-parity-auth",
            authorized_by="parity",
        )
        result = import_authorized_aret_v1_component_entities(
            authorization=authorization,
            preflight=preflight,
            projection=projection,
            target_clear_check=clear,
            target_store=store,
        )
        return entities(store), result


def bundle_round_trip(root: Path) -> list[tuple[str, str, str, str]]:
    """Exporter la mémoire importée, la restaurer ailleurs, et rendre ce qui a survécu."""
    profile_path = root / "project" / ".vera-mmu" / "project.yaml"
    with MemoryStore.open(load_profile(profile_path), profile_path) as store:
        BundleService(store).export(BUNDLE_ID, confirm=True)
        bundle_path = project_bundle_path(store, BUNDLE_ID)
    restored_profile = project(root, "restored")
    restore_bundle(bundle_path, restored_profile, confirm=True)
    with MemoryStore.open(load_profile(restored_profile), restored_profile) as store:
        return entities(store)

FTS_MARKER = "_fts"


def insert_real_bricks(database: Path) -> None:
    """Ajouter les treize briques réelles à une source dont les composants existent déjà."""
    connection = sqlite3.connect(database)
    try:
        connection.executemany(
            "INSERT INTO brick(id, component_id, title, state, description, created_at, created_by, "
            "milestone, target_platform, priority) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row["id"], row["component_id"], row["title"], row["state"], row["description"],
                    row["created_at"], row["created_by"], row["milestone"], row["target_platform"],
                    row["priority"],
                )
                for row in BASELINE["brick_rows"]
            ],
        )
        connection.commit()
    finally:
        connection.close()


def import_real_bricks(store: MemoryStore, database: Path, source: Path):
    """Piloter la chaîne d'import structurel des treize briques depuis la source réelle."""
    from vera_mmu.domain_packs.aret.authorized_structural_import import (
        import_authorized_aret_v1_structural_page,
    )
    from vera_mmu.domain_packs.aret.brick_projection import project_aret_v1_brick_page
    from vera_mmu.domain_packs.aret.brick_reader import read_aret_v1_brick_page
    from vera_mmu.domain_packs.aret.structural_import_authorization import (
        authorize_aret_v1_structural_import,
    )
    from vera_mmu.domain_packs.aret.structural_import_preflight import structural_import_preflight
    from vera_mmu.domain_packs.aret.structural_import_preparation import structural_import_preparation
    from vera_mmu.domain_packs.aret.structural_schema_conformance import inspect_aret_v1_brick_schema
    from vera_mmu.domain_packs.aret.structural_target_collision import (
        check_aret_v1_structural_target_clear,
    )

    inspection = schema_inspection(database)
    conformance = inspect_aret_v1_brick_schema(inspection=inspection)
    page = read_aret_v1_brick_page(
        source_root=source, schema_inspection=inspection, after_id=None, limit=100
    )
    projection = project_aret_v1_brick_page(
        target_identity=store.identity, source_page=page, request_id="aret-brick-request"
    )
    preparation = structural_import_preparation(
        target_identity=store.identity,
        source_snapshot_sha256=inspection.source_snapshot_sha256,
        request_id="aret-brick-request",
        requested_by="parity",
        legacy_table="brick",
    )
    preflight = structural_import_preflight(
        preparation=preparation,
        schema_inspection=inspection,
        schema_conformance=conformance,
        source_page=page,
        preflight_id="aret-brick-page",
        confirmed_by="parity",
    )
    clear = check_aret_v1_structural_target_clear(
        preflight=preflight, projection=projection, target_store=store
    )
    authorization = authorize_aret_v1_structural_import(
        preflight=preflight,
        projection=projection,
        clear_check=clear,
        target_store=store,
        authorization_id="aret-brick-auth",
        authorized_by="parity",
    )
    return import_authorized_aret_v1_structural_page(
        preflight=preflight, projection=projection, authorization=authorization, target_store=store
    )


def work_items(store: MemoryStore) -> list[tuple[str, str, str, int]]:
    return [tuple(row) for row in store.connection.execute(
        "SELECT id, type, title, priority FROM work_item ORDER BY id"
    )]


def import_real_symbols(root: Path, store: MemoryStore, database: Path, source: Path):
    """Piloter la chaîne d'import structurel des neuf symboles depuis la source réelle.

    Les symboles portent une clé étrangère vers `component` : les composants doivent donc avoir été
    importés d'abord, sinon la projection désignerait des entités propriétaires inexistantes.
    """
    from vera_mmu.domain_packs.aret.authorized_structural_import import (
        import_authorized_aret_v1_structural_page,
    )
    from vera_mmu.domain_packs.aret.function_symbol_projection import (
        project_aret_v1_function_symbol_page,
    )
    from vera_mmu.domain_packs.aret.function_symbol_reader import read_aret_v1_function_symbol_page
    from vera_mmu.domain_packs.aret.structural_import_authorization import (
        authorize_aret_v1_structural_import,
    )
    from vera_mmu.domain_packs.aret.structural_import_preflight import structural_import_preflight
    from vera_mmu.domain_packs.aret.structural_import_preparation import structural_import_preparation
    from vera_mmu.domain_packs.aret.structural_schema_conformance import (
        inspect_aret_v1_function_symbol_schema,
    )
    from vera_mmu.domain_packs.aret.structural_target_collision import (
        check_aret_v1_structural_target_clear,
    )

    inspection = schema_inspection(database)
    conformance = inspect_aret_v1_function_symbol_schema(inspection=inspection)
    page = read_aret_v1_function_symbol_page(
        source_root=source, schema_inspection=inspection, after_id=None, limit=100
    )
    projection = project_aret_v1_function_symbol_page(
        target_identity=store.identity, source_page=page, request_id="aret-symbol-request"
    )
    preparation = structural_import_preparation(
        target_identity=store.identity,
        source_snapshot_sha256=inspection.source_snapshot_sha256,
        request_id="aret-symbol-request",
        requested_by="parity",
        legacy_table="function_symbol",
    )
    preflight = structural_import_preflight(
        preparation=preparation,
        schema_inspection=inspection,
        schema_conformance=conformance,
        source_page=page,
        preflight_id="aret-symbol-page",
        confirmed_by="parity",
    )
    clear = check_aret_v1_structural_target_clear(
        preflight=preflight, projection=projection, target_store=store
    )
    authorization = authorize_aret_v1_structural_import(
        preflight=preflight,
        projection=projection,
        clear_check=clear,
        target_store=store,
        authorization_id="aret-symbol-auth",
        authorized_by="parity",
    )
    return preflight, projection, authorization, import_authorized_aret_v1_structural_page


def symbols(store: MemoryStore) -> list[tuple[str, str, str, str, str]]:
    return [tuple(row) for row in store.connection.execute(
        "SELECT id, entity_id, kind, path, identifier FROM symbol ORDER BY id"
    )]
