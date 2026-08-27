"""Bounded stdio bridge for the VERA desktop application; never a network server."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hmac
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable, Mapping, Sequence

from .adapter_catalog import adapter_spec, call_adapter_json
from .agent_profiles import builtin_agent_profiles
from .capability_builder import CapabilityDraftPreview, apply_capability_draft, preview_capability_draft
from .coverage_report import compile_coverage_report
from .identity import load_profile
from .read_api import ReadService
from .memory_sync import automatic_memory_sync
from .project_bootstrap import (
    ProjectBootstrapError,
    ProjectInitializationPreview,
    apply_project_initialization,
    preview_project_initialization,
)
from .project_operations import ProjectOperationError, scan_project
from .store import MemoryStore, StoreError

BRIDGE_FORMAT = "vera-desktop-bridge/v1"
MAX_MESSAGE_BYTES = 16_384
_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}")


class DesktopBridgeError(StoreError):
    """Raised when the native parent supplies an unsafe bridge configuration."""


@dataclass(frozen=True)
class _CachedPreview:
    kind: str
    value: object


class DesktopBridge:
    """Route a small, versioned request set to existing VERA operations.

    The selected project root is supplied by the native desktop parent, never by
    a WebView request. The nonce is intentionally not part of a response.
    """

    def __init__(self, project_root: str | Path, *, nonce: str) -> None:
        self._project_root = _root(project_root)
        if not isinstance(nonce, str) or len(nonce) < 24 or len(nonce) > 256:
            raise DesktopBridgeError("Nonce de bridge invalide.")
        self._nonce = nonce
        self._previews: dict[str, _CachedPreview] = {}
        self._handlers: Mapping[str, Callable[[dict[str, Any]], dict[str, object]]] = {
            "project.scan": self._scan,
            "project.status": self._project_status,
            "project.init.preview": self._initialization_preview,
            "project.init.apply": self._initialization_apply,
            "capability.preview": self._capability_preview,
            "capability.apply": self._capability_apply,
            "memory.sync": self._memory_sync,
            "agents.list": self._agents_list,
            "adapter.generate": self._adapter_generate,
            "adapter.stage": self._adapter_stage,
            "adapter.install.preview": self._adapter_install_preview,
            "adapter.install.apply": self._adapter_install_apply,
            "adapter.doctor": self._adapter_doctor,
        }

    @property
    def project_root(self) -> Path:
        """Return the native-selected root for native-parent diagnostics only."""
        return self._project_root

    def handle_line(self, line: str) -> str:
        """Validate one JSON line and return exactly one normalized JSON response."""
        if not isinstance(line, str) or len(line.encode("utf-8")) > MAX_MESSAGE_BYTES:
            return _error(None, "MESSAGE_TOO_LARGE", "Message bridge trop volumineux.")
        try:
            request = json.loads(line)
        except (TypeError, json.JSONDecodeError):
            return _error(None, "JSON_INVALID", "Message bridge JSON invalide.")
        request_id = request.get("id") if isinstance(request, dict) and isinstance(request.get("id"), str) else None
        try:
            payload = self._request(request)
        except _ProtocolError as exc:
            return _error(request_id, exc.code, exc.message)
        except (ProjectBootstrapError, ProjectOperationError, StoreError, ValueError) as exc:
            return _error(request_id, "OPERATION_REFUSED", str(exc))
        return json.dumps({"format": BRIDGE_FORMAT, "id": payload["id"], "ok": True, "result": payload["result"]}, ensure_ascii=False, sort_keys=True)

    def _request(self, request: object) -> dict[str, object]:
        if not isinstance(request, dict) or set(request) != {"format", "id", "nonce", "operation", "input"}:
            raise _ProtocolError("ENVELOPE_INVALID", "Enveloppe bridge invalide.")
        request_id = request["id"]
        if not isinstance(request_id, str) or _REQUEST_ID.fullmatch(request_id) is None:
            raise _ProtocolError("ENVELOPE_INVALID", "Identifiant de requête invalide.")
        if request["format"] != BRIDGE_FORMAT:
            raise _ProtocolError("ENVELOPE_INVALID", "Version de protocole bridge invalide.")
        nonce = request["nonce"]
        if not isinstance(nonce, str) or not hmac.compare_digest(nonce, self._nonce):
            raise _ProtocolError("NONCE_INVALID", "Nonce de bridge refusé.")
        operation = request["operation"]
        if not isinstance(operation, str):
            raise _ProtocolError("ENVELOPE_INVALID", "Opération bridge invalide.")
        handler = self._handlers.get(operation)
        if handler is None:
            raise _ProtocolError("OPERATION_UNKNOWN", "Opération bridge inconnue.")
        value = request["input"]
        if not isinstance(value, dict):
            raise _ProtocolError("INPUT_INVALID", "Entrée bridge invalide.")
        return {"id": request_id, "result": handler(value)}

    def _scan(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, set())
        return scan_project(self._project_root).as_dict()

    def _project_status(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, set())
        profile_path = self._profile_path()
        with MemoryStore.open(load_profile(profile_path), profile_path) as store:
            return {
                "coverage": compile_coverage_report(store).as_dict(),
                "vcs": ReadService(store).vcs_status(),
            }

    def _initialization_preview(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, {"template", "projectId", "projectName"})
        template = _string(value, "template")
        project_id = _string(value, "projectId")
        project_name = _string(value, "projectName")
        preview = preview_project_initialization(self._project_root, template=template, project_id=project_id, project_name=project_name)
        self._previews[preview.preview_hash] = _CachedPreview("project.init", preview)
        return preview.as_dict()

    def _initialization_apply(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, {"previewHash", "confirm"})
        preview_hash = _string(value, "previewHash")
        confirm = value.get("confirm")
        if confirm is not True:
            raise _ProtocolError("CONFIRMATION_REQUIRED", "Application refusée sans confirmation explicite.")
        cached = self._previews.get(preview_hash)
        if cached is None or cached.kind != "project.init":
            raise _ProtocolError("PREVIEW_UNKNOWN", "Preview inconnue, expirée ou étrangère.")
        result = apply_project_initialization(self._project_root, cached.value, confirm=True)
        del self._previews[preview_hash]
        return result.as_dict()

    def _capability_preview(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, {"identifier", "name", "kind", "version", "description"})
        profile_path = self._profile_path()
        with MemoryStore.open(load_profile(profile_path), profile_path) as store:
            preview = preview_capability_draft(
                store,
                identifier=_string(value, "identifier"),
                name=_string(value, "name"),
                kind=_string(value, "kind"),
                version=_string(value, "version"),
                description=_optional_string(value, "description"),
            )
        self._previews[preview.preview_hash] = _CachedPreview("capability", preview)
        return preview.as_dict()

    def _capability_apply(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, {"previewHash", "confirm"})
        preview_hash = _string(value, "previewHash")
        if value.get("confirm") is not True:
            raise _ProtocolError("CONFIRMATION_REQUIRED", "Application refusée sans confirmation explicite.")
        cached = self._previews.get(preview_hash)
        if cached is None or cached.kind != "capability" or not isinstance(cached.value, CapabilityDraftPreview):
            raise _ProtocolError("PREVIEW_UNKNOWN", "Preview de capability inconnue, expirée ou étrangère.")
        profile_path = self._profile_path()
        with MemoryStore.open(load_profile(profile_path), profile_path) as store:
            result = apply_capability_draft(store, cached.value, confirm=True)
        del self._previews[preview_hash]
        return result

    def _agents_list(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, set())
        return {"format": "vera-agent-profiles/v1", "profiles": [profile.as_dict() for profile in builtin_agent_profiles().values()]}

    def _memory_sync(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, set())
        profile_path = self._profile_path()
        with MemoryStore.open(load_profile(profile_path), profile_path) as store:
            return automatic_memory_sync(store, "DESKTOP_MEMORY_SYNC")

    def _adapter_generate(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, {"agentProfileId"})
        profile = self._agent_profile(value)
        from .project_operations import compile_generation_preview

        profile_path = self._profile_path()
        with MemoryStore.open(load_profile(profile_path), profile_path) as store:
            return compile_generation_preview(store, profile.adapter).as_dict()

    def _adapter_stage(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, {"agentProfileId", "confirm"})
        profile = self._agent_profile(value)
        if value.get("confirm") is not True:
            raise _ProtocolError("CONFIRMATION_REQUIRED", "Staging refusé sans confirmation explicite.")
        result = _adapter_result(adapter_spec(profile.adapter).stage_entry, ["--profile", str(self._profile_path()), "--confirm"])
        return result

    def _adapter_install_preview(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, {"agentProfileId"})
        profile = self._agent_profile(value)
        result = _adapter_result(adapter_spec(profile.adapter).configure_entry, ["--profile", str(self._profile_path())])
        preview_hash = sha256(_json(result).encode()).hexdigest()
        self._previews[preview_hash] = _CachedPreview("adapter.install", (profile.id, result))
        return {"previewHash": preview_hash, "preview": result}

    def _adapter_install_apply(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, {"previewHash", "confirm"})
        preview_hash = _string(value, "previewHash")
        if value.get("confirm") is not True:
            raise _ProtocolError("CONFIRMATION_REQUIRED", "Installation refusée sans confirmation explicite.")
        cached = self._previews.get(preview_hash)
        if cached is None or cached.kind != "adapter.install" or not isinstance(cached.value, tuple) or len(cached.value) != 2 or not isinstance(cached.value[0], str):
            raise _ProtocolError("PREVIEW_UNKNOWN", "Preview inconnue, expirée ou étrangère.")
        agent_profile_id = cached.value[0]
        profile = builtin_agent_profiles().get(agent_profile_id)
        if profile is None:
            raise _ProtocolError("PREVIEW_UNKNOWN", "Agent Profile mémorisé invalide.")
        spec = adapter_spec(profile.adapter)
        current = _adapter_result(spec.configure_entry, ["--profile", str(self._profile_path())])
        if cached.value[1] != current:
            raise _ProtocolError("PREVIEW_STALE", "Preview périmée : le projet a changé depuis son affichage.")
        result = _adapter_result(spec.configure_entry, ["--profile", str(self._profile_path()), "--apply-project", "--confirm"])
        del self._previews[preview_hash]
        return result

    def _adapter_doctor(self, value: dict[str, Any]) -> dict[str, object]:
        _exact_input(value, {"agentProfileId"})
        profile = self._agent_profile(value)
        spec = adapter_spec(profile.adapter)
        profile_path = self._profile_path()
        configuration = self._project_root / spec.config
        with MemoryStore.open(load_profile(profile_path), profile_path) as store:
            runtime = store.locator.runtime_dir / "generated" / spec.runtime
        if runtime.is_symlink() or configuration.is_symlink():
            raise StoreError("Cible doctor symlinkée : refus de diagnostic ambigu.")
        return {
            "format": "vera-doctor-report/v1",
            "adapter": profile.adapter,
            "coverage": spec.coverage,
            "runtime": "RUNTIME_READY" if runtime.is_file() else "RUNTIME_MISSING",
            "configuration": "CONFIGURED" if configuration.exists() else "CONFIG_ABSENT",
            "host": "NOT_OBSERVED",
            "userScope": "NOT_OBSERVED",
        }

    def _agent_profile(self, value: Mapping[str, Any]):
        agent_profile_id = _string(value, "agentProfileId")
        profile = builtin_agent_profiles().get(agent_profile_id)
        if profile is None:
            raise _ProtocolError("INPUT_INVALID", "Agent Profile bridge inconnu.")
        return profile

    def _profile_path(self) -> Path:
        parent = self._project_root / ".vera-mmu"
        profile = parent / "project.yaml"
        if parent.is_symlink() or profile.is_symlink() or not profile.is_file():
            raise StoreError("Projet VERA non initialisé ou profil project-local ambigu.")
        return profile


@dataclass(frozen=True)
class _ProtocolError(Exception):
    code: str
    message: str


def _root(value: str | Path) -> Path:
    source = Path(value).expanduser()
    if source.is_symlink():
        raise DesktopBridgeError("Racine desktop symlinkée refusée.")
    try:
        target = source.resolve(strict=True)
    except OSError as exc:
        raise DesktopBridgeError("Racine desktop introuvable.") from exc
    if not target.is_dir():
        raise DesktopBridgeError("Racine desktop non répertoire.")
    return target


def _exact_input(value: Mapping[str, Any], expected: set[str]) -> None:
    if set(value) != expected:
        raise _ProtocolError("INPUT_INVALID", "Champs d’entrée bridge interdits ou manquants.")


def _string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise _ProtocolError("INPUT_INVALID", f"Champ bridge invalide : {key}.")
    return item


def _optional_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise _ProtocolError("INPUT_INVALID", f"Champ bridge invalide : {key}.")
    return item


def _error(request_id: str | None, code: str, message: str) -> str:
    return json.dumps({"format": BRIDGE_FORMAT, "id": request_id, "ok": False, "error": {"code": code, "message": message}}, ensure_ascii=False, sort_keys=True)


def _adapter_result(entry: str, args: list[str]) -> dict[str, object]:
    code, payload = call_adapter_json(entry, args)
    if code != 0 or payload.get("ok") is not True:
        raise StoreError(str(payload.get("error", "Opération adapter refusée.")))
    return {key: value for key, value in payload.items() if key != "ok"}


def _json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def desktop_bridge_main(argv: Sequence[str] | None = None) -> int:
    """Run the isolated desktop sidecar over stdio; never listen on a socket."""
    parser = argparse.ArgumentParser(description="Bridge stdio borné pour application desktop VERA.")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--nonce", required=True)
    args = parser.parse_args(argv)
    try:
        bridge = DesktopBridge(args.project_root, nonce=args.nonce)
    except DesktopBridgeError as exc:
        print(_error(None, "BRIDGE_START_REFUSED", str(exc)), flush=True)
        return 2
    for line in sys.stdin:
        print(bridge.handle_line(line.rstrip("\r\n")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(desktop_bridge_main())
