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
            self.assertIn("python", {item["marker"] for item in observations if item["kind"] == "dependency-manager"})
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

    def test_project_doctor_is_read_only_and_reports_profile_migration_check(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            preview = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "doctor-bridge", "projectName": "Doctor Bridge"})
            applied = self._call(bridge, "project.init.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": True})  # type: ignore[index]
            self.assertTrue(applied["ok"])
            response = self._call(bridge, "project.doctor", {})
            self.assertTrue(response["ok"])
            checks = response["result"]["checks"]  # type: ignore[index]
            self.assertIn("profile_migration", {item["name"] for item in checks})
            self.assertFalse(list(root.glob(".vera-profile-migration-*.json")))

    def test_migration_status_is_read_only_and_reports_empty_queue(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            preview = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "migration-bridge", "projectName": "Migration Bridge"})
            applied = self._call(bridge, "project.init.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": True})  # type: ignore[index]
            self.assertTrue(applied["ok"])
            response = self._call(bridge, "migration.status", {})
            self.assertTrue(response["ok"])
            self.assertEqual(response["result"]["status"], "NO_PENDING_MIGRATION")  # type: ignore[index]
            self.assertEqual(response["result"]["mutation"], "NONE")  # type: ignore[index]
            self.assertFalse(list(root.glob(".vera-profile-migration-*.json")))

    def test_profile_at_project_root_can_open_dashboard_status(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            content = "mmu:\n  version: '2.0'\nproject:\n  id: 'root-profile'\n  name: 'Root Profile'\n  domain: 'generic'\nworkspace:\n  root: '.'\nstorage:\n  memory_dir: '.vera-mmu'\n  sqlite_file: 'memory.sqlite'\n  artifacts_dir: 'artifacts'\n"
            profile = root / "project.yaml"
            profile.write_text(content, encoding="utf-8")
            response = self._call(self._bridge(root), "project.status", {})
            self.assertTrue(response["ok"])
            self.assertEqual(response["result"]["coverage"]["project_identity"]["project_id"], "root-profile")  # type: ignore[index]

    def test_profile_discovery_refuses_competing_canonical_locations(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / ".vera-mmu"
            runtime.mkdir()
            content = "mmu:\n  version: '2.0'\nproject:\n  id: 'dual-profile'\n  name: 'Dual'\n  domain: 'generic'\nworkspace:\n  root: '.'\nstorage:\n  memory_dir: '.vera-mmu'\n  sqlite_file: 'memory.sqlite'\n  artifacts_dir: 'artifacts'\n"
            (runtime / "project.yaml").write_text(content, encoding="utf-8")
            (root / "project.yaml").write_text(content, encoding="utf-8")
            response = self._call(self._bridge(root), "project.status", {})
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "OPERATION_REFUSED")  # type: ignore[index]

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

    def test_m11db_profile_rebind_requires_closed_preview_and_confirmation(self) -> None:
        from vera_mmu.identity import load_profile
        from vera_mmu.store import MemoryStore

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            init = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "profile-rebind", "projectName": "Initial profile"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": init["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]
            profile = root / ".vera-mmu" / "project.yaml"
            with MemoryStore.open(load_profile(profile), profile):
                pass
            injected = self._call(bridge, "profile.rebind.preview", {"projectId": "profile-rebind", "projectName": "Rebound profile", "projectDomain": "software", "projectDescription": "Confirmed rebind", "storage": "unsafe"})
            self.assertFalse(injected["ok"])
            self.assertEqual(injected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            preview = self._call(bridge, "profile.rebind.preview", {"projectId": "profile-rebind-next", "projectName": "Rebound profile", "projectDomain": "documentation", "projectDescription": "Confirmed rebind"})
            self.assertTrue(preview["ok"])
            preview_hash = preview["result"]["preview_hash"]  # type: ignore[index]
            refused = self._call(bridge, "profile.rebind.apply", {"previewHash": preview_hash, "confirm": False})
            self.assertFalse(refused["ok"])
            self.assertEqual(refused["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            applied = self._call(bridge, "profile.rebind.apply", {"previewHash": preview_hash, "confirm": True})
            self.assertTrue(applied["ok"])
            self.assertEqual(applied["result"]["status"], "REBOUND")  # type: ignore[index]
            with MemoryStore.open(load_profile(profile), profile) as store:
                self.assertEqual(store.metadata()["project_identity"], store.identity.as_dict())

    def test_m11d_doctor_recovery_requires_closed_preview_and_confirmation(self) -> None:
        from unittest.mock import patch
        from vera_mmu.identity import load_profile
        from vera_mmu.profile_rebind import apply_project_profile_rebind, preview_project_profile_rebind
        from vera_mmu.store import MemoryStore

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            init = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "recovery-profile", "projectName": "Recovery profile"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": init["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]
            profile = root / ".vera-mmu" / "project.yaml"
            with MemoryStore.open(load_profile(profile), profile):
                pass
            preview = preview_project_profile_rebind(profile, project_name="Interrupted profile", project_description="Interrupted deliberately")
            with patch("vera_mmu.profile_rebind._write_atomic", side_effect=OSError("simulated interruption")):
                with self.assertRaises(OSError):
                    apply_project_profile_rebind(profile, preview, confirm=True)
            injected = self._call(bridge, "profile.rebind.recovery.preview", {"previewHash": "untrusted"})
            self.assertFalse(injected["ok"])
            self.assertEqual(injected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            recovery = self._call(bridge, "profile.rebind.recovery.preview", {})
            self.assertTrue(recovery["ok"])
            recovery_hash = recovery["result"]["preview_hash"]  # type: ignore[index]
            refused = self._call(bridge, "profile.rebind.recovery.apply", {"previewHash": recovery_hash, "confirm": False})
            self.assertFalse(refused["ok"])
            self.assertEqual(refused["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            recovered = self._call(bridge, "profile.rebind.recovery.apply", {"previewHash": recovery_hash, "confirm": True})
            self.assertTrue(recovered["ok"])
            self.assertEqual(recovered["result"]["status"], "RECOVERED")  # type: ignore[index]

    def test_m11dc_capability_contract_requires_closed_preview_and_confirmation(self) -> None:
        """The full §32 contract crosses the bridge; a command field never does."""
        contract = {
            "identifier": "lint", "name": "Lint", "description": "Contrôle de style déclaré.",
            "kind": "COLLECTOR", "version": "1.0.0", "runner": "NOOP", "policy": "READ_ONLY",
            "timeoutSeconds": 60, "inputs": ["tool"], "outputs": ["verdict"], "artifacts": [],
            "validator": "EVIDENCE_FIELDS", "yieldsProof": False, "confirmationRequired": False,
            "gateBacked": True,
        }
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            preview = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "builder-desktop", "projectName": "Builder desktop"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]
            options = self._call(bridge, "capability.options", {})
            self.assertEqual(options["result"]["command"]["status"], "NOT_APPLICABLE")  # type: ignore[index]
            rejected = self._call(bridge, "capability.preview", {**contract, "command": "unsafe"})
            self.assertFalse(rejected["ok"])
            self.assertEqual(rejected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            incomplete = self._call(bridge, "capability.preview", {key: value for key, value in contract.items() if key != "timeoutSeconds"})
            self.assertFalse(incomplete["ok"])
            self.assertEqual(incomplete["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            network = self._call(bridge, "capability.preview", {**contract, "policy": "NETWORK"})
            self.assertTrue(network["ok"])
            self.assertEqual(network["result"]["status"], "REFUSED")  # type: ignore[index]
            self.assertEqual([item["code"] for item in network["result"]["refusals"]], ["NETWORK_WITHOUT_POLICY"])  # type: ignore[index]
            draft = self._call(bridge, "capability.preview", contract)
            self.assertTrue(draft["ok"])
            self.assertEqual(draft["result"]["contract"]["command"]["status"], "NOT_APPLICABLE")  # type: ignore[index]
            refused = self._call(bridge, "capability.apply", {"previewHash": draft["result"]["preview_hash"], "confirm": False})  # type: ignore[index]
            self.assertFalse(refused["ok"])
            self.assertEqual(refused["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            applied = self._call(bridge, "capability.apply", {"previewHash": draft["result"]["preview_hash"], "confirm": True})  # type: ignore[index]
            self.assertTrue(applied["ok"])
            self.assertEqual(applied["result"]["identifier"], "lint")  # type: ignore[index]
            self.assertEqual(applied["result"]["materialization"]["status"], "PENDING")  # type: ignore[index]

    def test_i013_policy_editor_reports_enforcement_and_refuses_what_the_core_cannot_honour(self) -> None:
        """The policy file was declared everywhere and editable by nothing; the bridge reaches it."""
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            init = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "policy-desktop", "projectName": "Policy desktop"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": init["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]
            options = self._call(bridge, "policy.options", {})
            self.assertTrue(options["ok"])
            enforcement = {f"{item['section']}.{item['key']}": item["enforcement"] for item in options["result"]["lines"]}  # type: ignore[index]
            self.assertEqual(enforcement["filesystem.write"], "ENFORCED")
            self.assertEqual(enforcement["filesystem.read"], "DECLARED_ONLY")
            injected = self._call(bridge, "policy.preview", {"changes": {"filesystem.write": "deny"}, "confirm": True})
            self.assertFalse(injected["ok"])
            self.assertEqual(injected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            empty = self._call(bridge, "policy.preview", {"changes": {}})
            self.assertFalse(empty["ok"])
            self.assertEqual(empty["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            network = self._call(bridge, "policy.preview", {"changes": {"network.default": "allow"}})
            self.assertTrue(network["ok"])
            self.assertEqual(network["result"]["status"], "REFUSED")  # type: ignore[index]
            preview = self._call(bridge, "policy.preview", {"changes": {"git.push": "deny"}})
            self.assertTrue(preview["ok"])
            refused = self._call(bridge, "policy.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": False})  # type: ignore[index]
            self.assertFalse(refused["ok"])
            self.assertEqual(refused["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            applied = self._call(bridge, "policy.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": True})  # type: ignore[index]
            self.assertTrue(applied["ok"])
            self.assertEqual(applied["result"]["status"], "APPLIED")  # type: ignore[index]

    def test_i009_resume_editor_reports_what_it_invalidates_and_reaches_step_thirteen(self) -> None:
        """`integrations.enabled` gated the journey's step 13 and nothing could write it."""
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            init = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "resume-desktop", "projectName": "Resume desktop"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": init["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]
            options = self._call(bridge, "resume.options", {})
            self.assertTrue(options["ok"])
            self.assertEqual(options["result"]["integrations"]["enabled"], [])  # type: ignore[index]
            self.assertIn("generic-mcp", options["result"]["integrations"]["available"])  # type: ignore[index]
            injected = self._call(bridge, "resume.preview", {"integrations": ["generic-mcp"], "confirm": True})
            self.assertFalse(injected["ok"])
            self.assertEqual(injected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            unknown = self._call(bridge, "resume.preview", {"template": None, "sections": None, "maxResumeBytes": None, "integrations": ["nowhere"]})
            self.assertTrue(unknown["ok"])
            self.assertEqual([item["code"] for item in unknown["result"]["refusals"]], ["INTEGRATION_UNDECLARED"])  # type: ignore[index]
            preview = self._call(bridge, "resume.preview", {"template": None, "sections": None, "maxResumeBytes": None, "integrations": ["generic-mcp"]})
            self.assertTrue(preview["ok"])
            # Nothing is armed on a fresh project, and the payload says so rather than staying silent.
            self.assertEqual(preview["result"]["invalidates"], [])  # type: ignore[index]
            refused = self._call(bridge, "resume.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": False})  # type: ignore[index]
            self.assertFalse(refused["ok"])
            self.assertEqual(refused["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            applied = self._call(bridge, "resume.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": True})  # type: ignore[index]
            self.assertTrue(applied["ok"])
            self.assertEqual(applied["result"]["integrations"], ["generic-mcp"])  # type: ignore[index]
            journey = self._call(bridge, "wizard.state", {})
            steps = {item["id"]: item["state"] for item in journey["result"]["steps"]}  # type: ignore[index]
            self.assertEqual(steps["choose-integrations"], "COMPLETED")

    def test_b11_the_bridge_serves_the_journey_s_conclusion_without_writing(self) -> None:
        """The console's own route to steps 15 to 18, and its refusal to guess them early."""
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            init = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "journey-bridge", "projectName": "Journey bridge"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": init["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]

            outcome = self._call(bridge, "journey.outcome", {})
            self.assertTrue(outcome["ok"])
            result = outcome["result"]  # type: ignore[index]
            self.assertEqual(result["format"], "vera-journey-outcome/v1")
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertEqual(result["doctor"]["status"], "NOT_REACHED")
            self.assertEqual(result["mutation"], "NONE")

            rejected = self._call(bridge, "journey.outcome", {"root": str(root)})
            self.assertFalse(rejected["ok"])
            self.assertEqual(rejected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]

    def test_b12_the_bridge_reads_the_taxonomy_before_it_is_asked_to_edit_it(self) -> None:
        """The read the taxonomy editor shipped without, now the console's own route to steps 5-7."""
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            init = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "taxonomy-bridge", "projectName": "Taxonomy bridge"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": init["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]

            options = self._call(bridge, "taxonomy.options", {})
            self.assertTrue(options["ok"])
            sections = options["result"]["sections"]  # type: ignore[index]
            self.assertEqual(set(sections), {"knowledge", "entities", "relations"})
            self.assertTrue(sections["knowledge"]["declared"])
            self.assertEqual(set(sections["knowledge"]["usage"]), set(sections["knowledge"]["declared"]))

            # The edit the console can now plan from what it just read.
            declared = list(sections["knowledge"]["declared"])
            preview = self._call(bridge, "taxonomy.preview", {"knowledgeTypes": declared + ["NOUVEAU"], "entityTypes": None, "relationTypes": None})
            self.assertTrue(preview["ok"])
            self.assertEqual(preview["result"]["status"], "PREVIEW")  # type: ignore[index]
            refused = self._call(bridge, "taxonomy.apply", {"previewHash": preview["result"]["preview_hash"], "confirm": False})  # type: ignore[index]
            self.assertEqual(refused["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]

    def test_m11dd2_gate_structure_builder_requires_cached_preview_and_confirmation(self) -> None:
        from vera_mmu.capabilities import CapabilityService
        from vera_mmu.capability_contracts import CapabilityContractService
        from vera_mmu.capability_policies import CapabilityPolicyService
        from vera_mmu.evidence import EvidenceService
        from vera_mmu.executions import ExecutionService
        from vera_mmu.identity import load_profile
        from vera_mmu.store import MemoryStore
        from vera_mmu.work_items import WorkItemService

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = self._bridge(root)
            init = self._call(bridge, "project.init.preview", {"template": "software", "projectId": "gate-structure", "projectName": "Gate structure"})
            self.assertTrue(self._call(bridge, "project.init.apply", {"previewHash": init["result"]["preview_hash"], "confirm": True})["ok"])  # type: ignore[index]
            profile = root / ".vera-mmu" / "project.yaml"
            with MemoryStore.open(load_profile(profile), profile) as store:
                CapabilityService(store).create("source", "Source", "CHECK", "1.0.0")
                CapabilityContractService(store).declare("source", "NOOP", "DENY_NETWORK", 30)
                CapabilityPolicyService(store).declare("source", "ALLOW", "test")
                ExecutionService(store).run_noop("execution", "source", {})
                for evidence_id in ("e1", "e2"):
                    EvidenceService(store).record(evidence_id, "execution", "TEST_PROOF", "PASS", {"evidence": evidence_id})
                WorkItemService(store).create("dashboard-gate", "SUBTASK", "Dashboard gate")
            injected = self._call(bridge, "gate.structure.preview", {"gateId": "dashboard-gate", "workItemId": "dashboard-gate", "primaryEvidenceId": "e1", "requirementEvidenceIds": ["e2"], "verdict": "PASS"})
            self.assertFalse(injected["ok"])
            self.assertEqual(injected["error"]["code"], "INPUT_INVALID")  # type: ignore[index]
            preview = self._call(bridge, "gate.structure.preview", {"gateId": "dashboard-gate", "workItemId": "dashboard-gate", "primaryEvidenceId": "e1", "requirementEvidenceIds": ["e2"]})
            self.assertTrue(preview["ok"])
            # §33: the classes cross the bridge with the structure, before the gate exists.
            self.assertEqual([item["evidence_class"] for item in preview["result"]["endpoints"]], ["TECHNICAL_VALIDATION", "TECHNICAL_VALIDATION"])  # type: ignore[index]
            self.assertTrue(preview["result"]["promotion"]["can_create_proof"])  # type: ignore[index]
            preview_hash = preview["result"]["preview_hash"]  # type: ignore[index]
            refused = self._call(bridge, "gate.structure.apply", {"previewHash": preview_hash, "confirm": False})
            self.assertFalse(refused["ok"])
            self.assertEqual(refused["error"]["code"], "CONFIRMATION_REQUIRED")  # type: ignore[index]
            applied = self._call(bridge, "gate.structure.apply", {"previewHash": preview_hash, "confirm": True})
            self.assertTrue(applied["ok"])
            self.assertEqual(applied["result"]["status"], "DECLARED")  # type: ignore[index]
            report = self._call(bridge, "gate.report", {"gateId": "dashboard-gate"})
            self.assertTrue(report["ok"])
            self.assertEqual(report["result"]["capability"], {"status": "DERIVED", "capability_id": "source"})  # type: ignore[index]
            self.assertEqual({item["evidence_class"] for item in report["result"]["requirements"]}, {"TECHNICAL_VALIDATION"})  # type: ignore[index]
            self.assertTrue(report["result"]["promotion"]["can_create_proof"])  # type: ignore[index]
            absent = self._call(bridge, "gate.report", {"gateId": "nowhere"})
            self.assertFalse(absent["ok"])
            self.assertEqual(absent["error"]["code"], "OPERATION_REFUSED")  # type: ignore[index]

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
