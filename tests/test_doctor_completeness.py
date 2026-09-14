"""Check the Doctor against the report the specification requires (§45).

The specification lists fifteen rows and demands that each failure point at the element that
repairs it. The report previously merged capability catalog, gates and policies into one row,
omitted HMAC and hooks entirely, and offered no human-readable rendering.

Invariants exercised: I004/I014 (a policy requiring HMAC without a secret must be visible, not
silent) and I013 (every check states an explicit decision and its remediation).
"""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from vera_mmu.doctor import SPECIFIED_CHECKS, diagnose_project, render_doctor_report
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import PROOF_HMAC_SECRET_VARIABLE, WriteService


class DoctorCompletenessTests(unittest.TestCase):
    def _project(self, root: Path, template: str = "software") -> Path:
        preview = preview_project_initialization(root, template=template, project_id="doctor-project", project_name="Doctor Project")
        apply_project_initialization(root, preview, confirm=True)
        profile = root / ".vera-mmu" / "project.yaml"
        with MemoryStore.open(load_profile(profile), profile):
            pass
        return profile

    def test_report_covers_every_specified_check(self) -> None:
        with TemporaryDirectory() as tmp:
            report = diagnose_project(self._project(Path(tmp)))
            names = {check.name for check in report.checks}
            self.assertTrue(SPECIFIED_CHECKS.issubset(names), f"Contrôles manquants : {sorted(SPECIFIED_CHECKS - names)}")

    def test_catalog_rows_are_separate_so_a_failure_points_at_one_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "gates.yaml").write_text("format: vera-gate-catalog/v1\ngates: nope\n", encoding="utf-8")
            report = diagnose_project(profile)
            checks = {check.name: check for check in report.checks}
            self.assertEqual(report.status, "FAIL")
            self.assertEqual(checks["gates"].status, "FAIL")
            self.assertIn("gates.yaml", checks["gates"].remediation)

    def test_every_check_states_a_remediation(self) -> None:
        with TemporaryDirectory() as tmp:
            report = diagnose_project(self._project(Path(tmp)))
            for check in report.checks:
                self.assertTrue(check.remediation.strip(), f"{check.name} ne propose aucune remédiation.")

    # --- HMAC ------------------------------------------------------------

    def test_hmac_is_informational_until_a_proof_policy_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            report = diagnose_project(self._project(Path(tmp)))
            hmac_check = next(check for check in report.checks if check.name == "hmac")
            self.assertEqual(hmac_check.status, "INFO")

    def test_hmac_fails_when_the_policy_requires_a_secret_that_is_absent(self) -> None:
        """I014: the gap must be loud before a promotion is attempted, not at promotion time."""
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                WriteService(store).declare_proof_policy("HMAC_SHA256", hmac_required=True, actor="test")
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop(PROOF_HMAC_SECRET_VARIABLE, None)
                report = diagnose_project(profile)
            hmac_check = next(check for check in report.checks if check.name == "hmac")
            self.assertEqual(hmac_check.status, "FAIL")
            self.assertIn(PROOF_HMAC_SECRET_VARIABLE, hmac_check.remediation)

    def test_hmac_passes_when_the_required_secret_is_present(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                WriteService(store).declare_proof_policy("HMAC_SHA256", hmac_required=True, actor="test")
            with mock.patch.dict(os.environ, {PROOF_HMAC_SECRET_VARIABLE: "secret-projet"}):
                report = diagnose_project(profile)
            hmac_check = next(check for check in report.checks if check.name == "hmac")
            self.assertEqual(hmac_check.status, "PASS")

    def test_hmac_never_reports_the_secret_itself(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                WriteService(store).declare_proof_policy("HMAC_SHA256", hmac_required=True, actor="test")
            with mock.patch.dict(os.environ, {PROOF_HMAC_SECRET_VARIABLE: "tres-secret-unique"}):
                report = diagnose_project(profile)
            self.assertNotIn("tres-secret-unique", render_doctor_report(report))
            self.assertNotIn("tres-secret-unique", str(report.as_dict()))

    # --- hooks -----------------------------------------------------------

    def test_hooks_reports_no_declared_integration(self) -> None:
        with TemporaryDirectory() as tmp:
            report = diagnose_project(self._project(Path(tmp)))
            hooks = next(check for check in report.checks if check.name == "hooks")
            self.assertEqual(hooks.status, "INFO")

    def test_hooks_fails_when_a_declared_integration_is_not_installed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            content = profile.read_text(encoding="utf-8").replace("  enabled: []", "  enabled: [generic-mcp]")
            profile.write_text(content, encoding="utf-8")
            report = diagnose_project(profile)
            hooks = next(check for check in report.checks if check.name == "hooks")
            self.assertEqual(hooks.status, "FAIL")
            self.assertIn("generic-mcp", hooks.detail)

    # --- human rendering -------------------------------------------------

    def test_human_rendering_lists_every_check_with_its_status(self) -> None:
        with TemporaryDirectory() as tmp:
            report = diagnose_project(self._project(Path(tmp)))
            rendered = render_doctor_report(report)
            for check in report.checks:
                self.assertIn(check.name.upper().replace("_", " "), rendered)
                self.assertIn(check.status, rendered)
            self.assertIn("doctor-project", rendered)

    def test_human_rendering_surfaces_remediation_for_failures_only(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "policies.yaml").write_text("format: vera-policy-catalog/v1\nnope: true\n", encoding="utf-8")
            rendered = render_doctor_report(diagnose_project(profile))
            self.assertIn("POLICIES", rendered)
            self.assertIn("FAIL", rendered)
            self.assertIn("→ Corriger `.vera-mmu/policies.yaml`", rendered)
            # Only the named catalog fails; the others are reported unevaluated, not broken.
            self.assertIn("CAPABILITY CATALOG", rendered)
            self.assertIn("Non évalué", rendered)


if __name__ == "__main__":
    unittest.main()
