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

> **État de reprise :** M1 est clos par son verdict `LOG-0009` et son commit atomique. Les gates techniques C01/C02/C11 passent ; la parité ARET demeure `UNKNOWN` et `MEM-WALL-001` est toujours ouvert. Aucun lot M2 n’est encore ouvert.

| Reprendre par | Lire ensuite | Ne pas faire avant |
|---|---|---|
| `UNIVERSALIZATION_WORKPLAN.md`, état actif puis lot M2 | `PROJECT_MEMORY.md`, sections 4–7 ; `LOG-0008` et `LOG-0009`. | Déclarer une parité ARET, créer un alias `ARET://`, démarrer M2 sans rituel distinct ou lever `MEM-WALL-001` par hypothèse. |

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
