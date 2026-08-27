from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.evidence import EvidenceService
from vera_mmu.gates import GateService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from tests.test_gate_policies import PROFILE, GatePolicyTests


class GatePolicyBuilderTests(GatePolicyTests):
    def test_preview_confirmation_and_catalog_freshness(self) -> None:
        from vera_mmu.gate_policy_builder import GatePolicyBuilderError, apply_gate_policy_draft, preview_gate_policy_draft

        with self._open() as store:
            self._evidence(store)
            gates = self._gate(store, "policy-builder")
            before = len(store.audit_events())
            preview = preview_gate_policy_draft(store, gate_id="policy-builder", mode="AT_LEAST", minimum_admissions=2)
            self.assertEqual(len(store.audit_events()), before)
            with self.assertRaises(GatePolicyBuilderError):
                apply_gate_policy_draft(store, preview, confirm=False)
            result = apply_gate_policy_draft(store, preview, confirm=True)
            self.assertEqual(result["policy"]["mode"], "AT_LEAST")
            self.assertEqual(gates.get_policy("policy-builder").minimum_admissions, 2)
            next_gate = self._gate(store, "stale-gate")
            stale = preview_gate_policy_draft(store, gate_id="stale-gate", mode="ANY", minimum_admissions=None)
            EvidenceService(store).record("e4", "execution", "TEST_PROOF", "PASS", {"evidence": "e4"})
            GateService(store).add_requirement("stale-gate", "e4")
            with self.assertRaises(GatePolicyBuilderError):
                apply_gate_policy_draft(store, stale, confirm=True)
            with self.assertRaises(GatePolicyBuilderError):
                preview_gate_policy_draft(store, gate_id="stale-gate", mode="ALL", minimum_admissions=1)


if __name__ == "__main__":
    unittest.main()
