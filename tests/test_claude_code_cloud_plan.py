from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.claude_code_integration import compile_claude_code_integration_plan
from vera_mmu.claude_code_local import compile_claude_code_local_plan
from vera_mmu.identity import load_profile
from vera_mmu.lifecycle_adapters import compile_lifecycle_adapter_plan
from vera_mmu.mcp_hooks import compile_mcp_hook_plan
from vera_mmu.mcp_instructions import compile_mcp_instructions
from vera_mmu.mcp_integration import compile_mcp_integration
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "claude-cloud-project"
  name: "Claude Cloud Project"
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


class ClaudeCodeCloudPlanTests(unittest.TestCase):
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

    @staticmethod
    def _snapshots(store: MemoryStore, *, adapter_bindings: dict[str, str] | None = None):
        manifest = compile_mcp_manifest(
            store,
            adapter_bindings=adapter_bindings or {"alpha-check": "adapter-alpha-v1"},
        )
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
        local = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
        return manifest, instructions, integration, hooks, review, lifecycle, local

    def _cloud_plan(self, store: MemoryStore):
        from vera_mmu.claude_code_cloud import compile_claude_code_cloud_plan

        snapshots = self._snapshots(store)
        return snapshots, compile_claude_code_cloud_plan(store, *snapshots)

    def test_i007_i011_i012_compiles_stable_preinstalled_cloud_plan_without_secret_or_network(self) -> None:
        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                snapshots, first = self._cloud_plan(store)
                _, second = self._cloud_plan(store)
                self.assertEqual(first, second)
                self.assertEqual(first.format, "vera-claude-code-cloud/v1")
                self.assertEqual(first.project_id, store.identity.project_id)
                self.assertEqual(first.mcp_build_hash, snapshots[0].mcp_build_hash)
                self.assertEqual(first.local_plan_hash, snapshots[-1].plan_hash)
                self.assertEqual(len(first.plan_hash), 64)
                payload = json.loads(first.json_text)["claudeCodeCloud"]
                self.assertEqual(payload["runtime"], {"network": "FORBIDDEN", "provider": "PREINSTALLED_VERA"})
                self.assertEqual(payload["trust"], {"mode": "PREVIEW_ONLY", "target": "$HOME/.claude/settings.json"})
                self.assertEqual(payload["secrets"], {"mode": "EXTERNAL_ONLY", "requirements": []})
                self.assertEqual(payload["mcpServer"]["command"], "vmmu-claude-code-cloud-mcp")
                self.assertNotIn("ARET", first.json_text)
                self.assertNotIn("pip", first.json_text.lower())
                self.assertNotIn("curl", first.json_text.lower())
                self.assertNotIn("hmac", first.json_text.lower())

    def test_i011_refuses_stale_snapshot_and_non_preinstalled_provider(self) -> None:
        from vera_mmu.claude_code_cloud import ClaudeCodeCloudError, compile_claude_code_cloud_plan

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                snapshots, _ = self._cloud_plan(store)
                self._declare(store, "beta-check")
                with self.assertRaises(ClaudeCodeCloudError):
                    compile_claude_code_cloud_plan(store, *snapshots)
                with self.assertRaises(ClaudeCodeCloudError):
                    compile_claude_code_cloud_plan(
                        store,
                        *self._snapshots(
                            store,
                            adapter_bindings={
                                "alpha-check": "adapter-alpha-v1",
                                "beta-check": "adapter-beta-v1",
                            },
                        ),
                        runtime_provider="NETWORK_BOOTSTRAP",
                    )

    def test_i014_doctor_is_observational_and_never_promotes_pending_disabled_or_missing_runtime(self) -> None:
        from vera_mmu.claude_code_cloud import ClaudeCodeCloudObservation, inspect_claude_code_cloud

        with TemporaryDirectory() as directory:
            project = Path(directory)
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                snapshots, plan = self._cloud_plan(store)
                before = sorted(path.relative_to(project).as_posix() for path in project.rglob("*"))
                missing = inspect_claude_code_cloud(
                    store,
                    *snapshots,
                    plan,
                    observation=ClaudeCodeCloudObservation("CLAUDE_CODE_CLOUD", "TRUST_PENDING"),
                    command_lookup=lambda _: None,
                )
                self.assertEqual(missing.status, "RUNTIME_MISSING")
                self.assertEqual(missing.install_actions, ())
                pending = inspect_claude_code_cloud(
                    store,
                    *snapshots,
                    plan,
                    observation=ClaudeCodeCloudObservation("CLAUDE_CODE_CLOUD", "TRUST_PENDING"),
                    command_lookup=lambda _: "/usr/bin/true",
                )
                self.assertEqual(pending.status, "TRUST_PENDING")
                disabled = inspect_claude_code_cloud(
                    store,
                    *snapshots,
                    plan,
                    observation=ClaudeCodeCloudObservation("CLAUDE_CODE_CLOUD", "DISABLED"),
                    command_lookup=lambda _: "/usr/bin/true",
                )
                self.assertEqual(disabled.status, "DISABLED")
                ready = inspect_claude_code_cloud(
                    store,
                    *snapshots,
                    plan,
                    observation=ClaudeCodeCloudObservation("CLAUDE_CODE_CLOUD", "TRUSTED"),
                    command_lookup=lambda _: "/usr/bin/true",
                )
                self.assertEqual(ready.status, "RUNTIME_READY")
                self.assertEqual(ready.install_actions, ())
                after = sorted(path.relative_to(project).as_posix() for path in project.rglob("*"))
                self.assertEqual(before, after)

    def test_i014_refuses_invalid_or_non_cloud_observation(self) -> None:
        from vera_mmu.claude_code_cloud import ClaudeCodeCloudError, ClaudeCodeCloudObservation, inspect_claude_code_cloud

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                snapshots, plan = self._cloud_plan(store)
                with self.assertRaises(ClaudeCodeCloudError):
                    inspect_claude_code_cloud(
                        store,
                        *snapshots,
                        plan,
                        observation=ClaudeCodeCloudObservation("LOCAL", "TRUSTED"),
                        command_lookup=lambda _: "/usr/bin/true",
                    )
                with self.assertRaises(ClaudeCodeCloudError):
                    inspect_claude_code_cloud(
                        store,
                        *snapshots,
                        plan,
                        observation=ClaudeCodeCloudObservation("CLAUDE_CODE_CLOUD", "READY"),
                        command_lookup=lambda _: "/usr/bin/true",
                    )


if __name__ == "__main__":
    unittest.main()
