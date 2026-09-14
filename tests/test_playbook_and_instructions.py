"""Cover the universal playbook and the five-section MCP instructions (§20, §26).

The playbook was written at initialization and read by nothing: a project received a document
for humans, not a rule the system applied. The generated instructions carried a core doctrine
and the capability list, but neither the project playbook, the policy summary nor the resume
protocol the specification requires.

Invariants exercised: I001 (the store and its declared files are the source of truth), I009
(resume bound to a hashed contract), I012 (the generated runtime is traceable) and I015 (the
Core carries no domain vocabulary of its own).
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.mcp_instructions import compile_mcp_instructions
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.playbook import (
    CORE_LAWS,
    PlaybookError,
    compile_project_playbook,
)
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteService


class PlaybookTests(unittest.TestCase):
    def _project(self, root: Path, template: str = "software") -> Path:
        preview = preview_project_initialization(root, template=template, project_id="book-project", project_name="Book Project")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    # --- core laws -------------------------------------------------------

    def test_core_laws_are_the_eight_the_specification_fixes(self) -> None:
        self.assertEqual(len(CORE_LAWS), 8)
        for law in CORE_LAWS:
            self.assertTrue(law.strip())
            self.assertFalse(law.endswith(" "))

    def test_playbook_is_loaded_hashed_and_bounded(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                playbook = compile_project_playbook(store)
                self.assertEqual(playbook.format, "vera-project-playbook/v1")
                self.assertEqual(len(playbook.playbook_hash), 64)
                self.assertIn("Book Project", playbook.text)
                self.assertEqual(playbook.core_laws, CORE_LAWS)

    def test_playbook_is_deterministic(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                self.assertEqual(compile_project_playbook(store), compile_project_playbook(store))

    def test_missing_playbook_is_refused_loudly(self) -> None:
        """I014: an absent project rule is a refusal, not a silent empty section."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(PlaybookError):
                    compile_project_playbook(store)

    def test_oversized_playbook_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "playbook.md").write_text("x" * 200_000, encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(PlaybookError):
                    compile_project_playbook(store)

    def test_symlinked_playbook_is_refused(self) -> None:
        """I008: a project rule is read from the runtime, never followed out of it."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            target = root / "elsewhere.md"
            target.write_text("# Ailleurs\n", encoding="utf-8")
            book = root / ".vera-mmu" / "playbook.md"
            book.unlink()
            book.symlink_to(target)
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(PlaybookError):
                    compile_project_playbook(store)


class InstructionsCompositionTests(unittest.TestCase):
    def _ready(self, root: Path) -> Path:
        preview = preview_project_initialization(root, template="software", project_id="instr-project", project_name="Instr Project")
        apply_project_initialization(root, preview, confirm=True)
        profile = root / ".vera-mmu" / "project.yaml"
        with MemoryStore.open(load_profile(profile), profile) as store:
            WriteService(store).sync_profile_capabilities(actor="test")
        return profile

    def _instructions(self, store: MemoryStore):
        rows = store.connection.execute("SELECT capability_id FROM capability_policy WHERE decision='ALLOW' ORDER BY capability_id").fetchall()
        manifest = compile_mcp_manifest(store, adapter_bindings={str(row[0]): "generic-mcp-deny-v1" for row in rows})
        return compile_mcp_instructions(store, manifest)

    def test_instructions_carry_the_five_required_sections(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                text = self._instructions(store).text
                for heading in ("CORE DOCTRINE", "PROJECT PLAYBOOK", "CAPABILITY RULES", "POLICY SUMMARY", "RESUME PROTOCOL"):
                    self.assertIn(heading, text, f"Section {heading} absente des instructions.")

    def test_core_doctrine_states_every_universal_law(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                text = self._instructions(store).text
                for law in CORE_LAWS:
                    self.assertIn(law, text)

    def test_project_playbook_reaches_the_instructions(self) -> None:
        """The whole point of §20: the project's own rules must govern the agent."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._ready(root)
            marker = "Toute mesure de latence doit citer son banc d’essai."
            book = root / ".vera-mmu" / "playbook.md"
            book.write_text(book.read_text(encoding="utf-8") + f"\n## Règle locale\n\n{marker}\n", encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                self.assertIn(marker, self._instructions(store).text)

    def test_policy_summary_reports_the_declared_decisions(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                text = self._instructions(store).text
                self.assertIn("network", text)
                self.assertIn("deny", text)

    def test_resume_protocol_names_the_required_sections(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                text = self._instructions(store).text
                self.assertIn("working-rules", text)
                self.assertIn("mmu_acknowledge_resume", text)

    def test_instructions_are_bound_to_the_profile_hash(self) -> None:
        """§26: the compiled text is hashed and bound to the Profile Hash."""
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                compiled = self._instructions(store)
                self.assertEqual(compiled.profile_hash, store.identity.profile_hash)
                self.assertIn(store.identity.profile_hash, compiled.text)
                self.assertEqual(len(compiled.instructions_hash), 64)

    def test_editing_the_playbook_changes_the_instructions_hash(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._ready(root)
            with MemoryStore.open(load_profile(profile), profile) as store:
                before = self._instructions(store).instructions_hash
            book = root / ".vera-mmu" / "playbook.md"
            book.write_text(book.read_text(encoding="utf-8") + "\n## Ajout\n\nUne règle de plus.\n", encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                self.assertNotEqual(self._instructions(store).instructions_hash, before)

    def test_instructions_carry_no_domain_vocabulary_of_their_own(self) -> None:
        """I015: the Core text must not name a domain concept it does not own."""
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                text = self._instructions(store).text.lower()
                for forbidden in ("aret", "brick", "function_symbol"):
                    self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
