from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "cap-builder"
  name: "Capability Builder"
  domain: "software"
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


class CapabilityBuilderTests(unittest.TestCase):
    def _store(self, root: Path) -> MemoryStore:
        runtime = root / ".vera-mmu"
        runtime.mkdir()
        profile = runtime / "project.yaml"
        profile.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile), profile)

    def test_i001_i003_i007_i009_preview_is_non_mutating_and_apply_is_confirmed_fresh_atomic(self) -> None:
        from vera_mmu.capabilities import CapabilityService
        from vera_mmu.capability_builder import CapabilityBuilderError, apply_capability_draft, preview_capability_draft

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                audits = store.audit_events()
                preview = preview_capability_draft(store, identifier="lint", name="Lint", kind="CHECK", version="1.0.0", description="Static check")
                self.assertEqual(store.audit_events(), audits)
                with self.assertRaises(CapabilityBuilderError):
                    apply_capability_draft(store, preview, confirm=False)
                result = apply_capability_draft(store, preview, confirm=True)
                self.assertEqual(result["status"], "DECLARED")
                self.assertEqual(result["capability"]["address"], "vera://cap-builder/capability/lint")
                self.assertEqual(CapabilityService(store).get("lint").created_by, "DASHBOARD")
                stale = preview_capability_draft(store, identifier="unit", name="Unit", kind="CHECK", version="1.0.0")
                CapabilityService(store).create("other", "Other", "QUERY", "1.0.0")
                with self.assertRaises(CapabilityBuilderError):
                    apply_capability_draft(store, stale, confirm=True)
                with self.assertRaises(CapabilityBuilderError):
                    preview_capability_draft(store, identifier="bad/path", name="Bad", kind="CHECK", version="1.0.0")
                with self.assertRaises(CapabilityBuilderError):
                    preview_capability_draft(store, identifier="network", name="Network", kind="RUN", version="1.0.0")


if __name__ == "__main__":
    unittest.main()
