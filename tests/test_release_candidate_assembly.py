"""M9-B — contrat de l’assemblage final de candidat, sans publication."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("assemble_release_candidate", ROOT / "scripts" / "assemble_release_candidate.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Assembleur M9-B introuvable.")
assembly = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = assembly
SPEC.loader.exec_module(assembly)


class ReleaseCandidateAssemblyTests(unittest.TestCase):
    def test_format_and_targets_are_closed(self) -> None:
        self.assertEqual(assembly.FORMAT, "vera-release-candidate/v1")
        with self.assertRaises(assembly.ReleaseCandidateError):
            assembly._desktop_outputs("aarch64-unknown-linux-gnu")

    def test_desktop_outputs_refuse_missing_or_partial_bundles(self) -> None:
        with TemporaryDirectory() as directory, patch.object(assembly, "ROOT", Path(directory)):
            with self.assertRaises(assembly.ReleaseCandidateError):
                assembly._desktop_outputs("x86_64-unknown-linux-gnu")

    def test_final_checksum_refuses_to_hash_itself(self) -> None:
        with TemporaryDirectory() as directory:
            checksum = Path(directory) / "SHA256SUMS"
            checksum.write_text("ignored", encoding="utf-8")
            with self.assertRaises(assembly.ReleaseCandidateError):
                assembly._checksum_lines((checksum,))

    def test_cli_manifest_is_renamed_to_prevent_collision_with_final_manifest(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sources = assembly._candidate_sources(root / "vmmu.tar.gz", root / "release-manifest.json", (root / "desktop.AppImage", root / "desktop.deb"))
            self.assertEqual([name for _, name in sources], ["vmmu.tar.gz", "cli-release-manifest.json", "desktop.AppImage", "desktop.deb"])

    def test_desktop_outputs_ignore_a_previous_version(self) -> None:
        with TemporaryDirectory() as directory, patch.object(assembly, "ROOT", Path(directory)):
            bundle = Path(directory) / "apps" / "desktop" / "src-tauri" / "target" / "release" / "bundle"
            (bundle / "appimage").mkdir(parents=True)
            (bundle / "deb").mkdir()
            (bundle / "appimage" / "VERA-MMU_0.1.0-4_amd64.AppImage").write_bytes(b"current")
            (bundle / "deb" / "VERA-MMU_0.1.0-4_amd64.deb").write_bytes(b"current")
            (bundle / "deb" / "VERA-MMU_0.1.0_amd64.deb").write_bytes(b"obsolete")
            outputs = assembly._desktop_outputs("x86_64-unknown-linux-gnu", "0.1.0-4")
            self.assertEqual([path.name for path in outputs], ["VERA-MMU_0.1.0-4_amd64.AppImage", "VERA-MMU_0.1.0-4_amd64.deb"])


if __name__ == "__main__":
    unittest.main()
