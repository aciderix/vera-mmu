from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from vera_mmu.domain_packs.aret.oracle_contract import ARET_ORACLES
from vera_mmu.domain_packs.aret.toolchain_doctor import (
    ARET_TOOLKIT_REFERENCE_COMMIT,
    AretToolchainDoctorError,
    inspect_aret_toolchain,
)


class AretToolchainDoctorTests(unittest.TestCase):
    def _repository(self, root: Path) -> Path:
        for spec in ARET_ORACLES.values():
            if spec.script is not None:
                path = root / spec.script
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        (root / "src").mkdir(exist_ok=True)
        (root / "src" / "cpudiff.rs").write_text("// fixture\n", encoding="utf-8")
        return root

    def test_ready_report_is_deterministic_and_observational(self) -> None:
        with TemporaryDirectory() as directory:
            root = self._repository(Path(directory) / "reference")
            binary = Path(directory) / "build" / "aret"
            binary.parent.mkdir()
            binary.write_bytes(b"attested binary")
            with patch(
                "vera_mmu.domain_packs.aret.toolchain_doctor.ARET_TOOLKIT_BINARY_SHA256",
                sha256(binary.read_bytes()).hexdigest(),
            ):
                report = inspect_aret_toolchain(
                    root,
                    aret_binary=binary,
                    tool_lookup=lambda _: "/bin/true",
                    revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                    clean_checker=lambda _: True,
                )
            self.assertEqual(report.status, "READY")
            self.assertEqual(report.reference_commit, ARET_TOOLKIT_REFERENCE_COMMIT)
            self.assertTrue(report.reference_clean)
            self.assertEqual(report.binary.status, "PASS")
            self.assertEqual(tuple(check.oracle_name for check in report.oracles), tuple(ARET_ORACLES))
            self.assertTrue(all(check.status == "READY" for check in report.oracles))
            self.assertEqual(report.install_actions, ())

    def test_missing_tool_is_reported_as_degraded_without_installation(self) -> None:
        with TemporaryDirectory() as directory:
            root = self._repository(Path(directory) / "reference")
            binary = Path(directory) / "build" / "aret"
            binary.parent.mkdir()
            binary.write_bytes(b"attested binary")
            with patch(
                "vera_mmu.domain_packs.aret.toolchain_doctor.ARET_TOOLKIT_BINARY_SHA256",
                sha256(binary.read_bytes()).hexdigest(),
            ):
                report = inspect_aret_toolchain(
                    root,
                    aret_binary=binary,
                    tool_lookup=lambda name: None if name == "cargo" else "/bin/true",
                    revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                    clean_checker=lambda _: True,
                )
            self.assertEqual(report.status, "DEGRADED")
            cpudiff = next(check for check in report.oracles if check.oracle_name == "cpudiff")
            self.assertEqual(cpudiff.status, "SKIPPED")
            self.assertEqual(cpudiff.missing_dependencies, ("cargo",))
            self.assertEqual(report.install_actions, ())

    def test_missing_network_sandbox_degrades_report(self) -> None:
        with TemporaryDirectory() as directory:
            root = self._repository(Path(directory) / "reference")
            binary = Path(directory) / "build" / "aret"
            binary.parent.mkdir()
            binary.write_bytes(b"attested binary")
            with patch(
                "vera_mmu.domain_packs.aret.toolchain_doctor.ARET_TOOLKIT_BINARY_SHA256",
                sha256(binary.read_bytes()).hexdigest(),
            ):
                report = inspect_aret_toolchain(
                    root,
                    aret_binary=binary,
                    tool_lookup=lambda name: None if name == "unshare" else "/bin/true",
                    revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                    clean_checker=lambda _: True,
                )
            self.assertEqual(report.status, "DEGRADED")
            self.assertEqual(report.network_sandbox_status, "MISSING")
            self.assertTrue(all(check.status == "READY" for check in report.oracles))

    def test_reference_or_binary_mismatch_is_error_not_ready(self) -> None:
        with TemporaryDirectory() as directory:
            root = self._repository(Path(directory) / "reference")
            binary = Path(directory) / "build" / "aret"
            binary.parent.mkdir()
            binary.write_bytes(b"unattested binary")
            report = inspect_aret_toolchain(
                root,
                aret_binary=binary,
                tool_lookup=lambda _: "/bin/true",
                revision_reader=lambda _: "0" * 40,
                clean_checker=lambda _: False,
            )
            self.assertEqual(report.status, "ERROR")
            self.assertEqual(report.reference_status, "ERROR")
            self.assertEqual(report.binary.status, "ERROR")
            self.assertEqual(report.install_actions, ())
            with self.assertRaises(AretToolchainDoctorError):
                inspect_aret_toolchain(
                    Path(directory) / "missing",
                    aret_binary=binary,
                    tool_lookup=lambda _: "/bin/true",
                    revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                    clean_checker=lambda _: True,
                )


if __name__ == "__main__":
    unittest.main()
