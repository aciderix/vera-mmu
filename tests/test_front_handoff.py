from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.agent_profiles import builtin_agent_profiles_json


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "front-project"
  name: "Front Project"
  domain: "software"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
  max_resume_bytes: 4096
front:
  fields: [active_goal, current_work, risks]
resume:
  template: engineering
  sections:
    - id: working-rules
      required: true
    - id: current-state
      required: true
"""


class FrontHandoffTests(unittest.TestCase):
    def _store(self, directory: Path, *, write_policy: str = "confirm", schema_dir: Path | None = None) -> MemoryStore:
        runtime = directory / ".vera-mmu"
        runtime.mkdir(exist_ok=True)
        profile_path = runtime / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        (runtime / "capabilities.yaml").write_text("format: vera-capability-catalog/v1\ncapabilities: []\n", encoding="utf-8")
        (runtime / "gates.yaml").write_text("format: vera-gate-catalog/v1\ngates: []\n", encoding="utf-8")
        (runtime / "agent-profiles.yaml").write_text(builtin_agent_profiles_json(), encoding="utf-8")
        (runtime / "policies.yaml").write_text(f"""format: vera-policy-catalog/v1
filesystem: {{read: allow, write: {write_policy}}}
network: {{default: deny}}
process: {{allowed_runners: []}}
git: {{commit: confirm, push: confirm}}
destructive: {{default: confirm}}
promotion: {{proven_requires: [admissible_pass]}}
""", encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path, schema_dir=schema_dir)

    @staticmethod
    def _front() -> dict[str, str]:
        return {
            "active_goal": "Livrer un Front traçable et exactement lié au Project Profile.",
            "current_work": "Vérifier les snapshots append-only, hashes et refus atomiques.",
            "risks": "Aucune hypothèse de réussite ne doit remplacer une preuve persistante.",
        }

    def test_i001_i006_i009_front_is_profile_bound_versioned_and_append_only(self) -> None:
        from vera_mmu.front import FrontError, FrontService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                service = FrontService(store)
                with self.assertRaises(FrontError):
                    service.replace("front-0", self._front(), actor="test")
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM front_revision").fetchone()[0], 0)
                first = service.replace("front-1", self._front(), actor="test", confirm=True)
                self.assertEqual(service.current(), first)
                self.assertEqual(first.profile_hash, store.identity.profile_hash)
                self.assertEqual(len(first.fields_hash), 64)
                second = service.update("front-2", {"current_work": "Préparer le handoff avec le dossier de reprise vérifié."}, actor="test", confirm=True)
                self.assertEqual(second.previous_front_id, "front-1")
                self.assertEqual(second.fields["active_goal"], self._front()["active_goal"])
                self.assertEqual(service.current(), second)
                with self.assertRaises(FrontError):
                    service.replace("front-bad", {"active_goal": "Valeur", "current_work": "Valeur", "foreign": "Interdit"}, actor="test", confirm=True)
                with self.assertRaises(sqlite3.IntegrityError):
                    store.connection.execute("UPDATE front_revision SET fields_json='{}' WHERE id='front-1'")
                with self.assertRaises(sqlite3.IntegrityError):
                    store.connection.execute("DELETE FROM front_revision WHERE id='front-1'")
                self.assertEqual([event["action"] for event in store.audit_events()][-2:], ["FRONT_REPLACED", "FRONT_UPDATED"])

    def test_i006_project_write_policy_is_closed_confirmed_and_atomic(self) -> None:
        from vera_mmu.front import FrontError, FrontService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory), write_policy="deny") as store:
                audits = len(store.audit_events())
                with self.assertRaises(FrontError):
                    FrontService(store).replace("front-denied", self._front(), actor="test", confirm=True)
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM front_revision").fetchone()[0], 0)
                self.assertEqual(len(store.audit_events()), audits)

        with TemporaryDirectory() as directory:
            with self._store(Path(directory), write_policy="allow") as store:
                service = FrontService(store)
                audits = len(store.audit_events())
                with self.assertRaises(FrontError):
                    service.replace("front-unconfirmed", self._front(), actor="test")
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM front_revision").fetchone()[0], 0)
                self.assertEqual(len(store.audit_events()), audits)
                self.assertEqual(service.replace("front-allowed", self._front(), actor="test", confirm=True).id, "front-allowed")

    def test_i001_i009_existing_038_store_upgrades_to_append_only_front_handoff(self) -> None:
        from vera_mmu.front import FrontService
        from vera_mmu.handoff import HandoffService
        from vera_mmu.profile_resume import compile_profile_resume_dossier

        with TemporaryDirectory() as directory:
            project = Path(directory)
            schema = project / "schema"
            schema.mkdir()
            source = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
            for version in range(1, 39):
                migration = next(source.glob(f"{version:03d}_*.sql"))
                copyfile(migration, schema / migration.name)
            with self._store(project, schema_dir=schema) as legacy:
                self.assertEqual(legacy.metadata()["store_format"], {"schema_version": 38})
                identity = legacy.metadata()["project_identity"]
                self.assertEqual(legacy.connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('front_revision', 'handoff')").fetchone()[0], 0)

            migration = next(source.glob("039_*.sql"))
            copyfile(migration, schema / migration.name)
            with self._store(project, schema_dir=schema) as upgraded:
                self.assertEqual(upgraded.metadata()["store_format"], {"schema_version": 39})
                self.assertEqual(upgraded.metadata()["project_identity"], identity)
                front = FrontService(upgraded).replace("front-upgraded", self._front(), actor="test", confirm=True)
                dossier = compile_profile_resume_dossier(upgraded, {"working-rules": "Les décisions de reprise doivent reposer sur des faits, des preuves et un refus explicite en cas d’ambiguïté.", "current-state": "La migration 039 a été appliquée à une mémoire préexistante et le handoff est prêt à être vérifié."})
                HandoffService(upgraded).prepare("handoff-upgraded", dossier, actor="test", confirm=True)
                with self.assertRaises(sqlite3.IntegrityError):
                    upgraded.connection.execute("UPDATE front_revision SET fields_json='{}' WHERE id=?", (front.id,))
                with self.assertRaises(sqlite3.IntegrityError):
                    upgraded.connection.execute("DELETE FROM handoff WHERE id='handoff-upgraded'")
                self.assertIn("STORE_MIGRATED", [event["action"] for event in upgraded.audit_events()])

    def test_i009_i014_handoff_requires_current_front_and_matching_profile_resume(self) -> None:
        from vera_mmu.front import FrontError, FrontService
        from vera_mmu.handoff import HandoffError, HandoffService
        from vera_mmu.profile_resume import compile_profile_resume_dossier

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                front = FrontService(store).replace("front-1", self._front(), actor="test", confirm=True)
                dossier = compile_profile_resume_dossier(store, {"working-rules": "Mesurer les faits et conserver toutes les preuves avant de conclure.", "current-state": "Le Front est persistant, vérifié et prêt pour un handoff traçable."})
                audits = len(store.audit_events())
                with self.assertRaises(HandoffError):
                    HandoffService(store).prepare("handoff-unconfirmed", dossier, actor="test")
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM handoff").fetchone()[0], 0)
                self.assertEqual(len(store.audit_events()), audits)
                handoff = HandoffService(store).prepare("handoff-1", dossier, actor="test", confirm=True)
                self.assertEqual(handoff.front_revision_id, front.id)
                self.assertEqual(handoff.resume_contract_hash, dossier.resume_contract_hash)
                self.assertEqual(HandoffService(store).latest(), handoff)
                tampered = replace(dossier, profile_hash="0" * 64)
                with self.assertRaises(HandoffError):
                    HandoffService(store).prepare("handoff-2", tampered, actor="test", confirm=True)
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM handoff").fetchone()[0], 1)
                self.assertEqual(store.audit_events()[-1]["action"], "HANDOFF_PREPARED")
        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                dossier = compile_profile_resume_dossier(store, {"working-rules": "Mesurer les faits et conserver toutes les preuves avant de conclure.", "current-state": "Aucun Front ne doit permettre de préparer un handoff implicite ici."})
                with self.assertRaises(FrontError):
                    HandoffService(store).prepare("handoff-1", dossier, actor="test", confirm=True)


if __name__ == "__main__":
    unittest.main()
