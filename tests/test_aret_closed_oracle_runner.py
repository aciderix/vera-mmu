from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

from vera_mmu.assets import AssetService
from vera_mmu.domain_packs.aret.closed_oracle_runner import (
    ARET_TOOLKIT_REFERENCE_COMMIT,
    AretClosedOracleError,
    OracleProcessResult,
    declare_aret_oracle_capability,
    run_closed_oracle,
)
from vera_mmu.evidence import EvidenceService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "aret-oracle-runner-project"
  name: "ARET Oracle Runner Project"
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
'''


@dataclass(frozen=True)
class CapturedCall:
    command: tuple[str, ...]
    cwd: Path
    environment: dict[str, str]
    timeout_seconds: int


class AretClosedOracleRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"
        runtime.mkdir()
        self.profile_path = runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def _repository(self, root: Path) -> Path:
        binary = root / "target" / "release" / "aret"
        binary.parent.mkdir(parents=True)
        binary.write_text("aret", encoding="utf-8")
        for script in (
            "bench/difftest.sh",
            "bench/winediff.sh",
            "bench/winoracle/wine_hashes.sh",
        ):
            path = root / script
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        return root

    def test_declares_one_immutable_generic_capability_per_closed_oracle(self) -> None:
        with self._open() as store:
            declared = declare_aret_oracle_capability(store, "difftest", actor="test-suite")
            self.assertEqual(declared.capability.id, "aret-oracle-difftest")
            self.assertEqual(declared.contract.runner_profile, "OBSERVED_PROCESS")
            self.assertEqual(declared.contract.network_policy, "DENY_NETWORK")
            self.assertEqual(declared.contract.timeout_seconds, 1800)
            self.assertFalse(declared.contract.yields_proof)
            self.assertEqual(declared.policy.decision, "ALLOW")
            self.assertEqual(declared.capability.metadata["oracle"], "difftest")

    def test_runs_only_closed_script_in_network_sandbox_and_records_pending_evidence(self) -> None:
        with self._open() as store:
            declared = declare_aret_oracle_capability(store, "difftest", actor="test-suite")
            root = self._repository(Path(self._directory.name) / "reference")
            captured: list[CapturedCall] = []

            def fake_runner(command: tuple[str, ...], cwd: Path, environment: dict[str, str], timeout_seconds: int) -> OracleProcessResult:
                captured.append(CapturedCall(command, cwd, environment, timeout_seconds))
                return OracleProcessResult(exit_code=0, stdout="differential equivalence: 2/2 functions", stderr="", timed_out=False)

            outcome = run_closed_oracle(
                store,
                root,
                "difftest",
                execution_id="oracle-run-001",
                evidence_id="oracle-evidence-001",
                actor="test-suite",
                command_runner=fake_runner,
                revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                clean_checker=lambda _: True,
                tool_lookup=lambda _: "/bin/true",
            )

            self.assertEqual(outcome.verdict, "PASS")
            self.assertEqual(outcome.execution.capability_id, declared.capability.id)
            self.assertEqual(outcome.evidence.verdict, "PASS")
            self.assertEqual(outcome.evidence.admission_status, "PENDING")
            self.assertIn(b"differential equivalence: 2/2 functions", AssetService(store).read(outcome.asset_id))
            self.assertEqual(len(captured), 1)
            self.assertEqual(captured[0].command[:4], ("unshare", "--user", "--map-root-user", "--net"))
            self.assertEqual(captured[0].command[-2:], ("bash", str((root / "bench" / "difftest.sh").resolve())))
            self.assertEqual(captured[0].cwd, root.resolve())
            self.assertEqual(captured[0].environment["ARET"], str((root / "target" / "release" / "aret").resolve()))
            self.assertEqual(captured[0].environment["LC_ALL"], "C")
            self.assertEqual(captured[0].environment["TZ"], "UTC")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0], 0)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge_proof").fetchone()[0], 0)
            self.assertEqual(EvidenceService(store).get("oracle-evidence-001"), outcome.evidence)

    def test_attested_external_binary_unblocks_clean_reference_checkout(self) -> None:
        with self._open() as store:
            declare_aret_oracle_capability(store, "difftest", actor="test-suite")
            root = self._repository(Path(self._directory.name) / "reference")
            (root / "target" / "release" / "aret").unlink()
            external_binary = Path(self._directory.name) / "build" / "aret"
            external_binary.parent.mkdir()
            external_binary.write_bytes(b"attested external binary")
            captured: list[CapturedCall] = []

            def fake_runner(command: tuple[str, ...], cwd: Path, environment: dict[str, str], timeout_seconds: int) -> OracleProcessResult:
                captured.append(CapturedCall(command, cwd, environment, timeout_seconds))
                return OracleProcessResult(exit_code=0, stdout="differential equivalence: 1/1 functions", stderr="", timed_out=False)

            with patch(
                "vera_mmu.domain_packs.aret.closed_oracle_runner.ARET_TOOLKIT_BINARY_SHA256",
                sha256(external_binary.read_bytes()).hexdigest(),
            ):
                outcome = run_closed_oracle(
                    store,
                    root,
                    "difftest",
                    execution_id="oracle-run-external-binary",
                    evidence_id="oracle-evidence-external-binary",
                    actor="test-suite",
                    aret_binary=external_binary,
                    command_runner=fake_runner,
                    revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                    clean_checker=lambda _: True,
                    tool_lookup=lambda _: "/bin/true",
                )
            self.assertEqual(outcome.verdict, "PASS")
            self.assertEqual(captured[0].environment["ARET"], str(external_binary.resolve()))

    def test_nonzero_exit_with_skip_text_stays_fail_and_never_runs_external_path(self) -> None:
        with self._open() as store:
            declare_aret_oracle_capability(store, "winediff", actor="test-suite")
            root = self._repository(Path(self._directory.name) / "reference")

            def fake_runner(command: tuple[str, ...], cwd: Path, environment: dict[str, str], timeout_seconds: int) -> OracleProcessResult:
                return OracleProcessResult(
                    exit_code=1,
                    stdout="SKIP GUI\nOS-API (Wine) equivalence: 255/264 programs",
                    stderr="",
                    timed_out=False,
                )

            outcome = run_closed_oracle(
                store,
                root,
                "winediff",
                execution_id="oracle-run-002",
                evidence_id="oracle-evidence-002",
                actor="test-suite",
                fixture="user32_paint",
                command_runner=fake_runner,
                revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                clean_checker=lambda _: True,
                tool_lookup=lambda _: "/bin/true",
            )
            self.assertEqual(outcome.verdict, "FAIL")
            self.assertEqual(outcome.evidence.verdict, "FAIL")
            self.assertEqual(outcome.evidence.admission_status, "PENDING")

            with self.assertRaises(AretClosedOracleError):
                run_closed_oracle(
                    store,
                    root,
                    "difftest",
                    execution_id="oracle-run-003",
                    evidence_id="oracle-evidence-003",
                    actor="test-suite",
                    fixture="not-accepted",
                    command_runner=fake_runner,
                    revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                    clean_checker=lambda _: True,
                    tool_lookup=lambda _: "/bin/true",
                )

    def test_refuses_revision_drift_and_script_symlink_escape_without_execution(self) -> None:
        with self._open() as store:
            declare_aret_oracle_capability(store, "difftest", actor="test-suite")
            root = self._repository(Path(self._directory.name) / "reference")
            calls = 0

            def fake_runner(command: tuple[str, ...], cwd: Path, environment: dict[str, str], timeout_seconds: int) -> OracleProcessResult:
                nonlocal calls
                calls += 1
                return OracleProcessResult(exit_code=0, stdout="differential equivalence: 1/1 functions", stderr="", timed_out=False)

            with self.assertRaises(AretClosedOracleError):
                run_closed_oracle(
                    store,
                    root,
                    "difftest",
                    execution_id="oracle-run-004",
                    evidence_id="oracle-evidence-004",
                    actor="test-suite",
                    command_runner=fake_runner,
                    revision_reader=lambda _: "0" * 40,
                    clean_checker=lambda _: True,
                    tool_lookup=lambda _: "/bin/true",
                )
            self.assertEqual(calls, 0)

            outside = Path(self._directory.name) / "outside.sh"
            outside.write_text("outside", encoding="utf-8")
            script = root / "bench" / "difftest.sh"
            script.unlink()
            script.symlink_to(outside)
            with self.assertRaises(AretClosedOracleError):
                run_closed_oracle(
                    store,
                    root,
                    "difftest",
                    execution_id="oracle-run-005",
                    evidence_id="oracle-evidence-005",
                    actor="test-suite",
                    command_runner=fake_runner,
                    revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                    clean_checker=lambda _: True,
                    tool_lookup=lambda _: "/bin/true",
                )
            self.assertEqual(calls, 0)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
