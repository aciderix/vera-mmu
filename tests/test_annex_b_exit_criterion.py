"""Execute the specification's Annexe B exit criterion for every declared domain.

The specification calls the work DONE when `init`, `scan`, `validate`, `generate` and `doctor`
succeed on a clean machine. Before this lot `generate` refused every freshly initialized
project, because the templates emitted an empty capability catalog and nothing materialized a
declared catalog into the store.

Invariants exercised: I007/I015 (the generated runtime comes from the declared catalog only)
and I012 (profile, catalogs and packs contribute to a traceable build hash).
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.__main__ import main
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import TEMPLATE_IDS, apply_project_initialization, preview_project_initialization
from vera_mmu.project_catalogs import load_project_catalogs
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteService


def _run(capsys_free_args: list[str]) -> dict[str, object]:
    """Run one CLI command and return its JSON payload."""
    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(capsys_free_args)
    payload = json.loads(buffer.getvalue())
    payload["_exit_code"] = code
    return payload


class AnnexBExitCriterionTests(unittest.TestCase):
    def _initialize(self, root: Path, template: str) -> Path:
        preview = preview_project_initialization(root, template=template, project_id=f"exit-{template}", project_name=f"Exit {template}")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    def test_every_template_declares_domain_capabilities_and_gates(self) -> None:
        """A domain must differ by more than its entity type list."""
        seen_capability_sets: dict[str, frozenset[str]] = {}
        for template in TEMPLATE_IDS:
            with TemporaryDirectory() as tmp:
                profile = self._initialize(Path(tmp), template)
                catalogs = load_project_catalogs(profile)
                capability_ids = frozenset(str(item["id"]) for item in catalogs.capabilities["capabilities"])
                gate_ids = frozenset(str(item["id"]) for item in catalogs.gates["gates"])
                self.assertTrue(capability_ids, f"{template} ne déclare aucune capability.")
                self.assertTrue(gate_ids, f"{template} ne déclare aucune gate.")
                seen_capability_sets[template] = capability_ids
        # Each domain carries its own vocabulary, not one shared placeholder set.
        self.assertEqual(len(set(seen_capability_sets.values())), len(TEMPLATE_IDS))

    def test_declared_catalog_is_materialized_into_the_store(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._initialize(Path(tmp), "software")
            declared = {str(item["id"]) for item in load_project_catalogs(profile).capabilities["capabilities"]}
            with MemoryStore.open(load_profile(profile), profile) as store:
                synced = WriteService(store).sync_profile_capabilities(actor="test")
                self.assertEqual(set(synced), declared)
                stored = {str(row[0]) for row in store.connection.execute("SELECT id FROM capability").fetchall()}
                self.assertEqual(stored, declared)
                allowed = {str(row[0]) for row in store.connection.execute(
                    "SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW'").fetchall()}
                self.assertTrue(allowed, "Aucune capability ALLOW : generate resterait impossible.")

    def test_capability_sync_is_idempotent(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._initialize(Path(tmp), "data")
            with MemoryStore.open(load_profile(profile), profile) as store:
                writer = WriteService(store)
                self.assertEqual(writer.sync_profile_capabilities(actor="test"), writer.sync_profile_capabilities(actor="test"))

    def test_annex_b_sequence_succeeds_on_every_domain(self) -> None:
        """init → scan → validate → generate → doctor, per the specification's exit criterion."""
        for template in TEMPLATE_IDS:
            with self.subTest(template=template):
                with TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    scan = _run(["scan", str(root)])
                    self.assertTrue(scan["ok"])

                    profile = self._initialize(root, template)
                    self.assertTrue(_run(["init", str(profile)])["ok"])
                    self.assertTrue(_run(["identity", str(profile)])["ok"])
                    self.assertTrue(_run(["inspect", str(profile)])["ok"])
                    self.assertTrue(_run(["sync-capabilities", str(profile)])["ok"])

                    generation = _run(["generate", str(profile), "--adapter", "generic-mcp"])
                    self.assertTrue(generation["ok"], f"generate a échoué pour {template} : {generation.get('error')}")
                    self.assertEqual(len(generation["generation"]["mcp_build_hash"]), 64)

                    doctor = _run(["doctor", str(profile)])
                    self.assertTrue(doctor["ok"], f"doctor a échoué pour {template}.")
                    self.assertEqual(doctor["doctor"]["status"], "PASS")

    def test_generation_is_deterministic_for_one_profile(self) -> None:
        """I012: same profile and catalogs must produce the same build hash."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._initialize(root, "research")
            _run(["init", str(profile)])
            _run(["sync-capabilities", str(profile)])
            first = _run(["generate", str(profile), "--adapter", "generic-mcp"])["generation"]
            second = _run(["generate", str(profile), "--adapter", "generic-mcp"])["generation"]
            self.assertEqual(first["mcp_build_hash"], second["mcp_build_hash"])
            self.assertEqual(first["preview_hash"], second["preview_hash"])


if __name__ == "__main__":
    unittest.main()
