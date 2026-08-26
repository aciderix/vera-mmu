# Journal d’ingénierie VERA-MMU

> **Statut :** registre chronologique append-only et index de recherche.
>
> **Document lié :** chaque entrée porte des liens vers la [mémoire factuelle](PROJECT_MEMORY.md) ; les décisions de plan sont consolidées dans le [plan vivant](UNIVERSALIZATION_WORKPLAN.md).
>
> **Règle :** aucun changement important, résultat de test, wall, décision, comparaison ou handoff ne reste seulement dans une conversation.

## 1. Convention d’identification et de recherche

Chaque entrée reçoit un identifiant monotone `LOG-NNNN`. Les records liés utilisent les formats `MEM-…` pour la mémoire, `M…` pour les lots, `I…` pour les invariants, `G…` pour les gates futures et `E…` pour les evidence/executions futures. Une recherche documentaire commence par le tableau d’index, puis lit l’entrée exacte ; elle ne constitue jamais une preuve à elle seule.

| Champ | Règle |
|---|---|
| `Type` | `BASELINE`, `INSPECTION`, `DECISION`, `CHANGE`, `RUN`, `EVIDENCE`, `COMPARISON`, `VERDICT`, `WALL`, `RISK`, `HANDOFF` ou `SECURITY`. |
| `Certitude` | `PROVEN`, `OBSERVED`, `INFERRED`, `HYPOTHESIS`, `DECISION`, `RISK`, `BLOCKED` ou `UNKNOWN`. |
| `Sources` | Commit, chemin, plage de lignes, artefact, commande, hash, URL ou record mémoire. |
| `Invariants` | Tous les invariants réellement touchés, jamais une liste décorative. |
| `Baseline` | Référence explicite lorsque l’entrée modifie ou mesure un comportement. |
| `Verdict` | Uniquement `PASS`, `FAIL`, `UNKNOWN`, `NOT_RUN` ou `N/A`, avec motif. |
| `Suivi` | Prochaine action concrète, blocage ou record qui supersède celui-ci. |

## 2. Index de recherche rapide

| ID | Date | Type | Lot | Mots-clés | Certitude | Verdict | Mémoire liée |
|---|---|---|---|---|---|---|---|
| `LOG-0001` | 2026-08-25 | `BASELINE` | Pré-M0 | ARET, clone, commit, main, arbre propre | `OBSERVED` | `N/A` | `MEM-BASE-001` |
| `LOG-0002` | 2026-08-25 | `DECISION` | Pré-M0 | VERA-MMU, identité, dépôt indépendant, fondation | `DECISION` | `PASS` | `MEM-ID-001`, `MEM-BASE-002`, `MEM-DEC-001`, `MEM-DEC-002` |
| `LOG-0003` | 2026-08-25 | `INSPECTION` | M0.1 | spécification, doctrine ARET, continuité, baseline, reprise | `OBSERVED` | `PASS` | `MEM-SRC-001`, `MEM-SRC-002`, `MEM-DEC-003`, `MEM-DEC-004` |
| `LOG-0004` | 2026-08-25 | `INSPECTION` | M0.0 | continuité, liens croisés, Git, reprise, format | `OBSERVED` | `PASS` | `MEM-DEC-003`, reprise active |
| `LOG-0005` | 2026-08-25 | `BASELINE` | M0.1 | ouverture, environnement, périmètre, préconditions | `OBSERVED` | `NOT_RUN` | `MEM-RISK-001`, reprise active |
| `LOG-0006` | 2026-08-25 | `BASELINE` / `WALL` | M0.1 | inventaire, pytest, hooks, MCP, bundle, toolchain, intégrité | `OBSERVED` | `UNKNOWN` | `MEM-BASE-003`, `MEM-BASE-004`, `MEM-WALL-001` |
| `LOG-0007` | 2026-08-25 | `INSPECTION` / `DECISION` | M0.2 | découplage, adressage, store, schéma, MCP, hooks, bundle, VCS | `OBSERVED` | `PASS` pour la cartographie ; `UNKNOWN` pour les parités | `MEM-COMP-001`, `MEM-DEC-005`, `MEM-WALL-001` |
| `LOG-0008` | 2026-08-25 | `HYPOTHESIS` | M1 | profile, identité, workspace, runtime, `vera://`, no-Git, multi-repo | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-005`, reprise active |
| `LOG-0009` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M1 | C01/C02/C11, Core universel, distribution | `OBSERVED` | `PASS` pour les gates M1 ; `UNKNOWN` pour la parité ARET | `MEM-STATE-006`, `MEM-DEC-006`, `MEM-WALL-001` |
| `LOG-0010` | 2026-08-25 | `HYPOTHESIS` | M2.1 | SQLite, migrations, identité de store, audit technique | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-007`, `MEM-WALL-001` |
| `LOG-0011` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.1 | substrate SQLite, migration, identité, transaction, CLI | `OBSERVED` | `PASS` pour M2.1 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-007`, `MEM-DEC-007`, `MEM-WALL-001` |
| `LOG-0012` | 2026-08-25 | `HYPOTHESIS` | M2.2 | registre de types d’entité, entités, audit métier | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-008`, `MEM-WALL-001` |
| `LOG-0013` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.2 | types d’entité, entités, lecture exacte, audit | `OBSERVED` | `PASS` pour M2.2 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-008`, `MEM-DEC-008`, `MEM-WALL-001` |
| `LOG-0014` | 2026-08-25 | `HYPOTHESIS` | M2.3 | registre relationnel, arêtes entre entités, audit | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-009`, `MEM-WALL-001` |
| `LOG-0015` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.3 | types relationnels, arêtes, immuabilité, audit | `OBSERVED` | `PASS` pour M2.3 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-009`, `MEM-DEC-009`, `MEM-WALL-001` |
| `LOG-0016` | 2026-08-25 | `HYPOTHESIS` | M2.4 | registre knowledge, append-only, statuts épistémiques, audit | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-010`, `MEM-WALL-001` |
| `LOG-0017` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.4 | types knowledge, append-only, hash, statuts, audit | `OBSERVED` | `PASS` pour M2.4 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-010`, `MEM-DEC-010`, `MEM-WALL-001` |
| `LOG-0018` | 2026-08-25 | `HYPOTHESIS` | M2.5 | provenance documentaire, sources hashées, audit | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-011`, `MEM-WALL-001` |
| `LOG-0019` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.5 | sources knowledge, confinement, immuabilité, audit | `OBSERVED` | `PASS` pour M2.5 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-011`, `MEM-DEC-011`, `MEM-WALL-001` |
| `LOG-0020` | 2026-08-25 | `HYPOTHESIS` | M2.6 | supersession knowledge, append-only, audit | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-012`, `MEM-WALL-001` |
| `LOG-0021` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.6 | supersession knowledge, sidecar immutable, anti-cycle, audit | `OBSERVED` | `PASS` pour M2.6 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-012`, `MEM-DEC-012`, `MEM-WALL-001` |
| `LOG-0022` | 2026-08-25 | `RECORD` / `HANDOFF` | M2.6 | commit, publication, vérification distante | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-012`, `MEM-DEC-012`, `MEM-WALL-001` |
| `LOG-0023` | 2026-08-25 | `HYPOTHESIS` | M2.7 | asset binaire, SHA-256, lecture exacte, audit | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-013`, `MEM-WALL-001` |
| `LOG-0024` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.7 | asset binaire, hash avant lecture, immuabilité, audit | `OBSERVED` | `PASS` pour M2.7 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-013`, `MEM-DEC-013`, `MEM-WALL-001` |
| `LOG-0025` | 2026-08-25 | `RECORD` / `HANDOFF` | M2.7 | commit, publication, vérification distante | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-013`, `MEM-DEC-013`, `MEM-WALL-001` |
| `LOG-0026` | 2026-08-25 | `HYPOTHESIS` | M2.8 | association exacte knowledge–asset, immuabilité, audit | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-014`, `MEM-WALL-001` |
| `LOG-0027` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.8 | association exacte knowledge–asset, immuabilité, audit | `OBSERVED` | `PASS` pour M2.8 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-014`, `MEM-DEC-014`, `MEM-WALL-001` |
| `LOG-0028` | 2026-08-25 | `RECORD` / `HANDOFF` | M2.8 | commit, publication, vérification distante | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-014`, `MEM-DEC-014`, `MEM-WALL-001` |
| `LOG-0029` | 2026-08-25 | `HYPOTHESIS` | M2.9 | index direct knowledge–asset, borne, audit existant | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-015`, `MEM-WALL-001` |
| `LOG-0030` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.9 | index direct knowledge–asset, ordre/borne, sans contenu | `OBSERVED` | `PASS` pour M2.9 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-015`, `MEM-DEC-015`, `MEM-WALL-001` |
| `LOG-0031` | 2026-08-25 | `RECORD` / `HANDOFF` | M2.9 | commit, publication, vérification distante | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-015`, `MEM-DEC-015`, `MEM-WALL-001` |
| `LOG-0032` | 2026-08-25 | `HYPOTHESIS` | M2.10 | provenance déclarative asset, immuabilité, audit | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-016`, `MEM-WALL-001` |
| `LOG-0033` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.10 | provenance déclarative asset, immuabilité, audit | `OBSERVED` | `PASS` pour M2.10 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-016`, `MEM-DEC-016`, `MEM-WALL-001` |
| `LOG-0034` | 2026-08-25 | `RECORD` / `HANDOFF` | M2.10 | commit, publication, vérification distante | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-016`, `MEM-DEC-016`, `MEM-WALL-001` |
| `LOG-0035` | 2026-08-25 | `HYPOTHESIS` | M2.11 | index exact assets par hash, borne, sans bytes | `HYPOTHESIS` | `REJECTED` comme redondant | `MEM-DEC-017`, `MEM-WALL-001` |
| `LOG-0036` | 2026-08-25 | `COMPARISON` / `RECORD` | M2.11 | rejet d’index asset par hash redondant | `OBSERVED` | `REJECTED` | `MEM-DEC-018`, `MEM-WALL-001` |
| `LOG-0037` | 2026-08-25 | `HYPOTHESIS` | M2.11 | index exact sources knowledge par hash, borne, sans contenu | `HYPOTHESIS` | `NOT_RUN` | `MEM-DEC-018`, `MEM-WALL-001` |
| `LOG-0038` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.11 | index exact sources knowledge par hash, borne, sans contenu | `OBSERVED` | `PASS` pour M2.11 ; `UNKNOWN` pour M2 complet/parité ARET | `MEM-STATE-017`, `MEM-DEC-017`, `MEM-DEC-018`, `MEM-WALL-001` |
| `LOG-0039` | 2026-08-25 | `RECORD` / `HANDOFF` | M2.11 | commit, publication, vérification distante | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-017`, `MEM-DEC-017`, `MEM-DEC-018`, `MEM-WALL-001` |
| `LOG-0040` | 2026-08-25 | `DECISION` / `ROADMAP` | Cadrage M2 | gate terminale, M2/M3, anti-redondance, macro-lots | `DECISION` | `PASS` pour le cadrage | `MEM-DEC-019` à `MEM-DEC-021`, `MEM-STATE-018`, `MEM-WALL-001` |
| `LOG-0041` | 2026-08-25 | `HYPOTHESIS` | M2.12 | symbol, entity FK, immuabilité, audit, no-scan | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-DEC-022`, `MEM-WALL-001` |
| `LOG-0042` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.12 | symbol, migration 012, URI, audit, wheel | `OBSERVED` | `PASS` pour M2.12 ; M2 restant/parité ARET `UNKNOWN` | `MEM-STATE-019`, `MEM-DEC-022`, `MEM-STATE-020`, `MEM-WALL-001` |
| `LOG-0043` | 2026-08-25 | `RECORD` / `HANDOFF` | M2.12 | commit, publication, vérification distante | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-019`, `MEM-STATE-020`, `MEM-WALL-001` |
| `LOG-0044` | 2026-08-25 | `HYPOTHESIS` | M2.13 | work item, parent, statut initial, immuabilité, no-graph | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-020`, `MEM-WALL-001` |
| `LOG-0045` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.13 | work item, migration 013, parent, audit, wheel | `OBSERVED` | `PASS` pour M2.13 ; M2 restant/parité ARET `UNKNOWN` | `MEM-STATE-021`, `MEM-DEC-023`, `MEM-STATE-022`, `MEM-WALL-001` |
| `LOG-0046` | 2026-08-25 | `RECORD` / `HANDOFF` | M2.13 | commit, publication, vérification distante | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-021`, `MEM-STATE-022`, `MEM-WALL-001` |
| `LOG-0047` | 2026-08-25 | `HYPOTHESIS` | M2.14 | capability, execution, déclaration, immuabilité, no-runner | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-022`, `MEM-WALL-001` |
| `LOG-0048` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M2.14 | capability, execution schema, URI, audit, wheel | `OBSERVED` | `PASS` pour M2.14 ; M2.EXIT/parité ARET `UNKNOWN` | `MEM-STATE-023`, `MEM-DEC-024`, `MEM-WALL-001` |
| `LOG-0049` | 2026-08-25 | `RUN` / `COMPARISON` / `VERDICT` | M2.EXIT | migrations 001–014, schema universel, upgrade, wheel, frontières | `OBSERVED` | `PASS` pour M2 ; parité ARET `UNKNOWN` | `MEM-STATE-024`, `MEM-DEC-025`, `MEM-WALL-001` |
| `LOG-0050` | 2026-08-25 | `HYPOTHESIS` | M3.1 | contracts capability, runner fermé, no-shell, no-network | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-WALL-001` |
| `LOG-0051` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.1 | capability contracts, migration 015, publication | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-025`, `MEM-WALL-001` |
| `LOG-0052` | 2026-08-25 | `PREPARATION` | M3.2 | runner borné, `NOOP`, `DENY_NETWORK` | `DECISION` | `N/A` | `MEM-STATE-025` |
| `LOG-0053` | 2026-08-25 | `HYPOTHESIS` | M3.2 | execution, runner `NOOP`, no-processus | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-025` |
| `LOG-0054` | 2026-08-25 | `RUN` / `VERDICT` | M3.2 | execution immutable, `NOOP`, no-network | `OBSERVED` | `PASS` technique | `MEM-STATE-025` |
| `LOG-0055` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.2 | publication execution runner | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-025` |
| `LOG-0056` | 2026-08-25 | `HYPOTHESIS` | M3.3 | evidence hashée, verdict, admission pending | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-025` |
| `LOG-0057` | 2026-08-25 | `RUN` / `VERDICT` | M3.3 | evidence store, hash, immuabilité | `OBSERVED` | `PASS` technique | `MEM-STATE-025` |
| `LOG-0058` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.3 | publication evidence store | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-025` |
| `LOG-0059` | 2026-08-25 | `HYPOTHESIS` | M3.4 | admission immutable, evidence `PASS` | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-025` |
| `LOG-0060` | 2026-08-25 | `RUN` / `VERDICT` | M3.4 | admission, `ADMITTED`, `REJECTED` | `OBSERVED` | `PASS` technique | `MEM-STATE-025` |
| `LOG-0061` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.4 | publication admission | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-025` |
| `LOG-0062` | 2026-08-25 | `HYPOTHESIS` | M3.6 | work dependencies, gates, anti-cycle | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-025` |
| `LOG-0063` | 2026-08-25 | `HYPOTHESIS` | M3.5 | HMAC, evidence-knowledge, proof dérivée | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-025` |
| `LOG-0064` | 2026-08-25 | `DECISION` | M3.5 | `PROVEN` dérivé, secret HMAC en mémoire | `DECISION` | `PASS` pour le cadrage | `MEM-DEC-026` |
| `LOG-0065` | 2026-08-25 | `BASELINE` | M3.5 | preuve dérivée, invariant de non-réécriture | `OBSERVED` | `READY_FOR_TESTS_FIRST` | `MEM-STATE-025` |
| `LOG-0066` | 2026-08-25 | `RUN` / `VERDICT` | M3.5 | proof, admission, HMAC digest | `OBSERVED` | `PASS` technique | `MEM-STATE-025` |
| `LOG-0067` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.5 | publication proof dérivée | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-025` |
| `LOG-0068` | 2026-08-25 | `RUN` / `VERDICT` | M3.6 | work graph, gate mono-evidence, admission | `OBSERVED` | `PASS` technique | `MEM-STATE-025` |
| `LOG-0069` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.6 | publication work graph/gate | `OBSERVED` | `PASS` pour la publication | `MEM-STATE-025` |
| `LOG-0070` | 2026-08-25 | `RUN` / `COMPARISON` / `VERDICT` / `DECISION` | M3.S1.EXIT | migrations 001–019, tests, wheel, frontières, portée | `OBSERVED` / `DECISION` | `PASS` pour M3.S1 ; M3/parité ARET non clos | `MEM-STATE-025`, `MEM-DEC-026`, `MEM-STATE-026`, `MEM-WALL-001` |
| `LOG-0071` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.S1.EXIT | publication gate, commit, vérification distante | `OBSERVED` | `PASS` pour la publication; M3 reste ouvert | `MEM-STATE-026`, `MEM-WALL-001` |
| `LOG-0072` | 2026-08-25 | `HYPOTHESIS` | M3.7 | parameter schema fermé, validation locale, no-runner | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-027`, `MEM-DEC-027`, `MEM-WALL-001` |
| `LOG-0073` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M3.7 | paramètres, atomicité, wheel, frontières | `OBSERVED` | `PASS` technique; publication à finaliser | `MEM-STATE-027`, `MEM-STATE-028`, `MEM-DEC-027`, `MEM-WALL-001` |
| `LOG-0074` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.7 | publication, commit, vérification distante | `OBSERVED` | `PASS` pour la publication; M3 reste ouvert | `MEM-STATE-028`, `MEM-WALL-001` |
| `LOG-0075` | 2026-08-25 | `HYPOTHESIS` | M3.8 | policy fermée, `ALLOW`, `DENY`, `CONFIRM`, no-runner | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-029`, `MEM-DEC-028`, `MEM-WALL-001` |
| `LOG-0076` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M3.8 | policy, atomicité, wheel, frontières | `OBSERVED` | `PASS` technique; publication à finaliser | `MEM-STATE-029`, `MEM-STATE-030`, `MEM-DEC-028`, `MEM-WALL-001` |
| `LOG-0077` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.8 | publication, commit, vérification distante | `OBSERVED` | `PASS` pour la publication; M3 reste ouvert | `MEM-STATE-030`, `MEM-WALL-001` |
| `LOG-0078` | 2026-08-25 | `HYPOTHESIS` | M3.9 | policy HMAC projet, secret en mémoire, no-runner | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-031`, `MEM-DEC-029`, `MEM-WALL-001` |
| `LOG-0079` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M3.9 | policy HMAC, non-persistance secret, wheel, frontières | `OBSERVED` | `PASS` technique; publication à finaliser | `MEM-STATE-031`, `MEM-STATE-032`, `MEM-DEC-029`, `MEM-WALL-001` |
| `LOG-0080` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.9 | publication, commit, vérification distante | `OBSERVED` | `PASS` pour la publication; M3 reste ouvert | `MEM-STATE-032`, `MEM-WALL-001` |
| `LOG-0081` | 2026-08-25 | `HYPOTHESIS` | M3.10 | validator local `EVIDENCE_HASH`, no-oracle | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-033`, `MEM-DEC-030`, `MEM-WALL-001` |
| `LOG-0082` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M3.10 | intégrité locale, atomicité, wheel, frontières | `OBSERVED` | `PASS` technique; publication à finaliser | `MEM-STATE-033`, `MEM-STATE-034`, `MEM-DEC-030`, `MEM-WALL-001` |
| `LOG-0083` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.10 | publication, commit, vérification distante | `OBSERVED` | `PASS` pour la publication; M3 reste ouvert | `MEM-STATE-034`, `MEM-WALL-001` |
| `LOG-0084` | 2026-08-25 | `HYPOTHESIS` | M3.11 | gate multi-evidence conjonctive, no-runner | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-035`, `MEM-DEC-031`, `MEM-WALL-001` |
| `LOG-0085` | 2026-08-25 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M3.11 | exigences, atomicité, wheel, frontières | `OBSERVED` | `PASS` technique; publication à finaliser | `MEM-STATE-035`, `MEM-STATE-036`, `MEM-DEC-031`, `MEM-WALL-001` |
| `LOG-0086` | 2026-08-25 | `RECORD` / `HANDOFF` | M3.11 | publication, commit, vérification distante | `OBSERVED` | `PASS` pour la publication; M3 reste ouvert | `MEM-STATE-036`, `MEM-WALL-001` |
| `LOG-0087` | 2026-08-26 | `HYPOTHESIS` | M3.12 | lifecycle dérivé, événements fermés, no-runner | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-037`, `MEM-DEC-032`, `MEM-WALL-001` |
| `LOG-0088` | 2026-08-26 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M3.12 | transitions, atomicité, wheel, frontières | `OBSERVED` | `PASS` technique; publication à finaliser | `MEM-STATE-037`, `MEM-STATE-038`, `MEM-DEC-032`, `MEM-WALL-001` |
| `LOG-0089` | 2026-08-26 | `RECORD` / `HANDOFF` | M3.12 | publication, commit, vérification distante | `OBSERVED` | `PASS` pour la publication; M3 reste ouvert | `MEM-STATE-038`, `MEM-WALL-001` |
| `LOG-0090` | 2026-08-26 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M3.S2.EXIT | chaîne M3.7–M3.12, wheel, frontières | `OBSERVED` | `PASS` de tranche; M3 global ouvert | `MEM-STATE-039`, `MEM-DEC-033`, `MEM-WALL-001` |
| `LOG-0091` | 2026-08-26 | `RECORD` / `HANDOFF` | M3.S2.EXIT | publication, commit, vérification distante | `OBSERVED` | `PASS` pour la publication; M3 reste ouvert | `MEM-STATE-040`, `MEM-WALL-001` |
| `LOG-0092` | 2026-08-26 | `HYPOTHESIS` | M3.13 | policy d’admission validée, no-validator implicite | `HYPOTHESIS` | `PENDING` à l’ouverture | `MEM-STATE-041`, `MEM-DEC-034`, `MEM-WALL-001` |
| `LOG-0093` | 2026-08-26 | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` | M3.13 | policy, atomicité, wheel, frontières | `OBSERVED` | `PASS` technique; publication à finaliser | `MEM-STATE-041`, `MEM-STATE-042`, `MEM-DEC-034`, `MEM-WALL-001` |
| `LOG-0094` | 2026-08-26 | `RECORD` / `HANDOFF` | M3.13 | publication, commit, vérification distante | `OBSERVED` | `PASS` pour la publication; M3 reste ouvert | `MEM-STATE-042`, `MEM-WALL-001` |

## 3. Entrées append-only

### LOG-0001 — Baseline locale ARET-MMU

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `BASELINE` |
| Lot | Pré-M0 — référence ARET |
| Certitude | `OBSERVED` |
| Sources | Clone local `/home/ubuntu/ARET-MMU`; `git rev-parse HEAD`; `git branch --show-current`; `git status --short`. |
| Résultat | Commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, branche `main`, arbre propre au relevé. |
| Invariants concernés | I001, I004, I010, I014, I015 — comme références de migration à préserver, sans preuve de parité à ce stade. |
| Baseline | Cette entrée est la référence Git initiale ; elle ne constitue pas encore un baseline complet de comportement. |
| Verdict | `N/A` — inventaire Git seulement. |
| Mémoire liée | `MEM-BASE-001`. |
| Suivi | `LOG-0005` doit compléter tests, dépendances, schéma, hooks, MCP et bundle. |

### LOG-0002 — Fondation indépendante VERA-MMU

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `DECISION` |
| Lot | Pré-M0 — identité et fondation |
| Certitude | `DECISION` et `OBSERVED` |
| Sources | Dépôt `/home/ubuntu/vera-mmu`, commit `ef707339c245ee1d36b8a78312d1a441c86296dc`, [identité](../IDENTITY.md), [README](../../README.md), [invariants](../INVARIANTS.md), [matrice](../DECOUPLING_MATRIX.md). |
| Décision | Construire VERA-MMU dans un dépôt indépendant ; employer la forme composée VERA-MMU, le package `vera_mmu`, la CLI `vmmu`, le répertoire `.vera-mmu/` et le schéma `vera://`. |
| Justification | Préserver l’intégrité du dépôt ARET-MMU, rendre le découplage mesurable et éviter qu’une spécialisation ARET devienne une dépendance du Core. |
| Validation existante | La fondation a été construite en wheel et les tests d’identité ont passé lors de son établissement ; tout nouveau lot doit les relancer, sans les considérer comme une preuve de fonctionnalités non implémentées. |
| Invariants concernés | I009, I011, I012, I014, I015. |
| Verdict | `PASS` pour la création de la fondation ; `UNKNOWN` pour toute capacité universelle non encore implémentée. |
| Mémoire liée | `MEM-ID-001`, `MEM-BASE-002`, `MEM-DEC-001`, `MEM-DEC-002`, `MEM-STATE-001` à `MEM-STATE-005`. |
| Suivi | Démarrer le baseline ARET avant tout mouvement de code depuis ARET-MMU. |

### LOG-0003 — Institution du dispositif de continuité

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `INSPECTION` puis `DECISION` |
| Lot | M0.1 — préparation du freeze |
| Certitude | `OBSERVED` pour les sources ; `DECISION` pour le protocole documentaire. |
| Sources lues | Spécification `UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md` fournie par le propriétaire ; doctrine ARET `pasted_content.txt` fournie par le propriétaire ; [README](../../README.md), [invariants](../INVARIANTS.md) et [matrice](../DECOUPLING_MATRIX.md) de VERA-MMU. |
| Faits pertinents | La spécification exige un Core sans dépendance ARET, un pack ARET de compatibilité, une migration progressive/réversible, des capabilities fermées, des gates basées sur executions/evidence, des tests de sécurité et une conformance multi-domaines. La doctrine ARET exige baseline, changement minimal, comparaison au baseline, fail loud, séparation des niveaux de certitude, Git protecteur et enregistrement de l’état. |
| Décision | Créer trois documents liés : plan vivant, mémoire factuelle append-only et journal indexé. Ils constituent le dispositif de transition jusqu’à ce que VERA-MMU fournisse son propre store/evidence/audit/resume universel. |
| Invariants concernés | I001–I015 comme lois de conception ; principalement I001, I004, I009, I014 et I015 pour le suivi. |
| Baseline | `LOG-0001` et `LOG-0002`. |
| Verdict | `PASS` pour l’institution du suivi ; aucune preuve de parité ARET n’est produite par cette entrée. |
| Mémoire liée | `MEM-SRC-001`, `MEM-SRC-002`, `MEM-DEC-003`, `MEM-DEC-004`, `MEM-RISK-001` à `MEM-RISK-004`. |
| Suivi | Ouvrir `LOG-0005` avant tout test ou capture du freeze ARET. |

### LOG-0004 — Validation documentaire de continuité

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `INSPECTION` |
| Lot | M0.0 — gouvernance de continuité |
| Certitude | `OBSERVED` |
| Sources | Les trois documents de `docs/continuity/`, README, invariants et matrice de découplage. |
| Contrôles | Existence des trois fichiers, présence de renvois mutuels plan ↔ mémoire ↔ journal, référencement depuis README, `git diff --check`. |
| Résultat | Les fichiers existent, les renvois essentiels sont présents et le contrôle de format Git ne signale aucune erreur. |
| Limite | Cette validation contrôle la structure documentaire ; elle ne produit pas de preuve de parité ARET, de migration, de test Core ni d’exécution de Capability. |
| Invariants | I001, I004, I009, I014 et I015 comme discipline documentaire de transition. |
| Baseline | `LOG-0001`, `LOG-0002`, `LOG-0003`. |
| Verdict | `PASS` pour la cohérence documentaire ; `UNKNOWN` pour les capacités non implémentées. |
| Mémoire liée | `MEM-DEC-003`, section Reprise active. |
| Suivi | Ouvrir `LOG-0005` pour le freeze ARET. |

### LOG-0005 — Ouverture du freeze ARET

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `BASELINE` |
| Lot | `M0.1 — Freeze ARET` |
| Hypothèse | Le baseline peut être reproduit sur l’environnement décrit ; toute précondition manquante ou divergence d’environnement sera journalisée comme une wall, sans assimilation à un `PASS`. |
| Périmètre | Commit, état Git, versions Python/dépendances, schéma et checksums, tests, surface MCP, hooks, bundle et outils système. Aucune modification d’ARET-MMU n’est autorisée dans ce lot. |
| Préconditions observées | ARET-MMU est sur `main` au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, avec arbre Git propre. Python `3.12.3`, Git `2.43.0`, pytest `9.1.1` et Bash `5.2.21` sont disponibles ; le client `sqlite3` est absent. |
| Répertoire d’évidence | À créer hors des dépôts sous `/home/ubuntu/ARET_MMU_M0_1_BASELINE/`. |
| Artefacts attendus | Inventaire de fichiers/dépendances, hashes de schéma/migrations, sorties de tests, surface MCP, comportement des hooks, bundle ou motif d’impossibilité. |
| Comparaison | Première mesure de référence ; les runs futurs seront comparés à ses hashes, comptes, statuts et divergences qualifiées. |
| Invariants | I001, I004–I011, I014 et I015, selon les validations réalisables. |
| Verdict | `NOT_RUN` — le baseline est ouvert ; aucune exécution de test, de hook ou de bundle n’est encore qualifiée. |
| Mémoire liée | `MEM-BASE-001`, `MEM-RISK-001`, `MEM-RISK-004`. |
| Suivi | Le résultat de freeze et la wall d’environnement sont consignés dans `LOG-0006`. |

### LOG-0006 — Freeze M0.1 : baseline capturé avec wall de toolchain

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `BASELINE` / `WALL` / `VERDICT` |
| Lot | `M0.1 — Freeze ARET` |
| Certitude | `OBSERVED` |
| Baseline source | ARET-MMU `main` à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, arbre propre avant et après les captures. |
| Inventaire | 130 fichiers Git, 180 fichiers package, 25 fichiers de tests, 90 tests collectés, 6 migrations SQL, 44 outils MCP `aret_*` statiques et 11 modules de hooks. |
| Environnement | Python 3.12.3, Git 2.43.0, pytest 9.1.1 et Bash 5.2.21 ; client `sqlite3` absent. L’inventaire complet est dans le répertoire de baseline. |
| Exécutions | Collecte pytest : `PASS` (90). Suite complète : 82 passés, 1 échec, 7 ignorés. Sous-ensemble hooks/reprise/bundle : 10 passés. |
| Wall | `tests/test_execution_confinement.py::test_oracle_repository_path_and_resolved_script_stay_under_configured_repository` échoue parce que `gcc` est absent : l’oracle fermé retourne `SKIPPED` avant l’exécution de la fixture et le marqueur attendu n’est pas produit. Cargo, Wine, MinGW, Clang, LLD, LLVM DLLTool, le binaire réel ARET et le script réel de difftest sont aussi absents. |
| Bundle | Bundle de mécanique exporté, importé et réimporté idempotent ; hash `1001e6a907c5103bc4e327abc75918a36e4ed851318cc41a38b6baac5bd2642e`. |
| Evidence | `/home/ubuntu/ARET_MMU_M0_1_BASELINE/BASELINE_REPORT.md`, manifeste SHA-256 `05e9c126425a27d6440cb5e92c367bcae6676ff04b430fe4b3618c7afff7984d`, archive `ARET_MMU_M0_1_BASELINE_7f7b4df.tar.gz`. |
| Invariants | I001, I004–I011, I014 et I015 ; aucune preuve de parité VERA n’est produite. |
| Comparaison | Première mesure : les exécutions futures doivent comparer les comptes, hashes, résultats et la disponibilité de toolchain à cette capture. |
| Verdict | `UNKNOWN` pour un baseline d’exécution exhaustif ; `PASS` pour la capture de référence, l’intégrité des artefacts, les hooks/reprises testés et la mécanique de bundle. |
| Mémoire liée | `MEM-BASE-003`, `MEM-BASE-004`, `MEM-WALL-001`. |
| Suivi | Le registre et la décision de séquencement M1 sont consignés dans `LOG-0007`; maintenir `MEM-WALL-001` comme précondition des claims d’oracle/parité. |

### LOG-0007 — M0.2 : registre de compatibilité ARET

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `INSPECTION` / `DECISION` / `VERDICT` |
| Lot | `M0.2 — Registre de compatibilité ARET` |
| Certitude | `OBSERVED` pour les sources et le registre ; `DECISION` pour l’ordre d’implémentation. |
| Baseline | `LOG-0006`, commit ARET `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, archive de baseline M0.1. |
| Périmètre | Adressage, runtime/store, entités, symboles, roadmap, pipelines, oracles, toolchain, instructions, API MCP, workspace, playbook, VCS, bundles, hooks de reprise, knowledge/evidence/audit. |
| Résultat | La matrice détaille 16 couplages. C01–C06 et C09–C16 sont `SPLIT`; C07 et C08 restent `BLOCKED` par `MEM-WALL-001`. Chaque ligne référence une source, une abstraction cible, une stratégie de migration et des assertions de parité. |
| Contrôles | Sources ARET lues sans modification ; état Git ARET conservé propre ; registre contrôlé par `git diff --check`. |
| Décision | Le premier code M1 portera seulement C01/C02/C11 : profile, identité, workspace, runtime et `vera://`; il ne doit importer aucun module, nom, chemin, binaire ou toolchain ARET. |
| Invariants | I001, I004–I015 ; principalement I008, I011, I014 et I015. |
| Verdict | `PASS` pour le registre de compatibilité ; `UNKNOWN` pour toute parité de comportement, non encore implémentée ni exécutée. |
| Mémoire liée | `MEM-COMP-001`, `MEM-DEC-005`, `MEM-WALL-001`. |
| Suivi | L’hypothèse, le périmètre et les validations du patch M1 sont consignés dans `LOG-0008`. |

### LOG-0008 — Hypothèse M1 : Core d’identité sans domaine

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M1 — Core d’identité` |
| Hypothèse | Le Core peut valider un Project Profile, dériver une identité stable, résoudre un workspace mono/multi/no-Git, borner son runtime et traiter `vera://` sans vocabulaire, chemin ou import ARET. |
| Périmètre | C01, C02 et C11 seulement : `ProjectProfile`, `ProjectIdentity`, `WorkspaceResolver`, `RuntimeLocator`, `vera://` et la CLI de validation associée. |
| Exclusions | Aucune migration de store, aucune evidence, aucun alias `ARET://`, aucun pack ARET, aucune capability, aucun hook de runtime ou adapter MCP. |
| Baseline | Fondation VERA `ef707339c245ee1d36b8a78312d1a441c86296dc`; matrice C01/C02/C11; `LOG-0007`. |
| Invariants | I008, I009, I011, I012, I014 et I015. |
| Tests prévus | Stabilité d’identité, parsing/round-trip de `vera://`, rejets de traversal et ressources inconnues, runtime borné, no-Git, multi-repo et scan anti-dépendance ARET. |
| Verdict | `NOT_RUN` — aucun patch M1 n’est encore appliqué. |
| Mémoire liée | `MEM-DEC-005`, `MEM-COMP-001`, `MEM-WALL-001`. |
| Suivi | Inspecter l’API `identity.py`, le profile minimal et les tests existants avant de modifier le Core. |

### LOG-0009 — Verdict M1 : identité universelle confinée

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M1 — Core d’identité` |
| Certitude | `OBSERVED` : les commandes et tests ont produit les résultats enregistrés ; aucune evidence canonique VERA n’existe encore. |
| Sources | `src/vera_mmu/{addressing,identity,workspace,runtime}.py`, surface publique, CLI, tests ciblés et profile minimal. |
| Baseline | Fondation VERA `ef707339c245ee1d36b8a78312d1a441c86296dc`; hypothèse `LOG-0008`; couplages C01/C02/C11 de la matrice M0.2. |
| Changement | URI `vera://` strictes et canonisées ; Project Profile normalisé/hashé ; ProjectIdentity avec `workspace_hash` ; roots mono/multi/no-Git contrôlées ; détection locale optionnelle d’un marqueur VCS sans exécuter Git ; runtime, SQLite et artefacts confinés. |
| Invariants | I008, I009, I011, I012, I014, I015. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **21 passés, 14 sous-tests, 0 échec**. `vmmu identity` et `vmmu inspect` sur `profiles/minimal/project.yaml` : sortie JSON `ok: true`. |
| Contrôles de sûreté | Tests de traversal, resource inconnue, forme URI non canonique, no-Git, multi-root, symlink sortant, runtime sortant et préfixe de lecteur Windows. `git diff --check` réussit. Le scan imposé de `src/vera_mmu/*.py` ne contient aucun terme ARET interdit. |
| Distribution | Wheel construit puis installé dans une cible temporaire ; `vmmu inspect` réussit depuis le wheel. SHA-256 wheel : `92078ad9018f0a26d5b6999fcfe25f32dd6ca1699b6b49c501b7bc12c8f13e1e`. SHA-256 sortie inspect : `b7179255542a2ab7d24a4ff63c9a422a3a28f1f26e73560e69a9a08577fe42f2`. |
| Comparaison | La fondation ne validait que le hash de profile et quatre assertions locales. M1 ajoute les contrats C01/C02/C11 et leur couverture de sûreté, sans migration, store ni import de code ARET. |
| Limites | Aucune parité d’exécution ARET, aucun lecteur `ARET://`, store, evidence, policy, capability, bundle, adapter MCP ou pack n’est fourni. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre et les gates techniques M1. `UNKNOWN` pour toute parité ou capacité hors C01/C02/C11. |
| Mémoire liée | `MEM-STATE-006`, `MEM-DEC-006`, `MEM-RISK-002`, `MEM-WALL-001`. |
| Suivi | Relire le diff, mettre à jour plan et matrice, puis créer le commit atomique M1. |

### LOG-0010 — Hypothèse M2.1 : substrate de persistance universel

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.1 — Substrate SQLite` |
| Hypothèse | Le Core peut créer un store SQLite canonique, migrationné de façon déterministe et lié à l’identité M1, sans vocabulaire métier, evidence, pack ou exécution ARET. |
| Périmètre | Gestionnaire de migrations SQL checksumées, connexion SQLite bornée (`foreign_keys`, WAL, timeout), métadonnées de store, binding de ProjectIdentity et audit technique minimal. |
| Exclusions | Knowledge append-only, entités/symboles/work items, relations, evidence/proofs, bundles, policies, capabilities, commandes, sync VCS, MCP et tout lecteur/pack ARET. |
| Baseline | M1 publié au commit `c48efc4ec824a9ec5b1a3742f7022636e9ef082b`; `LOG-0009`; C02/C03/C04/C05/C14/C16 de la matrice. |
| Invariants | I001, I010, I011, I014, I015. |
| Tests prévus | Initialisation vide, migration idempotente, checksum modifié, ordre/duplication de migrations, identité projet mismatched, transaction atomique, paramètres SQLite et confinement runtime. |
| Verdict | `NOT_RUN` — aucun patch M2.1 n’est appliqué. |
| Mémoire liée | `MEM-STATE-003`, `MEM-DEC-007` à créer, `MEM-WALL-001`. |
| Suivi | Inspecter le packaging, les APIs M1 et les patterns transactionnels avant de créer les premiers modules Core. |

### LOG-0011 — Verdict M2.1 : substrate SQLite universel

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.1 — Substrate SQLite` |
| Certitude | `OBSERVED` : résultats produits par tests, CLI et wheel ; aucune evidence canonique VERA métier n’existe encore. |
| Baseline | M1 publié `c48efc4ec824a9ec5b1a3742f7022636e9ef082b`; `LOG-0010`; schéma/migrations ARET lus comme référence d’invariants, sans import de vocabulaire ni de code. |
| Changement | Migration `001_core_store.sql`, `MigrationRunner`, `MemoryStore`, métadonnées JSON de format et ProjectIdentity, audit `STORE_INITIALIZED`/`STORE_MIGRATED`, transaction explicite et CLI `vmmu init`. |
| Invariants | I001, I010, I011, I014, I015. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **31 passés, 14 sous-tests, 0 échec**. Les cas couvrent initialisation, idempotence, checksum altéré, inventaire incomplet/discontinu, identité différente, rollback et échec SQL atomique. |
| Contrôles de sûreté | Connexion SQLite avec foreign keys, WAL et timeout ; runtime fourni seulement par le profile validé ; `git diff --check` et scan imposé anti-ARET du Core réussis. |
| Distribution | Wheel construit, installé dans une cible temporaire et exécuté par `vmmu init` sur un projet temporaire. Migration SQL présente dans le wheel. SHA-256 wheel : `10d5ae624e21acae97a4c7e4c3975367beb35a5ec742b9e3abd6f3ac84d482ef`; sortie init : `43820b4c67cc8727b8a7cee94437bce8f02b4d085687d0edcd369a1e81c6e8d7`. |
| Comparaison | Avant M2.1, VERA n’avait ni migration, ni store, ni identity binding de base. M2.1 ajoute uniquement le substrate sans knowledge, entité, relation, evidence, bundle, policy, capability ou transport. |
| Limites | Aucun contrat append-only métier, admission `PROVEN`, FTS, artifact read, relation, work item, evidence/proof, bundle ou compatibilité ARET n’est livré. Les critères de parité des lignes C02/C14/C16 demeurent partiels. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.1. `UNKNOWN` pour M2 dans son ensemble et toute parité ARET. |
| Mémoire liée | `MEM-STATE-007`, `MEM-DEC-007`, `MEM-WALL-001`. |
| Suivi | Mettre à jour plan, mémoire et matrice ; relire le diff puis committer atomiquement. |

### LOG-0012 — Hypothèse M2.2 : registre d’entités génériques

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.2 — Entity Registry` |
| Hypothèse | Le Core peut enregistrer des types d’entités et créer/lire des entités génériques, liées à un ProjectIdentity et auditées, sans réintroduire `component`, `function_symbol`, symboles ou vocabulaire ARET. |
| Périmètre | Migration `002`, `EntityService` composé sur `MemoryStore`, registre de types, entités, lecture exacte, JSON canonique et audit métier de création. |
| Exclusions | Symboles, relations, knowledge, recherche/FIND, evidence/proofs, work items, suppression/modification, bundles, policies, capability, MCP, pack/lecteur/import ARET. |
| Baseline | M2.1 publié au commit `3fc41eff3fb525bab82338287ddde33b3dce9358`; `LOG-0011`; C03/C04/C16 de la matrice et sections 8–9 de la spécification. |
| Invariants | I001, I002, I003, I011, I014, I015. |
| Tests prévus | Migration 1→2, type inconnu/dupliqué, ID invalide, entity dupliquée, JSON non canonique, lecture exacte, audit de création, rollback atomique et absence de vocabulaire ARET. |
| Verdict | `NOT_RUN` — aucun patch M2.2 n’est appliqué. |
| Mémoire liée | `MEM-DEC-008` à créer, `MEM-STATE-007`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, puis ajouter tests et code dans des modules séparés avant toute extension relationnelle ou de connaissance. |

### LOG-0013 — Verdict M2.2 : registre d’entités génériques

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.2 — Entity Registry` |
| Certitude | `OBSERVED` : les tests, le wheel et le contrôle de création/lecture ont produit les résultats consignés ; aucune evidence métier VERA n’est encore disponible. |
| Baseline | M2.1 publié `3fc41eff3fb525bab82338287ddde33b3dce9358`; `LOG-0012`; C03/C04/C16 de la matrice et tables génériques de la spécification, sans import de code ARET. |
| Changement | Migration `002_entity_registry.sql`, `EntityService`, `EntityType`/`Entity`, type préalablement enregistré, création atomique, lecture exacte, JSON canonique et audit `ENTITY_TYPE_REGISTERED`/`ENTITY_CREATED`. |
| Invariants | I001, I002, I003, I011, I014, I015. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **40 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration M2.1→M2.2, type inconnu/dupliqué, identifiant invalide, entity dupliquée, lecture exacte, JSON mapping et rollback entity+audit. |
| Contrôles de sûreté | `git diff --check` et scan anti-ARET du Core réussis. Le type doit être enregistré, l’ID est validé par l’adresse `vera://`, et mutation/audit se font dans une transaction unique. |
| Distribution | Wheel construit puis installé dans une cible temporaire ; migration `002` présente et création/lecture d’une entité réussie depuis le wheel. SHA-256 wheel : `668982804257229fb76542a21c21baa311b3a183e28db46c3a8a46ba099fb92e`; sortie de contrôle : `48c145310fad36ce52f58bc0a6a5253328e70dc130cc697b83a21733b3fbd6ae`. |
| Comparaison | M2.1 ne pouvait que créer un substrate neutre. M2.2 ajoute le premier objet métier universel, sans table ARET de component/function, symboles, relations, FIND, knowledge ou evidence. |
| Limites | Pas de relation, symbole, knowledge append-only, recherche, supersession, proof/evidence, artifact, work item, bundle, policy, capability, MCP ou compatibilité ARET. L’invariant I003 n’est pas encore exercé par une table knowledge. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.2. `UNKNOWN` pour M2 dans son ensemble et toute parité ARET. |
| Mémoire liée | `MEM-STATE-008`, `MEM-DEC-008`, `MEM-WALL-001`. |
| Suivi | Mettre à jour le plan, la mémoire, la matrice et le manifeste ; relire le diff, committer puis publier atomiquement. |

### LOG-0014 — Hypothèse M2.3 : registre relationnel entre entités

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.3 — Relation Registry` |
| Hypothèse | Le Core peut enregistrer des types de relation génériques puis créer/lire exactement des arêtes immuables entre entités existantes, avec contraintes déclaratives de type et audit atomique, sans vocabulaires ARET codés en dur. |
| Périmètre | Migration `003`, `RelationService`, `relation_type`, `relation`, contraintes `from_types`/`to_types`, lecture exacte, JSON canonique et audit de création. |
| Exclusions | Traversal/FIND, lifecycle de supersession, relation vers knowledge/evidence/symbol, bootstrap de vocabulaire métier, mise à jour/suppression, knowledge, proofs, bundles, policies, MCP, pack/lecteur/import ARET. |
| Baseline | M2.2 publié au commit `8f367ca5fdf906f48a58e739360af97d1649c40a`; `LOG-0013`; C16 de la matrice, section 9 de la spécification et test ARET de lifecycle lus comme références de périmètre. |
| Invariants | I001, I002, I003, I011, I014, I015. |
| Tests prévus | Migration 2→3, type relation/entités inconnus ou dupliqués, contraintes source/cible, ID invalide, lecture exacte, audit de création, rollback atomique, trigger d’immuabilité et absence de vocabulaire ARET. |
| Verdict | `NOT_RUN` — aucun patch M2.3 n’est appliqué. |
| Mémoire liée | `MEM-DEC-009` à créer, `MEM-STATE-008`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, puis créer les tests et modules M2.3 sans étendre vers lifecycle ou knowledge. |

### LOG-0015 — Verdict M2.3 : registre relationnel entre entités

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.3 — Relation Registry` |
| Certitude | `OBSERVED` : les tests, le wheel et le contrôle de relation ont produit les résultats consignés ; aucune evidence métier VERA n’est encore disponible. |
| Baseline | M2.2 publié `8f367ca5fdf906f48a58e739360af97d1649c40a`; `LOG-0014`; C16 de la matrice, section 9 de la spécification et test ARET de lifecycle lus comme références de périmètre, sans import de code ARET. |
| Changement | Migration `003_relation_registry.sql`, `RelationService`, `RelationType`/`Relation`, contraintes déclaratives source/cible, arêtes exactes, triggers d’immuabilité et audit `RELATION_TYPE_REGISTERED`/`RELATION_CREATED`. |
| Invariants | I001, I002, I003, I011, I014, I015. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **48 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration M2.2→M2.3, type relationnel/entités inconnus ou dupliqués, contraintes source/cible, ID invalide, lecture exacte, rollback audit et refus SQL de rewrite/delete. |
| Contrôles de sûreté | `git diff --check` et scan anti-ARET du Core réussis. Les endpoints doivent être des entités existantes, chaque type peut contraindre leurs types, et mutation/audit restent dans une transaction unique. |
| Distribution | Wheel construit puis installé dans une cible temporaire ; migration `003` présente et création/relecture d’une relation typée réussie depuis le wheel. SHA-256 wheel : `a165e622ca79095b8732c8a2db3e4d421ff48e2379028720c5e4b839d789ea4d`; sortie de contrôle : `e2ee68133c3e49a177f37a55a7b692339d5b170e1fbcc503b2ac8348d6bdf209`. |
| Comparaison | M2.2 ne pouvait relier aucun objet. M2.3 ajoute une arête universelle entre entités, sans relation codée ARET, traversal, lifecycle, supersession ou connaissance. |
| Limites | Pas de traversal/FIND, lifecycle de supersession, relation vers knowledge/evidence/symbol, knowledge append-only, proof/evidence, artifact, work item, bundle, policy, capability, MCP ou compatibilité ARET. L’invariant I003 ne couvre encore que les types/arêtes relationnels, pas knowledge. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.3. `UNKNOWN` pour M2 dans son ensemble et toute parité ARET. |
| Mémoire liée | `MEM-STATE-009`, `MEM-DEC-009`, `MEM-WALL-001`. |
| Suivi | Mettre à jour le plan, la mémoire, la matrice et le manifeste ; relire le diff, committer puis publier atomiquement. |

### LOG-0016 — Hypothèse M2.4 : noyau knowledge append-only

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.4 — Knowledge Registry` |
| Hypothèse | Le Core peut enregistrer des types de connaissance puis ajouter/lire exactement des enregistrements append-only, avec hash de contenu, statuts épistémiques contrôlés et audit atomique, sans créer une voie de contournement vers `PROVEN`. |
| Périmètre | Migration `004`, `KnowledgeService`, `knowledge_type`, `knowledge`, métadonnées JSON canoniques, hash SHA-256 du contenu, statuts initiaux `ACTIVE`/`OBSERVED`/`HYPOTHESIS`/`CONFLICTING`, lecture exacte et audit de création. |
| Exclusions | `PROVEN`, preuves/evidence/artifacts, FTS/FIND, tags, sources documentaires, supersession/versioning, relations, mise à jour/suppression, promotion/demotion, bundle, policy, capability, MCP, pack/lecteur/import ARET. |
| Baseline | M2.3 publié au commit `5e68a9694137dd1e49f6a8b4a1700c7ca2e40764`; `LOG-0015`; C16 de la matrice, sections 7 et 17 de la spécification et contrat ARET d’append knowledge lus comme références de périmètre. |
| Invariants | I001, I002, I003, I004, I011, I014, I015. |
| Tests prévus | Migration 3→4, type inconnu/dupliqué, statut interdit, `PROVEN` rejeté, ID invalide, hash de contenu, lecture exacte, immuabilité SQL, audit de création, rollback atomique et absence de vocabulaire ARET. |
| Verdict | `NOT_RUN` — aucun patch M2.4 n’est appliqué. |
| Mémoire liée | `MEM-DEC-010` à créer, `MEM-STATE-009`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, puis créer les tests et modules M2.4 sans étendre vers evidence, recherche ou supersession. |

### LOG-0017 — Verdict M2.4 : noyau knowledge append-only

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.4 — Knowledge Registry` |
| Certitude | `OBSERVED` : les tests, le wheel et le contrôle knowledge ont produit les résultats consignés ; aucune evidence métier VERA admissible n’existe encore. |
| Baseline | M2.3 publié `5e68a9694137dd1e49f6a8b4a1700c7ca2e40764`; `LOG-0016`; C16 de la matrice, taxonomie de la spécification et contrat ARET d’append knowledge lus comme références de périmètre, sans import de code ARET. |
| Changement | Migration `004_knowledge_registry.sql`, `KnowledgeService`, `KnowledgeType`/`Knowledge`, hash SHA-256 de contenu, JSON canonique, statuts initiaux sûrs, triggers append-only et audit `KNOWLEDGE_TYPE_REGISTERED`/`KNOWLEDGE_APPENDED`. |
| Invariants | I001, I002, I003, I004, I011, I014, I015. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **57 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration 3→4, type inconnu/dupliqué, statuts admissibles, `PROVEN` rejeté par l’API et le schéma, ID invalide, hash de contenu, lecture exacte, hash incohérent, rollback audit et refus SQL de rewrite/delete. |
| Contrôles de sûreté | `git diff --check` et scan anti-ARET du Core réussis. `PROVEN` est refusé à l’admission et par la contrainte SQL, car aucune Evidence Store ne peut établir la preuve requise. |
| Distribution | Wheel construit puis installé dans une cible temporaire ; migration `004` présente et append/relecture d’une knowledge observée réussie depuis le wheel. SHA-256 wheel : `2614d3930d5f63489aa78d4f0bc35d2f17af207208f925a9d92442c05f935305`; sortie de contrôle : `14e8c5346dedec5c5c2f8166c18d5d2a9750f4feb753f0caa5644d47eef83950`. |
| Comparaison | M2.3 ne persistait pas de connaissance. M2.4 ajoute une assertion générique append-only, sans type ARET codé, FTS/FIND, source documentaire, supersession, relation ou preuve. |
| Limites | Pas de `PROVEN`, evidence/proof/artifact, FTS/FIND, tags, sources documentaires, supersession/versioning, relation vers knowledge, promotion/demotion, bundle, policy, capability, MCP ou compatibilité ARET. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.4. `UNKNOWN` pour M2 dans son ensemble et toute parité ARET. |
| Mémoire liée | `MEM-STATE-010`, `MEM-DEC-010`, `MEM-WALL-001`. |
| Suivi | Mettre à jour le plan, la mémoire, la matrice et le manifeste ; relire le diff, committer puis publier atomiquement. |

### LOG-0018 — Hypothèse M2.5 : provenance documentaire attachée

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.5 — Knowledge Source Registry` |
| Hypothèse | Le Core peut attacher à une connaissance existante une référence documentaire relative, bornée par des lignes et hashée, puis la relire exactement, sans lire le document, lancer un importeur, modifier la connaissance ou admettre `PROVEN`. |
| Périmètre | Migration `005`, `KnowledgeSource`, `KnowledgeSourceService`, références repository/revision/path/section/plage/source hash, unicité de slice, lecture bornée des sources d’une knowledge et audit de création. |
| Exclusions | Lecture/fetch de document, vérification du hash contre un fichier, importeur/migration batch, tags, FTS/FIND, evidence/proof/artifact, `PROVEN`, supersession/versioning, mutation/suppression de source, bundle, policy, capability, MCP, pack/lecteur/import ARET. |
| Baseline | M2.4 publié au commit `a783d3efefafe0b1e80c5454e8649f082858611e`; `LOG-0017`; C16 de la matrice, provenance ARET et spécification lus comme références de périmètre. |
| Invariants | I001, I002, I003, I004, I011, I014, I015. |
| Tests prévus | Migration 4→5, knowledge inconnue, source dupliquée, chemin absolu/traversant/lecteur Windows, lignes invalides, hash invalide, lecture exacte bornée, immuabilité SQL, audit de création, rollback atomique et absence de vocabulaire ARET. |
| Verdict | `NOT_RUN` — aucun patch M2.5 n’est appliqué. |
| Mémoire liée | `MEM-DEC-011` à créer, `MEM-STATE-010`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, puis créer les tests et modules M2.5 sans étendre vers import, fetch, evidence ou `PROVEN`. |

### LOG-0019 — Verdict M2.5 : provenance documentaire attachée

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.5 — Knowledge Source Registry` |
| Certitude | `OBSERVED` : les tests, le wheel et le contrôle de provenance ont produit les résultats consignés ; aucune source n’a été ouverte ou importée. |
| Baseline | M2.4 publié `a783d3efefafe0b1e80c5454e8649f082858611e`; `LOG-0018`; C16 de la matrice, schema/validateur ARET et spécification lus comme références de périmètre, sans import de code ARET. |
| Changement | Migration `005_knowledge_sources.sql`, `KnowledgeSourceService`, `KnowledgeSource`, référence repository/revision/path/section/lignes/hash, lecture exacte ou liste bornée, triggers append-only et audit `KNOWLEDGE_SOURCE_ATTACHED`. |
| Invariants | I001, I002, I003, I004, I011, I014, I015. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **65 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration 4→5, knowledge inconnue, duplicat de slice, chemin absolu/traversant/lecteur Windows, lignes/hash invalides, lecture ordonnée bornée, hash injecté invalide, rollback audit et refus SQL de rewrite/delete. |
| Contrôles de sûreté | `git diff --check` et scan anti-ARET du Core réussis. Une source est une donnée déclarée : le service ne lit, ne télécharge, ne vérifie ni n’interprète le document référencé. |
| Distribution | Wheel construit puis installé dans une cible temporaire ; migration `005` présente et attache/relecture de provenance réussie depuis le wheel. SHA-256 wheel : `e2049bfa5a4502a2984185cdb4e77ab032fbfb630ac07f3857676b6d56c34dcb`; sortie de contrôle : `b07586f3818a833b9dfc875b4b0ffabd04f202ffa813a13e0933ae91f6508dd2`. |
| Comparaison | M2.4 ne persistait que la connaissance hashée. M2.5 ajoute une provenance déclarative bornée, sans document source, import, evidence, relation ou admission `PROVEN`. |
| Limites | Pas de fetch/vérification de document, importeur/migration batch, evidence/proof/artifact, `PROVEN`, FTS/FIND, tags, supersession/versioning, relations vers knowledge, bundle, policy, capability, MCP ou compatibilité ARET. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.5. `UNKNOWN` pour M2 dans son ensemble et toute parité ARET. |
| Mémoire liée | `MEM-STATE-011`, `MEM-DEC-011`, `MEM-WALL-001`. |
| Suivi | Mettre à jour le plan, la mémoire, la matrice et le manifeste ; relire le diff, committer puis publier atomiquement. |

### LOG-0020 — Hypothèse M2.6 : supersession knowledge append-only

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.6 — Knowledge Supersession Registry` |
| Hypothèse | Le Core peut enregistrer une relation immuable de supersession entre une knowledge antérieure et une knowledge de remplacement déjà appendée, sans réécrire le contenu, le statut ni les métadonnées d’aucune des deux assertions. |
| Périmètre | Migration `006`, `KnowledgeSupersession`, `KnowledgeSupersessionService`, prédécesseur/successeur exacts, unicité d’un successeur par prédécesseur, prévention de cycle, lecture directe prédécesseur/successeur et audit de création. |
| Exclusions | Mise à jour de statut `SUPERSEDED`, mutation de knowledge, construction automatisée d’un successeur, traversal/lineage/FIND, version counter, `PROVEN`, evidence/proof/artifact, fetch/import, relation générique, bundle, policy, capability, MCP, pack/lecteur/import ARET. |
| Baseline | M2.5 publié au commit `fc34cccf867c3044203085ca1618b9095c2cfa44`; `LOG-0019`; cycle de versioning ARET lu comme référence de périmètre, sans import de code ARET. |
| Invariants | I001, I002, I003, I004, I011, I014, I015. |
| Tests prévus | Migration 5→6, knowledge inconnue, prédécesseur=successeur, prédécesseur déjà supersédé, successeur déjà lié, cycle, lecture directe, immuabilité SQL, audit de création, rollback atomique et absence de vocabulaire ARET. |
| Verdict | `NOT_RUN` — aucun patch M2.6 n’est appliqué. |
| Mémoire liée | `MEM-DEC-012` à créer, `MEM-STATE-011`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, puis créer les tests et modules M2.6 sans étendre vers statut, traversal, proof ou recherche. |

## 4. Protocole de journalisation d’un changement

Avant un patch, créer une entrée `HYPOTHESIS` ou compléter l’entrée du work item actif avec : cause supposée, comportement cible, surface de fichiers, baseline, invariants et tests prévus. Après le patch, ajouter des entrées distinctes pour `RUN`, `EVIDENCE`, `COMPARISON` et `VERDICT` si le changement est significatif. Une entrée de verdict doit pouvoir être lue indépendamment et répondre à quatre questions : qu’a-t-on changé, contre quelle baseline, quelle preuve a été produite et quelle limite demeure ?

| Cas | Entrée obligatoire | Exemple de verdict |
|---|---|---|
| Test ciblé vert | `RUN` + `COMPARISON` | `UNKNOWN` si le test ne couvre pas l’invariant prétendu. |
| Nouvelle divergence | `WALL` + `RISK` | `FAIL` pour le lot ; nouveau work item à qualifier. |
| Dépendance manquante | `WALL` | `NOT_RUN`, jamais `PASS`. |
| Migration avec parité | `RUN` + `EVIDENCE` + `COMPARISON` + `VERDICT` | `PASS` seulement si aucune régression pertinente n’est observée. |
| Décision durable | `DECISION` | `N/A` ; lien mémoire obligatoire. |
| Interruption/compaction | `HANDOFF` | `N/A` ; reprise active mise à jour. |

## 5. Handoff actif

> **État de reprise :** M2.5 est clos par son verdict `LOG-0019` et sera versionné dans son commit atomique. M1/M2.1/M2.2/M2.3/M2.4 demeurent publiés ; M2 complet et la parité ARET restent `UNKNOWN`, et `MEM-WALL-001` reste ouvert. Aucun sous-lot M2.6 n’est encore ouvert.

| Reprendre par | Lire ensuite | Ne pas faire avant |
|---|---|---|
| `UNIVERSALIZATION_WORKPLAN.md`, état actif puis rituel M2.6 | `PROJECT_MEMORY.md`, sections 4–7 ; `LOG-0018` et `LOG-0019`. | Présenter M2.5 comme un importeur, une Evidence Store ou une mémoire complète, ouvrir/télécharger/vérifier un document par effet de bord, admettre `PROVEN`, déclarer une parité ARET, créer un alias `ARET://`, démarrer M2.6 sans hypothèse distincte ou lever `MEM-WALL-001` par hypothèse. |

## 6. Gabarit d’entrée future

```markdown
### LOG-NNNN — Titre factuel

| Champ | Valeur |
|---|---|
| Date | YYYY-MM-DD |
| Type | INSPECTION / CHANGE / RUN / EVIDENCE / COMPARISON / VERDICT / WALL / HANDOFF |
| Lot | M… |
| Certitude | OBSERVED / HYPOTHESIS / PROVEN / DECISION / RISK / BLOCKED |
| Sources | Commit, chemins, lignes, commandes, hashes, artefacts, records mémoire. |
| Baseline | LOG-… / commit / hash / métrique. |
| Invariants | I… |
| Résultat | Faits mesurés, sans interprétation non signalée. |
| Comparaison | Baseline vs run, divergences et dimensions non couvertes. |
| Verdict | PASS / FAIL / UNKNOWN / NOT_RUN avec motif. |
| Mémoire liée | MEM-… |
| Suivi | Prochaine action atomique ou condition de blocage. |
```

## Références

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — dépôt de référence"

### LOG-0021 — Verdict M2.6 : supersession knowledge déclarative

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.6 — Knowledge Supersession Registry` |
| Certitude | `OBSERVED` : les tests, le contrôle de distribution et les checks statiques ont produit les résultats consignés ; aucune preuve métier VERA n’est admise ou créée. |
| Baseline | M2.5 publié `fc34cccf867c3044203085ca1618b9095c2cfa44`; `LOG-0020`; invariants I001/I002/I003/I004/I011/I014/I015. ARET-MMU est resté propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Changement | Migration `006_knowledge_supersession.sql`, sidecar `knowledge_supersession`, `KnowledgeSupersession` et `KnowledgeSupersessionService`. Une relation directe immutable lie deux knowledge préexistantes ; chaque prédécesseur et chaque successeur sont uniques, les self-links et cycles sont refusés, et les deux lectures sont exactes. L’audit consigne `KNOWLEDGE_SUPERSESSION_RECORDED`. |
| Invariants | I001, I002, I003, I004, I011, I014, I015. Les enregistrements knowledge eux-mêmes restent inchangés, append-only et liés au ProjectIdentity. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **72 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration 5→6, identifiants inconnus, self-link, prédécesseur/successeur dupliqués, cycle de longueur trois, lectures exactes, immuabilité SQL et rollback conjoint lien+audit. |
| Contrôles de sûreté | `git diff --check` réussit. Le scan ciblé des artefacts M2.6 ne trouve aucune dépendance ARET, admission `PROVEN`, evidence, FTS/FIND ou API de découverte/traversal. Les seules APIs publiques sont `supersede`, `successor_of` et `predecessor_of`. |
| Distribution | Wheel construit via `pip wheel`, installé dans une cible isolée, puis contrôlé par un script hors dépôt qui initialise le store, append deux knowledge, enregistre et relit une supersession. SHA-256 wheel : `2e95db8422fa68f9f59c93c19886efcd700fe062c5f6e037088b524252f8b479`; sortie de contrôle : `63bc2eb446dfd81bf749c8525508a493de600ec7bf0b964695d6db251c8e04b3`; migration : `80bb4a78e92bedebe313bf6b5dfd09819e47bfaf872e1df5522bb5c0b486bafe`; service : `f4047c56e630c25cb61c918cd8a2754458e0d48607bec4e2d4c78109c94a7060`. |
| Comparaison | M2.5 pouvait déclarer des sources d’une knowledge mais pas exprimer qu’une assertion nouvelle remplace une assertion antérieure. M2.6 ajoute seulement ce lien direct immutable, sans réécrire le contenu, le hash, les métadonnées, la provenance ou le statut de l’assertion remplacée. |
| Limites | Aucun statut `SUPERSEDED`, version counter, création automatique de successeur, traversal ou listing de lignée, intégration à `RelationService`, evidence/proof/artifact, admission `PROVEN`, fetch/import, FTS/FIND, policy, capability, bundle, MCP, pack ou compatibilité ARET n’est livré. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.6 et ses gates techniques. `UNKNOWN` pour M2 au total, toute parité ARET et tout comportement hors périmètre. |
| Mémoire liée | `MEM-STATE-012`, `MEM-DEC-012`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, le plan, la matrice et le README ; relancer les checks finaux, puis committer et publier atomiquement. |

### LOG-0022 — Publication M2.6 vérifiée

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RECORD` / `HANDOFF` |
| Lot | `M2.6 — Publication` |
| Certitude | `OBSERVED` |
| Baseline | Verdict technique M2.6 `LOG-0021`; branche VERA locale et distante sur `main`; ARET-MMU inchangé à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, arbre propre. |
| Commit publié | `e6afb43e1f840cbf5c909f6522d65c351ae62411` — `feat: add M2 knowledge supersession`. |
| Vérification | `git push origin main` a réussi, puis `git ls-remote origin refs/heads/main` a retourné le même SHA que `git rev-parse HEAD`. L’arbre VERA était propre après publication. |
| Limites | Cette publication ne change pas le verdict M2.6 ni les exclusions : M2 complet et toute parité ARET restent `UNKNOWN`; `MEM-WALL-001` reste actif. |
| Mémoire liée | `MEM-STATE-012`, `MEM-DEC-012`, `MEM-WALL-001`. |
| Suivi | Actualiser les références de reprise qui signalaient la publication en attente, committer ce record documentaire puis vérifier de nouveau la référence publique. |

### LOG-0023 — Hypothèse M2.7 : registre d’assets hashés

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.7 — Asset Registry` |
| Hypothèse | Le Core peut enregistrer et relire des assets binaires locaux dans SQLite, append-only et liés à leur SHA-256, sans accéder à un chemin client, sans réseau, sans runner et sans les confondre avec une evidence ou une preuve. |
| Périmètre | Migration `007`, table `asset` contenant identifiant, hash, taille, media type, contenu binaire, auteur et horodatage ; `AssetService` pour l’enregistrement, la lecture exacte de métadonnées et la lecture de bytes après revérification du hash/format ; audit atomique. |
| Justification | I005 et la politique de sécurité imposent la vérification du hash avant toute lecture d’artefact. L’espace d’adressage Core possède déjà la ressource générique `asset`, mais le schéma ne possède encore aucun registre associé. Le stockage du payload en SQLite évite l’exposition d’un chemin, les courses fichier↔base et toute sémantique d’import/fetch. |
| Exclusions | Aucun chemin, fichier externe, symlink, fetch, réseau, import/export, bundle, déduplication inter-projet, execution, validator, evidence/proof, admission `PROVEN`, relation vers knowledge, mutation/suppression, recherche/listing, capability, policy ou MCP. Aucun vocabulaire ARET. |
| Baseline | VERA-MMU `main` et `origin/main` à `2986774c91bb3e90f4dfce9457a17ce6e19ad99b`, propres ; M2.6 publié `e6afb43e1f840cbf5c909f6522d65c351ae62411`. ARET-MMU intact à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, propre. |
| Invariants | I001, I002, I004, I005, I011, I014, I015. |
| Tests prévus | Migration 6→7 ; asset valide ; hash/taille/media type/identifiant invalides ; duplicat ; lecture exacte avec hash revérifié ; altération SQL ; triggers d’immuabilité ; rollback asset+audit ; wheel isolé. |
| Verdict | `NOT_RUN` — aucun patch M2.7 n’est appliqué. |
| Mémoire liée | `MEM-DEC-013` à créer, `MEM-STATE-012`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, écrire les tests M2.7 avant la migration et le service, puis vérifier les gates complètes. |

### LOG-0024 — Verdict M2.7 : registre d’assets hashés

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.7 — Asset Registry` |
| Certitude | `OBSERVED` : les tests, la migration, les checks statiques et le wheel ont produit les résultats consignés ; aucune evidence métier VERA n’est créée ou admise. |
| Baseline | M2.6 publié `e6afb43e1f840cbf5c909f6522d65c351ae62411`; `LOG-0023`; VERA `main`/`origin/main` à `2986774c91bb3e90f4dfce9457a17ce6e19ad99b` avant patch. ARET-MMU est resté propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Changement | Migration `007_asset_registry.sql`, table SQLite stricte `asset`, `Asset` et `AssetService`. Un asset contient bytes, SHA-256, taille, media type, auteur et horodatage ; il est append-only, audité et adressé par `vera://<project>/asset/<id>`. |
| Invariants | I001, I002, I004, I005, I011, I014, I015. Le hash SHA-256 et la taille sont revérifiés avant que `read` ne restitue les bytes. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **79 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration 6→7, enregistrement/lecture exacte, hash/taille/media type/ID invalides, duplicats, asset SQL altéré, rewrite/delete SQL refusés et rollback conjoint asset+audit. |
| Contrôles de sûreté | `git diff --check` réussit. Le scan ciblé des nouveaux artefacts M2.7 ne trouve aucune dépendance ARET, admission `PROVEN`, evidence, MCP ou réseau. La seule API publique M2.7 est `record`, `get`, `read` ; aucun listing, scan, import ou export n’est exposé. |
| Distribution | Wheel construit via `pip wheel`, installé dans une cible isolée, puis contrôlé par un script hors dépôt qui initialise un store, écrit et relit un asset hashé. SHA-256 wheel : `6fa127198a92f67d51de48853df6c061826cdfee78d71da8e2bfc9776dea9fdd`; sortie de contrôle : `9cf128e5a13914b989cef7aa17539d41cad218e333cef54f41dee83e43ab3002`; migration : `8009c584940d4c262cb7eceb38d08ef3269c23896900a4c6a8da0811fb99ba04`; service : `90a60e112b1951a025d0ac3c977733294e9ec14db11309a3f19605f7ffa7c2ea`. |
| Comparaison | M2.6 rendait le remplacement d’assertions knowledge explicite, mais le Core ne possédait aucun contenu binaire canonique protégé par hash avant lecture. M2.7 ajoute ce substrat d’asset sans créer de fichier externe, execution, validator, preuve ou promotion épistémique. |
| Limites | Aucun chemin/fichier externe, symlink, fetch, réseau, import/export, bundle, déduplication inter-projet, relation avec knowledge, execution, validator, evidence/proof, admission `PROVEN`, policy, capability, MCP, recherche/listing ou mutation/suppression n’est livré. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.7 et ses gates techniques. `UNKNOWN` pour M2 au total, toute parité ARET et toute sémantique d’evidence ou d’exécution. |
| Mémoire liée | `MEM-STATE-013`, `MEM-DEC-013`, `MEM-WALL-001`. |
| Suivi | Mettre à jour mémoire, plan, matrice et README ; relancer les checks finaux, puis committer et publier atomiquement. |

### LOG-0025 — Publication M2.7 vérifiée

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RECORD` / `HANDOFF` |
| Lot | `M2.7 — Publication` |
| Certitude | `OBSERVED` |
| Baseline | Verdict technique M2.7 `LOG-0024`; branche VERA locale et distante sur `main`; ARET-MMU inchangé à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, arbre propre. |
| Commit publié | `f4b878061dfaa1dd4f22b6b6f21a18f49ec5a1f8` — `feat: add M2 asset registry`. |
| Vérification | `git push origin main` a réussi, puis `git ls-remote origin refs/heads/main` a retourné le même SHA que `git rev-parse HEAD`. L’arbre VERA était propre après publication. |
| Limites | Cette publication ne change pas le verdict M2.7 ni les exclusions : M2 complet et toute parité ARET restent `UNKNOWN`; `MEM-WALL-001` reste actif. |
| Mémoire liée | `MEM-STATE-013`, `MEM-DEC-013`, `MEM-WALL-001`. |
| Suivi | Actualiser les références de reprise qui signalaient la publication en attente, committer ce record documentaire puis vérifier de nouveau la référence publique. |

### LOG-0026 — Hypothèse M2.8 : association knowledge–asset déclarative

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.8 — Knowledge-Asset Link Registry` |
| Hypothèse | Le Core peut rendre explicite l’association entre une knowledge existante et un asset existant par un sidecar immutable et audité, sans prétendre que l’asset est une evidence, sans modifier la knowledge et sans exposer de découverte ou lecture indirecte. |
| Périmètre | Migration `008`, table `knowledge_asset_link` avec clés étrangères vers `knowledge` et `asset`, unicité de paire, audit et triggers anti-réécriture/suppression ; dataclass et service dédiés pour créer/lire une seule paire exacte. |
| Justification | M2.4 rend les assertions knowledge hashées ; M2.7 rend les bytes assets canoniques et vérifiés avant lecture. Une liaison déclarative permet de les référencer sans franchir I004 : une association n’est ni une evidence, ni un résultat, ni une promotion `PROVEN`. |
| Exclusions | Aucun changement de statut knowledge, `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, traversal, listing, recherche, lecture de bytes à travers le lien, fetch, fichier externe, bundle, policy, capability, MCP, import/export ou compatibilité ARET. |
| Baseline | VERA-MMU `main` et `origin/main` à `fb3b287c1c973ca4d56c317dca899276bb65ccd4`, propres. M2.7 publié `f4b878061dfaa1dd4f22b6b6f21a18f49ec5a1f8`. ARET-MMU intact à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, propre. |
| Invariants | I001, I002, I003, I004, I005, I011, I014, I015. |
| Tests prévus | Migration 7→8 ; association et lecture exacte ; endpoints inconnus ; duplicat ; identifiants invalides ; immuabilité SQL ; rollback lien+audit ; absence de mutation knowledge et de lecture asset ; wheel isolé. |
| Verdict | `NOT_RUN` — aucun patch M2.8 n’est appliqué. |
| Mémoire liée | `MEM-DEC-014` à créer, `MEM-STATE-014`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, écrire les tests M2.8 avant la migration et le service, puis exécuter les gates complètes. |

### LOG-0027 — Verdict M2.8 : association knowledge–asset déclarative

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.8 — Knowledge-Asset Link Registry` |
| Certitude | `OBSERVED` : les tests, la migration, les contrôles statiques et le wheel ont produit les résultats consignés ; le lien créé n’est pas une evidence VERA-MMU. |
| Baseline | M2.7 publié `f4b878061dfaa1dd4f22b6b6f21a18f49ec5a1f8`; `LOG-0026`; VERA `main`/`origin/main` à `fb3b287c1c973ca4d56c317dca899276bb65ccd4` avant patch. ARET-MMU est resté propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Changement | Migration `008_knowledge_asset_links.sql`, table stricte `knowledge_asset_link`, `KnowledgeAssetLink` et `KnowledgeAssetLinkService`. Une paire relie une knowledge et un asset déjà existants, avec foreign keys, unicité de paire, immuabilité et audit atomique. |
| Invariants | I001, I002, I003, I004, I005, I011, I014, I015. La liaison ne modifie ni contenu, hash ou statut knowledge, ni métadonnées d’asset ; elle ne lit aucun byte et ne confère aucune admissibilité. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **85 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration 7→8, création/lecture de paire exacte, endpoints et identifiants invalides, duplicat, immuabilité SQL, absence de mutation des endpoints et rollback conjoint lien+audit. |
| Contrôles de sûreté | `git diff --check` réussit. Le scan ciblé des nouveaux artefacts M2.8 ne trouve aucune dépendance ARET, admission `PROVEN`, `AssetService`, lecture de bytes, execution, validator, MCP ou réseau. La seule API publique M2.8 est `link` et `get`; aucun listing, traversal, import, export ou read n’est exposé. |
| Distribution | Wheel construit via `pip wheel`, installé dans une cible isolée, puis contrôlé par un script hors dépôt qui crée knowledge, asset et lien, relit la paire et confirme le schéma 8. SHA-256 wheel : `72af37c2edb36eb04e926ee4dbb724ccc350a084e1ddb407dda9f31f456dcac5`; sortie de contrôle : `7c2919ee95bef8e6ceb12f163cba4306ef8c594ee50bdf1e30c166ffef2e17d2`; migration : `8d7c0d050f8c885249b2c06fd7e2909fc10a9f7ab85d6e2617c8986df4b5fc0c`; service : `5a322dd24ebcdb77ba0d6dec0df110ecfe51bb0133ee0ac7a45f9d3817da99c6`. |
| Comparaison | M2.7 possédait des assets hashés mais sans association persistée à une knowledge. M2.8 ajoute une référence déclarative minimale, sans conversion en evidence, preuve, résultat d’exécution ou promotion épistémique. |
| Limites | Aucun statut `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, listing/traversal, lecture asset via lien, fetch, fichier externe, bundle, policy, capability, MCP, import/export ou compatibilité ARET n’est livré. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.8 et ses gates techniques. `UNKNOWN` pour M2 au total, toute parité ARET et toute sémantique d’evidence ou d’exécution. |
| Mémoire liée | `MEM-STATE-014`, `MEM-DEC-014`, `MEM-WALL-001`. |
| Suivi | Mettre à jour mémoire, plan, matrice et README ; relancer les checks finaux, puis committer et publier atomiquement. |

### LOG-0028 — Publication M2.8 vérifiée

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RECORD` / `HANDOFF` |
| Lot | `M2.8 — Publication` |
| Certitude | `OBSERVED` |
| Baseline | Verdict technique M2.8 `LOG-0027`; branche VERA locale et distante sur `main`; ARET-MMU inchangé à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, arbre propre. |
| Commit publié | `8982b7855e09db8ed009ca2081021b9210bc8088` — `feat: add M2 knowledge asset links`. |
| Vérification | `git push origin main` a réussi, puis `git ls-remote origin refs/heads/main` a retourné le même SHA que `git rev-parse HEAD`. L’arbre VERA était propre après publication. |
| Limites | Cette publication ne change pas le verdict M2.8 ni les exclusions : M2 complet et toute parité ARET restent `UNKNOWN`; `MEM-WALL-001` reste actif. |
| Mémoire liée | `MEM-STATE-014`, `MEM-DEC-014`, `MEM-WALL-001`. |
| Suivi | Actualiser les références de reprise qui signalaient la publication en attente, committer ce record documentaire puis vérifier de nouveau la référence publique. |

### LOG-0029 — Hypothèse M2.9 : index borné des associations knowledge–asset

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.9 — Bounded Knowledge-Asset Index` |
| Hypothèse | Le Core peut exposer un index direct, déterministe et borné des associations déjà enregistrées pour un endpoint knowledge ou asset exact, sans restituer les contenus des endpoints, sans graph traversal et sans conférer de sémantique de preuve. |
| Périmètre | Migration `009` créant l’index SQL nécessaire à la lecture directe inversée par asset ; méthodes `list_for_knowledge` et `list_for_asset` sur `KnowledgeAssetLinkService`, retour limité et ordonné d’objets de liaison existants seulement. |
| Justification | I002 distingue FIND et READ. Après M2.8, une paire doit être connue à l’avance pour être relue. Un index direct, borné et sans contenu constitue une découverte contrôlée, distincte de la lecture des knowledge ou des bytes d’asset, sans ouvrir un moteur de recherche ni un graphe. |
| Exclusions | Aucun contenu knowledge/asset, `AssetService.read`, statut knowledge, `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, traversal multi-sauts, recherche texte, filtre libre, fetch, fichier externe, bundle, policy, capability, MCP, import/export ou compatibilité ARET. |
| Baseline | VERA-MMU `main` et `origin/main` à `bb0cf0c428eb4fc324a33563f1ec53cc5ae4dd9a`, propres. M2.8 publié `8982b7855e09db8ed009ca2081021b9210bc8088`. ARET-MMU intact à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, propre. |
| Invariants | I001, I002, I003, I004, I005, I011, I014, I015. |
| Tests prévus | Migration 8→9 ; index direct par knowledge et asset ; ordre/borne ; endpoint et limite invalides ; absence de contenu ou de lecture asset ; immuabilité préservée ; wheel isolé. |
| Verdict | `NOT_RUN` — aucun patch M2.9 n’est appliqué. |
| Mémoire liée | `MEM-DEC-015` à créer, `MEM-STATE-015`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, écrire les tests M2.9 avant migration et service, puis exécuter les gates complètes. |

### LOG-0030 — Verdict M2.9 : index borné des associations knowledge–asset

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.9 — Bounded Knowledge-Asset Index` |
| Certitude | `OBSERVED` : les tests, la migration, les contrôles statiques et le wheel ont produit les résultats consignés ; un résultat d’index ne constitue pas une evidence VERA-MMU. |
| Baseline | M2.8 publié `8982b7855e09db8ed009ca2081021b9210bc8088`; `LOG-0029`; VERA `main`/`origin/main` à `bb0cf0c428eb4fc324a33563f1ec53cc5ae4dd9a` avant patch. ARET-MMU est resté propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Changement | Migration `009_knowledge_asset_link_indexes.sql` ajoutant l’index inversé `(asset_id, knowledge_id)` ; `KnowledgeAssetLinkService.list_for_knowledge` et `.list_for_asset`, retour direct, trié et limité d’objets de liaison uniquement. |
| Invariants | I001, I002, I003, I004, I005, I011, I014, I015. L’index impose un endpoint existant et une limite bornée, ne lit aucun contenu de knowledge ou d’asset et ne modifie aucun état. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **90 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration 8→9, index direct dans les deux directions, ordre déterministe, borne, endpoint/limite invalides, endpoint existant sans lien et absence de contenu d’endpoint. |
| Contrôles de sûreté | `git diff --check` réussit. Le scan ciblé des nouveaux artefacts M2.9 ne trouve aucune dépendance ARET, admission `PROVEN`, `AssetService`, lecture de bytes, execution, validator, MCP ou réseau. La surface est limitée à `link`, `get`, `list_for_knowledge`, `list_for_asset` ; aucun filtre libre, search, scan, traversal, import, export ou read n’est exposé. |
| Distribution | Wheel construit via `pip wheel`, installé dans une cible isolée, puis contrôlé par un script hors dépôt qui crée des liens et vérifie les listes ordonnées/bornées, sans contenu. SHA-256 wheel : `e7bd35c33e1f257fb253c0de6edc67885fdaa2d26d7a5743b8bc413a317558ac`; sortie de contrôle : `a41655c91f394192e51e1e38c962af4e23ed909b248d6721787b5757f46d4111`; migration : `2000ac153a3cd496c8abd13e2b1925e2e2df6149711d7786cce8fe4a3e53325b`; service : `626ecc23cfd074ca65786ffc1a47c326706716ad924b0e67ae7929185142da5c`. |
| Comparaison | M2.8 permettait uniquement la lecture d’une paire connue. M2.9 rend les associations d’un endpoint exact observables de manière bornée, sans ouvrir un moteur de recherche, un graphe ou une lecture de contenu. |
| Limites | Aucun contenu endpoint, `AssetService.read`, statut `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, traversal multi-sauts, recherche texte, filtre libre, fetch, fichier externe, bundle, policy, capability, MCP, import/export ou compatibilité ARET n’est livré. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.9 et ses gates techniques. `UNKNOWN` pour M2 au total, toute parité ARET et toute sémantique d’evidence ou d’exécution. |
| Mémoire liée | `MEM-STATE-015`, `MEM-DEC-015`, `MEM-WALL-001`. |
| Suivi | Mettre à jour mémoire, plan, matrice et README ; relancer les checks finaux, puis committer et publier atomiquement. |

### LOG-0031 — Publication M2.9 vérifiée

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RECORD` / `HANDOFF` |
| Lot | `M2.9 — Publication` |
| Certitude | `OBSERVED` |
| Baseline | Verdict technique M2.9 `LOG-0030`; branche VERA locale et distante sur `main`; ARET-MMU inchangé à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, arbre propre. |
| Commit publié | `c888958cc184c621b5cf02b95defa0d3fb706b56` — `feat: add M2 bounded knowledge asset index`. |
| Vérification | `git push origin main` a réussi, puis `git ls-remote origin refs/heads/main` a retourné le même SHA que `git rev-parse HEAD`. L’arbre VERA était propre après publication. |
| Limites | Cette publication ne change pas le verdict M2.9 ni les exclusions : M2 complet et toute parité ARET restent `UNKNOWN`; `MEM-WALL-001` reste actif. |
| Mémoire liée | `MEM-STATE-015`, `MEM-DEC-015`, `MEM-WALL-001`. |
| Suivi | Actualiser les références de reprise qui signalaient la publication en attente, committer ce record documentaire puis vérifier de nouveau la référence publique. |

### LOG-0032 — Hypothèse M2.10 : provenance déclarative des assets

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.10 — Asset Source Registry` |
| Hypothèse | Le Core peut attacher à un asset existant une référence documentaire déclarative immutable, hashée et bornée par lignes, sans ouvrir, télécharger, vérifier ni comparer la ressource déclarée au contenu de l’asset. |
| Périmètre | Migration `010` créant `asset_source`; `AssetSource` et `AssetSourceService` dédiés avec attach/get/list_for asset, validations de repository/révision/chemin relatif/plage/section/hash, contraintes de foreign key, unicité de slice, triggers append-only et audit atomique. |
| Justification | M2.5 a établi la provenance documentaire déclarative des knowledge et M2.7 a établi les assets hashés. M2.10 applique le même contrat de provenance au contenu binaire sans ajouter une règle de vérification ou une relation de preuve. |
| Exclusions | Aucun fichier ou chemin externe ouvert, fetch, import, comparaison de hash asset↔source, read de bytes, `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, traversal, recherche libre, bundle, policy, capability, MCP ou compatibilité ARET. |
| Baseline | VERA-MMU `main` et `origin/main` à `3b9f4798fd3385c33c53aea2140326e8cd0bc88a`, propres. M2.9 publié `c888958cc184c621b5cf02b95defa0d3fb706b56`. ARET-MMU intact à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, propre. |
| Invariants | I001, I002, I004, I005, I011, I014, I015. |
| Tests prévus | Migration 9→10 ; attache/lecture/liste bornée ; endpoints et données invalides ; duplicat ; immuabilité SQL ; rollback audit ; absence de lecture/fetch/comparaison ; wheel isolé. |
| Verdict | `NOT_RUN` — aucun patch M2.10 n’est appliqué. |
| Mémoire liée | `MEM-DEC-016` à créer, `MEM-STATE-016`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, écrire les tests M2.10 avant migration et service, puis exécuter les gates complètes. |

### LOG-0033 — Verdict M2.10 : provenance déclarative des assets

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.10 — Asset Source Registry` |
| Certitude | `OBSERVED` : les tests, la migration, les contrôles statiques et le wheel ont produit les résultats consignés ; une source attachée n’est pas une evidence VERA-MMU. |
| Baseline | M2.9 publié `c888958cc184c621b5cf02b95defa0d3fb706b56`; `LOG-0032`; VERA `main`/`origin/main` à `3b9f4798fd3385c33c53aea2140326e8cd0bc88a` avant patch. ARET-MMU est resté propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Changement | Migration `010_asset_sources.sql`, table stricte `asset_source`, `AssetSource` et `AssetSourceService`. Une référence porte repository, revision, chemin relatif, plage de lignes, section et SHA-256 déclarés pour un asset existant, avec foreign key, unicité de slice, triggers append-only et audit atomique. |
| Invariants | I001, I002, I004, I005, I011, I014, I015. La source ne lit ni le document déclaré ni les bytes de l’asset, ne compare aucun hash et ne modifie aucune métadonnée d’asset. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **96 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration 9→10, attache/lecture/liste bornée, données/endpoints invalides, duplicats, immuabilité SQL, asset inchangé et rollback conjoint source+audit. |
| Contrôles de sûreté | `git diff --check` réussit. Le scan ciblé des nouveaux artefacts M2.10 ne trouve aucune dépendance ARET, admission `PROVEN`, `AssetService`, lecture de bytes, fetch, comparaison, execution, validator, MCP ou réseau. La surface publique se limite à `attach`, `get`, `list_for`; aucun listing global, search, scan, traversal, import, export ou read n’est exposé. |
| Distribution | Wheel construit via `pip wheel`, installé dans une cible isolée, puis contrôlé par un script hors dépôt qui crée un asset et une provenance déclarative, relit/liste la référence et vérifie le schéma 10. SHA-256 wheel : `19a7c67caabffb6c07fb28b2d1324254536092611a10d657648265a52a3eac6e`; sortie de contrôle : `ee0df256dd021741593177f39a719fe8d22639addc2174a4f86f97e21001efc2`; migration : `bd8dd0c5a41dd056ce9a38f13adb27fe1447915ef7527876522b2eb8cf6d1adb`; service : `c4c41a235a6d31bc9bbc44f8a09f8dbfae9549569187437f33f25e59a8e5692b`. |
| Comparaison | M2.5 attachait des références documentaires déclaratives à une knowledge ; M2.7 introduisait les assets hashés. M2.10 attache la même forme déclarative à l’asset sans égaler les hashes, sans inspecter l’origine et sans transformer la provenance en preuve. |
| Limites | Aucun document/fichier externe, fetch, import, comparaison source↔asset, `AssetService.read`, statut `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, traversal, recherche libre, bundle, policy, capability, MCP ou compatibilité ARET n’est livré. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.10 et ses gates techniques. `UNKNOWN` pour M2 au total, toute parité ARET et toute sémantique d’evidence ou d’exécution. |
| Mémoire liée | `MEM-STATE-016`, `MEM-DEC-016`, `MEM-WALL-001`. |
| Suivi | Mettre à jour mémoire, plan, matrice et README ; relancer les checks finaux, puis committer et publier atomiquement. |

### LOG-0034 — Publication M2.10 vérifiée

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RECORD` / `HANDOFF` |
| Lot | `M2.10 — Publication` |
| Certitude | `OBSERVED` |
| Baseline | Verdict technique M2.10 `LOG-0033`; branche VERA locale et distante sur `main`; ARET-MMU inchangé à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, arbre propre. |
| Commit publié | `e568cd5fe8bda80b4d9434836a9173ad0195d9f0` — `feat: add M2 asset provenance`. |
| Vérification | `git push origin main` a réussi, puis `git ls-remote origin refs/heads/main` a retourné le même SHA que `git rev-parse HEAD`. L’arbre VERA était propre après publication. |
| Limites | Cette publication ne change pas le verdict M2.10 ni les exclusions : M2 complet et toute parité ARET restent `UNKNOWN`; `MEM-WALL-001` reste actif. |
| Mémoire liée | `MEM-STATE-016`, `MEM-DEC-016`, `MEM-WALL-001`. |
| Suivi | Actualiser les références de reprise qui signalaient la publication en attente, committer ce record documentaire puis vérifier de nouveau la référence publique. |

### LOG-0035 — Hypothèse M2.11 : index exact d’assets par hash

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.11 — Bounded Asset Hash Index` |
| Hypothèse | Le Core peut lister les métadonnées d’assets existants partageant un SHA-256 exact, dans un ordre déterministe et une borne explicite, sans restituer leurs bytes ni créer de sémantique de déduplication, d’évidence ou de preuve. |
| Périmètre | Migration `011` ajoutant seulement un index SQL sur `asset(content_hash, id)` ; extension minimale de `AssetService` avec une lecture d’index par hash exact et limite validée ; aucune nouvelle table ni mutation. |
| Justification | M2.7 a séparé `AssetService.get` (métadonnées) de `read` (bytes hash-vérifiés), et M2.9 a établi le patron de liste directe, ordonnée et bornée. M2.11 rend le hash exact utilisable comme index sans ouvrir une recherche textuelle ou une lecture de contenu. |
| Exclusions | Aucun `read`, contenu binaire, déduplication, fusion, suppression, mutation, fetch, import/export, preuve/evidence, admission `PROVEN`, validator, execution, gate, relation générique, traversal, filtre libre, préfixe/substring de hash, policy, capability, MCP ou compatibilité ARET. |
| Baseline | VERA-MMU `main` et `origin/main` à `2ca3235b33d4e0493cce7e9513ac60b3a49f2bab`, propres. M2.10 publié `e568cd5fe8bda80b4d9434836a9173ad0195d9f0`. ARET-MMU intact à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, propre. |
| Invariants | I001, I002, I004, I005, I011, I014, I015. |
| Tests prévus | Migration 10→11 ; multiple assets au même hash ; ordre/borne ; hash/limite invalides ; résultat vide ; aucune byte exposée ; non-mutation/audit absent ; wheel isolé. |
| Verdict | `NOT_RUN` — aucun patch M2.11 n’est appliqué. |
| Mémoire liée | `MEM-DEC-017` à créer, `MEM-STATE-017`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la mémoire active, écrire les tests M2.11 avant migration et service, puis exécuter les gates complètes. |

### LOG-0036 — Rejet contrôlé du candidat M2.11 initial

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `COMPARISON` / `RECORD` |
| Candidat rejeté | Index exact et borné d’assets par `content_hash`. |
| Observation | `007_asset_registry.sql` déclare déjà `asset.content_hash TEXT NOT NULL UNIQUE`. SQLite maintient donc déjà un index d’unicité et interdit plusieurs assets pour un même hash. Le test rouge a confirmé que l’enregistrement de deux contenus identiques échoue par contrainte d’unicité. |
| Verdict | `REJECTED` — ne pas ajouter la migration `011_asset_hash_indexes.sql` ni une API de liste multi-résultats redondante. Aucun patch de production M2.11 n’a été appliqué ; le test exploratoire est retiré. |
| Motif de sûreté | Une migration/index supplémentaire ne fournirait pas de nouvelle capacité et risquerait de présenter à tort un mécanisme de déduplication ou de recherche. La doctrine impose un patch minimal fondé sur une différence observée. |
| Conséquence | Réouvrir la phase d’hypothèse M2.11. Le candidat suivant doit rester déclaratif, borné et sans lecture de contenu ni preuve. |
| Mémoire liée | `MEM-DEC-017` est remplacé par `MEM-DEC-018` ; `MEM-WALL-001` inchangé. |

### LOG-0037 — Hypothèse M2.11 révisée : index exact des sources knowledge par hash

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.11 — Bounded Knowledge-Source Hash Index` |
| Hypothèse | Le Core peut lister les métadonnées de références `knowledge_source` ayant un SHA-256 source exact, dans un ordre déterministe et une borne explicite, sans lire la knowledge cible, ouvrir le document, vérifier la source ou conférer une preuve. |
| Périmètre | Migration `011` ajoutant seulement un index SQL sur `knowledge_source(source_hash, knowledge_id, id)` ; extension minimale de `KnowledgeSourceService` avec une liste par hash exact et limite validée ; aucune nouvelle table ni mutation. |
| Justification | `knowledge_source.source_hash` n’est pas unique : plusieurs knowledge peuvent déclarer le même slice hash. M2.5 a établi les références documentaires déclaratives et M2.9 le patron de liste directe, ordonnée et bornée. L’index ajoute donc une différence réelle sans toucher au contenu des knowledge. |
| Exclusions | Aucun `KnowledgeService.get`, contenu knowledge, ouverture/fetch/import de document, comparaison de hash, preuve/evidence, admission `PROVEN`, validator, execution, gate, relation générique, traversal, recherche textuelle, préfixe/substring de hash, policy, capability, MCP ou compatibilité ARET. |
| Baseline | VERA-MMU `main` et `origin/main` à `2ca3235b33d4e0493cce7e9513ac60b3a49f2bab`, propres. M2.10 publié `e568cd5fe8bda80b4d9434836a9173ad0195d9f0`. Le candidat `LOG-0035` est rejeté par `LOG-0036`. ARET-MMU intact à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, propre. |
| Invariants | I001, I002, I004, I011, I014, I015. |
| Tests prévus | Migration 10→11 ; mêmes hash déclarés sur knowledge distinctes ; ordre/borne ; hash/limite invalides ; résultat vide ; absence de contenu knowledge/audit/mutation ; wheel isolé. |
| Verdict | `NOT_RUN` — aucun patch de production M2.11 n’est appliqué. |
| Mémoire liée | `MEM-DEC-018`, `MEM-STATE-017`, `MEM-WALL-001`. |
| Suivi | Remplacer le record de décision actif en mémoire, écrire les tests M2.11 révisés avant migration et service, puis exécuter les gates complètes. |

### LOG-0038 — Verdict M2.11 : index exact des sources knowledge par hash

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.11 — Bounded Knowledge-Source Hash Index` |
| Certitude | `OBSERVED` : les tests, la migration, les contrôles statiques et le wheel ont produit les résultats consignés ; une source indexée n’est pas une evidence VERA-MMU. |
| Rejet préalable | Le candidat `LOG-0035` d’index d’assets par hash a été rejeté : `asset.content_hash` est déjà `UNIQUE`, ce qui rend une liste multi-résultats et un index supplémentaire redondants (`LOG-0036`). Aucun code de ce candidat n’est présent. |
| Baseline | M2.10 publié `e568cd5fe8bda80b4d9434836a9173ad0195d9f0`; `LOG-0037`; VERA `main`/`origin/main` à `2ca3235b33d4e0493cce7e9513ac60b3a49f2bab` avant patch. ARET-MMU est resté propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Changement | Migration `011_knowledge_source_hash_indexes.sql` créant `idx_knowledge_source_hash_knowledge`; `KnowledgeSourceService.list_by_source_hash` impose un SHA-256 complet et une borne, retourne des `KnowledgeSource` dans l’ordre `knowledge_id`, chemin, lignes, id et ne modifie aucun état. |
| Invariants | I001, I002, I004, I011, I014, I015. La méthode ne lit ni knowledge cible ni document source, ne vérifie ni ne compare aucun contenu et n’insère aucun audit. |
| Run | `PYTHONPATH=src python3 -m pytest -q` : **100 passés, 14 sous-tests, 0 échec**. Les cas couvrent migration 10→11, mêmes hash sur knowledge distinctes, ordre, borne, hash/limites invalides, résultat vide, absence de contenu knowledge et absence d’audit de lecture. |
| Contrôles de sûreté | `git diff --check` réussit. Le scan ciblé de M2.11 ne trouve aucune dépendance ARET, admission `PROVEN`, `KnowledgeService`, lecture de contenu, fetch, comparaison, execution, validator, MCP ou réseau. La surface ajoutée se limite à `list_by_source_hash`; aucun search, scan, traversal, import, export ou read n’est exposé. |
| Distribution | Wheel construit via `pip wheel`, installé dans une cible isolée, puis contrôlé par un script hors dépôt qui crée deux knowledge et deux sources partageant le même hash déclaré, lit l’index et vérifie le schéma 11. SHA-256 wheel : `e24cb7f767386044da53a7faf0ec41f42dd8eaf25dc4e57accd3bfc2c89ea577`; sortie de contrôle : `6e15849e95fa383f09ed7e3bb49651c569a78c450a815a7b01c61b86b928e82c`; migration : `f5cd619752b1b10f5c7ea77c53a2cf1bd012f3606c360eb4e26da471d8170e0c`; service : `6764969733fe40bdebc7952133facacd2afc81c6c1a92eab92b14a0e79f19dcb`. |
| Comparaison | M2.5 listait les sources d’une knowledge exacte ; M2.11 inverse cette vue uniquement par hash déclaré exact, sans traverser vers la knowledge ni changer la qualité épistémique. Le rejet préalable d’un index d’asset redondant montre que le sous-lot final ajoute une capacité observée et non un index décoratif. |
| Limites | Aucun contenu knowledge/document, `KnowledgeService.get`, ouverture/fetch/import, comparaison de hash, `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, traversal, recherche textuelle, préfixe de hash, bundle, policy, capability, MCP ou compatibilité ARET n’est livré. `MEM-WALL-001` reste inchangé. |
| Verdict | `PASS` pour le périmètre M2.11 révisé et ses gates techniques. `UNKNOWN` pour M2 au total, toute parité ARET et toute sémantique d’evidence ou d’exécution. |
| Mémoire liée | `MEM-STATE-017`, `MEM-DEC-017`, `MEM-DEC-018`, `MEM-WALL-001`. |
| Suivi | Mettre à jour mémoire, plan, matrice et README ; relancer les checks finaux, puis committer et publier atomiquement. |

### LOG-0039 — Publication M2.11 vérifiée

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RECORD` / `HANDOFF` |
| Lot | `M2.11 — Publication` |
| Certitude | `OBSERVED` |
| Baseline | Verdict technique M2.11 `LOG-0038`, avec rejet préalable du candidat d’index d’assets consigné dans `LOG-0036`; branche VERA locale et distante sur `main`; ARET-MMU inchangé à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, arbre propre. |
| Commit publié | `34d9c2595ab93c1e041c88fb213451b2b1794929` — `feat: add M2 knowledge source hash index`. |
| Vérification | `git push origin main` a réussi, puis `git ls-remote origin refs/heads/main` a retourné le même SHA que `git rev-parse HEAD`. L’arbre VERA était propre après publication. |
| Limites | Cette publication ne change pas le verdict M2.11 ni les exclusions : M2 complet et toute parité ARET restent `UNKNOWN`; `MEM-WALL-001` reste actif. |
| Mémoire liée | `MEM-STATE-017`, `MEM-DEC-017`, `MEM-DEC-018`, `MEM-WALL-001`. |
| Suivi | Actualiser les références de reprise qui signalaient la publication en attente, committer ce record documentaire puis vérifier de nouveau la référence publique. |

### LOG-0040 — Décision de cadrage terminal M2 et cadence

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `DECISION` / `ROADMAP` |
| Déclencheur | Le propriétaire demande un cadrage plus strict et plus efficace : la rigueur ne doit pas produire une succession indéfinie de micro-lots décoratifs. |
| Source normative | La spécification fournie, section 55, définit M2 comme **Universal Schema** : entity registry, relation registry, symbol, work item, execution et capability registry. Elle place explicitement en M3 runner engine, validators, evidence, gates et work graph. Les sections 10 à 15 distinguent work item, execution, proof et Evidence Store. |
| Écart observé | VERA livre entity/relations et le socle M2.4–M2.11, mais ne possède encore aucune table `symbol`, `work_item`, `capability` ou `execution`. Le catalogue URI réserve déjà `symbol`, `work-item` et `execution`; il ne les matérialise pas. |
| Décision de frontière | L’Evidence Store, l’admission `PROVEN`, HMAC, validators, runners, gates et work graph relèvent de M3. M2 ne les anticipe pas. M2 peut uniquement préparer des modèles persistants déclaratifs sans exécuter, valider, promouvoir ou gouverner. |
| Cadence adoptée | Cesser les index ou raffinements isolés qui ne ferment aucune gate. Regrouper les manques restants en trois **macro-lots fonctionnels** puis un audit de sortie : `M2.12 Symbol Registry`, `M2.13 Work-Item Backbone`, `M2.14 Capability Declaration & Execution Schema`, `M2.EXIT Universal-Schema Gate`. Chaque macro-lot conserve le rituel complet, mais aucun sous-lot décoratif n’est ouvert entre eux. |
| M2.12 | Registre générique, immutable et référentiellement contraint de symboles attachables à une entity existante : kind, path, identifier, signature déclarative, metadata, lecture exacte et audit. Aucun scan de code, résolution de fichier, FTS, import ARET ou sémantique `function_symbol`. |
| M2.13 | Backbone générique de work items : création exacte, parent optionnel, types/statuts initiaux sûrs, metadata et audit. Aucun lifecycle mutable, gate, dépendance, traversal, assignation active, exécution ni work graph. |
| M2.14 | Registre immutable de capability **déclarative** et schéma `execution` réservé au moteur M3. Aucun runner, shell, commande, réseau, policy, validator, écriture d’exécution, verdict de preuve ou admission `PROVEN`. L’API M2 se limite aux déclarations de capability ; l’écriture/lecture opérationnelle d’execution ouvre en M3 avec le runner réel. |
| Gate M2.EXIT | Les migrations historiques et fresh install couvrent les ressources M2 prévues ; les services M2 exposés restent exacts, bornés et sans effets opérationnels ; FKs, immuabilité/audit et rollback sont testés ; upgrade 001→courant et wheel isolé passent ; scan anti-ARET et barrières no-shell/no-network/no-path/no-`PROVEN` passent ; M3 reste non commencé. Cette gate conclut `PASS` pour **Universal Schema M2**, sans conclure la parité ARET ni l’achèvement du produit. |
| Invariants | I001–I006, I010, I011, I014, I015 ; plus I004 et I013 pour préparer la frontière capability/execution sans l’ouvrir. |
| Exclusions confirmées | Aucun Evidence Store, proof, HMAC, admission, `PROVEN`, runner, validator, gate, work graph, lifecycle, policy, shell, réseau, fetch, import ARET, pack ou MCP dans M2 restant. |
| Statut | `DECIDED` ; aucun code M2.12 n’est ouvert par cette décision. |
| Mémoire liée | `MEM-DEC-019`, `MEM-WALL-001`. |
| Suivi | Mettre le workplan et la mémoire en cohérence, publier le cadrage documentaire, puis seulement ouvrir M2.12 par le rituel normal. |

### LOG-0041 — Hypothèse M2.12 : Symbol Registry générique

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.12 — Symbol Registry` |
| Baseline | VERA `b1b6704bf97b081b45f9b7fb972e0a07b0360e05`, `main` propre et alignée à `origin/main`; ARET `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, `main` propre et non modifié. Baseline VERA : 100 tests et 14 sous-tests `PASS`; schéma courant 001–011. |
| Écart contractuel | La spécification Universal Schema requiert `symbol`; `CORE_RESOURCE_TYPES` autorise déjà `symbol`, mais aucune table, migration, modèle ni service correspondant n’existe. |
| Hypothèse | Si VERA ajoute un `SymbolService` append-only avec la migration 012, un symbole référant obligatoirement une `entity` existante, `kind`, `path`, `identifier`, `signature`, metadata JSON canonique, création/lecture exacte, unicité sémantique et audit atomique, alors le Core ferme la ressource déclarative `symbol` de M2 sans importer le modèle ARET `function_symbol` ni ouvrir une capacité M3. |
| Décision de modélisation | La colonne est nommée `entity_id` plutôt que `component_id` : son endpoint est une entity universelle, pas un vocabulaire de composant. Une entity propriétaire est obligatoire pour garantir l’intégrité référentielle du registre et empêcher un espace de symboles non rattaché. `path` est un locator déclaratif strict, jamais un chemin ouvert ou résolu. |
| Tests-first attendus | Migration 001→012 et installation fresh ; création/lecture et URI `vera://…/symbol/…`; FK owner inconnue ; identifiant/kind/path/JSON invalides ; doublon sémantique ; audit atomique et rollback ; refus des UPDATE/DELETE ; absence de scan, lecture de fichier, réseau, FTS/FIND, preuve, relation automatique ou vocabulaire ARET. |
| Invariants | I001, I002, I003, I011, I014, I015. |
| Non-objectifs | Aucun scanner de source, parser, résolution de fichier, FTS/FIND, import ARET, traversal, relation automatique, evidence, execution, validator, gate, policy, shell, réseau ni promotion `PROVEN`. |
| Verdict | `PENDING` — tests et patch minimal à produire; aucune capacité n’est encore livrée. |

### LOG-0042 — Verdict M2.12 : Symbol Registry

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.12 — Symbol Registry` |
| Changement minimal | Migration `012_symbol_registry.sql`; module `symbols.py`; exports publics `Symbol`, `SymbolError`, `SymbolNotFoundError`, `SymbolService`; tests-first `test_symbols.py`; ajustement mécanique des attentes de baseline globale 11→12. Aucune CLI, capability, policy, runner, evidence, gate, réseau, fichier externe ou dépendance ARET n’est ajoutée. |
| Exécution ciblée | `PYTHONPATH=src python3 -m pytest -q tests/test_symbols.py` : 9 tests `PASS`. |
| Exécution Core | `PYTHONPATH=src python3 -m pytest -q` : 109 tests et 14 sous-tests `PASS`. |
| Distribution | Wheel construit avec `python3 -m pip wheel --no-deps --no-build-isolation`; SHA-256 `c2a674fccc719c3c6e890cebae8bd27d2aa9e8dc1d987beba9031da6089456ab`. Installation hors arbre source dans `/tmp/vera-m212-install` et script d’intégration : migration 012, entity propriétaire et symbole vérifiés `PASS`. |
| Contrôles | `git diff --check` `PASS`; scan ciblé de `symbols.py` et migration 012 sans vocabulaire ARET, `function_symbol`, shell, réseau ni ouverture de fichier `PASS`. |
| Comparaison | Baseline M2.11 : 100 tests et 14 sous-tests `PASS`, schéma 011. Résultat : 109 tests et 14 sous-tests `PASS`, schéma 012. Les neuf tests additionnels couvrent migration, création/lecture exacte, URI, FK, entrées invalides, unicité, audit/rollback et immuabilité SQL. |
| Invariants | I001, I002, I003, I011, I014, I015. |
| Limites | Le `path` reste déclaratif ; aucune lecture, recherche, résolution, import V1, relation automatique, proof, execution, validator, gate ou admission `PROVEN` n’existe. C04/C16 restent `SPLIT`; la parité ARET exhaustive reste `UNKNOWN` sous `MEM-WALL-001`. |
| Verdict | `PASS` pour M2.12 ; `UNKNOWN` pour M2 restant et toute parité ARET. |
| Mémoire liée | `MEM-STATE-019`, `MEM-DEC-022`, `MEM-STATE-020`, `MEM-WALL-001`. |
| Suivi | Mettre à jour le plan et le README, committer/publier atomiquement, puis ouvrir la baseline/hypothèse distincte M2.13. |

### LOG-0043 — Publication vérifiée M2.12

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RECORD` / `HANDOFF` |
| Lot | `M2.12 — Symbol Registry` |
| Commit fonctionnel | `769e8779dfcaf3f8fbe5a5d8beadbf0c7114a6a4` — `feat: add generic symbol registry`. |
| Publication | `git push origin main` a publié `b1b6704..769e877`; `git ls-remote origin refs/heads/main` retourne `769e8779dfcaf3f8fbe5a5d8beadbf0c7114a6a4`. |
| État final | `main...origin/main` propre après publication ; helper d’authentification éphémère supprimé. ARET reste propre au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Verdict | `PASS` pour la publication M2.12. |
| Mémoire liée | `MEM-STATE-019`, `MEM-STATE-020`, `MEM-WALL-001`. |
| Suivi | Publier ce record documentaire, puis établir la baseline M2.13 sans transférer la responsabilité de work graph, gate, policy ou Evidence Store dans M2. |

### LOG-0044 — Hypothèse M2.13 : Work-Item Backbone

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.13 — Work-Item Backbone` |
| Baseline | VERA `48962892e0f2576e5940108c22643daba10bcc04`, `main` propre et alignée à `origin/main`; ARET `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, `main` propre et non modifié. Baseline VERA : 109 tests et 14 sous-tests `PASS`; schéma courant 001–012. |
| Écart contractuel | La spécification Universal Schema requiert `work_item`; `CORE_RESOURCE_TYPES` autorise déjà `work-item`, mais aucune table, migration, modèle ni service correspondant n’existe. |
| Hypothèse | Si VERA ajoute une migration 013 et un `WorkItemService` append-only, créant/lisant exactement un work item générique de type fermé (`GOAL`, `EPIC`, `WORK_ITEM`, `SUBTASK`), titre/description, priorité, assignee déclaratif, metadata JSON et parent optionnel existant, alors le Core ferme la ressource structurelle `work-item` sans ouvrir lifecycle, graph ou gate. |
| Décision de sûreté | Le statut initial est imposé à `PLANNED` à la création et `updated_at` est égal à `created_at`; aucune API de mise à jour, transition, `DONE`, assignation active, dépendance ou traversal n’existe. Un parent doit déjà exister; l’immutabilité et les FKs empêchent les cycles créés a posteriori. |
| Tests-first attendus | Migration 001→013 et installation fresh ; création/lecture et URI `vera://…/work-item/…`; types/identifiants/JSON/priority invalides ; parent inconnu ou self-parent ; statut initial imposé ; audit atomique/rollback ; UPDATE/DELETE SQL refusés ; aucune liste, traversal, gate, execution, evidence ou vocabulaire ARET. |
| Invariants | I001, I002, I003, I009, I011, I014, I015. |
| Non-objectifs | Aucun lifecycle, update, dépendance, work graph, Front, resume, gate, execution, evidence, proof, policy, shell, réseau, import ARET ou promotion `PROVEN`. |
| Verdict | `PENDING` — tests et patch minimal à produire; aucune capacité n’est encore livrée. |

### LOG-0045 — Verdict M2.13 : Work-Item Backbone

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.13 — Work-Item Backbone` |
| Changement minimal | Migration `013_work_item_registry.sql`; module `work_items.py`; exports publics `WorkItem`, `WorkItemError`, `WorkItemNotFoundError`, `WorkItemService`; tests-first `test_work_items.py`; ajustement mécanique des attentes de baseline globale 12→13. Aucune CLI, lifecycle, work graph, gate, capability, policy, runner, evidence, réseau, fichier externe ou dépendance ARET n’est ajoutée. |
| Exécution ciblée | `PYTHONPATH=src python3 -m pytest -q tests/test_work_items.py` : 9 tests `PASS`. |
| Exécution Core | `PYTHONPATH=src python3 -m pytest -q` : 118 tests et 14 sous-tests `PASS`. |
| Distribution | Wheel construit avec `python3 -m pip wheel --no-deps --no-build-isolation`; SHA-256 `1405e80ffd9bab0d986256fb15abc3a6723c4ea63440459023a3f40316a8d876`. Installation hors arbre source dans `/tmp/vera-m213-install` et script d’intégration : migration 013, parent/child, statut initial et URI vérifiés `PASS`. |
| Contrôles | `git diff --check` `PASS`; scan ciblé de `work_items.py` et migration 013 sans vocabulaire ARET, shell, réseau ni ouverture de fichier `PASS`. |
| Comparaison | Baseline M2.12 : 109 tests et 14 sous-tests `PASS`, schéma 012. Résultat : 118 tests et 14 sous-tests `PASS`, schéma 013. Les neuf tests additionnels couvrent migration, création/lecture exacte, URI, type fermé, parent, statut initial, entrées invalides, audit/rollback et immuabilité SQL. |
| Invariants | I001, I002, I003, I009, I011, I014, I015. |
| Limites | Aucun lifecycle, update, `DONE`, assignation active, dépendance, traversal, work graph, Front, resume, gate, execution, proof, evidence ou admission `PROVEN` n’existe. C05/C16 restent `SPLIT`; la parité ARET exhaustive reste `UNKNOWN` sous `MEM-WALL-001`. |
| Verdict | `PASS` pour M2.13 ; `UNKNOWN` pour M2 restant et toute parité ARET. |
| Mémoire liée | `MEM-STATE-021`, `MEM-DEC-023`, `MEM-STATE-022`, `MEM-WALL-001`. |
| Suivi | Mettre à jour la matrice, la mémoire, le plan et le README ; committer/publier atomiquement, puis ouvrir la baseline/hypothèse distincte M2.14. |

### LOG-0046 — Publication vérifiée M2.13

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RECORD` / `HANDOFF` |
| Lot | `M2.13 — Work-Item Backbone` |
| Commit fonctionnel | `c1db7e1e6140e100c8702b49b0ef18e7b05a3abc` — `feat: add immutable work item backbone`. |
| Publication | `git push origin main` a publié `4896289..c1db7e1`; `git ls-remote origin refs/heads/main` retourne `c1db7e1e6140e100c8702b49b0ef18e7b05a3abc`. |
| État final | `main...origin/main` propre après publication ; helper d’authentification éphémère supprimé. ARET reste propre au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Verdict | `PASS` pour la publication M2.13. |
| Mémoire liée | `MEM-STATE-021`, `MEM-STATE-022`, `MEM-WALL-001`. |
| Suivi | Publier ce record documentaire, puis établir la baseline M2.14 sans ouvrir runner, validator, Evidence Store, gate, policy ou admission `PROVEN`. |

### LOG-0047 — Hypothèse M2.14 : Capability Declaration & Execution Schema

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `HYPOTHESIS` |
| Lot | `M2.14 — Capability Declaration & Execution Schema` |
| Baseline | VERA `a7ae4831524447a1ffb1fb03d294d3be4fabe5ba`, `main` propre et alignée à `origin/main`; ARET `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, `main` propre et non modifié. Baseline VERA : 118 tests et 14 sous-tests `PASS`; schéma courant 001–013. |
| Écart contractuel | Le schéma M2 requiert un capability registry et une `execution` distincte de proof. `CORE_RESOURCE_TYPES` ne contient pas encore `capability`; aucune table, migration, modèle ni service de capability/execution n’existe. |
| Hypothèse | Si VERA ajoute une migration 014 avec un registre immutable de capabilities déclaratives, fermé sur les types universels de la spécification, et une table `execution` append-only référant une capability mais sans service public d’écriture/lecture, alors M2 ferme les deux dernières ressources de schéma sans déplacer runner, policy, validation, Evidence Store ou gate de M3. |
| Décision de frontière | `CapabilityService` ne persiste que identité, nom, description, kind, version et schémas JSON déclaratifs d’inputs/paramètres/outputs. Il n’accepte ni commande, runner, policy, réseau, timeout, artefact, validator ni secret. La table `execution` est contrôlée structurellement par migration/FK/immutabilité seulement : une écriture/lecture opérationnelle ne sera ouverte qu’avec le runner M3. |
| Tests-first attendus | Migration 001→014 et installation fresh ; nouvelle ressource URI `capability`; création/lecture exacte de capability; types/version/JSON/identifiants invalides; unicité, audit atomique et rollback; triggers anti-UPDATE/DELETE sur capability/execution; FK execution→capability vérifiée par SQL de structure; absence de `ExecutionService`, runner, shell, policy, validator, evidence, proof, gate et admission `PROVEN`. |
| Invariants | I001, I002, I003, I004, I006, I007, I008, I011, I014, I015. |
| Non-objectifs | Aucun runner, commande, shell, paramètres exécutés, policy, timeout, réseau, validator, artefact, writing/lecture opérationnelle d’execution, Evidence Store, HMAC, proof, gate, work graph, admission ou promotion `PROVEN`, import ARET. |
| Verdict | `PENDING` — tests et patch minimal à produire; aucune capacité d’exécution n’est encore livrée. |

### LOG-0048 — Verdict M2.14 : Capability Declaration & Execution Schema

| Champ | Valeur |
|---|---|
| Date | 25 août 2026 |
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Lot | `M2.14 — Capability Declaration & Execution Schema` |
| Changement minimal | Migration `014_capability_execution_schema.sql`; `CapabilityService`/`Capability`; URI `capability`; tests-first `test_capabilities.py`; attentes de baseline globale 13→14. La table `execution` est structurelle et immutable, sans service d’exécution. |
| Exécution ciblée | `tests/test_capabilities.py` : 8 tests `PASS`. |
| Exécution Core | `PYTHONPATH=src python3 -m pytest -q` : 126 tests et 14 sous-tests `PASS`. |
| Distribution | Wheel isolé `PASS`, SHA-256 `b94a06c2216abd97847402a77ac9ab1fcde2a0836b93ad24389548631bc3cd08`; migration 014, URI capability et absence de `ExecutionService` vérifiées hors arbre source. |
| Contrôles | `git diff --check` `PASS`; scan sans accès externe, runner/execution service, shell ou vocabulaire ARET `PASS`. |
| Comparaison | Baseline M2.13 : 118 tests et 14 sous-tests, schéma 013. Résultat : 126 tests et 14 sous-tests, schéma 014. Les huit tests ajoutés couvrent migrations, capability exacte, URI, validation, audit/rollback, triggers et FK execution. |
| Invariants | I001, I002, I003, I004, I006, I007, I008, I011, I014, I015. |
| Limites | La capability est déclarative ; aucun runner/policy/validator/commande/réseau/artefact n’est stocké. `execution` n’est ni produite ni lue par un service M2 et n’est jamais une proof. Aucun Evidence Store, admission ou `PROVEN` n’existe. |
| Verdict | `PASS` pour M2.14 ; `UNKNOWN` pour M2.EXIT et toute parité ARET. |
| Mémoire liée | `MEM-STATE-023`, `MEM-DEC-024`, `MEM-WALL-001`. |
| Suivi | Mettre à jour mémoire, plan, README et matrice ; publier M2.14 puis exécuter l’audit M2.EXIT séparé. |

### LOG-0049 — Gate terminale M2.EXIT

| Champ | Valeur |
|---|---|
| Type | `RUN` / `COMPARISON` / `VERDICT` |
| Périmètre | Contrat Universal Schema M2 : migrations 001–014, entity, relation, symbol, work item, capability et execution structurelle. |
| Contrôles | Upgrade indépendant 001→014 `PASS`; création d’entity/symbol/work item/capability après upgrade `PASS`; execution reste vide et sans service. Suite complète : 126 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scans M2 sans shell/réseau/I/O externe/ARET et sans runner/`ExecutionService` `PASS`. |
| Verdict | `PASS` pour **M2 Universal Schema**. `UNKNOWN` pour la parité ARET exhaustive sous `MEM-WALL-001`; M3 reste non commencé. |
| Limites | Evidence Store, runner, validator, policy, admission, HMAC, `PROVEN`, gates et work graph sont explicitement différés à M3. |
| Suivi | Mettre à jour mémoire/plan/README, publier le record terminal, puis ouvrir M3 seulement sous un plan et une hypothèse distincts. |

### LOG-0050 — Hypothèse M3.1 : Closed Capability Contract

| Champ | Valeur |
|---|---|
| Type | `HYPOTHESIS` |
| Baseline | VERA `0df618e1f9de127760564e4c9ea1692f8a8bcafb`, propre et alignée ; 126 tests et 14 sous-tests `PASS`; M2.EXIT `PASS`. ARET reste propre à `7f7b4df…`; parité exhaustive `UNKNOWN` sous `MEM-WALL-001`. |
| Écart | Les capabilities M2 sont déclaratives, immuables et sans runner/policy. M3 doit être fermé et sûr avant qu’un runner puisse exister. |
| Hypothèse | Ajouter un registre append-only de contrats de capability, distinct de la déclaration M2 immuable, avec un profil de runner **fermé**, une policy **fermée**, timeout borné, schéma de paramètres JSON et `yields_proof` explicite, sans commande, chemin, secret ni exécution. |
| Sûreté | Le client ne pourra sélectionner qu’un `capability_id`; aucun contrat n’accepte du shell, une URL, un path ou une commande. Aucun service `run`, écriture d’execution, evidence, HMAC, admission ou `PROVEN` ne sera ajouté dans ce lot. |
| Tests-first attendus | Migration, FK capability, enums/policies/timeout/JSON, unicité, audit/rollback, immuabilité SQL, lecture exacte et absence expresse de runner/`ExecutionService`/promotion. |
| Verdict | `PENDING` — aucune capacité M3 n’est encore livrée. |

### LOG-0051 — Publication vérifiée M3.1

| Champ | Valeur |
|---|---|
| Lot | `M3.1 — Closed Capability Contract` |
| Commit | `79a3e188e2645b685866217c89930d93b965792e` — `feat: add closed capability contracts`. |
| Validation | 129 tests et 14 sous-tests `PASS`; migration 015, FK, enums, audit/rollback et immuabilité SQL couverts. |
| Publication | `git push origin main` et `git ls-remote` confirment `79a3e188e2645b685866217c89930d93b965792e`; arbre propre et helper supprimé. |
| Limite | Le seul runner autorisé est `NOOP` et aucune API `run`/execution/evidence/proof/gate n’est présente. |
| Suivi | Mettre à jour le plan/mémoire, puis ouvrir séparément la baseline du premier runner borné. |

### LOG-0052 — Préparation M3.2 : runner borné

| Champ | Valeur |
|---|---|
| Contrainte | Le client sélectionnera exclusivement une capability déclarée et des paramètres validés; aucune commande, path, URL ou shell arbitraire ne sera accepté. |
| Précondition | Le contrat fermé M3.1 publié fixe actuellement `NOOP` et `DENY_NETWORK`; le premier runner réel exigera une hypothèse, une policy et des tests séparés. |
| Statut | `PREPARATION` — aucun runner ni execution opérationnelle n’est encore livré. |

### LOG-0053 — Hypothèse M3.2 : NOOP Execution Runner

| Champ | Valeur |
|---|---|
| Hypothèse | Un `ExecutionService` limité au contrat `NOOP` et `DENY_NETWORK` peut valider un objet de paramètres JSON, écrire une execution `COMPLETED` à code `0`, un environnement déclaré minimal et un résultat déclaratif, puis auditer le fait dans la même transaction. |
| Sûreté | Aucun sous-processus, shell, fichier, réseau, artefact, secret, validator, evidence ou promotion `PROVEN`; `yields_proof` doit être `false`. Une capability sans contrat ou avec paramètres hors schéma est refusée. |
| Tests attendus | Résolution exacte capability/contrat, validation JSON-object minimaliste, refus de tout contrat non NOOP/non DENY_NETWORK ou `yields_proof`, rollback audit, immuabilité de l’execution et absence de lecture/evidence. |
| Statut | `PENDING` — tests-first et patch minimal à produire. |

### LOG-0054 — Verdict M3.2 : NOOP Execution Runner

| Champ | Valeur |
|---|---|
| Résultat | `ExecutionService.run_noop` exige un contrat exact `NOOP` / `DENY_NETWORK` avec `yields_proof=false`, paramètres objet et actor. Il écrit une execution `COMPLETED`, code `0`, environnement/résultat JSON minimaux, sans artefact. |
| Validation | Tests dédiés : 2 `PASS`; suite complète : 131 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan sans processus, shell, réseau ou I/O externe `PASS`. |
| Limite | Une execution est un fait opérationnel auditée; elle ne constitue ni evidence, ni proof, ni admission `PROVEN`. |
| Verdict | `PASS` pour M3.2 technique; publication et documentation de continuité restent à finaliser. |

### LOG-0055 — Publication vérifiée M3.2

| Champ | Valeur |
|---|---|
| Commit | `61a3bba33ee0dbad0453f1b3f87ac3a28a4fb0d7` — `feat: add noop execution runner`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt propre et helper supprimé. |
| Statut | `PASS` pour la publication M3.2. Evidence, proof, admission, HMAC et `PROVEN` restent absents. |

### LOG-0056 — Hypothèse M3.3 : Evidence Store minimal

| Champ | Valeur |
|---|---|
| Hypothèse | Ajouter une evidence append-only liée à une execution existante, typée dans un enum universel, hashée, avec verdict fermé (`PASS`, `FAIL`, `ERROR`, `SKIPPED`, `UNKNOWN`) et statut d’admission initial `PENDING`. |
| Sûreté | L’écriture d’evidence n’admet rien, ne promeut aucune knowledge et ne produit aucun `PROVEN`. `PASS` seul demeure insuffisant sans policy d’admission explicite. |
| Invariants | I001, I003, I004, I005, I006, I011, I014, I015. |
| Statut | `PENDING` — tests-first, schéma et service minimaux à produire. |

### LOG-0057 — Verdict M3.3 : Evidence Store minimal

| Champ | Valeur |
|---|---|
| Résultat | Migration 016 et `EvidenceService` : evidence append-only liée à une execution, type/verdict fermés, contenu JSON canonique SHA-256 et admission initiale `PENDING`. |
| Validation | Tests dédiés : 3 `PASS`; suite complète : 134 tests et 14 sous-tests `PASS`; diff et scan de périmètre `PASS`. |
| Limite | Aucun mécanisme d’admission, HMAC, promotion de knowledge ou `PROVEN` n’est présent. |
| Verdict | `PASS` pour M3.3 technique; publication à finaliser. |


### LOG-0058 — Publication vérifiée M3.3

| Champ | Valeur |
|---|---|
| Commit | `a7b29168c49515e543832a6829c4d4ebade584f1` — `feat: add hashed evidence store`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt propre et helper supprimé. |
| Statut | `PASS` pour la publication M3.3. Admission, HMAC, promotion `PROVEN` et gates restent absents. |


### LOG-0059 — Hypothèse M3.4 : Evidence Admission Policy

| Champ | Valeur |
|---|---|
| Hypothèse | Une policy d’admission append-only peut décider `ADMIT` ou `REJECT` pour une evidence existante, uniquement si son verdict est `PASS`, avec motif et audit, sans modifier l’evidence elle-même. |
| Sûreté | `FAIL`, `ERROR`, `SKIPPED` et `UNKNOWN` sont non admissibles. L’admission ne promeut pas encore de knowledge à `PROVEN`; HMAC reste absent tant qu’une policy de projet ne le requiert explicitement. |
| Statut | `PENDING` — tests-first, relation de décision immutable et validations dédiées à produire. |


### LOG-0060 — Verdict M3.4 : Evidence Admission Policy

| Champ | Valeur |
|---|---|
| Résultat | Migration 017 et `AdmissionService` : une décision immutable `ADMITTED`/`REJECTED` par evidence, avec motif et audit. `ADMITTED` refuse toute evidence non `PASS`. |
| Validation | Tests dédiés : 2 `PASS`; suite complète : 136 tests et 14 sous-tests `PASS`; diff et scan de périmètre `PASS`. |
| Limite | L’evidence conserve son statut `PENDING`; knowledge n’est pas modifiée et aucune promotion `PROVEN`, HMAC ou gate n’est ajoutée. |
| Verdict | `PASS` pour M3.4 technique; publication à finaliser. |


### LOG-0061 — Publication vérifiée M3.4

| Champ | Valeur |
|---|---|
| Commit | `fda5154035af0d7859a652e432c9a330dba681e3` — `feat: add evidence admission policy`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt propre et helper supprimé. |
| Statut | `PASS` pour la publication M3.4. HMAC, lien evidence↔knowledge, promotion `PROVEN`, gates et work graph restent à concevoir séparément. |


### LOG-0062 — Hypothèse M3.5 : Work Graph & Admission Gate

| Champ | Valeur |
|---|---|
| Hypothèse | Ajouter des dépendances immuables entre work items existants, avec anti-cycle, puis une gate déclarative dont l’évaluation retourne uniquement `PASS` lorsqu’une admission `ADMITTED` existe pour chaque evidence requise. |
| Sûreté | Aucun runner, mutation de work item, traversal libre, admission nouvelle, HMAC ou promotion `PROVEN`. La gate rend une décision calculée et auditée; elle ne modifie aucune evidence ni knowledge. |
| Statut | `PENDING` — tests-first, schéma et services bornés à produire. |


### LOG-0063 — Hypothèse M3.5 : HMAC, Evidence-Knowledge & PROVEN

| Champ | Valeur |
|---|---|
| Hypothèse | Une liaison immutable entre knowledge et evidence peut déclencher une promotion `PROVEN` seulement lorsque l’evidence est `PASS`, possède une décision `ADMITTED` et satisfait la règle HMAC explicitement requise par la policy du projet. |
| Sûreté | Le secret HMAC reste uniquement en mémoire d’exécution et n’est jamais sérialisé. Sans policy explicite ou HMAC valide lorsqu’il est requis, la promotion échoue bruyamment. Une promotion ne modifie ni evidence, ni admission; elle crée un record de décision traçable. |
| Statut | `PENDING` — policy, tests-first, liaison immutable et transaction de promotion à produire. |


### LOG-0064 — Décision de conception : promotion PROVEN append-only

| Champ | Valeur |
|---|---|
| Décision | Une promotion `PROVEN` ne réécrira jamais un knowledge historique. Elle sera représentée par un record dérivé immutable, lié à la knowledge cible, à l’evidence `PASS` admise et à une policy de promotion. |
| HMAC | Si la policy requiert HMAC, le service recevra le secret uniquement en mémoire d’exécution; aucun champ de schéma, audit ou erreur ne doit en exposer la valeur. |
| Statut | `DECISION` — le test et le patch doivent préserver I003, I004, I006 et I014. |


### LOG-0065 — Baseline M3.5 : promotion dérivée

| Champ | Valeur |
|---|---|
| Baseline | VERA `3b2d05f50812178a1cff4c6b8a46349b9c810877`, `main` propre et alignée; 136 tests et 14 sous-tests `PASS`. |
| Contrat | Toute preuve dérivée doit préserver le knowledge historique, référencer evidence `PASS` admise et vérifier HMAC seulement lorsque la policy le requiert. |
| Statut | `READY_FOR_TESTS_FIRST` — aucune migration ou promotion n’est encore implémentée. |


### LOG-0066 — Verdict M3.5 : preuve dérivée PROVEN

| Champ | Valeur |
|---|---|
| Résultat | Migration 018 et `ProofService` : record immutable `PROVEN` lié à knowledge, evidence `PASS` et admission `ADMITTED`; le knowledge d’origine conserve son statut historique. |
| HMAC | Une policy de service peut exiger un secret HMAC; son absence échoue bruyamment. Le digest seul est persistant, jamais le secret. |
| Validation | Tests dédiés : 2 `PASS`; suite complète : 138 tests et 14 sous-tests `PASS`; diff et scan de périmètre `PASS`. |
| Verdict | `PASS` pour M3.5 technique; publication à finaliser. |


### LOG-0067 — Publication vérifiée M3.5

| Champ | Valeur |
|---|---|
| Commit | `7a91b80c9c800ae81755a196e81ed06012c576fc` — `feat: add derived knowledge proofs`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt propre et helper supprimé. |
| Statut | `PASS` pour la publication M3.5. Gates et work graph restent un lot distinct; la parité ARET demeure `UNKNOWN`. |


### LOG-0068 — Verdict M3.6 : Work Graph & Admission Gate

| Champ | Valeur |
|---|---|
| Résultat | Migration 019 et `GateService` : dépendance directe de work items append-only avec détection de cycle, gate immutable liée à une evidence, évaluation `FAIL` sans admission puis `PASS` avec décision `ADMITTED`. |
| Validation | Test dédié : 1 `PASS`; suite complète : 139 tests et 14 sous-tests `PASS`; diff et scan de périmètre `PASS`. |
| Limite | La gate lit des décisions existantes : elle n’exécute aucune capability, n’admet aucune evidence, ne modifie pas de knowledge et ne promulgue aucun état. |
| Verdict | `PASS` pour M3.6 technique; publication à finaliser. |


### LOG-0069 — Publication vérifiée M3.6

| Champ | Valeur |
|---|---|
| Commit | `63f4b028a3432e6308e78988ebf5faaa90d63537` — `feat: add work graph admission gates`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt propre et helper supprimé. |
| Statut | `PASS` pour la publication M3.6. La gate terminale M3 doit encore vérifier les migrations 001→019, la distribution isolée, les frontières de preuve et l’absence de régression ARET. |



### LOG-0070 — Gate `M3.S1.EXIT` : tranche opérationnelle minimale

| Champ | Valeur |
|---|---|
| Type | `RUN` / `COMPARISON` / `VERDICT` / `DECISION` |
| Périmètre admis | Migrations 015–019 : contrat fermé, runner `NOOP` sous `DENY_NETWORK`, execution immutable, evidence hashée, admission immutable, preuve dérivée sans réécriture de knowledge, dépendance directe et gate mono-evidence. |
| Contrôles | `tests/test_work_graph_gates.py` : 1 `PASS`; suite complète : 139 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan de `gates.py` sans processus, shell, réseau, I/O externe, insertion d’execution ni mutation knowledge/evidence `PASS`; wheel construit sans dépendance, installé hors source et vérifiant migrations 001→019 et les imports de services M3 `PASS`. |
| Comparaison | Le contrôle final conserve le contrat M2.EXIT et ajoute seulement M3.1–M3.6; aucun résultat `UNKNOWN` ou `SKIPPED` n’est requalifié. ARET demeure au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, arbre propre, sans test de parité nouvellement produit. |
| Preuve appliquée | Execution ≠ evidence; evidence `PASS` ≠ admission; une preuve dérivée exige evidence `PASS` + admission `ADMITTED`; le secret HMAC facultatif ne persiste pas; une gate lit uniquement l’admission existante. |
| Exclusions | Aucun runner externe, shell arbitraire, réseau implicite, validation typée complète de paramètres, policy `ALLOW`/`DENY`/`CONFIRM`, validator framework, policy HMAC de projet, gate multi-evidence, traversal/lifecycle, CLI/MCP ou pack ARET. |
| Décision de scope | La gate est nommée `M3.S1.EXIT` afin de valider cette tranche verticale finie sans déclarer **M3 global** complet. Les exclusions deviennent des futurs lots M3, chacun soumis à baseline, hypothèse, tests-first et gate propres. |
| Verdict | `PASS` pour **M3.S1**; `IN_PROGRESS` pour **M3 global**; `UNKNOWN` pour toute parité/exécution exhaustive ARET sous `MEM-WALL-001`. |
| Mémoire liée | `MEM-STATE-025`, `MEM-DEC-026`, `MEM-STATE-026`, `MEM-WALL-001`. |
| Suivi | Publier atomiquement la synchronisation de continuité; ouvrir ensuite un unique lot M3 manquant, sans mélanger refactoring ou fonctionnalité adjacente. |


### LOG-0071 — Publication vérifiée de `M3.S1.EXIT`

| Champ | Valeur |
|---|---|
| Commit | `47eb39f9c6f778b7183ec2471fa4c46af7e19470` — `docs: record M3 operational slice gate`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; arbre VERA propre et helper d’authentification supprimé. |
| Statut | `PASS` pour la publication de la gate `M3.S1.EXIT`. M3 global reste `IN_PROGRESS`; `MEM-WALL-001` maintient la parité ARET à `UNKNOWN`. |
| Suivi | Le prochain lot ne peut porter que sur une exclusion de `MEM-STATE-026`, avec baseline, hypothèse, tests-first et gate distinctes. |


### LOG-0072 — Hypothèse M3.7 : validation bornée des paramètres

| Champ | Valeur |
|---|---|
| Baseline | VERA `62f388e94e90d6ccfe382ba11db67a097f2a85c0`, `main` propre et alignée; 139 tests et 14 sous-tests `PASS`; `M3.S1.EXIT` publié. ARET reste propre à `7f7b4df…`; parité exhaustive `UNKNOWN` sous `MEM-WALL-001`. |
| Écart | Le contrat M3.1 persiste un objet JSON `parameter_schema`, mais `run_noop` vérifie seulement que les paramètres sont un `Mapping`. Il faut rejeter tôt les schémas et valeurs hors sous-ensemble admis, sans transformer ce contrôle en moteur de code ou runner. |
| Hypothèse | Un validateur local et déterministe, limité à un schéma d’objet avec `properties`, `required`, `additionalProperties` et types scalaires fermés, peut valider le schéma lors de sa déclaration puis valider les paramètres avant toute insertion d’execution. |
| Sûreté | Aucun `eval`, import dynamique, callback, accès fichier, processus, shell, réseau, artefact, validator externe, policy nouvelle ni capability additionnelle. Les schémas non supportés et paramètres invalides échouent bruyamment; le contrat et les executions historiques ne sont jamais réécrits. |
| Tests-first attendus | Rejet de schema root/type/propriété/required/additionalProperties invalides; acceptation de scalaires valides; refus de clé inconnue, clé requise absente, type erroné et booléen à la place d’un entier; absence d’insertion/audit d’execution au refus. |
| Invariants | I001, I004, I006–I008, I011, I013–I015. |
| Verdict | `PENDING` — aucun patch M3.7 n’est encore produit. |


### LOG-0073 — Verdict M3.7 : validation bornée des paramètres

| Champ | Valeur |
|---|---|
| Résultat | `parameter_validation.py` définit un sous-ensemble local et fermé : racine `object`, `properties`, `required`, `additionalProperties` et propriétés scalaires `string`, `integer`, `number`, `boolean` ou `null`. La déclaration rejette tout schéma hors contrat; `run_noop` relit et valide ce schéma avant l’insertion d’execution. |
| Validation | Tests-first : 2 échecs attendus avant patch; test ciblé : 4 `PASS`; suite complète : 141 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan sans processus, shell, réseau, I/O, `eval`, import dynamique, mutation knowledge/evidence ni nouvelle insertion d’execution `PASS`; wheel isolé construit/installé et scénario validé/refusé `PASS`. |
| Atomicité | Un paramètre requis absent, non déclaré ou de type incompatible — notamment `bool` pour `integer` — lève une erreur avant insertion d’execution et sans audit additionnel. |
| Limite | Cette validation n’implémente ni JSON Schema général, ni `enum`, array, object imbriqué, callback, validator externe, policy `ALLOW`/`DENY`/`CONFIRM`, runner additionnel, réseau, artefact ou gate nouvelle. |
| Verdict | `PASS` pour M3.7 technique; publication et synchronisation de continuité à finaliser. |


### LOG-0074 — Publication vérifiée M3.7

| Champ | Valeur |
|---|---|
| Commit | `b85a791fbb66f6f1a657cbdafeeb02bdaa5374c4` — `feat: validate bounded capability parameters`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt VERA propre et helper d’authentification supprimé. |
| Statut | `PASS` pour la publication M3.7. M3 global reste `IN_PROGRESS`; la parité ARET reste `UNKNOWN` sous `MEM-WALL-001`. |
| Suivi | Cadrer séparément la policy explicite `ALLOW`/`DENY`/`CONFIRM`, sans modifier le runner `NOOP` ni rendre le réseau implicite. |


### LOG-0075 — Hypothèse M3.8 : policy d’exécution explicite

| Champ | Valeur |
|---|---|
| Baseline | VERA `9887564564ed4d0bf77927a2515d2c2ec655a7e3`, `main` propre et alignée; 141 tests et 14 sous-tests `PASS`; M3.7 publié. ARET reste propre à `7f7b4df…`; parité exhaustive `UNKNOWN` sous `MEM-WALL-001`. |
| Écart | Le contrat capability fixe actuellement le profil `NOOP` et `DENY_NETWORK`, mais aucune décision universelle `ALLOW`/`DENY`/`CONFIRM` n’est persistée ni exigée avant l’execution. I013 reste donc non matérialisé pour le runner. |
| Hypothèse | Une policy append-only liée à une capability existante, avec décision fermée, motif et audit, peut être déclarée une seule fois; `run_noop` doit exiger exclusivement une décision `ALLOW` avant toute validation de paramètres ou insertion d’execution. |
| Sûreté | `DENY` et `CONFIRM` refusent bruyamment et sans effet; l’absence de policy refuse aussi. Aucun mécanisme de confirmation interactive, runner additionnel, modification de contrat, shell, fichier, réseau, artefact, evidence, admission, HMAC ou preuve n’est ajouté. |
| Tests-first attendus | Migration/FK/enum/immutabilité/audit/rollback; lecture exacte; refus absence/`DENY`/`CONFIRM`; `ALLOW` seul permet le `NOOP`; aucun refus ne crée execution ou audit de runner. |
| Invariants | I001, I004, I006–I008, I011, I013–I015. |
| Verdict | `PENDING` — aucun patch M3.8 n’est encore produit. |


### LOG-0076 — Verdict M3.8 : policy d’exécution explicite

| Champ | Valeur |
|---|---|
| Résultat | Migration 020 et `CapabilityPolicyService` : une policy immutable par capability, avec décision fermée `ALLOW`/`DENY`/`CONFIRM`, motif et audit. `run_noop` exige désormais une policy `ALLOW` après vérification de son contrat fermé et avant validation des paramètres ou insertion d’execution. |
| Validation | Tests-first : import absent attendu; tests ciblés : 14 `PASS`; suite complète : 143 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan sans processus, shell, réseau, I/O, `eval`, import dynamique, mutation de policy/knowledge/evidence ni nouvelle insertion d’execution `PASS`; wheel isolé avec migration 020, `ALLOW` accepté et `DENY` refusé `PASS`. |
| Atomicité | L’absence de policy, `DENY` ou `CONFIRM` lève une erreur avant validation des paramètres, insertion d’execution et audit de runner. Seule la déclaration de policy elle-même produit son audit append-only. |
| Limite | `CONFIRM` reste un refus explicite : aucun protocole de confirmation interactive, override temporaire, expiration, changement de décision, runner additionnel, réseau, artefact, evidence ou promotion n’est ajouté. |
| Verdict | `PASS` pour M3.8 technique; publication et synchronisation de continuité à finaliser. |


### LOG-0077 — Publication vérifiée M3.8

| Champ | Valeur |
|---|---|
| Commit | `53515175156846a68496d3a952a9fbe04d47c7c2` — `feat: add explicit capability policies`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt VERA propre et helper d’authentification supprimé. |
| Statut | `PASS` pour la publication M3.8. M3 global reste `IN_PROGRESS`; la parité ARET reste `UNKNOWN` sous `MEM-WALL-001`. |
| Suivi | Cadrer séparément un framework de validators fermé, sans exécution d’oracle ARET, runner additionnel ni réseau implicite. |


### LOG-0078 — Hypothèse M3.9 : policy HMAC de projet

| Champ | Valeur |
|---|---|
| Baseline | VERA `ae80ea9380968e99baa7e73327f1353d0d165010`, `main` propre et alignée; 143 tests et 14 sous-tests `PASS`; M3.8 publié. ARET reste propre à `7f7b4df…`; parité exhaustive `UNKNOWN` sous `MEM-WALL-001`. |
| Écart | `ProofService` reçoit encore `hmac_required` comme configuration du processus. La règle est locale mais non déclarée au niveau du projet, ce qui n’établit ni policy persistante ni fail-loud lorsque le projet n’a pas de règle. |
| Hypothèse | Une policy de projet singleton, append-only, déclarant seulement `HMAC_SHA256` et `hmac_required`, peut être persistée sans secret. `ProofService` doit exiger cette policy avant une preuve; si HMAC est requis, seul un secret bytes fourni en mémoire est accepté et seul le digest est persisté. |
| Sûreté | Aucun secret, encodage de secret, hint, longueur ou valeur de secret ne doit être écrit dans SQLite, audit, retour, erreur ou document. Absence de policy, secret manquant si requis, ou secret fourni quand non requis échouent bruyamment. Aucun runner, réseau, shell, evidence, admission ou knowledge n’est modifié. |
| Tests-first attendus | Migration singleton/immutabilité/audit/rollback; lecture exacte; refus sans policy; policy non-HMAC refusée; HMAC requis sans secret refusé; HMAC requis avec secret produit seulement un digest; HMAC non requis refuse un secret; knowledge historique inchangée. |
| Invariants | I001, I003–I008, I011, I013–I015. |
| Verdict | `PENDING` — aucun patch M3.9 n’est encore produit. |


### LOG-0079 — Verdict M3.9 : policy HMAC de projet

| Champ | Valeur |
|---|---|
| Résultat | Migration 021 et `ProofPolicyService` : policy singleton immutable `HMAC_SHA256` avec `hmac_required`, sans champ de secret. `ProofService` exige cette policy avant une preuve dérivée; secret bytes en mémoire seulement si requis, digest SHA-256 seul persistant. |
| Validation | Tests-first : import absent attendu; tests ciblés : 5 `PASS`; suite complète : 146 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan sans processus, shell, réseau, I/O, `eval`, import dynamique, persistance/audit/retour de secret ni mutation knowledge/evidence `PASS`; wheel isolé avec migration 021, refus sans secret et preuve HMAC valide `PASS`. |
| Atomicité | L’absence de policy, un secret manquant lorsque requis, ou un secret fourni lorsque non requis échouent avant insertion de `knowledge_proof` et audit de preuve. Le knowledge historique reste inchangé. |
| Limite | La policy ne gère ni rotation/révocation de secret, ni expiration, ni plusieurs algorithmes, ni plusieurs policies de projet, ni validator, runner, réseau, artefact ou gate nouvelle. |
| Verdict | `PASS` pour M3.9 technique; publication et synchronisation de continuité à finaliser. |


### LOG-0080 — Publication vérifiée M3.9

| Champ | Valeur |
|---|---|
| Commit | `492821da74c5b37519f234cd76fa2272e24fde55` — `feat: add project proof hmac policy`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt VERA propre et helper d’authentification supprimé. |
| Statut | `PASS` pour la publication M3.9. M3 global reste `IN_PROGRESS`; la parité ARET reste `UNKNOWN` sous `MEM-WALL-001`. |
| Suivi | Cadrer séparément un framework de validators fermé, sans oracle ARET, runner additionnel, réseau implicite ni exécution de commande. |


### LOG-0081 — Hypothèse M3.10 : validator d’intégrité `EVIDENCE_HASH`

| Champ | Valeur |
|---|---|
| Baseline | VERA `c37f6438b85e9e7a4a6aeee0dc11c2212d40e65e`, `main` propre et alignée; 146 tests et 14 sous-tests `PASS`; M3.9 publié. ARET reste propre à `7f7b4df…`; parité exhaustive `UNKNOWN` sous `MEM-WALL-001`. |
| Écart | Une evidence enregistre un `content_hash`, mais sa lecture ne revalide pas ce hash. Aucun résultat de validation persistent ne distingue actuellement l’intégrité locale vérifiée d’un simple champ stocké. |
| Hypothèse | Un registre fermé de validators limité à `EVIDENCE_HASH` et un résultat append-only lié à une evidence peuvent recalculer localement SHA-256 du JSON canonique et produire uniquement `PASS` ou `FAIL`, sans exécuter de command, lire de fichier, contacter de réseau ou admettre l’evidence. |
| Sûreté | Aucun oracle, runner, subprocessus, shell, URL, path, artefact, admission, gate, HMAC, mutation de knowledge/evidence ni promotion `PROVEN`. Un résultat `PASS` de validator n’est pas une admission et ne suffit pas à promouvoir une preuve. |
| Tests-first attendus | Migration/FK/enum/immutabilité/audit/rollback; validator inconnu refusé; evidence intacte `PASS`; contenu/hash altéré `FAIL`; résultat unique par validator/evidence; refus sans audit de runner ni modification d’evidence. |
| Invariants | I001, I004–I008, I011, I013–I015. |
| Verdict | `PENDING` — aucun patch M3.10 n’est encore produit. |


### LOG-0082 — Verdict M3.10 : validator d’intégrité `EVIDENCE_HASH`

| Champ | Valeur |
|---|---|
| Résultat | Migration 022 et `ValidatorService` : registre immutable limité à `EVIDENCE_HASH`, lecture exacte et résultat `PASS`/`FAIL` append-only lié à une evidence. La validation recalcule SHA-256 du JSON canonique et ne modifie ni evidence, ni admission, ni knowledge. |
| Validation | Tests-first : import absent attendu; tests ciblés : 2 `PASS`; suite complète : 148 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan sans processus, shell, réseau, I/O, `eval`, import dynamique, mutation de validator/result/knowledge/evidence ni nouvelle insertion d’execution `PASS`; wheel isolé avec migration 022, evidence intacte `PASS`, evidence altérée `FAIL` et admission inchangée `PASS`. |
| Atomicité | Validator ou evidence inconnus refusent avant insertion et audit de résultat. La contrainte unique `(validator_id, evidence_id)` interdit une seconde validation ambiguë; un `FAIL` est un fait append-only, pas une admission ou une promotion. |
| Limite | Seul `EVIDENCE_HASH` local est livré. Aucun oracle externe, validator de contenu métier, runner, source de fichier, URL, réseau, admission automatique, gate multi-evidence ou exécution ARET n’est ajouté. |
| Verdict | `PASS` pour M3.10 technique; publication et synchronisation de continuité à finaliser. |


### LOG-0083 — Publication vérifiée M3.10

| Champ | Valeur |
|---|---|
| Commit | `71911de01b025b8ea3011ffb120ed58f8a6f24d0` — `feat: add evidence hash validator`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt VERA propre et helper d’authentification supprimé. |
| Statut | `PASS` pour la publication M3.10. M3 global reste `IN_PROGRESS`; la parité ARET reste `UNKNOWN` sous `MEM-WALL-001`. |
| Suivi | Cadrer séparément une gate multi-evidence ou un validator de contenu explicitement borné, sans oracle ARET, runner additionnel, réseau implicite ni exécution de commande. |


### LOG-0084 — Hypothèse M3.11 : gates d’admission multi-evidence

| Champ | Valeur |
|---|---|
| Baseline | VERA `8a88249a510583a04c69547698eb69a67948c93f`, `main` propre et alignée; 148 tests et 14 sous-tests `PASS`; M3.10 publié. ARET reste propre à `7f7b4df…`; parité exhaustive `UNKNOWN` sous `MEM-WALL-001`. |
| Écart | Une `admission_gate` publie actuellement une evidence principale unique. La gate lit l’admission de cette seule evidence, sans pouvoir exprimer qu’un ensemble fixe d’evidences doit être admis. |
| Hypothèse | Une table append-only d’exigences additionnelles liée à une gate existante peut compléter son evidence principale. L’évaluation reste pure et retourne `PASS` seulement si l’evidence principale et toutes les exigences additionnelles ont une admission existante `ADMITTED`. |
| Sûreté | L’ajout d’exigence ne lance aucune capability, ne crée ni evidence ni admission, ne modifie aucun work item ou knowledge et ne fait pas d’une gate un lifecycle. Absence, `REJECTED`, `PENDING`, `FAIL`, `UNKNOWN` ou `SKIPPED` reste `FAIL`. |
| Tests-first attendus | Migration/FK/immutabilité/audit/rollback; exigence liée à gate/evidence existantes; lecture `FAIL` tant que l’une manque puis `PASS` quand toutes sont admises; refus doublon/primaire; évaluation sans effet. |
| Invariants | I001, I004–I008, I011, I013–I015. |
| Verdict | `PENDING` — aucun patch M3.11 n’est encore produit. |


### LOG-0085 — Verdict M3.11 : gate multi-evidence

| Champ | Valeur |
|---|---|
| Résultat | Migration 023 ajoute des exigences additionnelles append-only pour une gate existante. `GateService.add_requirement` les lie à des evidences existantes; `evaluate` reste une lecture pure et retourne `PASS` seulement lorsque l’evidence principale et chaque exigence ont une admission `ADMITTED`. |
| Validation | Tests-first : méthode absente attendue; tests ciblés : 2 `PASS`; suite complète : 149 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan sans processus, shell, réseau, I/O, `eval`, import dynamique, insertion d’execution ni mutation work item/knowledge/evidence `PASS`; wheel isolé avec migration 023, séquence `FAIL` → `FAIL` → `PASS` selon les admissions `PASS`. |
| Atomicité | Gate ou evidence inconnue, exigence dupliquée ou evidence principale répétée refusent avant l’audit d’ajout. L’évaluation n’écrit ni audit, ni execution, ni evidence, ni admission, ni knowledge. |
| Limite | Les exigences sont une conjonction fixe. Aucun quorum, disjonction, pondération, ordre, expiration, lifecycle de work item, admission automatique, validator externe, runner, réseau ou shell n’est ajouté. |
| Verdict | `PASS` pour M3.11 technique; publication et synchronisation de continuité à finaliser. |


### LOG-0086 — Publication vérifiée M3.11

| Champ | Valeur |
|---|---|
| Commit | `a97fd8212cd0461d1d60d846927fd0c81a966c58` — `feat: add multi-evidence admission gates`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt VERA propre et helper d’authentification supprimé. |
| Statut | `PASS` pour la publication M3.11. M3 global reste `IN_PROGRESS`; la parité ARET reste `UNKNOWN` sous `MEM-WALL-001`. |
| Suivi | Cadrer séparément un lifecycle de work item minimal ou un validator de contenu explicitement borné, sans oracle ARET, runner additionnel, réseau implicite ni exécution de commande. |


### LOG-0087 — Hypothèse M3.12 : lifecycle dérivé de work item

| Champ | Valeur |
|---|---|
| Baseline | VERA `b8b7b22631212600f4fb5019f78d5fd1828d2751`, `main` propre et alignée; 149 tests et 14 sous-tests `PASS`; M3.11 publié. ARET reste propre à `7f7b4df…`; parité exhaustive `UNKNOWN` sous `MEM-WALL-001`. |
| Écart | Le registre `work_item` conserve volontairement `PLANNED` de manière immutable. Les dépendances et gates n’établissent aucun état de travail visible ou historique pour une activité démarrée, terminée ou annulée. |
| Hypothèse | Des événements append-only `START`, `COMPLETE` et `CANCEL`, avec séquence calculée par work item, peuvent dériver un état `PLANNED`/`ACTIVE`/`COMPLETED`/`CANCELLED` sans jamais modifier `work_item`. Les transitions admises sont fermées : `PLANNED→ACTIVE`, `ACTIVE→COMPLETED`, `PLANNED|ACTIVE→CANCELLED`. |
| Sûreté | Aucun événement ne lance de capability, n’admet d’evidence, ne crée de preuve, ne modifie une gate, knowledge, evidence, execution ou work item. Une complétion est un état de travail dérivé, jamais une promotion `PROVEN` ou un résultat de gate implicite. |
| Tests-first attendus | Migration/FK/enum/séquence/immutabilité/audit/rollback; état initial `PLANNED`; transitions admises; refus de transition inverse/terminale; historique exact; work item historique reste `PLANNED`; lecture sans effet. |
| Invariants | I001, I004–I008, I011, I013–I015. |
| Verdict | `PENDING` — aucun patch M3.12 n’est encore produit. |


### LOG-0088 — Verdict M3.12 : lifecycle dérivé de work item

| Champ | Valeur |
|---|---|
| Résultat | Migration 024 et `WorkLifecycleService` ajoutent des événements append-only `START`/`COMPLETE`/`CANCEL` séquencés par work item. L’état `PLANNED`/`ACTIVE`/`COMPLETED`/`CANCELLED` est calculé à la lecture; le `work_item.status` historique reste `PLANNED`. |
| Validation | Tests-first : import absent attendu; tests ciblés : 2 `PASS`; suite complète : 151 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan sans processus, shell, réseau, I/O, `eval`, import dynamique, insertion d’execution ni mutation work item/knowledge/evidence `PASS`; wheel isolé avec migration 024, transitions valides, refus terminal et work item inchangé `PASS`. |
| Atomicité | Work item inconnu, événement hors catalogue ou transition interdite refusent avant insertion et audit. Les séquences sont uniques par work item; état et historique sont des lectures sans effet. |
| Limite | Le lifecycle ne requiert aucune gate, ne gère ni pause/reprise, réouverture, échéance, assignation, propagation parent/enfant, ordre de dépendance, exécution ou preuve. Une complétion n’est pas `PROVEN`. |
| Verdict | `PASS` pour M3.12 technique; publication et synchronisation de continuité à finaliser. |


### LOG-0089 — Publication vérifiée M3.12

| Champ | Valeur |
|---|---|
| Commit | `86f9ccbdfe7b1435ca6305fdf2f8dc943f96a40c` — `feat: add derived work lifecycle`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt VERA propre et helper d’authentification supprimé. |
| Statut | `PASS` pour la publication M3.12. M3 global reste `IN_PROGRESS`; la parité ARET reste `UNKNOWN` sous `MEM-WALL-001`. |
| Suivi | Définir une gate de tranche M3 supplémentaire et bornée, distinguant les primitives livrées des validators métier, runners sûrs, CLI/MCP et compatibilité ARET encore absents. |


### LOG-0090 — Gate M3.S2 : slice de sûreté policy, validation, gate et lifecycle

| Champ | Valeur |
|---|---|
| Périmètre fermé | M3.7–M3.12 seulement : paramètres fermés, policy `ALLOW`/`DENY`/`CONFIRM`, policy HMAC singleton sans secret persistant, `EVIDENCE_HASH`, gate conjonctive multi-evidence et lifecycle dérivé. Le seul runner demeure `NOOP` sous `DENY_NETWORK`. |
| Gate intégrée | Wheel isolé, migrations 001→024, profil neuf, refus atomique de paramètre requis absent, policy `ALLOW`, execution NOOP, deux evidences `PASS`, validator local, gate `FAIL` puis `PASS` après les deux admissions, preuve dérivée HMAC sans mutation de knowledge, lifecycle `START`→`COMPLETE` sans mutation de `work_item.status`. |
| Contrôles | Suite complète : 151 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan des modules M3.7–M3.12 sans processus, shell, réseau, I/O, `eval`, import dynamique `PASS`; VERA et ARET propres. |
| Verdict | `M3.S2.EXIT = PASS` pour la tranche livrée. Ce verdict ne ferme pas M3 global, ne déclare aucune parité ARET et ne transforme pas `MEM-WALL-001` en `PASS`. |
| Exclusions structurantes | Pas de runner externe sûr, validator métier/externe, JSON Schema général, confirmation interactive, rotation HMAC, quorum/disjonction, orchestration/réouverture de lifecycle, traversal de graph, CLI/MCP de production, pack ARET ou parité ARET. |


### LOG-0091 — Publication vérifiée M3.S2

| Champ | Valeur |
|---|---|
| Commit | `fa8d07bc9e5b88822fae21551e87d35a87d4c3bd` — `docs: record M3 S2 exit gate`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt VERA propre et helper d’authentification supprimé. |
| Statut | `PASS` pour la publication de `M3.S2.EXIT`. M3 global reste `IN_PROGRESS`; la parité ARET reste `UNKNOWN` sous `MEM-WALL-001`. |
| Suivi | Aucun lot supplémentaire ne peut étendre implicitement le périmètre M3.S2. Cadrer un nouveau lot et une nouvelle gate de tranche avant toute capacité de runner ou validator supplémentaire. |


### LOG-0092 — Hypothèse M3.13 : policy d’admission validée

| Champ | Valeur |
|---|---|
| Baseline | VERA `1bc5d88b0ac4f6d40b74ed17a1a9467c711bd1f6`, `main` propre et alignée; 151 tests et 14 sous-tests `PASS`; M3.S2 publié. ARET reste propre à `7f7b4df…`; parité exhaustive `UNKNOWN` sous `MEM-WALL-001`. |
| Écart | `AdmissionService` exige une evidence `PASS`, mais l’admission ne peut pas être explicitement rendue dépendante d’un résultat de validator persistant. `ValidatorService` reste donc une primitive distincte sans policy d’enforcement d’admission. |
| Hypothèse | Une policy singleton immutable fermée peut déclarer `PASS_EVIDENCE` ou `VALIDATED_PASS_EVIDENCE`. Lorsque le mode strict est déclaré, `ADMITTED` exige une evidence `PASS` et au moins un résultat de validator préexistant `PASS`; elle ne déclenche aucun validator. |
| Sûreté | La policy ne crée ni execution, evidence, résultat de validator, admission, preuve ou knowledge. Un résultat `FAIL`, l’absence de validation, `UNKNOWN`, `SKIPPED` ou toute valeur non prévue refuse `ADMITTED` en mode strict. `REJECTED` reste autorisé comme décision d’admission diagnostique. |
| Tests-first attendus | Migration singleton/enum/immutabilité/audit/rollback; mode compatible `PASS_EVIDENCE`; mode strict refusant avant toute écriture sans validation `PASS`, puis admission après validation `PASS`; lecture pure; secret, runner, réseau et shell absents. |
| Invariants | I001, I004–I008, I011, I013–I015. |
| Verdict | `PENDING` — aucun patch M3.13 n’est encore produit. |


### LOG-0093 — Verdict M3.13 : policy d’admission validée

| Champ | Valeur |
|---|---|
| Résultat | Migration 025 ajoute une policy singleton immutable `PASS_EVIDENCE`/`VALIDATED_PASS_EVIDENCE`. En mode strict, `AdmissionService` exige une evidence `PASS` et un résultat de validator `PASS` préexistant avant l’insertion `ADMITTED`; il ne déclenche aucune validation. |
| Validation | Tests-first : import absent attendu; tests ciblés : 3 `PASS`; chaînes admission/preuve/gates : 12 `PASS`; suite complète : 154 tests et 14 sous-tests `PASS`; `git diff --check` `PASS`; scan du patch sans processus, shell, réseau, I/O, `eval`, import dynamique, exécution, evidence, validation ou preuve implicites `PASS`; wheel isolé avec migration 025, refus strict sans validation puis admission après `EVIDENCE_HASH` `PASS`. |
| Atomicité | Evidence inconnue, evidence non `PASS`, policy absente et validation manquante en mode strict refusent avant insertion/audit d’admission. `REJECTED` reste une décision diagnostique possible sans validation. |
| Limite | Seul le validator local existant peut actuellement fournir un résultat `PASS`. Aucun oracle externe, validator métier, runner, réseau, shell, admission automatique, nouvelle preuve, modification d’evidence ou rotation de policy n’est ajouté. |
| Verdict | `PASS` pour M3.13 technique; publication et synchronisation de continuité à finaliser. |


### LOG-0094 — Publication vérifiée M3.13

| Champ | Valeur |
|---|---|
| Commit | `448693681b3fc4d2ccff39195d62c4d8598fb363` — `feat: add validated admission policy`. |
| Publication | `git push origin main` et `git ls-remote` confirment le commit; dépôt VERA propre et helper d’authentification supprimé. |
| Statut | `PASS` pour la publication M3.13. M3 global reste `IN_PROGRESS`; la parité ARET reste `UNKNOWN` sous `MEM-WALL-001`. |
| Suivi | Cadrer séparément un validator de contenu explicitement borné ou un runner sûr additionnel, avec une nouvelle gate de tranche; ne pas étendre implicitement M3.S2 ni réutiliser un résultat local comme oracle métier. |


### LOG-0095 — Hypothèse M3.14 : runner local `EVIDENCE_HASH`

| Champ | Valeur |
|---|---|
| Baseline | VERA `1e46c043085222e0e8cdbe2e32fbf03f4cf27a25`, `main` propre et alignée; 154 tests et 14 sous-tests `PASS`; M3.13 publié. ARET reste propre à `7f7b4df…`; parité exhaustive `UNKNOWN` sous `MEM-WALL-001`. |
| Écart | Le seul runner est `NOOP`; `ValidatorService.validate` est local mais doit être appelé séparément. Aucune execution persistée ne décrit une validation locale ni ne la relie atomiquement à son résultat. |
| Hypothèse | Le catalogue fermé peut ajouter `EVIDENCE_HASH`, sous `DENY_NETWORK`, `ALLOW`, paramètres exacts `validator_id`/`evidence_id` et `yields_proof=false`. Son runner ne lance aucun processus : il exécute seulement la validation hash locale et persiste, dans une transaction unique, une execution complétée avec résultat et le `validation_result` associé. |
| Sûreté | Aucun shell, sous-processus, fichier, réseau, URL, import dynamique, artefact, evidence, admission, proof ou knowledge n’est créé ou modifié. Toute policy absente/non `ALLOW`, contrat impropre, paramètre non fermé, validator/evidence inconnu ou résultat déjà existant refuse sans execution ni audit. |
| Tests-first attendus | Contrat fermé par profile; refus atomiques; execution et résultat créés ensemble pour evidence intacte `PASS` ou altérée `FAIL`; trace de résultat; absence de promotion/admission/evidence; immutabilité; wheel isolé. |
| Invariants | I001, I004–I008, I011, I013–I015. |
| Verdict | `PENDING` — aucun patch M3.14 n’est encore produit. |


### LOG-0096 — Verdict M3.14 : runner local fermé `EVIDENCE_HASH`

| Champ | Valeur |
|---|---|
| Portée livrée | Migration `026_evidence_hash_runner.sql` reconstruit uniquement `capability_contract` pour ajouter le catalogue SQL fermé `NOOP` / `EVIDENCE_HASH`, recopie les contrats historiques et recrée les triggers append-only. Le runner `ExecutionService.run_evidence_hash` exige exactement `EVIDENCE_HASH` / `DENY_NETWORK` / `yields_proof=false`, une policy capability `ALLOW` et le schéma fermé `validator_id` / `evidence_id`. |
| Transaction | Le runner appelle la validation hash locale via le helper transactionnel puis persiste une execution `COMPLETED`, son résultat JSON et les audits `VALIDATION_RECORDED` puis `EXECUTION_RECORDED` dans une seule transaction. Un validator/evidence inconnu, un schéma impropre, une policy non `ALLOW` ou une validation dupliquée laisse zéro nouvelle execution, validation ou audit. |
| Résultats observés | Evidence intacte : validation `PASS`, execution `COMPLETED`, résultat JSON persistant. Altération contrôlée du `content_hash` : validation `FAIL` avec execution locale toujours `COMPLETED`; ce verdict ne crée ni admission ni preuve. Upgrade historique réel `025→026` validé avec contrat `NOOP` conservé et nouveau contrat `EVIDENCE_HASH` accepté. |
| Gates exécutées | Tests ciblés : `10 passed`; suite complète : `159 passed, 14 subtests passed`; `git diff --check` passe. Scan du patch : absence de shell, sous-processus, accès fichier/réseau, URL, import dynamique, `eval`/`exec`, création d’evidence/admission/preuve et dépendance ARET. Wheel sans dépendances installée dans une cible externe : parcours `PASS` / `FAIL` sans admission ni preuve. |
| Limites préservées | Aucun shell, processus, filesystem, réseau, oracle externe, artefact, promotion de knowledge, admission ou preuve n’est introduit. Le runner est une execution locale de validation d’intégrité, non un oracle de contenu ni une admission implicite. `yields_proof` reste `false`. |
| Verdict | `PASS` pour M3.14. M3 global reste `IN_PROGRESS`; `C06` reste `SPLIT`, `C07` reste `BLOCKED` sous `MEM-WALL-001`, et la parité exhaustive ARET reste `UNKNOWN`. |
| Suite | Publier atomiquement ce lot; le lot suivant doit rester distinct et borné parmi validator de contenu/oracle explicitement cadré, runner sûr additionnel, politiques/gates avancées ou surface CLI/MCP. |


### LOG-0097 — Publication et handoff M3.14

| Champ | Valeur |
|---|---|
| Commit publié | `703d7a234a83066457402baf0efef76976473e35` — `feat: add evidence hash validation runner`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `703d7a234a83066457402baf0efef76976473e35`. |
| État de reprise | M3.14 est publié avec migration 026. M3 reste `IN_PROGRESS`; conserver `MEM-WALL-001`, C06 `SPLIT`, C07 `BLOCKED` et parité ARET `UNKNOWN`. |
| Prochain choix | Choisir explicitement un seul gap M3 borné; candidats : validator de contenu/oracle sous policy distincte, runner sûr additionnel, politiques/gates avancées ou surface CLI/MCP. Ne pas étendre implicitement le runner `EVIDENCE_HASH`. |


### LOG-0098 — Verdict M3.15 : policies de gate `ALL` / `ANY` / `AT_LEAST`

| Champ | Valeur |
|---|---|
| Portée livrée | Migration `027_admission_gate_policies.sql` ajoute une policy immutable par gate avec catalogue SQL fermé `ALL`, `ANY` et `AT_LEAST`. La policy est optionnelle : toute gate historique sans policy conserve exactement la sémantique conjonctive `ALL`. |
| Contrat | `ALL` et `ANY` n’acceptent aucun seuil; `AT_LEAST` exige un entier positif ne dépassant pas le nombre d’evidences déjà requises. Après policy, les exigences sont gelées afin que le seuil et la population évaluée restent déterministes. |
| Évaluation | `GateService.evaluate` reste une lecture pure : il compte seulement les admissions `ADMITTED` existantes et retourne statut, mode, nombre admis, nombre requis et seuil effectif. Il ne lance aucune capability, ne crée aucune admission, evidence, proof, execution ni mutation de work item/knowledge. |
| Compatibilité | Upgrade historique réel `026→027` validé : une gate conjonctive historique est lue comme `ALL`, puis peut recevoir une policy explicite. Les gates conjonctives M3.11 restent couvertes sans régression. |
| Gates exécutées | Tests-first : 4 échecs attendus avant code. Tests ciblés : `7 passed`; suite complète : `164 passed, 14 subtests passed`; `git diff --check` passe. Scan du patch : absence de shell, sous-processus, accès fichier/réseau, URL, import dynamique, création de faits adjacents et dépendance ARET. Wheel isolée : `ALL` / `ANY` / `AT_LEAST` validés sur admissions préexistantes. |
| Limites préservées | Aucun quorum pondéré, expiration, fenêtre temporelle, désaveu/révocation d’admission, exécution implicite, admission automatique, oracle, réseau, shell, CLI/MCP ou parité ARET n’est introduit. |
| Verdict | `PASS` pour M3.15. M3 global reste `IN_PROGRESS`; C05/C06/C16 restent `SPLIT`, C07 reste `BLOCKED` sous `MEM-WALL-001`, et la parité exhaustive ARET reste `UNKNOWN`. |
| Suite | Publier atomiquement le lot. Le prochain lot doit être choisi explicitement parmi validators de contenu/oracles policy-gated, runners sûrs additionnels, gates temporelles/pondérées si cadrées, lifecycle/graph avancés ou surfaces CLI/MCP. |


### LOG-0099 — Publication et handoff M3.15

| Champ | Valeur |
|---|---|
| Commit publié | `c6a605278b2ad5aabdd13bb32e4f1dab725b4363` — `feat: add immutable admission gate policies`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `c6a605278b2ad5aabdd13bb32e4f1dab725b4363`. |
| État de reprise | M3.15 est publié avec migration 027. M3 reste `IN_PROGRESS`; conserver `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et parité ARET `UNKNOWN`. |
| Prochain choix | Choisir explicitement un seul gap M3 borné; candidats : validator de contenu/oracle sous policy distincte, runner sûr additionnel, extension temporelle/pondérée de gate, lifecycle/graph avancé ou surface CLI/MCP. Ne pas étendre implicitement les policies de gate actuelles. |


### LOG-0100 — Verdict M3.16 : readiness dérivée et policy de démarrage stricte

| Champ | Valeur |
|---|---|
| Portée livrée | Migration `028_work_start_policies.sql` ajoute une policy singleton immutable `OPEN` / `REQUIRE_READY`. `WorkReadinessService` dérive, en lecture seule, la readiness d’un work item depuis ses dépendances `COMPLETED` et ses gates `PASS` existantes. |
| Contrat | Sans policy ou avec `OPEN`, le lifecycle historique est inchangé. Sous `REQUIRE_READY`, seul l’événement `START` refuse lorsque dependencies ou gates ne sont pas satisfaites; `COMPLETE` et `CANCEL` ne sont pas réinterprétés. |
| Transaction | Le contrôle de readiness s’exécute dans la transaction de transition avant insertion/audit. Un démarrage bloqué ajoute zéro événement lifecycle et zéro audit. La readiness elle-même ne crée aucun record. |
| Compatibilité | Upgrade historique réel `027→028` validé : un work item antérieur est `READY` en l’absence de dépendance/gate et peut recevoir une policy stricte après migration. |
| Gates exécutées | Tests-first : erreur d’import attendue avant code. Tests ciblés : `8 passed`; suite complète : `168 passed, 14 subtests passed`; `git diff --check` passe. Scan du patch : absence de shell, sous-processus, accès fichier/réseau, URL, import dynamique, création de faits adjacents et dépendance ARET. Wheel isolée : refus strict, puis readiness après completion/admissions et `START` validés. |
| Limites préservées | Aucun scheduler, orchestration, mutation automatique de `work_item`, execution, validator, evidence, admission, preuve, oracle, réseau, shell, CLI/MCP ou parité ARET n’est introduit. `READY` est dérivé, non écrit comme état métier. |
| Verdict | `PASS` pour M3.16. M3 global reste `IN_PROGRESS`; C05/C06/C16 restent `SPLIT`, C07 reste `BLOCKED` sous `MEM-WALL-001`, et la parité exhaustive ARET reste `UNKNOWN`. |
| Suite | Publier atomiquement le lot. Le prochain lot doit rester distinct parmi lifecycle/graph avancé, validator de contenu/oracle policy-gated, runner sûr additionnel ou surface CLI/MCP. |


### LOG-0101 — Publication et handoff M3.16

| Champ | Valeur |
|---|---|
| Commit publié | `8ee7a7562ead8c1b2de6521b6dd17db47fb4cab9` — `feat: add strict work start readiness policy`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `8ee7a7562ead8c1b2de6521b6dd17db47fb4cab9`. |
| État de reprise | M3.16 est publié avec migration 028. M3 reste `IN_PROGRESS`; conserver `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et parité ARET `UNKNOWN`. |
| Prochain choix | Choisir explicitement un seul gap M3 borné : lifecycle/graph avancé, validator de contenu/oracle sous policy distincte, runner sûr additionnel ou surface CLI/MCP. Ne pas transformer readiness en scheduler ou orchestration implicite. |


### LOG-0102 — Verdict M3.17 : validator local `EVIDENCE_FIELDS`

| Champ | Valeur |
|---|---|
| Portée livrée | Migration `029_evidence_field_validators.sql` étend le catalogue de validators à `EVIDENCE_HASH` et `EVIDENCE_FIELDS`, avec règle JSON immutable de clés requises. |
| Contrat | `EVIDENCE_FIELDS` exige une liste non vide, unique et bornée de clés sans séparateur. Il produit `PASS` si toutes les clés existent dans le JSON d’evidence, sinon `FAIL`; il n’interprète pas la valeur métier et n’appelle aucun oracle. |
| Compatibilité | Les validators/résultats hash existants sont reconstruits avec leurs clés étrangères et règles `{}` conservées. |
| Gates | Tests-first : 2 échecs attendus. Tests ciblés : `4 passed`; suite complète : `170 passed, 14 subtests passed`; scan de frontières et `git diff --check` passent; wheel isolée valide `PASS`/`FAIL`. |
| Limites | Aucun réseau, shell, filesystem, oracle, admission, preuve, execution, mutation de knowledge ou promotion implicite. Ce n’est ni JSON Schema général ni validator de contenu métier. |
| Verdict | `PASS` pour M3.17. M3 reste `IN_PROGRESS`; C05/C06/C16 restent `SPLIT`, C07 `BLOCKED` sous `MEM-WALL-001`, parité ARET `UNKNOWN`. |


### LOG-0103 — Publication et handoff M3.17

| Champ | Valeur |
|---|---|
| Commit publié | `1429572c7cab5e406d27851a034c337d30625020` — `feat: add evidence field validator`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `1429572c7cab5e406d27851a034c337d30625020`. |
| État de reprise | M3.17 est publié avec migration 029. M3 reste `IN_PROGRESS`; conserver `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et parité ARET `UNKNOWN`. |
| Prochain choix | Choisir explicitement un seul gap M3 : validator/oracle métier sous policy distincte, runner sûr additionnel, lifecycle/graph avancé ou surface CLI/MCP. Ne pas étendre `EVIDENCE_FIELDS` en JSON Schema général ou oracle métier implicite. |


### LOG-0104 — Verdict M3.18 : runner local fermé `EVIDENCE_FIELDS`

| Champ | Valeur |
|---|---|
| Portée livrée | Migration `030_evidence_fields_runner.sql` étend le catalogue de contrats à `NOOP`, `EVIDENCE_HASH`, `EVIDENCE_FIELDS`. `ExecutionService.run_evidence_fields` exécute localement un validator de présence de clés. |
| Contrat | Profile exact `EVIDENCE_FIELDS`, `DENY_NETWORK`, `yields_proof=false`, policy capability `ALLOW`, schema exact `validator_id`/`evidence_id`. Le runner exige un validator `EVIDENCE_FIELDS` persistant. |
| Transaction | Validation `PASS`/`FAIL`, execution `COMPLETED` et audits sont atomiques. Un refus/duplicat rollbacke les écritures. Aucun admission, evidence, preuve, knowledge ou work item n’est créé/modifié. |
| Gates | Tests-first : échec attendu sans migration/runner. Tests ciblés : `6 passed`; suite complète : `171 passed, 14 subtests passed`; `git diff --check`, scan sans I/O/ARET et wheel isolée `PASS`/`FAIL` passent. |
| Limites | Aucun shell, processus, réseau, filesystem, oracle externe, JSON Schema général, admission automatique ou preuve implicite. Le runner ne juge que la présence de clés selon la règle du validator. |
| Verdict | `PASS` pour M3.18. M3 reste `IN_PROGRESS`; C05/C06/C16 restent `SPLIT`, C07 reste `BLOCKED` sous `MEM-WALL-001`, parité ARET `UNKNOWN`. |


### LOG-0105 — Publication et handoff M3.18

| Champ | Valeur |
|---|---|
| Commit publié | `708c318f319dbfae59f42e547143a41c08a8667d` — `feat: add evidence fields validation runner`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `708c318f319dbfae59f42e547143a41c08a8667d`. |
| État de reprise | M3.18 est publié avec migration 030. M3 reste `IN_PROGRESS`; conserver `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et parité ARET `UNKNOWN`. |
| Prochain choix | Choisir explicitement un seul gap M3 : validator/oracle métier sous policy distincte, runner sûr additionnel, lifecycle/graph avancé ou surface CLI/MCP. Ne pas étendre les deux runners locaux en exécution arbitraire. |


### LOG-0106 — Verdict M3.19 : diagnostic pur de dépendances bloquantes

| Champ | Valeur |
|---|---|
| Portée livrée | `WorkBlockerService.diagnose(work_item_id)` retourne les dépendances directes dont l’état dérivé n’est pas `COMPLETED`, avec identifiant et statut courant. |
| Sémantique | Le diagnostic est une lecture pure, déterministe et ordonnée. Il n’écrit ni audit, ni event lifecycle, ni work item, ni evidence/admission/preuve/execution. |
| Gates | Tests-first : erreur d’import attendue. Tests ciblés : `3 passed`; suite complète : `172 passed, 14 subtests passed`; scan sans I/O/écriture/ARET et wheel isolée passent. |
| Limites | Aucun traversal transitif, agrégation de gates, scheduler, orchestration, mutation automatique, oracle, réseau ou shell n’est introduit. |
| Verdict | `PASS` pour M3.19. M3 reste `IN_PROGRESS`; C05/C06/C16 restent `SPLIT`, C07 `BLOCKED` sous `MEM-WALL-001`, parité ARET `UNKNOWN`. |


### LOG-0107 — Publication et handoff M3.19

| Champ | Valeur |
|---|---|
| Commit publié | `af6fa4526f0fff74a18cd6a6810eadf9438fbfbd` — `feat: add pure work dependency blockers`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `af6fa4526f0fff74a18cd6a6810eadf9438fbfbd`. |
| État de reprise | M3.19 est publié. M3 reste `IN_PROGRESS`; conserver `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et parité ARET `UNKNOWN`. |
| Prochain choix | Choisir explicitement un seul gap M3 : traversal/graph avancé, validator/oracle métier sous policy distincte, runner sûr additionnel ou surface CLI/MCP. Ne pas faire du diagnostic un scheduler ou une orchestration. |


### LOG-0108 — Verdict M3.20 : diagnostic transitif de dépendances

| Champ | Valeur |
|---|---|
| Portée livrée | `WorkBlockerService.diagnose_transitive(work_item_id)` parcourt les dépendances transitives en ordre stable et retourne une seule fois chaque prérequis non `COMPLETED`. |
| Sémantique | Le parcours est une lecture pure : aucune écriture, audit, transition lifecycle, capability, execution, evidence, admission ou preuve. Les cycles restent refusés lors de la déclaration de dépendance existante. |
| Gates | Tests-first : méthode absente; tests ciblés : `4 passed`; suite complète : `173 passed, 14 subtests passed`; scan sans I/O/écriture/ARET et wheel isolée passent. |
| Limites | Aucun diagnostic de gates, pondération, fenêtrage temporel, scheduler, orchestration ou mutation automatique. |
| Verdict | `PASS` pour M3.20. M3 reste `IN_PROGRESS`; C05/C06/C16 restent `SPLIT`, C07 `BLOCKED` sous `MEM-WALL-001`, parité ARET `UNKNOWN`. |


### LOG-0109 — Publication et handoff M3.20

| Champ | Valeur |
|---|---|
| Commit publié | `35743f6feacbe77766883c428a5e1f6512e52179` — `feat: add transitive work dependency blockers`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `35743f6feacbe77766883c428a5e1f6512e52179`. |
| État de reprise | M3.20 est publié. M3 reste `IN_PROGRESS`; conserver `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et parité ARET `UNKNOWN`. |
| Prochain choix | Choisir explicitement un seul gap M3 : diagnostic de gates, lifecycle/graph avancé, validator/oracle métier sous policy distincte, runner sûr additionnel ou surface CLI/MCP. Ne pas faire du traversal une orchestration. |


### LOG-0110 — Verdict M3.21 : diagnostic de gates bloquantes

| Champ | Valeur |
|---|---|
| Portée livrée | `GateBlockerService.diagnose(work_item_id)` retourne les gates directes non `PASS`, avec identifiant, verdict et compteurs d’admissions/requirements. |
| Sémantique | Chaque verdict est lu par `GateService.evaluate` sur les admissions existantes. Le diagnostic n’écrit ni audit, lifecycle, work item, execution, evidence, admission ou preuve. |
| Gates | Tests-first : module absent; tests ciblés : `6 passed`; suite complète : `174 passed, 14 subtests passed`; scan sans I/O/écriture/ARET et wheel isolée passent. |
| Limites | Aucun traversal de gates, diagnostic composite dependency+gate, pondération/temporalité, scheduler, orchestration ou mutation automatique. |
| Verdict | `PASS` pour M3.21. M3 reste `IN_PROGRESS`; C05/C06/C16 restent `SPLIT`, C07 `BLOCKED` sous `MEM-WALL-001`, parité ARET `UNKNOWN`. |


### LOG-0111 — Publication et handoff M3.21

| Champ | Valeur |
|---|---|
| Commit publié | `b0cd1cc365091a6283bf6fd246b8d3a2c63b9bac` — `feat: add pure gate blockers`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `b0cd1cc365091a6283bf6fd246b8d3a2c63b9bac`. |
| État de reprise | M3.21 est publié. M3 reste `IN_PROGRESS`; conserver `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et parité ARET `UNKNOWN`. |
| Prochain choix | Choisir explicitement un seul gap M3 : diagnostic composite, graph/lifecycle avancé, validator/oracle métier sous policy distincte, runner sûr additionnel ou surface CLI/MCP. Ne pas rendre le diagnostic actif. |


### LOG-0112 — Approbation du contrat terminal M3.EXIT

| Champ | Valeur |
|---|---|
| Décision | L’utilisateur approuve l’enchaînement jusqu’à M3.EXIT et le périmètre fini M3.22–M3.25 + M3.EXIT. |
| Lots restants | M3.22 rapport composite de blockers ; M3.23 policy de complétion optionnelle ; M3.24 binding admission-validation ; M3.25 catalogue de compatibilité locale ; M3.EXIT audit cumulatif. |
| Limites conservées | Aucun shell, réseau, filesystem externe, oracle métier, runner générique, promotion implicite, parité ARET ou surface CLI/MCP n’est ajouté à M3. |
| Statut | Contrat approuvé et documenté ; M3 reste `IN_PROGRESS` jusqu’aux gates cumulatives M3.EXIT. |


### LOG-0113 — Verdict M3.22 : rapport composite de blockers

| Champ | Valeur |
|---|---|
| Portée livrée | `WorkBlockerReportService.diagnose(work_item_id)` compose les dépendances transitives non `COMPLETED` et les gates directes non `PASS`; le statut est `BLOCKED` si l’un des ensembles est non vide, sinon `READY`. |
| Sémantique | Le rapport délègue aux diagnostics publiés, conserve leurs ordres canoniques et n’écrit ni audit, lifecycle, work item, execution, evidence, admission ou preuve. |
| Gates | Tests-first : module absent; tests ciblés : `4 passed`; suite complète : `175 passed, 14 subtests passed`; scan sans I/O/écriture/ARET et wheel isolée passent. |
| Limites | Aucun scheduler, orchestration, traversal de gates, pondération/temporalité ou mutation automatique. |
| Verdict | `PASS` pour M3.22. M3 reste `IN_PROGRESS` jusqu’à M3.EXIT; C05/C06/C16 `SPLIT`, C07 `BLOCKED`, parité ARET `UNKNOWN`. |


### LOG-0114 — Publication et handoff M3.22

| Champ | Valeur |
|---|---|
| Commit publié | `8ff298d2af5c24930d8d6bc82139f1618221c8b7` — `feat: add composite work blocker report`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `8ff298d2af5c24930d8d6bc82139f1618221c8b7`. |
| État de reprise | M3.22 est publié. M3.23 est le lot suivant du contrat approuvé ; M3 reste `IN_PROGRESS` et les limites/parités inchangées. |


### LOG-0115 — Verdict M3.23 : policy de complétion optionnelle

| Champ | Valeur |
|---|---|
| Portée livrée | La migration `031_work_completion_policies.sql` et `WorkCompletionPolicyService` ajoutent une policy singleton immutable `OPEN` / `REQUIRE_READY_FOR_COMPLETE`. `WorkLifecycleService.transition` ne consulte cette policy que pour `COMPLETE`, après légalité de transition et avant insertion/audit. |
| Sémantique | Sans policy ou sous `OPEN`, la complétion historique demeure possible. Sous le mode strict, une readiness dérivée `BLOCKED` refuse `COMPLETE` avec rollback de l’événement et de l’audit; `START` conserve sa policy propre et `CANCEL` est inchangé. |
| Gates | Tests-first : module absent; tests ciblés : `5 passed`; suite complète : `180 passed, 14 subtests passed`; fresh install 031, upgrade historique 030→031, scans Core no-shell/no-network/no-filesystem/no-ARET/no-mutation hors périmètre et wheel isolée des chemins COMPLETE bloqué/prêt passent. |
| Limites | Aucun scheduler, complétion automatique, orchestration, execution, evidence, admission, preuve, oracle, réseau, shell ou accès filesystem externe. |
| Verdict | `PASS` pour M3.23. M3 reste `IN_PROGRESS` jusqu’à M3.EXIT; C05/C06/C16 `SPLIT`, C07 `BLOCKED` sous `MEM-WALL-001`, parité ARET `UNKNOWN`. |


### LOG-0116 — Publication et handoff M3.23

| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `e87a3b189f355fa5b6db815be73759a3eb0b0d15` — `feat: add optional work completion policy`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `e87a3b189f355fa5b6db815be73759a3eb0b0d15` avant le handoff documentaire. |
| État de reprise | M3.23 est fonctionnellement publié. M3.24 est le seul lot suivant autorisé par le contrat M3.EXIT; conserver les limites et états de parité existants. |


### LOG-0117 — Verdict M3.24 : binding admission-validation strict

| Champ | Valeur |
|---|---|
| Portée livrée | La migration `032_admission_validation_bindings.sql` ajoute `admission_validation_binding`, avec FKs, unicité et triggers append-only. En policy `VALIDATED_PASS_EVIDENCE`, `AdmissionService.decide` exige un `validation_id` explicite, `PASS` et de la même evidence, puis persiste admission et binding dans une transaction unique. |
| Sémantique | `PASS_EVIDENCE` reste compatible et sans binding. Le mode strict refuse validation absente, cross-evidence ou `FAIL` avant admission, binding et audit; aucune validation n’est déclenchée. |
| Gates | Tests-first : migration/API absentes; tests ciblés : `7 passed`; suite complète : `184 passed, 14 subtests passed`; fresh install 032, upgrade 031→032, FKs/unicité/immutabilité, scans Core no-shell/no-network/no-filesystem/no-ARET/no-mutation hors admission et wheel isolée passent. |
| Limites | Aucun validator, oracle, runner, admission automatique, execution, evidence, mutation de knowledge ou preuve automatique. |
| Verdict | `PASS` pour M3.24. M3 reste `IN_PROGRESS` jusqu’à M3.EXIT; C05/C06/C16 `SPLIT`, C07 `BLOCKED` sous `MEM-WALL-001`, parité ARET `UNKNOWN`. |


### LOG-0118 — Publication et handoff M3.24

| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `14fda1f972745eaada9b8f30806dedd7ac58fe43` — `feat: bind strict admissions to validations`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `14fda1f972745eaada9b8f30806dedd7ac58fe43` avant le handoff documentaire. |
| État de reprise | M3.24 est fonctionnellement publié. M3.25 est le seul lot suivant autorisé par le contrat M3.EXIT; conserver les limites et états de parité existants. |


### LOG-0119 — Verdict M3.25 : catalogue fermé runner-validator-schema

| Champ | Valeur |
|---|---|
| Portée livrée | `runner_validator_compatibility.py` ferme le catalogue aux paires `EVIDENCE_HASH`/`EVIDENCE_HASH` et `EVIDENCE_FIELDS`/`EVIDENCE_FIELDS`, sous un schéma exact `validator_id`/`evidence_id`. Les runners existants consultent ce catalogue avant toute validation/execution. |
| Sémantique | Les chemins valides conservent leurs verdicts `PASS`/`FAIL`. Les incompatibilités cross-kind, profil hors catalogue ou schéma différent échouent avant validation, execution et audit; aucune admission ni preuve n’est créée. |
| Gates | Tests-first : module absent; tests ciblés : `8 passed`; suite complète : `186 passed, 14 subtests passed`; matrice profile×validator×schema×policy, rollback, scans Core no-shell/no-network/no-filesystem/no-ARET/no-mutation et wheel isolée passent. |
| Limites | Aucun runner générique, JSON Schema général, oracle, fichier, réseau, shell, admission ou preuve automatique. |
| Verdict | `PASS` pour M3.25. Les lots fonctionnels M3.22–M3.25 sont `PASS`; M3 reste `IN_PROGRESS` jusqu’à la seule gate restante, M3.EXIT. C05/C06/C16 `SPLIT`, C07 `BLOCKED` sous `MEM-WALL-001`, parité ARET `UNKNOWN`. |


### LOG-0120 — Publication et handoff M3.25

| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `a67d0dd05102b1d14341bd299d9fc62ce6029e2e` — `feat: close runner validator compatibility`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `a67d0dd05102b1d14341bd299d9fc62ce6029e2e` avant le handoff documentaire. |
| État de reprise | M3.25 est fonctionnellement publié. M3.EXIT est la seule action M3 autorisée; ne pas introduire de lot ou extension supplémentaire. |


### LOG-0121 — Verdict terminal M3.EXIT : Core M3 borné

| Champ | Valeur |
|---|---|
| Périmètre audité | M3.1–M3.25 : contrats/policies/runners locaux fermés, evidence hashée, validators, admission liée, preuve dérivée, gates, diagnostics, readiness et lifecycle strictement dérivés. |
| Chaîne terminale | Store frais : capability → execution → evidence `PASS` → validation `PASS` → admission strictement liée → proof `PROVEN` sans réécriture de knowledge → gate → readiness → lifecycle `START`/`COMPLETE` sous policies strictes. |
| Gates cumulatives | Fresh install 032 et checksums 001→032; upgrade historique 001→032; `tests/test_m3_exit.py` : `2 passed`; suite complète : `188 passed, 14 subtests passed`; scans no-shell/no-network/no-filesystem/no-ARET/no-secret/no-rewrite knowledge; wheel isolée de la chaîne terminale : `PASS`. |
| Frontières vérifiées | Aucun shell, réseau, filesystem externe, runner générique, oracle métier, JSON Schema général, admission/proof automatique, CLI/MCP, dashboard, importeur/pack ARET ou orchestration n’est ajouté. |
| Verdict | `PASS` pour M3.EXIT et donc pour M3 dans son périmètre Core borné. C05/C06/C16 restent `SPLIT`; C07 reste `BLOCKED` sous `MEM-WALL-001`; parité ARET `UNKNOWN`; ARET-MMU reste intact à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |


### LOG-0122 — Publication et handoff M3.EXIT

| Champ | Valeur |
|---|---|
| Commit de preuve publié | `1d7b2efb6fdd914e58b8de7d3ff232de848c59a2` — `test: add M3 exit integration gate`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `1d7b2efb6fdd914e58b8de7d3ff232de848c59a2` avant le handoff documentaire terminal. |
| État de reprise | M3 est terminé dans le périmètre contractuel. Aucun nouveau lot M3 ne peut être créé; les évolutions postérieures sont reportées explicitement vers M4+ selon la roadmap. |


### LOG-0123 — Verdict M4.1 : lecteur ARET V1 strictement en lecture

| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.addressing` expose le parsing et la construction canoniques d’adresses `ARET://` V1 fermées : `knowledge`, `component`, `function`, `brick`, `proof`, `relation`, `asset`, `pipeline` et `front/current`. |
| Invariant | Le parser n’effectue aucune recherche, résolution de store, import, migration, traduction en `vera://`, écriture ou mutation. Il refuse schéma, type, identifiant, encodage ou forme non canonique. |
| Isolation | Le Core n’importe pas le pack; le pack n’importe ni store, SQLite, filesystem, réseau, shell ni toolchain ARET. ARET-MMU est resté propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : module absent; ciblé : `4 passed`; Core : `192 passed, 14 subtests passed`; `git diff --check`, scans de frontière et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.1 uniquement. C01 demeure `SPLIT`; aucune parité ARET ou migration de données n’est affirmée. M4 reste `IN_PROGRESS`. |


### LOG-0124 — Publication et handoff M4.1

| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `fc91a1c202cc507666c38535c11d3d40a0045aae` — `feat: add read-only ARET address pack`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `fc91a1c202cc507666c38535c11d3d40a0045aae` avant le handoff documentaire. |
| Reprise | Le prochain lot M4 doit être contractuellement borné contre la matrice de découplage; il ne peut pas inférer la parité ARET à partir de M4.1. |


### LOG-0125 — Verdict M4.2 : manifeste du runtime ARET V1

| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.runtime` déclare immuablement les conventions legacy : `ARET_MEMORY_DIR`, `.aret-memory`, `aret_memory.sqlite`, `artifacts` et `exports`. |
| Invariant | La surface ne lit pas l’environnement, ne résout ni ne crée de chemin, n’ouvre aucune SQLite, n’applique aucune migration et ne lit aucun secret. Elle est une donnée de pack, distincte du `RuntimeLocator` Core. |
| Isolation | Le Core n’importe pas le pack; le manifeste ne contient ni filesystem, store, SQLite, réseau, shell ni toolchain ARET. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : module absent; ciblé : `6 passed` avec M4.1; Core : `194 passed, 14 subtests passed`; `git diff --check`, scans de frontière et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.2 uniquement. C02 reste `SPLIT`; aucune résolution de runtime, compatibilité de store, WAL, doctor ou parité ARET n’est affirmée. M4 reste `IN_PROGRESS`. |


### LOG-0126 — Publication et handoff M4.2

| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `e023a12ab506c5ce44a1566f2b221e2aba88b8bc` — `feat: declare legacy ARET runtime layout`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `e023a12ab506c5ce44a1566f2b221e2aba88b8bc` avant le handoff documentaire. |
| Reprise | Le lot M4 suivant doit rester lié à un couplage de la matrice et séparer strictement description de layout, résolution de runtime et migration de données. |


### LOG-0127 — Verdict M4.3 : manifeste du schéma ARET V1 observé

| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.schema` déclare immuablement les migrations 001–006 et les dix-huit tables applicatives observées dans la base ARET V1, sans les tables FTS internes. |
| Invariant | Une inspection de baseline a été réalisée une fois en SQLite `mode=ro`; le code livré ne contient ni SQLite, ni chemin, ni ouverture de fichier, ni lecture de ligne, ni import. |
| Isolation | Le Core n’importe pas le pack; le manifeste ne contient ni filesystem, store, SQLite, réseau, shell ni toolchain ARET. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : module absent; ciblé : `8 passed` avec M4.1–M4.2; Core : `196 passed, 14 subtests passed`; `git diff --check`, scans de frontière et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.3 uniquement. Aucune compatibilité de données, import, mapping de schéma, proof/evidence, audit ou parité ARET n’est affirmée. M4 reste `IN_PROGRESS`. |


### LOG-0128 — Publication et handoff M4.3

| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `b98058c0365131ff4070a4d3c9c248a00a48d475` — `feat: declare observed ARET v1 schema`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `b98058c0365131ff4070a4d3c9c248a00a48d475` avant le handoff documentaire. |
| Reprise | Le lot M4 suivant doit traiter un seul mapping de compatibilité ou une policy de lecture sous contrat fermé; il ne peut pas importer une table complète ni déduire une équivalence ARET à partir d’un inventaire. |


### LOG-0129 — Verdict M4.4 : profil de compatibilité ARET V1 borné

| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.profile` expose le profil immutable `aret-v1-compatibility`, composé des manifestes M4.1–M4.3. Ses seules opérations déclarées sont `parse_address`, `describe_runtime` et `describe_schema`. |
| Invariant | Le profil déclare explicitement `resolve_runtime`, `read_sqlite`, `import_data` et `write_vera` comme interdits. Il ne lit ni n’écrit, ne devient pas un Project Profile VERA, ne lance aucune capacité et n’expose aucune API MCP. |
| Isolation | Le Core n’importe pas le pack; le profil ne contient ni filesystem, store, SQLite, réseau, shell ni toolchain ARET. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : module absent; ciblé : `10 passed` avec M4.1–M4.3; Core : `198 passed, 14 subtests passed`; `git diff --check`, scans de frontière et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.4 uniquement. Le profil est descriptif, non opérationnel; aucun import, mapping de données, pipeline, preuve, playbook, hook, toolchain ou parité ARET n’est affirmé. M4 reste `IN_PROGRESS`. |


### LOG-0130 — Publication et handoff M4.4

| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `c067ea0dfec94292de1e9f826512646a7fc7fe15` — `feat: add bounded ARET compatibility profile`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `c067ea0dfec94292de1e9f826512646a7fc7fe15` avant le handoff documentaire. |
| Reprise | Le lot M4 suivant doit poursuivre un seul couplage avec une policy et des mappings explicites; aucune opération déclarée interdite par M4.4 ne peut être introduite implicitement. |


### LOG-0131 — Verdict M4.5 : mappings structurels ARET V1 explicitement revus

| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.mapping` déclare seulement `component→entity` (`COMPONENT`), `function_symbol→symbol` et `brick→work_item`. |
| Invariant | Les trois entrées ont `requires_explicit_import=True`. Le registre ne lit aucun store, ne convertit aucune ligne et exclut explicitement les tables knowledge, proof, relation, asset, audit, front, pipeline et bundle. |
| Isolation | Le Core n’importe pas le pack; le registre ne contient ni filesystem, store, SQLite, réseau, shell ni toolchain ARET. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : module absent; ciblé : `12 passed` avec M4.1–M4.4; Core : `200 passed, 14 subtests passed`; `git diff --check`, scans de frontière et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.5 uniquement. Les mappings sont des contrats de préparation, non un moteur d’import ni une preuve de compatibilité ou de parité ARET. M4 reste `IN_PROGRESS`. |


### LOG-0132 — Publication et handoff M4.5

| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `55d184b87f7242cf36bd45767df9825bfe5cf357` — `feat: declare ARET structural mappings`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `55d184b87f7242cf36bd45767df9825bfe5cf357` avant le handoff documentaire. |
| Reprise | Le lot M4 suivant doit choisir une seule policy d’import ou une seule ressource mappée, avec source explicite, provenance, rollback et refus de toute promotion implicite. |

### LOG-0133 — Verdict M4.6 : pré-contrat fail-closed d’import de composant ARET V1
| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.import_preparation` expose exclusivement `component_import_preparation`. La demande résultante est liée à une `ProjectIdentity` VERA, un SHA-256 source déclaré, un `request_id` et un `requested_by`; elle cible uniquement `component→entity` de type `COMPONENT`. |
| Invariant | L’objet est figé et porte `requires_explicit_import=True`, `PREPARED_NOT_EXECUTED` et `UNVERIFIED_DECLARATION`. L’empreinte est contrôlée pour sa forme canonique, mais n’est ni calculée ni vérifiée par ce lot. Toute identité non explicite, hash non canonique, ID invalide ou acteur vide/multiligne est refusé. |
| Isolation | Le Core n’importe pas le pack. Le pré-contrat n’accepte aucun chemin, ne contient ni filesystem, store, SQLite, réseau, shell, lecture de ligne, transaction, audit ni écriture VERA. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : surface absente; ciblé : `10 passed`; Core : `210 passed, 14 subtests passed`; `git diff --check`, scans de frontière et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.6 uniquement. Il s’agit d’une préparation déclarative fail-closed; aucun import de composant, lecture de source, attestation de source, preuve, audit, rollback ni parité ARET n’est affirmé. M4 reste `IN_PROGRESS`. |

### LOG-0134 — Publication fonctionnelle et handoff M4.6
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `179474b8cf9914be3d04167d5573e1a331a93a61` — `feat: prepare explicit ARET component imports`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `179474b8cf9914be3d04167d5573e1a331a93a61` avant le handoff documentaire. |
| Reprise | Un lot M4 futur doit commencer par un contrat isolé de source read-only et d’attestation vérifiable, puis seulement traiter lecture transactionnelle, provenance/audit, collision/non-fusion, rollback et validation. Il ne doit pas exécuter une demande M4.6 par simple existence. |

### LOG-0135 — Verdict M4.7 : attestation bornée d’un snapshot ARET V1
| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.source_attestation` expose `attest_aret_v1_component_source`. La fonction exige une préparation M4.6 `component→entity` non exécutée/non attestée, une racine absolue/canonique/non liée et le snapshot V1 attendu `.aret-memory/aret_memory.sqlite`. |
| Invariant | Seuls les bytes du fichier régulier attendu sont lus en chunks puis hashés SHA-256. La taille, l’inode, le device et le `mtime_ns` sont contrôlés avant/après lecture; tout changement, lien, chemin absent, digest divergent, préparation dérivée ou référence différente de la baseline figée est refusé. |
| Observation ponctuelle | Contre `/home/ubuntu/ARET-MMU/aret-memory` au commit propre `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, la lecture read-only a attesté le snapshot de `11280384` bytes avec SHA-256 `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5`. |
| Isolation | Le Core n’importe pas le pack. Le module n’ouvre pas SQLite, n’exécute aucun shell/réseau, ne lit aucune ligne, ne crée ni transaction, audit, evidence, proof, import ou écriture VERA. L’égalité à la référence de baseline ne vérifie pas elle-même l’état Git ni le contenu de schéma. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : surface absente; ciblé : `9 passed`; Core : `219 passed, 14 subtests passed`; scans de frontière, attestation read-only ponctuelle et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.7 uniquement. Le lot atteste un snapshot de bytes et non l’identité intégrale de sa source, son contenu relationnel, une compatibilité de données, un import, une preuve ou une parité ARET. M4 reste `IN_PROGRESS`. |

### LOG-0136 — Publication fonctionnelle et handoff M4.7
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `a2af05459b7b3527c1a4a0deeb6f3400fc4d9f4a` — `feat: attest ARET V1 source snapshots`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `a2af05459b7b3527c1a4a0deeb6f3400fc4d9f4a` avant le handoff documentaire. |
| Reprise | Un lot M4 futur doit introduire, séparément, une identité de source vérifiable (répertoire/commit) ou une inspection SQLite strictement read-only et bornée; aucune lecture de lignes ni exécution de demande M4.6 ne peut être déduite de M4.7. |

### LOG-0137 — Verdict M4.8 : identité Git read-only de la source ARET V1 attestée
| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.git_identity` expose `verify_aret_v1_git_source_identity`. La fonction accepte exclusivement une attestation M4.7 liée au snapshot attendu, résout la racine Git, compare `HEAD` à la baseline V1 figée et exige un statut Git complètement propre. |
| Invariant | Les seules invocations sont `git rev-parse --show-toplevel`, `git rev-parse HEAD` et `git status --porcelain=v1 --untracked-files=all`, sous `GIT_OPTIONAL_LOCKS=0`, sans configuration système/globale, avec hooks et fsmonitor désactivés. Il n’y a ni shell, ni argument de commande fourni par un appelant, ni écriture Git. Toute racine non canonique, attestation divergente, commit non attendu ou arbre sale est refusé. |
| Observation ponctuelle | Contre `/home/ubuntu/ARET-MMU/aret-memory`, la vérification read-only retourne la racine `/home/ubuntu/ARET-MMU`, le commit propre `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4` et le hash de snapshot M4.7 `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5`. |
| Isolation | Le Core n’importe pas le pack. Le module n’ouvre pas SQLite, ne contacte aucun réseau, ne vérifie ni remote, ni signature/auteur du commit, ne lit aucune ligne et ne crée ni transaction, audit, evidence, proof, import ou écriture VERA. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : surface absente; ciblé : `5 passed`; Core : `224 passed, 14 subtests passed`; scans de frontière, vérification read-only ponctuelle et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.8 uniquement. Le lot lie un snapshot attesté à une identité Git locale propre; il ne certifie pas une provenance distante/cryptographique, n’ouvre pas SQLite et n’affirme ni import, preuve ou parité ARET. M4 reste `IN_PROGRESS`. |

### LOG-0138 — Publication fonctionnelle et handoff M4.8
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `86281dd0e718083a958c071929a81102f61859c9` — `feat: verify ARET V1 git source identity`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `86281dd0e718083a958c071929a81102f61859c9` avant le handoff documentaire. |
| Reprise | Un lot M4 futur peut, séparément, inspecter le schéma SQLite en mode read-only et sous contrat borné, ou définir l’admission transactionnelle d’un unique composant. Il ne doit ni déduire une signature/provenance Git inexistante, ni lire/importer une ligne par simple existence de M4.8. |

### LOG-0139 — Verdict M4.9 : inspection SQLite read-only du manifeste ARET V1
| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.sqlite_schema` expose `inspect_aret_v1_schema_snapshot`. La fonction exige une identité M4.8 propre liée au snapshot attendu, vérifie le hash avant/après et ouvre SQLite seulement en `mode=ro&immutable=1` avec `query_only`. |
| Invariant | Les seules requêtes SQL lisent `schema_migrations.version` ordonné et les noms de tables applicatives depuis `sqlite_schema`, en excluant tables système et FTS `knowledge_fts*`. Les tuples obtenus doivent correspondre exactement au manifeste V1 M4.3; tout hash, migration, table, chemin ou identité divergent est refusé. |
| Observation ponctuelle | Contre le snapshot baseline au hash `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5`, l’inspection read-only retourne les migrations `(1, 2, 3, 4, 5, 6)` et les 18 tables applicatives manifestées; le hash est identique avant/après. |
| Isolation | Le Core n’importe pas le pack. Le module ne lit aucune ligne métier, colonne, contrainte, index, trigger ni détail FTS; il n’exécute aucune requête mutante, shell ou réseau, et ne crée ni transaction VERA, audit, evidence, proof, import ou écriture. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : surface absente; ciblé : `5 passed`; Core : `229 passed, 14 subtests passed`; scans de frontière, inspection read-only ponctuelle et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.9 uniquement. Le lot confirme le manifeste du snapshot, non le contenu de ses tables, les données métier, leur compatibilité, un import, une preuve ou une parité ARET. M4 reste `IN_PROGRESS`. |

### LOG-0140 — Publication fonctionnelle et handoff M4.9
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `ef7f45e89790012669211d488f5ddd3ebe96d44a` — `feat: inspect ARET V1 schema snapshots`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `ef7f45e89790012669211d488f5ddd3ebe96d44a` avant le handoff documentaire. |
| Reprise | Un lot M4 futur doit isoler un premier lecteur de lignes `component` avec pagination, collision policy, batch/provenance/audit/rollback et zéro promotion, ou préciser d’abord ces contrats. La seule inspection de manifeste ne l’autorise pas implicitement. |

### LOG-0141 — Verdict M4.10 : lecture paginée brute de `component` ARET V1
| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.component_reader` expose `read_aret_v1_component_page`. La fonction exige le snapshot inspecté M4.9, applique un hash avant/après et retourne seulement des pages keyset ordonnées de colonnes raw `component` : `id`, `title`, `description`, `created_at`, `created_by`. |
| Invariant | SQLite est ouvert en `mode=ro&immutable=1` avec `query_only`. La seule requête métier est paramétrée, ordonnée par `id`, limitée à 100 et bornée par `after_id`; hash, inspection, chemin, curseur et limite divergents sont refusés. |
| Observation ponctuelle | Contre le snapshot baseline au hash `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5`, une page `limit=100` observe 17 composants, sans afficher ni persister leur contenu; aucun curseur suivant n’est requis et le hash est inchangé avant/après. |
| Isolation | Le Core n’importe pas le pack. Le module ne lit aucune autre table, ne construit ni `entity` ni mapping, ne réalise aucune normalisation/collision, et ne crée ni transaction VERA, audit, evidence, proof, admission, import ou écriture. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : surface absente; ciblé : `9 passed`; Core : `238 passed, 14 subtests passed`; scans de frontière, lecture read-only ponctuelle et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.10 uniquement. Le lot rend des lignes source observables, non des ressources VERA importées; il n’affirme ni conversion, provenance de lot, preuve, écriture réversible ou parité ARET. M4 reste `IN_PROGRESS`. |

### LOG-0142 — Publication fonctionnelle et handoff M4.10
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `f2a97e5c88c5ecd5c8924a7bea789ad239ec0f5f` — `feat: read ARET V1 component source pages`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `f2a97e5c88c5ecd5c8924a7bea789ad239ec0f5f` avant le handoff documentaire. |
| Reprise | Un lot M4 futur doit définir séparément la projection `component→entity`, les identifiants cibles, collision/non-fusion, le batch transactionnel, provenance/audit, rollback et l’admission. La présence d’un lecteur ne déclenche ni n’autorise implicitement un import. |

### LOG-0143 — Verdict M4.11 : préflight fail-closed `component→entity` ARET V1
| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.component_import_preflight` expose `component_import_preflight`. La fonction lie une demande M4.6 `component→entity`, une inspection M4.9 et une page M4.10 au même hash source, puis restitue le contexte cible et la plage observée. |
| Invariant | Les politiques sont fixes : `REJECT_EXISTING_TARGET`, `FORBID` merge/promotion/write et rollback/audit/provenance `REQUIRED_BEFORE_WRITE`. Préparation non pending, inspection/page/hash/ordre divergents, page vide ou acteur/ID non canoniques sont refusés. L’état final est exclusivement `PREFLIGHT_NOT_EXECUTABLE`. |
| Observation ponctuelle | Contre la baseline déjà attestée, identifiée, inspectée et lue, le préflight lie 17 composants au hash `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5`, avec `write_policy=FORBID`, `merge_policy=FORBID` et état `PREFLIGHT_NOT_EXECUTABLE`. |
| Isolation | Le Core n’importe pas le pack. Le module n’ouvre ni fichier/source/SQLite/store VERA, n’exécute aucun shell/réseau et ne réalise aucune projection, collision, transaction, rollback, audit, provenance, evidence, proof, admission, import ou écriture. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : surface absente; ciblé : `5 passed`; Core : `243 passed, 14 subtests passed`; scans de frontière, préflight ponctuel et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.11 uniquement. Le lot impose des préconditions à un futur write-path; il ne fournit ni write-path, ni rollback/audit/provenance effectifs, ni import, preuve ou parité ARET. M4 reste `IN_PROGRESS`. |

### LOG-0144 — Publication fonctionnelle et handoff M4.11
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `df262387f733a53a35e3fc63983dc40f1fdcdfe1` — `feat: preflight ARET V1 component imports`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `df262387f733a53a35e3fc63983dc40f1fdcdfe1` avant le handoff documentaire. |
| Reprise | Le prochain lot ne peut progresser qu’avec une projection de champs `component→entity` explicitement définie, puis un contrôle de collision VERA read-only et un write-path transactionnel distinct. Le préflight seul ne permet aucune écriture. |

### LOG-0145 — Verdict M4.12 : projection non écrivable `component→entity` ARET V1
| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.component_entity_projection` expose `project_aret_v1_component_entities`. La fonction lie un préflight M4.11 à sa page source et produit des drafts génériques déterministes avec identifiant `aret-component--<source_id>`, adresse VERA, type `component` et métadonnées de source. |
| Invariant | Le préflight doit rester fail-closed, la page doit correspondre exactement au hash, à la cardinalité et à la plage source préflightées. Les champs sont refusés s’ils ne satisfont pas les contrats textuels/adresse VERA; les brouillons dupliqués sont refusés. Le type porte `entity_type_registration_required=True` et l’état est `PROJECTED_NOT_WRITABLE`. |
| Observation ponctuelle | Contre la baseline déjà attestée, identifiée, inspectée, lue et préflightée, la projection produit 17 brouillons `component` en `PROJECTED_NOT_WRITABLE`, sans afficher les données source ni enregistrer un type/entity VERA. |
| Isolation | Le Core n’importe pas le pack. Le module n’ouvre ni fichier/source/SQLite/store VERA, n’appelle pas le service d’entités, n’exécute aucun shell/réseau et ne réalise ni collision, transaction, rollback, audit, provenance, evidence, proof, admission, import ou écriture. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : surface absente; ciblé : `4 passed`; Core : `247 passed, 14 subtests passed`; scans de frontière, projection ponctuelle et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.12 uniquement. Le lot rend une représentation cible déterministe contrôlable, non des entities créées; il n’affirme ni enregistrement, collision résolue, import, preuve ou parité ARET. M4 reste `IN_PROGRESS`. |

### LOG-0146 — Publication fonctionnelle et handoff M4.12
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `ee8736f6d08733ef044b21a2592ed704faee9133` — `feat: project ARET V1 component entity drafts`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `ee8736f6d08733ef044b21a2592ed704faee9133` avant le handoff documentaire. |
| Reprise | Le prochain lot peut isoler l’enregistrement exact du type générique `component` dans un store VERA cible ou un contrôle de collision read-only; tout write-path de brouillon reste séparé, transactionnel et soumis au préflight M4.11. |

### LOG-0147 — Verdict M4.13 : contrôle read-only des collisions cible `component` ARET V1
| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.component_target_collision` expose `check_aret_v1_component_target_clear`. Le contrôle exige une projection M4.12 non écrivable et un store VERA explicitement fourni dont l’identité est strictement égale à l’identité cible. |
| Invariant | Deux lectures exactes seulement : présence du type `component`, puis présence de chaque identifiant de draft. Un type ou identifiant existant, une identité/état/projection divergente ou une liste invalide est refusé. Un résultat clair porte `entity_type_state=ABSENT_REQUIRED` et `TARGET_CLEAR_NOT_WRITABLE`. |
| Observation ponctuelle | Contre la baseline source vérifiée et un store VERA temporaire explicitement créé, le contrôle couvre 17 drafts, constate l’absence du type/IDs, ne modifie pas le journal d’audit cible et retourne `TARGET_CLEAR_NOT_WRITABLE`. |
| Isolation | Le Core n’importe pas le pack. Le module n’ouvre aucune source ARET ni SQLite externe, n’ouvre aucune transaction, ne crée ni type/entity/audit et n’exécute ni rollback, provenance, evidence, proof, admission, import, shell ou réseau. ARET-MMU demeure propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Gates | Tests-first : surface absente; ciblé : `5 passed`; Core : `252 passed, 14 subtests passed`; scans de frontière, contrôle ponctuel avec audit invariant et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.13 uniquement. Le lot constate un état cible clair, non une permission d’écrire : aucun type/entity n’est créé, aucun import/proof/parité ARET n’est affirmé. M4 reste `IN_PROGRESS`. |

### LOG-0148 — Publication fonctionnelle et handoff M4.13
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `458675e29bae3d59bb02a7f19d91b16ec04e70a9` — `feat: check ARET V1 component target collisions`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `458675e29bae3d59bb02a7f19d91b16ec04e70a9` avant le handoff documentaire. |
| Reprise | Le prochain lot doit isoler l’enregistrement du type `component` dans un store dont M4.13 a attesté l’absence, avec transaction/audit et refus de type divergent. Toute création d’entity reste un lot séparé après cette préparation. |

### LOG-0149 — Verdict M4.14 : batch atomique générique de type et d’entités
| Champ | Valeur |
|---|---|
| Portée livrée | `EntityService.register_type_and_create_batch` reçoit un type générique absent, 1–100 `EntityCreateInput` validés et un acteur. Il enregistre type, entités et audits associés dans une unique transaction Core. |
| Invariant | Toutes les entrées sont validées avant transaction; IDs du batch sont uniques. Type déjà existant, conflit d’ID à n’importe quel rang ou erreur interne annule type, entités et audits créés par le batch. Un commit réussi conserve les records append-only; le lot ne fournit pas de suppression/réversion métier ultérieure. |
| Isolation | Aucun terme, import ou pack ARET n’est présent dans le Core. La primitive ne lit aucune source, ne lance aucun shell/réseau et ne lie aucune demande, preflight, projection ou provenance ARET. |
| Gates | Tests-first : surface absente; ciblé : `4 passed`; Core : `256 passed, 14 subtests passed`; scan anti-ARET/no-shell/no-network, rollback sur conflit et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.14 uniquement. Le lot fournit une capacité Core générique nécessaire à un futur write-path mais n’exécute ni import ARET, ni provenance de source, ni parité. M4 reste `IN_PROGRESS`. |

### LOG-0150 — Publication fonctionnelle et handoff M4.14
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `e868b1c4fef8e531aba2481b2c27029663b1887f` — `feat: create generic entity batches atomically`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `e868b1c4fef8e531aba2481b2c27029663b1887f` avant le handoff documentaire. |
| Reprise | Un lot M4 futur doit lier explicitement M4.11–M4.13 à ce primitif, transférer une provenance source déclarée/auditée et conserver zéro promotion. La primitive seule n’autorise aucun import. |


### LOG-0151 — Verdict M4.15 : premier import atomique explicitement autorisé `component→entity` ARET V1
| Champ | Valeur |
|---|---|
| Portée livrée | `vera_mmu.domain_packs.aret.component_authorized_import` expose une autorisation explicite, liée à M4.11–M4.13, puis `import_authorized_aret_v1_component_entities`. L’import revalide l’identité, hash, request/preflight, projection, cardinalité et cible ; il recontrôle les collisions juste avant d’appeler exclusivement `EntityService.register_type_and_create_batch`. |
| Invariant | Type `component`, entities et audits sont créés dans une transaction Core unique ou intégralement rollbackés. L’autorisation est strictement `EXPLICIT_ONE_SHOT_IMPORT_ALLOWED`; merge, promotion et preuve sont `FORBID`. Le résultat réussi est `IMPORTED_NO_PROMOTION` et conserve les métadonnées source de chaque draft. |
| Observation ponctuelle | Contre le snapshot baseline attesté/identifié/inspecté, une page de 17 composants a été importée dans un store VERA temporaire seulement : 17 entities, 18 nouveaux audits (`ENTITY_TYPE_REGISTERED` puis 17 `ENTITY_CREATED`), zéro action de preuve/promotion. ARET-MMU est resté propre au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Isolation | Le Core n’importe pas le pack. Le write-path de pack n’ouvre ni source ARET ni SQLite externe, n’emploie ni SQL brut, shell, réseau, evidence, proof, admission ou promotion ; l’unique écriture passe par la primitive Core générique. |
| Gates | Tests-first red : surface absente; ciblé : `5 passed`; suite Core : `261 passed, 14 subtests passed`; scans Core/pack, recheck de collision/rollback, intégration ponctuelle et wheel isolée : `PASS`. |
| Verdict | `PASS` pour M4.15 uniquement. C’est un premier import autorisé et borné, pas un import intégral, un mécanisme de reprise/idempotence, une migration des autres tables, une compatibilité ARET ni une preuve de parité. M4 reste `IN_PROGRESS`; C07/C08 restent `BLOCKED` sous `MEM-WALL-001`. |

### LOG-0152 — Publication fonctionnelle et handoff M4.15
| Champ | Valeur |
|---|---|
| Commit fonctionnel publié | `034efaf9f6d845742d2209c89099d10dd5fc4ad0` — `feat(aret-pack): authorize bounded component import`. |
| Dépôt et branche | `https://github.com/aciderix/vera-mmu.git`, `main`. |
| Vérification distante | `git ls-remote origin refs/heads/main` retourne exactement `034efaf9f6d845742d2209c89099d10dd5fc4ad0` après le push fonctionnel. |
| Reprise | Un lot suivant doit viser une seule gate du registre M4, sans étendre l’autorisation M4.15. Les priorités de migration de données sont la source/runtime stable, le ledger/reprise de `component`, puis `function_symbol→symbol`, `brick→work_item` et les tables/invariants associés. |

### LOG-0153 — Registre de clôture M4 établi
| Champ | Valeur |
|---|---|
| Portée | `docs/continuity/M4_COMPLETION_REGISTER.md` fournit les quinze gates de clôture : admission source/runtime, schéma profond, imports complets, data/invariants, capabilities, oracles/toolchain, playbook, MCP/hooks, VCS/bundles, parité et contrat public de sortie. |
| Règle de sortie | `M4.EXIT` est interdit tant qu’une gate est `SPLIT`, `BLOCKED` ou `UNKNOWN`. Les responsabilités M5/M6 sont distinguées de leurs dépendances de preuve qui bloquent néanmoins la compatibilité ARET. |
| Wall | `MEM-WALL-001` rend C07/C08 `BLOCKED` : la restauration mesurable des oracles/toolchain ARET dans un environnement de référence est une condition explicite, et non un travail contournable par simulation. |
| Verdict | Le registre est `ACTIVE`; M4 est `NOT_ELIGIBLE` pour clôture globale. |

### LOG-0154 — Verdict M4-A : ledger Core et migration paginée `component`
| Champ | Valeur |
|---|---|
| Portée livrée | Le Core reçoit `EntityService.create_batch_for_registered_type` et le ledger générique migration 033 `import_batch`/`import_batch_entity`, append-only, fingerprinté et idempotent. Le pack ARET reçoit la conformité SQLite read-only de `component` et l’autorisation explicite de page, qui délègue toute écriture au ledger Core. |
| Commits fonctionnels | `1ea116faeac58958311e6f135a6c68df8e6a5a53` — batch Core sur type enregistré ; `e3105b00a6d6152c5a833d0b7bafcd579442062c` — ledger d’import ; `cdf65f7150023d6dd57739f991db8c1ac93aeba2` — conformité `component` ; `8263d40b709acce40b946bd575cf8f648ae842b3` — série de pages ARET. Tous publiés et vérifiés sur `main`. |
| Invariants | Une page exige hash source, préflight, projection, conformité des colonnes, identité cible et autorisation liés. La première page exige une cible vide ; une page suivante exige le même snapshot/mapping/type dans le ledger. Collision, type manuel, binding divergent ou fingerprint divergent sont refusés; le ledger rollbacke intégralement le batch. Aucun chemin ne crée evidence, proof, admission ou promotion. |
| Gates | Tests-first rouges puis ciblés : batch type existant `4 passed`, ledger `6 passed`, conformité `component` `6 passed`, pages `7 passed`. Suite complète finale : `284 passed, 14 subtests passed`. Scans Core/pack, `git diff --check` et roues isolées : `PASS`. |
| Intégration réelle bornée | La chaîne attestée de la baseline ARET a lu la page de 17 composants en lecture seule. Dans un store VERA temporaire uniquement : 17 entities, 17 liens de ledger, replay exact sans écriture, `0` evidence et `0` proof link. ARET-MMU est resté propre à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Verdict | `PASS borné` pour les sous-contrats M4-A publiés. Il ne valide ni resolver/WAL, ni conformance multi-table, ni source réelle multi-pages, ni imports `function_symbol`/`brick`, ni données sémantiques, capabilities, toolchain, runtime/MCP/hooks/bundles/VCS ou parité ARET. M4 reste `IN_PROGRESS`; C01–C06/C16 `SPLIT`; C07/C08 `BLOCKED — MEM-WALL-001`; parité `UNKNOWN`. |

### LOG-0155 — Handoff documentaire M4-A
| Champ | Valeur |
|---|---|
| Registre | `M4_COMPLETION_REGISTER.md` est enrichi des résultats M4-A, de leurs preuves et des gates résiduelles M4-EXIT-01 à M4-EXIT-03. |
| Matrice et plan | La matrice documente les quatre sous-lots publiés et leurs hashes de commit. Le plan vivant pointe vers la révision fonctionnelle `8263d40b709acce40b946bd575cf8f648ae842b3`, migration 033 et la prochaine frontière. |
| Reprise | Avant M4-B, relire `MEM-STATE-099` à `MEM-STATE-101`, `LOG-0154`, ce registre et la matrice. Le prochain lot doit fermer un contrat distinct : soit resolver/WAL/post-validation M4-A, soit la chaîne structurelle `function_symbol→symbol` avec ses dépendances component déjà importées. |

### LOG-0156 — Verdict M4-A2 : resolver runtime ARET V1 et policy WAL/SHM
| Champ | Valeur |
|---|---|
| Portée livrée | `runtime_resolution.py` résout en lecture seule un runtime V1 existant depuis une racine source canonique et un mapping explicite : layout `.aret-memory` par défaut ou override unique `ARET_MEMORY_DIR`. La safety gate vérifie le snapshot régulier/stable et refuse tout sidecar `-wal` ou `-shm` au lieu de checkpoint, d’ouvrir SQLite ou d’écrire. |
| Gates | Tests-first rouge : surface absente ; ciblé : `14 passed`; suite complète : `298 passed, 14 subtests passed`; baseline réelle : `DEFAULT_RUNTIME_LAYOUT`, `NO_WAL_SIDECARS`, snapshot `11280384` bytes ; scan Core anti-ARET et pack no-SQLite/no-process/no-network/no-write, roue isolée et `git diff --check` : `PASS`. |
| Sécurité | Les répertoires et snapshot doivent exister, être absolus/canoniques et non liés. L’environnement global n’est jamais lu : seul le mapping caller fourni est admis, sans clé inconnue. Les sidecars actifs sont une condition de refus fail-closed. |
| Publication | Commit fonctionnel `c18d08c675c1bd69602471c082efc1c978b643e1` — `feat(aret-pack): resolve runtime safely before import` — publié et vérifié sur `main`. ARET-MMU demeure propre au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Verdict | `PASS borné` pour M4-A2. Le module ne lie pas encore un override à la chaîne complète attestation/Git/SQLite/reader/import; il ne fournit ni checkpoint, ni doctor, ni parité runtime complète. M4 reste `IN_PROGRESS`; C01–C06/C16 `SPLIT`; C07/C08 `BLOCKED — MEM-WALL-001`; parité `UNKNOWN`. |

### LOG-0157 — Handoff documentaire M4-A2
| Champ | Valeur |
|---|---|
| Registre | `M4_COMPLETION_REGISTER.md` marque runtime default/override et refus WAL/SHM comme prouvés, mais conserve l’intégration de l’override et le cycle d’attestation comme sorties obligatoires. |
| Reprise | Avant toute extension de l’attestation, lire `MEM-STATE-102` à `MEM-STATE-104`, `LOG-0156` et les conditions M4-EXIT-01 du registre. Le prochain patch doit soit lier le resolver à chaque maillon read-only de la chaîne, soit ouvrir M4-B sous un contrat structurel indépendant. |

### LOG-0158 — Verdict M4-A3 : chaînage runtime default/override vers le reader
| Champ | Valeur |
|---|---|
| Portée livrée | M4.7 accepte facultativement une résolution runtime et une safety WAL liées. M4.8 transporte le chemin de snapshot attesté; M4.9 puis M4.10 inspectent/lisent ce chemin exact. Un layout default garde le chemin V1 exact; un chemin divergent n’est possible que sous `ARET_MEMORY_DIR_OVERRIDE` explicite. |
| Gates | Tests-first rouges : nouvelles interfaces absentes; ciblés M4.7–M4.10 et chaîne : `31 passed`; suite complète : `301 passed, 14 subtests passed`; scans read-only/Core anti-ARET et roue isolée : `PASS`. |
| Intégration | Sur une copie temporaire du snapshot baseline : resolution `ARET_MEMORY_DIR_OVERRIDE` → `NO_WAL_SIDECARS` → attestation → identité Git baseline propre → manifeste SQLite → page component, soit 17 records. ARET-MMU est demeuré propre au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Sécurité | La chaîne ne crée aucun runtime, n’ouvre pas de write-path ARET et ne permet aucun snapshot custom sous un layout default. Le reader suit le snapshot inspecté lié à l’identité, jamais un chemin reconstruit sans attestation. |
| Publication | Commit fonctionnel `4f9d1ed0c881d41b7e98a01e228f05903e65a408` — `feat(aret-pack): bind runtime overrides to source chain` — publié et vérifié sur `main`. |
| Verdict | `PASS borné` pour M4-A3. La conformance des tables, les sources réellement multi-pages, post-validation, les imports structurels, les données sémantiques, toolchain/oracles, intégrations et la parité ARET restent hors contrat. M4 demeure `IN_PROGRESS`. |

### LOG-0159 — Handoff documentaire M4-A3
| Champ | Valeur |
|---|---|
| Registre | M4-EXIT-01 reflète le resolver et le chaînage override prouvés, mais ne conclut aucune compatibilité runtime ni parité. |
| Reprise | Avant le prochain sous-lot, relire `MEM-STATE-105` à `MEM-STATE-107`, `LOG-0158` et les gates M4-EXIT-02/M4-EXIT-03. Le prochain changement prioritaire peut fermer la conformance profonde de `component` ou ouvrir M4-B (`function_symbol→symbol`) sous contrat séparé. |

### LOG-0160 — Verdict M4-A : post-validation read-only de page component
| Champ | Valeur |
|---|---|
| Portée livrée | `component_post_validation.py` relit le batch `import_batch`, les liens `import_batch_entity` et les entités génériques après l’import de page autorisé. Il exige le binding autorisation/projection/résultat/store, le mapping/source snapshot exacts et l’égalité type/titre/description/métadonnées des entités avec les drafts. |
| Gates | Tests-first rouge : surface absente ; ciblés : `4 passed`; suite complète : `305 passed, 14 subtests passed`; scans no-source-I/O/no-write/no-proof, roue isolée et `git diff --check` : `PASS`. |
| Sécurité | Le contrôle ne crée aucun audit, evidence, proof link, admission ou promotion. Une projection/liaison ledger divergente est refusée; les triggers append-only ont également refusé la tentative de corruption directe de fixture. |
| Publication | Commit fonctionnel `2d237f05e762dd9cffc89a1c1c9a8c9be1da5ea9` — `feat(aret-pack): post-validate imported component pages` — publié et vérifié sur `main`; ARET-MMU reste propre au commit baseline. |
| Verdict | `PASS borné` pour post-validation d’une page component. Les sources multi-pages réelles, la post-validation exhaustive, les imports structurels/sémantiques, toolchain, M5/M6 et parité restent requis; M4 demeure `IN_PROGRESS`. |

### LOG-0161 — Handoff documentaire post-validation M4-A
| Champ | Valeur |
|---|---|
| Reprise | Lire `MEM-STATE-108`/`MEM-STATE-109`, `LOG-0160` et M4-EXIT-02/03. Le prochain sous-lot prioritaire est la conformance profonde de `component` ou l’ouverture contrôlée de M4-B. |

### LOG-0162 — Verdict M4-B : lecteurs structurels function_symbol et brick
| Champ | Valeur |
|---|---|
| Portée | Lecteurs ARET V1 `function_symbol` et `brick` publiés : pagination keyset, hash avant/après, SQLite `mode=ro&immutable=1`, `query_only`, snapshot inspecté et aucune conversion/import/écriture VERA. |
| Gates | Tests-first rouges ; ciblés `5 passed`; suite complète `310 passed, 14 subtests passed`; scans Core anti-ARET/pack no-write/no-network et roue isolée : `PASS`. |
| Publication | Commit fonctionnel `fb5a04db57f3dd00feca81724157df08502eb0ca` — `feat(aret-pack): read structural function and brick pages` — publié et vérifié sur `main`. ARET-MMU reste propre au baseline fixé. |
| Verdict | `PASS borné` pour les lecteurs seulement. Les projections, conformance profonde, authorisations, imports, rollback/reprise et sémantiques de statut restent non livrés ; M4-B reste `IN_PROGRESS`, M4 global `IN_PROGRESS`, parité `UNKNOWN`. |

### LOG-0163 — Verdict M4-B : projection pure function_symbol vers symbol
| Champ | Valeur |
|---|---|
| Portée | Projection déterministe `function_symbol→symbol` : owner component VERA, `FUNCTION`, module→path, symbole→identifier, convention/provenance source conservées. |
| Gates | Tests-first rouge ; ciblés `2 passed`; suite complète `312 passed, 14 subtests passed`; scans no-I/O/no-write/no-SymbolService et roue isolée : `PASS`. |
| Publication | Commit `e0a75c441c617000334cc2b275b5dcdd68e2bbcf` publié sur `main`. |
| Verdict | `PASS borné` pour projection sans écriture. Conformance source, binding à components importés, autorisation, import atomique, rollback/reprise et parité restent requis. |

### LOG-0164 — Verdict M4-B : projection pure brick vers work_item
| Champ | Valeur |
|---|---|
| Portée | Projection déterministe `brick→work_item` : type générique `WORK_ITEM`, titre/description/priorité et provenance legacy exhaustive (`state`, component, milestone, target platform). |
| Gates | Tests-first rouge ; ciblés `2 passed`; suite complète `314 passed, 14 subtests passed`; scans no-I/O/no-write/no-WorkItemService et roue isolée : `PASS`. |
| Publication | Commit `568d9fb296c2d8a03f525f3c1312260eb6287b83` publié sur `main`. |
| Verdict | `PASS borné` pour projection sans écriture. La sémantique de statut cible, le binding component, l’autorisation, l’import atomique, rollback/reprise et parité restent requis. |

### LOG-0165 — Verdict Core : batch générique de ressources structurelles
| Champ | Valeur |
|---|---|
| Portée | Migration Core `034_resource_import_batch_ledger.sql` et `ImportBatchService.commit_resource_import_batch` pour les seuls kinds fermés `SYMBOL` et `WORK_ITEM`. Les payloads sont préparés/fingerprintés canoniquement, les ressources sont créées exclusivement par `SymbolService` ou `WorkItemService`, puis liées à un batch/record append-only. Les transactions imbriquées du Core composent désormais par savepoint. |
| Gates | Tests-first rouges puis ciblés : `10 passed` pour le ledger 034 et `20 passed` avec le store ; suite complète : `325 passed, 14 subtests passed`. Tests : kind inconnu, prérequis parent, conflit sémantique, rollback, fingerprint divergent, replay sans écriture, migration réelle 033→034, immutabilité et savepoint imbriqué. |
| Sécurité | Aucun terme ARET dans le Core, aucune I/O source ou réseau, aucun SQL d’écriture du pack. Les ledger rows sont immuables ; une ressource inconnue, un payload incomplet, un conflit ou un parent absent rollbackent le lot. Le batch n’écrit ni evidence, ni admission, ni proof/proof link, ni promotion. |
| Distribution | `git diff --check`, scan Core anti-ARET et wheel isolée : `PASS`; l’API et la migration 034 sont présentes dans la wheel. |
| Publication | Commit fonctionnel `77591e586d8dfa60bb0b49dd06f1c056d11658a0` — `feat(core): add atomic generic resource import batches` — publié et vérifié sur `origin/main`. ARET-MMU reste propre au commit baseline `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Verdict | `PASS borné` pour la primitive Core générique uniquement. Aucun contrat de conformance source, préflight, collision de série, autorisation, import ou post-validation ARET `function_symbol→symbol` / `brick→work_item` n’est encore livré ; M4-B reste `IN_PROGRESS`, M4 global `IN_PROGRESS`, parité `UNKNOWN`. |

### LOG-0166 — Handoff documentaire Core 034 vers M4-B
| Champ | Valeur |
|---|---|
| Reprise | Lire `MEM-STATE-113`, `LOG-0165`, M4-EXIT-04/05 et le registre de clôture M4. Le prochain sous-lot autorisé est la conformance source et le préflight read-only propres à `function_symbol` et `brick`, avant toute authorisation ou écriture du pack. |
| Interdits maintenus | Ne pas modifier ARET ; ne pas importer de données sémantiques, evidence, proof, admission ou promotion ; ne pas contourner `MEM-WALL-001`; ne pas déclarer de compatibilité ni de parité. |

### LOG-0167 — Correctif Core 034 : refus de coercition implicite de payload
| Champ | Valeur |
|---|---|
| Constat | La revue a relevé que le dispatcher de batch pouvait convertir implicitement certains scalaires de payload via `str(...)` avant l’appel au service cible. Un test tests-first a démontré qu’un titre numérique de `WORK_ITEM` était accepté. |
| Correctif | Le préflight exige désormais que tous les champs textuels déclarés de `SYMBOL` et de `WORK_ITEM` soient déjà des chaînes avant toute transaction. Aucun payload non typé ne peut donc devenir valide par coercition implicite. |
| Gates | Test rouge ciblé puis vert ; contrats `resource_import_batches` + `store` : `21 passed`; suite complète : `326 passed, 14 subtests passed`; `git diff --check` et scan Core anti-ARET : `PASS`. |
| Publication | Commit fonctionnel `8e0d56692c3f1a5b19d9e2ac1d40678f10c7c7fc` — `fix(core): reject coerced resource batch payloads` — publié et vérifié sur `origin/main`. |
| Verdict | Durcissement `PASS` du contrat Core 034. Il ne modifie aucun état M4-B, aucune autorisation ARET, aucune parité, ni les blocages `MEM-WALL-001`. |

### LOG-0168 — Verdict M4-B : conformance et préflight structurels read-only
| Champ | Valeur |
|---|---|
| Portée | Le pack ARET vérifie maintenant, en SQLite `mode=ro&immutable=1`, la conformance de `function_symbol` (colonnes, FK component et unicité `(component_id,module,symbol)`) et de `brick` (colonnes, FK optionnelle, états fermés, priorité 1..5 et index roadmap). La préparation structurelle borne les seuls mappings `function_symbol→symbol` et `brick→work_item`; le préflight lie préparation, inspection, conformance et page source à une politique zéro-write. |
| Sémantique préservée | Le préflight function vérifie l’ID stable `component:module!symbol` — y compris `component:!symbol` si module vide. Le préflight brick interdit une priorité/état hors V1 et porte explicitement `PRESERVE_LEGACY_STATE_AS_METADATA`; il n’exécute aucune transition de lifecycle ni garde Front. |
| Gates | Tests-first rouges ; ciblés chaîne M4-B : `23 passed`; suite complète : `340 passed, 14 subtests passed`; scans Core anti-ARET et pack no-write/no-network/no-shell, `git diff --check`, wheel isolée et contrôle API isolé : `PASS`. |
| Publication | Commit fonctionnel `8d6e4fc2ec674ac3d2be8297ad3b3f9868239eaa` — `feat(aret-pack): add structural source conformance preflights` — publié et vérifié sur `origin/main`. ARET-MMU reste propre au commit baseline. |
| Verdict | `PASS borné` pour conformance/préflight read-only seulement. Collision de série, autorisation explicite, import, audit de lot structurel, post-validation, intégration réelle, Front ACTIVE, preuves/admission/promotion et parité restent non livrés. |

### LOG-0169 — Handoff M4-B vers collision et autorisation
| Champ | Valeur |
|---|---|
| Reprise | Lire `MEM-STATE-116`, `LOG-0168`, M4-EXIT-04/05 et le registre M4. Le prochain sous-lot est le contrat de collision/non-fusion et d’autorisation explicite, distinct par mapping, lié aux préflights et au Core 034. |
| Interdits maintenus | Aucune écriture ARET ; aucun import ARET sans autorisation future ; aucun evidence, proof/proof link, admission ou promotion ; pas de contournement `MEM-WALL-001`, ni claim de compatibilité/parité. |

### LOG-0170 — Verdict M4-B : collision non-fusionnelle et autorisation structurelle
| Champ | Valeur |
|---|---|
| Portée | `structural_target_collision` relit la cible VERA sans écriture, exige les entities parent pour les symboles et refuse toute ressource `symbol` ou `work_item` préexistante. `structural_import_authorization` relit ce check, lie préflight/projection/hash/cible et produit seulement une permission explicite `EXPLICIT_STRUCTURAL_IMPORT_ALLOWED`. |
| Sémantique | Les mappings sont fermés : `aret-v1-function-symbol-to-symbol-v1` et `aret-v1-brick-to-work-item-v1`. La cible doit être vide ; aucune fusion, reprise de série, ressource manuelle ni collision sémantique n’est acceptée dans ce contrat initial. Pour `brick`, `PRESERVE_LEGACY_STATE_AS_METADATA` demeure obligatoire et l’état lifecycle/Front reste différé. |
| Gates | Tests-first rouges ; ciblés : `9 passed`; suite complète : `349 passed, 14 subtests passed`; scans Core/pack, `git diff --check`, wheel isolée et contrôle API : `PASS`. |
| Publication | Commit fonctionnel `3f21200cc0ca31119e752b5a785dc54170fa15ce` — `feat(aret-pack): bind structural import authorization` — publié et vérifié sur `origin/main`. ARET-MMU est toujours propre au baseline `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Verdict | `PASS borné` pour les checks et autorisations sans effet. Les write-paths, audits de batch structurel, post-validations, intégrations réelles, lifecycle/Front, evidence/proof/admission/promotion et parité restent non livrés. |

### LOG-0171 — Handoff M4-B vers imports structurels contrôlés
| Champ | Valeur |
|---|---|
| Reprise | Lire `MEM-STATE-118`, `LOG-0170`, M4-EXIT-04/05. Le prochain lot peut définir les write-paths distincts `function_symbol→symbol` et `brick→work_item` à condition de consommer l’autorisation exacte, de recontrôler les collisions à l’écriture, de déléguer exclusivement au Core 034 et de post-valider sans écriture. |
| Interdits maintenus | Pas de SQL d’écriture dans le pack, pas de modification ARET, pas de merge, aucune evidence/proof/admission/promotion, aucun claim de parité ; la garde Front `ACTIVE` demeure un contrat lifecycle séparé. |


### LOG-0172 — Intégration temporaire M4-B et correction de parent `brick`
| Champ | Valeur |
|---|---|
| Baseline | VERA part de `8772f871fe8120e06be03ef30229ed6576a0656a`, tests initiaux `359 passed, 14 subtests passed`. ARET reste au commit propre `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |
| Hypothèse | Le mapping M4-A crée les parents `component` avec l’identifiant VERA déterministe `aret-component--<source_id>` ; un `brick.component_id` legacy doit être résolu vers cette même identité avant le contrôle des parents. |
| Observation initiale | L’intégration temporaire a attesté le snapshot, importé/post-validé 17 components et 9 symbols, puis le contrôle `brick` a refusé les parents `CORE`/`LIFT` sous leur identifiant source brut. Une requête SQLite read-only a confirmé que ces deux components existent bien dans la source et que leurs entités VERA projetées sont `aret-component--CORE` et `aret-component--LIFT`. |
| Correctif minimal | Le Domain Pack résout maintenant uniquement les `brick.component_id` non nuls en `aret-component--<component_id>` avant `_require_existing_entities`. Le Core reste sans ARET et aucun SQL d’écriture de pack n’est ajouté. Un nouveau test reproduit le défaut, vérifie la résolution du parent et confirme l’absence d’audit supplémentaire. Commit fonctionnel local : `2ab13fb4d8b6cb7558c824f6d405c4d7b27e95db`. |
| Intégration réelle | Dans `/tmp/vera-m4b-real-integration-_k5hvo49`, la source a été attestée au SHA-256 `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5`, taille `11 280 384`, runtime `NO_WAL_SIDECARS`, Git `CLEAN`; le manifest 001→006 est conforme. La page complète 17 components a été importée/post-validée et replayée sans écriture ; 9 symbols puis 13 work items ont suivi la chaîne conformance→preparation→preflight→projection→collision→autorisation→ledger Core→post-validation et chacun a été replayé sans écriture. |
| Contrôles | Ciblés : `27 passed`. Suite complète : `360 passed, 14 subtests passed`. `git diff --check`, scan Core anti-ARET, scans de write-path/post-validation et roue isolée : `PASS`. ARET demeure propre, sans WAL/SHM. |
| Limites et verdict | `OBSERVED_INTEGRATION_SUCCESS_NO_PROMOTION` seulement. Les work items Core sont tous `PLANNED`; les états legacy restent dans les métadonnées. Zéro `evidence`, `evidence_admission`, `knowledge_proof`, admission ou promotion. M4/M4-B restent `IN_PROGRESS`; C01–C06/C16 `SPLIT`; C07/C08 `BLOCKED — MEM-WALL-001`; parité `UNKNOWN`; `M4.EXIT` `NOT_ELIGIBLE`. |
| Publication | Aucun push n’a été effectué. Toute publication distante attend la validation explicite du propriétaire après remise du rapport. |

### LOG-0173 — M4-B : séries structurelles non fusionnelles et intégration réelle multi-pages

| Étape | Observation vérifiée |
|---|---|
| Baseline | `main` VERA à `e92ab70c2608bac4fa2e21e401ec9d1833f747bb`; ARET à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, arbres propres; `362 passed, 14 subtests passed` après le patch. |
| Défaut reproduit | Les nouvelles régressions de seconde page symbol et work item échouaient d’abord parce que `structural_target_collision` refusait toute cible ressource non vide, y compris une cible créée par la même série ARET V1. |
| Correction minimale | Le contrôle read-only identifie désormais une série compatible seulement lorsque le nombre total de ressources égale le nombre d’identifiants de cible reliés au même `source_system`, snapshot, mapping et resource kind. Il distingue `INITIAL_EMPTY_RESOURCE_TARGET_REQUIRED` de `MATCHING_PRIOR_SERIES_REQUIRED`; toute autre surface reste un conflit. L’autorisation, le write-path et la post-validation acceptent uniquement ces deux états. Le write-path recontrôle l’état avant commit et conserve `require_empty_target` pour la première page seulement. |
| Tests | Les deux tests de seconde page couvrent symbol et work item, imports, post-validations et non-écriture de replay. Ciblés : `17 passed`. Suite complète : `362 passed, 14 subtests passed`. `git diff --check` : `PASS`. La roue setuptools est installée depuis `/tmp/vera-m4b-wheelhouse` dans `/tmp/vera-m4b-wheel-venv`, avec import du package depuis `site-packages`. Commit fonctionnel local : `d2efe72`. |
| Intégration source | Le script temporaire `/tmp/vera_m4b_real_series_integration.py` utilise un store VERA neuf sous `/tmp`, l’attestation ARET, le manifest et les lecteurs `mode=ro&immutable=1`. Le snapshot `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5` est resté stable; runtime `NO_WAL_SIDECARS`; Git ARET `CLEAN`. |
| Résultat | Avec des pages de trois records, 17 components sont importés une fois, 9 symbols en 3 pages et 13 work items en 5 pages. Les pages suivantes sont autorisées dans l’état `MATCHING_PRIOR_SERIES_REQUIRED`, post-validées, puis rejouées sans écriture. Le ledger final contient 8 resource batches et 22 liens; `evidence=0`, `evidence_admission=0`, `knowledge_proof=0`. |
| Verdict | `OBSERVED_MULTI_PAGE_INTEGRATION_SUCCESS_NO_PROMOTION`. Ce lot améliore M4-B mais ne clôt pas les gates M4-EXIT-04/05 : lifecycle/Front, courses concurrentes indépendantes, données sémantiques, toolchain/oracles, M5/M6 et parité restent distincts. Aucun push n’est déclenché par cette entrée. |

### LOG-0174 — M4-C.1 : substrate d’import knowledge et projection read-only

| Étape | Observation vérifiée |
|---|---|
| Cadrage source | Inventaire SQLite read-only du snapshot ARET attesté : 532 `knowledge`, 517 `knowledge_source`, 2 545 `knowledge_tag`, 47 `relation`, 4 `proof`, 3 `proof_link`, 24 `front_state` et 0 `asset`. Types legacy : 8; statuts : `ACTIVE` 50, `OBSERVED` 481, `SUPERSEDED` 1. L’artefact de cadrage est versionné dans `continuity/artifacts/m4c_knowledge_source_inventory_2026-08-26.md`. |
| Contrat Core | Migration 035 et API générique `KnowledgeImportBatchInput` ajoutées avec ledger append-only, fingerprint, borne 1–100, type préexistant, cible vide optionnelle, rollback et replay exact. Aucun terme, mapping ou I/O ARET n’existe dans le Core. |
| Contrat Pack | `knowledge_reader` lit une page ordonnée via SQLite immutable, atteste la stabilité du snapshot et vérifie `content_hash`. `knowledge_projection` conserve la sémantique source dans les métadonnées, utilise `aret-legacy-knowledge` et rabat exclusivement `SUPERSEDED` vers `OBSERVED` afin de ne créer ni supersession ni promotion implicite. |
| Validation | Tests rouges avant API/projection; ciblés `7 passed`; suite `369 passed, 14 subtests passed`; `git diff --check` et roue isolée : `PASS`. Commit fonctionnel local : `41594ba`. |
| Verdict | `PASS borné` pour le substrate et la projection. Aucun import source→cible réel n’est encore observé et aucune table sémantique associée ne peut être déclarée migrée. La suite exigera un contrat de type cible, préflight/collision/autorisation, post-validation et une intégration temporaire avant toute extension à `knowledge_source`, tags, relations, supersession, proof, Front ou audit. |

### LOG-0175 — M4-C.2 : import knowledge ARET en série, sans promotion

| Étape | Observation vérifiée |
|---|---|
| Défaut exposé | La première intégration réelle a refusé la source car le lecteur supposait `effective_at` non nullable. Le schéma observé le déclare nullable; un diagnostic SQLite immutable a exclu tout écart de `content_hash`. Le patch minimal accepte seulement cette nullabilité. |
| Chaîne | Un type cible `aret-legacy-knowledge` doit être déclaré explicitement avant autorisation. Chaque page lie source/projection/préflight/clear-check/autorisation; la cible est soit initialement vide, soit la même série attestée. Le write-path relit cet état avant le batch Core 035; la post-validation relit ledger et knowledge sans écriture. |
| Politique | `SUPERSEDED` source est importé Core `OBSERVED`, avec état et prédécesseur legacy conservés en métadonnées; aucune `knowledge_supersession`, evidence, admission, proof ou promotion n’est créée. |
| Intégration source | Le snapshot ARET attesté et stable `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5`, Git `CLEAN`, runtime `NO_WAL_SIDECARS`, a été importé vers un store `/tmp` : 532 knowledge en six pages. Les pages 2 à 6 ont toutes la série `MATCHING_PRIOR_SERIES_REQUIRED`; post-validation et replay sont read-only. Résultat archivé sous `continuity/artifacts/m4c_multi_page_knowledge_integration_2026-08-26.json`, SHA-256 `567cdf8ccd06ee714c2220548e9677c0ad25d384a73286a57117be482f47ac1c`. |
| Contrôles | Ciblés `10 passed`; suite `372 passed, 14 subtests passed`; `git diff --check`, scan Core anti-ARET et roue installée isolément : `PASS`. Commit fonctionnel local : `88e56d5`. |
| Verdict | `OBSERVED_MULTI_PAGE_KNOWLEDGE_IMPORT_NO_PROMOTION`. Aucun claim de ligne de supersession, de provenance attachée, de tag, relation, preuve, Front, audit importé, compatibilité intégrale ou parité n’est autorisé. |

### LOG-0135 — 2026-08-26 — M4.EXIT — Audit complet, restauration impossible et verdict fail-closed

| Champ | Valeur |
|---|---|
| Type | `RUN` / `COMPARISON` / `WALL` / `VERDICT` |
| Baseline | VERA `873fad9`; ARET `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, worktree propre. |
| Hypothèse | Les gates M4 restantes pourraient être satisfaites ou la toolchain/oracles pourrait être restaurée à partir d’une référence versionnée accessible. |
| Vérifications | Audit gate par gate dans `artifacts/m4_exit_precondition_audit_2026-08-26.md`; inspection passive des dépendances, artefacts, références Git locales et quatre branches publiques dans `artifacts/m4_exit_toolchain_restoration_check_2026-08-26.md`; suite VERA finale : `378 passed, 14 subtests passed`. |
| Observation | `gcc`, Cargo, Wine, MinGW, Clang/LLVM et `zstd` sont absents; `target/release/aret`, `bench/*`, `Cargo.toml` et `src/cpudiff.rs` sont absents du checkout et de toutes les branches publiques accessibles. |
| Verdict | `M4.EXIT = NOT_ELIGIBLE`. Les migrations restantes, la wall C07/C08, les surfaces M5/M6 et le harnais de parité ne peuvent pas être remplacés par des fixtures ou assertions locales. |
| Suivi | Attendre un bundle/révision ARET attesté contenant corpus, scripts et build/binaire reproductible; poursuivre ensuite M4-C, M5/M6 et la parité avant un nouvel audit de sortie. |

### LOG-0176 — 2026-08-26 — Toolchain toolkit restaurée et oracles ARET exécutés en observation externe
| Champ | Valeur |
|---|---|
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Baseline protégée | Le worktree `/home/ubuntu/ARET-MMU` demeure propre au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4` et n’a reçu aucune écriture. |
| Référence exécutée | Clone isolé de `aciderix/Automatic-reverse-engineering-toolkit`, branche `claude/aret-mcp-startup-check-5a13sx`, commit `7a0429790bb04d1ad3c1819449e906140ebf4513`, resté propre. |
| Build reproductible | Cargo 1.75 refuse le lockfile v4 ; Cargo 1.79 refuse une dépendance en édition Rust 2024. Rust/Cargo 1.85.0 construit avec `--locked --release` le binaire SHA-256 `6ca52f0955266aeda31d235caacf0844e2516f41d67468632f2ddb1bb1e16a19`, dans un répertoire externe au clone. |
| Préconditions restaurées | GCC 32 bits, MinGW i686, Wine 9.0, Clang/LLD 18, zstd et `libunicorn-dev` ont été installés explicitement dans le sandbox ; versions, scripts, corpus, commandes et logs sont préservés dans `artifacts/aret_toolkit_oracle_run_2026-08-26/`. |
| Oracles observés positifs | `difftest 272/272`; transpile `4/4`; audit `__stdcall PASS`; EH MSVC `6/6`; EH GNU `7/7`; `funcdiff` avec Rust 1.85 : 22 672 fonctions liftées, 11 602 optimisées, 0 divergence. |
| Résultats non promouvables | `wine_hashes` : 155 `OK`, 14 `BUILD-FAIL`, 90 `SKIP`, avec format réel `<fixture> OK <hash>` distinct du normaliseur historique. `winediff` : `255/264`, exit 1, neuf divergences conservées comme `FAIL`. |
| Distinction de preuve | Les scripts ont été appelés directement depuis le clone de référence, pas via une capability VERA. Ces sorties sont des observations externes hashées, **pas** des evidence/admissions/proofs VERA, et ne promeuvent aucun statut `PROVEN`. |
| Décision | La sous-partie factuelle de `MEM-WALL-001` portant sur l’absence de la référence/toolchain est `OBSERVED_RESTORED`; C07/C08 restent `IN_PROGRESS` faute de capability, normalisation, admission et doctor. `M4.EXIT = NOT_ELIGIBLE` est maintenu, notamment parce que `winediff` échoue et que M5/M6 restent requis. |
| Suivi | Implémenter test-first le pack de capability fermé et son normaliseur ; investiguer les neuf divergences Wine sans filtrage de fixture. |

Références : [rapport d’exécution](artifacts/aret_toolkit_oracle_execution_2026-08-26.md), [audit M4.EXIT actualisé](artifacts/m4_exit_precondition_audit_2026-08-26.md).

### LOG-0177 — 2026-08-26 — M4-D : pipeline d’oracles ARET fermé, sandboxé et non promouvable
| Champ | Valeur |
|---|---|
| Type | `BASELINE` / `PATCH` / `RUN` / `EVIDENCE` / `WALL` / `VERDICT` |
| Baseline protégée | ARET-MMU reste au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, sans écriture. Le toolkit distinct est propre au commit `7a0429790bb04d1ad3c1819449e906140ebf4513`. |
| Hypothèse | Un Pack ARET peut encapsuler le catalogue historique fermé dans un runner reproductible sans donner au Core la moindre connaissance d’ARET ni produire implicitement une proof. |
| Patches fonctionnels | `124670e` : catalogue de neuf oracles, préflight, confinement repository/symlink et normalisation fail-closed. `d204d28` : migration 037 et enregistrement Core générique `OBSERVED_PROCESS` hash-bound. `e5e7ca1` : capability/policy Pack, commit/checksum binaire, sandbox `unshare --user --map-root-user --net`, asset Core, execution et evidence `PENDING`. |
| Tests-first | Tests rouges puis verts : catalogue exact, paramètres/fixtures fermés, traversal/symlink, dépendances manquantes `SKIPPED`, timeout `ERROR`, sortie non nulle avec texte `SKIP` conservée `FAIL`, `winehash` `UNKNOWN`, policy, hash, atomicité, append-only, checkout Git, sandbox et binaire externe attesté. |
| Runs VERA | `difftest` complet : `PASS 272/272`, asset SHA-256 `6e94b379cde87de75064ea038a99707fd67e96796427af29d3a6448f58f93d3e`, evidence `PENDING`. `winediff win32_username` : `PASS 1/1`, asset SHA-256 `0155b815f2c9ab5d898825525dd244ad000f2ebbbd93207265c3612c633c98e7`, evidence `PENDING`. |
| Wall | Une tentative de corpus `winediff` complet a bloqué sur `win32_winsock` sous sandbox et a été arrêtée par supervision avant la création d’un artifact/evidence complet. Elle n’a aucun verdict. Le baseline externe `winediff 255/264`, exit 1 et ses neuf divergences demeurent un `FAIL` distinct et visible. |
| Contrôles | Suite complète : `390 passed, 17 subtests passed`; scan Core anti-ARET, `git diff --check` et installation de roue isolée : `PASS`. |
| Verdict | `OBSERVED_CLOSED_ORACLE_PIPELINE_NO_ADMISSION`. C07/C08 sont `IN_PROGRESS`, jamais `PASS` : validator, admission HMAC, proof/gate, doctor, corpus Wine complet et parité restent requis. `M4.EXIT = NOT_ELIGIBLE`. |
| Référence | `artifacts/m4d_closed_oracle_pipeline_integration_2026-08-26.md`; `MEM-STATE-124`; registre M4 et matrice C07/C08. |

### LOG-0178 — 2026-08-26 — M4-D : matrice universelle de verdict et chaîne stricte `PASS`
| Champ | Valeur |
|---|---|
| Type | `HYPOTHESIS` / `PATCH` / `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Hypothèse | VERA peut traiter universellement un résultat de capability sans connaître ARET : seul un `PASS` normalisé, lié à son artifact et validé peut atteindre admission → proof → gate; toutes les autres classes restent non promouvables. |
| Test rouge | `tests/test_evidence_asset_validator.py` échoue initialement car le kind fermé `EVIDENCE_ASSET` n’existe pas. Il couvre `PASS`, `FAIL`, `ERROR`, `SKIPPED`, `UNKNOWN` et un `PASS` dont le hash d’asset est altéré. |
| Patch Core | `7365ba8` ajoute migration 038, le validator générique `EVIDENCE_ASSET` et la reconstruction sécurisée du binding admission-validation afin de préserver les clés étrangères et les triggers append-only. Aucun vocabulaire, script ou dépendance ARET n’entre dans le Core. |
| Matrice vérifiée | Un asset correctement lié ne rend pas un verdict fonctionnel admissible : `FAIL`/`ERROR`/`SKIPPED`/`UNKNOWN` sont refusés par `AdmissionService`; `PASS` à asset altéré échoue au validator; aucun ne crée proof ni gate `PASS`. |
| Run réel | `difftest` via toolkit verrouillé, binaire attesté et sandbox réseau : `PASS 272/272`; asset `aba12da0f0279ffcb2b834df6aba0db8a0966d271b288e1c368dc3c5286911fe`; validator `PASS`; admission `ADMITTED` stricte; proof HMAC `PROVEN`; gate `PASS`, dans `/tmp/vera-aret-universal-chain`. |
| Contrôles | Ciblés : `15 passed, 4 subtests passed`; suite : `391 passed, 21 subtests passed`; migration 001→038, scan Core anti-ARET, `git diff --check` et roue isolée : `PASS`. |
| Non-déduction | Cette proof de runtime temporaire démontre le mécanisme, non la parité ARET. `winediff 255/264` reste `FAIL`; le corpus Wine sandboxé bloqué n’a aucun verdict; C07/C08 restent `IN_PROGRESS`, parité `UNKNOWN`, M4.EXIT `NOT_ELIGIBLE`. |
| Référence | `artifacts/m4d_universal_verdict_chain_2026-08-26.md`; `MEM-STATE-125`. |

### LOG-0179 — 2026-08-26 — M4-D : `winehash UNKNOWN` réel, asset valide et admission refusée
| Champ | Valeur |
|---|---|
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| But | Vérifier sur une sortie réelle non positive que le mécanisme VERA conserve le verdict de l’oracle, même lorsque l’artefact et son execution sont intègres. |
| Run | `winehash` a été exécuté par le runner Pack fermé dans `/tmp/vera-aret-unknown-chain`, depuis le toolkit ARET verrouillé et sans modification du script ou du corpus. |
| Observation | Execution `COMPLETED`; normalisation Pack `UNKNOWN`; asset SHA-256 `70aa80f03a37ef6e6232249273546f61ec527a5b58f2d4757eaae6a7f57cb63f`; validator `EVIDENCE_ASSET=PASS`. |
| Barrière | Sous policy `VALIDATED_PASS_EVIDENCE`, l’admission est refusée avec `Seule une evidence PASS est admissible.` Le runtime contient `0` evidence admission et `0` proof; aucune gate ne peut passer. |
| Comparaison | Le cas montre que l’intégrité physique de la trace ne remplace pas la sémantique de l’oracle : `UNKNOWN` reste non promouvable. Il complète le `difftest PASS` réel de LOG-0178 sans modifier les oracles. |
| Verdict | `OBSERVED` : classement fail-closed réel d’un `UNKNOWN`. C07/C08 `IN_PROGRESS`; Wine/parité `UNKNOWN`; `M4.EXIT = NOT_ELIGIBLE`. |
| Référence | `artifacts/m4d_real_unknown_verdict_2026-08-26.md`; `MEM-STATE-126`. |

### LOG-0180 — 2026-08-26 — M4-D : `SKIPPED`/`FAIL` réels et doctor Pack
| Champ | Valeur |
|---|---|
| Type | `RUN` / `EVIDENCE` / `COMPARISON` / `PATCH` / `VERDICT` |
| Objectif | Compléter des cas réels non positifs sans altérer les scripts ARET, puis rendre observable la disponibilité du runner fermé et de ses prérequis. |
| `SKIPPED` | `difftest` dans le checkout toolkit propre sans binaire local : préflight détecte `target/release/aret`; verdict `SKIPPED`; asset/evidence persistés; validator `PASS`; admission refusée; `0` proof/gate. |
| `FAIL` | `winediff user32_paint` réel avec binaire attesté : verdict `FAIL`; asset `abb71efd27a9d288aa9de79790c13d4494e76c1165e1169b71a5a28aff906bf4`; validator `PASS`; admission refusée; `0` proof/gate. Aucun corpus ou normaliseur n’est modifié. |
| `ERROR` | Contrat testé pour timeout/sortie inconnue; aucun timeout runtime n’est forcé artificiellement. L’absence de run `ERROR` réel est un fait, non une promotion de couverture. |
| Doctor | `4e30eeb` ajoute le doctor ARET observationnel : référence Git/propreté, binaire SHA-256, neuf préflights et sandbox `unshare`; aucune installation. Le doctor réel est `READY`; sandbox absente est `DEGRADED` par test. |
| Contrôles | `395 passed, 21 subtests passed`; wheel isolée, scan Core anti-ARET et diff : `PASS`. |
| Verdict | Classification universelle fail-closed observée pour `PASS`, `UNKNOWN`, `SKIPPED` et `FAIL`; C07/C08 `IN_PROGRESS`; parité `UNKNOWN`; M4.EXIT `NOT_ELIGIBLE`. |
| Référence | `artifacts/m4d_real_verdict_matrix_and_doctor_2026-08-26.md`; `MEM-STATE-127`. |

### LOG-0181 — 2026-08-26 — Correction M4 : transport interne de verdicts, façade MCP en M5
| Champ | Valeur |
|---|---|
| Type | `DECISION` / `PATCH` / `TEST` / `VERDICT` |
| Correction | Le score local d’un oracle ARET ne constitue pas un critère de réussite VERA. M4 évalue la classification et le transport fail-closed de son verdict; M5 évaluera ensuite le même comportement via un vrai serveur/client MCP. |
| Patch | `8818100` modifie le normaliseur fractionnaire Pack : sortie reconnue complète → `PASS`; sortie reconnue partielle, par exemple `271/272`, → `FAIL`; sortie non reconnue → `ERROR`. Les patterns de transpile/Wine/EH suivent la même règle. |
| Matrice | Les tests de transport construisent uniquement une référence Pack et un adapter de processus déclaré par le test. Ils couvrent `272/272 PASS`, `271/272 FAIL`, timeout `ERROR`, sortie inconnue `ERROR`, dépendance absente `SKIPPED`, format Wine hash `UNKNOWN`, asset valide et admission stricte. Le client futur ne peut injecter aucune de ces valeurs. |
| Contrôles | Test rouge `271/272` initialement `ERROR`; patch minimal; ciblés `11 passed, 4 subtests passed`; suite `397 passed, 25 subtests passed`; scan Core anti-ARET, diff et roue isolée : `PASS`. |
| MCP | L’inventaire confirme l’absence actuelle de serveur MCP de production. Le contrat M5 exige une vraie session client→serveur, les outils bornés et les mêmes scénarios sans injection client de commande/verdict/artefact. |
| Verdict | C07 reste `IN_PROGRESS` pour la couverture service complète; la conformance MCP est `PLANNED` M5. M4.EXIT reste `NOT_ELIGIBLE` pour ses gates d’import/compatibilité/bundle/playbook restantes, pas pour le score Wine local. |
| Référence | `artifacts/m4d_verdict_transport_scope_correction_2026-08-26.md`; `artifacts/m5_mcp_verdict_transport_contract_2026-08-26.md`; `MEM-DEC-128`. |

### LOG-0182 — 2026-08-26 — M5-A : portage adaptatif de la façade MCP stdio VERA
| Champ | Valeur |
|---|---|
| Type | `BASELINE` / `PATCH` / `RUN` / `EVIDENCE` / `VERDICT` |
| Baseline | ARET-MMU contient déjà un serveur MCP réel, stdio/HTTP, catalogue fermé, réponses structurées et contrôle client stdio. VERA n’avait jusqu’ici qu’une CLI `identity` / `inspect` / `init`; M1–M4 avaient livré le Core universel et le Pack ARET sans façade MCP. |
| Patch | `5ffe182` porte le socle de transport à `src/vera_mmu/mcp_server.py`, avec SDK `mcp>=2.0,<3.0` et entry point `vmmu-mcp`. La façade Core définit exactement sept outils : catalogue, exécution de capability, lecture d’execution, lecture d’asset, validation, admission et gate. |
| Frontière | `mcp_server.py` n’importe aucun Pack ni concept ARET, ne crée aucun subprocess, réseau ou shell, et refuse l’exécution si aucun adapter serveur explicite n’est configuré. Seul un adapter hôte crée execution/evidence; le client n’envoie ni commande, chemin, stdout, stderr, exit code, score, verdict ou artifact. |
| Test MCP | `tests/test_mcp_stdio_verdict_transport.py` lance le serveur de fixture stdio puis un vrai `ClientSession`. Le scénario est fixé côté serveur au démarrage. La matrice couvre `272/272 PASS`, `271/272 FAIL`, prérequis absent `SKIPPED`, timeout/sortie inconnue `ERROR`, Wine hash `UNKNOWN` et asset déclaré altéré (`validation FAIL`). Seul `PASS` validé obtient admission et gate `PASS`. |
| Injection | Le schéma MCP de `mmu_run_capability` ne contient que `capability_id` et `parameters`; une tentative client de fournir `parameters.verdict=PASS` est refusée, sans execution/admission/gate promue. |
| Incident résolu | Les handlers MCP synchrones étaient exécutés par le SDK dans un thread distinct du store SQLite. Ils sont async afin de rester dans le thread propriétaire du store. L’enveloppe d’erreur reste structurée et le refus ne devient jamais un succès. |
| Contrôles | Rouge initial : SDK MCP absent. Après ajout de dépendance/portage : `2 passed, 7 subtests passed` (MCP); ciblés `5 passed, 15 subtests passed`; suite complète `399 passed, 32 subtests passed`; frontière Core sans imports Pack/ARET ni shell/réseau : `PASS`; `git diff --check`: `PASS`; roue isolée et `vmmu` / `vmmu-mcp --help`: `PASS`. |
| Limite | Le point d’entrée générique `vmmu-mcp` est intentionnellement fail-closed : sans adapter déclaré par un manifeste/configuration future, il permet les lectures mais refuse toute exécution. L’adapter de scénario est exclusivement une fixture de test et ne constitue pas un runtime ARET de production. |
| Verdict | `M5-A = PASS` : premier transport MCP universel et vérifié. M5 global, compilateur/manifeste immutable, configuration/hook et adapters de production restent `IN_PROGRESS` / `PLANNED`. |
| Référence | `5ffe182`; `tests/test_mcp_stdio_verdict_transport.py`; `tests/mcp_verdict_fixture_server.py`; `MEM-DEC-129`. |

### LOG-0183 — 2026-08-26 — M5-B : manifeste MCP canonique et vérifié
| Champ | Valeur |
|---|---|
| Type | `BASELINE` / `PATCH` / `TEST` / `VERDICT` |
| But | Fermer I007/I008/I011/I012 après M5-A : la façade MCP doit pouvoir être bornée par une configuration déclarative, project-bound, canonicalisée et non réutilisable après dérive du store. |
| Patch | `5de260d` ajoute `mcp_manifest.py`. `compile_mcp_manifest` produit `vera-mcp-manifest/v1` depuis identité de projet, checksums de migrations, outils M5-A, capabilities `ALLOW`, contracts, policies et bindings symboliques d’adapter. Le SHA-256 du JSON canonique est `mcp_build_hash`. |
| Fermeture | Chaque capability visible exige exactement un binding; binding absent, supplémentaire ou ressemblant à un chemin/une commande est refusé. Le manifeste ne contient ni commande, stdout/stderr, code de sortie, verdict ni artifact client. |
| Vérification | `verify_mcp_manifest` recompile le snapshot depuis le store courant. Un projet distinct, un catalogue/policy/migration modifié, un binding divergent ou un hash incohérent est refusé bruyamment. |
| Façade | `create_server(..., manifest=...)` vérifie le manifest au démarrage, limite le catalogue au snapshot et refuse une capability dont l’`adapter_id` runtime ne correspond pas au binding attesté. La fixture stdio M5-A passe désormais par cette voie. |
| Contrôles | Rouge : module puis vérificateur absents; vert : `5 passed` manifeste et `2 passed, 7 subtests passed` MCP. Suite complète : `404 passed, 32 subtests passed`. Frontière sans Pack/ARET/shell/réseau : `PASS`; roue isolée, inclusion de `mcp_manifest.py` et entry points : `PASS`; diff : `PASS`. |
| Limite | Les bindings restent symboliques : registry/adapters de production, instructions/hooks/config générés et snapshots d’installation sont des lots M5 suivants. Aucun adapter de test n’est promu en runtime ARET. |
| Verdict | `M5-B = PASS`. M5 reste `IN_PROGRESS`; M5-A/B n’autorise ni exécution implicite ni injection client de résultat. |
| Référence | `5de260d`; `tests/test_mcp_manifest.py`; `tests/test_mcp_stdio_verdict_transport.py`; `MEM-DEC-130`. |

### LOG-0184 — 2026-08-26 — M5-C : registry d’adapters runtime manifest-bound
| Champ | Valeur |
|---|---|
| Type | `PATCH` / `TEST` / `VERDICT` |
| But | Après M5-A (transport) et M5-B (manifeste), retirer le câblage global d’adapter lors d’une exécution MCP et sélectionner l’objet runtime uniquement à partir de la capability attestée. |
| Patch | `50cc79a` ajoute `mcp_adapters.py`. `RuntimeAdapterRegistry` reçoit exclusivement des objets déjà instanciés par l’hôte serveur; il ne charge ni module ni chemin et ne lance aucune commande pendant la résolution. |
| Fermeture | Un `adapter_id` est validé comme symbole fermé; chemin, espace/commande, doublon, méthode `run` absente, adapter introuvable ou capability dupliquée dans le manifeste sont refusés. La résolution ne renvoie que la table immutable capability→objet. |
| Intégration | `create_server` accepte `adapter_registry` seulement avec un manifeste M5-B vérifié. Adapter direct et registry sont mutuellement exclusifs. À l’appel MCP, l’objet est résolu par `capability_id` puis son `adapter_id` est recontrôlé contre le binding manifest avant toute persistence. |
| Test réel | Le serveur fixture stdio M5-A passe désormais `RuntimeAdapterRegistry((adapter,))`; le vrai client MCP conserve toute la matrice `PASS`/`FAIL`/`SKIPPED`/`ERROR`/`UNKNOWN`/asset altéré sous manifest et registry. |
| Contrôles | Rouge : module registry absent. Verts : `4 passed, 5 subtests passed` registry, puis `10 passed, 12 subtests passed` registry/manifeste/MCP. Suite complète `408 passed, 37 subtests passed`; frontière Core sans Pack/ARET/shell/réseau, `git diff --check` et roue isolée : `PASS`. |
| Limite | Le registry est un mécanisme générique, pas un adapter ARET de production. La fixture reste test-only. Les adapters spécifiques, instructions/hooks/config générés et installation restent hors M5-C. |
| Verdict | `M5-C = PASS`; M5 reste `IN_PROGRESS`. Aucun client ne peut choisir l’adapter, fournir une commande ou promouvoir un verdict. |
| Référence | `50cc79a`; `tests/test_mcp_adapter_registry.py`; `tests/test_mcp_stdio_verdict_transport.py`; `MEM-DEC-131`. |

### LOG-0185 — 2026-08-26 — M5-D : premier adapter MCP de production du Pack ARET
| Champ | Valeur |
|---|---|
| Type | `PATCH` / `TEST` / `VERDICT` |
| But | Transformer le mécanisme M5-C en premier runtime de Pack concret, sans introduire de dépendance ARET dans la façade, le manifeste ou le registry génériques. |
| Patch | `e073fa2` ajoute `domain_packs/aret/mcp_adapter.py` et `mcp_runtime.py`. `AretClosedOracleMCPAdapter` a l’ID fermé `aret-closed-oracle-v1` et délègue exclusivement chaque capability canonique `aret-oracle-*` au runner `run_closed_oracle`. |
| Entrées | Le Pack accepte seulement la capability déclarée et le champ `fixture` lorsque le contrat de l’oracle l’autorise. Commande, verdict, stdout, stderr, code de sortie, score et artifact client restent refusés avant le runner. |
| Hôte | `build_aret_mcp_runtime` instancie adapter→registry→manifest→façade. Il extrait les seules capabilities `ALLOW` du Pack puis demande au compilateur M5-B de couvrir le catalogue complet; une capability ALLOW étrangère et sans adapter fait donc refuser le démarrage. |
| Persistence | Le runner Pack conserve préflight, commit toolkit, propreté, binaire attesté, sandbox `unshare`, asset/execution/evidence. L’adapter n’ajoute qu’un work item/gate lié à la même evidence, sans admission ni proof implicite. |
| Test réel | Un vrai client stdio démarre l’hôte ARET, vérifie le catalogue `aret-oracle-difftest`, tente `parameters.command` (refus), exécute la capability, puis obtient `PASS` → validation asset `PASS` → admission `ADMITTED` → gate `PASS`. Le résultat de processus reste déterminé côté serveur. |
| Contrôles | Rouge : adapter puis runtime/fixture absents. Verts : `4 passed` adapter/runtime, `1 passed` vrai stdio, `21 passed, 12 subtests passed` ciblés. Suite complète : `413 passed, 37 subtests passed`. Scan Core sans import Pack/ARET, wheel isolée avec modules Pack : `PASS`. |
| Limite | L’hôte est une API de composition Python attestée, pas encore une configuration installable issue d’un profile. La fixture stdio utilise un runner déterministe de test; elle ne démontre pas la réussite locale des oracles ARET ni ne modifie ARET-MMU. |
| Verdict | `M5-D = PASS`; M5 reste `IN_PROGRESS`. La façade générique demeure fail-closed sans hôte de Pack explicitement assemblé. |
| Référence | `e073fa2`; `tests/test_aret_mcp_adapter.py`; `tests/test_aret_mcp_runtime.py`; `tests/test_aret_mcp_stdio_runtime.py`; `MEM-DEC-132`. |

### LOG-0186 — 2026-08-26 — M5-E : instructions MCP manifest-bound et vérifiées
| Champ | Valeur |
|---|---|
| Type | `PATCH` / `TEST` / `VERDICT` |
| But | Remplacer, pour les runtimes explicitement assemblés, la doctrine MCP générique non attestée par une instruction compilée depuis le snapshot M5-B courant. |
| Patch | `9010293` ajoute `mcp_instructions.py` et le format `vera-mcp-instructions/v1`. Le compilateur vérifie d’abord le manifeste contre le Store puis produit un texte canonique et `instructions_hash=SHA-256(text)`. |
| Contenu | Le texte contient seulement l’identité projet du manifeste, son `mcp_build_hash`, la doctrine universelle VERA et les capacités manifestées sous la forme `id | kind | runner | network | timeout | adapter`. Il ne lit aucun fichier, playbook, Pack, runtime ou résultat externe. |
| Fermeture | Le compilateur refuse store/manifest invalides ou périmés. `create_server` refuse toute instruction sans manifeste, d’un autre type ou distincte de la recompilation exacte. Ni un client MCP ni un hôte ne peuvent substituer un texte qui ne correspond pas au snapshot attesté. |
| Application | `build_aret_mcp_runtime` compile et attache les instructions M5-E avant de créer la façade; l’entry point générique conserve son texte statique seulement lorsqu’aucun manifeste/hôte n’est configuré et demeure incapable d’exécuter. |
| Tests | Rouge : module absent, puis option façade absente. Vert : stabilité texte/hash, identité et `mcp_build_hash` inclus, absence de vocabulaire ARET, manifeste périmé refusé, hash de manifeste discordant refusé par la façade, runtime ARET et vrai client stdio non régressés. |
| Contrôles | Ciblés : `6 passed`. Suite complète : `416 passed, 37 subtests passed`. Scan `mcp_instructions.py` sans Pack/ARET/shell/réseau; roue isolée avec module et entry points : `PASS`; `git diff --check` : `PASS`. |
| Limite | Les instructions de playbook, de reprise, hooks et configuration d’installation ne sont pas encore compilées. M5-E établit la couche universelle minimale attestée; aucune doctrine spécifique ARET n’est transférée au Core. |
| Verdict | `M5-E = PASS`; M5 reste `IN_PROGRESS`. |
| Référence | `9010293`; `tests/test_mcp_instructions.py`; `src/vera_mmu/mcp_instructions.py`; `MEM-DEC-133`. |

### LOG-0187 — 2026-08-26 — M5-F : prévisualisation d’intégration MCP manifest-bound
| Champ | Valeur |
|---|---|
| Type | `PATCH` / `TEST` / `VERDICT` |
| But | Produire la première configuration MCP project-localisée depuis les snapshots M5-B/E, sans écrire `.mcp.json`, hooks ou code métier avant l’existence d’un installateur attesté. |
| Patch | `5dab574` ajoute `mcp_integration.py` et le format `vera-mcp-integration/v1`. Il vérifie manifeste et instructions, puis produit JSON canonique et `config_hash=SHA-256(json_text)`. |
| Sortie | La prévisualisation contient un unique serveur `vera-mmu-<project_id>`, `command: vmmu-mcp`, `args: [--profile, ${CLAUDE_PROJECT_DIR:-.}/<profile relatif>]` et environnement descriptif `VERA_PROJECT_ID`, `VERA_MCP_BUILD_HASH`, `VERA_MCP_INSTRUCTIONS_HASH`. |
| Confinement | Le seul write-path est `<runtime>/generated/mcp.json`, créé en mode exclusif. Une seconde écriture échoue; `.mcp.json`, `.claude/`, le profil et le code métier ne sont jamais modifiés. |
| Fermeture | Le compilateur refuse Store, manifeste, instruction, identité, profile path ou snapshot incohérents. La configuration ne transporte ni commande libre, chemin d’exécutable, adapter, verdict, résultat, artifact, secret ou hook. |
| Portée réelle | Le JSON cible l’entry point générique VERA, donc fail-closed sans hôte Pack explicite. Les variables de hash sont descriptives dans cette tranche; aucun lanceur/installeur n’est encore autorisé à les substituer à la vérification server-side M5-B/E. |
| Tests | Rouge : module absent. Vert : JSON stable, champs standard bornés, manifest+instruction liés, dérive de catalogue refusée, preview runtime exclusive et zéro `.mcp.json` créée. |
| Contrôles | Ciblés : `3 passed`. Suite complète : `419 passed, 37 subtests passed`. Scan de `mcp_integration.py` sans Pack/ARET/shell/réseau; roue isolée et entry points : `PASS`; `git diff --check` : `PASS`. |
| Limite | Hooks, fusion/idempotence de `.mcp.json`, configuration d’hôte Pack installable, validation du client configuré et approbations runtime restent ouverts. |
| Verdict | `M5-F = PASS`; M5 reste `IN_PROGRESS`. |
| Référence | `5dab574`; `tests/test_mcp_integration_config.py`; `src/vera_mmu/mcp_integration.py`; `MEM-DEC-134`. |

### LOG-0188 — 2026-08-26 — M5-G : plan de hook SessionStart déclaratif
| Champ | Valeur |
|---|---|
| Type | `PATCH` / `TEST` / `VERDICT` |
| But | Préparer le cycle de session à partir des artefacts MCP attestés, sans importer les scripts/hooks ARET et sans faire croire qu’un hook runtime existe déjà dans VERA. |
| Audit | VERA ne possède ni resume service ni hook runtime. La forme ARET comporte des commandes spécifiques `SessionStart`, compactage, garde de reprise et stop; aucune ne peut être portée mécaniquement dans le Core universel. |
| Patch | `ea7235a` ajoute `mcp_hooks.py` et `vera-mcp-hooks/v1`. `compile_mcp_hook_plan` revalide manifest, instructions et config M5-F, puis produit un JSON canonique contenant seulement `hookPlan.SessionStart`. |
| Contrat | L’événement déclare `mode=DECLARATIVE_ONLY`, `delivery=HOST_ADAPTER_REQUIRED`, `instruction_source=ATTESTED_MCP_INSTRUCTIONS`. Il ne comprend aucune commande, script, chemin, capability, résultat, verdict, artifact ou secret. |
| Confinement | La prévisualisation ne peut écrire que `<runtime>/generated/hooks.json` en mode création exclusive. Elle ne crée ni `.claude/settings.json`, ni script, ni sous-dossier hooks, ni modification de code métier. |
| Fermeture | Toute divergence de Store, manifeste, instructions ou configuration fait échouer la compilation. Une seconde écriture de preview échoue; le plan ne peut pas être traité comme un hook exécutable. |
| Tests | Rouge : module absent. Vert : stabilité du texte/hash, valeurs SessionStart exactes, absence de `command`/ARET, config périmée refusée, preview runtime exclusive et zéro réglage Claude créé. |
| Contrôles | Ciblés : `3 passed`. Suite complète : `422 passed, 37 subtests passed`. Scan `mcp_hooks.py` sans Pack/ARET/shell/réseau; roue isolée et entry points : `PASS`; `git diff --check` : `PASS`. |
| Limite | Un adapter spécifique à l’hôte et un installateur opt-in doivent encore traduire ce plan en hooks réellement exécutables. Resume, acknowledgement et checkpoint ne sont pas revendiqués par M5-G. |
| Verdict | `M5-G = PASS`; M5 reste `IN_PROGRESS`. |
| Référence | `ea7235a`; `tests/test_mcp_hook_plan.py`; `src/vera_mmu/mcp_hooks.py`; `MEM-DEC-135`. |

### LOG-0189 — 2026-08-26 — M5-H : adapter de revue Claude Code attesté
| Champ | Valeur |
|---|---|
| Type | `PATCH` / `TEST` / `VERDICT` |
| But | Traduire les artefacts universels M5-B/E/F/G vers un plan cible Claude Code, sans appliquer de configuration, injecter de script ou transformer un hook déclaratif en commande. |
| Patch | `8b38b1b` ajoute `claude_code_integration.py` et le format `vera-claude-code-integration/v1`. Il recompile manifest, instructions, config et plan de hooks contre le Store avant de produire le plan. |
| Cible MCP | Le plan désigne uniquement `.mcp.json` avec `content_sha256=config_hash`. Le contenu effectif demeure le JSON standard M5-F ; le plan n’introduit ni commande, ni argument, ni variable, ni chemin supplémentaire. |
| Hooks | `SessionStart` est explicitement rendu `UNTRANSLATED` / `DECLARATIVE_HOOK_REQUIRES_EXECUTABLE_ADAPTER`. L’absence d’un adapter hôte exécutable est donc un refus visible, non une installation partielle silencieuse. |
| Installation | `installation.mode=REVIEW_REQUIRED`, `writes=[]`. La seule écriture offerte est la prévisualisation `<runtime>/generated/claude-code-integration.json` en création exclusive. `.mcp.json` et `.claude/` restent intacts. |
| Fermeture | Toute divergence d’identité, manifeste, instructions, config ou hook plan est refusée. Le module ne contient ni Pack/ARET, shell, réseau, accès client ou write-path projet. |
| Tests | Rouge : module absent. Vert : plan stable, hashes des quatre snapshots, cible `.mcp.json`, hook non traduit, refus d’un snapshot périmé et preview runtime exclusive. |
| Contrôles | Ciblés : `3 passed`. Suite complète : `425 passed, 37 subtests passed`. Scan de frontière, `git diff --check`, roue isolée et points d’entrée : `PASS`. |
| Limite | L’installateur opt-in reste ouvert. Il devra vérifier ce plan puis appliquer de façon idempotente la seule cible MCP autorisée; le hook ne pourra être installé qu’après livraison d’un adapter exécutable séparé. |
| Verdict | `M5-H = PASS`; M5 reste `IN_PROGRESS`. |
| Référence | `8b38b1b`; `tests/test_claude_code_integration_adapter.py`; `src/vera_mmu/claude_code_integration.py`; `MEM-DEC-136`. |

### LOG-0190 — 2026-08-26 — M5-I : installateur MCP Claude Code opt-in et idempotent
| Champ | Valeur |
|---|---|
| Type | `PATCH` / `TEST` / `VERDICT` |
| But | Appliquer la première configuration MCP VERA dans un projet uniquement après confirmation explicite, sans installer de hook ni modifier une configuration hôte ambiguë. |
| Patch | `674929c` ajoute `claude_code_installer.py` et `install_claude_code_mcp`. Le write-path est limité à `<project_root>/.mcp.json`. |
| Liaison | L’installateur revalide manifeste, instructions, config, hook plan et plan Claude Code via recompilation depuis le Store. Toute divergence rend l’installation invalide avant écriture. |
| Opt-in | `confirm=True` est obligatoire. Sans cette valeur exacte, l’installateur refuse et aucun fichier projet n’est créé. |
| Fusion | Le JSON existant est conservé; seuls `mcpServers.vera-mmu-<project_id>` et son contenu attesté peuvent être ajoutés. Les clés et serveurs tiers restent intacts. |
| Idempotence | Si ce serveur est déjà strictement identique, résultat `UNCHANGED` et zéro réécriture. S’il diffère, le conflit est refusé et les octets existants restent inchangés. |
| Confinement | Symlink, fichier non régulier, JSON non objet, `mcpServers` non objet et cible hors root sont refusés. L’écriture est atomique et n’affecte jamais `.claude/`, hooks, scripts ou code métier. |
| Tests | Rouge : module absent. Vert : confirmation obligatoire, fusion avec serveur tiers, conservation de clés, idempotence, conflit et symlink refusés sans write. |
| Contrôles | Ciblés : `4 passed`. Suite complète : `429 passed, 37 subtests passed`. Scan de frontière, `git diff --check`, roue isolée et points d’entrée : `PASS`. |
| Limite | L’installateur n’exécute pas ni n’installe de hook. La config installée cible l’entry point générique, qui reste fail-closed sans hôte de Pack explicitement assemblé. |
| Verdict | `M5-I = PASS`; M5 reste `IN_PROGRESS`. |
| Référence | `674929c`; `tests/test_claude_code_mcp_installer.py`; `src/vera_mmu/claude_code_installer.py`; `MEM-DEC-137`. |

### LOG-0191 — 2026-08-26 — Cadrage M5 : lifecycle universel, reprise et adapters multi-hôtes
| Champ | Valeur |
|---|---|
| Type | `BASELINE` / `INSPECTION` / `DECISION` |
| But | Recadrer la suite M5 à partir du lifecycle fonctionnel ARET : démarrage, pré/post-compaction, garde de reprise, acquittement, arrêt et fonctionnement local/cloud ne doivent pas être réduits à un hook Claude isolé. |
| Baseline ARET | Inspection strictement en lecture seule de `resume_guard.py`, `common.py`, handlers SessionStart/PreCompact/PostCompact/PreToolUse/PostToolUse/Stop, config Claude, installateur, bootstrap/launcher cloud et tests de garde. Les invariants observés sont hash du dossier, sessions isolées, hard/soft, anti-deadlock, preservation contrôlée sur reprise vivante, réarmement sur vraie perte de contexte et kill-switch opérateur. |
| Baseline VERA | M5-A à M5-I fournissent façade, manifests/snapshots attestés, config, plan déclaratif et installation `.mcp.json` sûre. Le Core n’a toutefois aucun Resume Dossier, état session, garde, acquittement, adapter exécutable ni bootstrap cloud. L’installateur ne crée pas `.claude`. |
| Sources hôte | Les documentations actuelles Claude Code, Codex, Gemini CLI et Antigravity ont été consultées. Elles confirment MCP et des hooks, mais des cycles et capacités différents : Claude/Codex offrent compaction ; Gemini expose PreCompress advisory ; Antigravity n’expose pas de SessionStart/compaction dans la surface étudiée. |
| Décision | Créer un Lifecycle Core transport-neutre puis des adapters déclaratifs/manifest-bound. Les niveaux `MCP_ONLY`, `RESUME_DELIVERY`, `RESUME_GUARD_SOFT`, `RESUME_GUARD_HARD`, `COMPACTION_AWARE` et `CLOUD_BOOTSTRAPPED` seront déclarés et plafonnés par les capacités de chaque adapter. |
| Ordre | M5-J Core lifecycle ; M5-K registry/plan adapter et acknowledgement contextualisé ; M5-L Claude local ; M5-M Claude cloud ; M5-N/O/P Codex/Gemini/Antigravity ; M5-Q MCP générique. Le prochain patch autorisé est M5-J seulement. |
| Non-changement | Aucun hook, script, config hôte, bootstrap, synchronisation VCS, réseau, Pack ou code fonctionnel n’a été ajouté. ARET-MMU et le toolkit ne sont pas modifiés. |
| Contrôles | `git status --short` propre pour VERA, ARET-MMU et toolkit au contrôle terminal ; `HEAD` VERA = `f234fc6`, identique à `origin/main`. |
| Verdict | `M5-LIFECYCLE-CADRAGE = PASS` comme décision documentée ; `M5-J = PLANNED`; M5 reste `IN_PROGRESS`. |
| Référence | `MEM-DEC-138`; `artifacts/m5_universal_lifecycle_adapter_contract_2026-08-26.md`; sources hôte référencées dans l’artefact. |

### LOG-0192 — 2026-08-26 — M5-J : Lifecycle Core et Resume Guard universels
| Champ | Valeur |
|---|---|
| Type | `BASELINE` / `HYPOTHESIS` / `PATCH` / `TEST` / `VERDICT` |
| But | Extraire le mécanisme de dossier et de garde de reprise fonctionnelle ARET dans un Core VERA sans adopter un protocole d’hôte, un script ou une doctrine de Pack. |
| Hypothèse | Un dossier canonique project-bound, un état local hashé par projet/adapter/session et des décisions fermées `ALLOW`/`ALLOW_WITH_NOTICE`/`DENY`/`NUDGE` suffisent à préserver les garanties de reprise avant M5-K, sans avoir besoin d’un hook réellement installé. |
| Rouge | `tests/test_session_lifecycle.py` a d’abord produit `8 failed` par absence attendue de `vera_mmu.session_lifecycle`. |
| Patch | `e576b1a` ajoute `session_lifecycle.py` et 9 tests. `ResumeDossierService` valide sections exactes et bornées, sérialise canoniquement `vera-resume-dossier/v1`, le lie à `project_hash`/`profile_hash` et produit un SHA-256. `ResumeGuardService` écrit un état éphémère atomique sous runtime, auditant armement/acquittement sans persister le texte du récapitulatif dans SQLite. |
| Hard/soft | Mode `HARD` : pré-action refusée jusqu’à un acquittement du hash de dossier et des sections attendues. Mode `SOFT` : notice/nudge bruyant, mais action autorisée pour éviter le deadlock. `RESUME` conserve un acquittement vivant ; `CONTEXT_RESTORED` réarme. |
| Fermeture | Session/adaptor différents sont isolés par clé hashée. Identité de session absente, dossier falsifié, hash divergent, adapter divergent, état JSON corrompu, symlink ou état non régulier sont refusés ou ne lèvent jamais la garde. |
| Frontière | Aucun import ARET/Pack, MCP, Claude, shell, commande, réseau, subprocess ou bootstrap n’est présent dans le nouveau module. Aucun fichier `.mcp.json`, `.claude/` ou script hôte n’est créé. |
| Contrôles | Ciblés : `9 passed`. Suite complète : `438 passed, 37 subtests passed`. `py_compile`, scans Core, `git diff --check` : `PASS`. `uv build --wheel`, installation isolée avec dépendances déclarées, présence du module dans la roue et `vmmu`/`vmmu-mcp --help` : `PASS`. |
| Note packaging | Une première installation délibérément `--no-deps` a échoué à l’entrée CLI faute de PyYAML ; la roue déclare cette dépendance. La validation isolée réexécutée avec dépendances déclarées est `PASS`; ce n’est pas une régression M5-J. |
| Verdict | `M5-J = PASS`; M5 reste `IN_PROGRESS`. |
| Référence | `e576b1a`; `tests/test_session_lifecycle.py`; `src/vera_mmu/session_lifecycle.py`; `MEM-DEC-139`; `artifacts/m5_universal_lifecycle_adapter_contract_2026-08-26.md`. |

### LOG-0193 — 2026-08-26 — M5-K : registry lifecycle attesté et acquittement MCP contextualisé
| Champ | Valeur |
|---|---|
| Type | `BASELINE` / `HYPOTHESIS` / `PATCH` / `TEST` / `VERDICT` |
| But | Relier M5-J à MCP sans hook : attester un contexte hôte déjà instancié et acquitter le dossier réellement armé, sans accepter session/adapter/hash/verdict depuis le client. |
| Rouge | `5 failed` : module `lifecycle_adapters` et fixture stdio M5-K absents ; aucune capacité implicite n’était disponible. |
| Patch | `df73425` ajoute `vera-lifecycle-adapter-plan/v1`, hashé et project-/manifest-bound ; `LifecycleAdapterRegistry` immutable valide id/version/mode, refuse vide/doublon/absence/divergence et ne charge rien dynamiquement. |
| Liaison MCP | `TOOL_NAMES` contient désormais huit tools, dont `mmu_acknowledge_resume(sections)`. La façade exige registry+plan ensemble, les résout au démarrage, reçoit l’identité uniquement par `session_identity()` côté hôte et appelle `acknowledge_current`, qui relit le hash depuis l’état local. |
| Fermeture | Le schema du tool n’expose que `sections`; session, adapter, version, hash, verdict, statut, commande et chemin ne sont pas des entrées. Une clé d’injection placée dans les sections est refusée; les clés MCP externes inconnues sont filtrées par le SDK et ne peuvent pas changer le contexte hôte. |
| Harness | `mcp_lifecycle_fixture_server.py` est un serveur de test générique, sans Pack, qui arme une session fixée au démarrage. Il démontre le chemin réel `ClientSession` stdio; ce n’est ni un adapter de production ni un hook. |
| Contrôles | Ciblés : `22 passed, 7 subtests passed`. Suite complète : `444 passed, 37 subtests passed`. `py_compile`, scans anti-ARET/Pack/hôte/shell/réseau, `git diff --check` : `PASS`. Roue isolée avec dépendances, inclusion `lifecycle_adapters.py`, `vmmu --help`, `vmmu-mcp --help` : `PASS`. |
| Verdict | `M5-K = PASS`; M5 reste `IN_PROGRESS`. |
| Limite | Aucun adapter réellement installable, hook, `.claude`, `.mcp.json`, wrapper, doctor, bootstrap cloud ou événement host lifecycle n’est livré. M5-L reste l’adapter Claude Code local séparé et opt-in. |
| Référence | `df73425`; `MEM-DEC-140`; `tests/test_lifecycle_adapter_registry.py`; `tests/test_mcp_lifecycle_acknowledgement.py`; contrat M5 lifecycle et registre M5 central. |

### LOG-0194 — 2026-08-26 — M5-L : adapter Claude Code local attesté, hooks opt-in et doctor
| Champ | Valeur |
|---|---|
| Type | `BASELINE` / `HYPOTHESIS` / `PATCH` / `TEST` / `VERDICT` |
| But | Livrer le premier adapter d’hôte concret sans transférer le bootstrap/sync/cloud ARET : Claude Code local project-bound, SessionStart/PreToolUse/compaction/Stop, installateur opt-in et doctor observationnel. |
| Sources hôte | La documentation Claude vérifiée décrit `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `PostCompact`, `Stop`, JSON stdin/stdout et `permissionDecision: deny`; les settings projet sont `.claude/settings.json`. Les scopes home/cloud sont volontairement exclus. |
| Rouge | `5 failed` : `vera_mmu.claude_code_local` absent ; aucun plan/hook/installateur/doctor local n’était disponible. |
| Patch | `45fe9af` ajoute `claude_code_local.py`, `vmmu-claude-code-local-hook` et `vmmu-claude-code-local-mcp`. Le plan `vera-claude-code-local/v1` est hashé et lie manifeste, instructions, config, hook plan, revue, lifecycle et bindings d’adapters. |
| Hooks | SessionStart lie une session locale unique au runtime, arme M5-J et injecte le dossier. PreToolUse bloque par `permissionDecision: deny` tant que le dossier n’est pas acquitté, en autorisant seulement le nom MCP exact `mmu_acknowledge_resume`; Pre/PostCompact réarment; Stop nudges puis libère la liaison. |
| MCP | Le serveur local relit l’état installé, recrée le manifeste depuis les bindings attestés et résout l’adapter session local. Il ne sélectionne aucun Pack et conserve `DenyRuntimeAdapter` pour toutes capabilities. Le client MCP ne fournit toujours ni session, adapter, hash, verdict, commande ou chemin. |
| Installation | `confirm=True` requis; fusion atomique non destructive des seuls hooks VERA dans `.claude/settings.json`; remplacement uniquement du serveur VERA générique par le serveur local attesté dans `.mcp.json`; état install hashé sous runtime. Conflit, JSON ambigu, symlink ou état divergent : refus sans écriture. |
| Doctor | `NOT_INSTALLED`/`DEGRADED`/`READY`, sans création de `.claude` ou du runtime, ni installation/téléchargement/approbation. `READY` requiert settings, MCP, état et les deux entry points disponibles. |
| Conformance | `test_claude_code_local_adapter.py` couvre plan, stale, hard guard, exception d’acquittement, compaction, session conflict, merge, idempotence, symlink et doctor. `test_claude_code_local_hook_cli.py` exécute le hook stdin/stdout; `test_claude_code_local_mcp_runtime.py` prouve hook→vrai stdio MCP→acquittement→PreTool allow. |
| Contrôles | Ciblés : `7 passed`. Suite complète : `451 passed, 37 subtests passed`. `py_compile`, scans anti-domaines/réseau/shell/bootstrap, `git diff --check` : `PASS`. Roue isolée : module et `vmmu`, `vmmu-mcp`, hook local, MCP local : `PASS`. |
| Verdict | `M5-L = PASS`; M5 reste `IN_PROGRESS`. |
| Limite | Une session locale active par projet est supportée et les conflits sont refusés; aucun cloud, home settings, trust/setup, réseau, bootstrap, sync/push, Pack réel ou autre IA n’est livré. |
| Référence | `45fe9af`; `MEM-DEC-141`; contrat lifecycle M5; registre MCP M5. |
