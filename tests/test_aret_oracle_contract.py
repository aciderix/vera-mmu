from __future__ import annotations

from pathlib import Path
import unittest

from vera_mmu.domain_packs.aret.oracle_contract import (
    ARET_ORACLES,
    AretOracleContractError,
    normalize_oracle_result,
    preflight_oracle,
    resolve_repository_file,
)


class AretOracleContractTests(unittest.TestCase):
    def _repository(self, root: Path) -> Path:
        binary = root / "target" / "release" / "aret"
        binary.parent.mkdir(parents=True)
        binary.write_text("binary", encoding="utf-8")
        for spec in ARET_ORACLES.values():
            if spec.script is not None:
                path = root / spec.script
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        return root

    def test_catalogue_is_closed_and_preserves_historical_limits(self) -> None:
        self.assertEqual(
            tuple(ARET_ORACLES),
            (
                "difftest",
                "transpilediff",
                "stdcall_audit",
                "winediff",
                "winehash",
                "ehdiff",
                "gnuehdiff",
                "funcdiff",
                "cpudiff",
            ),
        )
        self.assertEqual(ARET_ORACLES["difftest"].timeout_seconds, 1800)
        self.assertEqual(ARET_ORACLES["winediff"].timeout_seconds, 3600)
        self.assertTrue(ARET_ORACLES["winediff"].accepts_fixture)
        self.assertFalse(ARET_ORACLES["difftest"].accepts_fixture)
        self.assertTrue(ARET_ORACLES["difftest"].requires_aret_binary)
        self.assertIsNone(ARET_ORACLES["winehash"].command)
        self.assertEqual(
            ARET_ORACLES["cpudiff"].command,
            ("cargo", "test", "--release", "--features", "unpack", "cpudiff"),
        )
        with self.assertRaises(AretOracleContractError):
            preflight_oracle(Path("/missing"), "not-an-oracle", tool_lookup=lambda _: "/bin/true")

    def test_repository_file_refuses_traversal_and_symlink_escape(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            root = Path(directory) / "reference"
            outside = Path(directory) / "outside.sh"
            root.mkdir()
            inside = root / "bench" / "difftest.sh"
            inside.parent.mkdir()
            inside.write_text("ok", encoding="utf-8")
            outside.write_text("outside", encoding="utf-8")

            self.assertEqual(resolve_repository_file(root, "bench/difftest.sh", "script"), inside.resolve())
            with self.assertRaises(AretOracleContractError):
                resolve_repository_file(root, "../outside.sh", "script")

            inside.unlink()
            inside.symlink_to(outside)
            with self.assertRaises(AretOracleContractError):
                resolve_repository_file(root, "bench/difftest.sh", "script")

    def test_preflight_is_observational_and_reports_exact_missing_dependencies(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            root = Path(directory) / "reference"
            self._repository(root)
            result = preflight_oracle(root, "difftest", tool_lookup=lambda name: "/bin/true" if name == "bash" else None)
            self.assertEqual(result.oracle_name, "difftest")
            self.assertEqual(result.missing_dependencies, ("gcc",))
            self.assertEqual(result.status, "SKIPPED")
            self.assertEqual(result.script_path, (root / "bench" / "difftest.sh").resolve())
            self.assertEqual(result.aret_binary, (root / "target" / "release" / "aret").resolve())

    def test_normalizer_is_fail_closed_and_never_masks_failure_as_skip(self) -> None:
        self.assertEqual(
            normalize_oracle_result("difftest", 0, "differential equivalence: 2/2 functions", "", (), False),
            "PASS",
        )
        self.assertEqual(
            normalize_oracle_result("winediff", 1, "SKIP GUI\nOS-API (Wine) equivalence: 255/264 programs", "", (), False),
            "FAIL",
        )
        self.assertEqual(
            normalize_oracle_result("funcdiff", None, "", "", ("cargo",), False),
            "SKIPPED",
        )
        self.assertEqual(
            normalize_oracle_result("ehdiff", None, "", "timeout", (), True),
            "ERROR",
        )
        self.assertEqual(
            normalize_oracle_result("winehash", 0, "user32 OK " + "a" * 64, "", (), False),
            "UNKNOWN",
        )
        self.assertEqual(
            normalize_oracle_result("stdcall_audit", 0, "unexpected output", "", (), False),
            "ERROR",
        )


if __name__ == "__main__":
    unittest.main()
