# VeriChronicle

> **A deterministic memory, provenance, evidence, and continuity engine for AI-assisted projects.**

VeriChronicle is a new, independent foundation for a project-aware MCP. It is designed to ensure that an agent’s assertions do not become the project’s truth merely because they were stated in a conversation. Canonical memory, exact addressing, provenance, execution records, admissible evidence, policy decisions, and resumable work are first-class objects.

The product is intentionally broader than software delivery. The same Core must support projects in software, research, data, documentation, games, and hardware through **Project Profiles** and optional **Domain Packs**. Its first compatibility target will be an ARET domain pack; ARET-specific concepts, toolchains, and rules must not become Core dependencies.

## Product principles

| Principle | Operational meaning |
|---|---|
| **Canonical state is external to the model** | SQLite-backed state, profiles, artifacts, and audit records—not model text—are the source of truth. |
| **Discovery is not proof** | `FIND` identifies candidates; `READ` retrieves exact canonical objects; neither a search result nor a model statement is evidence. |
| **Knowledge is append-only** | Material corrections create superseding records; silent rewrites are rejected. |
| **Proof is traceable** | A promotable assertion must link to an admissible `PASS` evidence record and to the execution and environment that produced it. |
| **Capabilities are closed and policy-gated** | The model selects a declared capability with schema-bounded parameters; it never submits an arbitrary shell command. |
| **Continuity is verifiable** | Front state, handoffs, resume acknowledgements, project identity, profiles, and generated runtime are hash-linked. |
| **Domains remain optional** | Business vocabulary, tools, workflows, and requirements live in packs and profiles—not in the Core. |

## Current status

This repository is at **M0/M1 foundation**. It establishes the namespace, declared invariants, profile format, architecture boundary, and a minimal deterministic identity utility. It does **not** yet provide a production MCP server, a generic capability runner, an ARET migration tool, or a dashboard.

## Intended repository layout

```text
src/verichronicle/       # Installable Python package and stable Core namespace
docs/                    # Invariants, architecture, decoupling ledger, contribution rules
profiles/                # Versioned Project Profile templates
domains/                 # Optional domain packs; ARET is a future reference pack
tests/                   # Unit, security, conformance, and compatibility tests
```

## Local start

```bash
python3 -m unittest discover -s tests -v
python3 -m verichronicle identity profiles/minimal/project.yaml
```

The current `identity` command validates the minimal profile shape and prints a deterministic SHA-256 profile identity. The implementation is deliberately small so that migration, policy, and execution semantics can be introduced behind explicit tests instead of copied wholesale from a domain-specific system.

## Roadmap

| Milestone | Outcome |
|---|---|
| **M0 — Governance baseline** | Invariants, decoupling matrix, test conventions, provenance rules, and independent package namespace. |
| **M1 — Universal identity and profile** | Canonical project profile, profile hash, project identity, workspace resolution, and generic `mmu://` addressing. |
| **M2 — Universal persistence** | SQLite migrations, append-only knowledge, entities, work items, executions, evidence, artifacts, bundles, and audit. |
| **M3 — ARET compatibility pack** | Read-only importer, `ARET://` compatibility reader, profile, toolchain declarations, and parity suite. |
| **M4 — Capabilities and gates** | Closed catalog, policy engine, safe runners, validators, executions, and gate engine. |
| **M5 — MCP compiler and adapters** | Generated manifest, stable MCP Core API, runtime adapters, instructions, hooks, and doctor. |
| **M6+ — CLI, dashboard, multi-domain conformance** | Project scanner, configuration workflow, installation, visual editor, and cross-domain fixtures. |

## Provenance and boundaries

VeriChronicle is inspired by the invariant-driven design of ARET-MMU, but it is a **separate repository and implementation**. No ARET-MMU source code is copied into this foundation. Any future migration adapter must explicitly record the originating commit, hashes, source paths, and transformation report.

The repository is public, but a formal licence must be selected by the project owner before third-party reuse or releases. Until then, contributors should treat the contents as non-redistributable unless the owner states otherwise.

## References

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — reference repository"

---

*VeriChronicle is a working title selected for its connection to verifiable truth and durable project history. The public repository slug is intended to be `aciderix/verichronicle`.*
