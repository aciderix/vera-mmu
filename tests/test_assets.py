from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.assets import AssetError, AssetNotFoundError, AssetService, MAX_ASSET_BYTES
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "asset-project"
  name: "Asset Project"
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


class AssetServiceTests(unittest.TestCase):
    """I001/I002/I004/I005/I011/I014/I015: assets are immutable and hash-verified before byte reads."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.runtime = Path(self._directory.name) / "project" / ".vera-mmu"
        self.runtime.mkdir(parents=True)
        self.profile_path = self.runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _profile(self) -> dict[str, object]:
        return load_profile(self.profile_path)

    def _open(self) -> MemoryStore:
        return MemoryStore.open(self._profile(), self.profile_path)

    def test_default_migrations_include_asset_registry(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 17})

    def test_existing_m2_6_store_migrates_to_asset_registry(self) -> None:
        schema = Path(self._directory.name) / "m2_6_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in (
            "001_core_store.sql",
            "002_entity_registry.sql",
            "003_relation_registry.sql",
            "004_knowledge_registry.sql",
            "005_knowledge_sources.sql",
            "006_knowledge_supersession.sql",
        ):
            shutil.copyfile(source_dir / version, schema / version)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as m2_6_store:
            self.assertEqual(m2_6_store.metadata()["store_format"], {"schema_version": 6})
        shutil.copyfile(source_dir / "007_asset_registry.sql", schema / "007_asset_registry.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 7})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )

    def test_record_metadata_and_hash_verified_byte_read(self) -> None:
        content = b"immutable asset bytes\x00\xff"
        with self._open() as store:
            assets = AssetService(store)
            recorded = assets.record("asset-001", content, media_type="application/octet-stream", actor="test-suite")
            self.assertEqual(assets.get("asset-001"), recorded)
            self.assertEqual(assets.read("asset-001"), content)
            self.assertEqual(recorded.address, "vera://asset-project/asset/asset-001")
            self.assertEqual(recorded.content_hash, sha256(content).hexdigest())
            self.assertEqual(recorded.byte_length, len(content))
            self.assertEqual(store.audit_events()[-1]["action"], "ASSET_RECORDED")

    def test_rejects_invalid_inputs_unknown_and_duplicate_content(self) -> None:
        with self._open() as store:
            assets = AssetService(store)
            with self.assertRaises(AssetError):
                assets.record("../escape", b"asset", media_type="application/octet-stream")
            with self.assertRaises(AssetError):
                assets.record("asset-empty", b"", media_type="application/octet-stream")
            with self.assertRaises(AssetError):
                assets.record("asset-type", b"asset", media_type="Text/Plain")
            with self.assertRaises(AssetError):
                assets.record("asset-large", b"x" * (MAX_ASSET_BYTES + 1), media_type="application/octet-stream")
            recorded = assets.record("asset-001", b"asset", media_type="text/plain")
            with self.assertRaises(AssetError):
                assets.record("asset-001", b"different", media_type="text/plain")
            with self.assertRaises(AssetError):
                assets.record("asset-002", b"asset", media_type="text/plain")
            self.assertEqual(assets.get("asset-001"), recorded)
            with self.assertRaises(AssetNotFoundError):
                assets.get("asset-missing")
            with self.assertRaises(AssetNotFoundError):
                assets.read("asset-missing")

    def test_byte_read_rejects_stored_hash_or_length_inconsistency(self) -> None:
        with self._open() as store:
            assets = AssetService(store)
            store.connection.execute(
                "INSERT INTO asset(id, content_hash, byte_length, media_type, content, created_at, created_by) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                (
                    "asset-tampered",
                    sha256(b"expected").hexdigest(),
                    len(b"tampered"),
                    "application/octet-stream",
                    b"tampered",
                    "2026-01-01T00:00:00Z",
                    "test-suite",
                ),
            )
            with self.assertRaises(AssetError):
                assets.read("asset-tampered")

    def test_database_rejects_asset_rewrites_and_deletes(self) -> None:
        with self._open() as store:
            assets = AssetService(store)
            assets.record("asset-001", b"asset", media_type="text/plain")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("UPDATE asset SET media_type = 'application/json' WHERE id = 'asset-001'")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("DELETE FROM asset WHERE id = 'asset-001'")
            self.assertEqual(assets.read("asset-001"), b"asset")

    def test_asset_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            assets = AssetService(store)
            store.connection.execute(
                "CREATE TRIGGER reject_asset_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'ASSET_RECORDED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(AssetError):
                assets.record("asset-001", b"asset", media_type="text/plain")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM asset").fetchone()[0], 0)
            self.assertNotIn("ASSET_RECORDED", [event["action"] for event in store.audit_events()])


if __name__ == "__main__":
    unittest.main()
