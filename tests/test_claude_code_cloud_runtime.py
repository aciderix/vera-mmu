from __future__ import annotations

from contextlib import asynccontextmanager, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.claude_code_cloud import compile_claude_code_cloud_plan
from vera_mmu.claude_code_integration import compile_claude_code_integration_plan
from vera_mmu.claude_code_local import compile_claude_code_local_plan
from vera_mmu.identity import load_profile
from vera_mmu.lifecycle_adapters import compile_lifecycle_adapter_plan
from vera_mmu.mcp_hooks import compile_mcp_hook_plan
from vera_mmu.mcp_instructions import compile_mcp_instructions
from vera_mmu.mcp_integration import compile_mcp_integration
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.store import MemoryStore


ROOT = Path(__file__).resolve().parents[1]
PROFILE = """
mmu:
  version: "2.0"
project:
  id: "claude-cloud-mcp"
  name: "Claude Cloud MCP"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
"""


class ClaudeCodeCloudRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def _prepare(self, project: Path) -> Path:
        from vera_mmu.claude_code_cloud import stage_claude_code_cloud_runtime

        profile = project / "project.yaml"
        profile.write_text(PROFILE, encoding="utf-8")
        with MemoryStore.open(load_profile(profile), profile) as store:
            CapabilityService(store).create(
                "alpha-check", "Alpha", "CHECK", "1.0.0", parameter_schema={"type": "object", "additionalProperties": False}, metadata={}, actor="test"
            )
            CapabilityContractService(store).declare(
                "alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type": "object", "additionalProperties": False}, actor="test"
            )
            CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")
            manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
            instructions = compile_mcp_instructions(store, manifest)
            integration = compile_mcp_integration(store, manifest, instructions)
            hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
            review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
            local_lifecycle = compile_lifecycle_adapter_plan(
                store, manifest, adapter_id="claude-code-local-v1", adapter_version="1.0.0", maximum_guard_mode="HARD"
            )
            local = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, local_lifecycle)
            cloud = compile_claude_code_cloud_plan(store, manifest, instructions, integration, hooks, review, local_lifecycle, local)
            result = stage_claude_code_cloud_runtime(
                store, manifest, instructions, integration, hooks, review, local_lifecycle, local, cloud, confirm=True
            )
            self.assertEqual(result.status, "STAGED")
        return profile

    def _hook(self, profile: Path, event: str, payload: dict[str, object]) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "vera_mmu.claude_code_cloud", "--profile", str(profile), "--event", event],
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    @asynccontextmanager
    async def _session(self, profile: Path):
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-c", "from vera_mmu.claude_code_cloud import claude_code_cloud_mcp_main; claude_code_cloud_mcp_main()", "--profile", str(profile)],
            env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
            cwd=str(ROOT),
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    @staticmethod
    def _payload(response):
        if not isinstance(response.structured_content, dict):
            raise AssertionError(f"Réponse MCP structurée absente : {response}")
        return response.structured_content

    async def test_i007_i011_stage_refuses_unconfirmed_and_writes_only_runtime(self) -> None:
        from vera_mmu.claude_code_cloud import ClaudeCodeCloudError, stage_claude_code_cloud_runtime

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = project / "project.yaml"
            profile.write_text(PROFILE, encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                CapabilityService(store).create(
                    "alpha-check", "Alpha", "CHECK", "1.0.0", parameter_schema={"type": "object", "additionalProperties": False}, metadata={}, actor="test"
                )
                CapabilityContractService(store).declare(
                    "alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type": "object", "additionalProperties": False}, actor="test"
                )
                CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                integration = compile_mcp_integration(store, manifest, instructions)
                hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
                review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
                lifecycle = compile_lifecycle_adapter_plan(
                    store, manifest, adapter_id="claude-code-local-v1", adapter_version="1.0.0", maximum_guard_mode="HARD"
                )
                local = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
                cloud = compile_claude_code_cloud_plan(store, manifest, instructions, integration, hooks, review, lifecycle, local)
                with self.assertRaises(ClaudeCodeCloudError):
                    stage_claude_code_cloud_runtime(store, manifest, instructions, integration, hooks, review, lifecycle, local, cloud, confirm=False)
                result = stage_claude_code_cloud_runtime(store, manifest, instructions, integration, hooks, review, lifecycle, local, cloud, confirm=True)
                self.assertEqual(result.status, "STAGED")
                self.assertTrue(result.state_path.is_file())
                self.assertFalse((project / ".claude").exists())
                self.assertFalse((project / ".mcp.json").exists())
                unchanged = stage_claude_code_cloud_runtime(store, manifest, instructions, integration, hooks, review, lifecycle, local, cloud, confirm=True)
                self.assertEqual(unchanged.status, "UNCHANGED")

    async def test_i007_i011_cloud_host_preview_is_deterministic_and_preserves_unrelated_entries(self) -> None:
        from vera_mmu.claude_code_cloud import preview_claude_code_cloud_host_config

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            existing_settings = {
                "hooks": {
                    "Stop": [
                        {
                            "hooks": [
                                {"command": "third-party-stop", "type": "command"}
                            ]
                        }
                    ]
                },
                "model": "claude-sonnet",
            }
            existing_mcp = {
                "mcpServers": {
                    "third-party": {"command": "third-party-mcp", "args": []}
                }
            }
            with MemoryStore.open(load_profile(profile), profile) as store:
                first = preview_claude_code_cloud_host_config(store, existing_settings, existing_mcp)
                second = preview_claude_code_cloud_host_config(store, existing_settings, existing_mcp)
            self.assertEqual(first, second)
            self.assertEqual(first.status, "PREVIEW")
            self.assertIn("third-party-stop", first.settings_json_text)
            self.assertIn("claude-sonnet", first.settings_json_text)
            self.assertIn("third-party-mcp", first.mcp_json_text)
            self.assertIn("vmmu-claude-code-cloud-hook", first.settings_json_text)
            self.assertIn("vmmu-claude-code-cloud-mcp", first.mcp_json_text)
            self.assertEqual(first.user_scope_status, "NOT_DELIVERED")
            self.assertFalse((project / ".claude").exists())
            self.assertFalse((project / ".mcp.json").exists())

    async def test_i007_i011_cloud_host_preview_refuses_conflicting_vera_entries(self) -> None:
        from vera_mmu.claude_code_cloud import ClaudeCodeCloudError, preview_claude_code_cloud_host_config

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            conflicting_settings = {
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "command": "vmmu-claude-code-cloud-hook --profile foreign.yaml --event SessionStart",
                                    "type": "command",
                                }
                            ]
                        }
                    ]
                }
            }
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(ClaudeCodeCloudError):
                    preview_claude_code_cloud_host_config(store, conflicting_settings, {})
            self.assertFalse((project / ".claude").exists())
            self.assertFalse((project / ".mcp.json").exists())

    async def test_i007_i011_cloud_host_preview_refuses_conflicting_vera_server(self) -> None:
        from vera_mmu.claude_code_cloud import ClaudeCodeCloudError, preview_claude_code_cloud_host_config

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            with MemoryStore.open(load_profile(profile), profile) as store:
                baseline = preview_claude_code_cloud_host_config(store, {}, {})
                server_id = next(iter(json.loads(baseline.mcp_json_text)["mcpServers"]))
                conflicting_mcp = {"mcpServers": {server_id: {"command": "foreign-mcp", "args": []}}}
                with self.assertRaises(ClaudeCodeCloudError):
                    preview_claude_code_cloud_host_config(store, {}, conflicting_mcp)
            self.assertFalse((project / ".claude").exists())
            self.assertFalse((project / ".mcp.json").exists())

    async def test_i007_i011_cloud_host_apply_refuses_symlinked_project_target(self) -> None:
        from vera_mmu.claude_code_cloud import ClaudeCodeCloudError, apply_claude_code_cloud_host_config, preview_claude_code_cloud_host_config

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            target = project / "outside-settings.json"
            target.write_text("{}", encoding="utf-8")
            (project / ".claude").mkdir()
            (project / ".claude" / "settings.json").symlink_to(target)
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(ClaudeCodeCloudError):
                    preview_claude_code_cloud_host_config(store, {}, {})
                with self.assertRaises(ClaudeCodeCloudError):
                    apply_claude_code_cloud_host_config(store, object(), confirm=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "{}")

    async def test_i007_i011_cloud_host_apply_requires_confirmation_and_never_targets_user_scope(self) -> None:
        from vera_mmu.claude_code_cloud import ClaudeCodeCloudError, apply_claude_code_cloud_host_config, preview_claude_code_cloud_host_config

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            with MemoryStore.open(load_profile(profile), profile) as store:
                preview = preview_claude_code_cloud_host_config(store, {}, {})
                with self.assertRaises(ClaudeCodeCloudError):
                    apply_claude_code_cloud_host_config(store, preview, confirm=False)
                result = apply_claude_code_cloud_host_config(store, preview, confirm=True)
            self.assertEqual(result.status, "APPLIED_PROJECT_LOCAL")
            self.assertEqual(result.settings_path, project.resolve() / ".claude" / "settings.json")
            self.assertEqual(result.mcp_path, project.resolve() / ".mcp.json")
            self.assertTrue(result.settings_path.is_file())
            self.assertTrue(result.mcp_path.is_file())
            self.assertTrue(result.state_path.is_file())
            self.assertNotIn(str(Path.home()), str(result.settings_path))
            self.assertNotIn(str(Path.home()), str(result.mcp_path))
            self.assertIn("vmmu-claude-code-cloud-hook", result.settings_path.read_text(encoding="utf-8"))
            self.assertIn("vmmu-claude-code-cloud-mcp", result.mcp_path.read_text(encoding="utf-8"))

    async def test_i007_i011_user_trust_preview_is_deterministic_and_preserves_settings(self) -> None:
        from vera_mmu.claude_code_cloud import (
            apply_claude_code_cloud_host_config,
            preview_claude_code_cloud_host_config,
            preview_claude_code_cloud_user_trust,
        )

        with TemporaryDirectory() as directory, TemporaryDirectory() as simulated_home:
            project = Path(directory)
            home = Path(simulated_home)
            profile = self._prepare(project)
            with patch.object(Path, "home", return_value=home):
                with MemoryStore.open(load_profile(profile), profile) as store:
                    project_preview = preview_claude_code_cloud_host_config(store, {}, {})
                    apply_claude_code_cloud_host_config(store, project_preview, confirm=True)
                    first = preview_claude_code_cloud_user_trust(store, {"theme": "dark", "enabledMcpjsonServers": ["other"]})
                    second = preview_claude_code_cloud_user_trust(store, {"theme": "dark", "enabledMcpjsonServers": ["other"]})
            self.assertEqual(first, second)
            self.assertEqual(first.status, "PREVIEW_USER_SCOPE")
            self.assertEqual(first.settings_path, home / ".claude" / "settings.json")
            merged = json.loads(first.settings_json_text)
            self.assertEqual(merged["theme"], "dark")
            self.assertEqual(merged["enabledMcpjsonServers"][0], "other")
            self.assertIn(first.server_id, merged["enabledMcpjsonServers"])
            self.assertFalse((home / ".claude").exists())

    async def test_i007_i011_user_trust_preview_refuses_missing_project_config_or_disabled_server(self) -> None:
        from vera_mmu.claude_code_cloud import (
            ClaudeCodeCloudError,
            apply_claude_code_cloud_host_config,
            preview_claude_code_cloud_host_config,
            preview_claude_code_cloud_user_trust,
        )

        with TemporaryDirectory() as directory, TemporaryDirectory() as simulated_home:
            project = Path(directory)
            profile = self._prepare(project)
            with patch.object(Path, "home", return_value=Path(simulated_home)):
                with MemoryStore.open(load_profile(profile), profile) as store:
                    with self.assertRaises(ClaudeCodeCloudError):
                        preview_claude_code_cloud_user_trust(store, {})
                    project_preview = preview_claude_code_cloud_host_config(store, {}, {})
                    apply_claude_code_cloud_host_config(store, project_preview, confirm=True)
                    server_id = preview_claude_code_cloud_user_trust(store, {}).server_id
                    with self.assertRaises(ClaudeCodeCloudError):
                        preview_claude_code_cloud_user_trust(store, {"disabledMcpjsonServers": [server_id]})

    async def test_i007_i011_user_trust_cli_preview_is_no_write(self) -> None:
        from vera_mmu.claude_code_cloud import (
            apply_claude_code_cloud_host_config,
            claude_code_cloud_config_main,
            preview_claude_code_cloud_host_config,
        )

        with TemporaryDirectory() as directory, TemporaryDirectory() as simulated_home:
            project = Path(directory)
            home = Path(simulated_home)
            profile = self._prepare(project)
            with MemoryStore.open(load_profile(profile), profile) as store:
                project_preview = preview_claude_code_cloud_host_config(store, {}, {})
                apply_claude_code_cloud_host_config(store, project_preview, confirm=True)
            output = io.StringIO()
            with patch.object(Path, "home", return_value=home), redirect_stdout(output):
                status = claude_code_cloud_config_main(["--profile", str(profile), "--preview-user-scope"])
            payload = json.loads(output.getvalue())
            self.assertEqual(status, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["status"], "PREVIEW_USER_SCOPE")
            self.assertEqual(payload["userScope"], "PREVIEW_ONLY")
            self.assertFalse((home / ".claude").exists())

    async def test_i007_i011_user_trust_apply_requires_two_confirmations_and_refuses_symlink(self) -> None:
        from vera_mmu.claude_code_cloud import (
            ClaudeCodeCloudError,
            apply_claude_code_cloud_host_config,
            apply_claude_code_cloud_user_trust,
            preview_claude_code_cloud_host_config,
            preview_claude_code_cloud_user_trust,
        )

        with TemporaryDirectory() as directory, TemporaryDirectory() as simulated_home:
            project = Path(directory)
            home = Path(simulated_home)
            profile = self._prepare(project)
            with patch.object(Path, "home", return_value=home):
                with MemoryStore.open(load_profile(profile), profile) as store:
                    project_preview = preview_claude_code_cloud_host_config(store, {}, {})
                    apply_claude_code_cloud_host_config(store, project_preview, confirm=True)
                    preview = preview_claude_code_cloud_user_trust(store, {})
                    with self.assertRaises(ClaudeCodeCloudError):
                        apply_claude_code_cloud_user_trust(store, preview, confirm_preview=False, confirm_user_scope=True)
                    with self.assertRaises(ClaudeCodeCloudError):
                        apply_claude_code_cloud_user_trust(store, preview, confirm_preview=True, confirm_user_scope=False)
                    result = apply_claude_code_cloud_user_trust(store, preview, confirm_preview=True, confirm_user_scope=True)
            self.assertEqual(result.status, "APPLIED_USER_SCOPE")
            self.assertEqual(result.settings_path, home / ".claude" / "settings.json")
            self.assertIn(result.server_id, json.loads(result.settings_path.read_text(encoding="utf-8"))["enabledMcpjsonServers"])

        with TemporaryDirectory() as directory, TemporaryDirectory() as simulated_home:
            project = Path(directory)
            home = Path(simulated_home)
            profile = self._prepare(project)
            (home / ".claude").mkdir()
            target = home / "outside.json"
            target.write_text("{}", encoding="utf-8")
            (home / ".claude" / "settings.json").symlink_to(target)
            with patch.object(Path, "home", return_value=home):
                with MemoryStore.open(load_profile(profile), profile) as store:
                    project_preview = preview_claude_code_cloud_host_config(store, {}, {})
                    apply_claude_code_cloud_host_config(store, project_preview, confirm=True)
                    with self.assertRaises(ClaudeCodeCloudError):
                        preview_claude_code_cloud_user_trust(store, {})
            self.assertEqual(target.read_text(encoding="utf-8"), "{}")

    async def test_hook_to_cloud_mcp_acknowledgement_to_pretool_allow(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            session_id = "cloud-mcp-session"
            started = self._hook(profile, "SessionStart", {"session_id": session_id, "cwd": str(project), "source": "startup"})
            self.assertIn("Resume Dossier", started["hookSpecificOutput"]["additionalContext"])
            denied = self._hook(profile, "PreToolUse", {"session_id": session_id, "cwd": str(project), "tool_name": "Read", "tool_input": {}})
            self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
            async with self._session(profile) as session:
                tools = await session.list_tools()
                acknowledgement = next(tool for tool in tools.tools if tool.name == "mmu_acknowledge_resume")
                self.assertEqual(set(acknowledgement.input_schema.get("properties", {})), {"sections"})
                result = self._payload(
                    await session.call_tool(
                        "mmu_acknowledge_resume",
                        {
                            "sections": {
                                "working-rules": "Mesurer les faits avant toute conclusion.",
                                "current-state": "La garde Claude cloud attend un acquittement.",
                            }
                        },
                    )
                )
                self.assertTrue(result["ok"])
                self.assertEqual(result["result"], {"acknowledged": True})
            allowed = self._hook(profile, "PreToolUse", {"session_id": session_id, "cwd": str(project), "tool_name": "Read", "tool_input": {}})
            self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])
            compacted = self._hook(profile, "PostCompact", {"session_id": session_id, "cwd": str(project)})
            self.assertIn("Resume Dossier", compacted["hookSpecificOutput"]["additionalContext"])
            rearmed = self._hook(profile, "PreToolUse", {"session_id": session_id, "cwd": str(project), "tool_name": "Read", "tool_input": {}})
            self.assertEqual(rearmed["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
