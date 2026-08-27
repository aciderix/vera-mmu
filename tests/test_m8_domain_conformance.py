from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.agent_profiles import builtin_agent_profiles
from vera_mmu.__main__ import main
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.desktop_bridge import DesktopBridge
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.project_operations import scan_project
from vera_mmu.store import MemoryStore
from vera_mmu.workspace import resolve_workspace


DOMAINS = {
    "software": "pyproject.toml",
    "data": "requirements.txt",
    "research": "README.md",
    "documentation": "docs/guide.md",
    "game": "package.json",
    "hardware": "Cargo.toml",
}
NONCE = "m8-conformance-nonce-000000000001"


def _call(bridge: DesktopBridge, operation: str, payload: dict[str, object], request_id: str) -> dict[str, object]:
    envelope = {
        "format": "vera-desktop-bridge/v1",
        "id": request_id,
        "nonce": NONCE,
        "operation": operation,
        "input": payload,
    }
    return json.loads(bridge.handle_line(json.dumps(envelope)))


def _invoke(argv: list[str]) -> tuple[int, dict[str, object]]:
    output = StringIO()
    with redirect_stdout(output):
        code = main(argv)
    return code, json.loads(output.getvalue())


def _seed(profile: Path) -> list[dict[str, object]]:
    statuses: list[dict[str, object]] = []
    with MemoryStore.open(load_profile(profile), profile) as store:
        CapabilityService(store).create("check", "Check", "CHECK", "1.0.0", parameter_schema={"type": "object", "additionalProperties": False}, metadata={}, actor="m8")
        statuses.append(store.last_sync_status)
        CapabilityContractService(store).declare("check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type": "object", "additionalProperties": False}, actor="m8")
        statuses.append(store.last_sync_status)
        CapabilityPolicyService(store).declare("check", "ALLOW", "m8", actor="m8")
        statuses.append(store.last_sync_status)
    return statuses


class M8DomainConformanceTests(unittest.TestCase):
    def test_i001_i007_i011_all_domain_templates_follow_the_same_project_local_mcp_path(self) -> None:
        for domain, marker in DOMAINS.items():
            with self.subTest(domain=domain), TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / marker
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("marker only\n", encoding="utf-8")
                scan = scan_project(root)
                self.assertEqual(scan.status, "OBSERVED")
                self.assertFalse((root / ".vera-mmu").exists())
                code, payload = _invoke(["scan", str(root)])
                self.assertEqual(code, 0)
                self.assertEqual(payload["scan"]["status"], "OBSERVED")
                self.assertFalse((root / ".vera-mmu").exists())

                code, payload = _invoke(["init-project", str(root), "--template", domain, "--project-id", f"m8-{domain}", "--project-name", f"M8 {domain}"])
                self.assertEqual(code, 0)
                self.assertEqual(payload["initialization"]["status"], "PREVIEW")
                self.assertFalse((root / ".vera-mmu").exists())

                bridge = DesktopBridge(root, nonce=NONCE)
                preview = _call(bridge, "project.init.preview", {"template": domain, "projectId": f"m8-{domain}", "projectName": f"M8 {domain}"}, "preview-001")
                self.assertTrue(preview["ok"])
                self.assertEqual(preview["result"]["status"], "PREVIEW")
                initialized = _call(bridge, "project.init.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": True}, "apply-001")
                self.assertTrue(initialized["ok"])
                profile = root / ".vera-mmu" / "project.yaml"
                self.assertEqual(load_profile(profile)["project"]["domain"], domain)
                _seed(profile)

                generated = _call(bridge, "adapter.generate", {"agentProfileId": "generic-mcp"}, "generate-001")
                self.assertTrue(generated["ok"])
                self.assertEqual(generated["result"]["status"], "PREVIEW")
                self.assertEqual(generated["result"]["adapter"], builtin_agent_profiles()["generic-mcp"].adapter)
                self.assertTrue(_call(bridge, "adapter.stage", {"agentProfileId": "generic-mcp", "confirm": True}, "stage-001")["ok"])
                installation = _call(bridge, "adapter.install.preview", {"agentProfileId": "generic-mcp"}, "install-preview-001")
                self.assertTrue(installation["ok"])
                applied = _call(bridge, "adapter.install.apply", {"previewHash": installation["result"]["previewHash"], "confirm": True}, "install-apply-001")
                self.assertTrue(applied["ok"])
                self.assertEqual(applied["result"]["status"], "APPLIED_PROJECT_LOCAL")
                self.assertTrue((root / ".mcp.json").is_file())

    def test_i004_workspace_topologies_keep_git_optional_and_roots_confined(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            preview = preview_project_initialization(root, template="software", project_id="m8-no-git", project_name="M8 no Git")
            apply_project_initialization(root, preview, confirm=True)
            workspace = resolve_workspace(load_profile(root / ".vera-mmu" / "project.yaml"), root / ".vera-mmu" / "project.yaml")
            self.assertEqual(workspace.vcs_roots, ())
            self.assertEqual(workspace.roots, (root.resolve(),))

        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            (root / "services" / "api").mkdir(parents=True)
            (root / "clients" / "ui").mkdir(parents=True)
            preview = preview_project_initialization(root, template="software", project_id="m8-mono", project_name="M8 mono")
            apply_project_initialization(root, preview, confirm=True)
            profile = root / ".vera-mmu" / "project.yaml"
            text = profile.read_text(encoding="utf-8").replace('  root: "."\n', '  root: "."\n  additional_roots: ["services/api", "clients/ui"]\n')
            profile.write_text(text, encoding="utf-8")
            workspace = resolve_workspace(load_profile(profile), profile)
            self.assertEqual(workspace.vcs_roots, (root.resolve(),))
            self.assertEqual(len(workspace.roots), 3)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            (root / "vendor" / ".git").mkdir(parents=True)
            preview = preview_project_initialization(root, template="software", project_id="m8-multi", project_name="M8 multi")
            apply_project_initialization(root, preview, confirm=True)
            profile = root / ".vera-mmu" / "project.yaml"
            text = profile.read_text(encoding="utf-8").replace('  root: "."\n', '  root: "."\n  additional_roots: ["vendor"]\n')
            profile.write_text(text, encoding="utf-8")
            workspace = resolve_workspace(load_profile(profile), profile)
            self.assertEqual(workspace.vcs_roots, (root.resolve(), (root / "vendor").resolve()))

    def test_i007_memory_sqlite_reaches_a_fresh_clone_without_a_binary_merge(self) -> None:
        with TemporaryDirectory() as directory:
            parent = Path(directory)
            source = parent / "source"
            remote = parent / "remote.git"
            clone = parent / "clone"
            source.mkdir()
            preview = preview_project_initialization(source, template="research", project_id="m8-clone", project_name="M8 clone")
            apply_project_initialization(source, preview, confirm=True)
            profile = source / ".vera-mmu" / "project.yaml"
            with MemoryStore.open(load_profile(profile), profile):
                pass
            subprocess.run(["git", "init", "-q"], cwd=source, check=True)
            subprocess.run(["git", "config", "user.email", "m8@example.invalid"], cwd=source, check=True)
            subprocess.run(["git", "config", "user.name", "M8"], cwd=source, check=True)
            subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
            subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=source, check=True)
            subprocess.run(["git", "add", ".vera-mmu"], cwd=source, check=True)
            subprocess.run(["git", "commit", "-qm", "initial VERA memory"], cwd=source, check=True)
            branch = subprocess.run(["git", "branch", "--show-current"], cwd=source, check=True, capture_output=True, text=True).stdout.strip()
            subprocess.run(["git", "push", "-qu", "origin", branch], cwd=source, check=True)
            subprocess.run(["git", "symbolic-ref", "HEAD", f"refs/heads/{branch}"], cwd=remote, check=True)
            statuses = _seed(profile)
            self.assertEqual([status["status"] for status in statuses], ["SYNCED", "SYNCED", "SYNCED"])
            subprocess.run(["git", "clone", "-q", "--branch", branch, str(remote), str(clone)], check=True)
            cloned_profile = clone / ".vera-mmu" / "project.yaml"
            with MemoryStore.open(load_profile(cloned_profile), cloned_profile) as store:
                count = store.connection.execute("SELECT COUNT(*) AS count FROM capability").fetchone()["count"]
            self.assertEqual(count, 1)
            self.assertFalse((clone / ".vera-mmu" / "memory.sqlite-wal").exists())


if __name__ == "__main__":
    unittest.main()
