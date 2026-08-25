# VERA-MMU

> **Verifiable Epistemics & Relational Architecture**
>
> *A proof-oriented memory, provenance, and governance engine for AI-assisted projects.*

VERA-MMU is an independent foundation for a project-aware MCP. It ensures that an agent’s assertion does not become a project fact merely because it was stated in a conversation. Canonical memory, exact `vera://` addressing, provenance, execution records, admissible evidence, policy decisions, and resumable work are first-class objects.

The product is intentionally broader than software delivery. The same Core must support software, research, data, documentation, game, and hardware projects through **Project Profiles** and optional **Domain Packs**. Its first compatibility target will be an ARET domain pack; ARET-specific concepts, toolchains, and rules must never become Core dependencies.

## Product principles

| Principle | Operational meaning |
|---|---|
| **Canonical state is external to the model** | SQLite-backed state, profiles, artifacts, and audit records—not model text—are the source of truth. |
| **Discovery is not proof** | `FIND` identifies candidates; `READ` retrieves exact canonical objects; neither a search result nor a model statement is evidence. |
| **Knowledge is append-only** | Material corrections create superseding records; silent rewrites are rejected. |
| **Proof is traceable** | A promotable assertion must link to admissible `PASS` evidence and to the execution and environment that produced it. |
| **Capabilities are closed and policy-gated** | The model selects a declared capability with schema-bounded parameters; it never submits an arbitrary shell command. |
| **Continuity is verifiable** | Front state, handoffs, resume acknowledgements, project identity, profiles, and generated runtime are hash-linked. |
| **Relations are first-class** | Knowledge, entities, work, executions, evidence, artifacts, and policies are connected through explicit typed relations. |
| **Domains remain optional** | Business vocabulary, tools, workflows, and requirements live in packs and profiles—not in the Core. |

## Canonical identity

| Surface | Identifier |
|---|---|
| Public project name | **VERA-MMU** |
| Long form | **Verifiable Epistemics & Relational Architecture** |
| Repository / distribution | `vera-mmu` |
| Python namespace | `vera_mmu` |
| CLI | `vmmu` |
| Canonical resource scheme | `vera://<project>/<resource>/<id>` |
| Project runtime directory | `.vera-mmu/` |

The composed name must be used consistently in public documentation and tooling. The naming audit records existing uses of the bare term “Vera”; VERA-MMU makes no claim of exclusive ownership over that term.

## Current status

This repository now contains the **M1 identity Core**, the **M2.1 SQLite substrate**, the **M2.2 generic Entity Registry**, the **M2.3 Relation Registry**, the **M2.4 Knowledge Registry**, the **M2.5 Knowledge Source Registry**, the **M2.6 Knowledge Supersession Registry**, the **M2.7 Asset Registry**, the **M2.8 Knowledge-Asset Link Registry**, the **M2.9 Bounded Knowledge-Asset Index**, and the **M2.10 Asset Source Registry**: a safely normalized Project Profile, deterministic project identities, a `WorkspaceResolver`, a confined `RuntimeLocator`, strict canonical `vera://` addresses, an immutable migration ledger, a ProjectIdentity-bound SQLite store, technical audit records, registered generic entity types, exact entity creation/read, immutable typed edges between entities, append-only knowledge assertions with content hashes, immutable declared source slices, explicit direct supersession links, binary Core assets whose SHA-256 and declared size are rechecked before byte reading, exact immutable associations between existing knowledge and assets, direct ordered/bounded indexes of those associations, and declared document-source slices attached to assets. A supersession link never rewrites the predecessor’s content, hash, metadata, provenance, or status. A knowledge–asset link does not read an asset, modify either endpoint, or make that asset evidence. Its index returns only link metadata for one exact endpoint; it does not read endpoint content or perform a free search. An asset source is a declared reference only: it does not open or fetch the source document, compare its hash to the asset, or confer evidence semantics. The asset registry stores small bytes in SQLite; it does not accept file paths or open external files. It does **not** yet provide document fetch or verification, import batches, status mutation or `SUPERSEDED`, version counters, lineage traversal, `PROVEN` admission, evidence services, executions or validators, gates, free-text knowledge search, generic-relation integration, symbols, bundles, a production MCP server, a generic capability runner, an ARET migration tool, or a dashboard.

## Continuity records

The universalization programme is governed through three linked, versioned documents. The [living work plan](docs/continuity/UNIVERSALIZATION_WORKPLAN.md) controls scope and gates; the [factual project memory](docs/continuity/PROJECT_MEMORY.md) preserves durable facts, decisions, risks, and the active resume; and the [engineering log](docs/continuity/ENGINEERING_LOG.md) records searchable chronology, runs, evidence, comparisons, walls, and handoffs. These records must be read before material work after an interruption or context compaction.

## Repository layout

```text
src/vera_mmu/             # Installable Python package and stable Core namespace
docs/                     # Invariants, architecture, decoupling ledger, naming audit
profiles/                 # Versioned Project Profile templates
domains/                  # Optional domain packs; ARET is a future reference pack
tests/                    # Unit, security, conformance, and compatibility tests
```

## Local start

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m vera_mmu identity profiles/minimal/project.yaml
PYTHONPATH=src python3 -m vera_mmu inspect profiles/minimal/project.yaml
PYTHONPATH=src python3 -m vera_mmu init profiles/minimal/project.yaml
```

The `identity` command validates the profile and prints its deterministic SHA-256 identity. The `inspect` command resolves project roots, optional local VCS markers, runtime, SQLite location, and artifact directory without opening a store or running Git. The `init` command opens only the profile-bound runtime, applies the checksum-protected migration ledger, records the ProjectIdentity and prints the resulting metadata. The public Python Core additionally exposes `EntityService` for registered generic types and exact entity creation/read, `RelationService` for registered immutable edges between existing entities, `KnowledgeService` for append-only hash-verified assertions under safe initial statuses, `KnowledgeSourceService` for immutable, line-bounded document references, `KnowledgeSupersessionService` to record or read one exact direct predecessor/successor link, `AssetService` for small binary assets stored in SQLite, `KnowledgeAssetLinkService` for exact declarative knowledge–asset pairs and their direct bounded indexes, and `AssetSourceService` for immutable declared document-source slices attached to assets. `KnowledgeSourceService` and `AssetSourceService` treat sources solely as declared data: neither opens, fetches, verifies, imports, or compares a source document. `KnowledgeSupersessionService` rejects unknown endpoints, self-links, duplicate endpoints and cycles; it does not change knowledge status or expose lineage traversal. `AssetService` accepts bytes rather than file paths, records SHA-256/size/media type, and rechecks hash and size before returning content. `KnowledgeAssetLinkService` requires pre-existing endpoints, records immutable pairs, lists only the ordered and bounded direct links of an exact endpoint, never reads asset content through a link, and does not provide a free search, traversal, or evidence semantics. `PROVEN` is explicitly rejected until Evidence Store exists. The implementation remains deliberately bounded: it adds no evidence, policy, execution, validator, gate, filesystem import or export semantics before their explicit tests and contracts exist.

## Roadmap

| Milestone | Outcome |
|---|---|
| **M0 — Governance baseline** | Invariants, decoupling matrix, test conventions, provenance rules, naming audit, and independent package namespace. |
| **M1 — Universal identity and profile** | Canonical Project Profile, profile/project/workspace hashes, confined runtime, mono/multi/no-Git resolution, and generic strict `vera://` addressing. Technical gates verified; ARET parity remains out of scope. |
| **M2 — Universal persistence** | **M2.1 delivered:** SQLite migration ledger, identity binding, format metadata, technical audit, transaction and CLI initialization. **M2.2 delivered:** generic entity types, exact entities, canonical JSON and atomic creation audit. **M2.3 delivered:** declarative relation types, immutable typed edges between entities, endpoint constraints and atomic creation audit. **M2.4 delivered:** generic knowledge types, append-only hash-verified assertions, safe initial epistemic statuses and atomic creation audit. **M2.5 delivered:** immutable declared document-source slices attached to knowledge, validated paths/lines/SHA-256 and atomic creation audit. **M2.6 delivered:** immutable direct predecessor/successor sidecar for existing knowledge, endpoint uniqueness, anti-cycle checks, exact two-way reads and atomic audit, with no change to the knowledge records. **M2.7 delivered:** small binary assets persisted in SQLite with immutable hash/size/media metadata, exact reads, SHA-256 verification before content return, and atomic creation audit. **M2.8 delivered:** immutable exact associations between existing knowledge and assets, with endpoint foreign keys, duplicate-pair refusal, no endpoint mutation, no implicit byte read, and atomic creation audit. **M2.9 delivered:** direct ordered and bounded indexes of the associations for an exact knowledge or asset endpoint, returning link metadata only with no free search, traversal, content read, or audit mutation. **M2.10 delivered:** immutable document-source slices attached to existing assets, with validated repository/revision/path/lines/SHA-256, exact/bounded reads, and atomic attachment audit; sources are declared only and are never opened, fetched, compared, or treated as proof. Document fetch/verification/import, filesystem paths, source-to-asset comparison, status mutation, `PROVEN`/evidence, execution/validator/gate, free search, lineage traversal, generic-relation integration, symbols, bundles and broader audit remain separate future sub-lots. |
| **M3 — ARET compatibility pack** | Read-only importer, `ARET://` compatibility reader, profile, toolchain declarations, and parity suite. |
| **M4 — Capabilities and gates** | Closed catalog, policy engine, safe runners, validators, executions, and gate engine. |
| **M5 — MCP compiler and adapters** | Generated manifest, stable MCP Core API, runtime adapters, instructions, hooks, and doctor. |
| **M6+ — CLI, dashboard, multi-domain conformance** | Project scanner, configuration workflow, installation, visual editor, and cross-domain fixtures. |

## Provenance and boundaries

VERA-MMU is informed by the invariant-driven design of [ARET-MMU][1], but it is a **separate repository and implementation**. No ARET-MMU source code is copied into this foundation. Any future migration adapter must explicitly record the originating commit, hashes, source paths, and transformation report.

The repository is public, but a formal licence must be selected by the project owner before third-party reuse or releases. Until then, contributors should treat the contents as non-redistributable unless the owner states otherwise.

## References

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — reference repository"
