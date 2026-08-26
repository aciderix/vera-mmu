from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.claude_code_integration import compile_claude_code_integration_plan
from vera_mmu.identity import load_profile
from vera_mmu.lifecycle_adapters import compile_lifecycle_adapter_plan
from vera_mmu.mcp_hooks import compile_mcp_hook_plan
from vera_mmu.mcp_instructions import compile_mcp_instructions
from vera_mmu.mcp_integration import compile_mcp_integration
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.session_lifecycle import ResumeGuardService
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "claude-local-project"
  name: "Claude Local Project"
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


class ClaudeCodeLocalAdapterTests(unittest.TestCase):
    def _store(self, directory: Path) -> MemoryStore:
        profile_path = directory / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    @staticmethod
    def _declare(store: MemoryStore, identifier: str) -> None:
        CapabilityService(store).create(
            identifier,
            f"Check {identifier}",
            "CHECK",
            "1.0.0",
            parameter_schema={"type": "object", "additionalProperties": False},
            metadata={},
            actor="test",
        )
        CapabilityContractService(store).declare(
            identifier,
            "OBSERVED_PROCESS",
            "DENY_NETWORK",
            30,
            parameter_schema={"type": "object", "additionalProperties": False},
            actor="test",
        )
        CapabilityPolicyService(store).declare(identifier, "ALLOW", "test", actor="test")

    def _snapshots(self, store: MemoryStore):
        manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
        instructions = compile_mcp_instructions(store, manifest)
        integration = compile_mcp_integration(store, manifest, instructions)
        hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
        review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
        lifecycle = compile_lifecycle_adapter_plan(
            store,
            manifest,
            adapter_id="claude-code-local-v1",
            adapter_version="1.0.0",
            maximum_guard_mode="HARD",
        )
        return manifest, instructions, integration, hooks, review, lifecycle

    def _local_plan(self, store: MemoryStore):
        from vera_mmu.claude_code_local import compile_claude_code_local_plan

        snapshots = self._snapshots(store)
        return snapshots, compile_claude_code_local_plan(store, *snapshots)

    def test_i007_i011_i012_compiles_stable_attested_local_plan(self) -> None:
        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                snapshots, first = self._local_plan(store)
                _, second = self._local_plan(store)
                self.assertEqual(first, second)
                self.assertEqual(first.format, "vera-claude-code-local/v1")
                self.assertEqual(first.project_id, store.identity.project_id)
                self.assertEqual(first.mcp_build_hash, snapshots[0].mcp_build_hash)
                self.assertEqual(first.lifecycle_plan_hash, snapshots[-1].lifecycle_plan_hash)
                self.assertEqual(len(first.plan_hash), 64)
                payload = json.loads(first.json_text)["claudeCodeLocal"]
                self.assertEqual(payload["installation"]["mode"], "OPT_IN")
                self.assertEqual(payload["installation"]["settingsTarget"], ".claude/settings.json")
                self.assertEqual(payload["mcpServer"]["command"], "vmmu-claude-code-local-mcp")
                self.assertEqual(set(payload["hooks"]), {"SessionStart", "PreToolUse", "PostToolUse", "PreCompact", "PostCompact", "Stop"})
                self.assertNotIn("ARET", first.json_text)
                self.assertNotIn("pip", first.json_text)
                self.assertNotIn("http", first.json_text.lower())

    def test_i011_refuses_stale_plan_or_snapshot(self) -> None:
        from vera_mmu.claude_code_local import ClaudeCodeLocalError, compile_claude_code_local_plan

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                snapshots, _ = self._local_plan(store)
                self._declare(store, "beta-check")
                with self.assertRaises(ClaudeCodeLocalError):
                    compile_claude_code_local_plan(store, *snapshots)

    def test_i007_i008_hook_handler_arms_blocks_and_preserves_session_scope(self) -> None:
        from vera_mmu.claude_code_local import ClaudeCodeLocalError, handle_claude_code_local_hook

        with TemporaryDirectory() as directory:
            project = Path(directory)
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                snapshots, plan = self._local_plan(store)
                start = handle_claude_code_local_hook(
                    store, snapshots[-1], plan, "SessionStart", {"session_id": "local-session-a", "cwd": str(project), "source": "startup"}
                )
                context = start["hookSpecificOutput"]["additionalContext"]
                self.assertIn("Resume Dossier", context)
                denied = handle_claude_code_local_hook(
                    store,
                    snapshots[-1],
                    plan,
                    "PreToolUse",
                    {"session_id": "local-session-a", "cwd": str(project), "tool_name": "Read", "tool_input": {}},
                )
                self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
                ack_tool = f"mcp__vera-mmu-{store.identity.project_id}__mmu_acknowledge_resume"
                excepted = handle_claude_code_local_hook(
                    store,
                    snapshots[-1],
                    plan,
                    "PreToolUse",
                    {"session_id": "local-session-a", "cwd": str(project), "tool_name": ack_tool, "tool_input": {}},
                )
                self.assertNotIn("permissionDecision", excepted["hookSpecificOutput"])
                self.assertTrue(
                    ResumeGuardService(store).acknowledge_current(
                        "local-session-a",
                        "claude-code-local-v1",
                        {
                            "working-rules": "Mesurer les faits avant toute conclusion.",
                            "current-state": "La garde Claude locale attend un acquittement.",
                        },
                    )
                )
                allowed = handle_claude_code_local_hook(
                    store,
                    snapshots[-1],
                    plan,
                    "PreToolUse",
                    {"session_id": "local-session-a", "cwd": str(project), "tool_name": "Read", "tool_input": {}},
                )
                self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])
                prepared = handle_claude_code_local_hook(
                    store, snapshots[-1], plan, "PreCompact", {"session_id": "local-session-a", "cwd": str(project)}
                )
                self.assertIn("prépare", prepared["hookSpecificOutput"]["additionalContext"])
                denied_after_prepare = handle_claude_code_local_hook(
                    store, snapshots[-1], plan, "PreToolUse", {"session_id": "local-session-a", "cwd": str(project), "tool_name": "Read", "tool_input": {}}
                )
                self.assertEqual(denied_after_prepare["hookSpecificOutput"]["permissionDecision"], "deny")
                restored = handle_claude_code_local_hook(
                    store, snapshots[-1], plan, "PostCompact", {"session_id": "local-session-a", "cwd": str(project)}
                )
                self.assertIn("Resume Dossier", restored["hookSpecificOutput"]["additionalContext"])
                with self.assertRaises(ClaudeCodeLocalError):
                    handle_claude_code_local_hook(
                        store, snapshots[-1], plan, "SessionStart", {"session_id": "local-session-b", "cwd": str(project), "source": "startup"}
                    )

    def test_i008_install_is_confirmed_merged_idempotent_and_refuses_conflict_or_symlink(self) -> None:
        from vera_mmu.claude_code_local import ClaudeCodeLocalError, install_claude_code_local

        with TemporaryDirectory() as directory:
            project = Path(directory)
            settings_path = project / ".claude" / "settings.json"
            settings_path.parent.mkdir()
            settings_path.write_text(json.dumps({"retained": {"x": 1}, "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "other-stop"}]}]}}), encoding="utf-8")
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                snapshots, plan = self._local_plan(store)
                with self.assertRaises(ClaudeCodeLocalError):
                    install_claude_code_local(store, *snapshots, plan, confirm=False)
                self.assertFalse((project / ".mcp.json").exists())
                first = install_claude_code_local(store, *snapshots, plan, confirm=True)
                self.assertEqual(first.status, "INSTALLED")
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
                self.assertEqual(settings["retained"], {"x": 1})
                self.assertEqual(len(settings["hooks"]["Stop"]), 2)
                self.assertIn("mcpServers", json.loads((project / ".mcp.json").read_text(encoding="utf-8")))
                settings_before = settings_path.read_bytes()
                mcp_before = (project / ".mcp.json").read_bytes()
                second = install_claude_code_local(store, *snapshots, plan, confirm=True)
                self.assertEqual(second.status, "UNCHANGED")
                self.assertEqual(settings_before, settings_path.read_bytes())
                self.assertEqual(mcp_before, (project / ".mcp.json").read_bytes())
            settings_path.unlink()
            outside = project / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            settings_path.symlink_to(outside)
            with self._store(project) as store:
                snapshots, plan = self._local_plan(store)
                with self.assertRaises(ClaudeCodeLocalError):
                    install_claude_code_local(store, *snapshots, plan, confirm=True)
            self.assertEqual(outside.read_text(encoding="utf-8"), "{}")

    def test_i014_doctor_is_observational_and_never_promotes_missing_or_conflict(self) -> None:
        from vera_mmu.claude_code_local import inspect_claude_code_local, install_claude_code_local

        with TemporaryDirectory() as directory:
            project = Path(directory)
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                snapshots, plan = self._local_plan(store)
                missing = inspect_claude_code_local(store, *snapshots, plan, command_lookup=lambda _: None)
                self.assertEqual(missing.status, "NOT_INSTALLED")
                self.assertEqual(missing.install_actions, ())
                self.assertFalse((project / ".claude").exists())
                self.assertFalse((project / ".vera-mmu" / "generated" / "claude-code-local-install.json").exists())
                install_claude_code_local(store, *snapshots, plan, confirm=True)
                degraded = inspect_claude_code_local(store, *snapshots, plan, command_lookup=lambda _: None)
                self.assertEqual(degraded.status, "DEGRADED")
                ready = inspect_claude_code_local(store, *snapshots, plan, command_lookup=lambda _: "/usr/bin/true")
                self.assertEqual(ready.status, "READY")
                self.assertEqual(ready.install_actions, ())


if __name__ == "__main__":
    unittest.main()
