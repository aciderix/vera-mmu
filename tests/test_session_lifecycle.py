from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "lifecycle-project"
  name: "Lifecycle Project"
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


class SessionLifecycleTests(unittest.TestCase):
    def _store(self, directory: Path) -> MemoryStore:
        profile_path = directory / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    @staticmethod
    def _requirements() -> tuple[object, ...]:
        from vera_mmu.session_lifecycle import ResumeSectionRequirement

        return (
            ResumeSectionRequirement("working-rules", 12, 256),
            ResumeSectionRequirement("current-state", 12, 256),
            ResumeSectionRequirement("next-action", 12, 256),
        )

    @staticmethod
    def _sections(*, suffix: str = "") -> dict[str, str]:
        return {
            "working-rules": f"Mesurer, comparer et prouver avant toute conclusion.{suffix}",
            "current-state": f"Le prochain lot est borné et le baseline reste identifié.{suffix}",
            "next-action": f"Écrire les tests ciblés puis valider les frontières de sécurité.{suffix}",
        }

    def _dossier(self, store: MemoryStore, *, suffix: str = "") -> object:
        from vera_mmu.session_lifecycle import ResumeDossierService

        return ResumeDossierService(store).compile(self._requirements(), self._sections(suffix=suffix))

    def test_i011_i012_compiles_project_bound_dossier_stably(self) -> None:
        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                first = self._dossier(store)
                second = self._dossier(store)
                self.assertEqual(first, second)
                self.assertEqual(first.project_id, "lifecycle-project")
                self.assertEqual(first.profile_hash, store.identity.profile_hash)
                self.assertEqual(len(first.resume_contract_hash), 64)
                self.assertNotIn("ARET", first.json_text)
                self.assertNotIn("command", first.json_text)

    def test_i014_refuses_unknown_or_incomplete_dossier_sections(self) -> None:
        from vera_mmu.session_lifecycle import LifecycleError, ResumeDossierService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                service = ResumeDossierService(store)
                incomplete = self._sections()
                incomplete.pop("next-action")
                with self.assertRaises(LifecycleError):
                    service.compile(self._requirements(), incomplete)
                unknown = self._sections()
                unknown["pack-specific"] = "Ce champ ne doit pas entrer dans le contrat Core."
                with self.assertRaises(LifecycleError):
                    service.compile(self._requirements(), unknown)

    def test_i011_i012_refuses_tampered_dossier_before_state_write(self) -> None:
        from vera_mmu.session_lifecycle import LifecycleError, ResumeGuardService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                dossier = self._dossier(store)
                tampered = replace(dossier, resume_contract_hash="0" * 64)
                guard = ResumeGuardService(store)
                with self.assertRaises(LifecycleError):
                    guard.arm("session-1", "test-host-v1", "SESSION_OPEN", tampered, mode="HARD")
                self.assertFalse(guard.state_path("session-1", "test-host-v1").exists())

    def test_i009_i011_hard_guard_blocks_until_matching_observed_acknowledgement(self) -> None:
        from vera_mmu.session_lifecycle import GuardDecision, ResumeGuardService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                dossier = self._dossier(store)
                guard = ResumeGuardService(store)
                armed = guard.arm("session-1", "test-host-v1", "SESSION_OPEN", dossier, mode="HARD")
                self.assertEqual(armed.status, "ARMED")
                denied = guard.precheck("session-1", "test-host-v1")
                self.assertEqual(denied.decision, GuardDecision.DENY)
                self.assertIn("acknowledgement", denied.reason)
                self.assertFalse(guard.acknowledge("session-1", "test-host-v1", "f" * 64, self._sections()))
                self.assertFalse(guard.acknowledge("session-1", "other-host-v1", dossier.resume_contract_hash, self._sections()))
                too_short = self._sections()
                too_short["next-action"] = "court"
                self.assertFalse(guard.acknowledge("session-1", "test-host-v1", dossier.resume_contract_hash, too_short))
                self.assertTrue(guard.acknowledge("session-1", "test-host-v1", dossier.resume_contract_hash, self._sections()))
                self.assertEqual(guard.precheck("session-1", "test-host-v1").decision, GuardDecision.ALLOW)
                actions = [event["action"] for event in store.audit_events()]
                self.assertIn("RESUME_GUARD_ARMED", actions)
                self.assertIn("RESUME_GUARD_ACKNOWLEDGED", actions)

    def test_i009_resume_preserves_live_ack_but_context_restored_rearms(self) -> None:
        from vera_mmu.session_lifecycle import GuardDecision, ResumeGuardService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                first = self._dossier(store)
                guard = ResumeGuardService(store)
                guard.arm("session-1", "test-host-v1", "SESSION_OPEN", first, mode="HARD")
                self.assertTrue(guard.acknowledge("session-1", "test-host-v1", first.resume_contract_hash, self._sections()))
                preserved = guard.arm("session-1", "test-host-v1", "RESUME", self._dossier(store, suffix=" refreshed"), mode="HARD")
                self.assertEqual(preserved.status, "ACKNOWLEDGED")
                self.assertEqual(guard.precheck("session-1", "test-host-v1").decision, GuardDecision.ALLOW)
                rearmed = guard.arm("session-1", "test-host-v1", "CONTEXT_RESTORED", self._dossier(store, suffix=" compacted"), mode="HARD")
                self.assertEqual(rearmed.status, "ARMED")
                self.assertEqual(guard.precheck("session-1", "test-host-v1").decision, GuardDecision.DENY)

    def test_i014_soft_guard_is_loud_but_never_deadlocks(self) -> None:
        from vera_mmu.session_lifecycle import GuardDecision, ResumeGuardService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                guard = ResumeGuardService(store)
                guard.arm("session-1", "test-host-v1", "SESSION_OPEN", self._dossier(store), mode="SOFT")
                precheck = guard.precheck("session-1", "test-host-v1")
                self.assertEqual(precheck.decision, GuardDecision.ALLOW_WITH_NOTICE)
                self.assertIn("degraded", precheck.reason)
                nudge = guard.session_ending("session-1", "test-host-v1", already_nudged=False)
                self.assertEqual(nudge.decision, GuardDecision.NUDGE)
                self.assertEqual(guard.session_ending("session-1", "test-host-v1", already_nudged=True).decision, GuardDecision.ALLOW)

    def test_i011_sessions_and_adapters_are_isolated(self) -> None:
        from vera_mmu.session_lifecycle import GuardDecision, ResumeGuardService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                guard = ResumeGuardService(store)
                dossier = self._dossier(store)
                guard.arm("session-a", "test-host-v1", "SESSION_OPEN", dossier, mode="HARD")
                self.assertEqual(guard.precheck("session-a", "test-host-v1").decision, GuardDecision.DENY)
                self.assertEqual(guard.precheck("session-b", "test-host-v1").decision, GuardDecision.ALLOW)
                self.assertEqual(guard.precheck("session-a", "other-host-v1").decision, GuardDecision.ALLOW)

    def test_i014_missing_session_or_corrupt_state_fails_closed_in_hard_mode(self) -> None:
        from vera_mmu.session_lifecycle import GuardDecision, ResumeGuardService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                guard = ResumeGuardService(store)
                dossier = self._dossier(store)
                guard.arm("session-1", "test-host-v1", "SESSION_OPEN", dossier, mode="HARD")
                self.assertEqual(guard.precheck("", "test-host-v1").decision, GuardDecision.DENY)
                path = guard.state_path("session-1", "test-host-v1")
                path.write_text("not-json", encoding="utf-8")
                refusal = guard.precheck("session-1", "test-host-v1")
                self.assertEqual(refusal.decision, GuardDecision.DENY)
                self.assertIn("integrity", refusal.reason)

    def test_i014_refuses_symlinked_state_target_without_following_it(self) -> None:
        from vera_mmu.session_lifecycle import LifecycleError, ResumeGuardService

        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self._store(root) as store:
                guard = ResumeGuardService(store)
                dossier = self._dossier(store)
                target = root / "outside.json"
                target.write_text("unchanged", encoding="utf-8")
                path = guard.state_path("session-1", "test-host-v1")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(target)
                with self.assertRaises(LifecycleError):
                    guard.arm("session-1", "test-host-v1", "SESSION_OPEN", dossier, mode="HARD")
                self.assertEqual(target.read_text(encoding="utf-8"), "unchanged")


if __name__ == "__main__":
    unittest.main()
