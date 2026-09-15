"""Cover the taxonomy, entity and relation editing of the journey (§29.2, steps 5 to 7).

The Core already declared these three sections and synchronised them into the store; nothing
could ask it to change them. This adds the editing, under the same cycle as every other sensitive
write: preview, freshness check, explicit confirmation, atomic write or refusal.

One refusal carries the lot. Removing a type that already carries knowledge, entities or
relations would orphan what the project has recorded, so it is refused **by the Core**, counted
against the memory itself — not greyed out in a screen. A rule enforced only in the interface is
a rule that disappears the moment anything else writes.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import yaml

from vera_mmu.identity import load_profile
from vera_mmu.profile_taxonomy import (
    TaxonomyError,
    apply_taxonomy_edit,
    preview_taxonomy_edit,
)
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteService


class TaxonomyEditTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        preview = preview_project_initialization(root, template="software", project_id="taxonomy-project", project_name="Taxonomy Project")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    @staticmethod
    def _declared(profile_path: Path, section: str) -> list[str]:
        return list(yaml.safe_load(profile_path.read_text(encoding="utf-8"))[section]["types"])

    def _record_knowledge(self, profile_path: Path, type_id: str) -> None:
        """Put one piece of knowledge under a declared type, so removing it would orphan it."""
        with MemoryStore.open(load_profile(profile_path), profile_path) as store:
            service = WriteService(store)
            service.sync_profile_knowledge_types(actor="test")
            service.append_knowledge(
                "fait-consigne", type_id=type_id, status="OBSERVED",
                title="Fait consigné", content="Contenu de test.", actor="test",
            )

    # --- the ordinary edit -------------------------------------------------

    def test_a_type_can_be_added_and_the_preview_writes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)
            before = profile_path.read_bytes()

            preview = preview_taxonomy_edit(profile_path, knowledge_types=[*self._declared(profile_path, "knowledge"), "CONSTRAINT"])

            self.assertEqual(preview.status, "PREVIEW")
            self.assertEqual(preview.mutation, "NONE")
            self.assertEqual(profile_path.read_bytes(), before)
            change = next(item for item in preview.changes if item.section == "knowledge")
            self.assertEqual(change.added, ("CONSTRAINT",))
            self.assertEqual(change.removed, ())

    def test_a_confirmed_edit_rewrites_only_the_section_it_names(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)
            entities_before = self._declared(profile_path, "entities")

            preview = preview_taxonomy_edit(profile_path, knowledge_types=[*self._declared(profile_path, "knowledge"), "CONSTRAINT"])
            result = apply_taxonomy_edit(profile_path, preview, confirm=True)

            self.assertEqual(result["status"], "APPLIED")
            self.assertIn("CONSTRAINT", self._declared(profile_path, "knowledge"))
            self.assertEqual(self._declared(profile_path, "entities"), entities_before)
            self.assertTrue(load_profile(profile_path))

    def test_the_three_sections_can_be_edited_in_one_confirmed_operation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)

            preview = preview_taxonomy_edit(
                profile_path,
                knowledge_types=[*self._declared(profile_path, "knowledge"), "CONSTRAINT"],
                entity_types=[*self._declared(profile_path, "entities"), "SERVICE"],
                relation_types=[*self._declared(profile_path, "relations"), "CONSTRAINS"],
            )
            apply_taxonomy_edit(profile_path, preview, confirm=True)

            self.assertIn("CONSTRAINT", self._declared(profile_path, "knowledge"))
            self.assertIn("SERVICE", self._declared(profile_path, "entities"))
            self.assertIn("CONSTRAINS", self._declared(profile_path, "relations"))

    def test_an_edit_that_changes_nothing_is_reported_as_such(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)
            preview = preview_taxonomy_edit(profile_path, knowledge_types=self._declared(profile_path, "knowledge"))
            self.assertEqual(preview.status, "NOTHING_TO_CHANGE")

    # --- the refusal that carries the lot ----------------------------------

    def test_removing_a_type_that_carries_knowledge_is_refused_by_the_core(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)
            self._record_knowledge(profile_path, "RULE")
            remaining = [item for item in self._declared(profile_path, "knowledge") if item != "RULE"]

            preview = preview_taxonomy_edit(profile_path, knowledge_types=remaining)

            self.assertEqual(preview.status, "REFUSED")
            self.assertTrue(any("RULE" in blocker for blocker in preview.blockers))
            with self.assertRaises(TaxonomyError):
                apply_taxonomy_edit(profile_path, preview, confirm=True)
            self.assertIn("RULE", self._declared(profile_path, "knowledge"))

    def test_the_refusal_says_how_much_would_have_been_orphaned(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)
            self._record_knowledge(profile_path, "RULE")
            remaining = [item for item in self._declared(profile_path, "knowledge") if item != "RULE"]
            blockers = preview_taxonomy_edit(profile_path, knowledge_types=remaining).blockers
            self.assertTrue(any("1" in blocker for blocker in blockers), blockers)

    def test_an_unused_type_can_be_removed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)
            self._record_knowledge(profile_path, "RULE")
            remaining = [item for item in self._declared(profile_path, "knowledge") if item != "HYPOTHESIS"]

            preview = preview_taxonomy_edit(profile_path, knowledge_types=remaining)
            apply_taxonomy_edit(profile_path, preview, confirm=True)

            self.assertNotIn("HYPOTHESIS", self._declared(profile_path, "knowledge"))
            self.assertIn("RULE", self._declared(profile_path, "knowledge"))

    # --- the other refusals ------------------------------------------------

    def test_a_lowercase_identifier_is_refused(self) -> None:
        """Declarative identifiers are uppercase; the store's lowercase form is derived, not typed."""
        with TemporaryDirectory() as tmp:
            profile_path = self._project(Path(tmp))
            with self.assertRaises(TaxonomyError):
                preview_taxonomy_edit(profile_path, knowledge_types=["rule"])

    def test_a_duplicate_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            profile_path = self._project(Path(tmp))
            with self.assertRaises(TaxonomyError):
                preview_taxonomy_edit(profile_path, knowledge_types=["RULE", "RULE"])

    def test_emptying_the_knowledge_taxonomy_is_refused(self) -> None:
        """A project that declares no knowledge type cannot record anything at all."""
        with TemporaryDirectory() as tmp:
            profile_path = self._project(Path(tmp))
            with self.assertRaises(TaxonomyError):
                preview_taxonomy_edit(profile_path, knowledge_types=[])

    def test_an_edit_requires_an_explicit_confirmation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)
            before = profile_path.read_bytes()
            preview = preview_taxonomy_edit(profile_path, knowledge_types=[*self._declared(profile_path, "knowledge"), "CONSTRAINT"])
            with self.assertRaises(TaxonomyError):
                apply_taxonomy_edit(profile_path, preview, confirm=False)
            self.assertEqual(profile_path.read_bytes(), before)

    def test_a_stale_preview_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)
            preview = preview_taxonomy_edit(profile_path, knowledge_types=[*self._declared(profile_path, "knowledge"), "CONSTRAINT"])

            other = preview_taxonomy_edit(profile_path, entity_types=[*self._declared(profile_path, "entities"), "SERVICE"])
            apply_taxonomy_edit(profile_path, other, confirm=True)

            with self.assertRaises(TaxonomyError):
                apply_taxonomy_edit(profile_path, preview, confirm=True)

    def test_calling_without_naming_any_section_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            profile_path = self._project(Path(tmp))
            with self.assertRaises(TaxonomyError):
                preview_taxonomy_edit(profile_path)

    def test_a_broken_profile_is_refused_rather_than_rewritten(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._project(root)
            profile_path.write_text("mmu:\n  version: \"2.0\"\n", encoding="utf-8")
            with self.assertRaises(TaxonomyError):
                preview_taxonomy_edit(profile_path, knowledge_types=["RULE"])


if __name__ == "__main__":
    unittest.main()
