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


## LOG-0195 — 2026-08-26 — M5-M.1 : plan Claude Code cloud attesté et doctor préinstallé

### Intention

Après M5-L local, utiliser les garanties observées d’ARET cloud sans recopier ses scripts ni faire glisser dans le Core une dépendance réseau, de secret, de trust ou de Pack. Le scope M5-M.1 est volontairement non exécutable : compilation du plan cloud et diagnostic observationnel du seul runtime préinstallé.

### Hypothèse

Un plan cloud `vera-claude-code-cloud/v1` peut être lié aux snapshots M5-B/E/F/G/H/J/K/L et distinguer `RUNTIME_MISSING`, trust pending/disabled/unverifiable et runtime déclaré, sans écrire sous `$HOME`, démarrer un hook, installer une dépendance ou consulter un secret.

### Preuves

1. Lecture ARET : le bootstrap historique sépare chemin chaud/froid, sérialisation et vérification d’import ; son installation cloud associe préchauffage et approbation user-scope. Ces mécanismes sont pris comme besoins fonctionnels, non comme code à porter.
2. Sources officielles Claude Code vérifiées : cloud environments, setup script et paramètres ; `.mcp.json` de projet non trusted ne peut pas s’auto-approuver ; les approbations user/managed sont distinctes.
3. Cycle rouge : `tests/test_claude_code_cloud_plan.py` a produit `4 failed` (`ModuleNotFoundError`) avant module M5-M.1.
4. Implémentation : `claude_code_cloud.py` compile le provider unique `PREINSTALLED_VERA`, réseau `FORBIDDEN`, trust `PREVIEW_ONLY`, secrets `EXTERNAL_ONLY`, serveur cloud déclaratif et doctor sans effet de bord. Provider `NETWORK_BOOTSTRAP`, observations invalides/non-cloud, snapshots stale et runtime/trust ambigus sont refusés ou dégradés.
5. Cycle vert : M5-M.1 `4 passed`; matrice locale/cloud concernée `11 passed`; suite complète `455 passed, 37 subtests passed`.
6. Qualité : compilation Python, scans sans Pack/ARET/shell/réseau/bootstrap/write-path dans le module cloud et `git diff --check` `PASS`.
7. Distribution : roue isolée construite et installée avec dépendances déclarées ; import `vera_mmu.claude_code_cloud`, `vmmu --help` et `vmmu-mcp --help` `PASS`; module présent dans la roue.

### Décision

Le commit fonctionnel `940fb7e` livre seulement le plan et le doctor M5-M.1. `RUNTIME_READY` décrit la cohérence d’un runtime préinstallé et d’un fait de trust déclaré ; il ne signifie pas que le hook, la connexion MCP, le setup ou une session Claude Code web réelle sont prouvés. Le secret ARET divulgué antérieurement n’est ni lu, ni stocké, ni copié dans VERA.

### Limites et suite

M5-M.2 devra être un contrat séparé pour runtime cloud effectivement distribuable/hook réel, puis test live Claude Code web. La roue attestée, le bootstrap réseau et le write-path `$HOME/.claude/settings.json` sont distincts. Toute écriture user-scope impose preview et double confirmation transactionnelle ; elle est hors M5-M.1.


## LOG-0196 — 2026-08-26 — M5-M.2 : adapter Claude Code cloud staged, hook/MCP distribués

### Intention

Faire passer M5-M.1 du plan cloud attesté au premier adapter cloud distribuable, sans reproduire un script ARET de setup, ni permettre un bootstrap réseau, un trust user-scope ou une configuration host implicite.

### Cycle de preuve

1. Contrat écrit avant patch : staging confirmé sous runtime VERA, adapter cloud distinct, hook stdin/stdout, serveur MCP deny-by-default et session project-bound ; aucun home/trust/réseau/secret.
2. Cycle rouge : `tests/test_claude_code_cloud_runtime.py` produit `2 failed` car le staging et les entry points cloud sont absents.
3. Implémentation : `claude_code_cloud.py` reçoit `ClaudeCodeCloudSessionAdapter`, staging atomique `vera-claude-code-cloud-runtime/v1`, binding cloud distinct, hook des six événements, serveur MCP stdio et commandes `vmmu-claude-code-cloud-{stage,hook,mcp}`. Le staging CLI construit des bindings symboliques `cloud-deny-v1` depuis le catalogue ALLOW persistant ; aucun adapter, hash, session ou secret n’est accepté en argument client.
4. Conformance : staging impose `confirm=True`, ne crée ni `.claude` ni `.mcp.json`; SessionStart arme, PreToolUse refuse, vrai client MCP acquitte seulement les sections, PreToolUse devient autorisé, PostCompact réarme le refus.
5. Validation : tests plan/runtime `6 passed`, matrice lifecycle Claude/MCP `19 passed`, suite `457 passed, 37 subtests passed`; compilation, scan sans Pack/ARET/shell/réseau/bootstrap/home access, `git diff --check` et roue isolée passent. Les trois entry points cloud sont présents dans la roue.

### Décision

Le commit fonctionnel `f79415b` livre le runtime cloud **staged**, pas la configuration Claude Code web. Le serveur utilise `DenyRuntimeAdapter` : aucune capability Pack n’est exécutée. Le staging est project-local, idempotent et confirmé ; il ne vaut ni installation de hook, ni trust, ni connexion MCP host, ni préparation de dépendance.

### Limite et wall

La preuve cloud web reste `NOT_RUN`, faute d’environnement Claude Code web attesté et de write-path séparé pour les settings/hooks de projet et l’approbation user-scope. Ce n’est pas masqué : le protocole `m5_claude_code_cloud_live_proof_protocol_2026-08-26.md` documente les préconditions, les assertions et les verdicts attendus. Le prochain sous-lot doit traiter preview/merge/refus/double-confirmation de configuration/trust, puis exécuter cette preuve live. Aucun bootstrap par roue ni réseau n’est autorisé par ce lot.

## LOG-0197 — 2026-08-26 — M5-M.3a : preview/fusion project-local Claude cloud

### Intention

Fermer uniquement la préparation hôte project-local nécessaire au hook/MCP M5-M.2 : construire un preview attesté, préserver les déclarations tierces, refuser les conflits et appliquer les fichiers de projet après confirmation, sans transformer cette opération en trust Claude Code web.

### Cycle de preuve

1. Baseline : `8955045` publié ; runtime M5-M.2 staged disponible, mais aucune configuration `.claude`/`.mcp.json` ni preuve web.
2. Recherche : la documentation officielle confirme que les hooks et serveurs MCP du dépôt peuvent atteindre les sessions cloud, alors que les réglages utilisateur locaux ne le peuvent pas ; elle confirme aussi qu’un projet non trusted ne s’auto-approuve pas.
3. Cycle rouge : `3 failed` — import des opérations preview/application absent.
4. Implémentation : `ClaudeCodeCloudHostConfigPreview`, fusion canonique des six hooks et du serveur cloud, hash du couple JSON, état `vera-claude-code-cloud-host-config/v1`, écriture atomique project-local et entry point `vmmu-claude-code-cloud-config`.
5. Refus : runtime absent/périmé, JSON non objet, conflit hook/MCP VERA, symlink, changement entre preview/apply, état divergent et confirmation absente refusent. L’API ne reçoit pas de chemin home ni de donnée user-scope.
6. Validation : tests cloud `7 passed`; suite `462 passed, 37 subtests passed`; compilation, diff/checks de frontière et roue isolée avec quatre entry points cloud passent.

### Décision

Le commit fonctionnel `ed9f2e8` rend M5-M.3a `PASS` pour **le preview, la fusion et l’application project-local contrôlée**. Il ne prouve pas Claude Code web : aucune session host réelle, aucun chargement effectif des fichiers, aucune connexion MCP trustée et aucun événement host n’ont été observés dans ce lot.

### Limites et suite

Le statut de l’approbation user-scope est `NOT_DELIVERED` par construction. M5-M.3b devra être un nouveau contrat : preview non secret de la modification user-scope, détection de conflit, puis double confirmation explicite et transactionnelle avant toute écriture sous `$HOME/.claude/settings.json`. Après seulement, une session cloud fraîche pourra suivre le protocole de preuve live. Secrets, setup, roue/bootstrap et réseau restent hors périmètre.

## LOG-0198 — 2026-08-27 — M5-M.3b : trust MCP user-scope préparé, double confirmation

### Intention

Préparer, sans l’exécuter dans l’environnement réel, le seul write-path user-scope nécessaire à l’approbation d’un serveur MCP VERA déclaré par le projet cloud. Cette préparation doit rester distincte de la configuration project-local M5-M.3a, de la présence d’un fichier dans le home et du trust effectivement constaté par Claude Code web.

### Cycle de preuve

1. Recherche officielle : un repository non trusted ne s’auto-approuve pas via ses réglages committés ; les approbations user/managed/`--settings` sont cependant des voies reconnues par l’hôte. Les settings user ont une portée machine et ne constituent pas à eux seuls une preuve d’une session cloud.
2. Cycle rouge : `3 failed`, car le preview et l’application user-scope n’existaient pas.
3. Implémentation : preview `vera-claude-code-cloud-user-trust/v1` lié au reçu M5-M.3a, fusion de la seule entrée `enabledMcpjsonServers`, refus de `disabledMcpjsonServers` et `Path.home()` comme chemin fixe sans argument client.
4. Double gate : `apply_claude_code_cloud_user_trust` exige exactement `confirm_preview=True` et `confirm_user_scope=True`, revalide le preview contre le fichier courant puis écrit atomiquement. La CLI sépare `--preview-user-scope` de `--apply-user-scope --confirm-preview --confirm-user-scope`.
5. Conformance : home temporaire patché, absence du reçu M5-M.3a, conflit disabled, préservation de réglages tiers, symlink, chaque confirmation isolée et preview CLI sans écriture sont couverts.
6. Validation : tests runtime `11 passed`, suite `465 passed, 37 subtests passed`; compilation, scans, `git diff --check` et roue isolée passent.

### Décision

Le commit fonctionnel `3f26dad` rend M5-M.3b `PASS` pour le **mécanisme de preview/fusion et ses garde-fous sous home simulé**. Il ne qualifie pas une écriture réelle, un trust host ou une compatibilité Claude Code web : ils restent `NOT_RUN`.

### Limite et prochain acte

Aucun chemin user-scope réel n’a été lu ni écrit par les validations. L’acte suivant doit être opératoire et non automatique : montrer le preview de l’environnement cible, puis demander deux confirmations utilisateur explicites et distinctes immédiatement avant l’écriture. Après seulement, contrôler le statut MCP réel et suivre le protocole de session fraîche. Aucun réseau, setup, secret ou bootstrap n’est autorisé.


## LOG-0199 — 2026-08-27 — M5-N : adapter Codex lifecycle à couverture bornée

**Hypothèse.** Codex peut recevoir l’adapter lifecycle universel VERA sans copier la logique Claude, à condition de limiter le claim aux événements et tools réellement documentés par le host.

**Sources vérifiées.** Les références officielles Codex consultées le 2026-08-27 documentent les fichiers `.codex/hooks.json` et `.codex/config.toml`, les événements `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `PostCompact` et `Stop`, les serveurs MCP stdio et la revue/trust obligatoire des hooks non managed. Elles indiquent aussi que des tools hosted ou chemins spécialisés échappent au chemin hook. Le niveau de garantie retenu est donc `PARTIAL_LOCAL_TOOLS`, pas `HARD` universel.

**Changement fonctionnel.** Le commit `588c886` ajoute `codex_adapter.py`, `tests/test_codex_adapter.py` et les commandes `vmmu-codex-stage`, `vmmu-codex-hook`, `vmmu-codex-mcp`, `vmmu-codex-config`. Le runtime staged recompile et revérifie le manifeste, les instructions, l’intégration, le plan de hooks et l’adapter lifecycle `codex-v1`. Le serveur MCP ne permet que l’acquittement lifecycle au-dessus de `DenyRuntimeAdapter`.

**Tests et contrôles.** Cycle rouge : trois tests échouent avant l’implémentation. Chaîne M5-N : `4 passed` après staging, conservation de configuration tiers, conflit, symlink, application confirmée, hook JSON, MCP stdio réel, acquittement et réarmement PostCompact. Suite VERA : `470 passed, 37 subtests passed`. Compilation, `git diff --check`, scans absence ARET/réseau/bootstrap/home/auto-approve dans l’adapter : `PASS`. Roue isolée : `PASS` pour les quatre entry points Codex. Présence du client : `CODEX_PRESENT=NO` ; aucune installation ni connexion n’a été lancée.

**Verdict.** `PASS` pour le mécanisme contrôlé et distribué ; `NOT_RUN` pour l’observation par Codex réel, la revue/trust du host et les outils non interceptés. Les fichiers `~/.codex/`, le réseau, bootstrap, secrets, OAuth et auto-approbation restent hors portée.

**Suite.** Poursuivre M5-O (Gemini) en conservant un adapter/version/contrat distinct ; ne pas conclure à une équivalence Codex/Gemini/Claude.


## LOG-0200 — 2026-08-27 — M5-O : adapter Gemini CLI sans réarmement post-compaction

**Hypothèse.** Gemini CLI peut utiliser le Core lifecycle et le MCP VERA pour les actions exposées au hook `BeforeTool`, sans simuler un événement de restauration de contexte que le host ne documente pas.

**Changement fonctionnel.** Le commit `7ca437e` ajoute `gemini_adapter.py`, `tests/test_gemini_adapter.py` et `vmmu-gemini-stage`, `vmmu-gemini-hook`, `vmmu-gemini-mcp`, `vmmu-gemini-config`. Le plan versionné `gemini-cli-v1` lie le runtime aux snapshots M5. Le serveur MCP est deny-by-default et ne délivre que l’acquittement contextualisé.

**Contrat et limite.** Les événements `SessionStart`, `BeforeTool`, `AfterTool`, `PreCompress` et `SessionEnd` sont traduits. La garde est applicable aux actions remises à `BeforeTool`, mais `PreCompress` émet seulement un avis : aucun `PostCompact`, réarmement synthétique ou support durable après réduction de contexte n’est déclaré. Le niveau est `TOOL_GUARD_NO_POST_COMPACTION`.

**Tests et contrôles.** Trois tests rouges précèdent l’implémentation. Les trois tests ciblés valident staging, préservation de réglages tiers, conflit/symlink, confirmation, hook JSON, MCP stdio réel, acquittement et absence de réarmement au `PreCompress`. La suite passe à `473 passed, 37 subtests passed`; compilation, diff propre et scans no-ARET/no-network/no-bootstrap/no-home/auto-approve passent. La roue isolée expose quatre entry points. `GEMINI_PRESENT=NO`; aucune installation ni connexion n’a été tentée.

**Verdict.** `PASS` pour la chaîne VERA contrôlée et le niveau annoncé ; `NOT_RUN` pour le trust hôte, l’exécution par Gemini réel, la connexion MCP observée et tout comportement post-compaction réel.

**Suite.** Ouvrir M5-P avec Antigravity comme adapter distinct et ne pas présumer que ses événements s’alignent sur Gemini.


## LOG-0201 — 2026-08-27 — M5-P : adapter Antigravity à garde par invocation

**Hypothèse.** Antigravity peut recevoir le Core VERA sans détourner les sémantiques d’autres hôtes, si le cycle est borné aux événements d’invocation et d’outil réellement exposés.

**Changement fonctionnel.** Le commit `df03100` ajoute `antigravity_adapter.py`, `tests/test_antigravity_adapter.py` et les quatre commandes stage/hook/MCP/config. Le runtime attesté lie manifeste, instructions, intégration MCP, plan de hooks et lifecycle `antigravity-v1`; le serveur MCP ne permet que l’acquittement contextualisé au-dessus de `DenyRuntimeAdapter`.

**Contrat.** `PreInvocation` constitue l’ouverture de tour, `PreToolUse` la garde, `PostToolUse` l’observation et `Stop` la libération. La garantie est `TURN_GUARD_HARD` pour les actions réellement remises au hook. Aucun `SessionStart`, compaction ou restauration de contexte n’est synthétisé.

**Tests et contrôles.** Trois tests rouges précèdent l’implémentation. Les trois tests ciblés valident staging, conservation des extensions tiers, refus conflit/symlink, application confirmée, injection, blocage, vrai client MCP stdio, acquittement et fin de tour. La suite VERA atteint `476 passed, 37 subtests passed`; compilation, diff propre et scans no-ARET/no-network/no-bootstrap/no-home/auto-approve passent. Roue isolée et quatre entry points : `PASS`. `ANTIGRAVITY_PRESENT=NO`; aucune installation ni connexion n’a été tentée.

**Verdict.** `PASS` pour le mécanisme VERA contrôlé et `TURN_GUARD_HARD`; `NOT_RUN` pour le host Antigravity, son trust et l’observation de hooks réels.

**Suite.** Ouvrir M5-Q, adapter MCP générique, afin que tout client MCP puisse accéder de manière sûre à l’acquittement sans prétendre à une garde automatique.


## LOG-0202 — 2026-08-27 — M5-Q : fallback MCP générique `MCP_ONLY`

**Hypothèse.** Tout client MCP compatible peut recevoir une façade VERA sûre sans qu’un adapter n’invente une session, une garde pré-action ou une compaction dont le host ne fournit aucun événement attesté.

**Changement fonctionnel.** Le commit `00f6cee` ajoute `generic_mcp_adapter.py`, `tests/test_generic_mcp_adapter.py` et les commandes `vmmu-generic-mcp-stage`, `vmmu-generic-mcp`, `vmmu-generic-mcp-config`. Le runtime lie manifeste et instructions compilés; la façade MCP est créée avec `DenyRuntimeAdapter` et sans registry lifecycle.

**Contrat.** Le catalogue est disponible via le transport MCP stdio. Toute capability est refusée; l’acquittement lifecycle est également refusé en absence de contexte hôte. La configuration `.mcp.json` est project-local, non destructive et confirmée. Le niveau est `MCP_ONLY` : aucune automation lifecycle n’est promise.

**Tests et contrôles.** Trois tests rouges précèdent l’implémentation. Les tests ciblés valident staging, preview/application, conflit/symlink, vrai `ClientSession` MCP, catalogue, refus d’acquittement sans session et refus de capability. La suite VERA atteint `479 passed, 37 subtests passed`; le premier scan de mot-clé a signalé la mention descriptive de « hook » dans une docstring, puis le contrôle structurel a confirmé l’absence de handler hook, registry lifecycle et `ResumeGuardService`. La roue isolée et ses trois entry points passent.

**Verdict.** `PASS` pour le fallback VERA contrôlé. Aucun host, trust, hook, session, compaction, réseau ou exécution de capability ne peut être déduit de M5-Q.

**Suite.** Ouvrir M6 pour fédérer les operations stage/configure/validate/doctor sous une CLI diagnostique, sans déplacer les règles d’adapter dans l’interface.


## LOG-0203 — 2026-08-27 — M6-A : façade CLI et doctor observationnel

**Hypothèse.** Une CLI centrale peut améliorer l’exploitation des adapters sans déplacer leur politique, leur lifecycle ni leurs confirmations dans une nouvelle surface permissive.

**Changement fonctionnel.** Le commit `17a2bba` étend `vmmu` avec `adapter matrix`, `doctor`, `validate`, `stage` et `configure`. La matrice est statique et rend les niveaux déclarés visibles; doctor ouvre seulement le profile/workspace et constate runtime/configuration; stage/configure routent vers les entry points déjà attestés.

**Garde de portée.** La CLI générale refuse `--apply-user-scope`. Elle ne peut donc pas appeler le write-path Claude cloud à deux confirmations. Elle refuse également les adapters inconnus et les cibles doctor symlinkées. Elle n’accepte aucune commande shell, capability, verdict, hash, session, adapter interne ou chemin hôte arbitraire.

**Tests et contrôles.** Trois tests rouges précèdent le code. Les trois tests ciblés valident matrice, doctor sans création de config, stage sans confirmation, refus user-scope et adapter inconnu. La suite VERA atteint `482 passed, 37 subtests passed`; compilation, scans no-ARET/no-network/no-bootstrap/no-home et diff propre passent. La roue isolée exécute `vmmu --help`, `vmmu adapter matrix` et l’entry point fallback MCP.

**Verdict.** `PASS` pour M6-A. Dashboard visuel, auto-installation, host live, trust user-scope et preuve web restent explicitement hors lot et `NOT_RUN`/`NOT_DELIVERED`.

**Suite.** M6-A satisfait le socle CLI/doctor. Toute extension dashboard doit devenir un lot web séparé, après définition de données locales et de ses frontières de sécurité.


## LOG-0204 — 2026-08-27 — M6-B : opérations communes scan/génération/installation

**Hypothèse.** CLI, bridge local et Dashboard peuvent partager les mêmes opérations VERA si elles exposent des contrats de données, non des commandes libres ou de la logique de configuration dupliquée.

**Changement fonctionnel.** Le commit `8d59939` ajoute `project_operations.py`, `tests/test_project_operations.py`, `vmmu scan`, `vmmu generate` et `vmmu install`. `ScanReport/v1` liste seulement les marqueurs réguliers et triés d’une arborescence explicitement choisie. `GenerationPreview/v1` réunit manifeste, instructions, intégration et hook plan calculés depuis le store. `install` route seulement l’adapter déclaré de la matrice CLI.

**Garde de sécurité.** Le scan refuse une racine symlinkée, ne suit pas les symlinks, ne lit pas le contenu, n’exécute rien et ne crée pas de runtime. Le preview ne touche aucune config hôte. L’installation conserve le preview et la confirmation de l’adapter, refuse un adapter inconnu et ne fournit aucune voie user-scope, home, réseau, bootstrap, secret, capability ou commande arbitraire.

**Tests et contrôles.** Trois tests rouges précèdent le code. Ils couvrent stabilité du scan, non-suivi de symlink, route CLI, absence de runtime, déterminisme de génération, absence de `.mcp.json` avant installation, preview/install confirmé et refus adapter inconnu. La suite VERA atteint `485 passed, 37 subtests passed`; compilation, scans no-content-read/no-process/no-network/no-home et roue isolée passent.

**Verdict.** `PASS` pour les contrats/opérations M6-B contrôlés. Aucun host réel, bridge local exposé, dashboard ou write-path user-scope n’est testé ou livré.

**Suite.** Ouvrir M6-C : init guidé, templates de domaine et Agent Profiles déclaratifs, avant le Dashboard et sans modifier le Core pour ajouter un agent.


## LOG-0205 — 2026-08-27 — M6-C : bootstrap guidé et profils d’agents déclaratifs

**Hypothèse.** Un projet peut recevoir un Project Profile de départ et sélectionner un agent sans que l’interface crée une capacité, une commande ou une garantie non fournie par le Core/adapters.

**Changement fonctionnel.** Le commit `5cd679a` ajoute `agent_profiles.py`, `project_bootstrap.py`, les tests associés et `vmmu init-project`. Les profils Claude local/cloud, Codex, Gemini, Antigravity et MCP générique déclarent identifiant, adapter allowlisté, mode, couverture et événements ; les templates de domaines proposent software, data, research, documentation, game et hardware.

**Garde de sécurité.** Les champs inattendus — notamment commandes — sont refusés. Une couverture dépassant le maximum de l’adapter, un événement absent, un template/identité invalide, une racine/cible symlinkée, un preview divergent ou l’absence de `--apply --confirm` refusent. La création est strictement sous `.vera-mmu/`, atomique et idempotente seulement pour un contenu identique.

**Tests et contrôles.** Trois tests rouges précèdent le code. Ils couvrent les profils déclaratifs, le preview sans écriture, l’application confirmée, l’idempotence, la divergence et les symlinks. Suite complète `488 passed, 37 subtests passed`; compilation, scans no-network/no-shell/no-home et roue isolée passent.
**Verdict.** `PASS` pour M6-C contrôlé. Les templates ne sont pas une preuve, et aucune installation/test d’agent réel, dashboard ou bridge local n’a été exécuté.
**Suite.** Construire M7 : Dashboard React séparé consommant les contrats M6-B/C via un bridge local borné ; une initialisation de projet web dédiée précédera le développement de l’interface.
## LOG-0206 — 2026-08-27 — M7-B : bridge desktop stdio et continuité Git project-local
**Hypothèse.** Une application desktop peut préparer et installer l’intégration MCP dans le projet choisi sans accorder de filesystem ou shell générique à son interface, si un sidecar VERA stdio fixe la racine native et ne route que les opérations existantes en entrée fermée.
**Baseline.** `origin/main` et `HEAD` étaient `6e29f8b1b2a60aea7c3f1b274d67528acd7c81fe` avant le lot. La consultation de la documentation Tauri confirme le modèle de sidecar embarqué, les capacités explicites par WebView et la nécessité de builds cibles pour les binaires sidecar ; aucun packaging ni installation Tauri n’a été exécuté.
**Tests rouges.** `tests/test_desktop_bridge.py` a d’abord échoué en l’absence de module bridge. Les scénarios spécifient enveloppe/version/nonce stricts, limite de taille, racine non fournie par l’interface, opérations fermées, preview d’initialisation caché + confirmation, et parcours MCP générique avec preview périmé refusé.
**Changement fonctionnel.** Le commit `57279e1` ajoute `desktop_bridge.py`, l’entry point `vmmu-desktop-bridge` et `adapter_catalog.py`. Le bridge ne démarre aucun réseau : il lit une ligne JSON, route scan, init preview/apply, Agent Profiles, generate, stage, install preview/apply et doctor, puis retourne une ligne JSON. La CLI consomme le même catalogue d’adapters immuable.
**Garde de sécurité.** Le parent fournit une racine réelle non symlinkée et un nonce privé ; l’interface ne peut pas fournir de chemin, shell, adapter brut, contenu, verdict, résultat, artifact ou hash de confiance. Les profils d’agents sont résolus depuis le catalogue VERA intégré. L’application exige un preview caché, `confirm: true` et une revalidation ; un changement de configuration après preview retourne `PREVIEW_STALE` sans écriture. Les configurations restent project-locales et les writes user-scope ne sont pas routés.
**Continuité Git corrigée.** La mémoire `.vera-mmu/memory.sqlite` est confirmée comme état project-local versionnable avec le dépôt : Git/GitHub peut donc la transporter vers une nouvelle session, où le MCP local retrouve le contexte du checkout. Le bridge/MCP ne fait aucun pull/push réseau implicite et tout conflit SQLite doit rester un refus explicite.
**Tests et contrôles.** Tests ciblés bridge/opérations : `8 passed`. Suite complète : `493 passed, 37 subtests passed`. `git diff --check` passe ; scan de frontière sur bridge/catalogue ne trouve aucune référence ARET, Wine, Ghidra, MinGW ou PE32. La roue isolée contient `vmmu-desktop-bridge` et un scan stdio exécute correctement hors du checkout ; SHA-256 : `fc0975912fcb623c8b3045cf288bceda887521358ec0e365156d2c3166099234`.
**Verdict.** `PASS` pour le bridge desktop stdio borné et le parcours MCP générique contrôlé. L’application Tauri, les installeurs Windows/Linux, la signature, les fixtures multi-domaines et tout test d’hôte réel restent `NOT_RUN`.
**Suite.** Mettre à jour l’architecture de partage Git de la mémoire SQLite, puis construire l’enveloppe desktop sur le protocole stdio sans exposition de permission filesystem/shell au frontend.

## LOG-0207 — 2026-08-27 — M7-C : synchronisation mémoire Git bornée et enveloppe Tauri Linux
**Hypothèse.** La continuité ARET peut être préservée dans VERA si une mutation SQLite réussie déclenche une synchronisation Git limitée à `.vera-mmu/`, sans confier de remote, branche, commande ou chemin aux clients, et sans rétrograder le résultat métier quand Git échoue.
**Baseline.** Le bridge M7-B publié à `57279e1` assure déjà le transport stdio fermé et l’installation project-local depuis previews. La mémoire `.vera-mmu/memory.sqlite` est reconnue project-local et versionnable par Git ; l’ancienne formulation excluant toute synchronisation MCP réseau est supersédée par `MEM-DEC-155`.
**Tests rouges.** `tests/test_memory_sync.py` a d’abord échoué faute de module, puis faute de déclencheur stocké après transaction. Les scénarios couvrent policy désactivée, policy inconnue, symlink cassé, base WAL, remote absent, changement métier non ajouté, commit/push de la branche courante vers un bare remote local et identifiant d’opération invalide. Les tests CLI/MCP/bridge ont d’abord refusé l’opération non encore routée.
**Changement fonctionnel.** `memory_sync.py` impose `vera-memory-sync-policy/v1`, `origin` et `CURRENT`. `MemoryStore.transaction()` conserve le statut de tentative après son commit outer ; `mcp_server.py` ne tente la synchronisation qu’après des mutations MCP réussies. La CLI ajoute `vmmu memory-sync`, le MCP `mmu_sync_memory()` sans entrée et le bridge `memory.sync` avec objet vide. L’initialisation VERA prévisualise la policy sous `.vera-mmu/sync-policy.json` ; l’application Tauri affiche l’action typée sans plugin filesystem/shell frontend.
**Garde de sécurité.** Les opérations Git ont des arguments fixes, un timeout, un pathspec `.vera-mmu/`, un checkpoint WAL et des refus explicites pour les entrées/politiques/chemins ambigus. Un échec Git devient `REFUSED` ou `ERROR` dans le statut de sync ; il ne transforme jamais une transaction Core déjà committée en succès différent, ni en échec rétroactif. Les fields `remote`, `branch`, `path` et `command` restent absents des surfaces client.
**Tests et contrôles.** Tests ciblés sync/CLI/MCP/bridge : `18 passed`. Suite VERA : `500 passed, 37 subtests passed`. `pnpm build`, `cargo test` et `cargo check` passent pour `apps/desktop`. Le script versionné construit le sidecar PyInstaller Linux ; Tauri produit `VERA-MMU_0.1.0_amd64.deb` contenant `usr/bin/vmmu-desktop-bridge`, dont l’extraction répond à un `project.scan` stdio. Les outputs PyInstaller/Tauri/dependencies sont exclus de Git.
**Verdict.** `PASS` pour la synchronisation Git automatique limitée à la mémoire VERA et pour la source/app packaging Debian debug contrôlés. Ce résultat ne constitue pas une release, ne prouve ni build Windows/AppImage ni signature, et ne vaut aucune preuve d’hôte Claude/Codex/Gemini/Antigravity réel.
**Suite.** Commiter/publier M7-C après contrôle de diff, roue isolée et garde de divergence distante ; poursuivre ensuite les builds natifs release et la conformance multi-domaines.

## LOG-0208 — 2026-08-27 — M7-D : builder natif et matrice de packaging Windows/Linux
**Hypothèse.** Les artefacts desktop VERA restent portables et contrôlables si le sidecar est compilé par le Python du système cible, reçoit le suffixe Tauri exact, puis est inspecté dans chaque bundle sans utiliser de compilation croisée non attestée.
**Baseline.** M7-C fournit la source Tauri et un paquet Debian debug contenant un sidecar. Aucun workflow de packaging Windows/Linux ni AppImage vérifié n’existait dans VERA.
**Changement fonctionnel.** `scripts/build_desktop_sidecar.py` remplace la logique POSIX comme autorité cross-platform et refuse tout target non natif ou non allowlisté. Le script Bash délègue à ce builder. `.github/workflows/desktop-packaging.yml` prépare deux runners natifs, leurs prérequis, le sidecar puis les bundles AppImage/Debian ou NSIS/MSI ; les sorties sont des workflow artifacts seulement. `apps/desktop/README.md` documente le même chemin local et les limites de publication.
**Tests et contrôles.** Sur Linux x64, le builder produit le sidecar PyInstaller, puis Tauri produit `VERA-MMU_0.1.0_amd64.AppImage` (99 232 248 octets) et `VERA-MMU_0.1.0_amd64.deb` (25 233 560 octets). L’AppImage extraite contient `usr/bin/vmmu-desktop-bridge` ; l’extraction Debian précédente répond à `project.scan`. `cargo test` et `cargo build --release` passent sans avertissement.
**Verdict.** `PASS` pour le packaging Linux x64 reproductible et le cadrage de CI native. `NOT_RUN` pour la sortie Windows native et l’exécution de la matrice GitHub tant que le commit n’est pas publié ; aucune release, signature ou publication GitHub Pages n’a été créée.
**Suite.** Commit documentaire, garde de divergence et push ; lire les runs CI déclenchés, qualifier chaque artefact par plateforme et poursuivre seulement si le runner Windows passe.

## LOG-0209 — 2026-08-27 — M7-D : échec d’infrastructure CI qualifié et correction pnpm
**Observation.** Le run GitHub Actions `33059343692` déclenché par `3f19882` a échoué sur les deux runners avant les étapes de dépendances, de sidecar ou de bundle. `actions/setup-node@v4` était configuré avec `cache: pnpm`, mais `pnpm` n’était pas encore présent dans `PATH`.
**Portée.** Ce résultat est une défaillance de préparation CI : aucun build Linux/Windows, NSIS, MSI, AppImage, Debian ou sidecar n’a été produit ou évalué par ce run. Il ne doit pas être qualifié comme échec du produit desktop.
**Correction.** Le commit fonctionnel `a542660` ajoute `pnpm/action-setup@v4` avant `actions/setup-node` et retire l’activation Corepack devenue redondante. La matrice suivante devra être observée sur `main` ; son résultat Windows reste `NOT_RUN` jusqu’à la sortie native effective.
**Verdict.** `PASS` pour le diagnostic et la correction minimale de la configuration CI ; `NOT_RUN` pour les artefacts de la nouvelle matrice.
**Suite.** Commiter la continuité, appliquer la garde de divergence, pousser, puis examiner les logs et artefacts par runner sans créer de release.

## LOG-0210 — 2026-08-27 — M7-D : résultats CI Linux, refus Windows de ressource et correction ICO
**Observation.** La matrice `33059519088` a passé sous Linux x64 : préparation pnpm, sidecar natif, bundles et téléversement des artefacts. Le runner Windows a aussi construit le sidecar `x86_64-pc-windows-msvc`, puis `tauri-build` s’est arrêté avant bundling avec `icons/icon.ico not found; required for generating a Windows Resource file`.
**Portée.** Aucun bundle NSIS ou MSI n’a été produit. Le résultat est un refus de ressource de build Windows, pas un résultat fonctionnel de l’application ni du bridge. Linux reste attesté par le run CI et les inspections locales AppImage/Debian.
**Correction.** `pnpm tauri icon` a généré `apps/desktop/src-tauri/icons/icon.ico` depuis le symbole PNG VERA. Les variantes inutiles ont été retirées ; seuls PNG et ICO sont conservés. Le builder sidecar Linux, le build React, les tests Rust et la compilation release locale passent après ce changement.
**Verdict.** `PASS` pour le diagnostic et la correction minimale ; `NOT_RUN` pour NSIS/MSI jusqu’à une nouvelle exécution CI native Windows.
**Suite.** Commiter l’icône et cette continuité, appliquer la garde de divergence, pousser, puis inspecter les artefacts Windows/Linux du prochain run sans publier de release.

## LOG-0211 — 2026-08-27 — M7-D : refus MSI sur déclaration ICO et correctif de configuration
**Observation.** Le run `33060333681` passe sous Linux x64. Sous Windows, après construction du sidecar et de l’exécutable Tauri, NSIS produit `VERA-MMU_0.1.0_x64-setup.exe`. Le même job échoue ensuite durant le bundle MSI avec `Couldn't find a .ico icon`.
**Cause observée.** L’ICO existe et permet la ressource de l’exécutable/NSIS, mais la liste `bundle.icon` de `tauri.conf.json` ne contenait que `icons/icon.png`. Le bundler WiX/MSI requiert une ICO explicitement déclarée.
**Correction.** `tauri.conf.json` inclut désormais les deux formats, PNG et ICO. Le builder sidecar Linux, le build React et le bundle Debian local passent après cette modification. Aucun chemin de bridge, accès WebView, policy Git ou configuration MCP n’est touché.
**Verdict.** `PASS` pour le diagnostic et correctif de configuration ; `NOT_RUN` pour MSI/NSIS de la matrice suivante.
**Suite.** Créer les commits fonctionnel et documentaire, vérifier la divergence, pousser et observer le run Windows/Linux suivant sans release ni publication GitHub Pages.

## LOG-0212 — 2026-08-27 — M7-D : matrice native Windows/Linux entièrement passée
**Observation.** Le run `33061136241` est `success`. Le job Linux x64 `98479903668` et le job Windows x64 `98479903284` passent chacun les étapes de sidecar natif, bundle desktop et téléversement d’artefact. Les corrections `pnpm/action-setup`, ICO Windows et déclaration `bundle.icon` ont donc fermé les trois causes de refus précédentes.
**Artefacts.** GitHub expose deux archives CI non expirées : Linux `vera-mmu-desktop-x86_64-unknown-linux-gnu`, artefact `9641938598`, 172 298 510 octets ; Windows `vera-mmu-desktop-x86_64-pc-windows-msvc`, artefact `9641944934`, 61 776 022 octets. Le téléchargement exhaustif par CLI a dépassé les délais locaux ; l’inventaire API et les étapes de téléversement passées constituent l’observation de présence, sans hash de release prétendu.
**Verdict.** `PASS` pour la matrice de packaging native de vérification Windows x64/Linux x64. Ce verdict n’implique ni signature, ni installation sur machine utilisateur, ni release GitHub, ni GitHub Pages, ni validation d’hôte agent réel.
**Suite.** Commiter cette continuité, garder M7 en `PARTIAL_PASS` jusqu’aux livrables de release, puis ouvrir M8 pour la conformance multi-domaines et les scénarios no-Git/multi-repo.

## LOG-0213 — 2026-08-27 — M8-A : matrice de conformance multi-domaines et topologies
**Hypothèse.** Un Core VERA universel doit appliquer le même protocole de préparation et d’intégration project-local aux domaines déclarés, sans absorber leurs sémantiques métier, et la mémoire SQLite versionnée doit être récupérable depuis un clone Git cohérent.
**Tests rouges et correction.** La première fixture utilisait des attributs de profil inexistants et une table SQLite au pluriel ; ces hypothèses ont été corrigées vers les mappings validés et la table `capability`. La suite globale a ensuite révélé que `_mutating_call` relançait Git après une transaction déjà synchronisée : le test MCP recevait `NO_CHANGES` au lieu du vrai `SYNCED`. La façade renvoie désormais le statut post-commit conservé dans le store.
**Conformance.** Six sous-tests couvrent software/data/research/documentation/game/hardware : scan CLI `OBSERVED`, init CLI en preview sans écriture, init via bridge à racine native, puis Agent Profile `generic-mcp`, génération, staging et installation confirmée. Les scénarios no-Git, mono-repo, multi-repo et clone Git vérifient la topologie et la reprise SQLite sans merge.
**Contrôles.** `tests/test_m8_domain_conformance.py` : `3 passed, 6 subtests passed`. Suite VERA : `504 passed, 43 subtests passed`. Roue isolée : `vmmu scan` produit `vera-scan-report/v1` `OBSERVED`. Le scan de frontière hors `domain_packs/aret/` est vide après désactivation explicite de la couleur Git.
**Verdict.** `PASS` local pour M8-A. Les runners CI Windows/Linux n’ont pas encore rejoué ce lot ; les domaines restent des fixtures de protocole, et les hôtes réels restent `NOT_RUN`.
**Suite.** Commiter/publier code et continuité M8 ; examiner la matrice native déclenchée, puis passer à M9 uniquement avec le résultat plateforme correctement qualifié.

## LOG-0214 — 2026-08-27 — M8-B : échec Windows de fixtures, diagnostic et correctif portable
**Déclencheur.** La première matrice desktop intégrant `python -m pytest -q` avant packaging (`33063264121`) a réussi sur Linux x64. Windows x64 a échoué dans cette étape ; la construction sidecar et les bundles Windows n’ont donc pas été lancés par ce run.
**Diagnostic.** Quatre tests `memory_sync` enregistraient `store.close` via `addCleanup` à l’intérieur d’un `TemporaryDirectory`. `unittest` déclenche ce cleanup après la sortie du répertoire temporaire ; Linux permet de délier le fichier SQLite ouvert, Windows le refuse. Cinq tests de previews comparaient également le `Path` temporaire long à une cible Core déjà canonisée en forme physique courte. Les deux chemins désignent le même emplacement, mais la comparaison structurale est différente.
**Correctif.** Fermeture explicite du store dans un `finally` avant le nettoyage temporaire ; attentes de chemins canonisées par `resolve`. Aucun module `src/vera_mmu/` n’est modifié. Les politiques Git, l’atomicité, les contrôles symlink et le confinement utilisent toujours la racine canonique existante.
**Validation locale.** Les six modules précédemment affectés, puis toute la suite : `504 passed, 43 subtests passed`.
**Verdict.** Correctif de test `PASS` local. Windows native reste `PENDING` jusqu’à la seconde matrice ; la qualification M8 reste donc `PARTIAL_PASS`.
**Suite.** Publier après garde de divergence, attendre la matrice Windows/Linux et n’enregistrer un `PASS` M8 multi-plateforme qu’après les deux résultats explicites.

## LOG-0215 — 2026-08-27 — M8-C : déclencheur CI étendu aux corrections de tests
**Observation.** Après le push du correctif Windows, `gh run list` ne présentait aucun nouveau run pour la révision concernée. Le workflow filtre les événements par chemins, et les commits `25d3df5`/`70eb6df` ne changeaient que `tests/**` et la continuité ; ce motif n’était pas inclus.
**Correction.** `desktop-packaging.yml` inclut `tests/**` dans les filtres `pull_request.paths` et `push.paths`. Le workflow exécute déjà toute la suite VERA avant le sidecar et les bundles ; le déclencheur devient donc cohérent avec cette responsabilité.
**Portée.** Aucun code de produit, test d’acceptation, capability, policy Git ou artefact de release n’a changé. La matrice suivante demeure exclusivement de vérification, non signée et non publiée comme release.
**Verdict.** `PASS` pour le diagnostic et le déclencheur. `PENDING` pour la preuve Windows/Linux déclenchée par le commit CI.
**Suite.** Commiter la continuité, appliquer la garde de divergence, pousser et attendre les deux jobs avant toute qualification M8.

## LOG-0216 — 2026-08-27 — M8-D : assertion user-scope Windows remplacée par le confinement réel
**Déclencheur.** Le rerun `33064757436` est de nouveau vert sous Linux et Windows progresse au-delà des verrous SQLite/alias de chemin précédemment corrigés. Il échoue sur la seule assertion restante de `test_i007_i011_cloud_host_apply_requires_confirmation_and_never_targets_user_scope`.
**Diagnostic.** L’assertion interdisait que la représentation textuelle de la cible contienne `Path.home()`. Sous le runner Windows, `TemporaryDirectory` se crée sous `C:\Users\runneradmin\AppData\Local\Temp`; un réglage parfaitement project-local contient donc logiquement ce préfixe parent. Cette condition ne teste pas le scope de destination.
**Correctif.** Les deux cibles effectivement appliquées doivent être relatives à la racine canonique `project.resolve()`. L’égalité exacte aux chemins `project/.claude/settings.json` et `project/.mcp.json`, les tests d’existence et les contrôles symlink restent en place. Le test devient plus précis et indépendant du parent temporaire.
**Validation locale.** Test cloud ciblé puis suite complète : `504 passed, 43 subtests passed`.
**Verdict.** `PASS` local pour l’assertion de confinement. Rerun Windows/Linux `PENDING`; M8 ne devient pas multi-plateforme avant sa réussite explicite.
**Suite.** Commiter/publier le correctif et son record avec garde de divergence, puis observer la troisième matrice native sans lancer de release.

## LOG-0217 — 2026-08-27 — M8.EXIT : conformance multi-domaines sur deux runners natifs
**Baseline.** Le run `33064757436` avait passé Linux mais arrêté Windows sur une heuristique de préfixe utilisateur qui ne représentait pas le confinement réel. Le commit `323704b` remplace cette heuristique par la relation directe à la racine projet ; `999a35e` enregistre son contexte.
**Exécution native.** Le run `33065626744` est `success` sur les deux runners. Linux x64, job `98494854034`, exécute `504 passed, 43 subtests passed` en 78,87 s ; Windows x64, job `98494854423`, exécute `504 passed, 43 subtests passed` en 220,82 s. Les deux jobs passent ensuite la construction sidecar, les bundles AppImage/Debian ou NSIS/MSI et le téléversement.
**Artefacts.** Les archives GitHub Actions présentes et non expirées sont `9643835349` (Linux, 175 864 787 octets) et `9643897645` (Windows, 65 365 241 octets). Elles servent à la vérification CI et ne sont ni signées ni qualifiées comme artefacts de release.
**Comparaison.** Les trois divergences Windows observées ont été attribuées à des mécanismes de fixtures : ordre de fermeture SQLite, alias de chemin long/court et parent temporaire sous `Path.home()`. Les assertions conservées vérifient désormais la fermeture, l’identité canonique et le confinement à `project.resolve()` ; aucun module de produit n’a été relâché ou modifié par ces correctifs.
**Verdict.** `PASS` pour M8 : six domaines déclaratifs, surfaces CLI/bridge/MCP, Git optionnel et clone de mémoire project-local sont attestés sous Linux et Windows. Hôtes agents réels, sémantique métier des domaines, installation utilisateur et release restent `NOT_RUN`.
**Suite.** Ouvrir M9 sur le contrat de release : version, archives CLI, hashes, manifest, signatures et décision de distribution du viewer statique. Ne créer aucune release ni signature sans contrat spécifique.

## LOG-0218 — 2026-08-27 — M9-A : candidat CLI natif, manifest et contrat de release
**Hypothèse.** La CLI doit être distribuable à un agent ou utilisateur terminal sans runtime Python manuel, tout en restant distincte du desktop Tauri et de toute publication publique non signée.
**Changement.** `build_cli_bundle.py` construit avec PyInstaller l’entrée minimaliste `cli_entry.py`, uniquement dans `.build/`, pour Linux x64 ou Windows x64 du même hôte. Il refuse l’arbre Git sale, les versions divergentes (`pyproject`, npm, Cargo, Tauri), target non allowlisté ou cross-build. Il produit une archive plate-forme, un `release-manifest.json` canonique et `SHA256SUMS`; le manifest lie version, SHA source, triple et hash du binaire. La matrice CI insère ce build après le sidecar et avant les bundles Tauri, puis collecte le répertoire candidat.
**Contrat et tests.** Le contrat M9 sépare candidat CI, tag, release, licence, signature et publication. Le test dédié couvre version, targets fermés, refus cross-build et canonicalisation (`4 passed`), et la suite complète passe à `508 passed, 43 subtests passed`.
**Décision viewer.** Le dashboard WebDev checkpoint `f28ac0fa` reste séparé ; aucune copie silencieuse dans VERA ni GitHub Pages n’est opérée. Un viewer publiable exige une source explicitement versionnée ultérieurement sous `apps/viewer/`, sans privilège local.
**Verdict.** `PASS` local pour M9-A. Les candidats Windows/Linux de la nouvelle matrice, la licence formelle, les signatures et toute release demeurent `PENDING`/`NOT_RUN`.
**Suite.** Commiter code puis continuité, appliquer la garde de divergence, pousser et vérifier la nouvelle matrice avant de préparer davantage de release.

## LOG-0219 — 2026-08-27 — M9-A : smoke test du candidat CLI Linux extrait
**Exécution.** Depuis le checkout propre à `98080dbc684245a9ab485b4ba78f3dc4868d61cc`, `scripts/build_cli_bundle.py x86_64-unknown-linux-gnu` construit un exécutable PyInstaller et l’archive `vera-mmu-cli_0.1.0_linux-x64.tar.gz`. `SHA256SUMS` valide l’archive et `release-manifest.json` dans le répertoire de candidat.
**Inspection.** L’archive contient seulement `vmmu` et le manifest de release. Après extraction dans `/tmp/vera-m9-cli-check`, l’exécutable autonome lance `vmmu scan` sur un répertoire de projet vide et retourne `ok: true`, format `vera-scan-report/v1`, statut `OBSERVED`. Le manifest lie l’archive au triple Linux, à la version `0.1.0`, au SHA source et au SHA-256 `17bc1e491c27cc85a5a4b9009f7867768f3a3b4f5941c8184321d0d494c590ee` du binaire.
**Verdict.** `PASS` pour le candidat CLI Linux local, son intégrité et son entrée observationnelle. Ce n’est pas une preuve Windows ni une release : aucun tag, signature, licence définitive, publication ou installation utilisateur n’est créé.
**Suite.** Enregistrer cette observation, publier après garde Git, puis lire la matrice native M9 qui doit construire et vérifier les candidats CLI sous Linux et Windows avant le développement de la suite de release.

## LOG-0220 — 2026-08-27 — M9-A.EXIT : archives CLI candidates Windows/Linux en CI native
**Exécution.** Le run `33067150688` pour la révision `c9f67f1` est `success`. Linux x64, job `98499947163`, passe la suite `508 passed, 43 subtests passed` en 74,67 s. Windows x64, job `98499946792`, passe la même suite en 198,53 s. Dans les deux cas, le sidecar, `Build standalone VERA CLI archive`, les bundles desktop et le téléversement passent.
**Artefacts.** GitHub Actions expose l’archive Linux `9644430339` (214 364 237 octets) et Windows `9644534152` (89 113 204 octets), non expirées. Elles contiennent les sorties de vérification du job, incluant le répertoire `.build/cli-release/<target>/` ajouté par M9-A.
**Comparaison.** La preuve Linux locale avait déjà confirmé l’archive extraite, son SHA-256 et `vmmu scan`. La CI étend désormais la construction du même builder au runner Windows natif sans compiler de Windows depuis Linux.
**Verdict.** `PASS` pour M9-A — candidats CLI natifs, manifests et checksums de CI. `NOT_RUN` pour une release : licence, clés/signatures, tag, notes remplies, publication et installation hôte ne sont pas réalisés.
**Suite.** Consigner/publier ce résultat, puis traiter les préconditions de licence et de signature comme décisions explicites du propriétaire. Ne pas créer de release ni d’artefact public à partir de ces archives CI.

## LOG-0221 — 2026-08-27 — M9-B : préversion Apache documentée et chaîne taggée non signante
**Décision.** Apache-2.0, DCO, marque officielle VERA-MMU, préversion publique contrôlée `v0.1.0-rc.1`, Windows/Linux x64, absence de mise à jour automatique et viewer Pages ultérieur sont retenus comme politique cible. `LICENSE-PENDING.md` est remplacé par le texte Apache exact, `NOTICE`, règles de contribution et politique de marque. La roue expose `License: Apache-2.0` et le classifieur OSI correspondant.
**Changement.** Le README est réécrit pour décrire le produit, les badges, les parcours CLI/desktop, la mémoire Git, les garanties, plateformes, vérifications, contribution, licence et limites réelles. `release-candidate.yml` s’exécute uniquement sur tag `v*` ou dispatch, reconstruit les candidates natives puis assemble un répertoire final manifesté/hashé. Son permission set est `contents: read`; il ne peut ni signer, ni taguer, ni publier une release.
**Contrôles.** Les tests rouges de l’assembleur ont vérifié le refus d’un bundle incomplet dans une racine isolée. Les tests de builder/assembleur passent (`6 passed`), puis la suite VERA complète : `510 passed, 43 subtests passed`.
**Verdict.** `PASS` local pour M9-B. Il ne s’agit pas encore d’un candidat de tag observé : aucune signature, release GitHub, hash public, installation utilisateur ou agent réel n’est revendiqué.
**Suite.** Publier le code/doc après garde Git. La création de `v0.1.0-rc.1`, l’exécution du workflow de tag, toute signature et publication publique exigent une confirmation spécifique ; vérifier ensuite tous les artefacts avant de présenter la préversion comme téléchargeable.

## LOG-0222 — 2026-08-27 — M9-B.EXIT : assemblage de préversion non signé sur CI native
**Exécution.** Le workflow manuel `33070861267` à la révision `b5b41b9` réussit sur Linux x64 (`98512443152`) et Windows x64 (`98512443367`). Les suites passent respectivement `510 passed, 43 subtests passed` en 77,18 s et 265,58 s. Les builds sidecar/CLI, desktop, assemblage `vera-release-candidate/v1` et upload passent dans chaque job.
**Sorties.** Les artefacts CI `9645991442` (Linux, 214 368 098 octets) et `9646108111` (Windows, 89 111 512 octets) sont présents, non expirés et explicitement non signés. Le workflow n’a que `contents: read` et n’a créé ni tag ni release.
**Contrôle local.** Le transfert passif de l’archive Linux a échoué par EOF imprévu avant son extraction ; aucun binaire CI n’a été exécuté. Les preuves du job suffisent au statut CI, mais ne remplacent pas la vérification de checksums qui devra être réalisée sur les artefacts du tag exact.
**Verdict.** `PASS` pour M9-B : la chaîne non signante est prête et exécutée nativement. `NOT_RUN` pour tag, signature, GitHub Release, téléchargement officiel, installation utilisateur et agents réels.
**Suite.** Commiter/publier ce record. Demander confirmation exacte avant de créer `v0.1.0-rc.1`, effectuer le run de tag et, faute de clés de signature disponibles, ne publier aucun binaire à ce stade.

## LOG-0223 — 2026-08-27 — M9-C : version `v0.1.0-rc.1` cohérente et vérifiée
**Problème prévenu.** Le tag `v0.1.0-rc.1` et les manifestes précédents `0.1.0` auraient produit une identité ambiguë : PyPI/packaging Python impose une forme PEP 440, alors que Tauri/Cargo/npm acceptent SemVer prérelease.
**Correction.** Les manifestes desktop sont alignés sur `0.1.0-rc.1`, `pyproject.toml` sur `0.1.0rc1`, et le builder convertit explicitement cette seule forme Python vers la représentation release avant son contrôle d’égalité. `Cargo.lock` ne change que la version du package local.
**Validation.** Les tests builder/assembleur et la suite complète passent (`510 passed, 43 subtests passed`). Le frontend passe `pnpm build`; Rust passe `cargo check --offline` puis `cargo check --locked`. Le premier check verrouillé avait correctement refusé le lock obsolète, mis à jour hors réseau avant revalidation.
**Verdict.** `PASS` pour l’identité de préversion. Tag, run déclenché par tag, signature, GitHub Release, installation utilisateur et agents réels restent `NOT_RUN`.
**Suite.** Publier cette cohérence, puis créer le tag annoté autorisé et n’attacher des artefacts non signés qu’après la matrice de ce tag exact.

## LOG-0224 — 2026-08-27 — M9-D : correction du format de préversion MSI
**Échec observé.** Le tag public `v0.1.0-rc.1` a déclenché le run `33073234774`. Linux réussit ; Windows passe tests et CLI mais Tauri refuse le bundle MSI avec : « optional pre-release identifier in app version must be numeric-only and cannot be greater than 65535 ». Aucun artefact Windows final ni release n’est créé.
**Correction minimale.** rc.1 est conservé comme tag historique non publiable. Un nouveau cycle rc.2 aligne npm/Cargo/Tauri sur `0.1.0-2`, Python sur `0.1.0rc2`, et le builder sur cette conversion unique. Le tag futur sera `v0.1.0-rc.2`. La contrainte est du bundle MSI, non du Core, de la CLI, du bridge ou des tests.
**Validation locale.** `cargo check --offline`, puis `cargo check --locked`, `pnpm build`, six tests builder/assembleur et la suite complète `510 passed, 43 subtests passed` passent.
**Verdict.** rc.2 est le candidat de préversion corrigé ; tag rc.2 et validation native restent requis. La release non signée reste conditionnelle à ces preuves et ne peut pas être rc.1.
**Suite.** Commiter/publier le correctif et cette continuité, créer le tag rc.2, puis n’attacher des assets à une GitHub Pre-release que si Linux et Windows réussissent depuis ce tag.

## LOG-0225 — 2026-08-27 — M9-E : contrôle d’intégrité final corrigé, rc.3
**Échec observé.** Après le run rc.2 vert, l’artefact Linux est téléchargé passivement et vérifié. `sha256sum -c` confirme l’archive CLI, le manifest CLI, AppImage, DEB et manifest final, puis échoue sur `SHA256SUMS` : l’assembleur écrivait le fichier final en le listant lui-même. Un checksum ne peut pas être un hash stable de son propre contenu.
**Correction minimale.** `_verify_checksum_file` valide le checksum CLI source avant toute copie ; le candidat final ne copie plus le checksum intermédiaire. `_checksum_lines` interdit explicitement un nom `SHA256SUMS` et le fichier final liste les assets et le manifest, pas lui-même. Une régression isole ce refus.
**Version.** rc.2 est documenté et conservé non publiable. La nouvelle préparation rc.3 utilise `0.1.0-3` pour desktop/MSI et `0.1.0rc3` pour Python ; le builder normalise la seule forme PEP 440 correspondante.
**Validation.** Six tests builder/assembleur et la suite complète : `511 passed, 43 subtests passed`. Cargo offline/locked passe après le lock de version.
**Verdict.** `PASS` local. Le tag rc.3 et son run de candidats doivent prouver la correction sur les artefacts natifs avant de publier une préversion non signée.

## LOG-0226 — 2026-08-27 — M9-F : collision de manifests rc.3, candidat rc.4
**Échec observé.** L’inspection passive des artefacts rc.3 passe les hashes déclarés mais montre que l’assembleur copie le manifest CLI sous `release-manifest.json`, puis écrit le manifest global sous le même nom. La liste des assets finalisés conserve donc un hash de manifest CLI qui n’existe plus à cette destination.
**Correction minimale.** `_candidate_sources` réserve le nom global `release-manifest.json` et exporte le manifest CLI sous `cli-release-manifest.json`. Il refuse tout nom de candidat ambigu ou toute tentative d’utiliser le nom réservé. Le manifest final et `SHA256SUMS` ont désormais des entrées distinctes pour l’archive CLI, le manifest CLI, les deux bundles et le manifest final.
**Version et contrôles.** rc.3 est conservé non publiable ; rc.4 passe à `0.1.0-4` desktop/MSI et `0.1.0rc4` Python. La régression de collision, les tests builder/assembleur, Cargo offline/locked et la suite complète passent (`512 passed, 43 subtests passed`).
**Verdict.** `PASS` local pour la correction. Le tag rc.4 et l’inspection des artefacts issus du tag restent obligatoires avant toute GitHub Pre-release.

## LOG-0227 — 2026-08-27 — M9.EXIT : GitHub Pre-release rc.4 non signée publiée
**Préconditions.** rc.4 pointe vers `3519f760497c03d4744448f416b9e7deaafae790`. Le run exact `33078499592` est vert : Linux `98538971733` (`512 passed, 43 subtests passed` en 96,84 s) et Windows `98538972155` (`512 passed, 43 subtests passed` en 244,72 s), suivis des builds CLI/desktop, assemblage et upload.
**Intégrité.** Les artifacts CI Linux `9649277094` et Windows `9649499388` sont récupérés passivement. `sha256sum -c SHA256SUMS` valide chaque entrée. rc.4 contient des noms non collisionnels : manifests CLI sous `cli-release-manifest.json`, manifests plateforme sous `release-manifest.json`, puis renommage public explicite et manifest global. `SHA256SUMS` ne s’auto-référence pas.
**Publication.** La page GitHub `v0.1.0-rc.4` est créée en mode Pre-release. Douze assets contrôlés sont téléversés : six binaires, quatre manifests de plateforme/CLI, manifest global et hashes. Les notes indiquent Apache-2.0, le statut non signé, les commandes de vérification et les limites. L’URL publique est `https://github.com/aciderix/vera-mmu/releases/tag/v0.1.0-rc.4`.
**Verdict.** `PARTIAL_PASS` pour M9 : release gratuite de préversion publiée et traçable. `NOT_RUN` demeure pour signature, installation sur poste réel, agents réels, macOS/ARM, auto-update et viewer Pages. rc.1/rc.2/rc.3 restent des tags de validation sans assets.
**Suite.** Révoquer le jeton jetable précédemment exposé, conserver les signatures comme gate stable, et lancer une campagne d’installation réelle puis d’agents réels seulement quand le protocole de double confirmation le permet.

## LOG-0228 — 2026-08-27 — M10-A : smoke Linux CLI, AppImage et Debian
**Implémentation.** `smoke_release_runtime.py` valide d’abord le manifest candidat et `SHA256SUMS`, extrait l’archive CLI sans accepter liens ou chemins de sortie, lance `vmmu --help` puis un scan `OBSERVED` sans créer `.vera-mmu/`. Il lance ensuite AppImage et le payload Debian sous Xvfb pendant huit secondes, puis arrête le groupe de processus. Le script PowerShell parallèle prépare les mêmes contrôles Windows CLI/NSIS/MSI. Ces étapes sont insérées avant l’upload dans le workflow par tag.
**Tests et corrections.** Le premier build local réussit mais l’assembleur refuse correctement deux `.deb` présents de versions différentes. Il filtre maintenant par version, avec régression. Le premier stop AppImage laisse l’enfant précédent vivant : session isolée et `killpg` corrigent l’arrêt. Le paquet contient `vera-mmu-desktop`, non `VERA-MMU`, correction couverte par test.
**Résultat local.** Helpers/assembleur : `9 passed`. Suite complète : `517 passed, 43 subtests passed`. Le smoke retourne `integrity`, `cli-help`, `cli-observed-scan`, `appimage-start`, `deb-payload-start` puis `NO_RESIDUAL_RUNTIME_PROCESSES`.
**Verdict.** `PARTIAL_PASS` : démarrage Linux local prouvé pour les trois voies. La matrice native doit encore exécuter ce même smoke Windows/Linux ; une preuve d’installation utilisateur et d’agents réels reste hors lot.
**Suite.** Publier le lot M10, déclencher la matrice native, puis inventorier formellement le reste MCP au regard des preuves host, jamais des fixtures seules.

## LOG-0229 — 2026-08-27 — M10-B : matrice runtime Linux et audit de dette MCP
**Observations M10.** Le premier run runtime `33088157116` sur `0ab1f2b` réussit sous Linux mais échoue sous Windows avant exécution du produit : une apostrophe typographique dans une chaîne PowerShell casse le parseur. Une régression dédiée interdit ces caractères dans `smoke_windows_release.ps1`; le correctif minimal est publié sous `1f81421`. La suite complète atteint ensuite `518 passed, 43 subtests passed`.

**Matrice native.** Le second run `33089780117` sur `1f81421` réussit sous Linux : le runner Ubuntu reconstruit, assemble, exécute le smoke pendant 18 secondes et téléverse le candidat après une durée totale de 9 min 17 s. La preuve complète ainsi le smoke Linux local CLI/AppImage/payload Debian. Sous Windows, la syntaxe est corrigée et le smoke atteint la CLI, NSIS puis MSI. `msiexec` retourne `0`, mais le chemin temporaire présumé est absent lors de la recherche de l’exécutable ; le lancement MSI n’est donc pas observé. L’absence de ce chemin ne devient pas un `PASS` implicite, ni un défaut démontré du paquet.

**Décision de périmètre.** Le propriétaire confirme que l’objectif présent est seulement le démarrage des livrables. Linux est `PASS` à ce niveau. La vérification de démarrage MSI Windows est laissée à une machine Windows du propriétaire ; aucune nouvelle tentative CI, modification d’installateur ou validation UX n’est entreprise. La préversion rc.4 reste non signée et ne devient pas stable.

**Audit MCP.** Les adapters Claude local/cloud, Codex, Gemini, Antigravity et generic-mcp sont construits, project-bound, configurables par preview/confirmation et couverts par vraies sessions MCP stdio contrôlées. Le restant concerne l’observation des hôtes réels : trust, chargement des hooks/configs, connexion MCP et séquences lifecycle. Claude Cloud conserve la gate additionnelle : preview réel, deux confirmations distinctes, écriture user-scope, puis session fraîche. Gemini, Codex, Antigravity et generic-mcp conservent leurs limites de couverture déclarées ; aucun adapter ne peut se prétendre live sans sa preuve host.

**Verdict.** `PARTIAL_PASS` pour M10 dans le périmètre de démarrage : Linux prouvé localement et en CI native, Windows CLI/NSIS observés, démarrage MSI `NOT_RUN` par choix de validation manuelle. `IN_PROGRESS` pour M5 : mécanismes testés, preuves hôtes/agents réels explicitement différées. Sources : `artifacts/m10_runtime_smoke_contract_2026-08-27.md`, `artifacts/m10_mcp_remaining_work_audit_2026-08-27.md`, `MEM-STATE-128`, `MEM-DEC-176`.

## LOG-0230 — 2026-08-27 — M11 : audit de complétude de la spécification finale
**Source et méthode.** La spécification `UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md` fournie par le propriétaire (version 1.0, SHA-256 `d8e5d01b673e243e0104a30fb62328bc2a7fc650373ab91b1a103652a1737d75`) est décomposée en exigences et confrontée à la révision VERA `9ac62d972633c04e9daa56723470f8d6ae7cab74`, aux sources publiques, à la matrice de découplage, aux tests et aux artefacts. Les statuts utilisés sont `PASS`, `PARTIAL`, `MISSING`, `NOT_PROVEN` et `OUT_OF_SCOPE`; aucun statut ne découle d’un simple jalon historique.

**Preuves exécutées.** La suite intégrale actuelle passe `518 passed, 43 subtests passed` en 110,22 s. Le scan anti-ARET du Core hors `domain_packs/aret` passe. Un projet temporaire est soumis à `vmmu scan`, `init-project --apply --confirm`, `init` et `adapter doctor`: il ne crée que les quatre fichiers initiaux sous `.vera-mmu`, le doctor déclare le runtime/config non présents et l’hôte non observé, tandis que `generate` refuse à juste titre toute génération sans capability `ALLOW`. Ces faits ont confirmé la différence entre mécanismes livrés et parcours complet visé.

**Résultat.** Core/relations/evidence/gates, conformance déclarative de six domaines, MCP stdio, adapters bornés, CLI de préparation et console Tauri sont livrés dans leurs périmètres. La spécification finale reste non satisfaite par des lacunes produit : Profile riche, capability runners génériques, bundles/export/import/restore, surface MCP/CLI complète, import project avec provenance, Dashboard de modélisation, Doctor composite, documentation dérivée, rapport coverage, VCS multi-provider, compatibilité et parité ARET. Les hôtes MCP réels restent `NOT_PROVEN`. La validation MSI Windows est explicitement `OUT_OF_SCOPE` du présent audit, mais son exclusion ne modifie aucune lacune listée.

**Verdict.** `NOT_DONE` pour « VERA totalement livré selon la spécification finale, hors Windows ». Les lots M11-A à M11-G sont créés pour traiter les écarts séparément. Aucun agent réel, trust, secret, bootstrap ou écriture user-scope n’est exécuté. Source complète : `artifacts/m11_specification_completeness_audit_2026-08-27.md`; mémoire : `MEM-DEC-177`.

## LOG-0231 — 2026-08-27 — M11-A : profil complet et catalogues déclaratifs
**Baseline et portée.** M11-A traite exclusivement la configuration déclarative qui était `PARTIAL` dans l’audit M11. Il ne lance aucun processus, ne réutilise aucun hook réel et ne modifie pas un projet métier. Le bootstrap conserve preview → confirmation → écriture atomique/refus de symlink.

**Résultat.** `project.yaml` porte maintenant project/description, workspace, storage, identité, resume structuré, Front, taxonomies knowledge/entity/relation, work, catalogues capabilities/gates/policies et intégrations. Les sept fichiers initiaux sont générés sous `.vera-mmu`; les six templates de domaine émettent des taxonomies différentes. Le chargeur `project_catalogs` refuse chemins hors runtime, symlinks, fichiers absents, YAML à clé dupliquée, formats et schémas inconnus, capabilities contenant une commande libre, gates non liées et profils agents absents. La génération MCP exige ces catalogues et incorpore leurs hashes dans son preview déterministe.

**Preuves.** Les régressions sont d’abord mises en échec pour chaque mécanisme nouveau, puis satisfaites. La CLI temporaire crée les sept fichiers et charge un profil Research. La suite intégrale atteint `523 passed, 43 subtests passed`. Les commits fonctionnels `e92edf7`, `1d9d8a8`, `88af9aa`, `a0e09cf`, `fb6a1ac` sont poussés linéairement après garde d’ascendance.

**Verdict.** `M11-A = PASS`. Les catalogues ne sont pas des runners : execution, import/export/restore, surfaces CLI/Doctor, Dashboard configurateur, VCS/migration ARET et preuves hôtes restent les lots suivants. Source : `artifacts/m11_a_project_profile_catalogs_2026-08-27.md`; mémoire : `MEM-DEC-178`.

## LOG-0232 — 2026-08-27 — M11-AF : Front/handoff et reprise profile sous policy fermée
**Baseline et portée.** M11-AF clôt exclusivement la persistance du Front/handoff, la compilation de reprise depuis le Project Profile et la policy de mutation project-local. Aucun lot bundle, import/export/restore, UI configuratrice, host réel ou écriture Claude Cloud user-scope n’est engagé. Le commit fonctionnel est `43e027a`.
**Résultat.** La migration checksummée 039 crée `front_revision` et `handoff` avec FKs, indexes et triggers anti-mutation. `FrontService` écrit des snapshots complets, versionnés, hashés et profile-bound; `HandoffService` lie un Front courant au Resume Dossier vérifié. Le dossier est dérivé des sections de reprise obligatoires et du budget du profil. `require_project_write` charge le catalogue validé avant toute mutation, exige `confirm=True`, refuse `deny` et toute policy invalide/absente, et ne laisse pas `allow` éliminer la confirmation d’une écriture M11-AF.
**Preuves.** Les scénarios Front/handoff/reprise passent à `15 passed`; les adapters/hooks/MCP qui consomment le dossier passent à `63 passed, 12 subtests passed`; la régression intégrale atteint `529 passed, 43 subtests passed` en 108,67 s. La régression historique 038→039 conserve `project_identity`, atteint le format 39 et exerce les écritures/locks append-only. Le contrôle `git diff --check` ne remonte aucun défaut avant l’index fonctionnel.
**Verdict.** `M11-AF = PASS` dans son périmètre. La conformité globale demeure `NOT_DONE` : les lots M11-B à M11.EXIT et la campagne d’hôtes réels restent ouverts. Après le push documentaire, l’exécution doit se mettre en pause sans commencer M11-B. Source : `artifacts/m11_af_front_handoff_resume_policy_2026-08-27.md`; mémoire : `MEM-DEC-179`.


### LOG-0180 — Verdict M11-B : bundle Core, restauration non fusionnelle et import documentaire

| Champ | Valeur |
|---|---|
| Date | 27 août 2026 |
| Type | `BASELINE` / `RUN` / `EVIDENCE` / `COMPARISON` / `VERDICT` |
| Baseline | `HEAD = origin/main = merge-base = bb3606ae1ad390cd437e2e89e66d5986bfd67030`, arbre propre, suite initiale `529 passed`. Les dépôts ARET de référence ont été consultés en lecture seule. |
| Hypothèse | Un mécanisme Core peut exporter/restaurer un snapshot VERA sans fusion, à identité et hashes vérifiés, et importer un ensemble explicite de documents locaux comme observations provenancées, sans connaître ARET ni exécuter de code projet. |
| Changement minimal | Ajout de `bundles.py` (`BundleService.export`, `restore_bundle`), `project_import.py` (preview/apply documentaire), extension minimale de `project_policy.py` pour vérifier une policy cible avant ouverture/mutation. Aucun changement de migration, CLI, MCP, schéma ou dépôt ARET. |
| Contrat bundle | ZIP borné, manifest JSON canonique, checkpoint WAL, snapshot SQLite, ledger des migrations, inventaire intégral SHA-256 et artefacts. Les symlinks, doublons ZIP, traversal, tailles excessives, ratios de compression, hash/ledger/SQLite/identité incohérents sont refusés avant mutation. |
| Contrat restore | `ProjectIdentity`, hash de profil, métadonnées SQLite, intégrité SQLite, clés étrangères et migrations supportées doivent être identiques. Cible mémoire non vide refusée sauf égalité exacte; staging puis rollback du runtime antérieur si la permutation finale échoue. |
| Contrat import | Le client fournit une liste explicite de documents réguliers UTF-8 situés dans les racines du workspace. Le preview hashé est relu avant commit. Une cible knowledge non vide est refusée, sauf replay exact; les knowledge importées restent `OBSERVED` avec provenance hashée, sans `PROVEN`. |
| Tests-first | `tests/test_m11b_bundle_project_import.py` : 7 `PASS`, couvrant E2E, altération, identité divergente, non-fusion, replay, confirmation, rollback, symlink et preview périmé. |
| Régression ciblée | 54 `PASS` en 3,31 s sur M11-B, bootstrap, opérations projet, Front/handoff, resume, ledgers d’import et memory-sync. |
| Régression complète | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q` : **536 passed in 52,96 s**. |
| Contrôles additionnels | `git diff --check` : `PASS`; contrôle lexical ciblé sans `ARET`, `Wine`, `MinGW`, `Ghidra` ou `PE32` dans les nouveaux modules : `PASS`. |
| Invariants | I003, I010, I011, I013, I014, I015. |
| Limites | Pas de CLI/MCP publique, pas de Dashboard, pas d’import automatique ou réseau, pas d’import de Git/issues, pas de nouvelle migration ni parité ARET. La surface de transport et l’interface publique restent M11-C. |
| Verdict | `PASS` pour **M11-B Core**. `IN_PROGRESS` pour M11 et `UNKNOWN` pour la parité ARET exhaustive. |
| Mémoire liée | `MEM-DEC-180`; artefact `continuity/artifacts/m11_b_bundle_restore_project_import_2026-08-27.md`. |


### LOG-0181 — Commit local M11-B

| Champ | Valeur |
|---|---|
| Commit | `23bb4558c8c2b67733e48ab819d373959f33af2b` — `feat: add verified VERA bundle restore and project import`. |
| Contenu | Services Core de bundle/restauration/import documentaire, test de contrat M11-B, artefact probatoire et mises à jour de continuité. |
| Validation liée | Régression complète : `536 passed in 52.96s`; diff whitespace : `PASS`. |
| Publication | Commit local créé ; aucune publication distante n’a été demandée ni effectuée dans cette session. |
| Statut | `PASS` pour l’enregistrement local du lot M11-B. |


## LOG-0233 — 2026-08-27 — M11-C.1 : transport public bundle/import

**Baseline et portée.** Le point de départ est `986f28d`, deux commits locaux devant `origin/main`, avec `536 passed`. Cette sous-tranche ne modifie ni le schéma, ni les primitives M11-B, ni les dépôts de référence. Elle expose seulement une surface CLI/MCP bornée qui délègue au Core.

**Résultat.** La CLI fournit `bundle-export`, `bundle-restore` et `project-import`. Le MCP fournit `mmu_export_bundle`, `mmu_preview_project_documents` et `mmu_import_project_documents`; les outils ont des schémas fermés, n’acceptent ni commande, ni contenu source, ni statut, ni provenance, ni chemin de sortie. L’export MCP accepte seulement `bundle_id` et `confirm`; l’import MCP exige les chemins relatifs explicitement sélectionnés, le `preview_hash` recomputé et une confirmation. Le contenu du document n’est jamais retourné par le preview. La liste canonique des tools du manifeste inclut aussi `mmu_sync_memory`, qui participe au `mcp_build_hash`.

**Décision de sûreté.** La restauration n’est pas servie par MCP. Elle reste CLI-only car le processus MCP garde le SQLite/runtime à restaurer ouvert : permettre à ce processus de se remplacer créerait une course et fragiliserait l’atomicité M11-B. La CLI appelle la restauration avant l’ouverture d’un store cible.

**Preuves.** Les contrats nouveaux passent à `2 passed` en 2,03 s; la cible CLI/MCP/manifeste/stdio/lifecycle atteint `17 passed` en 15,27 s. La régression complète atteint **`538 passed in 58.99s`**. Les assertions couvrent confirmation, confinement de sortie, absence de `path` dans l’export MCP, preview sans contenu, hash de preview, statut `OBSERVED`, manifest canonique et non-régression stdio.

**Verdict.** `M11-C.1 = PASS`; `M11-C global = IN_PROGRESS`. Doctor composite, API universelle de lecture/boot, commandes restantes, Dashboard et intégrations de production ne sont pas déduits de cette tranche. Artefact : `artifacts/m11_c1_public_bundle_import_transport_2026-08-27.md`; mémoire : `MEM-DEC-181`.


### LOG-0234 — Commit local M11-C.1

| Champ | Valeur |
|---|---|
| Commit | `85c59aa77750115049b43f491f1568589b656322` — `feat: expose verified bundle import transports`. |
| Contenu | CLI bundle-export/bundle-restore/project-import, trois outils MCP bornés, manifeste canonique étendu, contrats stdio/CLI et artefact M11-C.1. |
| Validation liée | Ciblé : `17 passed in 15.27s`; intégral : `538 passed in 58.99s`; `git diff --check` et scan lexical de frontière : `PASS`. |
| Publication | Commit local créé ; aucune publication distante n’a été demandée ni effectuée. |
| Statut | `PASS` pour l’enregistrement local de M11-C.1; M11-C global reste `IN_PROGRESS`. |


## LOG-0235 — 2026-08-27 — M11-C : Doctor composite et clôture des transports publics

**Baseline et portée.** Le point de départ est `d3b992f`, M11-C.1 validé localement à `538 passed`. M11-C clôt le transport CLI/MCP des primitives M11-B et ajoute seulement un Doctor de santé Core. Le lot ne modifie pas le schéma, n’exécute aucune capability, ne démarre pas d’host, ne contacte aucun réseau et ne touche pas les dépôts ARET.

**Résultat.** `doctor.py` produit un rapport `vera-doctor-report/v1` avec douze checks ordonnés : identité, profile, workspace, catalogues, runtime, intégrité SQLite, ledger, WAL, artefacts, reprise, transport MCP et VCS. SQLite est ouvert sous URI read-only; aucun `MemoryStore.open`, migration, transaction ou audit n’est déclenché. Une configuration no-Git ou un store d’artefacts non matérialisé est qualifiée sans faux échec; symlink d’artefacts, SQLite invalide, ledger/identité/mode journal incohérents sont des échecs explicites avec remédiation. `vmmu doctor` retourne un exit code 2 pour un rapport dégradé; `mmu_doctor` ne prend aucun argument et regarde uniquement le profile déjà lié au store actif. Le tool est inclus dans le manifeste MCP canonique.

**Preuves.** `tests/test_m11c_composite_doctor.py` : `3 passed`, dont non-mutation hash/audit, symlink et corruption SQLite, et vraie session stdio sans entrée client. La cible M11-B/M11-C associée atteint `27 passed in 19.39s`. La régression complète atteint **`541 passed in 64.78s`**.

**Verdict.** `M11-C = PASS` dans le périmètre documenté. Les APIs universelles boot/FIND/READ, commandes de produit restantes, Dashboard, documentation dérivée, VCS multi-provider, migration/parité ARET et hôtes réels restent hors lot et ne sont pas réétiquetés. Artefact : `artifacts/m11_c_composite_doctor_2026-08-27.md`; mémoire : `MEM-DEC-182`.


### LOG-0236 — Commit local M11-C

| Champ | Valeur |
|---|---|
| Commit | `daab1fce3d6cf6429c732fc3be2ab60cc68c39d2` — `feat: add non-mutating composite doctor`. |
| Contenu | Doctor Core read-only, commande `vmmu doctor`, tool `mmu_doctor`, manifeste MCP étendu, tests de non-mutation/corruption/stdio et continuité M11-C. |
| Validation liée | Doctor : `3 passed`; ciblé M11-B/M11-C : `27 passed in 19.39s`; intégral : `541 passed in 64.78s`; diff et scan de frontière : `PASS`. |
| Publication | Commit local créé ; aucune publication distante n’a été demandée ni effectuée. |
| Statut | `M11-C = PASS` dans le périmètre documenté. |


## LOG-0237 — 2026-08-27 — M11-H : boot, FIND et READ génériques

**Baseline et portée.** Le lot démarre à `b71cde9`, six commits locaux devant `origin/main`, avec `541 passed`. Il ajoute un service Core de lecture et des façades CLI/MCP, sans schéma, migration, mutation de connaissance, capability, preuve, provider, réseau ou interaction ARET.

**Résultat.** `ReadService.boot()` retourne l’identité project-bound, les références disponibles de Front/handoff et `resume_status=NOT_ARMED`, sans armer ou acquitter de garde. `find()` interroge uniquement les titres de `knowledge`, `entity` et `work-item`; il retourne des références compactes déterministes et ne contient ni contenu ni description. `read()` impose une adresse `vera://` strictement canonique et liée au project id du store, puis délègue au service exact concerné. `read_batch()` est limité à 1–32 adresses et conserve l’ordre. CLI : `boot`, `find`, `read`, `read-batch`. MCP : `mmu_boot`, `mmu_find`, `mmu_read`, `mmu_read_batch`; les tools sont ajoutés à `TOOL_NAMES` et donc au `mcp_build_hash`.

**Preuves.** Les trois tests M11-H initient un profile documentaire, puis vérifient les results de boot, la séparation FIND/READ, le refus d’adresse étrangère, les bornes de query/batch, l’absence d’audit nouveau, la CLI et une session MCP stdio sans profile path ni project id clients. Contrat : `3 passed in 2.04s`; cible CLI/MCP : `27 passed in 20.45s`; régression complète : **`544 passed in 62.63s`**.

**Verdict.** `M11-H = PASS` pour les trois ressources et opérations documentées. Front/handoff/relations/preuves/assets/capabilities/gates/executions, `related`, resume status détaillé, mutations, work/evidence et recherche/indexation plus large restent explicitement hors lot. Artefact : `artifacts/m11_h_boot_find_read_2026-08-27.md`; mémoire : `MEM-DEC-183`.


### LOG-0238 — Commit local M11-H

| Champ | Valeur |
|---|---|
| Commit | `eb26138f0727637ecbaa16cc5f7e3dee4e2b4208` — `feat: add generic boot find read APIs`. |
| Contenu | Service Core `ReadService`, CLI boot/find/read/read-batch, quatre tools MCP fermés, manifeste canonique étendu, contrats de lecture et continuité M11-H. |
| Validation liée | Contrat M11-H : `3 passed in 2.04s`; cible CLI/MCP : `27 passed in 20.45s`; intégral final : `544 passed in 62.63s`; diff et scan de frontière : `PASS`. |
| Publication | Commit local créé ; aucune publication distante n’a été demandée ni effectuée. |
| Statut | `M11-H = PASS` dans le périmètre documenté. |


## LOG-0239 — 2026-08-27 — M11-I : lectures Front, handoff et relation

**Baseline et portée.** Le lot démarre à `5d3b9b7`, M11-H livré localement à `544 passed`. Il étend `ReadService` sans modifier les services Front, handoff ou relation, sans migration, mutation, provider, réseau, artefact ou dépendance ARET.

**Résultat.** `current_front()` et `latest_handoff()` lisent les pointeurs persistants sans paramètre de sélection; la CLI les expose par `get-front` et `get-handoff`, et le MCP par `mmu_get_front` et `mmu_get_handoff`, tous sans entrées client. La lecture exacte accepte désormais `front`, `handoff` et `relation`: `handoff` est inscrit au contrat d’adressage, le payload handoff déjà validé est retourné comme JSON structuré et toute erreur des services est convertie en `ReadApiError` fail-closed. Front, handoff et relation restent exclus de FIND. Les tools ajoutés participent au manifeste canonique.

**Preuves.** `tests/test_m11i_specialized_reads.py` crée un Front profilé, un Resume Dossier réel, un handoff, une paire d’entités et une relation déclarée. Il vérifie les références/id/hashes/payload, les adresses d’extrémités, le refus cross-project et absent, l’absence d’audit de lecture, les commandes CLI et une session MCP stdio. Contrat : `3 passed in 2.17s`; cible M11-H/Front/relations/MCP/CLI : `30 passed in 17.45s`; régression complète : **`547 passed in 63.06s`**.

**Verdict.** `M11-I = PASS` pour Front/handoff/relation. Assets, preuves/evidence, capabilities, gates, executions, symboles, profil, traversal `related`, resume brief/status détaillé, recherche de contenu et mutations sont toujours hors lot. Artefact : `artifacts/m11_i_specialized_front_handoff_relation_reads_2026-08-27.md`; mémoire : `MEM-DEC-184`.


### LOG-0240 — Commit local M11-I

| Champ | Valeur |
|---|---|
| Commit | `b5f25e2dbb68d9a19e5fab0000cdbbf72270ad09` — `feat: add specialized core reads`. |
| Contenu | Extension `ReadService` Front/handoff/relation, adressage `handoff`, commandes CLI get-front/get-handoff, deux tools MCP fermés, manifeste, contrats et continuité M11-I. |
| Validation liée | Contrat M11-I : `3 passed in 2.17s`; cible M11-H/Front/relations/MCP/CLI : `30 passed in 17.45s`; intégral : `547 passed in 63.06s`; diff et scan de frontière : `PASS`. |
| Publication | Commit local créé ; aucune publication distante n’a été demandée ni effectuée. |
| Statut | `M11-I = PASS` dans le périmètre documenté. |


## LOG-0241 — 2026-08-27 — M11-J : lectures capability, execution et evidence

**Baseline et portée.** Le lot démarre à `9f2aca1`, M11-I livré localement à `547 passed`. Il étend la lecture Core de trois enregistrements persistés sans modifier schema, admission, policy, promotion, gate, capability runner, asset, provider, réseau ou compatibilité ARET.

**Résultat.** `ReadService.read` délègue les capabilities à `CapabilityService.get`, les evidences à `EvidenceService.get` et les executions à la nouvelle primitive `ExecutionService.get`. Cette dernière parse et valide les trois payloads JSON persistants avant de retourner un record normalisé et son adresse canonique. `vmmu read` et `mmu_read` restent les transports uniques : l’adresse exacte project-bound est leur seule entrée de sélection. Assets restent lus par le chemin hashé dédié; gates restent évalués par leur outil existant et ne sont pas présentés comme une simple ressource SQL.

**Preuves.** La fixture M11-J déclare une capability QUERY, son contract NOOP, sa policy ALLOW, exécute le runner NOOP réel puis enregistre une evidence TEST_PROOF réelle. Les deux tests contrôlent les champs persistants, cross-project, absent, non-mutation du journal d’audit et le schéma MCP `address` seul. Contrat : `2 passed in 2.05s`; cible evidence/execution/capability/MCP : `30 passed in 17.85s`; régression complète : **`549 passed in 63.57s`**.

**Verdict.** `M11-J = PASS` pour capability/execution/evidence en lecture exacte. Listing/history de preuves et evidences, assets dans READ, gates/work graph, symboles/profile, traversal `related`, mutations, VCS, Dashboard, parité ARET et hôtes réels restent hors lot. Artefact : `artifacts/m11_j_capability_execution_evidence_reads_2026-08-27.md`; mémoire : `MEM-DEC-185`.


### LOG-0242 — Commit local M11-J

| Champ | Valeur |
|---|---|
| Commit | `cecbc3c48cc848f00c11e0d17e27b606cca12585` — `feat: read execution and evidence records`. |
| Contenu | `ExecutionService.get`, extension `ReadService` pour capability/execution/evidence, contrat M11-J et continuité associée. |
| Validation liée | Contrat M11-J : `2 passed in 2.05s`; cible evidence/execution/capability/MCP : `30 passed in 17.85s`; intégral : `549 passed in 63.57s`; diff et scan de frontière : `PASS`. |
| Publication | Commit local créé ; aucune publication distante n’a été demandée ni effectuée. |
| Statut | `M11-J = PASS` dans le périmètre documenté. |


## LOG-0243 — 2026-08-27 — M11-K : parcours relationnel borné

**Résultat.** `ReadService.related` parcourt en largeur les relations d’une racine entité VERA canonique du projet courant. Les seules directions sont `INBOUND`, `OUTBOUND` et `BOTH`; profondeur 1–3 et cardinalité 1–50 sont contrôlées au Core. Les relations sont triées par identifiant, les voisins sont dédupliqués, et les cycles ne peuvent ni faire croître la réponse ni provoquer une boucle. CLI `related` et MCP `mmu_get_related` délèguent à ce service; le tool est inscrit au manifeste canonique.

**Preuves.** Le contrat construit un cycle d’entités et une branche, puis contrôle l’ordre BFS, la déduplication, les bornes, les racines invalides/cross-project et l’absence d’audit. Contrat : `1 passed in 0.16s`; cible relations/lecture/CLI/MCP : `27 passed in 17.29s`; régression intégrale : **`550 passed in 68.70s`**.

**Verdict.** `M11-K = PASS`. Il ne livre pas une requête de graphe générale, un filtrage relationnel, un traversal work/evidence, une mutation, une capability ou une gate. Artefact : `artifacts/m11_k_bounded_related_traversal_2026-08-27.md`; mémoire : `MEM-DEC-186`.

## LOG-0244 — 2026-08-27 — M11-L : READ exact de symbole

**Résultat.** Le type Core générique `symbol` est ajouté au READ exact de `ReadService`. Le record provient exclusivement de `SymbolService.get` après validation de l’adresse VERA canonique et de l’identité projet. CLI `read` et MCP `mmu_read` réemploient leur unique paramètre `address`; ni schéma MCP ni manifeste de tool ne sont élargis.

**Preuves.** Le contrat M11-L crée un symbole immutable avec metadata JSON, lit le record exact, vérifie l’absence d’audit, le refus cross-project et missing, et confirme que FIND ne retourne pas les symboles. Il exécute également `vmmu read` et un appel MCP stdio réel de `mmu_read`, dont le schéma reste `{address}`. Contrat : `3 passed in 2.07s`; cible lecture/CLI/MCP/symboles : `33 passed in 19.72s`; régression intégrale : **`553 passed in 67.48s`**.

**Verdict.** `M11-L = PASS`. Aucun FIND/listing, filtre kind/propriétaire, scan/résolution, chemin local, import, mutation, capability, gate, proof ou compatibilité historique n’est livré. Artefact : `artifacts/m11_l_symbol_read_2026-08-27.md`; mémoire : `MEM-DEC-187`.


## LOG-0245 — 2026-08-27 — M11-N : historique d’executions borné

**Résultat.** `ReadService.execution_history` retourne une projection compacte des executions persistées du projet actif, avec `max_items` de 1 à 100 et ordre total `started_at DESC, id DESC`. La projection exclut explicitement paramètres, environnement et résultat. CLI `list-executions` et MCP `mmu_list_executions` délèguent à cette primitive; le tool est ajouté au manifeste canonique hashé.

**Preuves.** La fixture crée trois executions `NOOP` par les services canoniques et contrôle ordre, borne, adresses project-bound, projection sans payload, refus des types/bornes invalides et absence d’audit. Elle appelle la CLI et le serveur/client MCP stdio; le schema MCP est `{max_items}` et une borne 101 est refusée. Contrat : `13 passed in 16.27s`; cible execution/lecture/CLI/MCP : `24 passed in 18.63s`; intégral : **`555 passed in 70.43s`**.

**Verdict.** `M11-N = PASS`. Aucun filtre, recherche, pagination, contenu execution/evidence, session de reprise, mutation, admission, proof, gate ou sync n’est ajouté. Artefact : `artifacts/m11_n_bounded_execution_history_2026-08-27.md`; mémoire : `MEM-DEC-188`.


## LOG-0246 — 2026-08-27 — M11-O : historique d’evidences borné

**Résultat.** `ReadService.evidence_history` retourne une projection compacte des evidences persistées du projet actif, avec `max_items` de 1 à 100 et ordre total `created_at DESC, id DESC`. La projection exclut strictement `content` et `created_by`. CLI `list-evidence` et MCP `mmu_list_evidence` délèguent à cette primitive; le tool est ajouté au manifeste canonique hashé.

**Preuves.** La fixture crée trois executions et evidences par les services canoniques, puis contrôle ordre, borne, adresses project-bound, projection sans contenu/acteur, refus des bornes invalides et absence d’audit. Elle appelle la CLI et le serveur/client MCP stdio; le schema MCP est `{max_items}` et une borne 101 est refusée. Contrat : `13 passed in 15.61s`; cible evidence/lecture/CLI/MCP : `27 passed in 17.87s`; intégral : **`557 passed in 67.38s`**.

**Verdict.** `M11-O = PASS`. Aucun filtre, recherche, pagination, contenu d’evidence, session de reprise, mutation, admission, proof, gate ou sync n’est ajouté. Artefact : `artifacts/m11_o_bounded_evidence_history_2026-08-27.md`; mémoire : `MEM-DEC-189`.


## LOG-0247 — 2026-08-27 — M11-E : rapport de couverture dérivé

**Résultat.** `compile_coverage_report` produit une projection `vera-coverage-report/v1` déterministe et hashée depuis l’identité du store, le manifeste MCP fermé, les ressources FIND/READ et les bornes d’historique. CLI `coverage` et MCP `mmu_get_coverage_report` exposent la même vue; le tool MCP est sans argument et appartient au manifeste hashé.

**Preuves.** Le contrat vérifie déterminisme, identité project-bound, surfaces symbol/historiques, liste FIND, absence de chemins workspace/profile et absence d’audit. CLI et MCP stdio sont exécutés réellement; le schéma du tool MCP est vide. Contrat : `14 passed in 16.88s`; intégral : **`559 passed in 71.67s`**.

**Verdict.** `M11-E = PASS` pour le rapport de couverture public limité. Les générateurs documentaires complets, pourcentages métier, hôtes réels, alias `mmu://`, VCS et parité ARET ne sont pas livrés ni déclarés couverts. Artefact : `artifacts/m11_e_derived_coverage_report_2026-08-27.md`; mémoire : `MEM-DEC-190`.


## LOG-0248 — 2026-08-27 — M11-F-A : bridge `mmu://` de lecture

**Résultat.** `parse_compat_address` accepte `mmu://` canonique comme alias d’entrée de lecture, puis délègue toute validation à `parse_address` en forme `vera://`. `ReadService.read` et `related` utilisent ce bridge; leurs sorties, records et identités restent `vera://`. CLI et MCP sont ainsi compatibles en lecture sans nouveau champ ou tool.

**Preuves.** Les tests couvrent adresse `mmu://` valide, formes invalides, une lecture Core, CLI réelle et MCP stdio réelle; toutes les réponses normalisent vers VERA persisté. Cible adressage/lecture : `12 passed in 3.09s`; intégral : **`560 passed in 68.01s`**.

**Verdict.** `M11-F-A = PASS`. Le parseur canonique VERA, les écritures, le schéma SQLite et le VCS ne changent pas. Pas d’alias `aret_*`, de lecteur `ARET://`, de migration d’adresses, de provider multi-VCS ou de parité ARET. Artefact : `artifacts/m11_fa_mmu_read_address_bridge_2026-08-27.md`; mémoire : `MEM-DEC-191`.


## LOG-0249 — 2026-08-27 — M11-F-B : diagnostic VCS local minimal

**Résultat.** `inspect_vcs` observe uniquement le marqueur `.git` project-local sans lancer Git. Il retourne `GIT/OBSERVED` pour un répertoire régulier, `NONE/NO_VCS` s’il est absent, et refuse les marqueurs symlinkés ou non-répertoires. `ReadService.vcs_status`, CLI `vcs-status` et MCP `mmu_get_vcs_status()` exposent ce résultat sans argument de sélection; le tool est manifesté/hashé.

**Preuves.** Le contrat couvre no-VCS, Git marker régulier, symlink ambigu et absence d’audit. La cible Core/manifeste/CLI/MCP compte `13 passed in 14.56s`; la suite intégrale compte **`561 passed in 67.71s`**.

**Verdict.** `M11-F-B = PASS`. Aucun subprocess/réseau, revision, branche, remote, log, sync, commit/push, provider Mercurial/SVN ou parité VCS n’est livré. Artefact : `artifacts/m11_fb_local_vcs_status_2026-08-27.md`; mémoire : `MEM-DEC-192`.


## LOG-0250 — 2026-08-27 — M11-D-A : vue Dashboard d’état projet

**Résultat.** Le bridge desktop expose `project.status` avec entrée `{}` seulement, puis compose le rapport Core de couverture et le statut VCS local du projet déjà initialisé. Rust expose `project_status` sans argument; React affiche tools MCP déclarés et VCS après une initialisation confirmée. L’ancien calcul implicite d’initialisation est remplacé par un état explicite mis à jour seulement après succès.

**Preuves.** `tests/test_desktop_bridge.py` valide la lecture dérivée et le refus d’une racine client : `7 passed in 1.04s`. `pnpm build` passe. Avec Rust stable 1.98, PyInstaller, GTK/WebKit et le sidecar native construits dans le sandbox, `cargo test` passe : `2 passed in 0.14s`. Python intégral : **`562 passed in 65.34s`**.

**Verdict.** `M11-D-A = PASS`. Le sidecar et `target/` générés sont ignorés par Git. Aucun builder visuel Profile/Capability/Gate, template enrichi, hôte réel ou parité ARET n’est déclaré livré. Artefact : `artifacts/m11_da_dashboard_project_status_2026-08-27.md`; mémoire : `MEM-DEC-193`.


## LOG-0251 — 2026-08-27 — M11-D-C : builder Dashboard de Capability

**Résultat.** `capability_builder` valide et prévisualise une déclaration à cinq champs, lie le preview au hash du catalogue courant puis délègue une application confirmée à `CapabilityService.create`. Le bridge expose `capability.preview`/`capability.apply` avec ensembles de champs exacts et cache nonce-scoped; Tauri et React fournissent un formulaire sans runner/commande/path/policy.

**Preuves.** Core/bridge : `9 passed in 1.12s`; React : `pnpm build PASS`; Tauri natif : `2 passed in 0.10s`; Python intégral : **`564 passed in 64.55s`**. Preview non mutateur, confirmation, stale catalog, id/kind invalides et champ bridge injecté sont refusés.

**Verdict.** `M11-D-C = PASS`. M11-D-B (Profile) est différé : `profile_hash` participe à l’identité SQLite et requiert un protocole de rebind atomique dédié. Artefact : `artifacts/m11_dc_dashboard_capability_builder_2026-08-27.md`; mémoire : `MEM-DEC-194`.


## LOG-0252 — 2026-08-27 — Garde d’identité Project Profile

**Résultat.** L’audit M11-D-B confirme qu’un changement sémantique de Project Profile change `profile_hash`, `project_identity` et `project_hash`. Sans protocole de rebind explicite, `MemoryStore.open` refuse correctement le store par `StoreIdentityError`.

**Preuves.** `tests/test_profile_edit_identity_guard.py` change uniquement `project.description` puis vérifie le refus : `1 passed in 0.10s`. La régression intégrale atteint **`565 passed in 64.32s`**.

**Verdict.** L’édition Profile est `NOT_ELIGIBLE` à ce stade, non absente par oubli. Le futur M11-D-B devra prouver une préparation, confirmation/fraîcheur, coordination durable profile+SQLite, rollback et reprise Doctor. Aucun rebind ni écriture Profile n’est introduit. Mémoire : `MEM-DEC-195`.

## LOG-0253 — M11-D-D1 : Dashboard Gate Policy Builder

**Statut : PASS dans le périmètre explicitement borné.**

Le Core ajoute un preview de déclaration de policy de Gate, hashé contre les exigences actuelles, et une application déléguée à `GateService.declare_policy`. Le bridge Desktop conserve le preview dans la session liée au nonce, exige des ensembles de champs exacts, une confirmation explicite et rejette les previews inconnus ou périmés. L’interface expose seulement l’identifiant de Gate, les modes fermés `ALL`/`ANY`/`AT_LEAST` et le seuil conditionnel.

Les validations observées sont : tests ciblés Core/bridge `19 passed in 1.41s`, build React PASS, tests Tauri natifs `2 passed in 0.10s`, régression Python intégrale `576 passed in 66.88s`. L’artefact est `docs/continuity/artifacts/m11_dd1_dashboard_gate_policy_builder_2026-08-27.md`.

**Exclusions vérifiées :** ce lot ne crée aucune Gate structurelle, ne modifie aucune exigence, ne collecte ni evidence ni admission, ne produit aucun verdict et ne permet pas de changer une policy après scellement. Il n’ajoute aucun concept ARET au Core ni shell, processus ou réseau au builder.

## LOG-0254 — M11-D-D2 : Dashboard Gate Structure Builder

**Statut : PASS dans le périmètre explicitement borné.**

Le Dashboard propose un preview non mutateur de structure Gate : `gate_id`, `work_item_id`, evidence principale et exigences exactes. Le bridge exige l’enveloppe authentifiée, les champs fermés et le cache de preview lié au nonce; l’application exige confirmation et rejettera un snapshot modifié ou périmé.

Le Core fournit `GateService.declare_with_requirements`, qui valide work-item et evidences existants, interdit les doublons et inscrit la Gate ainsi que toutes les exigences dans une transaction SQLite unique. Aucune Gate partielle ne peut persister après une erreur.

Les validations observées sont : ciblés Core/bridge `26 passed in 1.78s`, build React PASS, tests Tauri natifs `2 passed in 0.10s`, régression Python intégrale `589 passed in 64.46s`, `git diff --check` PASS et scan de frontière PASS.

**Exclusions vérifiées :** aucune admission, evidence, exécution, verdict ou évaluation n’est créable depuis le Dashboard. Le lot n’édite pas les exigences après déclaration de policy et n’ajoute aucun concept ARET, shell, processus ou réseau au Core.

## LOG-0255 — M11-D-B : Rebind contrôlé du Project Profile

**Statut : PASS dans le périmètre explicitement borné.**

Le builder Dashboard de Profile n’accepte que `projectName` et `projectDescription`. Il produit un preview contenant les hashes et identités avant/après; l’application exige cache bridge lié au nonce, confirmation explicite et recalcul de fraîcheur. Le Core n’expose pas d’écriture SQLite brute : `MemoryStore.rebind_identity` met à jour l’identité persistée dans une transaction auditée.

Le protocole écrit d’abord une sauvegarde et un journal durable à permissions restreintes. Après l’alignement SQLite, le Profile est remplacé par écriture atomique. Un test simule une interruption entre ces étapes : le journal persiste, Doctor produit un échec explicite `profile_rebind`, puis `recover_project_profile_rebind` termine uniquement le contenu journalisé et rétablit l’ouverture sous identité cohérente.

Validations : tests ciblés `17 passed in 2.59s`, build React PASS, Tauri natif `2 passed in 0.10s`, régression Python intégrale `593 passed in 63.09s`, `git diff --check` PASS et scan de frontière PASS.

**Exclusions vérifiées :** l’UI ne modifie pas l’identifiant, le domaine, workspace, storage, catalogues, policy, capability, Gate, evidence, admission ou verdict. Doctor ne répare jamais implicitement; les divergences de journal ou de Profile sont refusées fail-closed. Aucun concept ARET, shell, processus ou réseau n’est ajouté au Core.

## LOG-0256 — M11-D Doctor Recovery : reprise Profile explicitement confirmée

**Statut : PASS dans le périmètre de reprise Profile.**

Le Doctor ajoute le contrôle read-only `profile_rebind`, qui signale un journal de rebind persistant sans tenter de réparer. Le bridge/Tauri/Dashboard exposent séparément un preview de reprise sans entrée client puis une application confirmée. Le Core recalcule le journal et le hash courant de Profile, et refuse journal multiple, symlinké, illisible ou divergent.

La validation observée est : tests ciblés `16 passed in 2.49s`, build React PASS, Tauri `2 passed in 0.10s`, régression Python `593 passed in 64.28s`, `git diff --check` et scan de frontière PASS. La reprise n’ajoute aucune capacité client d’écrire un chemin, une identité, une evidence, une admission ou un verdict.

## LOG-0257 — M11-D-B2 : rebind structurel d’identifiant et domaine

**Statut : PASS dans le périmètre explicitement borné.**

Le rebind contrôlé étend le preview aux quatre champs `projectId`, `projectName`, `projectDomain` et `projectDescription`. Après confirmation et recalcul de fraîcheur, l’identité persistée est réalignée dans SQLite et les adresses dérivées sont relues avec le nouvel identifiant. Le bridge refuse toute entrée workspace, storage, catalogue, policy ou chemin.

Validation : ciblés Core/bridge `15 passed in 1.42s`, build React PASS, Tauri `2 passed in 0.10s`, intégral Python `595 passed in 64.98s`, diff et scan frontière PASS. Les mutations physiques du runtime et des catalogues restent expressément hors lot.

## LOG-0258 — Conception préalable de migration physique Profile/runtime

**Statut : DESIGN_REQUIRED.**

La résolution actuelle ancre un Profile `project.yaml` sous `.vera-mmu`; déplacer workspace ou storage modifie l’ancre, la SQLite WAL, les artefacts et les catalogues. Ces mutations doivent donc passer par préflight, journal durable hors runtime, inventaire/hash, renommages atomiques même filesystem, reprise confirmée et validation Doctor. Aucune écriture de chemin n’est implémentée dans cette décision.

## LOG-0259 — Générateur documentaire project-bound

**Statut : PASS pour la projection documentaire read-only.**

Le Core compile un bundle déterministe `MMU_SETUP`, `TOOLS`, `GATES`, `POLICIES`, `ARCHITECTURE` et `MAINTENANCE` depuis le Profile, les catalogues et la couverture VERA. Il vérifie que l’identité du Profile est celle du store et ne crée aucune transaction/audit. La validation atteint `596 passed in 64.40s`, avec diff et scan de frontière verts.

L’export project-local confirmé et les façades publiques restent ouverts : cette entrée ne les assimile pas à une livraison.

## LOG-0260 — Documentation générée via CLI

**Statut : PASS pour la projection documentaire CLI read-only.**

La commande `vmmu documentation` compile le bundle project-bound de six documents et son hash depuis l’identité, le Profile, les catalogues et la couverture. Les catalogues absents sont explicitement projetés `NOT_CONFIGURED`; aucune écriture de fichier ni d’audit n’est déclenchée. Les tests ciblés ont passé à `3 passed in 0.25s` et la régression complète à `597 passed in 65.16s`.

## LOG-0261 — Documentation générée via MCP

**Statut : PASS pour la projection documentaire MCP read-only.**

`mmu_get_documentation` ne prend aucun argument client et s’appuie sur le Profile lié au workspace du store. Une session MCP stdio réelle a détecté puis permis de corriger l’hypothèse erronée d’un Profile forcément sous le runtime. La suite complète passe à `598 passed in 67.00s`; aucune écriture, chemin client, processus ou réseau n’est ajouté.

## LOG-0262 — Documentation générée dans le Dashboard

**Statut : PASS pour la consultation Desktop read-only.**

`project.documentation` est une opération bridge allowlistée sans entrée; Tauri délègue au bridge stdio authentifié et la console rend le bundle et son hash comme résultat inspectable. Les validations ciblées atteignent `17 passed in 10.34s`, le build React et les tests Tauri sont verts. Aucun export, chemin destination ni mutation de document n’est exposé.

## LOG-0263 — Mise à jour du rapport de couverture dérivé

**Statut : PASS.**

La couverture dérivée reclasse précisément la documentation générée read-only et l’alias d’entrée `mmu://`, sans les confondre avec l’export documentaire ou une migration d’adresses persistées. Les tests ciblés passent et la régression complète atteint `598 passed in 65.18s`; les limites Dashboard global, VCS multi-provider, parité Pack et hôte réel restent explicitement non couvertes.

## LOG-0264 — Alias `mmu://` de lecture vérifié sur MCP

**Statut : PASS pour l’entrée READ seulement.**

Une session MCP stdio réelle confirme que `mmu_read` accepte une adresse `mmu://` canonique et retourne exclusivement `vera://`. Aucune persistance, mutation, migration de schéma d’adresse ou parité ARET n’est introduite. Les tests addressing/MCP passent à `9 passed in 10.81s`.

## LOG-0265 — Découverte d’ancre Profile non ambiguë

**Statut : PASS.**

Le bridge reconnaît exactement un Profile non symlinké sous `.vera-mmu/project.yaml` ou `project.yaml` racine, et refuse deux candidats concurrents. Le lot n’effectue ni déplacement, ni mutation d’identité et prépare seulement l’ancre requise par une migration physique sûre. Tests bridge/workspace `20 passed in 1.29s`; régression `600 passed in 65.23s`.

## LOG-0266 — M11-D-B2 : branchement de la copie vérifiée au journal
**Statut : PASS préparatoire dans le périmètre borné.**
`_copy_tree_verified()` accepte désormais un journal de migration. Pour chaque fichier, il persiste `COPYING` avant `copy2`, vérifie le hash SHA-256 et la taille, puis persiste `VERIFIED`. Lorsque la persistance de `VERIFIED` échoue après la copie, le journal conserve `EXECUTING` et l’événement `COPYING`, tandis que la cible partielle est supprimée ; la reprise est donc requise et aucun succès n’est inféré. L’exécuteur principal refuse toujours `COPY_VERIFY_SWITCH`.

Validation : `tests/test_profile_migration.py` — `10 passed`; suite Python — `622 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; scan de frontière Core PASS hors alias de compatibilité `ARET_MMU_BARRIER_OFF`; Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `589312e`. Suivi : fermer la machine d’états globale, valider l’inventaire avant bascule, traiter SQLite/WAL/SHM et tester les interruptions avant toute activation de `COPY_VERIFY_SWITCH`.

## LOG-0267 — M11-D-B2 : machine d’états globale du journal
**Statut : PASS préparatoire dans le périmètre borné.**
Le Core expose `transition_profile_migration_state()` et applique une allowlist atomique des transitions. Les sauts `PLANNED → SWITCHING/COMMITTED`, les états inconnus et toute transition après `COMMITTED` sont refusés. Les états déclarés couvrent `PLANNED`, `COPYING`, `VERIFIED`, `SWITCHING`, `COMMITTED`, `DIVERGED`, `RECOVERY_REQUIRED` et `ROLLED_BACK`; `EXECUTING` reste une compatibilité contrôlée du chemin same-filesystem. La validation complète de l’inventaire, la bascule inter-filesystems et la reprise correspondante restent ouvertes.

Validation : `tests/test_profile_migration.py` — `12 passed`; suite Python — `624 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; tests Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `1f65aba`. Suivi : brancher cette machine d’états sur la validation complète de copie/inventaire, puis traiter SQLite/WAL/SHM et les interruptions avant toute activation de `COPY_VERIFY_SWITCH`.

## LOG-0268 — M11-D-B2 : validation canonique de l’inventaire avant bascule
**Statut : PASS préparatoire dans le périmètre borné.**
`validate_profile_migration_inventory()` effectue une validation read-only du runtime cible. Elle exige `COPYING → VERIFIED` par fichier attendu, vérifie les hashes et tailles source/cible, les symlinks, les fichiers inattendus et le contenu du Profile cible. Elle renvoie `READY_FOR_SWITCH` seulement lorsque toutes les preuves sont présentes, `RECOVERY_REQUIRED` pour les absences ou progressions incomplètes et `DIVERGED` pour les divergences de cible. Les mouvements de racines workspace restent explicitement bloquants faute de validation dédiée.

Validation : `tests/test_profile_migration.py` — `14 passed`; suite Python — `626 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; scan de frontière Core PASS; tests Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `4a8e314`. Suivi : intégrer la validation des racines workspace, puis traiter SQLite/WAL/SHM et les interruptions avant toute activation de `COPY_VERIFY_SWITCH`.

## LOG-0269 — M11-D-B2 : validation SQLite/WAL/SHM et schéma cible
**Statut : PASS préparatoire dans le périmètre borné.**
`validate_sqlite_migration_target()` compare en lecture seule SQLite et les éventuels sidecars `-wal`/`-shm`, vérifie hashes et tailles, exécute `PRAGMA integrity_check`, calcule une empreinte canonique de `sqlite_master` et refuse les symlinks ou artefacts non réguliers. Les états `DIVERGED` couvrent corruption, divergence de schéma et divergence de sidecar. La fonction n’effectue pas de checkpoint, de copie ni de bascule ; l’intégration opérationnelle dans l’exécuteur reste ouverte.

Validation : `tests/test_profile_migration.py` — `16 passed`; suite Python — `628 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; scan de frontière Core PASS; tests Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `2f89d3c`. Suivi : intégrer checkpoint et validation SQLite/WAL/SHM dans la séquence `SWITCHING`, puis tester les interruptions et les reprises.

## LOG-0270 — M11-D-B2 : barrière SQLite dans la validation d’inventaire
**Statut : PASS préparatoire dans le périmètre borné.**
La validation d’inventaire appelle `validate_sqlite_migration_target()` pour les entrées `kind=sqlite`. Une corruption de la cible, une divergence de schéma ou un sidecar ambigu est maintenant remonté dans le rapport d’inventaire et empêche `READY_FOR_SWITCH`. Le checkpoint WAL et la copie opérationnelle ne sont pas encore intégrés à l’exécuteur.

Validation : `tests/test_profile_migration.py` — `16 passed`; suite Python — `628 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; scan de frontière Core PASS; tests Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `252fbcb`. Suivi : intégrer le checkpoint WAL et la séquence de copie SQLite/WAL/SHM avant `SWITCHING`.

## LOG-0271 — M11-D-B2 : préparation opérationnelle SQLite/WAL/SHM
**Statut : PASS préparatoire dans le périmètre borné.**
`prepare_sqlite_migration_artifacts()` effectue le checkpoint WAL, copie SQLite et les sidecars présents vers des fichiers temporaires, vérifie hash et taille, remplace atomiquement les cibles, journalise `COPYING/VERIFIED`, appelle la validation SQLite cible et supprime les cibles partielles en cas d’interruption. Le branchement dans la machine d’états globale `SWITCHING`, les racines workspace et la reprise complète restent ouverts.

Validation : `tests/test_profile_migration.py` — `18 passed`; suite Python — `630 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; scan de frontière Core PASS; tests Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `8f62826`. Suivi : intégrer cette préparation dans l’exécuteur inter-filesystems et prouver les interruptions autour de `SWITCHING`.

## LOG-0272 — M11-D-B2 : exécuteur same-filesystem sous preuve SQLite
**Statut : PASS dans le périmètre borné.**
L’exécuteur journalise `EXECUTING`, passe par `SWITCHING` après checkpoint SQLite, déplace le runtime et les racines autorisées, vérifie l’empreinte SQLite après déplacement, puis journalise `COMMITTED` uniquement après cette preuve. Une erreur tente le rollback et marque le journal `ROLLED_BACK`. La stratégie `COPY_VERIFY_SWITCH` reste refusée.

Validation : `tests/test_profile_migration.py` — `18 passed`; suite Python — `630 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; tests Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `c4cb7bc`. Suivi : intégrer la validation complète des racines workspace et construire la reprise des phases `SWITCHING`/`ROLLED_BACK` avant d’activer l’inter-filesystems.

## LOG-0273 — M11-D-B2 : reprise prouvée EXECUTING/SWITCHING
**Statut : PASS dans le périmètre borné.**
La reprise accepte les journaux `EXECUTING` et `SWITCHING`. Elle finalise uniquement si le runtime cible, le Profile cible, SQLite et les sidecars sont cohérents. Elle restaure vers `PLANNED` uniquement lorsque le runtime source et le backup Profile sont prouvés. Les runtimes simultanés, Profiles divergents, SQLite invalides et racines workspace ambiguës sont classés `RECOVERY_REQUIRED`.

Validation : `tests/test_profile_migration.py` — `20 passed`; suite Python — `632 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; tests Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `e35c13a`. Suivi : intégrer la preuve des racines workspace et construire les scénarios d’interruption inter-filesystems avant toute activation de `COPY_VERIFY_SWITCH`.

## LOG-0274 — M11-D-B2 : inventaire des racines workspace
**Statut : PASS préparatoire dans le périmètre borné.**
Le preview et le journal persistent `workspace_inventory` avec source, cible, type, taille et hash pour chaque fichier des racines workspace déplacées. La validation read-only contrôle sources/cibles, symlinks et entrées inattendues, classe les absences `RECOVERY_REQUIRED` et les divergences/ambiguïtés `DIVERGED`. La copie inter-filesystems et la progression workspace dédiée restent ouvertes.

Validation : `tests/test_profile_migration.py` — `20 passed`; suite Python — `632 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; tests Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `acb59b3`. Suivi : brancher la copie workspace journalisée et sa reprise avant toute activation de `COPY_VERIFY_SWITCH`.

## LOG-0275 — M11-D-B2 : COPY_VERIFY_SWITCH complet
**Statut : PASS dans le périmètre implémenté.**
Lorsque le preview sélectionne `COPY_VERIFY_SWITCH`, le runtime et les racines workspace sont copiés fichier par fichier avec progression journalisée `COPYING/VERIFIED`, vérification hash/taille et validation complète avant `SWITCHING`. Les sources sont supprimées seulement après bascule. Une erreur avant `SWITCHING` nettoie les cibles et marque `ROLLED_BACK`; une erreur pendant `SWITCHING` conserve le journal et marque `RECOVERY_REQUIRED`.

Validation : `tests/test_profile_migration.py` — `21 passed`; suite Python — `633 passed, 49 subtests passed`; `compileall` PASS; `git diff --check` PASS; build TypeScript/Vite PASS; scan frontière Core PASS; tests Tauri/Cargo `UNKNOWN` car `cargo` est indisponible.
Commit fonctionnel : `354e4dd`. La séquence de migration physique universelle est maintenant implémentée dans le périmètre couvert par les invariants et les tests ; toute extension future doit ajouter ses preuves avant activation.

## LOG-0276 — Intégration de la spécification finale Universal Dev-MMU
**Statut : PASS documentaire.**
Le document fourni `UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md` est intégré dans `docs/UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md` et référencé par le handoff et le workplan. SHA-256 : `d8e5d01b673e243e0104a30fb62328bc2a7fc650373ab91b1a103652a1737d75`. Cette intégration versionne la référence ; elle ne transforme pas la Definition of Done globale en statut livré.

## LOG-0277 — Ouverture des surfaces d’écriture CLI et MCP
**Statut : PASS dans le périmètre implémenté.**
Un audit de vérification a établi que `KnowledgeService.append`, `FrontService.update/replace`, `HandoffService.prepare`, `WorkItemService.create`, `GateService.declare` et `ProofService.promote` existaient, étaient testés, mais n’étaient atteignables par aucune surface : la CLI n’importait aucun de ces services et la façade MCP n’exposait que des lectures. `ProofService.promote`, qui porte l’invariant I004, n’avait aucun appelant hors tests.

`write_api.WriteService` est ajouté comme contrepartie mutante de `ReadService`, câblé à la CLI et à MCP. Deux impédances déclaratif/store bloquaient le parcours et sont résolues : les types knowledge sont déclarés en majuscules et stockés en minuscules, et le catalogue de capabilities était validé et hashé sans jamais être matérialisé en SQLite.

Le secret de promotion est lu dans `VERA_MMU_PROOF_HMAC_SECRET`, jamais fourni par le client et jamais placé sous `.vera-mmu/`, que la synchronisation mémoire commit sur Git. Une policy exigeant HMAC sans secret est un refus explicite, jamais une promotion non signée.

Validation : suite Python — `686 passed, 55 subtests passed`; `git diff --check` PASS; scan frontière Core PASS; parcours MCP stdio réel PASS. Couverture de l’API §24 : `24/30` outils, contre `14/30` avant ce lot. Restent non livrés : `mmu_restore`, `mmu_get_resume_brief`, `mmu_get_resume_status`, `mmu_attach_proof`, `mmu_export`, `mmu_import_bundle`.

## LOG-0278 — Critère de sortie Annexe B franchi sur les six domaines
**Statut : PASS dans le périmètre implémenté.**
`generate` refusait tout projet fraîchement initialisé : les six templates ne différaient que par leur liste de types d’entités et émettaient `capabilities: []`, alors que la génération exige au moins une capability `ALLOW`. Les capabilities et gates sont désormais déclarées par domaine, et la synchronisation matérialise le catalogue déclaré.

Un second défaut, invisible par la seule voie déclarative, a été trouvé en exécutant la chaîne : une capability peut passer la génération et rester inexécutable si son schéma de paramètres ne correspond pas au runner qu’elle nomme. Les runners `EVIDENCE_FIELDS` et `EVIDENCE_HASH` n’acceptent que `{validator_id, evidence_id}` ; les champs métier sont portés par `inputs` et deviennent les clés requises du validator. Chaque domaine déclare en outre un collecteur `NOOP`, sans lequel aucune evidence ne peut être rattachée à une execution.

Validation : `scan → init → validate → generate → doctor` rejoué pour `software`, `data`, `research`, `documentation`, `game` et `hardware`; déterminisme du `mcp_build_hash` vérifié; chaîne complète capability → evidence → validation → admission → promotion `PROVEN` signée, avec refus prouvé sur evidence incomplète.

## LOG-0279 — Doctor complété face à la spécification §45
**Statut : PASS dans le périmètre implémenté.**
Le rapport fusionnait capabilities, gates et policies en une ligne `catalogs`, omettait `HMAC` et `HOOKS`, et n’avait pas de rendu humain. Les trois catalogues sont désormais des lignes distinctes attribuées au fichier que l’erreur nomme, `hmac` signale une policy exigeant une signature dont le secret est absent avant qu’une promotion ne soit tentée, `hooks` vérifie que toute intégration déclarée est installée, et `vmmu doctor --human` rend les lignes alignées décrites par la spécification. Le secret n’apparaît jamais dans le rapport, ce qu’un test garantit.

## LOG-0280 — Péremption constatée du registre de découplage
**Statut : OBSERVED, aucune ligne promue.**
`DECOUPLING_MATRIX.md` est désigné par la spécification §52 comme la référence d’avancement. Son recomptage donne `75` lignes : `72 SPLIT`, `2 IN_PROGRESS`, `1 BLOCKED`, `0 DONE`. Son en-tête se date lui-même « registre M0.2, complété par l’avancement M1 » alors que le dépôt est à M11.

Aucune ligne n’est promue par ce lot : les travaux ci-dessus portent sur les surfaces universelles, pas sur la parité ARET que le registre mesure. Le constat est enregistré tel quel afin qu’aucune affirmation de parité ne s’appuie sur un registre qui ne mesure plus l’état réel. Sa remise en service, ou son remplacement formel, reste un lot distinct.

## LOG-0281 — API Core §24 complète
**Statut : PASS dans le périmètre implémenté.**
Les six outils restants du contrat §24 sont livrés : `mmu_get_resume_brief`, `mmu_get_resume_status`, `mmu_export`, `mmu_import_bundle`, `mmu_restore` et `mmu_attach_proof`. La couverture passe de `24/30` à `30/30`.

Deux choix de conception méritent d’être tracés. D’abord, `mmu_import_bundle` vérifie et décrit sans écrire, tandis que `mmu_restore` exécute après confirmation : plutôt que deux noms pour une même opération, la séparation preview/confirmation reprend la doctrine appliquée partout ailleurs dans le produit. Ensuite, un bundle est désigné par identifiant et jamais par chemin : `project_bundle_path` le résout dans le répertoire de bundles du projet après application de la règle canonique d’identifiant, de sorte qu’aucun séparateur ni segment de traversée n’atteint le système de fichiers.

Un comportement a été épinglé par test plutôt que contourné : restaurer un bundle dans le projet qui l’a produit est refusé comme fusion, car l’export écrit l’archive dans le runtime, qui ne correspond donc plus à son propre snapshot. Le bundle est fait pour voyager vers une cible vide de même identité.

`resume_status` ne retourne jamais la clé d’état de session dérivée de l’identité hôte : lire un statut n’est pas une raison de l’exposer.

Validation : suite Python — `699 passed, 55 subtests passed`; `git diff --check` PASS; scan frontière Core PASS.

## LOG-0282 — Tauri natif : build, paquet et sidecar prouvés
**Statut : PASS partiel, borne explicitement déclarée.**
Les audits précédents classaient le front Tauri « non démontré » parce que `cargo` était indisponible dans leur environnement. Il l’était ici, et la chaîne a été menée jusqu’au bout.

Prouvé par exécution :
- `cargo check --locked` PASS après installation des bibliothèques système GTK/WebKit ;
- `pnpm build` (tsc --noEmit puis Vite) PASS ;
- `tauri build --bundles deb` PASS en profil release, `Finished 1 bundle` ;
- le paquet `VERA-MMU_0.1.0-4_amd64.deb` (34 Mo) contient l’application et le sidecar `vmmu-desktop-bridge` ;
- l’application extraite du paquet démarre sous affichage virtuel et reste vivante, avec pour seule sortie un avertissement EGL d’accélération matérielle propre au conteneur ;
- le sidecar extrait du paquet répond en stdio : `project.scan` retourne un rapport `OBSERVED` hashé, `project.init.preview` retourne les 7 fichiers et son `preview_hash`, un nonce invalide est refusé `NONCE_INVALID` et une application sans confirmation est refusée `CONFIRMATION_REQUIRED`.

Une précondition d’ordre de build, jusqu’ici non documentée, a été identifiée : le sidecar Python doit être construit avant `cargo`, faute de quoi le build échoue sur `resource path binaries/vmmu-desktop-bridge-… doesn't exist`. Ce n’est ni un défaut de code ni une dette, mais un ordre à écrire pour que chaque nouvel arrivant ne le redécouvre pas.

**Ce qui reste non prouvé :** le dialogue WebView ↔ Rust ↔ sidecar déclenché par la sélection humaine d’un dossier dans le dialogue natif. Le parent Rust ne démarre le sidecar qu’à cette action, qui ne peut pas être simulée honnêtement ici. Le statut correct est donc : **build natif, paquet et sidecar prouvés ; parcours utilisateur interactif toujours à observer sur une machine réelle.**

## LOG-0283 — Correction du chiffrage du registre de découplage
**Statut : correction documentaire.**
LOG-0280 a décrit `DECOUPLING_MATRIX.md` comme comptant « 75 lignes, 0 `DONE` » et comme n’ayant « pas suivi les lots postérieurs à M1 ». Les deux formulations sont fautives et sont corrigées ici.

Le registre suit **16 couplages** (`C01`–`C16`), pas 75 : le comptage précédent additionnait les lignes mères et environ 59 sous-lignes des tables d’avancement observé, où un même couplage reparaît à chaque lot (`C03` y figure 20 fois, `C16` 19 fois). Et il a bien été tenu au-delà de M1 : 33 sections d’avancement couvrent M1, M2.1 à M2.14, M3.S1 et M4.1 à M4-C. Seul son en-tête est resté daté de M0.2/M1.

Le constat de fond est inchangé et reste le seul point qui compte : **aucune ligne mère n’est `DONE`**, 14 sont `SPLIT` et 2 `IN_PROGRESS`. Le registre enregistre donc scrupuleusement ce qui a été observé sans jamais conclure une parité, ce que sa propre règle interdit sans test de parité exécuté. Aucune affirmation de parité ARET ne peut s’appuyer sur lui en l’état.

## LOG-0284 — Finalisation du MCP face à la spécification
**Statut : PASS dans le périmètre implémenté.**
Quatre chapitres de la spécification touchant le MCP étaient partiellement livrés ; ils sont clos ici.

**§20 et §26 — playbook et instructions.** Le playbook était écrit à l’initialisation et lu par personne : `mcp_instructions.py` déclarait explicitement ne pas le charger. Le module `playbook.py` porte désormais les huit lois universelles du Core et charge, borne, hashe le playbook du projet. Les instructions composent exactement les cinq sections exigées — doctrine, playbook cité verbatim, règles de capabilities, résumé des policies, protocole de reprise — et sont liées au Profile Hash. Éditer une règle du projet change le hash des instructions, ce qu’un test épingle.

**§25 — compilateur.** Le pipeline de seize étapes est explicite, ordonné et enregistré étape par étape. La validation statique est bloquante : elle refuse un build dont les instructions sont liées à un autre manifeste ou à un autre profil, dont la configuration hôte ne cite ni l’un ni l’autre, dont les instructions omettent une capability déclarée, ou dont une sortie porte une clé `command`, `argv`, `shell`, `interpreter`, `cwd` ou `executable`. Chaque entrée déclarative atteint le hash du package.

**§28 — contrat de commandes.** Couverture portée de `8/13` à `13/13`, avec l’alias `mmu`. `validate` contrôle les fichiers déclaratifs **et leurs relations** : gate référençant une capability non déclarée, intégration activée sans agent profile, contrat de reprise sans section requise.

**§54 — réparabilité.** `install_repair.py` répare ce qui est honnêtement réparable : les fichiers déclaratifs dérivables du profile. Une mémoire SQLite absente n’est jamais recréée — la remplacer par une base vide masquerait précisément ce que le Doctor doit signaler.

Validation : suite Python — `749 passed, 55 subtests passed` ; parcours complet du contrat §28 rejoué sur un projet neuf, onze étapes nominales vertes et refus attendu sur bundle inexistant ; cycle casse → Doctor `FAIL` → réparation → Doctor `PASS` vérifié.

**Hors périmètre de ce lot :** le Dashboard configurateur visuel des §29 à §34. L’application desktop reste un assistant d’installation ; l’IDE de configuration complet décrit par la spécification n’est pas livré et ne doit pas être revendiqué.

## LOG-0285 — Décision : le Dashboard configurateur est une cible livrable
**Statut : décision du propriétaire, enregistrée. Aucun code écrit dans cette entrée.**

LOG-0284 rangeait les §29 à §34 hors périmètre. Le propriétaire a tranché l’inverse : le Dashboard configurateur visuel doit être **pleinement livré**. La mention « hors périmètre » de `todo.md` est donc remplacée, et `docs/continuity/REMAINING_WORK.md` découpe la cible en onze lots `B1` à `B11`.

**État mesuré du départ, pour que le découpage ne repose pas sur une impression.** `apps/desktop/ui/src/DesktopConsole.tsx` est une console d’une seule page, huit panneaux, 207 lignes, adossée à 24 méthodes de bridge. Du parcours en dix-huit étapes de §29.2, elle couvre les étapes 1 et 2, l’étape 4 partiellement, les étapes 9 et 10 sous une forme déclarative bornée, l’étape 13, et les étapes 15 à 18. Manquent l’étape 3, les étapes 5 à 8, les étapes 11, 12 et 14, ainsi que la forme complète de §32 et §33.

**Trois règles fixées pour tous les lots.** Aucun écran n’écrit sans le cycle preview → fraîcheur → confirmation → écriture atomique ou refus. L’interface ne fournit jamais commande, chemin, URL ou runner libre : elle compose à partir de ce que le Core déclare (I008). Toute validation vit dans le Core et est testée en Python ; l’interface l’affiche sans la réimplémenter, faute de quoi les deux divergeraient et c’est l’interface qui mentirait.

**Un point de tension est identifié plutôt que contourné.** §32 affiche un champ « commande » et I008 interdit qu’un client en fournisse une. La conciliation retenue, à écrire dans le lot `B6` : l’interface choisit parmi les profils de runner déclarés et leurs paramètres bornés, et n’envoie jamais de chaîne de commande.

**Ligne de sécurité retirée.** La ligne de `todo.md` demandant la révocation d’un jeton jetable est supprimée sur décision du propriétaire. Cette entrée ne la réintroduit pas ; elle en enregistre seulement le retrait, conformément à l’append-only.

## LOG-0286 — Trois causes racines derrière vingt-trois échecs de CI
**Statut : correctifs écrits et verts sur Linux x64. Verdict Windows en attente du prochain run.**

Le run `desktop-packaging.yml` #44 est rouge sur les deux runners. Premier fait à établir avant tout diagnostic : **ce rouge précède ce lot**. Au commit `afc931f` du 12 septembre, sur `main`, Linux tombait déjà sur les trois mêmes tests (`3 failed, 630 passed`) et Windows sur seize. Aucune régression de branche ; une dette de portabilité jamais traitée.

Les vingt échecs Windows et les trois échecs Linux se réduisent à trois causes.

**1. `os.fsync` sur une poignée ouverte en lecture seule — huit échecs.** `bundles.py` refermait l’archive zip puis la rouvrait en `"rb"` pour la synchroniser avant `os.replace`. Windows ne valide qu’une poignée ouverte en écriture ; l’`OSError` était rattrapée et présentée comme « Écriture atomique du bundle impossible », ce qui masquait la cause. Ouverture passée en `"rb+"`.

**2. Séparateur natif écrit dans un format déclaré portable — quatre échecs et une transition en cascade.** `_relative()` refuse explicitement toute barre inverse dans `copy_progress.path`. L’écrivain, lui, produisait `str(relative)`, donc `nested\file.txt` sous Windows : le module refusait son propre journal. Six sites convertis en `as_posix()` — écriture de la progression, clés d’inventaire attendu, progression workspace, fichiers cibles constatés, artefacts SQLite et comparaison du Profile. Un test vérifie désormais que chaque chemin journalisé repasse son propre validateur.

**3. Connexions SQLite laissées ouvertes par les fixtures — cinq `WinError 32` et, très probablement, les trois échecs Linux.** `with sqlite3.connect(...) as connection:` valide la transaction et **ne ferme pas** la connexion : le contrat du context manager porte sur la transaction, pas sur la poignée. Sous Windows, un fichier ouvert ne peut être ni déplacé ni supprimé. Sous Linux il se déplace, mais un `PRAGMA wal_checkpoint(TRUNCATE)` reste `busy` tant qu’un lecteur subsiste. Six fixtures passées par `closing()`.

**Ce qui reste non prouvé, et doit être dit comme tel.** La cause 3 est cohérente avec les deux plateformes mais n’a pas été reproduite localement : la suite complète passe ici en 3.11 comme en 3.12. Plutôt que de conclure par ressemblance, le refus de checkpoint énonce maintenant ce qu’il a observé — `busy`, `log`, `checkpointed`. Un refus qui ne dit pas ce qu’il a vu n’est pas diagnosticable depuis un journal de CI, et c’est exactement ce que I014 reproche à une incertitude silencieuse. Le prochain run tranchera par mesure.

## LOG-0287 — Le checkpoint WAL repliait sur rien
**Statut : Windows x64 vert pour la première fois. Correctif Linux écrit, verdict au prochain run.**

**Correction de LOG-0286.** J’y écrivais que les connexions SQLite laissées ouvertes par les fixtures expliquaient « très probablement » les trois échecs Linux. C’était faux. Je l’avais dit comme une probabilité et instrumenté le refus plutôt que de conclure ; la mesure a tranché contre l’hypothèse.

**Ce que le run #46 a mesuré.** Windows x64 passe intégralement — suite, sidecar, archive CLI, NSIS et MSI sur un vrai runner : les trois causes de LOG-0286 étaient les bonnes de ce côté. Linux tombait encore sur les mêmes trois tests, mais le refus portait ses chiffres : `busy=0, log=-1, checkpointed=-1`.

**Ce que ces chiffres disent.** Ce n’est pas un verrou. `(0, -1, -1)` est la réponse de SQLite lorsque le pager ne détient aucun objet WAL : déclarer `PRAGMA journal_mode=WAL` ne l’ouvre pas, il faut que la connexion lise la base. Le checkpoint retournait donc `SQLITE_OK` **sans rien replier**, et un appelant qui n’examine que `busy` ne pouvait pas distinguer ce succès sur rien d’un repli réel. Que le pager ouvre le WAL de lui-même dépend du build SQLite, ce qui explique que la machine de développement n’ait jamais vu le défaut.

**La portée dépassait le test qui échouait, et c’est le vrai enseignement.** Trois sites checkpointaient. `profile_migration` avant de copier la base — le test rouge. `bundles` avant un export, en n’examinant que `busy` : un bundle pouvait donc être pris par-dessus un WAL jamais replié, contre I010. `memory_sync` sur une connexion neuve, avant toute lecture : il pouvait committer dans Git une mémoire incomplète. Les deux derniers ne faisaient échouer aucun test ; ils rendaient un verdict faux en silence, ce qui est pire qu’un rouge.

**Correctif.** Un `checkpoint_wal()` unique dans `store.py` ouvre le WAL par une lecture avant de replier, et rend `(busy, log, checkpointed)`. Les trois appelants refusent désormais tout ce qui n’est pas `busy == 0` **et** `log == 0`, chacun avec son propre message.

**Ce qui reste non prouvé.** Le test de régression ajouté vérifie sur disque qu’un WAL réellement peuplé est replié et que les données restent lisibles. Il passe ici avec comme sans la lecture : il n’a de mordant que là où le pager n’ouvre pas son WAL seul. Seul un run vert sur le runner Linux tranchera. Suite locale : `750 passed, 55 subtests passed`.

## LOG-0288 — Premier run vert de la matrice native
**Statut : PASS mesuré sur les deux runners.**

Run `desktop-packaging.yml` #47 sur `ec1fd93`, le 2026-09-15 : **Linux x64 et Windows x64 sont verts**, quatorze étapes chacun — suite de conformité, sidecar natif, archive CLI autonome, AppImage et paquet Debian côté Linux, NSIS et MSI côté Windows. C’est le premier passage vert de ce workflow ; les quarante-six runs précédents avaient tous échoué, y compris sur `main`.

Quatre causes racines l’expliquaient, détaillées en LOG-0286 et LOG-0287 : `os.fsync` sur une poignée ouverte en lecture seule, le séparateur natif écrit dans un format dont le validateur refuse la barre inverse, les connexions SQLite laissées ouvertes par les fixtures, et un checkpoint WAL qui repliait sur rien faute d’avoir ouvert le WAL.

**Ce que ce run change dans ce que le produit a le droit de dire.** Le README portait la restriction « ce décompte est relevé sur Linux x64 ; le dernier passage Windows x64 attesté correspond à la campagne M8/M9 et porte sur une suite antérieure ». Elle est retirée : la suite, `750 passed, 55 subtests passed`, est désormais attestée sur les deux plateformes à la même date et sur le même commit. `REMAINING_WORK.md` passe A1 en clos, et `todo.md` coche la ligne correspondante.

**Ce que ce run ne prouve pas.** Il atteste que les binaires se construisent et que la suite passe, pas qu’une installation utilisateur réelle a été observée. Le parcours desktop interactif — sélection humaine d’un dossier, dialogue WebView ↔ Rust ↔ sidecar — reste non observé, et les preuves hôtes par fournisseur restent à faire. Ces deux points restent ouverts au chapitre D.

## LOG-0289 — Zero Pollution : la moitié de la promesse ne tenait pas
**Statut : PASS mesuré sur Linux x64. Les six tests ajoutés restent à attester sur Windows.**

§36 promet trois choses : aucune modification du code métier, une empreinte limitée au répertoire VERA et à la configuration hôte, et des fichiers SQLite volatils qui **restent ignorés** pendant que la mémoire canonique et le profil demeurent versionnables. Le comportement était réputé correct et n’était gardé par aucun test. La mesure sur un projet témoin a séparé le vrai du supposé.

**Ce qui tenait.** Une installation complète — `init-project`, déclaration des capabilities, `generate`, `adapter stage`, `install` — ne crée rien hors `.vera-mmu/` sauf `.mcp.json`, la configuration hôte déclarée, et ne touche aucun fichier métier préexistant.

**Ce qui ne tenait pas.** `automatic_memory_sync` stageait `.vera-mmu/` en bloc. `memory.sqlite-wal` et `memory.sqlite-shm` étaient donc **commités dans le dépôt de l’utilisateur**, exactement ce que §36 interdit. Aucun `.gitignore` n’existait nulle part.

**Corrigé en deux endroits, parce qu’un seul n’aurait pas suffi.** L’initialisation écrit désormais `.vera-mmu/.gitignore` : les règles vivent là où Git les voit, donc elles couvrent aussi un `git add -A` fait à la main par l’utilisateur, pas seulement la synchronisation automatique. Et `memory_sync` exclut les sidecars de son pathspec sur le `status`, le `add` **et** le `commit` — cette dernière exclusion n’est pas redondante : `commit --only` prend son contenu dans l’arbre de travail, donc un pathspec qui les nommait encore les aurait versionnés même laissés hors index. `.gitignore` rejoint les fichiers réparables de §54.

**Le cas que les règles ne peuvent pas régler, et le refus de le masquer.** Une règle ajoutée après coup ne désuit pas un fichier : une installation antérieure garde ses sidecars versionnés, avec des règles d’apparence parfaite. Une ligne de Doctor qui n’aurait vérifié que les règles aurait donc répondu `PASS` sur un projet en violation — le même défaut que LOG-0287 vient de corriger ailleurs. La ligne `zero_pollution` **interroge donc Git** plutôt que de déduire : elle nomme les fichiers volatils suivis et donne le `git rm --cached` correspondant, et quand elle ne peut pas interroger Git elle répond `INFO`, jamais un `PASS` qu’elle n’a pas vérifié.

**Volontairement hors de ce lot.** Retirer ces fichiers de l’index est une écriture dans l’historique de l’utilisateur. Elle relève du cycle preview → confirmation, donc de `repair`, et non d’une correction silencieuse. Le Doctor le signale ; personne ne le fait à sa place.

**Preuve.** `tests/test_zero_pollution.py` — six tests mesurés sur un projet témoin sous Git : empreinte, code métier intact, sidecars non versionnés y compris après un `git add -A` de l’utilisateur, mémoire et profil restés versionnables, installation ancienne signalée, et absence de `PASS` non vérifié. Le troisième échouait avant le correctif et passe après. Suite complète : `756 passed, 55 subtests passed`.

## LOG-0290 — Le scanner observe enfin les quatorze catégories de §30
**Statut : PASS mesuré sur Linux x64.**

**Correction préalable d’un chiffre que j’avais écrit.** `REMAINING_WORK.md` annonçait « au minimum quinze catégories ». §30 en énumère **quatorze** : gestionnaire de version, langages, frameworks, gestionnaires de dépendances, scripts de build, suites de tests, linters, CI, Docker, documentation, datasets, assets, sous-projets, fichiers de configuration. Le décompte a été refait sur le texte de la spécification, pas sur le registre.

**Écart réel : six sur quatorze.** Le scanner observait VCS, CI, documentation, conteneur et chemins de test, plus les langages — mais déduits d’un manifeste de dépendances, donc confondus avec la catégorie que §30 énumère séparément. Frameworks, scripts de build, linters, datasets, assets, sous-projets et fichiers de configuration n’avaient aucune catégorie.

**Le scanner a son module.** `project_scan.py` porte des tables déclaratives — marqueurs de répertoire, noms exacts, motifs de noms, extensions de source, extensions non-source, manifestes imbriqués. Une catégorie manquante se voit en lisant une table ; c’était précisément ce que l’ancienne forme, une suite de conditions dans `project_operations.py`, rendait invisible.

**Deux distinctions que la spécification impose et que le code porte maintenant.** Un manifeste n’est pas un langage : `package.json` seul déclare un gestionnaire de dépendances et **aucun** langage, car c’est l’extension d’un fichier source qui nomme le langage. Et un manifeste imbriqué désigne un sous-projet, celui de la racine non.

**Le rapport passe en `vera-scan-report/v2`.** `kind` porte la catégorie, `marker` ce qui a été reconnu, `occurrences` combien de fois. Une ligne par marqueur et non par fichier : quarante modules Python font une seule observation sur Python, portant son compte. Le format est bumpé plutôt que réinterprété en silence — `kind` passait de `"python"` à `"language"`, ce qui est un changement de sens, pas un ajout.

**Ce que le scanner reste.** Aucune lecture de contenu — un test réécrit les fichiers et exige un rapport identique —, aucun symlink suivi, aucun processus, aucun réseau, et uniquement des `OBSERVED`. La spécification écrit `DETECTED` ; VERA dit `OBSERVED` depuis l’origine et le vocabulaire est conservé : ce que §30 interdit est de présenter une observation comme `PROVEN`, et c’est respecté.

**Preuve.** `tests/test_project_scan.py` : une fixture par catégorie, douze tests, quatorze sous-tests. Le test de couverture a été vérifié par soustraction — en retirant les marqueurs de framework, il échoue. Passé sur ce dépôt : vingt-sept observations, dix catégories, les quatre absentes (scripts de build, conteneur, datasets, linters) l’étant réellement. Suite complète : `768 passed, 69 subtests passed`.

## LOG-0291 — La recommandation de profil argumente, elle ne décide pas
**Statut : PASS mesuré sur Linux x64.**

§31 était absent. `project_recommendation.py` lit un `ScanReport/v2` et propose un template, un jeu de capabilities et les gates que ces capabilities pourraient satisfaire. Exposé en CLI (`recommend`) et par le bridge (`project.recommend`).

**Le contrat de la section tient en une phrase : «l’utilisateur peut modifier chaque élément».** Le payload est donc `PROPOSED`, `mutation: NONE`, chaque élément porte `editable: true`, et chaque proposition cite les observations qui la soutiennent. Une recommandation qui ne peut pas dire pourquoi elle propose quelque chose est une opinion, et VERA n’a pas le droit d’en présenter une comme une mesure.

**Trois refus, plus intéressants que les propositions.**

*Aucune commande, aucun chemin, aucune URL, aucun runner.* Nommer une capability `lint` n’est pas dire ce que `lint` exécute : la première est une observation sur la forme du projet, la seconde une décision que seul son propriétaire prend. I008 interdit à ce côté de la frontière de la prendre ; le binding d’un runner reste au capability builder, sous preview et confirmation. Un test parcourt récursivement tout le payload et échoue sur la moindre clé `command`, `argv`, `shell`, `interpreter`, `cwd`, `executable`, `runner`, `path` ou `url`.

*Rien n’est déduit que le scan n’ait observé.* C’est le point qui méritait d’être tranché plutôt que contourné : l’exemple de §31 propose une capability `build` pour un arbre — TypeScript, React, Node, Vitest, Playwright, GitHub Actions — dont l’étape de build vit dans les `scripts` d’un `package.json`. Or ouvrir ce manifeste est exactement ce que §30 interdit au scanner. Proposer `build` malgré tout aurait été inventer une observation pour faire ressembler la sortie à l’exemple. `build` n’est donc proposé que si un marqueur de build a réellement été vu, et l’écart avec l’exemple est **inscrit dans `notes`** du rapport lui-même.

*Le template `research` n’est jamais recommandé automatiquement.* Aucun nom de fichier ne distingue un projet de recherche d’un autre. Il reste disponible au choix, et le rapport porte cette limite au lieu de la taire.

**Un aveu porté par le format.** Un template retenu faute de mieux se présente comme un défaut — « template `software` retenu par défaut : aucun marqueur observé ne permet de déduire un domaine » — et non comme une déduction. Un test l’exige littéralement : c’est la différence entre un fallback et une fabrication.

**Trois marqueurs ajoutés au scanner** pour que les domaines soient inférables sans lire : `platformio.ini`, `project.godot`, `tsconfig.json`, plus les extensions `.ino`, `.ipynb` et `.kicad_pcb`. Ajout purement additif aux tables de LOG-0290.

**Preuve.** `tests/test_project_recommendation.py`, quatorze tests : l’exemple de §31 rejoué tel qu’il est écrit, déterminisme, absence d’écriture vérifiée sur l’arborescence, absence de clé de commande, un gate jamais proposé sans sa capability, quatre templates, arbre vide ne proposant rien, et le lien au `report_hash` du scan lu — une proposition qui ne pourrait pas nommer son entrée pourrait être affichée à côté d’un autre projet. Passé sur ce dépôt : template `software` sur cinq langages et quatre gestionnaires de dépendances, capabilities `install`, `build`, `test`, `typecheck`, quatre gates. Suite complète : `782 passed, 69 subtests passed`.

## LOG-0292 — Le parcours en dix-huit étapes se dérive du projet
**Statut : dérivation PASS sur Linux x64. Lot déclaré PARTIEL, pas fait.**

`wizard.py` déclare les dix-huit étapes de §29.2 dans l’ordre, chacune avec son critère d’entrée et l’évidence qui la termine, et dérive leur état **du projet lui-même** — Project Profile, catalogues, `generated/`, configuration hôte. Aucun drapeau n’est conservé : fermer l’application et la rouvrir retrouve la même étape, et demander où l’on en est n’écrit rien. Exposé en CLI (`wizard`), par le bridge (`wizard.state`), par une commande Rust, et par un panneau de console qui affiche un état qu’il ne calcule pas.

**Un quatrième état, contre ce que j’avais moi-même annoncé.** `REMAINING_WORK.md` prévoyait `BLOCKED`, `AVAILABLE`, `COMPLETED`. Six étapes — scanner, détecter, proposer, prévisualiser le MCP, valider, lancer le Doctor — ne laissent aucune trace sur le disque. Les déclarer `COMPLETED` aurait inventé la seule chose qu’on ne peut pas voir ; les laisser `AVAILABLE` à jamais aurait été tout aussi faux. Elles sont `NOT_OBSERVABLE`. Le modèle a été corrigé parce que la réalité l’exigeait, et la correction est écrite, pas glissée.

**Un compteur qui mentait sur sa cause.** La règle des policies comptait une clé `policies:` que le format n’a jamais portée — le catalogue déclare chaque policy en section de premier niveau, à côté du marqueur de format. Elle aurait rapporté tout projet sain comme « illisible », c’est-à-dire un faux négatif habillé en diagnostic. Corrigé par un compteur dédié.

**Pourquoi ce lot ne se déclare pas fait.** La règle de mise à jour de `REMAINING_WORK.md` dit qu’une tâche partiellement faite reste ouverte et ne devient jamais « faite en partie ». Deux choses manquent. D’abord, la console reste une page de panneaux indépendants : le parcours y est affiché, il n’y gouverne rien, alors que le périmètre annoncé était de transformer la page en parcours ordonné. Ensuite, le critère de sortie que j’avais écrit exigeait « la navigation exercée dans la suite TypeScript » — **cette suite n’existe pas** : `apps/desktop` n’a aucun lanceur de tests et son `build` se limite à `tsc --noEmit && vite build`. Ce qui est prouvé côté interface est donc le typage et la construction, pas un comportement. Installer un lanceur toucherait au verrou de dépendances que la CI consomme en `--frozen-lockfile`, et ce lot a refusé de risquer une matrice qui vient de passer au vert pour la première fois afin de satisfaire un critère écrit avant d’avoir regardé.

**Preuve du livré.** `tests/test_wizard.py`, seize tests : ordre des dix-huit étapes, répertoire vierge où seules l’observation et le choix du domaine sont ouverts, ce que l’initialisation termine réellement, intégrations restées ouvertes tant qu’aucune n’est activée, installation bloquée puis disponible puis terminée, absence d’écriture vérifiée sur l’arborescence, état **redérivé à l’identique** après suppression complète du runtime, déterminisme, catalogue cassé qui bloque son étape sans faire tomber le parcours, profil cassé, racine symlinkée refusée. `tsc --noEmit`, `vite build` et `cargo check` passent. Suite complète : `798 passed, 69 subtests passed`.

## LOG-0293 — Le parcours gouverne la console, et l’interface a enfin un lanceur de tests
**Statut : PASS. Core et interface mesurés ; verdict Windows au prochain run.**

LOG-0292 laissait B1 explicitement partiel pour deux raisons. Les deux sont levées ici.

**Le gouvernail.** Quatre panneaux — déclaration de capability, structure de gate, policy de gate, intégration MCP — se ferment maintenant quand l’étape qui les gouverne est `BLOCKED`, affichent **la raison rendue par le Core** et désactivent leurs boutons. La console n’est plus une page de panneaux indépendants : elle est gouvernée par un état qu’elle ne calcule pas.

**Le lanceur de tests.** `apps/desktop` n’en avait aucun — le constat de LOG-0292. `vitest` est installé, `pnpm test` ajouté, et `build` enchaîne `tsc --noEmit && vitest run && vite build`. Comme `beforeBuildCommand` vaut `pnpm build`, la CI exécutait déjà ces tests via `pnpm tauri build` ; une étape explicite a néanmoins été ajoutée au workflow pour échouer tôt plutôt qu’au moment du bundle. Le risque identifié en LOG-0292 — la CI consomme le verrou en `--frozen-lockfile` — a été levé par la mesure : `rm -rf node_modules && pnpm install --frozen-lockfile` passe avec le verrou mis à jour.

**Ce que l’interface a le droit de porter.** Une seule chose, dans `journey.ts` : lire le payload du parcours et dire quel panneau une étape ouvre. Le reste est dérivé côté Core et seulement affiché. C’est la troisième des règles fixées pour tout le Dashboard : réimplémenter une validation en TypeScript laisserait les deux versions diverger, et c’est l’interface qui finirait par mentir.

**Deux refus épinglés côté interface.** Un état inconnu dans le payload est lu `BLOCKED`, jamais comme une progression. Et un parcours **non encore lu ne ferme aucun panneau** : verrouiller sans avoir demandé serait agir sur une information absente, ce que ce produit refuse partout ailleurs.

**Le mordant a été vérifié, pas supposé.** En cassant la règle de blocage — un panneau bloqué rendu ouvert — le test tombe. En revanche, supprimer un garde sur le parcours vide ne faisait tomber aucun test : le cas suivant l’absorbait déjà, le comportement était identique. C’était une ligne morte, retirée. Un test comportemental n’a pas à sanctionner du code redondant, et c’est le contrôle de mordant qui l’a montré plutôt qu’une lecture.

**Une règle d’ignorance trop étroite, révélée par le lot.** `vitest` crée un `node_modules` sous `apps/desktop/ui/`, et `.gitignore` ne couvrait que `apps/desktop/node_modules/`. La règle vaut désormais à toute profondeur. C’est la même classe de défaut que §36 : une promesse tenue par un chemin écrit à la main plutôt que par une règle.

**Preuve.** `apps/desktop/ui/src/journey.test.ts` : dix tests. Avec `tests/test_wizard.py` et ses seize tests côté Core, le parcours est désormais mesuré des deux côtés de la frontière. `tsc --noEmit`, `vitest run`, `vite build` et `cargo check` passent.

## LOG-0294 — Run #48 : le verrou modifié et les tests d’interface passent sur les deux runners
**Statut : PASS mesuré.**

Run `desktop-packaging.yml` #48 sur `14706d9` : **Linux x64 et Windows x64 verts**, quinze étapes chacun. L’étape ajoutée « Run desktop interface tests » a tourné sur les deux.

**Ce que ce run lève.** LOG-0293 avait vérifié en local que `pnpm install --frozen-lockfile` acceptait le verrou mis à jour ; c’était une mesure sur une seule machine. Elle est maintenant faite sur les runners, Windows compris, là où le risque était réel. Et la réserve traînée depuis LOG-0289 — « les tests ajoutés depuis le run #47 ne sont attestés que sur Linux » — tombe : `798 passed, 69 subtests` côté Core et `10 passed` côté interface sont attestés sur les deux plateformes, au même commit. Le README et `REMAINING_WORK.md` sont mis à jour en conséquence.

## LOG-0295 — La taxonomie devient éditable, et un retrait destructeur devient impossible
**Statut : PASS mesuré sur Linux x64. Les quatorze ajouts restent à attester sur Windows.**

Le Core déclarait les types de connaissance, d’entité et de relation, et les synchronisait dans le store ; **rien ne pouvait lui demander de les changer**. `profile_taxonomy.py` ferme cela, sous le cycle habituel — preview, vérification de fraîcheur, confirmation explicite, écriture atomique ou refus. Exposé en CLI (`taxonomy`) et par le bridge (`taxonomy.preview` / `taxonomy.apply`).

**Le refus qui porte le lot, et pourquoi il vit dans le Core.** Retirer un type qui porte déjà de la connaissance, des entités ou des relations rendrait orphelin ce que le projet a enregistré. Le compte est fait **contre la mémoire elle-même** — `COUNT(*)` sur `knowledge`, `entity` et `relation`, connexion en lecture seule — et le refus est rendu ici, pas grisé dans un écran. C’est la troisième des règles fixées pour tout le Dashboard : une règle tenue seulement par l’interface cesse d’exister dès que quoi que ce soit d’autre écrit — la CLI, le MCP, un autre agent.

**Le compteur ne peut pas être faussement toujours nul.** Deux tests l’encadrent : retirer un type utilisé est refusé avec le nombre d’enregistrements qui seraient orphelins, retirer un type inutilisé passe. Si le compte était systématiquement zéro, le premier tomberait ; s’il était systématiquement non nul, le second tomberait.

**Le piège des identifiants, tranché comme annoncé avant le lot.** Le déclaratif est en majuscules, le stockage en minuscules à tirets. L’écran n’édite que le déclaratif, la conversion reste dans le Core, et un identifiant minuscule est refusé à la saisie plutôt que converti en silence — convertir aurait accepté une saisie ambiguë en faisant semblant de la comprendre.

**Deux autres refus.** Une section `knowledge` vide : un projet sans type de connaissance ne peut rien mémoriser, et l’accepter aurait produit un projet muet d’apparence valide. Et un preview périmé : l’application rejoue exactement la même édition et exige que le Profile n’ait pas bougé depuis sa relecture.

**Une réparation du registre, à dire plutôt qu’à taire.** En réécrivant la section B au fil des lots précédents, j’avais fait disparaître de `REMAINING_WORK.md` les entrées B5 à B11 — Work Graph, Capability Builder §32, Gate Builder §33, policies, Resume et intégrations, MCP Preview §34, raccordement final. Elles sont rétablies avec leurs périmètres et critères de sortie. Un plan dont les lots restants s’effacent silencieusement au fil des réécritures est exactement le registre auquel ce document refuse de ressembler.

**Preuve.** `tests/test_profile_taxonomy.py`, quatorze tests. Suite complète : `812 passed, 69 subtests passed`.

## LOG-0296 — Le Work Graph se configure, mais ne s’invente pas
**Statut : PASS mesuré sur Linux x64. Les quatorze ajouts restent à attester sur Windows.**

**Un périmètre corrigé par la mesure, pas par confort.** `REMAINING_WORK.md` annonçait pour cette étape « déclarer les états de work item, les transitions autorisées et les dépendances ». La lecture du code a montré que ce n’était pas tenable : le cycle de vie est **fermé dans le Core** — quatre états, trois événements, transitions fixes dans `work_lifecycle.py`. Laisser un projet déclarer une machine à états que le Core n’applique pas produirait un graphe qui ment : l’écran offrirait une transition que le moteur refuse, et c’est exactement la classe de mensonge que ce produit existe pour empêcher. Le graphe est donc **rapporté**, depuis les constantes mêmes que le Core applique, et ce qu’un projet configure est la **sévérité de la barrière** sur une transition.

**Un test épingle cette équivalence** plutôt que de la supposer : une transition déclarée par le rapport est acceptée par le moteur, une transition absente du rapport est refusée par le Core — pas seulement absente d’un écran.

**Deux services sans appelant, encore.** `WorkStartPolicyService.declare` et `WorkCompletionPolicyService.declare` existaient, testés, et rien ne pouvait les atteindre : ni la CLI, ni le bridge, ni `write_api`. C’est le même défaut que le diagnostic d’ouverture avait nommé — des serrures excellentes sans porte. Ils en ont une maintenant : CLI `work-graph-config`, bridge `work.graph.read` / `work.graph.preview` / `work.graph.apply`.

**Une irréversibilité dite à voix haute.** Une policy de transition se déclare **une seule fois** : sa table tient une ligne unique et refuse `UPDATE` comme `DELETE` par trigger. C’est une garantie voulue — un projet ne peut pas assouplir sa propre règle après coup pour faire passer un élément gênant. Le preview l’énonce en toutes lettres, parce qu’un assistant qui laisserait cliquer là-dessus dans un formulaire ordinaire cacherait une décision définitive derrière une apparence banale.

**Une policy absente est rapportée `NOT_DECLARED`, jamais comme un défaut.** Le moteur traite l’absence comme non contrainte, mais écrire « OPEN » là où le store ne tient rien rapporterait une décision que personne n’a prise.

**Un test qui serait passé par accident.** J’avais écrit « `REQUIRE_READY` bloque le démarrage ». C’est faux tel quel : un élément sans prérequis **est** prêt et démarrerait, policy déclarée ou non — le test aurait été vert sans rien prouver. Il exige maintenant une dépendance non satisfaite, et son pendant vérifie qu’un élément sans prérequis démarre quand même. La policy est prouvée dans les deux sens.

**Une collision rattrapée par la suite complète.** La commande s’appelait d’abord `work-graph`, nom déjà porté par la lecture des items : 55 tests sont tombés d’un coup, dont toute la suite Zero Pollution. Renommée `work-graph-config`. C’est précisément pourquoi la suite complète tourne avant chaque push, et pas seulement les fichiers touchés.

**Preuve.** `tests/test_work_graph_config.py`, quatorze tests. Suite complète : `826 passed, 69 subtests passed`.

## LOG-0297 — Le contrat de capability en entier, ou rien
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Le défaut trouvé était plus grave que celui annoncé.** `REMAINING_WORK.md` décrivait B6 comme
« le builder ne saisit que cinq champs ». La lecture a montré pire : ces cinq champs partaient
**directement dans SQLite**, et une capability écrite ainsi ne porte **ni contrat ni policy**.
Aucun runner ne peut l’exécuter — `capability_contract` est absente et chaque runner exige la
sienne. Aucune décision ne la couvre — `capability_policy` est absente et chaque runner exige un
`ALLOW` explicite. Et aucun hash déclaratif ne la voit, parce que `capability_catalog_hash` porte
sur `capabilities.yaml`, que cette voie ne touchait jamais. L’écran annonçait « DECLARED » ; le
moteur tenait un objet inerte. C’est la même classe que les serrures sans porte du diagnostic
d’ouverture, retournée : une porte qui ne donne sur rien.

**Le contrat est désormais écrit là où il existe réellement.** `.vera-mmu/capabilities.yaml` est la
seule source qui porte le contrat entier de §32 — runner, policy projet, timeout, entrées, sorties,
artefacts, validator, admissibilité de preuve, confirmation. Le Core la valide (`load_project_catalogs`),
la hache (`capability_catalog_hash`) et la matérialise (`sync-capabilities`) en une capability, un
contrat et une décision de policy. Écrire ailleurs aurait créé une seconde vérité partielle. La
chaîne complète a été mesurée : `capability-contract --apply` puis `sync-capabilities` puis
`validate`, sur un projet neuf.

**La tension §32 / I008, tranchée par le code et pas par un arbitrage de confort.** §32 affiche une
ligne « Commande / API » ; I008 interdit qu’un client fournisse une commande. Le Core ne *borne*
pas une commande : **il n’a aucun champ de commande.** `capability_contract` tient un *profil* de
runner choisi parmi quatre, et aucun des quatre ne lance un processus depuis une chaîne fournie par
le projet — `OBSERVED_PROCESS` enregistre qu’un processus a eu lieu ailleurs, il n’en démarre pas.
La ligne est donc rapportée `NOT_APPLICABLE` avec son motif. Afficher un champ « Commande » vide
aurait invité quelqu’un à le remplir, et le refus serait arrivé après la frappe plutôt qu’avant.

**Le schéma de paramètres est dérivé, jamais saisi.** L’interface nomme des entrées ; le Core en
compose le schéma — chaînes requises, `additionalProperties: false` — et impose `validator_id` /
`evidence_id` aux deux runners de validation. Une classe entière d’erreur disparaît ainsi, et la
deuxième règle du Dashboard est tenue à la lettre : l’interface compose des déclarations à partir
de ce que le Core expose, elle n’en invente aucune. `capability.options` publie ces catalogues
fermés, y compris le fait que `NETWORK` n’est pas déclarable et que la policy réseau ne se choisit
pas.

**Les sept refus de §32, chacun avec un code stable, et chacun prouvé deux fois.** Une fois par le
builder — ce qu’un écran appelle — et une fois **contre le fichier déclaratif lui-même**, pour
qu’écrire `capabilities.yaml` à la main ne change rien. Une règle tenue seulement par le builder
cesserait d’exister dès que la CLI, le MCP ou un éditeur de texte écrit.

1. `COMMAND_NOT_BOUNDED` — une clé hors du contrat fermé (`command`, `api`, `argv`…), ou un runner
   hors des quatre profils.
2. `PATH_OUTSIDE_ROOTS` — un artefact absolu, en `..`, avec lettre de lecteur ou barre inverse. Le
   contrôle est lexical à dessein : un artefact est déclaré avant que quoi que ce soit ne le
   produise, il n’y a rien à résoudre sur le disque, et une déclaration qui pourrait sortir des
   racines doit être refusée quand elle est écrite, pas quand elle est suivie.
3. `NETWORK_WITHOUT_POLICY` — `policy: NETWORK` refusée : la seule policy réseau déclarable est
   `DENY_NETWORK`, donc rien ne bornerait une capability réseau.
4. `MISSING_TIMEOUT` — absent, non entier ou hors de 1 à 3600 secondes, sans valeur par défaut.
5. `OUTPUT_NOT_INTERPRETABLE` — destinée à une gate sans déclarer `verdict` en sortie. Le Core
   refuse aussi, dans `gates.yaml`, une gate adossée à une capability sans sortie lisible : elle
   rendrait une opinion là où elle prétend rapporter une observation.
6. `DEPENDENCY_MISSING` — deux dépendances qui n’existeraient jamais : un runner de validation dont
   le validator déclaré n’est pas du même type — l’exécution est refusée par
   `ensure_runner_validator_compatibility` — et un validator `EVIDENCE_FIELDS` sans aucune entrée,
   dont l’enregistrement est refusé faute de clé requise.
7. `PLACEHOLDER_VALIDATOR` — un validator hors catalogue, `TODO` ou `manual` en tête ; et
   `yields_proof: true`, qui est la même absence habillée : aucun runner du Core ne produit de
   preuve, tous refusent un contrat qui le prétend, et une preuve naît d’une evidence PASS validée
   puis admise (I004, I006).

**Un test qui attestait exactement l’inverse.** `test_project_bootstrap` déclarait une capability
`yields_proof: True` avec `outputs: []`, y adossait une gate, et vérifiait que le catalogue
**chargeait**. Or tous les runners refusent `yields_proof`, et la gate lisait un `verdict` qu’aucune
sortie ne rendait. Ce test épinglait comme valide une déclaration que le moteur ne peut ni exécuter
ni évaluer — précisément le genre de vert qui masque un défaut. Corrigé.

**Les refus sont rendus ensemble, pas un par un.** Un preview invalide rapporte tous ses codes en
une fois et vaut `REFUSED` ; `apply` refuse un preview `REFUSED` et n’écrit rien. Un écran qui
tomberait sur le premier refus ferait découvrir les six autres par essais successifs.

**Six de mes propres preuves passaient pour la mauvaise raison, et c’est le contrôle de mordant qui
l’a montré.** J’ai neutralisé chaque règle ajoutée une par une et rejoué les tests. Six refus
côté catalogue restaient verts sans leur règle : le helper qui écrit la déclaration à la main
remplaçait tout le catalogue par une seule capability, si bien que les gates du template ne
référençaient plus rien et que le chargeur s’arrêtait sur une gate orpheline **avant d’atteindre la
règle examinée**. Les assertions passaient ; elles ne prouvaient rien. Le helper vide désormais le
catalogue de gates pour la durée du contrôle, et la mesure a été refaite : les sept règles du Core
et les cinq garanties du builder — clé inconnue, timeout, sortie de gate, fraîcheur du preview,
confirmation — font toutes tomber un test quand on les retire. Lire le code n’aurait pas trouvé
cela : les deux versions du helper se ressemblent, et seule l’exécution distingue une preuve d’une
coïncidence.

**Côté interface.** `contract.ts` porte la seule logique que la console a le droit d’avoir : couper
une saisie en liste, lire les catalogues fermés que le Core publie, lire les refus qu’il a nommés.
Deux directions opposées y sont assumées et testées : un parcours non encore lu ne **ferme** aucun
panneau — verrouiller sans avoir demandé cacherait un écran —, mais un contrat non encore relu ne
se **confirme** pas — confirmer sans avoir demandé écrirait dans le projet. L’absence d’information
va vers le refus quand le refus est ce qui ne fait rien.

**Une affirmation du README corrigée au passage.** Il annonçait « 826 tests … passe intégralement
sur Linux x64 et Windows x64, mesuré … run #48 ». Le run #48 portait sur `14706d9` et comptait
`798 + 10` ; les vingt-huit ajouts de B4 et B5 n’ont jamais tourné sur Windows, ce que
`REMAINING_WORK.md` disait déjà et que le README contredisait. Il énonce désormais les deux
chiffres séparément : le décompte courant, et celui réellement attesté sur les deux plateformes.
Une phrase du même paragraphe répétait aussi sa propre seconde moitié ; elle est nettoyée.

**Preuve.** `tests/test_capability_builder.py`, dix-neuf tests ; `apps/desktop/ui/src/contract.test.ts`,
treize tests. Suite complète : `844 passed, 69 subtests passed` côté Core et `23 passed` côté
interface. `tsc --noEmit`, `vitest run`, `vite build` et `cargo check` passent — ce dernier après
avoir construit le sidecar PyInstaller, que le script de build Tauri exige.

## LOG-0298 — Une opinion cesse de pouvoir se ranger comme preuve
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Le trou, mesuré avant d’être bouché.** Rien dans la chaîne de promotion ne regardait ce qu’une
evidence *était*. `ProofService.promote` exigeait une evidence `PASS`, une admission `ADMITTED`,
une policy de preuve, un hash cohérent — et jamais son type. Donc une `HUMAN_ASSERTION` enregistrée
`PASS` puis admise promouvait une connaissance en `PROVEN` exactement comme un `TEST_PROOF`. C’est
une opinion rangée comme preuve : précisément ce que I004 et I006 existent pour empêcher, et ce
que §33 demande au Dashboard de rendre visible.

**Les trois classes vivent dans le modèle de données, pas dans une couleur.** C’est la formulation
du registre, et elle est prise au mot : une distinction qu’une interface dessine cesse d’exister
dès que la CLI, le serveur MCP ou un autre agent écrit. `evidence_classes.py` classe donc les dix
types fermés de `evidence.TYPES` selon ce que le Core peut dire de leur verdict :

- **validation technique** — le verdict découle d’un contrôle rejouable, qu’une réexécution peut
  contredire : `COMMAND_PROOF`, `TEST_PROOF`, `CI_PROOF`, `API_PROOF`, `HASH_PROOF`, `FILE_PROOF` ;
- **simple observation** — quelque chose a été enregistré tel que vu ; le nombre peut être exact
  sans rien décider, le Core n’en a dérivé aucun verdict : `METRIC_PROOF`, `EXTERNAL_ATTESTATION` ;
- **appréciation sémantique** — un jugement, humain ou de modèle, qu’aucune réexécution ne
  reproduit : `HUMAN_ASSERTION`, `MODEL_EVALUATION`.

**La classe est dérivée, pas stockée à côté.** Le type est déjà persisté, déjà fermé, déjà
immuable. Une seconde colonne portant la classe pourrait le contredire — et celle des deux qu’on
lirait déciderait si une opinion compte comme preuve. Dériver ne laisse rien diverger. Un test
exige que **tout** type admis par le Core porte exactement une classe : en ajouter un sans le
classer fait tomber la suite, au lieu de lui donner silencieusement un défaut.

**Les dents sont au bon endroit.** `promote` refuse toute evidence qui n’est pas une validation
technique, en nommant sa classe et la raison. Le critère de sortie du lot est épinglé tel quel :
une gate satisfaite par une appréciation admise `PASS` est bien `PASS` — le Core ne l’empêche pas —
et la promotion derrière elle est refusée. Le pendant est épinglé aussi, une validation technique
promeut toujours ; sans lui, le refus pourrait être un blocage général ne prouvant rien.

**Deux classes refusées, deux raisons différentes, et ce n’est pas cosmétique.** Ni une observation
ni une appréciation ne peut fonder une preuve, mais ce qu’il faut faire diffère : une observation
est un fait que le Core n’a jamais re-dérivé — ajouter un contrôle ; une appréciation n’est pas un
contrôle du tout — la remplacer. Les confondre dirait « impossible de promouvoir » sans dire
laquelle des deux.

**Une gate d’appréciations n’est pas refusée.** Une gate de relecture humaine est une chose
légitime à déclarer ; elle ne peut simplement jamais fonder une promotion. Le builder et le rapport
l’annoncent avant la déclaration plutôt que de le faire découvrir au moment de promouvoir. Refuser
la gate aurait interdit un usage réel pour appliquer une règle qui porte ailleurs.

**L’écran §33, entièrement dérivé.** `gate_reports.py` rend la gate, sa capability, ses exigences
classées une par une, et les deux lignes « peut satisfaire la gate » / « peut créer une proof ».
La capability est lue par la chaîne evidence → execution → capability : la redéclarer aurait créé
une seconde chose à maintenir vraie. Une policy non déclarée est rapportée `NOT_DECLARED` et jamais
« ALL », bien que le moteur évalue ainsi une policy absente — écrire le défaut du moteur
rapporterait une décision que personne n’a prise.

**Mon propre test le plus faible, trouvé par le contrôle de mordant.** J’avais vérifié que les deux
raisons diffèrent et que chacune contient un mot-clé. Une mutation qui échangeait les explications
de deux classes en gardant les mots-clés passait au vert. La vérification est maintenant
structurelle : la raison rapportée pour chaque type doit être exactement celle que sa propre classe
porte, et les trois doivent être deux à deux distinctes. Les sept autres règles du lot — le refus à
la promotion, la classification, le type inconnu refusé, les deux lignes de promotion, la gate
absente — faisaient déjà tomber un test chacune, ainsi que les trois refus côté interface.

**Laissé ouvert, et nommé.** `policies.yaml` déclare `promotion.proven_requires: [admissible_pass]`
dans tous les projets, et **rien ne le lit** : une serrure sans porte de plus. Elle n’est pas
ouverte ici à dessein — laisser un projet déclarer la condition de promotion lui permettrait de
déclarer que les opinions prouvent, ce que ce lot ferme. Le raccordement appartient à B8, et doit
d’abord trancher ce que `proven_requires` a le droit d’assouplir.

**Preuve.** `tests/test_evidence_classes.py`, douze tests ; `apps/desktop/ui/src/gate.test.ts`,
sept tests. Suite complète : `856 passed, 69 subtests passed` côté Core et `30 passed` côté
interface. `tsc --noEmit`, `vitest run`, `vite build` et `cargo check` passent.

## LOG-0299 — Les policies cessent d’être un fichier que personne n’applique
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Le lot annoncé était « un éditeur ». La mesure a montré qu’un éditeur seul aurait été un écran
qui ment.** `policies.yaml` validait sa **forme** — sept sections, chacune un objet — et presque
aucune de ses **valeurs**. Un projet pouvait écrire `network: {default: allow}`,
`destructive: {default: allow}` ou `promotion: {proven_requires: []}` : le chargeur acceptait, le
Doctor rapportait « Catalogue de policies valide », et rien de tout cela ne voulait dire quoi que
ce soit. Pire qu’une règle non appliquée : un fichier qui énonce une permission que le moteur
n’accorde jamais. Éditer cela sans fermer les valeurs aurait rendu le mensonge plus confortable.

**Les valeurs sont donc fermées, dans le Core, sur le fichier lui-même.** `network.default` ne peut
valoir que `deny` — le Core ne tient aucun chemin réseau et `capability_contract` contraint sa
policy réseau à `DENY_NETWORK` en SQL, donc offrir `allow` laisserait déclarer une permission que
rien ne peut accorder. C’est exactement le rappel fail-closed que le registre exigeait pour ce lot,
et il est tenu par le chargeur plutôt que par un menu grisé. `destructive.default` ne peut pas
valoir `allow` : une opération destructive qui s’annonce comme silencieusement permise est la seule
forme que toutes les écritures d’ici refusent.

**`proven_requires` : la question laissée ouverte par B7, tranchée.** Elle ne peut **pas** assouplir.
La liste enregistre ce que `ProofService.promote` vérifie — une evidence PASS admise **et** une
validation technique — et le Core refuse une liste qui en déclare moins, parce qu’elle décrirait un
moteur plus permissif que celui qui tourne : exactement la forme de mensonge que §33 vient de
fermer à la promotion. Elle refuse aussi une condition qu’il ne vérifie pas. Le champ cesse d’être
décoratif sans devenir un levier.

**`allowed_runners` était de la décoration pure.** Chaque projet l’expédiait **vide** pendant que
son catalogue de capabilities déclarait des runners, et rien ne comparait les deux fichiers. Le
template émet désormais exactement les runners que ses propres capabilities utilisent, et le
chargeur refuse une capability dont le runner n’y figure pas. Le builder §32 vérifie la même chose
**dans son preview**, pour refuser avant d’écrire plutôt que de laisser un fichier que le chargeur
rejettera ensuite.

**Une ligne enforced, une ligne déclarée : la différence est dite.** Chaque ligne porte `ENFORCED`
avec le module qui la lit, ou `DECLARED_ONLY` disant platement qu’aucun ne la lit — c’est le cas de
`filesystem.read` et de `destructive.default`. Rapporter `ENFORCED` partout aurait été le même
mensonge ailleurs ; omettre la distinction aurait laissé qui édite le fichier incapable de
distinguer une règle d’un vœu.

**Une duplication transformée en veto plutôt que laissée en double déclaration.** `policies.yaml`
déclarait `git.commit` / `git.push` et `sync-policy.json` décidait seul du comportement réel. Les
valeurs déclarées deviennent un **veto** : `deny` empêche le commit ou le push, et rien d’autre. Il
ne peut jamais élargir ce que `sync-policy.json` permet, donc la synchronisation automatique ne
gagne aucun droit. Et un catalogue illisible ne vétote rien qu’il n’a pas dit : transformer un
échec sans rapport en arrêt silencieux serait la même faute dans l’autre sens.

**Trois de mes preuves ne prouvaient rien, et le contrôle de mordant les a nommées.** Retirer la
règle « condition de promotion inconnue » ne faisait tomber aucun test : mon cas portait
`["admissible_pass", "vibes"]`, que la règle « liste incomplète » refusait déjà. Idem pour le
runner inconnu, refusé par le croisement avant d’atteindre sa propre règle. Et le veto de `push`
n’était couvert par rien. Les trois cas sont corrigés pour que la règle examinée soit la **seule**
cause du refus, et le veto de push a désormais son test sur un dépôt réel.

**Ce que ce dernier test a fait découvrir :** `MemoryStore.open` synchronise déjà la mémoire.
Mon premier scénario rapportait `NO_CHANGES` parce que l’ouverture du store avait committé
l’édition avant le sync explicite. Ce n’est pas un défaut, mais c’est un fait que le test doit
connaître pour prouver quoi que ce soit — il produit maintenant sa modification **après**
l’ouverture.

**Preuve.** `tests/test_policy_editor.py`, seize tests ; `apps/desktop/ui/src/policy.test.ts`,
six tests. CLI `policies`, bridge `policy.options` / `policy.preview` / `policy.apply`, commande
Rust et panneau de console. Suite complète : `873 passed, 69 subtests passed` côté Core et
`36 passed` côté interface. `tsc --noEmit`, `vitest run`, `vite build` et `cargo check` passent.

## LOG-0300 — Le contrat de reprise devient éditable, et deux briques sont trouvées sous l’éditeur
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Deux serrures sans porte, encore.** `integrations.enabled` gouverne l’étape 13 du parcours et
commande la génération MCP sur laquelle le projet se termine ; **rien** ne pouvait l’écrire — ni la
CLI, ni le bridge, ni `write_api` — donc un projet fraîchement initialisé restait indéfiniment sur
cette étape. Et l’étape 12 n’existait pas du tout : le contrat de reprise — quelles sections un
handoff doit porter, et le budget d’octets qu’elles partagent — était lu par
`profile_resume_requirements` et éditable par rien. `resume_editor.py` ferme les deux, sous le
cycle habituel, en une seule écriture atomique parce que les deux déclarations vivent dans le même
fichier.

**Ce lot n’est pas un éditeur de plus : celui-ci casse quelque chose en vol.** La barrière de
reprise lie une session au hash exact du dossier qui l’a armée, et ce dossier est compilé depuis ces
exigences et depuis le hash du profil. Changer l’un ou l’autre rend tout accusé déjà armé
impossible — la garantie qui fonctionne, pas un défaut. Le preview **nomme donc les gardes qu’il
invalidera**, avec leur hash, avant toute écriture, et l’application rapporte ceux qu’elle a
effectivement invalidés. Un éditeur qui casserait silencieusement une reprise en cours serait la
manière la plus polie de perdre une session.

**Le critère de sortie est prouvé dans ses deux moitiés, contre le Core.** Ce que le preview
annonce est exactement ce que `profile_resume_requirements` dérive ensuite. Et une garde armée sous
l’ancien contrat n’acquitte plus : réarmée sous le nouveau, elle exige un hash différent, l’ancien
est refusé, le nouveau accepté. Le pendant est épinglé chaque fois — sans lui, un refus général
prouverait la même chose qu’un moteur cassé.

**Puis la mesure a trouvé deux briques que ce lot ne pouvait pas contourner.**

**Première brique : toute édition de profil rendait le store SQLite inouvrable.** `project_identity`
inclut `profile_hash`, et `MemoryStore` s’y lie ; écrire un profil édité sans réaligner l’identité
laissait la mémoire du projet définitivement fermée. **B4 avait livré ce défaut** : le lot taxonomie
éditait le profil et ses tests n’ouvraient jamais de store avant d’éditer, si bien que rien ne l’a
vu. `profile_rebind` possédait déjà la machinerie exacte — sauvegarde, journal, `rebind_identity`,
écriture, puis nettoyage, avec la reprise Doctor en cas d’interruption. Elle est extraite en
`commit_profile_change`, le rebind y est routé pour qu’il n’existe qu’une implémentation, et les
deux éditeurs de profil l’utilisent. Une édition sur un projet sans store n’en crée aucun pour le
plaisir d’en rebinder un.

**Seconde brique, découverte en corrigeant la première : le Front devenait inécrivable.**
`FrontService.current()` lisait la dernière révision **quelle que soit** son profil, `_from_row` la
refusait comme étrangère, et comme `replace` lit le Front courant pour s’y chaîner, plus aucune
révision ne pouvait être enregistrée. Le Front était donc illisible *et* inécrivable, sans issue.
La requête est désormais **bornée au profil courant** : une révision d’un profil précédent est son
historique, pas le Front de celui-ci. Tous les refus restent intacts — une révision étrangère n’est
jamais courante, ne nourrit aucun handoff, n’arme aucune reprise — elle cesse simplement de bloquer
la suivante. `get()` la refuse toujours nommément.

**Une conséquence à dire plutôt qu’à taire.** Après une édition de profil, `_verify_dossier` refuse
un dossier ancien sur le **hash de profil** avant d’atteindre sa comparaison d’exigences. Cette
seconde règle ne peut donc se déclencher que sur un dossier fabriqué à la main. Le test l’énonce au
lieu d’affirmer un motif qu’il n’a pas obtenu.

**Une règle sans mordant, corrigée.** Retirer la revalidation du profil candidat ne faisait tomber
aucun test : toutes mes saisies invalides étaient déjà refusées en amont. Un identifiant de section
que ce module accepte mais que le contrat du Core refuse — `Not A Section!` — la rend seule cause du
refus. Les neuf autres règles du lot, et les deux refus côté interface, faisaient déjà tomber un
test chacune.

**Preuve.** `tests/test_resume_editor.py`, treize tests ; `apps/desktop/ui/src/resume.test.ts`, huit
tests. CLI `resume-contract`, bridge `resume.options` / `resume.preview` / `resume.apply`, commande
Rust et panneau de console. Suite complète : `887 passed, 69 subtests passed` côté Core et
`44 passed` côté interface. `tsc --noEmit`, `vitest run`, `vite build` et `cargo check` passent.

## LOG-0301 — Le MCP Preview de §34, et trois alertes qui ne peuvent plus se déclencher
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Rien ne classait les outils.** §34 demande de compter, avant génération, les outils en lecture
seule, en écriture, sensibles et réseau. La façade connaissait ses noms d’outils et rien d’autre :
n’importe quel décompte aurait donc été inventé à l’écran. `mcp_tool_classes.py` déclare ce que
chaque outil fait à l’état durable, et `mcp_preview.py` rend les chiffres, les hachages et les
alertes **sans en recalculer aucun** — une seconde mesure serait un second avis, et c’est l’écran
qui finirait par montrer le mauvais.

**Le marqueur évident n’était pas le bon.** `_mutating_call` ressemble à la réponse et ne l’est
pas : il signifie « rapporte ensuite le statut de synchronisation mémoire », pas « modifie quelque
chose ». `mmu_export_bundle` écrit une archive et `mmu_sync_memory` committe dans Git, et **aucun
des deux** ne passe par lui. Une classification dérivée de ce marqueur les aurait déclarés en
lecture seule : un décompte rassurant et faux. La table est donc déclarée, et un test épingle la
relation qui, elle, est dérivable — tout outil passant par `_mutating_call` doit être déclaré
`WRITE`. La réciproque est fausse, et c’est exactement le constat.

**Une dérive manifeste ↔ serveur, trouvée en comptant.** `mmu_get_documentation` est enregistré par
le serveur et **absent de `TOOL_NAMES`** : le manifeste annonçait quarante-six outils là où la
façade en sert quarante-sept. Tout chiffre bâti dessus sous-déclarait la surface. Le nom est ajouté
et un test lie désormais les deux ensembles, pour que la dérive ne revienne pas silencieusement.

**« Sensible » a une définition, pas une impression.** Un outil est sensible quand il écrit **hors**
du runtime VERA, remplace la mémoire canonique, ou signe une promotion `PROVEN`. Trois y répondent :
`mmu_sync_memory`, `mmu_restore`, `mmu_record_proof`. Tout autre choix aurait été une étiquette de
goût, et un décompte que personne ne peut vérifier. « Réseau » vaut zéro parce que zéro est vrai :
le Core ne tient aucun chemin réseau.

**Trois des quatre alertes de §34 ne peuvent plus se déclencher, et le preview le dit.** Une
capability sans validator objectif, une capability `NETWORK` derrière une gate, un chemin de sortie
hors périmètre : chacune était possible quand §34 a été écrit, et chacune est désormais refusée **à
la déclaration**, par le Core, sur le fichier déclaratif. Les rapporter à zéro se lirait comme une
rassurance ; elles sont rapportées `NOT_APPLICABLE` **avec la règle qui les a fermées**. C’est le
même raisonnement que le graphe de B5 : une alerte qui ne peut pas se déclencher n’est pas un
silence tranquille, c’est une règle qui a bougé.

**Celle qui reste atteignable l’est vraiment, et vaut la peine.** Le catalogue déclare un type de
validator, mais c’est `sync-capabilities` qui l’enregistre. Déclarer une capability avec le §32
builder puis générer sans resynchroniser produit une façade annonçant une capability qu’aucun
validator ne peut qualifier. L’alerte nomme la capability en cause, et elle est lue au même endroit
que le Doctor pour le secret HMAC, afin que les deux ne puissent pas se contredire.

**Mon test de décomptes se comparait à lui-même, et le contrôle de mordant l’a montré.** Il
vérifiait `payload["counts"] == tool_counts()` : remplacer le corps de `tool_counts` par une
constante faisait bouger les deux côtés ensemble et restait vert. Les figures sont maintenant
recomptées indépendamment — depuis la table, et depuis les enregistrements du serveur — avec la
partition épinglée : lecture seule plus écriture égale le nombre d’outils servis. Deux autres
décomptes passaient sur une coïncidence de valeur ; le test fait maintenant varier gates et
capabilities en sens opposés dans le même projet.

**Preuve.** `tests/test_mcp_preview.py`, douze tests ; `apps/desktop/ui/src/preview.test.ts`, neuf
tests. CLI `mcp-preview`, bridge `mcp.preview`, commande Rust et panneau de console. Suite
complète : `899 passed, 69 subtests passed` côté Core et `53 passed` côté interface. `tsc --noEmit`,
`vitest run`, `vite build` et `cargo check` passent.

---

## LOG-0302 — Le parcours cesse de finir en silence, et deux règles mortes tombent
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Le parcours finissait en silence sur un projet cassé.** Les quatre dernières étapes de §29.2 —
valider, générer, installer, lancer Doctor — existaient toutes et fonctionnaient toutes. Rien ne
les reliait. `wizard_state` rend `next_step: None` dès que chaque étape observable porte sa preuve,
et s’arrête là ; le Doctor siégeait dans la console comme un bouton parmi six, sous un titre
partagé avec la synchronisation mémoire. J’ai construit l’état : parcours mené jusqu’au bout par le
vrai pipeline, puis `memory.sqlite` supprimé. Le parcours répond « rien ne reste » et le Doctor
répond `FAIL`. Aucun écran du produit ne disait la seconde phrase. C’est ce silence que
`journey_outcome` ferme, et c’est de cet état que part le premier test du lot.

**Le wizard ne pouvait pas répondre, et ne doit pas essayer.** Il est délibérément bon marché,
total et dérivé : il doit décrire un projet à moitié configuré sans échouer dessus, donc il lit les
fichiers déclaratifs défensivement et n’ouvre jamais la mémoire. Le Doctor, lui, ouvre SQLite,
importe le runtime MCP et demande à Git ce qu’il suit. Fondre l’un dans l’autre aurait rendu le
parcours coûteux à chaque lecture et capable d’échouer sur l’état même qu’il existe pour décrire.

**« Non observable » recouvrait deux situations différentes.** Savoir si quelqu’un a *lancé* le
Doctor ne laisse aucune trace et n’en laissera jamais. Mais son **verdict** est une fonction pure
du projet sur le disque : personne n’a besoin d’avoir appuyé sur quoi que ce soit pour qu’il soit
vrai. Idem pour `validate`. Quatre étapes — scanner, détecter, proposer, prévisualiser — ne rendent
aucun verdict que le projet porte, et restent non observables pour de bon ; deux en rendent un, et
la conclusion le calcule. Les raisons affichées disent désormais laquelle des deux situations
s’applique, parce qu’aplatir les deux revient à annoncer qu’on ne peut rien savoir là où on peut.

**Le verdict est refusé tôt, exprès.** Tant qu’une étape observable est ouverte, le Doctor échoue
pour des raisons qui ne veulent dire que « pas encore » : pas de mémoire, pas de runtime généré,
pas de configuration hôte. Présenter cela comme des échecs à la fin d’un parcours qui n’est pas
fini apprendrait à l’opérateur à passer outre le seul contrôle qu’on ne doit jamais passer. Les
deux lignes valent alors `NOT_REACHED`, en nommant l’étape qui vient d’abord.

**Deux des trois relations croisées de `validate` ne pouvaient pas se déclencher.** Mesuré, pas
supposé : une gate référençant une capability non déclarée et une intégration activée sans Agent
Profile sont refusées par `load_project_catalogs`, qui lève avant que `_cross_references` ne soit
atteint. `project_validation` en portait sa propre copie ; aucune des deux ne pouvait être testée.
Une seconde implémentation d’une règle qui vit ailleurs n’est pas une défense en profondeur, c’est
une règle que personne ne peut éprouver et qui est libre de diverger de celle qui s’exécute. Les
copies sont retirées, et `test_cli_contract` épingle désormais **quelle couche refuse** chaque cas :
relâcher le chargeur fait tomber un test au lieu d’ouvrir un trou en silence. Ce que `validate`
ajoute vraiment reste : le contrat de reprise, que le chargeur ne lit jamais.

**Ce que le contrôle de mordant a trouvé.** Dix-huit règles neutralisées une à une ; dix-sept
mordaient du premier coup. La dix-huitième — la raison distincte des étapes 15 et 18 — était muette :
je l’avais écrite sans qu’aucun test ne la tienne, ce qui en faisait exactement la règle morte que
le même lot retire ailleurs. `test_wizard` épingle maintenant que ces deux étapes nomment la
conclusion et que les quatre autres ne la nomment pas.

**Ce que le lot ne fait pas, et qui est mesuré.** Cinq opérations du bridge ne sont appelées par
aucune commande Rust : `taxonomy.preview`, `taxonomy.apply`, `work.graph.read`, `work.graph.preview`
et `work.graph.apply`. Les étapes 5 à 8 du parcours ont donc un Core, un bridge et aucun contrôle
dans le Dashboard. Ce n’est pas bloquant pour conclure — le gabarit d’initialisation remplit déjà
ces sections, donc `COMPLETE` reste atteignable — mais c’est le même défaut, et il est inscrit en
B12 plutôt que traité ici.

**Preuve.** `tests/test_journey_outcome.py`, quatorze tests ; `apps/desktop/ui/src/outcome.test.ts`,
quatorze tests. CLI `conclude` (sortie `0` sur `COMPLETE` seulement), bridge `journey.outcome`,
commande Rust et panneau de console rendant le verdict, les deux lignes de clôture, les contrôles en
échec avec leur réparation et les étapes restantes. Suite complète : `917 passed, 69 subtests
passed` côté Core et `67 passed` côté interface. `tsc --noEmit`, `vitest run`, `vite build` et
`cargo check` passent.

---

## LOG-0303 — Quatre étapes que le Dashboard affichait sans pouvoir les faire
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Le défaut, mesuré pendant B11.** Cinq opérations du bridge — `taxonomy.preview`,
`taxonomy.apply`, `work.graph.read`, `work.graph.preview`, `work.graph.apply` — n’étaient appelées
par aucune commande Rust, et `desktop-api.ts` comme `DesktopConsole.tsx` n’en contenaient aucune
occurrence. Les lots B4 et B5 avaient livré le Core et le bridge, jamais le parent natif. Les
étapes 5 à 8 du parcours étaient donc **affichées** par la console, **exécutables** par le Core, et
impossibles depuis le Dashboard. Chaque couche passait ses propres tests ; il fallait lire les
quatre fichiers côte à côte pour le voir.

**C’est le genre de vérification qui ne doit pas dépendre de l’idée d’aller regarder.**
`tests/test_desktop_surface_parity.py` ferme la chaîne dans les cinq directions : toute opération du
bridge est appelée par une commande Rust, tout appel Rust nomme une opération déclarée, toute
commande `#[tauri::command]` est enregistrée et réciproquement, et tout ce qui est enregistré est
exposé par `desktopApi` — et rien d’autre. Les analyseurs sont eux-mêmes vérifiés contre un membre
connu et une taille plausible : une expression régulière qui ne trouverait rien ferait passer toutes
les règles pour la mauvaise raison, ce qui est précisément le défaut que ces règles existent pour
empêcher.

**L’éditeur de taxonomie n’avait aucune lecture, et c’est plus grave qu’une commodité manquante.**
Pour changer une section, l’écran doit envoyer la liste **entière** de cette section. Sans moyen
d’apprendre la liste courante, il faudrait la remplir de mémoire, et chaque entrée oubliée serait un
retrait silencieux — un retrait que le Core refuse à juste titre quand il orphelinerait quelque
chose, mais qu’il accepte quand le type est inutilisé. `taxonomy_options` rend donc les types
déclarés **et le nombre d’enregistrements que la mémoire porte déjà sous chacun**, de sorte que ce
qu’un retrait orphelinerait est visible *avant* le preview, pas seulement dans son refus.

**Le sens du refus de l’interface a une direction précise ici.** Un décompte que le Core n’a pas
donné vaut `null`, jamais `0` : zéro se lit « sans risque », et un type montré à tort comme inutilisé
est la seule erreur qui orpheline réellement. De même, un cycle de vie dont le drapeau `editable`
est illisible est tenu pour fixe : proposer une édition que le Core refuserait est pire que taire
une édition qu’il aurait permise.

**Preuve.** Trois tests de lecture dans `tests/test_profile_taxonomy.py`, un test de route dans
`tests/test_desktop_bridge.py`, six règles de parité dans `tests/test_desktop_surface_parity.py`, et
`apps/desktop/ui/src/structure.test.ts`, onze tests. Six commandes Rust (`work_graph_read`,
`work_graph_preview`, `work_graph_apply`, `taxonomy_options`, `taxonomy_preview`, `taxonomy_apply`),
leurs méthodes `desktopApi`, et deux panneaux de console gouvernés par le parcours. Contrôle de
mordant : treize règles neutralisées une à une, toutes mordent. Suite complète : `927 passed,
69 subtests passed` côté Core et `78 passed` côté interface. `tsc --noEmit`, `vitest run`,
`vite build` et `cargo check` passent.

---

## LOG-0304 — Les deux plateformes attestent enfin ce que le README affirme
**Statut : PASS mesuré sur Linux x64 et Windows x64.**

**L’écart, avant.** Le dernier run natif était le #48, sur `14706d92`, le 15 septembre. Depuis :
dix commits, 63 fichiers, 8327 lignes ajoutées — B4 à B12, soit +129 tests Core, +68 tests
d’interface et six commandes Rust. Rien de tout cela n’avait jamais tourné sur Windows, et le README
prononçait pourtant une phrase sur « les deux plateformes ». La phrase était en avance sur la mesure.

**Run #49 sur `9861450` : les deux runners sont verts, quinze étapes chacun, et les décomptes sont
identiques.** `927 passed, 69 subtests passed` côté Core — 220,79 s sur Linux, 515,88 s sur Windows —
et `78 passed` sur huit fichiers côté interface. Aucun test n’est conditionné à une plateforme, donc
la collecte est bien la même des deux côtés : les chiffres se comparent.

**L’audit préalable n’a rien trouvé, et c’est un résultat.** Les trois causes racines de septembre
ont été reprises une par une sur le code ajouté depuis #48. Les cinq `fsync` nouveaux portent tous
sur `NamedTemporaryFile(mode="w")`, donc une poignée d’écriture — le défaut de #44 était un `fsync`
sur `"rb"`. Les deux seules occurrences de barre inverse sont des **validateurs qui la refusent**,
le bon sens. Les connexions SQLite nouvelles ferment en `finally`, et `MemoryStore.__exit__` appelle
bien `close()`, donc aucun `WinError 32` à l’unlink dans les tests de B11. Les cinq écritures
atomiques passent `newline="\n"` : sans cela Windows aurait écrit des CRLF, les octets auraient
changé, et **tous les hachages du projet auraient divergé entre plateformes** sans qu’aucun test
local ne le voie.

**Une piste ouverte puis fermée par la mesure.** `profile_taxonomy` construit son URI SQLite sans
`as_posix()`, contrairement à quatre autres sites — de quoi soupçonner la cause racine nº 2. Mais
`profile_migration` fait de même, cette ligne **est couverte** — la neutraliser fait tomber un test —
et elle était passée verte sur Windows au run #48. La forme nue fonctionne donc ; c’est une
asymétrie de style, pas un défaut, et rien n’a été changé pour un soupçon que la mesure contredit.

**Preuve.** Run `desktop-packaging.yml` #49, jobs `Linux x64` et `Windows x64`, conclusion `success`,
sur `9861450`. Les chiffres sont lus dans les logs des deux runners, pas déduits du run local.

---

## LOG-0305 — `C01` promu : la première parité ARET réellement exécutée
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Le diagnostic que je répétais était faux.** `REMAINING_WORK` affirmait que C1 était bloqué par le
matériel — qu’il fallait la chaîne d’outils ARET réelle, absente. Vérifié plutôt que repris : c’est
vrai pour **deux** couplages sur seize. Les quatorze autres exigent une comparaison de données et de
comportement, dont les seuls prérequis sont la source ARET et une mémoire baseline. Les deux sont
disponibles : 64 fichiers Python au commit `b9511dcc`, et `aret_memory.sqlite` de `11 280 384`
octets — exactement la taille que le registre cite — portant 17 `component`, 532 `knowledge`,
47 `relation`. Wine et MinGW manquent, et sont installables par apt.

**Le test de compatibilité existant ne testait pas la compatibilité.**
`test_aret_address_compatibility.py` compare la réimplémentation VERA à **ses propres attentes** ;
il n’exécute jamais `core/addressing.py`. Il passerait à l’identique si les deux modules
divergeaient. C’est un test de cohérence interne portant le nom d’un test de parité — la même famille
de défaut que le décompte auto-référentiel de B10, et la raison pour laquelle aucune ligne mère
n’avait jamais été promue.

**Ce qui a été mesuré.** Une copie octet pour octet de `core/addressing.py` est versionnée sous
`tests/fixtures/aret_v1/` avec son SHA-256 épinglé dans le test, plus les 22 adresses `ARET://` que la
baseline porte réellement, avec l’empreinte de la mémoire d’où elles viennent. Les deux
implémentations sont exécutées et leurs verdicts comparés : écriture `242 paires, 0 divergence` ;
round-trip `160 adresses produites par ARET, 0 non relue à l’identique` ; corpus réel
`22 adresses, 0 divergence` ; direction `0 élargissement, 80 resserrements`.

**La parité utile est dirigée, et les deux directions n’ont pas la même gravité.** Ne pas relire ce
qu’ARET savait écrire rendrait une mémoire existante partiellement illisible. Accepter ce qu’ARET
refusait ne casserait rien — c’est exactement pourquoi cela passerait inaperçu, et pourquoi c’est
épinglé séparément. Les 80 resserrements portent tous sur des formes non canoniques —
`%41`, `%ZZ`, espace littéral, `#`, `+`, `?`, `é`, `日本` — et le test vérifie qu’aucune n’est dans
l’image de `ARET.make_address` : un resserrement sur une forme écrivable serait une régression de
lecture déguisée en rigueur.

**Deux erreurs de ma propre mesure, corrigées avant d’écrire le test.** Le premier différentiel
comparait les **noms de classes d’exception** et rapportait 92 divergences d’écriture ;
`AretAddressCompatibilityError` hérite de `ValueError`, donc deux refus identiques se lisaient comme
un désaccord. Le vrai chiffre est zéro. Et la première mutation de contrôle — élargir `safe` de
`quote` avec `~` — s’est révélée inerte parce que `~` n’est jamais échappé par Python quel que soit
`safe` ; remplacée par le retrait de `!`, qui mord.

**Preuve.** `tests/test_aret_c01_addressing_parity.py`, dix tests, mordant vérifié règle par règle
(sept mutations mordent ; deux se sont révélées inertes par construction et non par lacune du test).
Suite complète : `937 passed, 69 subtests passed`. `C01` passe de `SPLIT` à `DONE` — première
promotion du registre, et gabarit des treize couplages de données qui restent.

**Ce que cette promotion ne dit pas :** rien sur les quinze autres couplages. Une parité d’adressage
n’est pas une parité ARET, et l’en-tête du registre le dit désormais explicitement.

---

## LOG-0306 — `C03` promu : une fixture écrite d’après un contrat ne peut pas le réfuter
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Le défaut, un cran plus profond qu’en `C01`.** Les tests de composant bâtissaient leur source avec
un `CREATE TABLE component` **écrit à la main dans la fixture**, et la conformité de schéma se
vérifiait contre `aret_v1_schema_manifest()` — une déclaration VERA de ce qu’est le schéma ARET que
rien n’avait jamais comparée au vrai fichier. En `C01`, un module était comparé à ses propres
attentes ; ici c’est la **fixture** qui est écrite d’après elles. Un contrat faux passerait partout,
puisque la source de test le satisferait par construction.

**Ce que la fixture ratait, concrètement.** La vraie table `component` est `STRICT` et porte
`description TEXT NOT NULL DEFAULT ''`. La fixture écrivait une table ni stricte ni pourvue de
défaut. Le contrat déclaré, lui, était exact — par soin d’écriture, jamais par vérification. La
différence compte : une colonne ajoutée ou un défaut retiré côté ARET passait inaperçu.

**La source se construit désormais avec le DDL d’ARET.** Les six `schema/*.sql` sont versionnés sous
`fixtures/aret_v1/schema/` avec leurs SHA-256 épinglés, exécutés dans l’ordre, puis peuplés des
vraies lignes de la baseline. Si le DDL versionné dérive de l’amont, le test échoue plutôt que de
valider VERA contre un schéma qu’ARET n’a jamais eu. C’est la règle à retenir pour les douze
couplages restants.

**Les six dimensions que le registre exige, mesurées.** Import : la chaîne entière — lecture,
préparation, préflight, projection, contrôle de cible, autorisation, import — pilotée depuis la
vraie page, `17 composants` devenus entités génériques, `IMPORTED_NO_PROMOTION`, titres et
descriptions français intacts. Les tests existants fabriquaient préflight et projection à la main
avec un hash de source inventé (`"a" * 64`) et deux composants imaginaires ; la chaîne n’avait jamais
été pilotée bout en bout depuis une source réelle. Unicité : clé primaire de la table `STRICT`,
collision refusée. Liens de connaissance : `520`, toutes cibles déclarées. Intégrité référentielle :
`0 orphelin`. Bundle : export puis restauration dans un projet neuf, `17 entités identiques`.
Absence de `component` dans le Core : scan.

**Un écart au passage.** `aret_v1_schema_manifest()` déclare 18 tables applicatives et les migrations
1 à 6. Confronté au DDL réel : exact, les six tables FTS que SQLite crée pour `knowledge_fts` mises à
part. Exact, mais jamais vérifié jusqu’ici.

**Preuve.** `tests/test_aret_c03_component_parity.py`, douze tests ; mordant vérifié règle par règle
(onze mutations, toutes mordent). Suite complète : `949 passed, 69 subtests passed`. `C03` passe de
`SPLIT` à `DONE` — deuxième promotion du registre.

**Ce que cette promotion ne dit pas :** rien sur les quatorze autres couplages.

---

## LOG-0307 — `C04` promu, et le premier test de parité qui trouve un défaut au lieu de le confirmer
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**L’unicité d’ARET ne franchissait pas la frontière.** Le schéma garantit
`UNIQUE(component_id, module, symbol)`. La projection fabriquait son identifiant en joignant les
trois par `-`, or `_SAFE` admet `-` **dans** les composantes. Trois familles de triplets distincts
produisaient donc le même identifiant VERA : séparateur dans le module contre dans le symbole
(`("a-b","c")` et `("a","b-c")`), module vide contre module nommé `root`, séparateur dans le
composant contre dans le module. L’import aurait soit échoué sur une collision, soit écrasé une
ligne par l’autre.

**Latent, pas théorique.** Aucune des neuf lignes réelles ne le déclenche — pas un tiret, pas un
module vide. Mais `module` vaut `''` **par défaut dans le schéma ARET lui-même**, ce qui rend la
deuxième famille inévitable dès qu’une ligne sans module apparaît. C’est le genre de défaut qui
attend la migration pour se manifester.

**La correction ne déplace que les cas ambigus.** La projection échappe le séparateur en `%2D`. Sur
le corpus réel les identifiants sont inchangés, et un seul test existant a dû bouger : celui qui
épinglait `aret-symbol--CMP-001-core-alpha` pour un composant dont l’identifiant contient justement
le séparateur — l’illustration exacte du défaut.

**Une protection morte, retirée puis remplacée par une règle vivante.** Le premier échappement
traitait aussi `%`. Le contrôle de mordant l’a trouvé muet : `_SAFE` interdit déjà `%` dans une
composante, donc cette branche était inatteignable. Plutôt que de la garder pour le principe, elle
est retirée et la dépendance est épinglée — un test vérifie que `_SAFE` ne peut pas admettre le
marqueur d’échappement. Élargir `_SAFE` fait désormais tomber une règle au lieu de rouvrir la
collision en silence.

**Les quatre autres dimensions.** Import exact : la chaîne structurelle entière pilotée depuis la
source réelle, `9 symboles` écrits après leurs `17 composants` — les tests existants fabriquaient
préflight, conformité et projection à la main. Relations vers entité : chaque parent projeté est une
entité déclarée. Lecteur V1 : les neuf lignes rendues à l’identique, pagination terminée. Rollback :
une collision introduite **après** l’autorisation — ce qu’aucun contrôle préalable ne peut voir —
annule la page entière ; neuf moins un ne donne pas huit lignes de plus.

**Les fixtures de parité sont désormais partagées.** `tests/aret_v1_baseline.py` porte l’unique
façon de bâtir une source ARET V1 : exécuter le DDL réel, puis peupler des vraies lignes. Deux
fixtures divergentes seraient pires qu’une, et c’est exactement le défaut que `C03` a fermé.

**Preuve.** `tests/test_aret_c04_function_symbol_parity.py`, onze tests et six sous-tests ; mordant
vérifié règle par règle. Suite complète : `960 passed, 75 subtests passed`. `C04` passe de `SPLIT` à
`DONE` — troisième promotion.

---

## LOG-0308 — `C05` promu, et le piège inverse de `C04`
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Là où `C04` avait un défaut, `C05` avait un piège.** `brick.state` est contraint par un `CHECK` à
cinq valeurs, et il était tentant d’exiger que le `work_item` importé porte cet état. Ce serait
contredire le dessin que le registre énonce lui-même — « importer les briques avec leur métadonnée
sous namespace ARET », « le Core peut enregistrer un batch générique `WORK_ITEM` sans décider de la
sémantique legacy ». Le registre `work_item` fixe d’ailleurs `status = 'PLANNED'` par son propre
`CHECK` : le cycle de vie VERA est **événementiel**, porté par `work_lifecycle_event`, pas par une
colonne. Exiger la colonne aurait été inventer un défaut, ce qui coûte autant qu’en rater un.

**La parité tient donc en deux claims séparés, et les mélanger était l’erreur à éviter.** L’état
ARET est conservé sans perte — `PLANNED 10, ACTIVE 1, DONE 2`, jalons, plateformes et lien composant
compris. Et le cycle de vie de VERA tourne sur un item importé : `PLANNED → ACTIVE → COMPLETED`, avec
refus de la transition hors séquence. Les deux sont mesurés, séparément.

**Le Front sert de fil.** `RECOV-SPIRVCROSS-0X0` est la seule des treize briques à l’état `ACTIVE`,
et c’est bien elle que le `front_state` d’ARET désigne. C’est elle qu’on importe, qu’on démarre et
qu’on nomme dans le Front de VERA : une parité qui perdrait ce fil rendrait la reprise muette sur ce
que le projet était en train de faire.

**Les quatre autres dimensions.** Ordre roadmap : l’ordre de `idx_brick_roadmap` reste calculable
hors SQLite, et la brique active y arrive en tête. Liens : `component_id` est **nullable** —
contrairement à `function_symbol` — avec `8 liées / 5 non liées / 0 orpheline`, et l’absence de lien
survit à l’import. Dépendance/cycle : arête acceptée, boucle et auto-arête refusées, aucune arête
laissée derrière. Import V1 : `13 work items` exacts.

**Une seconde ceinture, nommée plutôt que supposée.** Le contrôle de mordant a montré que retirer la
garde Python contre l’auto-dépendance laissait le test vert : le schéma porte aussi
`CHECK(dependent_id != prerequisite_id)`, et SQLite prenait le relais. Plutôt que de resserrer sur un
message d’erreur — fragile —, le test nomme désormais **les deux couches**, comme `C01` nomme celle
qui refuse une adresse non canonique. Retirer l’une d’elles fait maintenant tomber une règle.

**La conformité de schéma a vu le vrai DDL pour la première fois.** Le `brick` réel naît de `001`
**plus** l’`ALTER TABLE` de la migration `005`, et SQLite stocke alors un texte que personne
n’écrirait à la main. La conformité de VERA passe dessus — elle était juste, mais jamais éprouvée.

**Preuve.** `tests/test_aret_c05_brick_parity.py`, treize tests et trois sous-tests ; mordant vérifié
règle par règle. Suite complète : `973 passed, 78 subtests passed`. `C05` passe de `SPLIT` à `DONE` —
quatrième promotion.

---

## LOG-0309 — `C02` promu : trois resserrements prouvés plutôt qu’affirmés
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Les faits ARET sont extraits, pas transcrits.** `legacy_runtime_layout()` déclare cinq chaînes —
`ARET_MEMORY_DIR`, `.aret-memory`, `aret_memory.sqlite`, `artifacts`, `exports` — et rien ne les
avait jamais confrontées au code qui les porte. Le test parcourt désormais l’arbre syntaxique de
`MemoryStore.__init__`, versionné sous `fixtures/aret_v1/source/` avec son SHA-256. Comparer une
déclaration à une transcription n’aurait prouvé que la fidélité du copier-coller.

**Trois resserrements, et il fallait montrer qu’ils sont délibérés.** ARET résout en lisant
`os.environ["ARET_MEMORY_DIR"]` : un resolver qui consulte l’environnement global décide d’un chemin
que l’appelant n’a pas vu passer. VERA exige un mapping fourni, et poser la variable ne déplace rien
— mesuré en la posant. ARET **crée** ses trois répertoires : un resolver qui crée transforme une
faute de frappe en projet vide. VERA refuse un runtime absent et ne laisse rien derrière lui.

**Le troisième est une correction, pas un choix de style.** Le checkpoint WAL d’ARET ne contrôle que
`busy`. Or déclarer `journal_mode=WAL` n’ouvre pas le WAL : tant que la connexion n’a pas lu la base,
le pager n’en tient aucun et `wal_checkpoint` répond `(0, -1, -1)` — un succès sur rien,
indiscernable d’un vrai repli pour qui ne regarde que `busy`. VERA lit d’abord, puis exige
`busy == 0` **et** `log == 0`. Le mode de défaillance avait été mesuré sur un runner Linux au run
CI #47 ; le test épingle maintenant les deux côtés, la lecture préalable comprise.

**Le multi-repo a deux faces, et n’en épingler qu’une en ferait un défaut.** Mon premier test exigeait
que deux racines différentes donnent des identités différentes. Il a échoué, et c’est l’assertion qui
avait tort : `_workspace_hash` hache une topologie **relative à la racine du projet** —
« portable workspace topology » — délibérément, et c’est cette portabilité qui rend le bundle de
`C03` restaurable dans un autre checkout. Le test épingle donc les deux : deux projets déclarés
différemment ne partagent aucune identité, et un même projet déplacé garde la sienne. ARET, lui, liait
son store à un chemin absolu tiré de l’environnement.

**Preuve.** `tests/test_aret_c02_runtime_parity.py`, douze tests et quatre sous-tests ; mordant
vérifié règle par règle. Suite complète : `985 passed, 82 subtests passed`. `C02` passe de `SPLIT` à
`DONE` — cinquième promotion.

---

## LOG-0310 — `C16` promu : la baseline montre I004 en train de tenir
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Le fait le plus intéressant n’est pas un défaut, c’est une confirmation.** La mémoire réelle porte
quatre preuves, toutes `PASS` et toutes `exit_code=0`. Aucune n’est admissible, aucune ne porte de
reçu HMAC. `KN-0011` est liée à trois d’entre elles — et n’est pas `PROVEN`. Cinq cent trente-deux
connaissances, zéro promotion. I004 n’est donc pas une intention de conception : c’est un
comportement observable dans des données de production, et le test part de cette situation exacte
pour exiger que VERA la refuse pareillement.

**Les deux moteurs ne placent pas la règle au même endroit, et l’exiger aurait été inventer un
défaut.** ARET garde une colonne `knowledge.status` et la protège par `reject_unproven_insert` et
`reject_unproven_promotion`. VERA n’a pas de statut à faire basculer : une promotion **est** une
ligne de `knowledge_proof`, table dont le `CHECK` n’admet que `PROVEN` et que deux triggers rendent
append-only. La vraie parité est le refus sans preuve admissible, pas la forme qu’il prend.

**L’append-only d’ARET est plus étroit qu’il n’en a l’air, et c’est mesuré en exécutant son propre
DDL.** Refusés : l’insertion directe en `PROVEN`, la promotion sans preuve admissible, la réécriture
du contenu. **Acceptés :** la mise à jour du seul statut — par conception, c’est ainsi que
`ACTIVE`/`SUPERSEDED` se déplacent — **et la suppression d’une connaissance**. ARET protège le
contenu, pas l’existence ; il n’a aucun trigger de suppression. VERA refuse toute mise à jour et
toute suppression.

**Un refus arrive une couche plus tôt chez VERA.** Une evidence `FAIL` n’atteint jamais le seuil de
promotion : `AdmissionService` n’admet qu’une evidence `PASS`, là où ARET laisse la preuve entrer en
table et la barre au moment de promouvoir. Les deux refusent ; VERA laisse moins d’états
intermédiaires à raisonner. Le test nomme les deux étages plutôt que de contourner la différence.

**Deux mutations de contrôle invalides, corrigées.** Renommer un trigger ne le désactive pas — il
continue de se déclencher — donc mes deux premières neutralisations d’append-only étaient muettes
pour une raison qui ne disait rien du test. Reprises en `WHEN 0`, elles mordent.

**Preuve.** `tests/test_aret_c16_epistemic_parity.py`, treize tests et sept sous-tests ; mordant
vérifié règle par règle. Suite complète : `998 passed, 89 subtests passed`. `C16` passe de `SPLIT` à
`DONE` — sixième promotion.

---

## LOG-0311 — `C09`, `C10` et `C11` promus : les trois couplages du serveur MCP
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Une seule source, trois aspects.** `aret_mmu_server.py` porte la doctrine statique, les
quarante-quatre outils écrits à la main et la racine unique imposée. Le verser une fois et l’analyser
dans `tests/aret_v1_server_reference.py` évitait trois copies qui divergeraient — et, plus important,
trois transcriptions de ce qu’il fait. Les outils, leurs paramètres et les constantes de module sont
extraits par analyse syntaxique.

**`C09` — la différence est de nature, pas de contenu.** `SERVER_INSTRUCTIONS` est une constante de
module : un texte identique pour tout projet lançant ce serveur. Il ne peut pas mentir sur le projet
qu’il décrit, parce qu’il ne le décrit pas — et c’est le problème, puisque la reprise s’appuie
dessus. VERA compile les siennes et en publie le hash. Mesuré dans les deux sens : même projet donne
le même hash, deux projets différents en donnent deux, et modifier le playbook le déplace. Un hash
qui ne bouge jamais et un hash qui bouge sans raison sont deux façons de ne rien prouver.

**Le test de `C09` passait d’abord pour la mauvaise raison.** Il cherchait l’identifiant du projet
« quelque part » dans les instructions. Le contrôle de mordant l’a montré : figer l’identifiant côté
manifeste laissait le test vert, parce que le playbook le portait aussi. L’identifiant entre par
**deux routes** — l’en-tête `Project:` et le titre du playbook — et chacune est désormais exigée
séparément, avec leur nombre épinglé pour qu’une route ajoutée soit revue plutôt qu’absorbée.

**`C10` — le nombre d’outils n’est pas la mesure.** ARET en écrit 44, VERA en sert 47, et comparer
les deux nombres ne dirait rien : une surface plus large peut être plus sûre si chaque outil y est
borné. Ce qui se compare est ce que chaque surface sait dire d’elle-même. ARET ne porte aucune table
d’accès — vérifié en cherchant `READ_ONLY`, `SENSITIVE_TOOLS`, `NETWORK_TOOLS` et `TOOL_ACCESS` dans
sa source, tous absents ; sa seule borne est l’absence de `*args`/`**kwargs`, mesurée sur les 44.
VERA classe les 47 de façon exhaustive et partitionnante, chaque outil sensible porte son motif, et
la classe réseau est vide parce que le Core ne tient aucun chemin réseau.

**`C11` — ne pas avoir le champ est plus fort que valider sa valeur.** ARET expose `repository_path`
sur trois de ses 44 outils et refuse toute valeur différente de la racine configurée. VERA ne
l’expose sur aucun des siens : zéro paramètre contenant `path`, `root`, `dir`, `file`, `repository`,
`command`, `url` ou `cwd` — la seule exception, `direction`, est nommée et justifiée plutôt que
silencieuse. Un garde qui compare peut être relâché d’une ligne ; un champ qui n’existe pas ne peut
pas l’être. C’est le raisonnement de I008 déjà appliqué au champ de commande de §32.

**Quatre dimensions de `C11` sont mesurées ailleurs, et citées plutôt que recopiées.** No-Git,
multi-repo et traversal par `C02`, identité incohérente par `C16`, non-pollution par `C2`. Un test
vérifie que ces fichiers existent : une dimension dont la preuve aurait disparu redeviendrait une
affirmation sans support, ce que le registre interdit.

**Preuve.** Trois fichiers, vingt-deux tests et cent-sept sous-tests ; mordant vérifié règle par
règle, trois mutations invalides reprises. Suite complète : `1020 passed, 196 subtests passed`.
**Neuf couplages sur seize sont désormais clos.**

## LOG-0312 — `C13` promu : la première fois que la référence ARET est **exécutée**
**Statut : PASS mesuré sur Linux x64. Les ajouts restent à attester sur Windows.**

**Un changement de méthode, imposé par la question posée.** Les douze couplages promus avant
celui-ci tiraient leurs faits ARET d’un arbre syntaxique : c’est la bonne lecture pour une
constante de module, un DDL ou une signature d’outil. `C13` demande autre chose — *que fait ce code
devant un dépôt Git réel* — et aucune lecture ne répond à cette question. `git_memory_reference.py`
est donc chargé comme module par `tests/aret_v1_git_reference.py` et ses fonctions tournent sur de
vrais dépôts montés pour l’occasion, à côté de celles de VERA sur les leurs. La copie versionnée
reste la seule source : la mesure doit porter sur le fichier dont le hash est épinglé.

**Le défaut trouvé dans ARET V1.** `invoke()` termine par `completed.stdout.strip()`. Appliqué à la
sortie de `git status --porcelain=v1`, ce `.strip()` retire l’espace de tête de la **première**
ligne quand celle-ci décrit une modification non indexée — la forme ` M chemin`. `changes()` découpe
ensuite à position fixe (`line[3:]`), et rend un chemin amputé de son premier caractère, avec les
deux caractères d’état décalés par-dessus le marché. `validate_scope` compare ce chemin au préfixe
du Memory Store, ne le reconnaît pas, et conclut qu’un fichier **situé dans** la mémoire est **hors**
de la mémoire.

Le cas où cela se produit n’est pas un cas limite : c’est le cas ordinaire, la base mémoire modifiée
en place et rien d’autre à côté. Mesuré sur un dépôt propre :

- `automatic_sync` rend `refused: True`, motif « Des changements hors du Memory Store sont
  présents : ret-memory/.aret-memory/aret_memory.sqlite » — en citant comme intrus un fichier de la
  mémoire, privé de son `a` initial. Aucun commit n’est fait.
- `sync_memory_only`, le point de persistance de fin de tour, filtre son périmètre avec le même
  parseur, ne trouve donc aucun changement mémoire, et rend « Aucun changement .aret-memory/ à
  committer » **sans erreur** pendant que la base est modifiée sur le disque. Le tour se termine sur
  un succès apparent et une mémoire non versionnée.

Le symptôme disparaît dès qu’une ligne indexée — qui commence par une lettre — passe en tête du tri :
`.strip()` n’a plus rien à retirer et toutes les lignes se découpent correctement. Un test écrit
avec un `git add` préalable passe donc, et ne dit rien du cas ordinaire. C’est vérifié ici aussi,
parce qu’une explication de pourquoi personne ne l’a vu vaut mieux qu’une supposition.

**Le défaut n’est pas corrigé.** La référence est une copie octet pour octet dont le hash est
épinglé ; la réparer reviendrait à mesurer autre chose qu’ARET. Il est consigné, et le mordant des
trois tests qui le constatent a été vérifié en le réparant temporairement : les trois tombent, et le
test de hash tombe avec eux.

**Pourquoi VERA y échappe, et ce n’est pas la chance.** Elle ne réimplémente pas le format de sortie
de Git. Elle passe le périmètre à Git sous forme de pathspec — `git status --porcelain=v1 -- <spec>`
— et ne lit de la réponse que son caractère vide ou non. Il n’y a pas de chemin à découper, donc pas
de découpe à rater. Le test épingle les deux faces : le comportement (la mémoire est bien committée
dans la situation exacte qui fait échouer ARET) et la raison (`return bool(changed)`, aucun
`splitlines()`, aucun `line[3:]` dans la source).

**La règle morte trouvée dans VERA, et corrigée.** En écrivant le cas de la HEAD détachée, le refus
attendu est bien arrivé — avec le mauvais motif. `symbolic-ref --quiet` ne rend pas une sortie vide
sur une HEAD détachée : il **sort en erreur**. Le refus passait donc par le gestionnaire générique
de `_run`, et le diagnostic dédié écrit juste en dessous — « HEAD détachée : aucune branche mémoire
à pousser » — n’était atteignable par aucun chemin. La sûreté était intacte, la lisibilité non : un
mainteneur lisant ce code croyait à une branche qui ne s’exécutait jamais. L’appel est désormais
fait directement et le motif exigé par le test est le diagnostic. Quatrième règle morte trouvée par
mutation dans cette série, après les deux de `B11` et la garde de `C04`.

**Les sept dimensions du registre, et ce que chacune a donné.**

| Dimension | ARET, exécuté | VERA, exécuté |
|---|---|---|
| NoVCS | `GitMemoryError` remontée de Git lui-même | `NO_VCS` observé sans lancer de commande ; sync `REFUSED` non fatal, la mutation SQLite survit |
| Git nominal | refuse (le défaut ci-dessus) | `COMMITTED`, périmètre `.vera-mmu` seul |
| Hors scope | refus **global** : un fichier de code en cours suffit à ne pas persister la mémoire | commit de la mémoire, travail en cours intact — suivi **et** non suivi |
| WAL occupé | lève, l’exception traverse `automatic_sync` | `REFUSED` dans la valeur de retour |
| HEAD détachée | `automatic_sync` ne consulte **jamais** HEAD : il pousse le nom écrit dans le fichier de policy | aucun nom à pousser, `CURRENT` seul admis, refus nommé |
| Refus de push | garde sur `--yes`, mais remote et branche viennent de `argv` | pas de destination à recevoir : hors `origin`/`CURRENT`, la policy est refusée avant tout commit |
| Policy invalide | clef inconnue **silencieusement retirée**, policy acceptée | contrat fermé, `REFUSED` |

Les deux points d’accord sont dits aussi — JSON illisible et `auto_push` sans `auto_commit` sont
refusés des deux côtés — parce qu’une parité qui ne relèverait que les divergences serait un
réquisitoire, pas une mesure.

**Deux mutations invalides, reprises.** Router le diagnostic de HEAD détachée autrement laissait le
test vert, parce que la sortie est vide dans les deux cas : la mutation juste est le retour au code
d’avant. Et `commit -a` ne stage pas les fichiers non suivis, si bien que le test du périmètre
passait encore ; le scénario porte désormais un fichier **suivi et modifié**, et la mutation mord.

**Une mesure pour le mauvais motif, resserrée.** Le test du remote imposé cherchait le mot
« origin » dans le motif de refus. Mesuré : le refus faute de remote contient ce mot lui aussi, donc
le test passait sans que la policy ait rien refusé. Le scénario monte maintenant un vrai remote, et
l’assertion porte sur la phrase de la policy et sur le fait que le dépôt distant n’a rien reçu.
Même classe de défaut que `C09` : une propriété satisfaite par plus d’une route ne prouve aucune
des deux.

**Preuve.** `tests/test_aret_c13_git_sync_parity.py`, quatorze tests ; sept règles VERA mutées une à
une, mordant vérifié ; le défaut ARET muté aussi. Suite complète : `1034 passed, 196 subtests
passed`. **Dix couplages sur seize sont désormais clos.**

## LOG-0313 — Run #50 : trois causes Windows, dont une qui attaquait le fondement de la parité
**Statut : Linux vert (`1016 passed`), Windows rouge à 18 échecs. Corrigé ; à ré-attester.**

Le run #50 sur `700e011` est la première attestation deux plateformes depuis que la série de parité
existe. Elle a trouvé trois défauts, tous propres à Windows, tous dans les tests plutôt que dans le
moteur — et le premier mettait en cause la prémisse même du programme de parité.

### 1. Git réécrivait les références épinglées (huit échecs)

Les fixtures ARET sont versionnées comme des **copies octet pour octet**, et leur SHA-256 est
épinglé : c'est ce qui rend la mesure opposable. Le runner Windows les sortait du dépôt converties
en CRLF, parce qu'aucune règle ne l'en empêchait. Une copie normalisée au checkout n'est plus la
copie dont le hash est épinglé — le fondement du raisonnement tombait, sans que rien ne le dise
ailleurs que par un test rouge.

La cause a été confirmée par le calcul avant d'être corrigée : le SHA-256 de chaque fichier converti
en CRLF **reproduit exactement** l'empreinte observée sur le runner, sur les quatre fichiers.

*Corrigé :* un `.gitattributes` marque `tests/fixtures/aret_v1/** -text`. Vérifié par un checkout
Windows simulé — un clone sous `core.autocrlf=true` — dans les deux sens : avec la règle, les quatre
empreintes sont justes et aucun CRLF n'apparaît ; sans elle, le fichier sort en CRLF avec le hash
`1ae8243d…`, celui-là même que Windows a rapporté.

### 2. Une racine temporaire non canonique (dix échecs)

Les lecteurs ARET refusent une racine non canonique, et ils ont raison : un chemin qui a deux
écritures est ambigu, et c'est exactement ce qu'un import ne doit pas avaler. Mais les tests leur
remettaient le chemin brut de `TemporaryDirectory`, qui n'est canonique que par accident. Sur
Windows il porte un nom court 8.3 — `C:\Users\RUNNER~1\…` — et `resolve()` ne l'étend que pour un
chemin **existant**, faute de poignée à ouvrir. `source_root()` résolvait avant de créer : la racine
restait non canonique, et le garde refusait.

C'était un défaut latent des tests, pas du moteur, et Linux ne pouvait pas le montrer : `/tmp/xxx`
y est canonique. La condition a néanmoins été reproduite ici avant correction, en remettant au
lecteur une racine non canonique atteinte par un lien : même refus, même message, et la résolution
le lève.

*Corrigé :* `temporary_root()` dans `tests/aret_v1_baseline.py` rend un répertoire temporaire déjà
canonique, et `source_root()` résout **après** la création. Les trente-et-un sites des cinq fichiers
concernés passent par ce socle.

### 3. Une connexion SQLite jamais fermée (un échec)

`sqlite3.connect(database).execute(...)` en une expression : la connexion n'a pas de nom, donc
personne ne la ferme, et Windows refuse ensuite d'effacer le répertoire temporaire — `WinError 32`.
Même classe que les six fixtures corrigées au run #46, où le motif était `with sqlite3.connect(...)`
qui valide mais ne ferme pas. *Corrigé :* `closing()`. Le reste des fichiers de parité a été
balayé : c'était la seule occurrence.

### Ce que ce run dit de la méthode

Les trois causes sont des défauts de **test**, pas de moteur, et les trois étaient invisibles sur
Linux. C'est l'argument pour la matrice deux plateformes, et c'est aussi la raison pour laquelle la
dette Windows ne doit pas s'accumuler : cent-sept tests avaient été écrits entre le run #49 et
celui-ci, et dix-huit d'entre eux étaient faux sans que rien ne le signale.

Suite complète après correction sur Linux : `1034 passed, 196 subtests passed`. Le décompte Windows
reste à établir au prochain run.

## LOG-0314 — Run #51 : la dette Windows est soldée, et les trois corrections tiennent
**Statut : PASS attesté sur Linux x64 et Windows x64, décomptes identiques, zéro échec.**

Run #51 sur `c014dbf`, le 19 septembre 2026. Les deux runners sont verts de bout en bout et rendent
**les mêmes chiffres** :

| | Linux x64 | Windows x64 |
|---|---|---|
| Suite de conformité | `1034 passed, 196 subtests passed` en 238,25 s | `1034 passed, 196 subtests passed` en 628,06 s |
| Tests d’interface | `78 passed` | `78 passed` |
| Sidecar natif, archive CLI | verts | verts |
| Bundles | AppImage, `.deb` | NSIS, MSI |

C’est la première attestation deux plateformes à couvrir les **107 tests de parité** `C01`–`C05`,
`C09`–`C11`, `C13` et `C16`. La restriction que le README portait depuis `C01` — « attestés
seulement sur Linux x64 » — tombe.

**Les trois corrections du run #50 sont vérifiées par le runner, pas par raisonnement.** Le
`.gitattributes` empêche Git de réécrire les références épinglées, donc les empreintes SHA-256
tiennent des deux côtés ; `temporary_root()` rend aux lecteurs ARET une racine canonique malgré le
nom court 8.3 du chemin temporaire Windows ; la connexion fermée laisse Windows effacer ses
répertoires. Zéro occurrence de `FAILED` dans les deux journaux.

**Une note de procédure, parce qu’elle change la cadence de travail.** Jusqu’ici le workflow ne
pouvait être déclenché que par le propriétaire : le jeton de la GitHub App était en lecture seule
sur Actions, et une tentative rendait `403 Resource not accessible by integration`. Le workflow,
lui, déclarait `workflow_dispatch` depuis toujours — il n’était pas en cause. La permission
`Actions: write` ayant été accordée, un lot peut désormais être attesté sur les deux plateformes
dans la foulée de son commit, au lieu d’attendre. C’est précisément la boucle qui avait laissé
cent-sept tests non attestés et dix-huit d’entre eux faux.

## LOG-0315 — `C14` promu : le bundle d'ARET exécuté, et ce qu'il ne sait pas dire
**Statut : PASS mesuré sur Linux x64. À attester sur Windows au prochain run.**

`C13` avait inauguré l'exécution de la référence ARET. `C14` la pousse plus loin : ce n'est plus une
fonction isolée qui tourne, c'est le `MemoryStore` entier, migré sur son propre DDL. Le layout
versionné le permet sans rien modifier — `_migrate` et `_bundle_migrations` cherchent leur schéma à
`Path(__file__).parents[1] / "schema"`, ce qui, depuis `fixtures/aret_v1/source/`, désigne
exactement `fixtures/aret_v1/schema/` et ses six migrations réelles. La seule dépendance externe,
`core.addressing`, est la référence déjà versionnée pour `C01`, présentée sous ce nom avec son
empreinte épinglée : charger un autre adressage ferait tourner un ARET qu'on ne mesure pas.

**Ce qu'ARET fait bien, dit en premier.** Huit altérations, huit refus : snapshot modifié, artefact
substitué, migration allongée, artefact retiré, champ du manifeste changé, snapshot retiré, chemin
d'évasion `../`, manifeste vidé. Les comparaisons passent par `hmac.compare_digest`, et la chaîne
tient sur trois hashes — `db_hash` sur le JSON canonique du snapshot, `snapshot_sha256` sur ses
octets, `manifest_hash` sur le manifeste privé de lui-même — plus une empreinte par migration et
par artefact. `C14` n'est pas un couplage où VERA serait simplement meilleur, et un registre qui ne
relèverait que les divergences serait un réquisitoire, pas une mesure.

**Premier écart : l'identité, et il est structurel.** Le manifeste d'ARET n'en contient aucune. Le
mot « project » est absent de ses 2677 lignes, et le `source_device_id` qu'il écrit apparaît **une
seule fois** dans toute la source — à l'écriture. Il n'est comparé nulle part. Mesuré en
l'exécutant : un bundle exporté d'une mémoire s'importe sans une objection dans une mémoire qui n'a
rien à voir, et les dix-sept composants réels de la baseline y arrivent intacts. La seule garde est
« la cible doit être vide », et une cible vide est précisément le cas normal d'une restauration.
C'est I011 qui n'a pas de prise : rien ne lie cette mémoire à son projet.

**Second écart : ce que le mot « idempotent » recouvre.** ARET consigne le bundle importé dans
`bundle_import` et répond d'après cette entrée. Mesuré : après un import suivi d'une mutation, le
ré-import rend encore `idempotent: True` alors que la mémoire porte désormais une ligne que le
bundle ne contient pas. La réponse est exacte sur le registre — « j'ai déjà vu ce bundle » — et
trompeuse sur l'état. VERA n'accorde `ALREADY_RESTORED` que si l'empreinte de la mémoire **et** la
configuration cible correspondent, et refuse sinon plutôt que d'annoncer une équivalence fausse.

**Ce sur quoi les deux s'accordent :** ni l'un ni l'autre ne fusionne un bundle dans une mémoire
qui porte déjà quelque chose. ARET lève, VERA lève, et le motif de fond est le même — une fusion
que personne n'a demandée produirait un état dont aucun des deux ne répond.

**Restauration du corpus réel.** Les dix-sept composants de la mémoire baseline sont insérés dans un
store ARET réel, exportés par son propre `export_bundle`, et relus après import : identiques, avec
l'artefact joint. C'est la dimension « restauration du bundle M0.1 », faite sur des données de
production et par le bundle d'ARET, pas sur un échantillon écrit pour l'occasion.

**Deux mesures passaient d'abord par une seconde route, et ont été isolées.** Altérer la mémoire
d'un bundle VERA restait refusé même en retirant la vérification d'inventaire, parce que le hash de
mémoire est contrôlé une **seconde** fois par sa propre règle ; l'altération porte désormais aussi
sur un artefact, que seul l'inventaire couvre. Et le contrat fermé du manifeste est une règle **de
lecture** : un test qui n'inspecte que le manifeste produit à l'export ne la touche jamais. En
écrivant ce cas, une garde plus forte est apparue — VERA exige les octets **canoniques** du
manifeste, donc toute édition est refusée quel qu'en soit le contenu, ce qui masquait les règles
suivantes. Elle est désormais nommée séparément, et les cas qui visent le contrat fermé, la
bijectivité de l'inventaire et le hash de profil redondant sérialisent canoniquement pour
l'atteindre. Même classe de défaut qu'en `C09` : une propriété satisfaite par plus d'une route n'en
prouve aucune.

**Preuve.** `tests/test_aret_c14_bundle_parity.py`, onze tests et quinze sous-tests ; sept règles
VERA mutées une à une et trois règles ARET, mordant vérifié — et le test d'empreinte est tombé avec
les mutations de la référence, comme il doit. Suite complète : `1045 passed, 211 subtests passed`.
**Onze couplages sur seize sont désormais clos.**

## LOG-0316 — Run #52 : ARET laisse trois poignées ouvertes, et seul Windows le dit
**Statut : Linux vert. Windows rouge à 7 échecs, tous dans `C14`. Corrigé ; à ré-attester.**

Le run #52 sur `7c03ddf`, premier à porter les onze tests de `C14`, est tombé sur Windows :
`7 failed, 1038 passed`. Les sept sont exactement les sept tests qui construisent un `MemoryStore`
ARET, et tous échouent de la même façon — `PermissionError: [WinError 32]` sur
`…\\aret_memory.sqlite` pendant l'effacement du répertoire temporaire. Linux passait.

**La cause est dans ARET, et elle ne peut pas y être corrigée.** `_migrate` ouvre sa connexion avec
`with self._connection() as conn` : ce `with` ouvre une **transaction**, il ne ferme pas la
connexion. Les deux gestionnaires de contexte du dépôt — `_transaction` et `_read_connection` —
ferment bien en `finally`, et `checkpoint_wal` aussi ; `_migrate` est le seul site brut, et il
tourne à chaque construction de store. La connexion finit dans un cycle que seul un passage du
ramasse-miettes défait.

**Mesuré sur Linux avant toute correction**, et c'est ce qui a évité de conclure par ressemblance :
après la seule construction d'un store, `/proc/self/fd` porte **trois** descripteurs ouverts — la
base, son `-wal` et son `-shm`. Un `gc.collect()` les ramène à zéro. Linux efface sans broncher un
fichier ouvert, donc la fuite était invisible ici ; Windows refuse, et c'est tout l'écart.

*Corrigé :* `temporary_root()` appelle `gc.collect()` **avant** `cleanup()`, donc avant
l'effacement et non après. La référence ARET n'est pas touchée — son empreinte est épinglée, et la
réparer ferait mesurer autre chose qu'ARET. C'est la troisième fois de la série qu'une poignée
SQLite non fermée fait tomber Windows : six fixtures au run #46, une expression sans nom au #50, et
ici un défaut de la référence elle-même, qu'il faut contourner plutôt que réparer.

Suite complète après correction sur Linux : `1045 passed, 211 subtests passed`.

**Attesté au run #53 sur `76ef275` :** les deux runners verts, `1045 passed, 211 subtests passed`
côté Core — 290,46 s sur Linux, 587,34 s sur Windows — et `78 passed` côté interface, chiffres
identiques, zéro échec et **aucune occurrence de `WinError`** dans les deux journaux. Le contournement
tient. L'attestation deux plateformes couvre désormais l'intégralité des **118 tests de parité**
`C01`–`C05`, `C09`–`C11`, `C13`, `C14` et `C16`.

Le cycle complet — écrire le lot, le pousser, déclencher l'attestation, corriger et réattester — a
tenu dans l'heure, parce que le workflow est déclenchable depuis la session. Comparé aux cent-sept
tests non attestés du run #50, c'est ce que change la permission `Actions: write`.

## LOG-0317 — `C06` promu : le catalogue d'ARET est fermé, son contrat de paramètres ne l'est pas
**Statut : PASS mesuré sur Linux x64. À attester au prochain run.**

Troisième couplage à exécuter ARET plutôt qu'à le lire. `evidence/adapters/pipelines.py` est versé
sous `fixtures/aret_v1/source/` avec son empreinte, chargé par
`tests/aret_v1_pipelines_reference.py`, et tourne contre le vrai `MemoryStore` d'ARET — l'import
`core.repository` est satisfait par la référence déjà chargeable de `C14`. `PROJECT_ROOT` y est
déclaré et n'est utilisé nulle part, vérifié sur la source entière, donc le déplacement du fichier
ne change rien à son comportement.

Les mesures se font en **dry-run**, et c'est le bon périmètre : `C06` porte sur ce qui se décide
avant l'exécution — le nom, les paramètres, le timeout, la policy. L'exécution réelle est
`C07`/`C08`, qui demandent Wine et MinGW.

**Ce qu'ARET fait bien, et il faut le dire avant le reste.** Son catalogue est une liste fermée de
**27 pipelines** nommés — 15 `READ_ONLY`, 9 `GENERATE`, 2 `NETWORK`, 1 `SENSITIVE` — comptés sur le
catalogue exécuté. Aucun client ne fournit de commande ; l'argv est construit par le moteur depuis
des chemins bornés au dépôt. Un nom inconnu est refusé, un timeout hors borne est refusé, et les
trois policies non triviales exigent chacune une confirmation **nommée** : `confirm_apply`,
`confirm_network`, `confirm_sensitive`. C'est un dessin sérieux.

**La divergence est structurelle et porte sur les paramètres.** Le catalogue déclare un nom, un
type, une description, des dépendances, un timeout et un runner. Il ne déclare **jamais** de schéma
de paramètres — vérifié sur les vingt-sept entrées et sur les huit champs de `PipelineSpec`. Les
paramètres sont un `dict` libre, validé au coup par coup à l'intérieur de chaque runner.

Mesuré en l'exécutant : `{"intrus": "valeur inventee", "rm": "-rf /"}` traverse la validation,
arrive dans le plan et y est rendu tel quel à l'appelant.

**Ce n'est pas une injection de commande, et le test l'épingle pour ne pas laisser croire à une
faille qui n'existe pas :** l'argv reste fermé — `["bash", "…/bench/regression.sh"]`, deux éléments
— et aucune de ces valeurs n'y entre. Le défaut est ailleurs, et il est plus insidieux : rien ne dit
quels paramètres un pipeline lit réellement. Mesuré aussi — un `binary_pathh` mal orthographié et un
`binary_path` absent rendent la **même** erreur, « Asset introuvable :  », avec un chemin vide.
L'appelant ne peut pas distinguer « tu as mal tapé la clef » de « tu as oublié la clef ». C'est
exactement ce qu'un schéma déclaré empêche, et c'est ce que `C06` demandait d'ajouter.

VERA déclare `parameter_schema` dans le contrat, le valide contre un sous-ensemble fermé de JSON
Schema — clefs racine limitées, racine `object`, `required` référençant une propriété déclarée — et
refuse à l'exécution un paramètre non déclaré, mal typé ou requis-absent. Son catalogue rend en plus
`command` sous la forme `{"status": "NOT_APPLICABLE", "reason": "…aucun champ de commande… (I008)"}` :
une case vide dans un formulaire se lit « à remplir », un `NOT_APPLICABLE` motivé se lit « il n'y en
a pas, et voici pourquoi ».

**Une nuance d'ARET est dite plutôt que tue.** Ses confirmations gardent l'**exécution**, pas la
consultation : `dry_run` est la valeur par défaut, et le plan d'un pipeline `SENSITIVE` se rend sans
confirmation, argv complet et `pid` inclus. C'est cohérent — on ne confirme que ce qu'on lance — mais
cela signifie qu'un argv sensible est lisible avant toute autorisation.

**Deux bornes de timeout, et une couche qui masquait l'autre.** Relâcher la garde Python de VERA
laissait le test vert : le `CHECK (timeout_seconds BETWEEN 1 AND 3600)` du DDL refuse la ligne de
toute façon. Le test nomme désormais les deux couches — motif exigé côté garde, `CHECK` épinglé
côté schéma — et neutraliser l'une ou l'autre se voit. Même discipline qu'en `C05`, où le garde
d'auto-arête était doublé par un `CHECK`.

**Preuve.** `tests/test_aret_c06_capability_parity.py`, quinze tests et quarante-cinq sous-tests ;
six règles VERA et trois règles ARET mutées une à une, mordant vérifié, et le test d'empreinte est
tombé avec chaque mutation de la référence. Suite complète : `1060 passed, 256 subtests passed`.
**Douze couplages sur seize sont désormais clos.**

**Run #54 : un échec Windows, et il venait du test.** `1 failed, 1059 passed`. L'assertion sur le
script du plan comparait une chaîne — `endswith("bench/gauntlet/score.sh")` — à un chemin qu'ARET
résout en `Path` et rend sous sa forme native. Sur Windows c'est `…\bench\gauntlet\score.sh`, et
la comparaison est fausse. Ni ARET ni VERA n'ont de défaut ici : le séparateur codé en dur était
dans le test.

*Corrigé* par une comparaison sur les **composants** du chemin — `Path(...).parts[-3:]` — qui est
indépendante de la plateforme et plus précise que l'ancienne, puisqu'elle épingle trois segments
plutôt qu'un suffixe. Vérifié dans les deux sens : `PurePosixPath` et `PureWindowsPath` rendent les
mêmes composants, là où l'ancienne assertion rendait `False` sur la forme Windows.

Le reste des tests de parité a été balayé pour la même classe d'erreur. Les autres occurrences de
séparateur littéral — `ARET://` en `C01`, `schema/` et `runtime/artifacts/` en `C14` — portent sur
un schéma d'adresse et sur des noms de membres ZIP, qui sont POSIX par contrat. Elles sont justes.

C'est la deuxième fois que ce projet écrit un séparateur natif là où un format portable était
attendu : au run #46 c'était le journal de migration, ici c'est un test. La leçon se répète, et
elle est consignée aux deux endroits.

**Attesté au run #55 sur `2806468` :** les deux runners verts, `1060 passed, 256 subtests passed`
côté Core — 355,00 s sur Linux, 885,66 s sur Windows — et `78 passed` côté interface, chiffres
identiques et zéro échec dans les deux journaux. `C06` est attesté sur les deux plateformes, et
l’attestation couvre désormais l’intégralité des **133 tests de parité** `C01`–`C06`, `C09`–`C11`,
`C13`, `C14` et `C16`.

## LOG-0318 — `C12` promu : le playbook, et ce qu'on apprend quand une règle n'arrive nulle part
**Statut : PASS mesuré sur Linux x64. À attester au prochain run.**

Quatrième couplage à exécuter ARET. Son playbook réel est versé sous
`fixtures/aret_v1/config/playbook.md`, et le chemin par défaut qu'ARET calcule —
`Path(__file__).parents[1] / "config" / "playbook.md"` depuis `source/repository_reference.py` —
désigne exactement cette copie. Le chargeur tourne donc sur le vrai fichier, ses cinq sections
réelles et leurs 8 019 octets de contenu.

**Le point d'accord d'abord, parce que c'est ce que `C12` protège.** Les deux moteurs tiennent le
playbook **hors** de la mémoire canonique. Chez ARET c'est écrit dans le fichier lui-même — « il
n'est jamais ingéré dans SQLite » — et chez VERA c'est la même règle. Les deux sont vérifiés en
éditant le playbook puis en rehachant la base : inchangée des deux côtés. Un fichier autoré qu'on
édite librement ne peut pas faire dériver la mémoire vivante, et c'est un bon dessin.

**Premier écart : ce qui arrive quand le playbook manque.** Le chargeur d'ARET rend une liste vide ;
le contrat de dossier signalera ensuite chaque domaine absent. VERA refuse à la compilation, et son
module dit pourquoi : un refus « plutôt qu'une section vide », parce que les instructions générées
ne doivent jamais laisser tomber en silence les règles qu'un projet a choisi d'imposer (I014). Les
deux réponses se défendent ; elles ne se ressemblent pas, et le registre demandait de le mesurer.

**Second écart, et c'est le plus coûteux à l'usage : le parseur d'ARET écarte en silence.** Mesuré
en l'exécutant sur trois fichiers construits pour l'occasion — un domaine **dupliqué** voit sa
seconde occurrence disparaître sans un mot, un titre `## PLAYBOOK_INVENTE` disparaît de même, et un
fichier absent rend `[]`. Un auteur de playbook ne peut donc pas savoir qu'une règle qu'il vient
d'écrire n'est arrivée nulle part. Une règle qui n'arrive nulle part n'est pas une règle.

**Troisième écart : les deux bornent, mais pas au même bout.** ARET borne le **dossier assemblé** à
12 500 octets, contrôlé après assemblage. Son fichier de playbook, lui, n'a aucune borne : la
mention « ≤ 12 500 octets » de son en-tête est un budget adressé à l'auteur, et le chargeur ne
mesure jamais la taille du fichier — vérifié sur le corps de la fonction, qui ne contient ni
`MAX_BYTES`, ni `len(text)`, ni `stat()`. VERA borne le **fichier** à 65 536 octets, refusé à la
lecture. Borner l'entrée dit quel fichier est fautif ; borner la sortie dit seulement que le total
déborde. Relevé au passage : le contenu réel des cinq sections occupe déjà plus de la moitié du
budget de dossier avant qu'un seul handoff n'y entre.

**Quatrième écart : les empreintes ne répondent pas à la même question.** ARET hache **chaque
section** — cinq empreintes distinctes, vérifiées — et n'expose aucune empreinte du fichier entier.
VERA hache le fichier entier et n'a pas d'empreinte par section, n'ayant pas de sections. « Cette
section a-t-elle changé ? » contre « ce playbook est-il celui que j'ai compilé ? » : aucune des deux
ne remplace l'autre, et le test épingle aussi l'absence de celle que chacun n'a pas.

**Injection de reprise.** ARET adresse ses sections par `playbook.md#<DOMAIN>`, ce qui permet de
désigner une loi sans la recopier. VERA cite son playbook **verbatim** dans les instructions
compilées — vérifié sur une ligne distinctive ajoutée exprès — et y énonce en plus ses huit lois
Core, toutes présentes.

**Preuve.** `tests/test_aret_c12_playbook_parity.py`, huit tests et dix-neuf sous-tests ; quatre
règles VERA et trois règles ARET mutées une à une, mordant vérifié. La mutation qui ajoutait une
sixième section au playbook réel n'a été rattrapée que par le test d'empreinte — c'est exactement
son rôle, puisque la section ajoutée était un doublon que le parseur écarte en silence. Suite
complète : `1068 passed, 275 subtests passed`. **Treize couplages sur seize sont désormais clos.**

**Attesté au run #56 sur `e2dbdfb` :** les deux runners verts, `1068 passed, 275 subtests passed`
côté Core — 248,19 s sur Linux, 696,16 s sur Windows — et `78 passed` côté interface, chiffres
identiques et zéro échec. L'attestation couvre l'intégralité des **141 tests de parité** `C01`–`C06`
et `C09`–`C16`.

## LOG-0319 — La suite passe de 261 s à 76 s, sans toucher un seul test
**Statut : mesuré cinq fois sur Linux x64, décomptes identiques à chaque passage.**

Le run CI atteignait vingt et une minutes, dont onze pour la seule suite de conformité côté Windows.
La question posée était de gagner du temps **sans casser les tests**, et la première chose à faire
était de mesurer plutôt que de deviner où il passe.

**Le profil ne montre aucun point chaud.** Les trente tests les plus lents pèsent 110 s sur 261 ;
le reste est étalé sur plus de mille tests, à 0,24 s de moyenne. Il n'y a donc rien à optimiser au
cas par cas : le levier est la parallélisation.

**Résultat : 261 s → 76 s sur quatre cœurs, facteur 3,43 pour un idéal de 4.** Cinq passages
successifs — `-n 4`, `-n auto`, et `--dist loadfile` — rendent tous exactement `1068 passed,
275 subtests passed`. Aucun test n'a été modifié, aucun n'a été marqué, aucun n'a été retiré.

**Le mode de distribution est choisi, pas subi.** `--dist loadfile` garde tous les tests d'un même
fichier sur un même worker. Plusieurs de nos fichiers partagent un module chargé une fois
(`aret_v1_repository_reference`, `aret_v1_pipelines_reference`) ou une variable d'environnement
qu'ils posent et restaurent (`ARET_PLAYBOOK_PATH`, `ARET_MEMORY_DIR`) ; les garder groupés retire
toute hypothèse d'ordre entre workers. Mesuré : **même durée** que la distribution test par test —
74 s contre 76 s. C'est donc le mode conservateur à prix égal, et il n'y avait pas à hésiter.

**Pourquoi les drapeaux sont dans le workflow et pas dans `addopts`.** Mettre `-n auto` dans la
configuration du projet ferait échouer `pytest` d'un contributeur qui n'a pas `pytest-xdist` — un
argument inconnu est une erreur dure, pas une dégradation. La suite doit rester exécutable après un
simple `pip install .`. `pytest-xdist` est donc déclaré dans un extra `test`, installé par la CI,
et les drapeaux sont écrits à l'étape qui s'en sert. Localement, `python -m pytest -q -n auto
--dist loadfile` donne le même gain, et `pytest` seul reste lisible pour déboguer.

**Le second levier, mesuré mais pas pris.** Ouvrir un `MemoryStore` coûte **94 ms**, dominés par
les trente-neuf migrations rejouées à chaque fois ; les tests l'appellent au moins 315 fois, soit
une trentaine de secondes de la suite en série. Le supprimer demanderait de mettre en cache une base
déjà migrée et de la recopier — ce qui touche la façon dont **tous** les tests bâtissent leur store,
et croise directement l'identité de projet que `I011` fait vérifier à l'ouverture. Le gain serait de
l'ordre de 10 %, le risque porte sur ce que les tests prouvent. Il est consigné ici comme disponible,
pas appliqué.

**Le troisième levier, pris celui-là : le workflow retéléchargeait ses dépendances à chaque run.**
Relevé sur les étapes du run #55, une fois la suite parallélisée le premier poste n'est plus la
suite mais la **construction des bundles** — 295 s côté Linux, 380 s côté Windows — parce que Tauri
recompilait ses **490 caisses** à chaque passage. Venaient ensuite l'installation pip (33 s sur
Windows, 11 s sur Linux) et l'`apt` Linux (45 s). Seul pnpm était déjà mis en cache.

Deux caches ajoutés : `cache: pip` sur `setup-python`, dont la clef dérive de `pyproject.toml`, et
`Swatinem/rust-cache` sur l'espace de travail `apps/desktop/src-tauri`, dont la clef dérive de
`Cargo.lock` et de la version de rustc. L'`apt` est laissé tel quel : le mettre en cache proprement
coûte plus de complexité que les 45 s qu'il rendrait.

**Une contrepartie est assumée et doit être dite :** avec un cache cargo, ce workflow ne vérifie
plus une construction entièrement à froid à chaque passage. Elle reste vérifiée dès que `Cargo.lock`
change, puisque la clef en dépend et que le cache est alors invalidé. C'est un échange délibéré
entre temps de boucle et surface de vérification, pas un oubli.

**Le premier run après cet ajout ne sera pas plus rapide** — il peuple les caches. Le gain se lit au
suivant, et c'est lui qu'il faudra mesurer avant d'annoncer un chiffre.

**Mesuré au run #57, et le gain est inégal entre les plateformes.** L'étape de conformité passe de
248 s à **85 s** sur Linux — facteur 2,9, cohérent avec les 76 s locaux, donc le runner a bien quatre
cœurs. Mais sur Windows elle ne passe que de 696 s à **412 s**, facteur **1,69**. Le job complet
tombe de ~13 min à ~8 min côté Linux, et de ~21 min à **15 min 14** côté Windows.

L'écart n'est pas expliqué par le nombre de cœurs, qui est le même. L'hypothèse la plus probable est
le coût de création de processus sous Windows : chaque worker xdist est un processus Python, et
surtout une partie de la suite — transports MCP en stdio, hooks, adaptateurs — lance de **vrais
sous-processus**, bien plus chers là-bas. Ce n'est pas vérifié, et c'est écrit ici comme hypothèse,
pas comme fait.

Profil Windows restant après parallélisation : conformité 412 s, bundles 341 s, installation pip
46 s, sidecar 42 s, archive CLI 30 s. Les deux premiers postes pèsent désormais autant l'un que
l'autre, ce qui est précisément ce que les caches ajoutés au commit suivant visent.

**Le gain des caches, mesuré au run #59 contre le run #58 qui les a peuplés.** Il est réel et il
est important, et c'est sur les bundles qu'il tombe, exactement là où il était visé :

| Étape | Linux #58 (froid) | Linux #59 (chaud) | Windows #58 (froid) | Windows #59 (chaud) |
|---|---|---|---|---|
| Restauration `rust-cache` | 2 s | 12 s | 3 s | 17 s |
| Installation pip | 12 s | 10 s | 29 s | 23 s |
| Suite de conformité | 107 s | 120 s | 409 s | 420 s |
| **Bundles desktop** | **324 s** | **162 s** | **336 s** | **144 s** |
| Sauvegarde `rust-cache` | 9 s | 0 s | 41 s | 0 s |
| **Job complet** | **9 min 31** | **7 min 14** | **15 min 33** | **11 min 55** |

Les bundles tombent de **moitié sur Linux** et de **57 % sur Windows**. Ce que le cache coûte se lit
aussi : sa restauration prend 10 s de plus qu'un cache vide, et sa sauvegarde ne coûte plus rien
quand rien n'a changé. Net : −2 min 17 côté Linux, −3 min 38 côté Windows.

**Une mesure incidente, et elle vaut d'être retenue pour la suite.** Entre `b91c771` et `834ee13` la
suite n'a pas changé d'une ligne — le second commit ne touche qu'un document. Son étape de
conformité passe pourtant de 107 s à 120 s sur Linux et de 409 s à 420 s sur Windows, soit jusqu'à
**12 % de variation d'un run à l'autre à code identique**. Toute comparaison de durée entre deux
runs doit s'en souvenir avant de conclure à un effet.

Le parcours complet depuis le début de ce travail : Windows 21 min → 15 min 33 → **11 min 55** ;
Linux ~13 min → 9 min 31 → **7 min 14**.

## LOG-0320 — `C15` : une barrière de reprise qui disparaît quand elle est en défaut

**Statut : `C15` promu `DONE`. 22 tests et 37 sous-tests, exécutés ; 18 mutations vérifiées mordantes.**

Cinquième couplage à **exécuter** ARET plutôt qu'à le lire, et le premier à exécuter ses *hooks* :
`resume_guard.py`, `common.py`, `session_start.py` et `post_compact.py` sont versionnés sous
`tests/fixtures/aret_v1/hooks/`, épinglés par leurs empreintes, et tournent ici sur un vrai
`MemoryStore` ARET. `session_start.handler` écrit un vrai fichier d'état, que le test relit.

Le registre demandait sept dimensions — session neuve, PostCompact, mode dégradé, acquittement
périmé, identité absente, kill-switch, Stop one-shot. Elles sont toutes couvertes, chacune posée
aux deux moteurs sur la même situation.

**Ce qu'ARET fait bien, et il faut le dire avant le reste.** Cinq choses, toutes mesurées, toutes
reprises par VERA sans rien y retrancher :

1. *Le kill-switch existe.* Son propre commentaire dit pourquoi : « une barrière ne doit jamais
   pouvoir s'armer sans issue », et il vient d'un deadlock réellement vécu. VERA honore même le nom
   de variable d'ARET, pour qu'un opérateur qui connaît l'un débloque l'autre.
2. *Le mode dégradé ne bloque pas dur.* Sur une mémoire cassée, un rituel rigide sans voie de sortie
   enferme l'agent. ARET arme quand même, injecte un contexte bruyant, et laisse passer.
3. *L'armement a lieu dans tous les cas.* Mesuré en exécutant le vrai `SessionStart` : sur une
   mémoire ARET vierge, le dossier est **dégradé** et la barrière s'arme malgré tout, en mode soft.
   Un ARET fraîchement installé ne bloque donc pas dur — ce qui ne se lit nulle part dans le code.
4. *`resume` préserve l'acquittement.* En session web ou asynchrone, `SessionStart` se redéclenche à
   chaque tour ; réarmer rebloquerait un agent vivant à chaque échange. Les deux distinguent ce cas.
5. *L'état reste éphémère et local.* Vérifié des deux côtés en réhachant la base après un armement
   et un acquittement : elle ne bouge pas d'un octet.

**La divergence porte sur ce qui arrive quand la barrière elle-même est en défaut**, et c'est
exactement ce que `I014` nomme. Trois mesures du même genre :

*Un état illisible désarme ARET.* `load_state` rend `None` sur un JSON corrompu comme sur un état de
version 2, et `decision` rend alors `None` : aucune décision, donc aucun blocage. La barrière
disparaît précisément là où elle devait tenir. `_read_existing` de VERA lève, et `precheck` refuse.

*Un état acquitté se transplante entre mémoires ARET.* Sa clef est `sha256(identité)[:24]`, sans
aucune identité de projet : le même fichier, copié dans une autre mémoire, y est **lu, accepté et
acquitté**. Le test le vérifie sur le contenu relu, pas seulement sur la décision — un état rejeté
y laisserait aussi passer l'action, et la distinction compte. Côté VERA, quatre couches (nom de
fichier, `sessionStateKey`, `projectId`/`projectHash`, `profileHash`) sont isolées **en réparant
toutes les autres**, si bien qu'aucune n'est créditée du travail d'une voisine.

*L'emplacement de l'état suit le payload.* Les wrappers d'ARET lisent `payload["memory_dir"]` avant
l'environnement : un payload nommant un autre répertoire ne trouve pas d'état, et la barrière laisse
passer. Celui de VERA se dérive du store déjà lié au projet (`I008`). Le payload d'un hook vient du
hôte et non du client : ceci mesure un chemin d'entrée, pas un exploit constaté, et c'est écrit ainsi.

**Trois écarts de plus, plus petits mais nets.** ARET tronque un récapitulatif à 4000 caractères et
enregistre l'acquittement comme complet — l'agent croit avoir déposé ce qu'il a écrit ; VERA refuse.
Les six volets d'ARET et leurs minimums sont des constantes de module ; le contrat de VERA est
déclaré par le projet et **inclus dans l'empreinte du dossier**, donc changer un minimum invalide
l'acquittement précédent sans toucher au moteur. Enfin ARET ne laisse aucune trace durable de son
rituel, là où VERA écrit deux lignes d'audit.

**Un accord qui n'est pas gratuit, et qui vaut pour les deux.** `resume` / `RESUME` préserve
l'acquittement *et adopte le nouveau hash de contrat* : un acquittement du contrat A vaut donc pour
le contrat B. Mesuré des deux côtés. Cela n'oppose pas les moteurs et ce n'est pas un défaut de
l'un d'eux, mais ce n'est pas rien, et le test l'épingle plutôt que de le passer sous silence.

**Un défaut de VERA trouvé par ce lot, et corrigé.** `precheck` consultait le kill-switch **après**
avoir lu l'état : sur un état illisible, la voie de sortie documentée ne fonctionnait plus — le cas
où l'opérateur en a le plus besoin. Le kill-switch est désormais consulté en premier, comme chez
ARET, et l'issue reste tracée (`ALLOW_WITH_NOTICE` porte sa raison, ce n'est jamais un laisser-passer
muet). Aucun test existant ne couvrait ce croisement ; c'est la comparaison qui l'a trouvé.

**Trois mutations sont d'abord revenues inertes, et chacune disait la même chose.** Un test qui
passe pour une autre raison que celle qu'il annonce. (1) L'isolation des couches de VERA réparait en
cascade : retirer la liaison de projet laissait la couche « profil » refuser à sa place — corrigé en
réparant toutes les autres couches et en laissant une seule étrangère. (2) La sentinelle symlinkée
pointait vers un fichier absent, donc `exists()` suffisait à la refuser : la mauvaise règle était
prouvée — corrigé en la faisant pointer vers un fichier bien réel. (3) La transplantation ARET
n'observait que la décision, or un état rejeté y laisse passer autant qu'un état accepté — corrigé
en observant l'état relu. C'est la même classe de défaut que `C09`, `C14` et `C06` avaient déjà
rencontrée : *une propriété satisfaite par plus d'un chemin n'en prouve aucun.*

Suite : `1090 passed, 312 subtests passed`. Quatorze couplages sur seize sont clos.

## LOG-0321 — Le run #60 tombe sur Windows, et l'échec devient la meilleure mesure du lot

**Statut : cause trouvée, mesurée et transformée en test. Suite `1091 + 312`.**

Le run #60 sur `6e48ce8` : Linux vert, **Windows rouge**, `2 failed, 1088 passed, 312 subtests` en
537 s. Les deux échecs sont les deux tests de `C15` qui exécutent les vrais hooks, et la cause n'est
aucune des trois causes Windows déjà connues, ni aucune des deux surfaces que j'avais nommées comme
suspectes (liens symboliques, variables d'environnement). Elle est dans ARET :

```
subprocess.TimeoutExpired: Command '['C:\Program Files\LLVM\bin\clang.EXE', '--version']'
timed out after 5 seconds
```

`toolchain_status` cherche neuf outils par `shutil.which`, puis lance `<outil> --version` avec
`timeout=5` et **sans aucune garde** — ni `try`, ni `except`, ni valeur de repli. Sur ce runner,
`clang --version` met plus de cinq secondes à répondre.

**Ce que ça coûte, mesuré en exécutant l'enveloppe `run()` d'ARET telle quelle**, avec un stub posé
à 6 secondes sur le `PATH` — la même panne, reproduite sur n'importe quelle plateforme :

* L'hôte ne reçoit **ni `result` ni `hookSpecificOutput`**. Le dossier de reprise, qui est toute la
  raison d'être du hook, n'est pas injecté du tout.
* L'erreur rendue est `INTERNAL_ERROR`, parce que `TimeoutExpired` n'est pas dans le tuple
  d'exceptions nommées de `run()`. Elle nomme une sonde `--version` expirée, pas une reprise perdue.
* L'état de barrière, lui, **survit** — `arm()` s'exécute plus tôt dans le handler que
  `toolchain_status`. C'est un ordre heureux, pas un repli conçu : rien dans le handler ne protège
  l'armement de ce qui le suit.

**Ma première assertion était fausse et le test me l'a dit.** J'avais écrit que la barrière ne
s'armait pas du tout ; le fichier d'état existait. `arm()` est à la ligne 27 du handler,
`toolchain_status` à la 46. La mesure a corrigé la lecture, ce qui est exactement l'ordre voulu.

**Côté VERA la question ne se pose pas**, et c'est vérifié plutôt qu'affirmé : la compilation du
dossier ne lance aucun processus, et `session_lifecycle.py` n'importe ni `subprocess` ni `shutil`.

**Les tests de hook posent désormais leurs propres stubs de toolchain.** Rien d'ARET n'est modifié :
c'est l'**environnement** que le hook interroge qui est posé, et c'est précisément ce qu'un hôte
fournit à un hook. Le `PATH` est préfixé et jamais remplacé, parce que `_repository_revision` appelle
`git` sans timeout ni garde et qu'un `git` introuvable ferait tomber le hook pour une seconde raison.
Le helper vérifie **son propre mécanisme** — `shutil.which("clang")` doit résoudre dans le répertoire
de stubs — plutôt que de le supposer : sous Windows la résolution passe par `PATHEXT`, et sans cette
vérification un échec de stub se lirait six lignes plus loin comme une cause obscure.

Trois mutations de plus, toutes mordantes : stub rendu rapide, `subprocess` réintroduit dans le Core,
et stubs placés en queue de `PATH` — cette dernière prouve que la vérification de mécanisme porte.
Vingt et une mutations vérifiées sur le lot.

**Une fausse piste, tracée pour ce qu'elle vaut.** Une exécution locale a rendu trois échecs sur ces
mêmes tests, et j'ai d'abord cru à une dépendance à l'ordre ou à `xdist`. C'était le harnais de
mutation : sa troisième mutation inverse exactement la ligne de `PATH`, et la signature de l'échec
— les trois seuls utilisateurs de `probed_toolchain`, ni plus ni moins — la désigne sans ambiguïté.
Le fichier restauré porte bien la forme préfixée, et dix exécutions consécutives sont vertes, dont
deux suites parallèles complètes. Ce n'est pas une certitude sur le mécanisme de la course, c'est
une conclusion appuyée sur la signature et sur l'état vérifié du fichier.

**Attesté au run #61 sur `2c6e6eb` : les deux runners verts**, `1091 passed, 312 subtests passed`
côté Core et `78 passed` côté interface, chiffres identiques des deux côtés, zéro échec et aucune
occurrence de `WinError`. Les **164 tests de parité** sont couverts, `C15` compris. Le correctif
tient donc sous Windows : les stubs `.bat` sont bien résolus par `shutil.which` à travers `PATHEXT`,
et exécutés par `CreateProcess` — c'était le seul point du lot que je ne pouvais pas vérifier ici.

**Une mesure que je ne m'explique pas, et qui est écrite comme telle.** L'étape de conformité
Windows passe de **420 s au #59 à 342 s au #61** alors qu'elle porte **23 tests de plus**, dont un
qui attend six secondes exprès. La variance de 12 % relevée plus haut ne couvre pas un écart de
18 %, et elle n'avait été mesurée que sur Linux. Les deux runs tournent sur des machines différentes
(`runner_id` 1000006361 puis 1000006365) : c'est une piste, pas une cause vérifiée. Le seul effet
que j'attribue au lot est que les six secondes du stub ne coûtent pas six secondes de mur, `xdist`
les absorbant dans un worker pendant que les autres avancent — ce qui explique l'absence de coût,
pas le gain.

Profil complet du #61 : conformité 118 s sur Linux et 342 s sur Windows, bundles 163 s et 152 s,
jobs complets **7 min 35** et **10 min 38**. Le parcours depuis le début de ce travail : Windows
21 min → 15 min 33 → 11 min 55 → **10 min 38**.

## LOG-0322 — `C07`/`C08` : le blocage était plus étroit qu'annoncé

**Statut : les deux lignes restent `IN_PROGRESS`, et c'est délibéré. 15 tests, 62 sous-tests,
9 mutations vérifiées mordantes. Suite `1106 + 374`.**

Le registre décrivait `C07` et `C08` comme bloqués sur Wine et MinGW. En vérifiant l'état réel du
conteneur plutôt qu'en reprenant cette ligne, trois faits sont apparus :

1. **Les neuf scripts d'oracle existent** — `bench/difftest.sh`, `winediff.sh`, `ehdiff.sh` et les
   autres —, mais dans `Automatic-reverse-engineering-toolkit`, pas dans `ARET-MMU`. Le clone
   d'`ARET-MMU` ne contient que `README.md` et `aret-memory/`.
2. **L'image de référence que `C08` exige existe déjà** : `docker/ci-toolchain/Dockerfile`, épinglée
   à `ubuntu:24.04`, avec ses raisons écrites (les constantes Wine mesurées viennent de cette
   distribution ; une version plus récente les déplacerait en silence).
3. **`docker` est présent** dans ce conteneur.

Mesuré ensuite sur le vrai dépôt toolkit : `cpudiff` et `funcdiff` n'ont **aucune dépendance
manquante** ici. Deux des neuf oracles sont satisfaits sur cette machine. C'est consigné comme
fait, pas exploité : le propriétaire a choisi le lot sans chaîne d'outils.

**Ce qui a été fait.** `oracles.py` et `evidence/capture.py` sont versionnés et épinglés, puis
**exécutés** — cinquième et sixième sources ARET traitées ainsi. Trois de leurs fonctions portent
l'essentiel et aucune ne lance de processus : `normalise_result` est une fonction **pure**,
`_repository_file` est de la résolution de chemin, `safe_fixture` est une expression régulière.

**Ce qu'ARET fait bien, mesuré avant tout le reste.** La précédence de normalisation est juste : une
dépendance manquante l'emporte sur un timeout, sur un échec et sur une sortie qui ressemble à un
succès — on ne rend pas de verdict sur une exécution qui n'a pas eu lieu. Un code de sortie non nul
reste un `FAIL` même avec une ligne `SKIP` dans la sortie. Un corpus vide n'est jamais un succès :
`0 / 0` rend `ERROR`, les regexes exigeant `> 0`. Le confinement tient sur les quatre évasions
posées, lien symbolique sortant compris. Et `winehash` rend `UNKNOWN` **même quand il réussit**,
parce que sa sortie est une mesure à comparer au runner Windows et non un gate — refuser de
transformer une mesure en verdict est exactement ce que `I004` demande.

**La divergence porte sur une seule question : d'où vient le verdict.** ARET le **dérive de la
prose** du script, par huit expressions régulières sur des lignes de résumé lisibles par un humain.
VERA le fait calculer par un validateur fermé, comme une comparaison d'empreintes, et son module de
validation n'importe même pas `subprocess`. La conséquence est mesurée : changer `functions` en
`function` — un caractère — transforme un `PASS` en `ERROR`. Le script n'a pas changé de
comportement, seulement de formulation.

**Deux écarts mineurs.** Le refus d'oracle inconnu ne nomme que quatre des neuf oracles : un message
devenu faux à mesure que le catalogue grandissait. Et un succès non reconnu retombe sur `ERROR`, pas
sur `UNKNOWN` — défendable, mais il fallait savoir lequel.

**Pourquoi rien n'est promu.** La preuve exigée de `C07` demande « evidence hashée, promotion
`PROVEN` et gate réelle » et celle de `C08` « exécutabilité mesurée dans une image de référence ».
Ces dimensions-là demandent d'exécuter un vrai oracle. Aucun test de ce lot ne les couvre, et aucune
ligne ne passe à `DONE` de ce fait. Le registre gagne des dimensions mesurées, pas une promotion.

**Une mutation est revenue inerte, et c'était encore la même classe de défaut.** Le refus de verdict
côté VERA était mesuré sur une `execution` inexistante : le refus venait de là, pas du verdict.
Corrigé en vérifiant le message, et en montrant que le même appel avec un verdict admis échoue plus
loin et pour une autre raison. *Une propriété satisfaite par plus d'un chemin n'en prouve aucun* —
quatrième lot où elle se présente.

**Attesté au run #62 sur `ca8a2f3` : les deux runners verts**, `1105 passed, 1 skipped, 365 subtests
passed` côté Core et `78 passed` côté interface, chiffres identiques des deux côtés, zéro échec et
aucune occurrence de `WinError`. Les **179 tests de parité** sont couverts.

**Le test sauté est attendu, et le vérifier valait mieux que le supposer.** Le check-in que j'avais
armé demandait de consigner `1106 + 374` ; ce chiffre aurait été faux.
`test_i013_a_missing_toolchain_yields_skipped_without_running_anything` interroge `required_tools`
contre le vrai dépôt `Automatic-reverse-engineering-toolkit`, qui n'est pas monté sur les runners
CI. Il porte un `skipTest` explicite pour ce cas et se saute proprement, emportant ses neuf
sous-tests — `374 − 9 = 365`, exactement les neuf oracles. Un test qui ne peut pas mesurer ce qu'il
annonce se saute **en le disant** ; il ne passe pas en silence.

**Une mesure de durée qui doit changer la façon de lire toutes les autres.** Côté Linux l'étape de
conformité tient entre 107 s et 120 s sur cinq runs. Côté Windows, à code de test quasi identique,
elle donne **409 s (#58), 420 s (#59), 342 s (#61) puis 643 s (#62)** — un rapport de **1,9 entre
les extrêmes**, avec un runner différent à chaque fois. Le `LOG-0319` parlait de 12 % de variance ;
c'était une mesure Linux, et elle ne vaut pas pour Windows. Aucune conclusion de durée ne doit être
tirée d'un seul run Windows, et les comparaisons Windows des entrées précédentes doivent se lire
avec cette réserve. Les quatre mesures sont consignées telles quelles, sans cause attribuée.

## LOG-0323 — Le chemin le moins cher n'existait pas, et l'enquête a trouvé mieux

**Statut : `C07`/`C08` restent `IN_PROGRESS`. 17 tests, 64 sous-tests, 11 mutations mordantes.
Suite `1108 + 376`.**

J'avais recommandé, mesures à l'appui, de construire `target/release/aret` avec `cargo` pour lancer
`cpudiff` et `funcdiff`, les deux oracles dont `required_tools` rend `[]`. **Cette recommandation
était fausse sur deux points, et il faut le dire avant le reste.**

*Premier point.* Ni `funcdiff` ni `cpudiff` n'a besoin de ce binaire : leur `requires_aret_binary`
vaut `False`. Construire `target/release/aret` ne les aurait pas rapprochés d'une exécution.

*Second point, et c'est lui qui ferme le chemin.* Les deux exigent `--features unpack`, c'est-à-dire
la **libunicorn système**, absente de cette machine. `funcdiff.sh` le découvre après avoir lancé
`cargo test --release --features unpack`, constate qu'aucune ligne `test result:` n'est sortie, et
imprime `SKIP (unpack build unavailable — is libunicorn installed?)` avant de sortir en 0. Le
verdict serait donc `SKIPPED`, au prix d'une compilation Rust complète qui ne peut pas se lier.

**Ce que l'enquête a trouvé à la place vaut mieux que ce qu'elle cherchait, et c'est exactement ce
que `C08` vise.**

*Le catalogue sous-déclare.* `funcdiff` déclare `('bash', 'cargo')`, `cpudiff` déclare `('cargo',)`.
Aucun des deux ne nomme libunicorn, que leurs scripts exigent pourtant. `required_tools` rend donc
`[]` — « rien ne manque, prêt à lancer » — pour deux oracles qui ne peuvent pas tourner ici. Un
catalogue de dépendances qui n'énumère pas ce dont le script a besoin n'est pas un préflight, c'est
une liste d'intentions. La chaîne ne ment pas sur le **résultat** : elle dégrade proprement en
`SKIPPED`. Elle ment sur la **disponibilité**, et seulement après avoir payé la compilation.

*Une sonde structurellement incapable de réussir.* `toolchain_status` cherche `unicorn` par
`shutil.which("libunicorn")` — une fonction qui parcourt le `PATH` à la recherche d'un
**exécutable**. Une bibliothèque partagée s'installe en `libunicorn.so.N` sous `/usr/lib`, jamais
sur le `PATH` et jamais exécutable. Cette sonde rend donc `available: False` sur une machine où la
bibliothèque est correctement installée comme sur une machine où elle manque : elle ne distingue
rien. C'est la cinquième règle morte trouvée par mutation dans cette série.

*Et les deux vues d'ARET se contredisent dans le même dépôt.* `toolchain_status` annonce `unicorn`
indisponible ; `required_tools` annonce `funcdiff` prêt. Le préflight qui garde l'exécution ne
consulte pas l'inventaire que le dossier de reprise publie à l'agent.

**Côté VERA, la surface n'existe pas.** Son `doctor` diagnostique le profil, le runtime, la base,
le magasin d'artefacts, la reprise, le transport MCP, le VCS, la non-pollution, les catalogues,
l'HMAC et les hooks — et **aucun outil externe**. Il ne prétend donc jamais qu'une chaîne d'outils
est prête. Son runner fermé refuse sur le **contrat** déclaré et la policy `ALLOW`, une assertion
qu'il peut tenir, plutôt que sur une présence devinée.

**Ce que cela change pour la suite.** L'exécution réelle d'un oracle demande `libunicorn` — pas
seulement Wine et MinGW comme le registre le disait, ni le binaire `aret` comme je l'avais dit.
C'est une dépendance de plus à fournir, et elle ne se contourne pas par une compilation.
