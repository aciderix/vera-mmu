from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from vera_mmu.documentation_generator import compile_project_documentation
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore, StoreError


def test_documentation_is_deterministic_and_non_mutating() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        preview = preview_project_initialization(root, template="software", project_id="docs-project", project_name="Docs project")
        apply_project_initialization(root, preview, confirm=True)
        profile_path = root / ".vera-mmu" / "project.yaml"
        with MemoryStore.open(load_profile(profile_path), profile_path) as store:
            before = store.audit_events()
            first = compile_project_documentation(store, profile_path)
            second = compile_project_documentation(store, profile_path)
            assert first == second
            assert set(first.documents) == {"MMU_SETUP.md", "TOOLS.md", "GATES.md", "POLICIES.md", "ARCHITECTURE.md", "MAINTENANCE.md"}
            assert "docs-project" in first.documents["MMU_SETUP.md"]
            assert first.bundle_hash
            assert store.audit_events() == before
            profile_path.write_text(profile_path.read_text(encoding="utf-8").replace("Docs project", "Different project"), encoding="utf-8")
            try:
                compile_project_documentation(store, profile_path)
            except StoreError:
                pass
            else:
                raise AssertionError("Le générateur doit refuser un Profile divergent du store actif.")
