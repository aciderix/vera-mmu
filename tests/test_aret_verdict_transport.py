from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.admission import AdmissionError, AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.domain_packs.aret.closed_oracle_runner import (
    ARET_TOOLKIT_REFERENCE_COMMIT,
    OracleProcessResult,
    declare_aret_oracle_capability,
    run_closed_oracle,
)
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "aret-verdict-transport"
  name: "ARET Verdict Transport"
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


class AretVerdictTransportTests(unittest.TestCase):
    def _reference(self, root: Path) -> Path:
        binary = root / "target" / "release" / "aret"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"aret fixture")
        for relative_path in ("bench/difftest.sh", "bench/winoracle/wine_hashes.sh"):
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        return root

    def _store(self, directory: Path) -> MemoryStore:
        runtime = directory / ".vera-mmu"
        runtime.mkdir()
        profile_path = runtime / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    def _run(
        self,
        store: MemoryStore,
        reference: Path,
        identifier: str,
        oracle_name: str,
        process: OracleProcessResult,
        *,
        tool_lookup=lambda _: "/bin/true",
    ):
        declare_aret_oracle_capability(store, oracle_name, actor="test")
        return run_closed_oracle(
            store,
            reference,
            oracle_name,
            execution_id=f"execution-{identifier}",
            evidence_id=f"evidence-{identifier}",
            actor="test",
            command_runner=lambda *_: process,
            revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
            clean_checker=lambda _: True,
            tool_lookup=tool_lookup,
        )

    def _validate_then_admit(self, store: MemoryStore, identifier: str, expected_verdict: str) -> None:
        validator = ValidatorService(store)
        validator.register("asset-binding", "EVIDENCE_ASSET")
        validation = validator.validate(
            f"validation-{identifier}", "asset-binding", f"evidence-{identifier}"
        )
        self.assertEqual(validation.verdict, "PASS")
        AdmissionPolicyService(store).declare("VALIDATED_PASS_EVIDENCE")
        if expected_verdict == "PASS":
            admission = AdmissionService(store).decide(
                f"admission-{identifier}",
                f"evidence-{identifier}",
                "ADMITTED",
                "contractual pass may be admitted",
                validation_id=validation.id,
            )
            self.assertEqual(admission.decision, "ADMITTED")
        else:
            with self.assertRaises(AdmissionError):
                AdmissionService(store).decide(
                    f"admission-{identifier}",
                    f"evidence-{identifier}",
                    "ADMITTED",
                    "non-pass must never be admitted",
                    validation_id=validation.id,
                )

    def test_difftest_payloads_have_semantic_verdicts_independent_of_local_execution(self) -> None:
        scenarios = (
            ("full", OracleProcessResult(0, "differential equivalence: 272/272 functions", "", False), "PASS"),
            ("partial", OracleProcessResult(0, "differential equivalence: 271/272 functions", "", False), "FAIL"),
            ("timeout", OracleProcessResult(None, "", "timeout", True), "ERROR"),
            ("unrecognized", OracleProcessResult(0, "unparseable payload", "", False), "ERROR"),
        )
        with TemporaryDirectory() as directory:
            for identifier, process, expected in scenarios:
                with self.subTest(identifier=identifier):
                    case_dir = Path(directory) / identifier
                    case_dir.mkdir()
                    reference = self._reference(case_dir / "reference")
                    with self._store(case_dir) as store:
                        outcome = self._run(store, reference, identifier, "difftest", process)
                        self.assertEqual(outcome.verdict, expected)
                        self.assertEqual(outcome.evidence.verdict, expected)
                        self._validate_then_admit(store, identifier, expected)

    def test_missing_dependency_and_nonpromotable_hash_payload_stay_non_admissible(self) -> None:
        with TemporaryDirectory() as directory:
            case_dir = Path(directory) / "skipped"
            case_dir.mkdir()
            reference = self._reference(case_dir / "reference")
            with self._store(case_dir) as store:
                skipped = self._run(
                    store,
                    reference,
                    "skipped",
                    "difftest",
                    OracleProcessResult(None, "", "", False),
                    tool_lookup=lambda name: None if name == "gcc" else "/bin/true",
                )
                self.assertEqual(skipped.verdict, "SKIPPED")
                self._validate_then_admit(store, "skipped", "SKIPPED")

            unknown_dir = Path(directory) / "unknown"
            unknown_dir.mkdir()
            reference = self._reference(unknown_dir / "reference")
            with self._store(unknown_dir) as store:
                unknown = self._run(
                    store,
                    reference,
                    "unknown",
                    "winehash",
                    OracleProcessResult(0, "fixture OK " + "a" * 64, "", False),
                )
                self.assertEqual(unknown.verdict, "UNKNOWN")
                self._validate_then_admit(store, "unknown", "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
