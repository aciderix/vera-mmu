"""M9 — contrat statique du builder CLI natif et de son manifest."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_cli_bundle", ROOT / "scripts" / "build_cli_bundle.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Builder CLI M9 introuvable.")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class CliBundleBuilderTests(unittest.TestCase):
    def test_release_versions_are_aligned_across_all_distributed_manifests(self) -> None:
        self.assertEqual(builder.product_version(), "0.1.0")

    def test_supported_targets_have_closed_names_and_platform_specific_archives(self) -> None:
        self.assertEqual(set(builder.TARGETS), {"x86_64-unknown-linux-gnu", "x86_64-pc-windows-msvc"})
        self.assertEqual(builder.TARGETS["x86_64-unknown-linux-gnu"].archive_suffix, "tar.gz")
        self.assertEqual(builder.TARGETS["x86_64-pc-windows-msvc"].binary_name, "vmmu.exe")

    def test_target_resolution_refuses_cross_build_and_unknown_target(self) -> None:
        with patch.object(builder, "host_tuple", return_value="x86_64-unknown-linux-gnu"):
            with self.assertRaises(builder.ReleaseBundleError):
                builder.target_spec("x86_64-pc-windows-msvc")
            with self.assertRaises(builder.ReleaseBundleError):
                builder.target_spec("aarch64-unknown-linux-gnu")

    def test_manifest_serialization_is_canonical_and_ends_with_newline(self) -> None:
        self.assertEqual(builder.canonical_json({"b": 1, "a": 2}), b'{"a":2,"b":1}\n')


if __name__ == "__main__":
    unittest.main()
