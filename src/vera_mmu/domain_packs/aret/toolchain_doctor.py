from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
import subprocess
from collections.abc import Callable

from .closed_oracle_runner import ARET_TOOLKIT_BINARY_SHA256, ARET_TOOLKIT_REFERENCE_COMMIT
from .oracle_contract import ARET_ORACLES, AretOracleContractError, preflight_oracle


class AretToolchainDoctorError(ValueError):
    """Le doctor ARET ne peut pas inspecter une référence bornée."""


@dataclass(frozen=True)
class AretBinaryDoctorCheck:
    path: str
    sha256: str | None
    expected_sha256: str
    status: str


@dataclass(frozen=True)
class AretOracleDoctorCheck:
    oracle_name: str
    status: str
    missing_dependencies: tuple[str, ...]


@dataclass(frozen=True)
class AretToolchainDoctorReport:
    status: str
    reference_status: str
    reference_commit: str
    reference_clean: bool
    network_sandbox_status: str
    binary: AretBinaryDoctorCheck
    oracles: tuple[AretOracleDoctorCheck, ...]
    install_actions: tuple[str, ...]


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


def _binary_check(repository: Path, aret_binary: Path | None) -> AretBinaryDoctorCheck:
    candidate = (aret_binary if aret_binary is not None else repository / "target" / "release" / "aret").expanduser().resolve()
    if not candidate.is_file():
        return AretBinaryDoctorCheck(str(candidate), None, ARET_TOOLKIT_BINARY_SHA256, "MISSING")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    return AretBinaryDoctorCheck(
        str(candidate),
        digest,
        ARET_TOOLKIT_BINARY_SHA256,
        "PASS" if digest == ARET_TOOLKIT_BINARY_SHA256 else "ERROR",
    )


def inspect_aret_toolchain(
    repository: Path,
    *,
    aret_binary: Path | None = None,
    tool_lookup: Callable[[str], str | None] = shutil.which,
    revision_reader: Callable[[Path], str] = _repository_revision,
    clean_checker: Callable[[Path], bool] = _repository_is_clean,
) -> AretToolchainDoctorReport:
    if not isinstance(repository, Path) or not callable(tool_lookup) or not callable(revision_reader) or not callable(clean_checker):
        raise AretToolchainDoctorError("Entrée doctor ARET invalide.")
    root = repository.expanduser().resolve()
    if not root.is_dir():
        raise AretToolchainDoctorError("Référence toolkit ARET introuvable.")

    commit = revision_reader(root)
    clean = clean_checker(root)
    reference_status = "PASS" if commit == ARET_TOOLKIT_REFERENCE_COMMIT and clean else "ERROR"
    binary = _binary_check(root, aret_binary)
    network_sandbox_status = "PASS" if tool_lookup("unshare") is not None else "MISSING"
    checks: list[AretOracleDoctorCheck] = []
    for spec in ARET_ORACLES.values():
        try:
            preflight = preflight_oracle(root, spec.name, tool_lookup=tool_lookup)
            missing = tuple(
                item
                for item in preflight.missing_dependencies
                if not (item == "target/release/aret" and binary.status == "PASS")
            )
            checks.append(AretOracleDoctorCheck(spec.name, "READY" if not missing else "SKIPPED", missing))
        except AretOracleContractError:
            checks.append(AretOracleDoctorCheck(spec.name, "ERROR", ("contract",)))

    if reference_status == "ERROR" or binary.status == "ERROR" or any(check.status == "ERROR" for check in checks):
        status = "ERROR"
    elif binary.status != "PASS" or network_sandbox_status != "PASS" or any(check.status == "SKIPPED" for check in checks):
        status = "DEGRADED"
    else:
        status = "READY"
    return AretToolchainDoctorReport(
        status,
        reference_status,
        commit,
        clean,
        network_sandbox_status,
        binary,
        tuple(checks),
        (),
    )
