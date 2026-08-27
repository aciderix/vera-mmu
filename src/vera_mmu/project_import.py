"""Explicit, provenance-preserving imports of existing project documents (M11-B)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from typing import Sequence

from .import_batches import (
    ImportBatchError,
    ImportBatchService,
    ImportKnowledgeInput,
    ImportKnowledgeSourceInput,
    KnowledgeImportBatchInput,
    KnowledgeSourceImportBatchInput,
)
from .knowledge import Knowledge, KnowledgeError, KnowledgeService
from .project_policy import ProjectPolicyError, require_project_write
from .provenance import KnowledgeSource, KnowledgeSourceService
from .store import MemoryStore, StoreError


PROJECT_DOCUMENT_IMPORT_FORMAT = "vera-project-document-import/v1"
_MAX_DOCUMENTS = 100
_MAX_DOCUMENT_BYTES = 1_048_576


class ProjectImportError(StoreError):
    """Raised when an existing-project document import is invalid, stale or unsafe."""


@dataclass(frozen=True)
class ProjectDocumentPreview:
    """One verified source file included in an explicit project-document import preview."""

    path: str
    sha256: str
    line_count: int
    content: str


@dataclass(frozen=True)
class ProjectDocumentImportPreview:
    """A deterministic, non-writing preview tied to exact source document bytes."""

    format: str
    batch_id: str
    knowledge_type_id: str
    knowledge_type_label: str
    actor: str
    documents: tuple[ProjectDocumentPreview, ...]
    source_snapshot_sha256: str
    preview_hash: str


@dataclass(frozen=True)
class ProjectDocumentImportResult:
    """Observed knowledge and provenance created by a committed import or returned by exact replay."""

    status: str
    batch_id: str
    knowledge: tuple[Knowledge, ...]
    provenance: tuple[KnowledgeSource, ...]
    source_snapshot_sha256: str


def preview_project_document_import(
    store: MemoryStore,
    document_paths: Sequence[str],
    *,
    batch_id: str,
    knowledge_type_id: str,
    knowledge_type_label: str,
    actor: str = "system",
) -> ProjectDocumentImportPreview:
    """Read an explicit bounded set of regular UTF-8 project files without writing any VERA state."""
    if not isinstance(store, MemoryStore):
        raise ProjectImportError("Aperçu d’import exige un MemoryStore VERA actif.")
    normalized_batch = _identifier(batch_id, "batch_id")
    type_id = _identifier(knowledge_type_id, "knowledge_type_id")
    label = _text(knowledge_type_label, "knowledge_type_label", 256)
    actor_value = _text(actor, "actor", 256)
    if not isinstance(document_paths, Sequence) or isinstance(document_paths, (str, bytes)) or not 1 <= len(document_paths) <= _MAX_DOCUMENTS:
        raise ProjectImportError("L’import de documents exige entre 1 et 100 chemins explicites.")
    documents: list[ProjectDocumentPreview] = []
    seen: set[str] = set()
    for raw_path in document_paths:
        relative = _relative_document_path(raw_path)
        if relative in seen:
            raise ProjectImportError("Un import de documents ne peut pas dupliquer un chemin source.")
        seen.add(relative)
        source = _resolve_document(store, relative)
        try:
            payload = source.read_bytes()
            if len(payload) > _MAX_DOCUMENT_BYTES:
                raise ProjectImportError("Document source hors borne de taille.")
            content = payload.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ProjectImportError("Document source illisible en UTF-8.") from exc
        if not content.strip():
            raise ProjectImportError("Document source vide : import refusé.")
        documents.append(
            ProjectDocumentPreview(
                path=relative,
                sha256=sha256(payload).hexdigest(),
                line_count=content.count("\n") + 1,
                content=content,
            )
        )
    documents_tuple = tuple(sorted(documents, key=lambda item: item.path))
    snapshot = sha256(
        "\0".join(f"{item.path}\0{item.sha256}" for item in documents_tuple).encode("utf-8")
    ).hexdigest()
    preview_material = "\0".join(
        [PROJECT_DOCUMENT_IMPORT_FORMAT, normalized_batch, type_id, label, actor_value, snapshot, *[item.sha256 for item in documents_tuple]]
    )
    return ProjectDocumentImportPreview(
        format=PROJECT_DOCUMENT_IMPORT_FORMAT,
        batch_id=normalized_batch,
        knowledge_type_id=type_id,
        knowledge_type_label=label,
        actor=actor_value,
        documents=documents_tuple,
        source_snapshot_sha256=snapshot,
        preview_hash=sha256(preview_material.encode("utf-8")).hexdigest(),
    )


def apply_project_document_import(
    store: MemoryStore,
    preview: ProjectDocumentImportPreview,
    *,
    confirm: bool,
) -> ProjectDocumentImportResult:
    """Commit an exact non-merging import after re-reading and matching every previewed source file."""
    if not isinstance(store, MemoryStore) or not isinstance(preview, ProjectDocumentImportPreview):
        raise ProjectImportError("Aperçu d’import de documents invalide.")
    if preview.format != PROJECT_DOCUMENT_IMPORT_FORMAT:
        raise ProjectImportError("Format d’aperçu d’import inconnu.")
    try:
        require_project_write(store, confirm=confirm)
    except ProjectPolicyError as exc:
        raise ProjectImportError("Import de documents refusé par la policy projet.") from exc
    _validate_preview_fresh(store, preview)
    if store.connection.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]:
        existing = _existing_import_result(store, preview)
        if existing is not None:
            return existing
        raise ProjectImportError("Import de projet refusé : mémoire cible non vide, fusion interdite.")

    try:
        with store.transaction() as connection:
            row = connection.execute(
                "SELECT label, description FROM knowledge_type WHERE id = ?",
                (preview.knowledge_type_id,),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO knowledge_type(id, label, description, created_at, created_by) "
                    "VALUES(?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (preview.knowledge_type_id, preview.knowledge_type_label, "Documents explicitement importés depuis le projet.", preview.actor),
                )
                store.append_audit(
                    connection,
                    "KNOWLEDGE_TYPE_REGISTERED",
                    {"knowledge_type_id": preview.knowledge_type_id, "actor": preview.actor},
                )
            elif str(row[0]) != preview.knowledge_type_label or str(row[1]) != "Documents explicitement importés depuis le projet.":
                raise ProjectImportError("Type knowledge existant incompatible avec l’import de projet.")

            knowledge_inputs = tuple(
                ImportKnowledgeInput(
                    identifier=f"project-document--{index:03d}",
                    source_identifier=item.path,
                    payload={
                        "type_id": preview.knowledge_type_id,
                        "status": "OBSERVED",
                        "title": item.path,
                        "content": item.content,
                        "metadata": {
                            "import": {
                                "format": PROJECT_DOCUMENT_IMPORT_FORMAT,
                                "path": item.path,
                                "source_hash": item.sha256,
                            }
                        },
                    },
                )
                for index, item in enumerate(preview.documents, start=1)
            )
            knowledge_result = ImportBatchService(store).commit_knowledge_import_batch(
                KnowledgeImportBatchInput(
                    batch_id=preview.batch_id,
                    source_system="project-documents",
                    source_snapshot_sha256=preview.source_snapshot_sha256,
                    mapping_id="project-document-to-knowledge-v1",
                    resources=knowledge_inputs,
                    actor=preview.actor,
                    require_empty_target=True,
                )
            )
            source_inputs = tuple(
                ImportKnowledgeSourceInput(
                    identifier=f"project-document-source-{index:03d}",
                    source_identifier=item.path,
                    knowledge_identifier=knowledge.id,
                    payload={
                        "repository": "project-local",
                        "revision": store.identity.project_hash,
                        "path": item.path,
                        "start_line": 1,
                        "end_line": item.line_count,
                        "section": "full-document",
                        "source_hash": item.sha256,
                    },
                )
                for index, (item, knowledge) in enumerate(zip(preview.documents, knowledge_result.resources, strict=True), start=1)
            )
            source_result = ImportBatchService(store).commit_knowledge_source_import_batch(
                KnowledgeSourceImportBatchInput(
                    batch_id=f"{preview.batch_id}-sources",
                    source_system="project-documents",
                    source_snapshot_sha256=preview.source_snapshot_sha256,
                    mapping_id="project-document-provenance-v1",
                    resources=source_inputs,
                    actor=preview.actor,
                    require_empty_target=True,
                )
            )
    except (ImportBatchError, KnowledgeError) as exc:
        raise ProjectImportError("Import de documents refusé ou rollbacké atomiquement.") from exc
    return ProjectDocumentImportResult(
        status="ALREADY_IMPORTED" if knowledge_result.was_already_committed else "IMPORTED",
        batch_id=preview.batch_id,
        knowledge=knowledge_result.resources,
        provenance=source_result.resources,
        source_snapshot_sha256=preview.source_snapshot_sha256,
    )


def _validate_preview_fresh(store: MemoryStore, preview: ProjectDocumentImportPreview) -> None:
    expected = preview_project_document_import(
        store,
        tuple(item.path for item in preview.documents),
        batch_id=preview.batch_id,
        knowledge_type_id=preview.knowledge_type_id,
        knowledge_type_label=preview.knowledge_type_label,
        actor=preview.actor,
    )
    if expected != preview:
        raise ProjectImportError("Aperçu d’import de documents altéré ou périmé.")


def _existing_import_result(store: MemoryStore, preview: ProjectDocumentImportPreview) -> ProjectDocumentImportResult | None:
    service = ImportBatchService(store)
    batch = service.get_knowledge_import_batch(preview.batch_id)
    source_batch = service.get_knowledge_source_import_batch(f"{preview.batch_id}-sources")
    if batch is None or source_batch is None:
        return None
    if batch.source_snapshot_sha256 != preview.source_snapshot_sha256 or source_batch.source_snapshot_sha256 != preview.source_snapshot_sha256:
        raise ProjectImportError("Ledger d’import existant divergent : refus de fusion.")
    try:
        knowledge = tuple(KnowledgeService(store).get(f"project-document--{index:03d}") for index, _ in enumerate(preview.documents, start=1))
        provenance = tuple(
            KnowledgeSourceService(store).get(f"project-document-source-{index:03d}")
            for index, _ in enumerate(preview.documents, start=1)
        )
    except (KnowledgeError, Exception) as exc:
        raise ProjectImportError("Ledger d’import incomplet ou illisible.") from exc
    return ProjectDocumentImportResult(
        status="ALREADY_IMPORTED",
        batch_id=preview.batch_id,
        knowledge=knowledge,
        provenance=provenance,
        source_snapshot_sha256=preview.source_snapshot_sha256,
    )


def _relative_document_path(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value or "\\" in value:
        raise ProjectImportError("Chemin document invalide.")
    path = Path(value)
    if path.is_absolute() or PureWindowsPath(value).drive or ".." in path.parts or path == Path("."):
        raise ProjectImportError("Chemin document hors projet ou non canonique.")
    return path.as_posix()


def _resolve_document(store: MemoryStore, relative: str) -> Path:
    candidates: list[Path] = []
    for root in store.workspace.roots:
        candidate = root / relative
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise ProjectImportError("Document hors des racines workspace ou introuvable.") from exc
        if candidate.is_symlink() or resolved.is_symlink() or not resolved.is_file():
            raise ProjectImportError("Document source non régulier ou symlinké.")
        candidates.append(resolved)
    if len(candidates) != 1:
        raise ProjectImportError("Chemin document ambigu entre les racines de workspace.")
    return candidates[0]


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 64:
        raise ProjectImportError(f"{label} invalide.")
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in value) or value[0] == "-" or value[-1] == "-":
        raise ProjectImportError(f"{label} non canonique.")
    return value


def _text(value: object, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum or "\x00" in value:
        raise ProjectImportError(f"{label} invalide.")
    return value
