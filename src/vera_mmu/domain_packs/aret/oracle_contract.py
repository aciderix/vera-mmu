from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from collections.abc import Callable


class AretOracleContractError(ValueError):
    """Le contrat d'oracle ARET est invalide ou ne peut pas être préflighté."""


@dataclass(frozen=True)
class AretOracleSpec:
    name: str
    kind: str
    script: str | None
    dependencies: tuple[str, ...]
    timeout_seconds: int
    accepts_fixture: bool = False
    requires_aret_binary: bool = False
    command: tuple[str, ...] | None = None


@dataclass(frozen=True)
class AretOraclePreflight:
    oracle_name: str
    script_path: Path | None
    aret_binary: Path
    missing_dependencies: tuple[str, ...]
    status: str


ARET_ORACLES: dict[str, AretOracleSpec] = {
    "difftest": AretOracleSpec(
        "difftest", "DIFFTEST", "bench/difftest.sh", ("bash", "gcc"), 1800, requires_aret_binary=True
    ),
    "transpilediff": AretOracleSpec(
        "transpilediff", "TRANSPILEDIFF", "bench/difftest_transpile.sh", ("bash", "gcc"), 1800,
        requires_aret_binary=True,
    ),
    "stdcall_audit": AretOracleSpec(
        "stdcall_audit", "STDCALL_AUDIT", "bench/stdcall_audit.sh", ("bash", "python3", "i686-w64-mingw32-nm"), 1800
    ),
    "winediff": AretOracleSpec(
        "winediff", "WINEDIFF", "bench/winediff.sh", ("bash", "wine", "i686-w64-mingw32-gcc"), 3600,
        accepts_fixture=True, requires_aret_binary=True,
    ),
    "winehash": AretOracleSpec(
        "winehash", "WINEHASH", "bench/winoracle/wine_hashes.sh", ("bash", "wine", "i686-w64-mingw32-gcc"), 3600
    ),
    "ehdiff": AretOracleSpec(
        "ehdiff", "EHDIFF", "bench/ehdiff.sh", ("bash", "clang", "lld-link", "llvm-dlltool", "wine"), 3600,
        requires_aret_binary=True,
    ),
    "gnuehdiff": AretOracleSpec(
        "gnuehdiff", "GNUEHDIFF", "bench/gnuehdiff.sh", ("bash", "i686-w64-mingw32-g++", "wine"), 3600,
        requires_aret_binary=True,
    ),
    "funcdiff": AretOracleSpec(
        "funcdiff", "FUNCDIFF", "bench/funcdiff.sh", ("bash", "cargo"), 1800
    ),
    "cpudiff": AretOracleSpec(
        "cpudiff", "CPUDIFF", "src/cpudiff.rs", ("cargo",), 3600,
        command=("cargo", "test", "--release", "--features", "unpack", "cpudiff"),
    ),
}


def oracle_spec(oracle_name: str) -> AretOracleSpec:
    if not isinstance(oracle_name, str):
        raise AretOracleContractError("Nom d'oracle invalide.")
    name = oracle_name.strip().lower()
    if name not in ARET_ORACLES:
        raise AretOracleContractError("Oracle ARET inconnu dans le catalogue fermé.")
    return ARET_ORACLES[name]


def resolve_repository_file(repository: Path, relative_path: str, label: str) -> Path:
    if not isinstance(repository, Path) or not isinstance(relative_path, str) or not relative_path:
        raise AretOracleContractError("Chemin de dépôt ou de ressource invalide.")
    root = repository.expanduser().resolve()
    if not root.is_dir():
        raise AretOracleContractError("Dépôt toolkit ARET introuvable.")
    candidate = (root / relative_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise AretOracleContractError(f"{label} résolu hors du dépôt toolkit ARET configuré.")
    return candidate


def preflight_oracle(
    repository: Path,
    oracle_name: str,
    *,
    tool_lookup: Callable[[str], str | None] = shutil.which,
) -> AretOraclePreflight:
    spec = oracle_spec(oracle_name)
    if not callable(tool_lookup):
        raise AretOracleContractError("Résolveur de dépendances invalide.")
    script_path = resolve_repository_file(repository, spec.script, "Script d'oracle") if spec.script else None
    aret_binary = resolve_repository_file(repository, "target/release/aret", "Binaire ARET")

    missing = [tool for tool in spec.dependencies if tool_lookup(tool) is None]
    if spec.requires_aret_binary and not aret_binary.is_file():
        missing.append("target/release/aret")
    if script_path is not None and not script_path.is_file():
        missing.append(spec.script)

    return AretOraclePreflight(
        oracle_name=spec.name,
        script_path=script_path,
        aret_binary=aret_binary,
        missing_dependencies=tuple(missing),
        status="READY" if not missing else "SKIPPED",
    )


def normalize_oracle_result(
    oracle_name: str,
    exit_code: int | None,
    stdout: str,
    stderr: str,
    missing_dependencies: tuple[str, ...],
    timed_out: bool,
) -> str:
    spec = oracle_spec(oracle_name)
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise AretOracleContractError("Sortie d'oracle invalide.")
    if not isinstance(missing_dependencies, tuple) or not all(isinstance(item, str) and item for item in missing_dependencies):
        raise AretOracleContractError("Dépendances manquantes invalides.")
    if not isinstance(timed_out, bool):
        raise AretOracleContractError("Indicateur timeout invalide.")
    if missing_dependencies:
        return "SKIPPED"
    if timed_out:
        return "ERROR"
    if exit_code is not None and (isinstance(exit_code, bool) or not isinstance(exit_code, int)):
        raise AretOracleContractError("Code de sortie invalide.")
    if exit_code is not None and exit_code != 0:
        return "FAIL"

    output = f"{stdout}\n{stderr}"
    if spec.name == "difftest":
        match = re.search(r"differential equivalence:\s*(\d+)\s*/\s*(\d+)\s+functions", output)
        if exit_code == 0 and match and int(match.group(1)) == int(match.group(2)) and int(match.group(2)) > 0:
            return "PASS"
    elif spec.name == "transpilediff":
        match = re.search(r"transpile-pipeline equivalence:\s*(\d+)\s*/\s*(\d+)\s+opt-levels", output)
        if exit_code == 0 and match and int(match.group(1)) == int(match.group(2)) and int(match.group(2)) > 0:
            return "PASS"
    elif spec.name == "stdcall_audit" and exit_code == 0 and re.search(r"stdcall-pop audit:\s*PASS", output):
        return "PASS"
    elif spec.name == "winediff":
        match = re.search(r"OS-API \(Wine\) equivalence:\s*(\d+)\s*/\s*(\d+)\s+programs", output)
        if exit_code == 0 and match and int(match.group(1)) == int(match.group(2)) and int(match.group(2)) > 0:
            return "PASS"
    elif spec.name == "ehdiff":
        match = re.search(r"MSVC EH differential:\s*(\d+)\s*/\s*(\d+)\s+fixtures", output)
        if exit_code == 0 and match and int(match.group(1)) == int(match.group(2)) and int(match.group(2)) > 0:
            return "PASS"
    elif spec.name == "gnuehdiff":
        match = re.search(r"GNU/Itanium C\+\+ EH differential:\s*(\d+)\s*/\s*(\d+)\s+fixtures", output)
        if exit_code == 0 and match and int(match.group(1)) == int(match.group(2)) and int(match.group(2)) > 0:
            return "PASS"
    elif spec.name == "funcdiff" and exit_code == 0 and re.search(r"funcdiff corpus gate:\s*PASS", output):
        return "PASS"
    elif spec.name == "cpudiff" and exit_code == 0 and re.search(r"test result:\s*ok", output):
        return "PASS"
    elif spec.name == "winehash":
        if exit_code == 0 and re.search(r"(?:^|\n)[A-Za-z0-9_.-]+\s+OK\s+[0-9a-f]{64}\b", output):
            return "UNKNOWN"

    if re.search(r"^SKIP(?:PED)?\b", output, flags=re.MULTILINE):
        return "SKIPPED"
    return "ERROR"
