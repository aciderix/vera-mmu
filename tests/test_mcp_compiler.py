"""Cover the explicit, ordered MCP compiler pipeline (§25).

Generation already produced a manifest, instructions, a host configuration and a hook plan,
but it did so implicitly: no named stages, no blocking static validation before the output was
handed back, and no package gathering what a clean machine would need.

Invariants exercised: I007 (only declared capabilities reach the package), I008 (no client
input selects a command or a path), I012 (profile, catalogs and packs feed a traceable build
hash) and I014 (an inconsistency stops the pipeline instead of shipping).
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.mcp_compiler import (
    COMPILER_STAGES,
    MCPCompilerError,
    compile_mcp_package,
)
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteService


class MCPCompilerTests(unittest.TestCase):
    def _ready(self, root: Path, template: str = "software") -> Path:
        preview = preview_project_initialization(root, template=template, project_id="compiler-project", project_name="Compiler Project")
        apply_project_initialization(root, preview, confirm=True)
        profile = root / ".vera-mmu" / "project.yaml"
        with MemoryStore.open(load_profile(profile), profile) as store:
            WriteService(store).sync_profile_capabilities(actor="test")
        return profile

    # --- stage order -----------------------------------------------------

    def test_stage_list_matches_the_specified_pipeline(self) -> None:
        self.assertEqual(
            COMPILER_STAGES,
            (
                "load", "normalize", "validate", "canonicalize", "compute_profile_hash",
                "resolve_capabilities", "resolve_gates", "resolve_policies", "resolve_integrations",
                "generate_tool_schemas", "generate_instructions", "generate_hooks", "generate_config",
                "generate_documentation", "run_static_validation", "produce_package",
            ),
        )

    def test_package_records_every_stage_in_order(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                package = compile_mcp_package(store, "generic-mcp")
                self.assertEqual(tuple(stage.name for stage in package.stages), COMPILER_STAGES)
                self.assertTrue(all(stage.status == "PASS" for stage in package.stages))

    # --- package content -------------------------------------------------

    def test_package_carries_every_generated_output(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                package = compile_mcp_package(store, "generic-mcp")
                self.assertEqual(package.format, "vera-mcp-package/v1")
                for name in ("manifest", "instructions", "integration", "hook_plan", "documentation", "tool_schemas"):
                    self.assertIn(name, package.outputs, f"Sortie {name} absente du package.")
                    self.assertTrue(str(package.outputs[name]).strip())
                self.assertEqual(len(package.package_hash), 64)

    def test_tool_schemas_expose_only_declared_tools(self) -> None:
        """I007: the package must never advertise a tool the manifest does not carry."""
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                package = compile_mcp_package(store, "generic-mcp")
                import json

                schemas = json.loads(package.outputs["tool_schemas"])
                self.assertEqual(set(schemas["tools"]), set(package.manifest.tool_names))
                self.assertNotIn("command", json.dumps(schemas))

    def test_package_is_deterministic_for_one_profile(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                first = compile_mcp_package(store, "generic-mcp")
                second = compile_mcp_package(store, "generic-mcp")
                self.assertEqual(first.package_hash, second.package_hash)
                self.assertEqual(first.outputs, second.outputs)

    def test_editing_the_playbook_changes_the_package_hash(self) -> None:
        """I012: every declarative input must reach the build hash."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._ready(root)
            with MemoryStore.open(load_profile(profile), profile) as store:
                before = compile_mcp_package(store, "generic-mcp").package_hash
            book = root / ".vera-mmu" / "playbook.md"
            book.write_text(book.read_text(encoding="utf-8") + "\n## Ajout\n\nUne règle de plus.\n", encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                self.assertNotEqual(compile_mcp_package(store, "generic-mcp").package_hash, before)

    # --- refusals --------------------------------------------------------

    def test_unknown_adapter_is_refused_before_any_stage_runs(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(MCPCompilerError):
                    compile_mcp_package(store, "not-an-adapter")

    def test_pipeline_refuses_a_project_without_allowed_capability(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview = preview_project_initialization(root, template="data", project_id="empty-project", project_name="Empty")
            apply_project_initialization(root, preview, confirm=True)
            profile = root / ".vera-mmu" / "project.yaml"
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(MCPCompilerError):
                    compile_mcp_package(store, "generic-mcp")

    def test_missing_playbook_stops_the_pipeline(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._ready(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(MCPCompilerError):
                    compile_mcp_package(store, "generic-mcp")

    # --- static validation -----------------------------------------------

    def test_static_validation_binds_every_output_to_the_same_build(self) -> None:
        """I014: an output bound to another build must stop the pipeline, not ship."""
        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                package = compile_mcp_package(store, "generic-mcp")
                self.assertIn(package.manifest.mcp_build_hash, package.outputs["instructions"])
                self.assertEqual(package.instructions.profile_hash, store.identity.profile_hash)
                validation = next(stage for stage in package.stages if stage.name == "run_static_validation")
                self.assertEqual(validation.status, "PASS")
                self.assertTrue(validation.detail)

    def test_generation_preview_still_matches_the_pipeline(self) -> None:
        """The existing preview is the same build, surfaced under its established shape."""
        from vera_mmu.project_operations import compile_generation_preview

        with TemporaryDirectory() as tmp:
            profile = self._ready(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                package = compile_mcp_package(store, "generic-mcp")
                preview = compile_generation_preview(store, "generic-mcp")
                self.assertEqual(preview.mcp_build_hash, package.manifest.mcp_build_hash)
                self.assertEqual(preview.instructions_hash, package.instructions.instructions_hash)
                self.assertEqual(preview.instructions_text, package.outputs["instructions"])


if __name__ == "__main__":
    unittest.main()
