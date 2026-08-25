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

