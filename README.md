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

This repository contains the **M1 identity Core**, the **M2 Universal Schema** (M2.1–M2.14), the published **M3.S1 operational slice** (M3.1–M3.6), **M3.7 bounded parameter validation**, **M3.8 explicit execution policy**, **M3.9 project HMAC policy**, **M3.10 local evidence integrity validation**, and **M3.11 multi-evidence admission gates**. The Core provides a normalized Project Profile, deterministic project identities, a confined runtime, strict canonical `vera://` addresses, a migration ledger, a ProjectIdentity-bound SQLite store, technical audit records, generic entities and relations, append-only knowledge and declared provenance, direct supersession links, hash-verified SQLite assets, immutable associations, generic symbols, work-item records, and declarative capabilities/execution structure. M3 adds immutable closed capability contracts; a local, closed parameter-schema subset; an immutable `ALLOW`/`DENY`/`CONFIRM` policy; the sole `NOOP` runner under `DENY_NETWORK`; immutable execution facts; hashed JSON evidence; immutable admission decisions; a project-level HMAC rule without any persistent secret; derived `PROVEN` proof records; direct work-item dependencies with conjunctive multi-evidence admission gates; and the local `EVIDENCE_HASH` validator.

The enforced proof chain is deliberately narrow: an execution is not evidence; `PASS` evidence is not admitted automatically; a derived proof requires existing `PASS` evidence and an `ADMITTED` decision; and a proof record does not rewrite the historical knowledge status. Where requested, HMAC secrets are supplied only in memory and only their digest is persisted. A gate merely reads existing admissions: it never runs a capability, creates an admission, changes knowledge, or declares work complete.

The repository still provides no external file or document fetch, implicit network access, arbitrary shell, generic external runner, general JSON Schema validation, interactive confirmation or policy revision, validator of business content or external oracle, HMAC rotation/revocation/expiration or alternate algorithms, gate quorum/disjunction/weighting or expiration, work-item lifecycle or graph traversal, production MCP surface, ARET importer/pack, dashboard, or claimed ARET parity. Those omissions are intentional and remain separately gated.

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

The `identity` command validates the profile and prints its deterministic SHA-256 identity. The `inspect` command resolves project roots, optional local VCS markers, runtime, SQLite location, and artifact directory without opening a store or running Git. The `init` command opens only the profile-bound runtime, applies the checksum-protected migration ledger, records the ProjectIdentity and prints the resulting metadata. The public Python Core exposes exact, bounded services for the universal schema and M3: `CapabilityContractService`, `CapabilityPolicyService`, `ExecutionService.run_noop`, `EvidenceService`, `AdmissionService`, `ProofPolicyService`, `ProofService`, `ValidatorService`, and `GateService` supplement the persistence services. A contract parameter schema is limited to an object root, named scalar properties, `required`, and `additionalProperties`; it is deliberately not general JSON Schema. A capability receives one immutable policy decision, `ALLOW`, `DENY`, or `CONFIRM`; only `ALLOW` permits `ExecutionService.run_noop` after parameter validation. `DENY`, `CONFIRM`, and no policy refuse before runner-side writes. `ExecutionService.run_noop` accepts only an existing `NOOP` / `DENY_NETWORK` contract with `yields_proof=false`; it starts no process, accesses no file, and contacts no network. `AdmissionService` admits only existing `PASS` evidence. `ProofPolicyService` requires a singleton `HMAC_SHA256` project rule before a derived proof; where HMAC is required, its secret is supplied only in memory and only its digest is persisted. `ProofService` creates a separate immutable proof record only from knowledge plus admitted `PASS` evidence, leaving knowledge untouched. `ValidatorService` registers only `EVIDENCE_HASH` and writes a separate `PASS` or `FAIL` integrity result by recomputing the evidence’s canonical JSON hash; that result never admits evidence or promotes knowledge. `GateService` adds direct dependencies with cycle refusal, can append additional evidence requirements to a gate, and evaluates all required existing admissions conjunctively, without any execution or promotion side effect.

## Roadmap

| Milestone | Outcome |
|---|---|
| **M0 — Governance baseline** | Invariants, decoupling matrix, test conventions, provenance rules, naming audit, and independent package namespace. |
| **M1 — Universal identity and profile** | Canonical Project Profile, profile/project/workspace hashes, confined runtime, mono/multi/no-Git resolution, and generic strict `vera://` addressing. Technical gates verified; ARET parity remains out of scope. |
| **M2 — Universal Schema** | **Delivered and gated:** M2.1–M2.14 provide the SQLite substrate; generic entities and relations; append-only knowledge, declared provenance and direct supersession; hash-verified SQLite assets and explicit knowledge–asset associations; immutable symbols and work items; and declarative Capability/Execution schemas. M2.EXIT passed without a parité ARET claim. |
| **M3 — Capability / Evidence / Gates** | **In progress. M3.S1 and M3.7–M3.11 delivered:** closed contracts, bounded local parameter validation, immutable `ALLOW`/`DENY`/`CONFIRM` policy, a `NOOP`/`DENY_NETWORK` runner, executions, hashed evidence, admission, project HMAC policy without secret persistence, derived proof, conjunctive multi-evidence admission gates and the local `EVIDENCE_HASH` validator. Deferred: business/external validators, additional runners, advanced graph/lifecycle and CLI/MCP surface. An execution event is never a proof. |
| **M4 — ARET compatibility pack** | Read-only importer, `ARET://` compatibility reader, profile, toolchain declarations and parity suite, all isolated from the Core. |
| **M5 — MCP compiler and adapters** | Generated manifest, stable MCP Core API, runtime adapters, instructions, hooks and doctor. |
| **M6+ — CLI, dashboard, multi-domain conformance** | Project scanner, configuration workflow, installation, visual editor and cross-domain fixtures. |

## Provenance and boundaries

VERA-MMU is informed by the invariant-driven design of [ARET-MMU][1], but it is a **separate repository and implementation**. No ARET-MMU source code is copied into this foundation. Any future migration adapter must explicitly record the originating commit, hashes, source paths, and transformation report.

The repository is public, but a formal licence must be selected by the project owner before third-party reuse or releases. Until then, contributors should treat the contents as non-redistributable unless the owner states otherwise.

## References

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — reference repository"
