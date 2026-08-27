from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


class DesktopBridgeTests(unittest.TestCase):
    def _bridge(self, root: Path):
        from vera_mmu.desktop_bridge import DesktopBridge

        return DesktopBridge(root, nonce="desktop-test-nonce-0000000000000001")

    def _call(self, bridge: object, operation: str, payload: dict[str, object], *, nonce: str = "desktop-test-nonce-0000000000000001", request_id: str = "request-001") -> dict[str, object]:
        request = {
            "format": "vera-desktop-bridge/v1",
            "id": request_id,
            "nonce": nonce,
            "operation": operation,
            "input": payload,
        }
        return json.loads(bridge.handle_line(json.dumps(request)))  # type: ignore[attr-defined]

    def test_i001_i003_requires_a_strict_versioned_envelope_and_private_nonce(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            bridge = self._bridge(root)
            accepted = self._call(bridge, "project.scan", {})
            self.assertTrue(accepted["ok"])
            self.assertEqual(accepted["result"]["status"], "OBSERVED")  # type: ignore[index]

            wrong_nonce = self._call(bridge, "project.scan", {}, nonce="untrusted-browser-value")
            self.assertFalse(wrong_nonce["ok"])
            self.assertEqual(wrong_nonce["error"]["code"], "NONCE_INVALID")  # type: ignore[index]

            malformed = json.dumps({"format": "vera-desktop-bridge/v1", "id": "request-001", "nonce": "desktop-test-nonce-0000000000000001", "operation": "project.scan", "input": {}, "root": str(root)})
            rejected = json.loads(bridge.handle_line(malformed))
            self.assertFalse(rejected["ok"])
            self.assertEqual(rejected["error"]["code"], "ENVELOPE_INVALID")  # type: ignore[index]

    def test_i001_i004_scan_uses_only_the_root_selected_by_the_native_parent(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "selected"
            foreign = Path(directory) / "foreign"
            root.mkdir()
            foreign.mkdir()
            (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            (foreign / "Cargo.toml").write_text("[package]\n", encoding="utf-8")
            bridge = self._bridge(root)
            response = self._call(bridge, "project.scan", {"root": str(foreign)})
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            valid = self._call(bridge, "project.scan", {})
            observations = valid["result"]["observations"]  # type: ignore[index]
            self.assertIn("python", {item["kind"] for item in observations})
            self.assertNotIn("rust", {item["kind"] for item in observations})
            self.assertFalse((root / ".vera-mmu").exists())

    def test_i002_i005_initialization_requires_cached_preview_hash_and_confirmation(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            preview = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "desktop-example", "projectName": "Desktop Example"})
            self.assertTrue(preview["ok"])
            self.assertEqual(preview["result"]["status"], "PREVIEW")  # type: ignore[index]
            preview_hash = preview["result"]["preview_hash"]  # type: ignore[index]
            self.assertFalse((root / ".vera-mmu").exists())

            missing_confirmation = self._call(bridge, "project.init.apply", {"previewHash": preview_hash, "confirm": False})
            self.assertFalse(missing_confirmation["ok"])
            self.assertEqual(missing_confirmation["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            self.assertFalse((root / ".vera-mmu").exists())

            unknown_preview = self._call(bridge, "project.init.apply", {"previewHash": "0" * 64, "confirm": True})
            self.assertFalse(unknown_preview["ok"])
            self.assertEqual(unknown_preview["error"]["code"], "PREVIEW_UNKNOWN")  # type: ignore[index]
            self.assertFalse((root / ".vera-mmu").exists())

            applied = self._call(bridge, "project.init.apply", {"previewHash": preview_hash, "confirm": True})
            self.assertTrue(applied["ok"])
            self.assertEqual(applied["result"]["status"], "INITIALIZED")  # type: ignore[index]
            self.assertTrue((root / ".vera-mmu" / "project.yaml").is_file())

    def test_i003_i004_accepts_only_closed_operations_and_declarative_agent_ids(self) -> None:
        with TemporaryDirectory() as directory:
            bridge = self._bridge(Path(directory))
            agents = self._call(bridge, "agents.list", {})
            self.assertTrue(agents["ok"])
            self.assertIn("generic-mcp", {item["id"] for item in agents["result"]["profiles"]})  # type: ignore[index]

            raw_adapter = self._call(bridge, "agents.list", {"adapter": "generic-mcp"})
            self.assertFalse(raw_adapter["ok"])
            self.assertEqual(raw_adapter["error"]["code"], "INPUT_INVALID")  # type: ignore[index]

            unknown_operation = self._call(bridge, "shell.execute", {"command": "echo unsafe"})
            self.assertFalse(unknown_operation["ok"])
            self.assertEqual(unknown_operation["error"]["code"], "OPERATION_UNKNOWN")  # type: ignore[index]

            oversized = bridge.handle_line("x" * 16_385)  # type: ignore[attr-defined]
            self.assertEqual(json.loads(oversized)["error"]["code"], "MESSAGE_TOO_LARGE")

    def test_m11da_project_status_is_derived_non_mutating_and_accepts_no_client_selection(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            preview = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "status-desktop", "projectName": "Status desktop"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]
            response = self._call(bridge, "project.status", {})
            self.assertTrue(response["ok"])
            result = response["result"]  # type: ignore[index]
            self.assertEqual(result["coverage"]["format"], "vera-coverage-report/v1")
            self.assertEqual(result["vcs"], {"provider": "NONE", "status": "NO_VCS"})
            injected = self._call(bridge, "project.status", {"root": str(root)})
            self.assertFalse(injected["ok"])
            self.assertEqual(injected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]

    def test_m11dc_capability_builder_requires_closed_preview_and_confirmation(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            preview = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "builder-desktop", "projectName": "Builder desktop"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]
            rejected = self._call(bridge, "capability.preview", {"identifier": "lint", "name": "Lint", "kind": "CHECK", "version": "1.0.0", "description": "", "command": "unsafe"})
            self.assertFalse(rejected["ok"])
            self.assertEqual(rejected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            draft = self._call(bridge, "capability.preview", {"identifier": "lint", "name": "Lint", "kind": "CHECK", "version": "1.0.0", "description": ""})
            self.assertTrue(draft["ok"])
            refused = self._call(bridge, "capability.apply", {"previewHash": draft["result"]["preview_hash"], "confirm": False})  # type: ignore[index]
            self.assertFalse(refused["ok"])
            self.assertEqual(refused["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            applied = self._call(bridge, "capability.apply", {"previewHash": draft["result"]["preview_hash"], "confirm": True})  # type: ignore[index]
            self.assertTrue(applied["ok"])
            self.assertEqual(applied["result"]["capability"]["id"], "lint")  # type: ignore[index]

    def test_i001_i007_memory_sync_has_no_git_input_in_desktop_protocol(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            preview = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "sync-desktop", "projectName": "Sync desktop"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]
            injected = self._call(bridge, "memory.sync", {"remote": "untrusted"})
            self.assertFalse(injected["ok"])
            self.assertEqual(injected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            result = self._call(bridge, "memory.sync", {})
            self.assertTrue(result["ok"])
            self.assertEqual(result["result"]["status"], "REFUSED")  # type: ignore[index]

    def test_i002_i005_routes_generic_mcp_only_from_a_declared_agent_profile_and_cached_preview(self) -> None:
        from vera_mmu.capabilities import CapabilityService
        from vera_mmu.capability_contracts import CapabilityContractService
        from vera_mmu.capability_policies import CapabilityPolicyService
        from vera_mmu.identity import load_profile
        from vera_mmu.store import MemoryStore

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            initialized = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "mcp-desktop", "projectName": "MCP Desktop"})
            initialized_hash = initialized["result"]["preview_hash"]  # type: ignore[index]
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": initialized_hash, "confirm": True})["ok"])
            profile = root / ".vera-mmu" / "project.yaml"
            with MemoryStore.open(load_profile(profile), profile) as store:
                CapabilityService(store).create("check", "Check", "CHECK", "1.0.0", parameter_schema={"type": "object", "additionalProperties": False}, metadata={}, actor="test")
                CapabilityContractService(store).declare("check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type": "object", "additionalProperties": False}, actor="test")
                CapabilityPolicyService(store).declare("check", "ALLOW", "test", actor="test")

            raw_adapter = self._call(bridge, "adapter.generate", {"adapter": "generic-mcp"})
            self.assertFalse(raw_adapter["ok"])
            self.assertEqual(raw_adapter["error"]["code"], "INPUT_INVALID")  # type: ignore[index]

            generated = self._call(bridge, "adapter.generate", {"agentProfileId": "generic-mcp"})
            self.assertTrue(generated["ok"])
            self.assertEqual(generated["result"]["adapter"], "generic-mcp")  # type: ignore[index]
            self.assertEqual(generated["result"]["status"], "PREVIEW")  # type: ignore[index]

            stage_refused = self._call(bridge, "adapter.stage", {"agentProfileId": "generic-mcp", "confirm": False})
            self.assertFalse(stage_refused["ok"])
            self.assertEqual(stage_refused["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            self.assertFalse((root / ".mcp.json").exists())
            staged = self._call(bridge, "adapter.stage", {"agentProfileId": "generic-mcp", "confirm": True})
            self.assertTrue(staged["ok"])

            preview = self._call(bridge, "adapter.install.preview", {"agentProfileId": "generic-mcp"})
            self.assertTrue(preview["ok"])
            preview_hash = preview["result"]["previewHash"]  # type: ignore[index]
            self.assertFalse((root / ".mcp.json").exists())
            unconfirmed = self._call(bridge, "adapter.install.apply", {"previewHash": preview_hash, "confirm": False})
            self.assertFalse(unconfirmed["ok"])
            self.assertEqual(unconfirmed["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            self.assertFalse((root / ".mcp.json").exists())

            (root / ".mcp.json").write_text('{"human":"changed"}\n', encoding="utf-8")
            stale = self._call(bridge, "adapter.install.apply", {"previewHash": preview_hash, "confirm": True})
            self.assertFalse(stale["ok"])
            self.assertEqual(stale["error"]["code"], "PREVIEW_STALE")  # type: ignore[index]
            self.assertEqual((root / ".mcp.json").read_text(encoding="utf-8"), '{"human":"changed"}\n')

            preview = self._call(bridge, "adapter.install.preview", {"agentProfileId": "generic-mcp"})
            preview_hash = preview["result"]["previewHash"]  # type: ignore[index]
            applied = self._call(bridge, "adapter.install.apply", {"previewHash": preview_hash, "confirm": True})
            self.assertTrue(applied["ok"])
            self.assertEqual(applied["result"]["status"], "APPLIED_PROJECT_LOCAL")  # type: ignore[index]
            self.assertTrue((root / ".mcp.json").is_file())
            doctor = self._call(bridge, "adapter.doctor", {"agentProfileId": "generic-mcp"})
            self.assertTrue(doctor["ok"])
            self.assertEqual(doctor["result"]["configuration"], "CONFIGURED")  # type: ignore[index]
            self.assertEqual(doctor["result"]["host"], "NOT_OBSERVED")  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
