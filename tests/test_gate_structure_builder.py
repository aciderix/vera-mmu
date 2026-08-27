from __future__ import annotations

import unittest

from vera_mmu.gates import GateService
from vera_mmu.work_items import WorkItemService
from tests.test_gate_policies import GatePolicyTests


class GateStructureBuilderTests(GatePolicyTests):
    def test_preview_is_pure_and_apply_creates_complete_structure_atomically(self) -> None:
        from vera_mmu.gate_structure_builder import apply_gate_structure_draft, preview_gate_structure_draft

        with self._open() as store:
            self._evidence(store)
            WorkItemService(store).create("dashboard-gate", "SUBTASK", "Dashboard gate")
            before = len(store.audit_events())
            preview = preview_gate_structure_draft(
                store,
                gate_id="dashboard-gate",
                work_item_id="dashboard-gate",
                primary_evidence_id="e1",
                requirement_evidence_ids=("e2", "e3"),
            )
            self.assertEqual(len(store.audit_events()), before)
            result = apply_gate_structure_draft(store, preview, confirm=True)
            self.assertEqual(result["status"], "DECLARED")
            self.assertEqual(GateService._requirements(store.connection, "dashboard-gate"), ["e1", "e2", "e3"])

    def test_refusals_are_non_mutating_and_stale_preview_is_rejected(self) -> None:
        from vera_mmu.gate_structure_builder import GateStructureBuilderError, apply_gate_structure_draft, preview_gate_structure_draft

        with self._open() as store:
            self._evidence(store)
            WorkItemService(store).create("stale-gate", "SUBTASK", "Stale gate")
            with self.assertRaises(GateStructureBuilderError):
                preview_gate_structure_draft(store, gate_id="bad/gate", work_item_id="stale-gate", primary_evidence_id="e1", requirement_evidence_ids=())
            with self.assertRaises(GateStructureBuilderError):
                preview_gate_structure_draft(store, gate_id="duplicate", work_item_id="stale-gate", primary_evidence_id="e1", requirement_evidence_ids=("e1",))
            preview = preview_gate_structure_draft(store, gate_id="stale-gate", work_item_id="stale-gate", primary_evidence_id="e1", requirement_evidence_ids=("e2",))
            GateService(store).declare("stale-gate", "stale-gate", "e1")
            with self.assertRaises(GateStructureBuilderError):
                apply_gate_structure_draft(store, preview, confirm=True)
            self.assertEqual(GateService._requirements(store.connection, "stale-gate"), ["e1"])


if __name__ == "__main__":
    unittest.main()
