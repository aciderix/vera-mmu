"""The complete capability contract of §32, and the seven refusals it requires.

Each refusal is proven twice where the difference matters: once through the builder, which is what
a screen calls, and once against the declarative catalogue itself, which is what the Core loads.
The second proof is the one that counts — a rule held only by the builder would stop existing the
moment anything else wrote `capabilities.yaml`.
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import yaml

from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization


BASE = {
    "id": "lint-report",
    "name": "Rapport de lint",
    "description": "Enregistre le résultat déclaré d’un contrôle de style.",
    "kind": "COLLECTOR",
    "version": "1.0.0",
    "runner": "NOOP",
    "policy": "READ_ONLY",
    "timeout_seconds": 60,
    "inputs": ["tool", "findings"],
    "outputs": ["verdict"],
    "artifacts": ["lint/report.json"],
    "validator": "EVIDENCE_FIELDS",
    "yields_proof": False,
    "confirmation_required": False,
    "gate_backed": True,
}


class CapabilityContractBuilderTests(unittest.TestCase):
    def _project(self, root: Path, template: str = "software") -> Path:
        preview = preview_project_initialization(root, template=template, project_id="contract-app", project_name="Contract App")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    def _catalog(self, profile: Path) -> dict:
        return yaml.safe_load((profile.parent / "capabilities.yaml").read_text(encoding="utf-8"))

    def _write_catalog(self, profile: Path, capability: dict) -> None:
        """Bypass the builder entirely and write the declaration by hand, as a person could."""
        entry = {key: value for key, value in capability.items() if key != "gate_backed"}
        entry.setdefault("network_policy", "DENY_NETWORK")
        entry.setdefault(
            "parameter_schema",
            {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
        )
        (profile.parent / "capabilities.yaml").write_text(
            json.dumps({"format": "vera-capability-catalog/v1", "capabilities": [entry]}) + "\n", encoding="utf-8"
        )

    def _assert_catalog_refused(self, profile: Path, capability: dict) -> None:
        """Write the declaration straight into the catalogue, and require the Core to refuse it.

        The gate catalogue is emptied for the duration. Leaving the template's gates in place would
        make every one of these refusals pass for the wrong reason — the gates reference the
        capabilities this helper just replaced, so the loader would stop on a dangling gate before
        ever reading the rule under test. It did exactly that until a mutation check showed six of
        these assertions surviving the removal of the rule they were meant to prove.
        """
        from vera_mmu.project_catalogs import ProjectCatalogError, load_project_catalogs

        catalog = profile.parent / "capabilities.yaml"
        gates = profile.parent / "gates.yaml"
        original_catalog, original_gates = catalog.read_bytes(), gates.read_bytes()
        try:
            self._write_catalog(profile, capability)
            gates.write_text("format: vera-gate-catalog/v1\ngates: []\n", encoding="utf-8")
            with self.assertRaises(ProjectCatalogError):
                load_project_catalogs(profile)
        finally:
            catalog.write_bytes(original_catalog)
            gates.write_bytes(original_gates)

    def _refusal_codes(self, profile: Path, **overrides) -> list[str]:
        from vera_mmu.capability_builder import preview_capability_contract

        preview = preview_capability_contract(profile, {**BASE, **overrides})
        return [item.code for item in preview.refusals]

    # --- the contract itself ---------------------------------------------

    def test_i007_i008_contract_reports_every_line_section_32_lists(self) -> None:
        from vera_mmu.capability_builder import preview_capability_contract

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            preview = preview_capability_contract(profile, BASE)
            self.assertEqual(preview.status, "PREVIEW")
            contract = preview.contract
            # §32 displays: Nom, Type, Runner, Commande/API, Entrées, Sorties, Timeout, Policy,
            # Artifacts, Validator, Proof admissible ?, Confirmation requise ?
            self.assertEqual(
                set(contract),
                {
                    "name", "type", "runner", "command", "inputs", "outputs", "timeout_seconds",
                    "policy", "artifacts", "validator", "proof_admissible", "confirmation_required",
                    "gate_backed",
                },
            )
            self.assertEqual(contract["runner"], "NOOP")
            self.assertEqual(contract["policy"], {"project": "READ_ONLY", "network": "DENY_NETWORK", "decision": "ALLOW"})
            self.assertEqual(contract["artifacts"], ["lint/report.json"])

    def test_i008_command_line_is_reported_not_applicable_rather_than_left_blank(self) -> None:
        """§32 lists a command; the Core holds no such field, and the contract says so."""
        from vera_mmu.capability_builder import capability_contract_options, preview_capability_contract

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self.assertEqual(capability_contract_options(profile)["command"]["status"], "NOT_APPLICABLE")
            command = preview_capability_contract(profile, BASE).contract["command"]
            self.assertEqual(command["status"], "NOT_APPLICABLE")
            self.assertIn("I008", command["reason"])

    def test_i007_i008_parameter_schema_is_derived_by_the_core_never_supplied(self) -> None:
        """A validator runner takes the schema the Core fixes; the interface composes none."""
        from vera_mmu.capability_builder import preview_capability_contract

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            collector = preview_capability_contract(profile, BASE).declaration["parameter_schema"]
            self.assertEqual(sorted(collector["properties"]), ["findings", "tool"])
            checker = preview_capability_contract(
                profile, {**BASE, "id": "hash-check", "kind": "CHECK", "runner": "EVIDENCE_HASH", "validator": "EVIDENCE_HASH"}
            ).declaration["parameter_schema"]
            self.assertEqual(sorted(checker["properties"]), ["evidence_id", "validator_id"])
            self.assertFalse(checker["additionalProperties"])

    def test_i001_i007_preview_is_non_mutating_and_apply_is_confirmed_fresh_and_atomic(self) -> None:
        from vera_mmu.capability_builder import CapabilityBuilderError, apply_capability_contract, preview_capability_contract

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            before = (profile.parent / "capabilities.yaml").read_bytes()
            preview = preview_capability_contract(profile, BASE)
            self.assertEqual((profile.parent / "capabilities.yaml").read_bytes(), before)
            with self.assertRaises(CapabilityBuilderError):
                apply_capability_contract(profile, preview, confirm=False)
            result = apply_capability_contract(profile, preview, confirm=True)
            self.assertEqual(result["status"], "DECLARED")
            self.assertEqual(result["materialization"], {
                "status": "PENDING",
                "command": "sync-capabilities",
                "reason": "Le contrat est déclaré ; sa matérialisation dans le store reste une opération explicite.",
            })
            declared = {str(item["id"]) for item in self._catalog(profile)["capabilities"]}
            self.assertIn("lint-report", declared)
            with self.assertRaises(CapabilityBuilderError):
                preview_capability_contract(profile, BASE)  # already declared

    def test_i007_a_preview_whose_catalog_changed_since_review_is_refused(self) -> None:
        from vera_mmu.capability_builder import CapabilityBuilderError, apply_capability_contract, preview_capability_contract

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            stale = preview_capability_contract(profile, BASE)
            other = preview_capability_contract(profile, {**BASE, "id": "other-report"})
            apply_capability_contract(profile, other, confirm=True)
            with self.assertRaises(CapabilityBuilderError):
                apply_capability_contract(profile, stale, confirm=True)

    def test_i007_i012_a_declared_contract_is_materialized_by_the_core_unchanged(self) -> None:
        """The contract reaches the engine: one capability, one contract, one policy decision."""
        from vera_mmu.capability_builder import apply_capability_contract, preview_capability_contract
        from vera_mmu.capability_contracts import CapabilityContractService
        from vera_mmu.capability_policies import CapabilityPolicyService
        from vera_mmu.identity import load_profile
        from vera_mmu.store import MemoryStore
        from vera_mmu.write_api import WriteService

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            preview = preview_capability_contract(profile, {**BASE, "confirmation_required": True})
            apply_capability_contract(profile, preview, confirm=True)
            with MemoryStore.open(load_profile(profile), profile) as store:
                self.assertIn("lint-report", WriteService(store).sync_profile_capabilities(actor="test"))
                contract = CapabilityContractService(store).get("lint-report")
                self.assertEqual((contract.runner_profile, contract.network_policy, contract.timeout_seconds), ("NOOP", "DENY_NETWORK", 60))
                self.assertFalse(contract.yields_proof)
                self.assertEqual(CapabilityPolicyService(store).get("lint-report").decision, "CONFIRM")

    # --- the seven refusals §32 requires ----------------------------------

    def test_refusal_1_i008_an_unbounded_command_is_refused_by_the_builder_and_by_the_core(self) -> None:
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self.assertEqual(self._refusal_codes(profile, command=["sh", "-c", "whoami"]), ["COMMAND_NOT_BOUNDED"])
            self.assertEqual(self._refusal_codes(profile, runner="SHELL"), ["COMMAND_NOT_BOUNDED"])
            self._assert_catalog_refused(profile, {**BASE, "command": ["sh", "-c", "whoami"]})

    def test_refusal_2_i005_a_path_outside_the_project_roots_is_refused(self) -> None:
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            for escape in ("../../etc/passwd", "/etc/passwd", "C:\\Windows\\system32", "~/secrets"):
                self.assertEqual(self._refusal_codes(profile, artifacts=[escape]), ["PATH_OUTSIDE_ROOTS"], escape)
                self._assert_catalog_refused(profile, {**BASE, "artifacts": [escape]})
            # An input or output names a field; a path there is a path wearing a field's clothes.
            for escape in ("../secrets", "reports/lint.json"):
                self.assertEqual(self._refusal_codes(profile, inputs=["tool", escape]), ["PATH_OUTSIDE_ROOTS"], escape)
                self._assert_catalog_refused(profile, {**BASE, "inputs": ["tool", escape]})
                self._assert_catalog_refused(profile, {**BASE, "outputs": ["verdict", escape]})
            # A confined relative path is accepted, so the rule is not simply refusing everything.
            self.assertEqual(self._refusal_codes(profile, artifacts=["reports/lint.json"]), [])

    def test_refusal_3_i013_a_network_capability_is_refused_because_nothing_would_bound_it(self) -> None:
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self.assertEqual(self._refusal_codes(profile, policy="NETWORK"), ["NETWORK_WITHOUT_POLICY"])
            self._assert_catalog_refused(profile, {**BASE, "policy": "NETWORK"})

    def test_refusal_4_i007_a_capability_without_a_timeout_is_refused(self) -> None:
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            for absent in (None, 0, 3601, "120", True):
                self.assertEqual(self._refusal_codes(profile, timeout_seconds=absent), ["MISSING_TIMEOUT"], absent)
            self._assert_catalog_refused(profile, {key: value for key, value in BASE.items() if key != "timeout_seconds"})

    def test_refusal_5_i006_an_uninterpretable_output_cannot_back_a_gate(self) -> None:
        """A gate reads `expected.verdict`; a capability declaring none leaves it nothing to read."""
        from vera_mmu.project_catalogs import ProjectCatalogError, load_project_catalogs

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self.assertEqual(self._refusal_codes(profile, outputs=["report"]), ["OUTPUT_NOT_INTERPRETABLE"])
            # Not destined for a gate, the same declaration is accepted: the refusal is about use.
            self.assertEqual(self._refusal_codes(profile, outputs=["report"], gate_backed=False), [])
            self._write_catalog(profile, {**BASE, "outputs": ["report"]})
            (profile.parent / "gates.yaml").write_text("format: vera-gate-catalog/v1\ngates: []\n", encoding="utf-8")
            load_project_catalogs(profile)  # the capability alone is fine; the gate on it is not
            (profile.parent / "gates.yaml").write_text(
                json.dumps({
                    "format": "vera-gate-catalog/v1",
                    "gates": [{"id": "LINT_OK", "name": "Lint", "capability_id": "lint-report", "required": True, "expected": {"verdict": "PASS"}}],
                }) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ProjectCatalogError):
                load_project_catalogs(profile)

    def test_refusal_6_i007_a_declaration_depending_on_an_absent_validator_is_refused(self) -> None:
        """Two dependencies that would never exist: a mismatched validator, and none at all."""
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            mismatch = {"runner": "EVIDENCE_HASH", "validator": "EVIDENCE_FIELDS", "kind": "CHECK"}
            self.assertEqual(self._refusal_codes(profile, **mismatch), ["DEPENDENCY_MISSING"])
            self.assertEqual(self._refusal_codes(profile, inputs=[]), ["DEPENDENCY_MISSING"])
            for declaration in ({**BASE, **mismatch}, {**BASE, "inputs": []}):
                self._assert_catalog_refused(profile, declaration)

    def test_refusal_6_i006_the_core_itself_refuses_the_mismatched_runner_at_execution(self) -> None:
        """The dependency is not merely absent from a screen: the engine refuses to run it."""
        from vera_mmu.capabilities import CapabilityService
        from vera_mmu.capability_contracts import CapabilityContractService
        from vera_mmu.capability_policies import CapabilityPolicyService
        from vera_mmu.executions import ExecutionError, ExecutionService
        from vera_mmu.identity import load_profile
        from vera_mmu.runner_validator_compatibility import EVIDENCE_VALIDATION_SCHEMA
        from vera_mmu.store import MemoryStore
        from vera_mmu.validators import ValidatorService

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                CapabilityService(store).create("mismatch", "Mismatch", "CHECK", "1.0.0", parameter_schema=EVIDENCE_VALIDATION_SCHEMA)
                CapabilityContractService(store).declare("mismatch", "EVIDENCE_HASH", "DENY_NETWORK", 30, parameter_schema=EVIDENCE_VALIDATION_SCHEMA)
                CapabilityPolicyService(store).declare("mismatch", "ALLOW", "test")
                ValidatorService(store).register("fields-only", "EVIDENCE_FIELDS", required_keys=("claim",))
                with self.assertRaises(ExecutionError):
                    ExecutionService(store).run_evidence_hash(
                        "run-1", "mismatch", {"validator_id": "fields-only", "evidence_id": "absent"}, validation_id="validation-1"
                    )

    def test_refusal_7_i004_a_placeholder_presented_as_a_validator_is_refused(self) -> None:
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            for placeholder in ("TODO", "manual", "none", "à définir"):
                self.assertEqual(self._refusal_codes(profile, validator=placeholder), ["PLACEHOLDER_VALIDATOR"], placeholder)
            # Claiming the capability produces the proof itself is the same absence, dressed up.
            self.assertEqual(self._refusal_codes(profile, yields_proof=True), ["PLACEHOLDER_VALIDATOR"])
            for declaration in ({**BASE, "validator": "TODO"}, {**BASE, "yields_proof": True}):
                self._assert_catalog_refused(profile, declaration)

    def test_refusal_7_i006_no_runner_of_the_core_honours_a_proof_yielding_contract(self) -> None:
        """`yields_proof` is refused because every runner refuses it — not merely by convention."""
        from vera_mmu.capabilities import CapabilityService
        from vera_mmu.capability_contracts import CapabilityContractService
        from vera_mmu.capability_policies import CapabilityPolicyService
        from vera_mmu.executions import ExecutionError, ExecutionService
        from vera_mmu.identity import load_profile
        from vera_mmu.store import MemoryStore

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                CapabilityService(store).create("claims-proof", "Claims proof", "CHECK", "1.0.0")
                CapabilityContractService(store).declare("claims-proof", "NOOP", "DENY_NETWORK", 30, yields_proof=True)
                CapabilityPolicyService(store).declare("claims-proof", "ALLOW", "test")
                with self.assertRaises(ExecutionError):
                    ExecutionService(store).run_noop("run-1", "claims-proof", {})

    # --- refusals reported together, and never written --------------------

    def test_i014_every_refusal_is_reported_at_once_and_a_refused_contract_is_never_written(self) -> None:
        from vera_mmu.capability_builder import CapabilityBuilderError, apply_capability_contract, preview_capability_contract

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            before = (profile.parent / "capabilities.yaml").read_bytes()
            preview = preview_capability_contract(profile, {
                **BASE, "command": "make test", "artifacts": ["../escape"], "policy": "NETWORK",
                "timeout_seconds": None, "outputs": ["report"], "validator": "TODO",
            })
            self.assertEqual(preview.status, "REFUSED")
            self.assertEqual(
                sorted({item.code for item in preview.refusals}),
                ["COMMAND_NOT_BOUNDED", "MISSING_TIMEOUT", "NETWORK_WITHOUT_POLICY", "OUTPUT_NOT_INTERPRETABLE", "PATH_OUTSIDE_ROOTS", "PLACEHOLDER_VALIDATOR"],
            )
            with self.assertRaises(CapabilityBuilderError):
                apply_capability_contract(profile, preview, confirm=True)
            self.assertEqual((profile.parent / "capabilities.yaml").read_bytes(), before)

    def test_i007_options_publish_only_what_the_core_admits(self) -> None:
        from vera_mmu.capability_builder import capability_contract_options

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            options = capability_contract_options(profile)
            self.assertEqual(options["network_policy"], {"value": "DENY_NETWORK", "editable": False, "available": ["DENY_NETWORK"]})
            self.assertEqual(options["validators"], ["EVIDENCE_FIELDS", "EVIDENCE_HASH"])
            network = next(item for item in options["policies"] if item["id"] == "NETWORK")
            self.assertFalse(network["declarable"])
            self.assertEqual({item["id"] for item in options["runners"] if item["consumes_validator"]}, {"EVIDENCE_HASH", "EVIDENCE_FIELDS"})
            self.assertIn("test-suite-report", options["declared_capabilities"])

    def test_i011_a_symlinked_or_foreign_catalog_is_refused(self) -> None:
        from vera_mmu.capability_builder import CapabilityBuilderError, apply_capability_contract, preview_capability_contract

        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            first.mkdir()
            second = root / "second"
            second.mkdir()
            profile = self._project(first)
            other = self._project(second, template="data")
            preview = preview_capability_contract(profile, BASE)
            with self.assertRaises(CapabilityBuilderError):
                apply_capability_contract(other, preview, confirm=True)
            catalog = profile.parent / "capabilities.yaml"
            catalog.unlink()
            catalog.symlink_to(profile.parent / "gates.yaml")
            with self.assertRaises(CapabilityBuilderError):
                preview_capability_contract(profile, BASE)

    def test_i015_the_contract_carries_no_domain_vocabulary_of_its_own(self) -> None:
        """Every domain template composes the same contract shape; only the names differ."""
        from vera_mmu.capability_builder import apply_capability_contract, preview_capability_contract

        with TemporaryDirectory() as directory:
            root = Path(directory)
            for index, template in enumerate(("software", "data", "research", "documentation", "game", "hardware")):
                project = root / template
                project.mkdir()
                profile = self._project(project, template=template)
                preview = preview_capability_contract(profile, {**BASE, "id": f"check-{index}"})
                self.assertEqual(preview.status, "PREVIEW", template)
                apply_capability_contract(profile, preview, confirm=True)


if __name__ == "__main__":
    unittest.main()
