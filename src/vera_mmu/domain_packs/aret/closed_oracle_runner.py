from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from collections.abc import Callable, Mapping
from typing import Any

from ...assets import Asset, AssetService
from ...capabilities import Capability, CapabilityError, CapabilityService
from ...capability_contracts import CapabilityContract, CapabilityContractError, CapabilityContractService
from ...capability_policies import CapabilityPolicy, CapabilityPolicyError, CapabilityPolicyService
from ...evidence import Evidence, EvidenceError, EvidenceService
from ...executions import Execution, ExecutionError, ExecutionService
from ...identity import canonical_json
from ...store import MemoryStore
from .oracle_contract import (
    AretOracleContractError,
    AretOraclePreflight,
    AretOracleSpec,
    oracle_spec,
    normalize_oracle_result,
    preflight_oracle,
)


ARET_TOOLKIT_REFERENCE_COMMIT = "7a0429790bb04d1ad3c1819449e906140ebf4513"
ARET_TOOLKIT_BINARY_SHA256 = "6ca52f0955266aeda31d235caacf0844e2516f41d67468632f2ddb1bb1e16a19"
_NETWORK_SANDBOX_PREFIX = ("unshare", "--user", "--map-root-user", "--net")
_FIXTURE_RE = re.compile(r"[A-Za-z0-9_.-]{1,100}")


class AretClosedOracleError(ValueError):
    """Le runner ARET fermé refuse une entrée, une référence ou une exécution non conforme."""


@dataclass(frozen=True)
class OracleProcessResult:
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool


@dataclass(frozen=True)
class DeclaredAretOracleCapability:
    capability: Capability
    contract: CapabilityContract
    policy: CapabilityPolicy


@dataclass(frozen=True)
class ClosedOracleOutcome:
    execution: Execution
    evidence: Evidence
    asset_id: str
    artifact_hash: str
    verdict: str
    preflight: AretOraclePreflight


def _capability_id(spec: AretOracleSpec) -> str:
    return f"aret-oracle-{spec.name}"


def _parameter_schema(spec: AretOracleSpec) -> dict[str, Any]:
    if spec.accepts_fixture:
        return {
            "type": "object",
            "properties": {"fixture": {"type": "string"}},
            "required": [],
            "additionalProperties": False,
        }
    return {"type": "object"}


def declare_aret_oracle_capability(
    store: MemoryStore,
    oracle_name: str,
    *,
    actor: str = "aret-oracle-pack",
) -> DeclaredAretOracleCapability:
    spec = oracle_spec(oracle_name)
    capability_id = _capability_id(spec)
    try:
        capability = CapabilityService(store).create(
            capability_id,
            f"ARET oracle {spec.name}",
            "ORACLE",
            "1.0.0",
            description="Oracle ARET fermé, exécuté seulement après préflight et confinement réseau.",
            parameter_schema=_parameter_schema(spec),
            metadata={
                "domain_pack": "aret",
                "oracle": spec.name,
                "kind": spec.kind,
                "timeout_seconds": spec.timeout_seconds,
                "requires_aret_binary": spec.requires_aret_binary,
                "reference_commit": ARET_TOOLKIT_REFERENCE_COMMIT,
            },
            actor=actor,
        )
        contract = CapabilityContractService(store).declare(
            capability_id,
            "OBSERVED_PROCESS",
            "DENY_NETWORK",
            spec.timeout_seconds,
            parameter_schema=_parameter_schema(spec),
            yields_proof=False,
            actor=actor,
        )
        policy = CapabilityPolicyService(store).declare(
            capability_id,
            "ALLOW",
            "Closed ARET oracle requires preflight and network sandbox.",
            actor=actor,
        )
    except (CapabilityError, CapabilityContractError, CapabilityPolicyError) as exc:
        raise AretClosedOracleError("Déclaration de capability ARET impossible ou déjà présente.") from exc
    return DeclaredAretOracleCapability(capability, contract, policy)


def _repository_revision(repository: Path) -> str:
    result = subprocess.run(
        ("git", "-C", str(repository), "rev-parse", "HEAD"),
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _repository_is_clean(repository: Path) -> bool:
    result = subprocess.run(
        ("git", "-C", str(repository), "status", "--porcelain=v1", "--untracked-files=all"),
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and not result.stdout.strip()


def _safe_fixture(spec: AretOracleSpec, fixture: str | None) -> str | None:
    if fixture is None:
        return None
    if not isinstance(fixture, str):
        raise AretClosedOracleError("Fixture invalide.")
    normalized = fixture.strip()
    if not spec.accepts_fixture or _FIXTURE_RE.fullmatch(normalized) is None:
        raise AretClosedOracleError("Fixture refusée par le contrat d'oracle fermé.")
    return normalized


def _run_subprocess(
    command: tuple[str, ...],
    cwd: Path,
    environment: dict[str, str],
    timeout_seconds: int,
) -> OracleProcessResult:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return OracleProcessResult(completed.returncode, completed.stdout, completed.stderr, False)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        return OracleProcessResult(None, stdout, stderr, True)


def _command_for(spec: AretOracleSpec, preflight: AretOraclePreflight, fixture: str | None) -> tuple[str, ...]:
    command = spec.command if spec.command is not None else ("bash", str(preflight.script_path))
    if fixture is not None:
        command = (*command, fixture)
    return (*_NETWORK_SANDBOX_PREFIX, *command)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_closed_oracle(
    store: MemoryStore,
    repository: Path,
    oracle_name: str,
    *,
    execution_id: str,
    evidence_id: str,
    actor: str = "aret-oracle-pack",
    fixture: str | None = None,
    aret_binary: Path | None = None,
    command_runner: Callable[[tuple[str, ...], Path, dict[str, str], int], OracleProcessResult] = _run_subprocess,
    revision_reader: Callable[[Path], str] = _repository_revision,
    clean_checker: Callable[[Path], bool] = _repository_is_clean,
    tool_lookup: Callable[[str], str | None],
) -> ClosedOracleOutcome:
    spec = oracle_spec(oracle_name)
    if not isinstance(repository, Path) or not callable(command_runner) or not callable(revision_reader) or not callable(clean_checker):
        raise AretClosedOracleError("Entrée de runner fermée invalide.")
    root = repository.expanduser().resolve()
    if not root.is_dir():
        raise AretClosedOracleError("Référence toolkit ARET introuvable.")
    if revision_reader(root) != ARET_TOOLKIT_REFERENCE_COMMIT or not clean_checker(root):
        raise AretClosedOracleError("Référence toolkit ARET non verrouillée ou non propre.")
    safe_fixture = _safe_fixture(spec, fixture)
    try:
        preflight = preflight_oracle(root, spec.name, tool_lookup=tool_lookup)
    except AretOracleContractError as exc:
        raise AretClosedOracleError("Préflight ARET fermé impossible.") from exc
    if aret_binary is not None:
        if not isinstance(aret_binary, Path):
            raise AretClosedOracleError("Binaire ARET externe invalide.")
        external_binary = aret_binary.expanduser().resolve()
        if not external_binary.is_file():
            raise AretClosedOracleError("Binaire ARET externe introuvable.")
        if hashlib.sha256(external_binary.read_bytes()).hexdigest() != ARET_TOOLKIT_BINARY_SHA256:
            raise AretClosedOracleError("Binaire ARET externe non attesté.")
        missing = tuple(item for item in preflight.missing_dependencies if item != "target/release/aret")
        preflight = replace(
            preflight,
            aret_binary=external_binary,
            missing_dependencies=missing,
            status="READY" if not missing else "SKIPPED",
        )
    if tool_lookup("unshare") is None:
        raise AretClosedOracleError("Sandbox réseau indisponible : exécution ARET refusée.")

    command = _command_for(spec, preflight, safe_fixture)
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "LC_ALL": "C",
        "TZ": "UTC",
        "ARET": str(preflight.aret_binary),
    }
    started_at = _now()
    if preflight.status == "READY":
        process = command_runner(command, root, environment, spec.timeout_seconds)
    else:
        process = OracleProcessResult(None, "", "", False)
    finished_at = _now()
    verdict = normalize_oracle_result(
        spec.name,
        process.exit_code,
        process.stdout,
        process.stderr,
        preflight.missing_dependencies,
        process.timed_out,
    )
    binary_hash = ""
    if preflight.aret_binary.is_file():
        binary_hash = hashlib.sha256(preflight.aret_binary.read_bytes()).hexdigest()
    artifact = {
        "format": "vera-aret-closed-oracle/v1",
        "oracle": spec.name,
        "kind": spec.kind,
        "reference_commit": ARET_TOOLKIT_REFERENCE_COMMIT,
        "command": list(command),
        "fixture": safe_fixture or "",
        "result": verdict,
        "exit_code": process.exit_code,
        "timed_out": process.timed_out,
        "missing_dependencies": list(preflight.missing_dependencies),
        "environment": {
            "lc_all": environment["LC_ALL"],
            "tz": environment["TZ"],
            "aret_binary_sha256": binary_hash,
            "network_sandbox": list(_NETWORK_SANDBOX_PREFIX),
        },
        "started_at": started_at,
        "finished_at": finished_at,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }
    artifact_bytes = (canonical_json(artifact) + "\n").encode("utf-8")
    asset_id = f"{execution_id}-artifact"
    try:
        asset: Asset = AssetService(store).record(asset_id, artifact_bytes, media_type="application/json", actor=actor)
        execution = ExecutionService(store).record_observed_process(
            execution_id,
            _capability_id(spec),
            {} if safe_fixture is None else {"fixture": safe_fixture},
            environment={
                "adapter": "vera-aret-closed-oracle/v1",
                "reference_commit": ARET_TOOLKIT_REFERENCE_COMMIT,
                "network_sandbox": "unshare-user-net",
                "oracle": spec.name,
            },
            exit_code=process.exit_code,
            artifact_hash=asset.content_hash,
            result={"verdict": verdict, "timed_out": process.timed_out, "asset_id": asset.id},
            actor=actor,
        )
        evidence = EvidenceService(store).record(
            evidence_id,
            execution_id,
            "TEST_PROOF",
            verdict,
            {
                "format": "vera-aret-closed-oracle-evidence/v1",
                "oracle": spec.name,
                "kind": spec.kind,
                "reference_commit": ARET_TOOLKIT_REFERENCE_COMMIT,
                "asset_id": asset.id,
                "asset_hash": asset.content_hash,
                "verdict": verdict,
                "exit_code": process.exit_code,
                "timed_out": process.timed_out,
                "missing_dependencies": list(preflight.missing_dependencies),
            },
            actor=actor,
        )
    except (ExecutionError, EvidenceError, ValueError) as exc:
        raise AretClosedOracleError("Enregistrement Core de l'oracle ARET impossible.") from exc
    return ClosedOracleOutcome(execution, evidence, asset.id, asset.content_hash, verdict, preflight)
