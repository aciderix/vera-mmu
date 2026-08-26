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

This repository contains the **M1 identity Core**, the **M2 Universal Schema** (M2.1–M2.14), the published **M3.S1 operational slice** (M3.1–M3.6), **M3.7 bounded parameter validation**, **M3.8 explicit execution policy**, **M3.9 project HMAC policy**, **M3.10 local evidence integrity validation**, **M3.11 multi-evidence admission gates**, **M3.12 derived work lifecycle**, **M3.13 validated admission policy**, the **M3.14 closed local `EVIDENCE_HASH` runner**, **M3.15 immutable gate policies**, **M3.16 derived work readiness with optional strict start policy**, **M3.17 local required-field validation**, **M3.18 closed `EVIDENCE_FIELDS` runner**, **M3.19–M3.22 passive direct/transitive/gate/composite blocker diagnostics**, **M3.23 optional strict completion policy**, **M3.24 explicit strict admission–validation binding**, **M3.25 closed runner–validator compatibility catalogue**, the **M3.EXIT terminal Core gate**, the **M4.1 read-only ARET V1 address-compatibility pack**, the **M4.2 declarative legacy-runtime manifest**, the **M4.3 observed ARET V1 schema manifest**, the **M4.4 bounded ARET V1 compatibility profile**, the **M4.5 explicit structural mapping registry**, the **M4.6 fail-closed component-import preparation contract**, the **M4.7 read-only ARET V1 snapshot attestation**, and the **M4.8 clean Git-source identity verification**. The Core provides a normalized Project Profile, deterministic project identities, a confined runtime, strict canonical `vera://` addresses, a migration ledger, a ProjectIdentity-bound SQLite store, technical audit records, generic entities and relations, append-only knowledge and declared provenance, direct supersession links, hash-verified SQLite assets, immutable associations, generic symbols, work-item records, and declarative capabilities/execution structure. M3 adds immutable closed capability contracts; a local, closed parameter-schema subset; an immutable `ALLOW`/`DENY`/`CONFIRM` policy; the local `NOOP`, `EVIDENCE_HASH` and `EVIDENCE_FIELDS` runners under `DENY_NETWORK`; immutable execution facts; hashed JSON evidence; immutable admission decisions; a project-level HMAC rule without any persistent secret; derived `PROVEN` proof records; direct work-item dependencies with multi-evidence admission gates and optional immutable `ALL`/`ANY`/`AT_LEAST` policies; the local `EVIDENCE_HASH` and `EVIDENCE_FIELDS` validators, whose runners accept only their exact matching validator kind and closed parameter schema; a derived lifecycle from append-only work events; derived work readiness and an optional strict start policy; an optional completion policy that can require derived readiness only for `COMPLETE`; and an admission policy that, in strict mode, requires an explicit binding to a pre-existing `PASS` validation of the same evidence before admission.

The enforced proof chain is deliberately narrow: an execution is not evidence; `PASS` evidence is not admitted automatically; a derived proof requires existing `PASS` evidence and an `ADMITTED` decision; and a proof record does not rewrite the historical knowledge status. An explicit admission policy can require a `PASS` validator result before `ADMITTED`; in strict mode it must name that result and it must belong to the same evidence, but it never triggers validation itself. Where requested, HMAC secrets are supplied only in memory and only their digest is persisted. A gate merely reads existing admissions: it never runs a capability, creates an admission, changes knowledge, or declares work complete.

The repository still provides no external file or document fetch, implicit network access, arbitrary shell, generic external runner beyond the three closed local profiles, general JSON Schema validation, interactive confirmation or policy revision, validator of business content or external oracle (the local field validator checks only declared key presence), automatic admission, HMAC rotation/revocation/expiration or alternate algorithms, weighted, temporal, expiration or revocation gate semantics, lifecycle pause/reopen/orchestration or graph behaviour beyond the published passive blocker diagnostics and derived readiness, production MCP surface, ARET importer or functional pack beyond the declarative M4.1–M4.8 compatibility surfaces, dashboard, or claimed ARET parity. Those omissions are intentional and remain separately gated.

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

The `identity` command validates the profile and prints its deterministic SHA-256 identity. The `inspect` command resolves project roots, optional local VCS markers, runtime, SQLite location, and artifact directory without opening a store or running Git. The `init` command opens only the profile-bound runtime, applies the checksum-protected migration ledger, records the ProjectIdentity and prints the resulting metadata. The public Python Core exposes exact, bounded services for the universal schema and M3: `CapabilityContractService`, `CapabilityPolicyService`, `ExecutionService.run_noop`, `ExecutionService.run_evidence_hash`, `EvidenceService`, `AdmissionPolicyService`, `AdmissionService`, `ProofPolicyService`, `ProofService`, `ValidatorService`, `GateService`, and `WorkLifecycleService` supplement the persistence services. A contract parameter schema is limited to an object root, named scalar properties, `required`, and `additionalProperties`; it is deliberately not general JSON Schema. A capability receives one immutable policy decision, `ALLOW`, `DENY`, or `CONFIRM`; only `ALLOW` permits `ExecutionService.run_noop` after parameter validation. `DENY`, `CONFIRM`, and no policy refuse before runner-side writes. `ExecutionService.run_noop` accepts only an existing `NOOP` / `DENY_NETWORK` contract with `yields_proof=false`; it starts no process, accesses no file, and contacts no network. `ExecutionService.run_evidence_hash` accepts only an exact `EVIDENCE_HASH` / `DENY_NETWORK` / `yields_proof=false` contract, an explicit `ALLOW` policy and the two closed parameters `validator_id` and `evidence_id`; it executes the existing local integrity validator and stores its `PASS` or `FAIL` result atomically with a completed execution. It starts no process, accesses no file, contacts no network, creates no evidence, admission or proof, and never promotes knowledge. `ExecutionService.run_evidence_fields` applies the same closed transaction boundary only to an `EVIDENCE_FIELDS` contract and validator; it records a local `PASS`/`FAIL` field-presence verdict plus execution, never an admission or proof. `AdmissionService` admits only existing `PASS` evidence. `ProofPolicyService` requires a singleton `HMAC_SHA256` project rule before a derived proof; where HMAC is required, its secret is supplied only in memory and only its digest is persisted. `ProofService` creates a separate immutable proof record only from knowledge plus admitted `PASS` evidence, leaving knowledge untouched. `ValidatorService` registers only `EVIDENCE_HASH` and `EVIDENCE_FIELDS` and writes a separate `PASS` or `FAIL` integrity result by recomputing the evidence’s canonical JSON hash; that result never admits evidence or promotes knowledge. `EVIDENCE_FIELDS` checks only a bounded immutable list of declared JSON keys and likewise never admits evidence or promotes knowledge. `GateService` adds direct dependencies with cycle refusal, can append additional evidence requirements to a policy-free gate, and evaluates only existing admissions without any execution or promotion side effect. A gate without a policy remains conjunctive (`ALL`); its optional immutable policy may instead select `ANY` or an `AT_LEAST` threshold, after which its evidence requirements are frozen. No weighted, temporal, expiration or revocation semantics are provided. `WorkReadinessService` derives `READY` or `BLOCKED` from existing completed prerequisites and passing gates without writing state; `WorkStartPolicyService` optionally makes only `START` refuse unless that readiness is `READY`. `WorkLifecycleService` records only `START`, `COMPLETE`, or `CANCEL` events and derives the current work state without rewriting the historical `work_item` record; `WorkCompletionPolicyService` can optionally require derived `READY` only for `COMPLETE`, before any event or audit is written. Completion is neither proof nor execution.

## Roadmap

| Milestone | Outcome |
|---|---|
| **M0 — Governance baseline** | Invariants, decoupling matrix, test conventions, provenance rules, naming audit, and independent package namespace. |
| **M1 — Universal identity and profile** | Canonical Project Profile, profile/project/workspace hashes, confined runtime, mono/multi/no-Git resolution, and generic strict `vera://` addressing. Technical gates verified; ARET parity remains out of scope. |
| **M2 — Universal Schema** | **Delivered and gated:** M2.1–M2.14 provide the SQLite substrate; generic entities and relations; append-only knowledge, declared provenance and direct supersession; hash-verified SQLite assets and explicit knowledge–asset associations; immutable symbols and work items; and declarative Capability/Execution schemas. M2.EXIT passed without a parité ARET claim. |
| **M3 — Capability / Evidence / Gates** | **Delivered within the approved bounded Core contract.** M3.EXIT verifies fresh install and upgrade 001→032, the closed chain capability → execution → evidence → validation → admission → proof → gate → readiness → lifecycle, full Core tests, checksums, boundary scans and an isolated wheel. Deferred to M4+: business/external validators, additional runners, weighted/temporal gates, advanced graph/lifecycle, CLI/MCP, dashboard and ARET compatibility. M3 does not claim ARET parity: C05/C06/C16 remain `SPLIT`, C07 remains `BLOCKED` under `MEM-WALL-001`, and parity remains `UNKNOWN`. An execution event is never a proof. |
| **M4 — ARET compatibility pack** | **In progress.** M4.1 parses canonical `ARET://` V1 addresses; M4.2 declares historical runtime names; M4.3 inventories the observed V1 application schema; M4.4 composes those declarations under a profile that explicitly forbids runtime resolution, SQLite reads, imports and VERA writes; M4.5 declares only the three reviewed structural targets (`component→entity`, `function_symbol→symbol`, `brick→work_item`), each requiring a future explicit import; M4.6 binds one future `component→entity` request to an explicit VERA `ProjectIdentity`, a canonical caller-declared source digest, a request ID and an actor, while marking it `PREPARED_NOT_EXECUTED` and `UNVERIFIED_DECLARATION`; M4.7 verifies that declared digest against only the expected regular, non-linked `.aret-memory/aret_memory.sqlite` snapshot under a caller-supplied absolute root, while binding the result to the fixed ARET V1 baseline reference and marking it `ATTESTED_SNAPSHOT_ONLY`; M4.8 binds that attestation to the expected commit and a clean Git worktree using only fixed `rev-parse` and `status` queries with hooks, global/system configuration and optional locks disabled. It does not open SQLite, inspect schema contents, validate remote or signed-commit provenance, or import rows. These surfaces perform no import, migration or conversion. An operational profile adapter, stronger source provenance policy, data mappings, offline importer, provenance/audit and rollback path, toolchain declarations and parity suite remain required and isolated from the Core. |
| **M5 — MCP compiler and adapters** | Generated manifest, stable MCP Core API, runtime adapters, instructions, hooks and doctor. |
| **M6+ — CLI, dashboard, multi-domain conformance** | Project scanner, configuration workflow, installation, visual editor and cross-domain fixtures. |

## Provenance and boundaries

VERA-MMU is informed by the invariant-driven design of [ARET-MMU][1], but it is a **separate repository and implementation**. No ARET-MMU source code is copied into this foundation. Any future migration adapter must explicitly record the originating commit, hashes, source paths, and transformation report.

The repository is public, but a formal licence must be selected by the project owner before third-party reuse or releases. Until then, contributors should treat the contents as non-redistributable unless the owner states otherwise.

## References

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — reference repository"
