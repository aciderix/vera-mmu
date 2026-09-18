"""Cover the transport-neutral VERA write facade.

Invariants exercised here: I003 (knowledge stays append-only), I004 (`PROVEN` is never
reachable through an append), I008 (no client input becomes an arbitrary command) and
I013 (a controlled write receives an explicit policy decision).
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.agent_profiles import builtin_agent_profiles_json
from vera_mmu.front import FrontService
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeAdmissionError, KnowledgeService
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteApiError, WriteService, declaration_to_store_type_id


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "write-project"
  name: "Write Project"
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


class WriteApiTests(unittest.TestCase):
    def _store(self, directory: Path, *, write_policy: str = "allow") -> MemoryStore:
        runtime = directory / ".vera-mmu"
        runtime.mkdir(exist_ok=True)
        profile_path = runtime / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        (runtime / "capabilities.yaml").write_text("format: vera-capability-catalog/v1\ncapabilities: []\n", encoding="utf-8")
        (runtime / "gates.yaml").write_text("format: vera-gate-catalog/v1\ngates: []\n", encoding="utf-8")
        (runtime / "agent-profiles.yaml").write_text(builtin_agent_profiles_json(), encoding="utf-8")
        (runtime / "policies.yaml").write_text(
            "format: vera-policy-catalog/v1\n"
            f"filesystem: {{read: allow, write: {write_policy}}}\n"
            "network: {default: deny}\n"
            "process: {allowed_runners: []}\n"
            "git: {commit: confirm, push: confirm}\n"
            "destructive: {default: confirm}\n"
            "promotion: {proven_requires: [admissible_pass, technical_validation]}\n",
            encoding="utf-8",
        )
        return MemoryStore.open(load_profile(profile_path), profile_path)

    def _register(self, store: MemoryStore) -> None:
        KnowledgeService(store).register_type("observation", "Observation", actor="test")

    # --- knowledge -------------------------------------------------------

    def test_append_knowledge_persists_and_returns_address(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self._register(store)
                record = WriteService(store).append_knowledge(
                    "kn-1", type_id="observation", status="OBSERVED", title="Titre", content="Contenu", actor="test",
                )
                self.assertEqual(record["id"], "kn-1")
                self.assertEqual(record["status"], "OBSERVED")
                self.assertEqual(record["address"], "vera://write-project/knowledge/kn-1")
                self.assertEqual(KnowledgeService(store).get("kn-1").title, "Titre")

    def test_append_knowledge_refuses_proven_status(self) -> None:
        """I004: promotion is never a side effect of an append."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self._register(store)
                with self.assertRaises(KnowledgeAdmissionError):
                    WriteService(store).append_knowledge(
                        "kn-proven", type_id="observation", status="PROVEN", title="T", content="C", actor="test",
                    )

    def test_append_knowledge_refuses_unknown_type(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                with self.assertRaises(Exception):
                    WriteService(store).append_knowledge(
                        "kn-x", type_id="not-registered", status="OBSERVED", title="T", content="C", actor="test",
                    )

    def test_append_knowledge_refuses_duplicate_identifier(self) -> None:
        """I003: an append never rewrites an existing record."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self._register(store)
                service = WriteService(store)
                service.append_knowledge("kn-dup", type_id="observation", status="OBSERVED", title="T", content="C", actor="test")
                with self.assertRaises(Exception):
                    service.append_knowledge("kn-dup", type_id="observation", status="OBSERVED", title="Autre", content="Autre", actor="test")

    # --- front -----------------------------------------------------------

    def test_replace_then_update_front(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                service = WriteService(store)
                first = service.replace_front(
                    "front-1", {"active_goal": "But", "current_work": "Travail", "risks": "Aucun"}, actor="test", confirm=True,
                )
                self.assertEqual(first["id"], "front-1")
                self.assertEqual(first["address"], "vera://write-project/front/front-1")
                second = service.update_front("front-2", {"risks": "Elevé"}, actor="test", confirm=True)
                self.assertEqual(second["fields"]["risks"], "Elevé")
                self.assertEqual(second["fields"]["active_goal"], "But")
                self.assertEqual(FrontService(store).current().id, "front-2")

    def test_front_write_refused_without_confirmation(self) -> None:
        """I013: a controlled write is refused rather than silently applied."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp), write_policy="confirm") as store:
                with self.assertRaises(Exception):
                    WriteService(store).replace_front(
                        "front-nc", {"active_goal": "A", "current_work": "B", "risks": "C"}, actor="test", confirm=False,
                    )

    def test_update_front_refused_without_current_snapshot(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                with self.assertRaises(Exception):
                    WriteService(store).update_front("front-none", {"risks": "X"}, actor="test", confirm=True)

    def test_front_refuses_undeclared_field(self) -> None:
        """I008: the client cannot widen the Front contract declared by the profile."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                with self.assertRaises(Exception):
                    WriteService(store).replace_front(
                        "front-bad",
                        {"active_goal": "A", "current_work": "B", "risks": "C", "injected": "D"},
                        actor="test",
                        confirm=True,
                    )

    # --- handoff ---------------------------------------------------------

    def test_prepare_handoff_compiles_dossier_from_profile(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                service = WriteService(store)
                service.replace_front(
                    "front-h", {"active_goal": "But", "current_work": "Travail", "risks": "Aucun"}, actor="test", confirm=True,
                )
                record = service.prepare_handoff(
                    "handoff-1", {"working-rules": "Regles de travail VERA", "current-state": "Etat courant du projet"}, actor="test", confirm=True,
                )
                self.assertEqual(record["id"], "handoff-1")
                self.assertEqual(record["front_revision_id"], "front-h")
                self.assertEqual(len(record["resume_contract_hash"]), 64)

    def test_prepare_handoff_refused_without_front(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                with self.assertRaises(Exception):
                    WriteService(store).prepare_handoff(
                        "handoff-nf", {"working-rules": "R", "current-state": "E"}, actor="test", confirm=True,
                    )

    def test_prepare_handoff_refuses_missing_required_section(self) -> None:
        """I009: the resume contract cannot be satisfied by fabricating absent context."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                service = WriteService(store)
                service.replace_front(
                    "front-s", {"active_goal": "But", "current_work": "Travail", "risks": "Aucun"}, actor="test", confirm=True,
                )
                with self.assertRaises(Exception):
                    service.prepare_handoff("handoff-ms", {"working-rules": "Regles de travail VERA"}, actor="test", confirm=True)

    # --- profile-declared knowledge types --------------------------------

    def test_declaration_maps_to_canonical_store_type(self) -> None:
        self.assertEqual(declaration_to_store_type_id("RULE"), "rule")
        self.assertEqual(declaration_to_store_type_id("PLAYER_STATE"), "player-state")
        with self.assertRaises(WriteApiError):
            declaration_to_store_type_id("not-a-declaration")

    def test_sync_registers_exactly_the_declared_types(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                registered = WriteService(store).sync_profile_knowledge_types(actor="test")
                self.assertEqual(registered, ["architecture", "decision", "discovery", "hypothesis", "measurement", "observation", "rule", "state"])
                label = store.connection.execute("SELECT label FROM knowledge_type WHERE id = ?", ("rule",)).fetchone()[0]
                self.assertEqual(label, "RULE")

    def test_sync_is_idempotent(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                service = WriteService(store)
                first = service.sync_profile_knowledge_types(actor="test")
                second = service.sync_profile_knowledge_types(actor="test")
                self.assertEqual(first, second)

    def test_append_accepts_declared_type_after_sync(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                service = WriteService(store)
                service.sync_profile_knowledge_types(actor="test")
                record = service.append_knowledge(
                    "kn-decl", type_id="OBSERVATION", status="OBSERVED", title="Titre", content="Contenu", actor="test",
                )
                self.assertEqual(record["type_id"], "observation")

    def test_append_refuses_type_absent_from_profile(self) -> None:
        """I007/I015: the profile catalog is closed; a client cannot invent a type."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                service = WriteService(store)
                service.sync_profile_knowledge_types(actor="test")
                with self.assertRaises(WriteApiError):
                    service.append_knowledge(
                        "kn-undeclared", type_id="SMUGGLED", status="OBSERVED", title="T", content="C", actor="test",
                    )

    # --- guards ----------------------------------------------------------

    def test_service_refuses_invalid_store(self) -> None:
        with self.assertRaises(WriteApiError):
            WriteService(object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
