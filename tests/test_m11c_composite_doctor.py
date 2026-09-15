from __future__ import annotations

from contextlib import asynccontextmanager, redirect_stdout
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.__main__ import main
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "m11c_mcp_fixture_server.py"


def _initialize(root: Path, project_id: str = "m11c-doctor") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root,
        template="documentation",
        project_id=project_id,
        project_name="M11-C Doctor",
    )
    apply_project_initialization(root, preview, confirm=True)
    profile = root / ".vera-mmu" / "project.yaml"
    output = StringIO()
    with redirect_stdout(output):
        assert main(["init", str(profile)]) == 0
    return profile


def _cli(arguments: list[str]) -> tuple[int, dict[str, object]]:
    output = StringIO()
    with redirect_stdout(output):
        status = main(arguments)
    return status, json.loads(output.getvalue())


class CompositeDoctorTests(unittest.TestCase):
    _required_checks = {
        "project_identity",
        "profile",
        "profile_rebind",
        "profile_migration",
        "workspace",
        "capability_catalog",
        "gates",
        "policies",
        "playbook",
        "runtime",
        "sqlite_integrity",
        "migration_ledger",
        "wal",
        "artifact_store",
        "hmac",
        "resume",
        "mcp_transport",
        "hooks",
        "vcs",
        "zero_pollution",
    }

    def test_i001_i005_i010_i011_doctor_reports_healthy_project_without_mutation(self) -> None:
        from vera_mmu.doctor import diagnose_project
        from vera_mmu.identity import load_profile
        from vera_mmu.store import MemoryStore

        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                audit_before = store.audit_events()
            database = profile.parent / "memory.sqlite"
            checksum_before = sha256(database.read_bytes()).hexdigest()

            report = diagnose_project(profile)

            self.assertEqual(report.status, "PASS")
            self.assertEqual(set(item.name for item in report.checks), self._required_checks)
            self.assertTrue(all(item.status in {"PASS", "INFO"} for item in report.checks))
            self.assertEqual(checksum_before, sha256(database.read_bytes()).hexdigest())
            with MemoryStore.open(load_profile(profile), profile) as store:
                self.assertEqual(store.audit_events(), audit_before)

            code, payload = _cli(["doctor", str(profile)])
            self.assertEqual(code, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["doctor"]["status"], "PASS")
            self.assertEqual({item["name"] for item in payload["doctor"]["checks"]}, self._required_checks)

    def test_profile_migration_journal_is_reported_without_implicit_repair(self) -> None:
        from copy import deepcopy
        from vera_mmu.doctor import diagnose_project
        from vera_mmu.identity import load_profile
        from vera_mmu.profile_migration import prepare_profile_migration_journal, preview_profile_physical_migration

        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = _initialize(root, project_id="doctor-migration")
            profile = load_profile(profile_path)
            candidate = deepcopy(profile)
            candidate["storage"]["memory_dir"] = ".vera-mmu-next"
            candidate["capabilities"]["catalog"] = ".vera-mmu-next/capabilities.yaml"
            candidate["gates"]["catalog"] = ".vera-mmu-next/gates.yaml"
            candidate["policies"]["file"] = ".vera-mmu-next/policies.yaml"
            candidate["integrations"]["agent_profiles"] = ".vera-mmu-next/agent-profiles.yaml"
            preview = preview_profile_physical_migration(profile_path, candidate)
            prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            report = diagnose_project(profile_path)
            checks = {item.name: item for item in report.checks}
            self.assertEqual(checks["profile_migration"].status, "INFO")
            self.assertEqual(len(list(root.glob(".vera-profile-migration-*.json"))), 1)

    def test_cli_migrate_status_is_read_only_and_deterministic(self) -> None:
        from copy import deepcopy
        from vera_mmu.identity import load_profile
        from vera_mmu.profile_migration import prepare_profile_migration_journal, preview_profile_physical_migration

        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = _initialize(root, project_id="cli-migration")
            code, payload = _cli(["migrate", "status", str(profile_path)])
            self.assertEqual(code, 0)
            self.assertEqual(payload["migration"]["status"], "NO_PENDING_MIGRATION")  # type: ignore[index]
            profile = load_profile(profile_path)
            candidate = deepcopy(profile)
            candidate["storage"]["memory_dir"] = ".vera-mmu-next"
            candidate["capabilities"]["catalog"] = ".vera-mmu-next/capabilities.yaml"
            candidate["gates"]["catalog"] = ".vera-mmu-next/gates.yaml"
            candidate["policies"]["file"] = ".vera-mmu-next/policies.yaml"
            candidate["integrations"]["agent_profiles"] = ".vera-mmu-next/agent-profiles.yaml"
            preview = preview_profile_physical_migration(profile_path, candidate)
            prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            code, payload = _cli(["migrate", "status", str(profile_path)])
            self.assertEqual(code, 0)
            self.assertEqual(payload["migration"]["status"], "READY_FOR_EXECUTOR")  # type: ignore[index]
            self.assertTrue((root / ".vera-mmu" / "project.yaml").is_file())

    def test_cli_migrate_recover_requires_confirmation_and_recovers_executing_journal(self) -> None:
        from copy import deepcopy
        from vera_mmu.identity import load_profile
        from vera_mmu.profile_migration import prepare_profile_migration_journal, preview_profile_physical_migration

        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = _initialize(root, project_id="cli-recovery")
            profile = load_profile(profile_path)
            candidate = deepcopy(profile)
            candidate["storage"]["memory_dir"] = ".vera-mmu-next"
            candidate["capabilities"]["catalog"] = ".vera-mmu-next/capabilities.yaml"
            candidate["gates"]["catalog"] = ".vera-mmu-next/gates.yaml"
            candidate["policies"]["file"] = ".vera-mmu-next/policies.yaml"
            candidate["integrations"]["agent_profiles"] = ".vera-mmu-next/agent-profiles.yaml"
            preview = preview_profile_physical_migration(profile_path, candidate)
            result = prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            journal = Path(str(result["journal_path"]))
            backup = root / ".vera-profile-migration-backup"
            backup.write_text(profile_path.read_text(encoding="utf-8"), encoding="utf-8")
            record = json.loads(journal.read_text(encoding="utf-8"))
            record.update({"state": "EXECUTING", "backup_path": str(backup)})
            journal.write_text(json.dumps(record) + "\n", encoding="utf-8")
            refused_code, refused = _cli(["migrate", "recover", str(journal)])
            self.assertEqual(refused_code, 2)
            self.assertFalse(refused["ok"])
            recovered_code, recovered = _cli(["migrate", "recover", str(journal), "--confirm"])
            self.assertEqual(recovered_code, 0)
            self.assertEqual(recovered["migration"]["status"], "ROLLED_BACK_TO_PLANNED")  # type: ignore[index]

    def test_i001_i005_i011_doctor_fails_loudly_for_tampered_sqlite_and_symlinked_artifacts(self) -> None:
        from vera_mmu.doctor import diagnose_project

        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile = _initialize(root)
            artifact_store = profile.parent / "artifacts"
            external = root / "external-artifacts"
            external.mkdir()
            artifact_store.symlink_to(external, target_is_directory=True)
            report = diagnose_project(profile)
            checks = {item.name: item for item in report.checks}
            self.assertEqual(report.status, "FAIL")
            self.assertEqual(checks["artifact_store"].status, "FAIL")
            self.assertEqual(checks["sqlite_integrity"].status, "PASS")

            artifact_store.unlink()
            database = profile.parent / "memory.sqlite"
            database.write_bytes(b"not a SQLite database")
            corrupted = diagnose_project(profile)
            corrupted_checks = {item.name: item for item in corrupted.checks}
            self.assertEqual(corrupted.status, "FAIL")
            self.assertEqual(corrupted_checks["sqlite_integrity"].status, "FAIL")
            self.assertEqual(corrupted_checks["migration_ledger"].status, "FAIL")


class CompositeDoctorMCPTests(unittest.IsolatedAsyncioTestCase):
    @asynccontextmanager
    async def _session(self, profile: Path):
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(FIXTURE_SERVER), "--profile", str(profile)],
            env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
            cwd=str(ROOT),
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    @staticmethod
    def _payload(response):
        payload = response.structured_content
        if not isinstance(payload, dict):
            raise AssertionError(f"Réponse MCP structurée absente : {response}")
        return payload

    async def test_i007_i008_i011_mcp_doctor_exposes_no_client_controlled_path_or_runtime(self) -> None:
        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            async with self._session(profile) as session:
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                self.assertIn("mmu_doctor", tools)
                self.assertEqual(set(tools["mmu_doctor"].input_schema.get("properties", {})), set())
                report = self._payload(await session.call_tool("mmu_doctor", {}))
                self.assertTrue(report["ok"])
                self.assertEqual(report["result"]["status"], "PASS")
                self.assertEqual({item["name"] for item in report["result"]["checks"]}, CompositeDoctorTests._required_checks)


if __name__ == "__main__":
    unittest.main()
