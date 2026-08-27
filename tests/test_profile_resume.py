from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "profile-resume"
  name: "Profile Resume"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
  max_resume_bytes: 1024
resume:
  template: engineering
  sections:
    - id: working-rules
      required: true
    - id: optional-context
      required: false
    - id: current-state
      required: true
"""


class ProfileResumeTests(unittest.TestCase):
    def test_i009_i012_profile_declares_the_resume_guard_contract(self) -> None:
        from vera_mmu.profile_resume import compile_profile_resume_dossier, profile_resume_requirements, profile_resume_sections

        with TemporaryDirectory() as directory:
            profile_path = Path(directory) / "project.yaml"
            profile_path.write_text(PROFILE, encoding="utf-8")
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                requirements = profile_resume_requirements(store)
                self.assertEqual([item.identifier for item in requirements], ["working-rules", "current-state"])
                self.assertEqual(set(profile_resume_sections(store, "Le Project Profile pilote le dossier de reprise.")), {"working-rules", "current-state"})
                dossier = compile_profile_resume_dossier(
                    store,
                    {
                        "working-rules": "Mesurer les faits avant toute conclusion importante.",
                        "current-state": "Le contrat de reprise est construit depuis le Project Profile.",
                    },
                )
                self.assertEqual([item.identifier for item in dossier.requirements], ["working-rules", "current-state"])
                self.assertEqual(dossier.profile_hash, store.identity.profile_hash)
                self.assertNotIn("optional-context", dossier.json_text)

    def test_i009_i014_profile_resume_refuses_missing_or_incoherent_sections(self) -> None:
        from vera_mmu.profile_resume import ProfileResumeError, compile_profile_resume_dossier

        with TemporaryDirectory() as directory:
            profile_path = Path(directory) / "project.yaml"
            profile_path.write_text(PROFILE, encoding="utf-8")
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                with self.assertRaises(ProfileResumeError):
                    compile_profile_resume_dossier(store, {"working-rules": "Mesurer les faits avant toute conclusion importante."})
                with self.assertRaises(ProfileResumeError):
                    compile_profile_resume_dossier(store, {"working-rules": "Mesurer les faits avant toute conclusion importante.", "current-state": "Le contrat est valide.", "foreign": "Ce champ est interdit."})


if __name__ == "__main__":
    unittest.main()
