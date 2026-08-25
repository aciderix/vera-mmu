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
