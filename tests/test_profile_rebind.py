from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore, StoreIdentityError
from tests.test_profile_edit_identity_guard import BASE


class ProfileRebindTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        runtime = self.root / ".vera-mmu"
        runtime.mkdir()
        self.profile_path = runtime / "project.yaml"
        self.profile_path.write_text(BASE, encoding="utf-8")
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path):
            pass

    def test_preview_is_pure_and_confirmed_rebind_keeps_profile_and_store_aligned(self) -> None:
        from vera_mmu.profile_rebind import apply_project_profile_rebind, preview_project_profile_rebind

        before = self.profile_path.read_text(encoding="utf-8")
        preview = preview_project_profile_rebind(self.profile_path, project_name="Rebound profile", project_description="Changed deliberately")
        self.assertEqual(self.profile_path.read_text(encoding="utf-8"), before)
        with self.assertRaises(Exception):
            apply_project_profile_rebind(self.profile_path, preview, confirm=False)
        result = apply_project_profile_rebind(self.profile_path, preview, confirm=True)
        self.assertEqual(result["status"], "REBOUND")
        profile = load_profile(self.profile_path)
        self.assertEqual(profile["project"]["name"], "Rebound profile")
        with MemoryStore.open(profile, self.profile_path) as store:
            self.assertEqual(store.metadata()["project_identity"], store.identity.as_dict())
            self.assertEqual(store.audit_events()[-1]["action"], "PROJECT_PROFILE_REBOUND")

    def test_interrupted_rebind_is_recovered_deterministically(self) -> None:
        from unittest.mock import patch
        from vera_mmu.profile_rebind import apply_project_profile_rebind, recover_project_profile_rebind, preview_project_profile_rebind

        preview = preview_project_profile_rebind(self.profile_path, project_name="Recovered profile", project_description="Recovered deliberately")
        with patch("vera_mmu.profile_rebind._write_atomic", side_effect=OSError("simulated interruption")):
            with self.assertRaises(OSError):
                apply_project_profile_rebind(self.profile_path, preview, confirm=True)
        with self.assertRaises(StoreIdentityError):
            MemoryStore.open(load_profile(self.profile_path), self.profile_path)
        self.assertEqual(recover_project_profile_rebind(self.profile_path)["status"], "RECOVERED")
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path) as store:
            self.assertEqual(store.metadata()["project_identity"], store.identity.as_dict())

    def test_stale_preview_refuses_without_changing_store_identity(self) -> None:
        from vera_mmu.profile_rebind import ProfileRebindError, apply_project_profile_rebind, preview_project_profile_rebind

        preview = preview_project_profile_rebind(self.profile_path, project_name="Rebound profile", project_description="Changed deliberately")
        self.profile_path.write_text(BASE.replace("Initial description", "Concurrent change"), encoding="utf-8")
        with self.assertRaises(ProfileRebindError):
            apply_project_profile_rebind(self.profile_path, preview, confirm=True)
        with self.assertRaises(StoreIdentityError):
            MemoryStore.open(load_profile(self.profile_path), self.profile_path)


if __name__ == "__main__":
    unittest.main()
