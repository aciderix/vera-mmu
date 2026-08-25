# Mémoire factuelle du chantier VERA-MMU

> **Statut :** registre canonique de continuité documentaire.
>
> **Règle :** ce document conserve des faits, des décisions, des risques et des références ; la chronologie détaillée est tenue dans le [journal d’ingénierie](ENGINEERING_LOG.md).
>
> **Mise à jour :** append-only ; une correction ajoute un nouveau record qui supersède explicitement le précédent.

## 1. Contrat de la mémoire

Cette mémoire sert à reprendre le chantier sans dépendre d’un contexte conversationnel. Elle ne remplace pas le futur store SQLite de VERA-MMU ; elle est le registre de transition versionné tant que le Core universel ne possède pas encore les primitives de knowledge, evidence, audit et resume complètes.

| Règle | Application documentaire |
|---|---|
| **Fait ≠ hypothèse** | Chaque entrée est classée `PROVEN`, `OBSERVED`, `INFERRED`, `HYPOTHESIS`, `DECISION`, `RISK`, `BLOCKED` ou `SUPERSEDED`. |
| **Recherche ≠ lecture** | Le journal peut indexer ou résumer ; cette mémoire renvoie toujours à une source, un commit, une section ou un identifiant de journal. |
| **Append-only** | Une correction n’écrase pas l’ancien record : elle crée un record `SUPERSEDES: MEM-…`. |
| **Fail loud** | Une absence de preuve, une référence cassée ou une contradiction devient un record `RISK` ou `BLOCKED`, jamais une réussite implicite. |
| **Reprise contrôlée** | Avant modification, relire les sections 2, 5, 6 et 7, puis les entrées de journal citées. |

## 2. Identité, sources et baseline

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-ID-001` | Identité | Le produit s’appelle **VERA-MMU**, pour *Verifiable Epistemics & Relational Architecture*. Les conventions sont `vera-mmu`, `vera_mmu`, `vmmu`, `.vera-mmu/` et `vera://<project>/<resource>/<id>`. | `PROVEN` | [Identité officielle](../IDENTITY.md) | `LOG-0002` |
| `MEM-BASE-001` | Baseline ARET | Le clone local de référence ARET-MMU est à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, branche `main`, arbre propre au relevé du 25 août 2026. | `OBSERVED` | Commande Git enregistrée ; dépôt [ARET-MMU][1] | `LOG-0001` |
| `MEM-BASE-002` | Baseline VERA | VERA-MMU est à `ef707339c245ee1d36b8a78312d1a441c86296dc`, branche `main`, arbre propre au relevé du 25 août 2026. | `OBSERVED` | `git rev-parse HEAD` et `git status --short` | `LOG-0002` |
| `MEM-SRC-001` | Source | La spécification fournie définit la cible : Core universel, Domain Packs, Project Profiles, Capability/Gate Engine, MCP Compiler, Runtime Adapters et Dashboard. | `OBSERVED` | `UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md`, sections 0–1 et 60, fourni par le propriétaire. | `LOG-0003` |
| `MEM-SRC-002` | Source | La doctrine ARET impose le cycle baseline → patch minimal → run → evidence → comparison → verdict → record, la non-régression et le fail loud. | `OBSERVED` | `pasted_content.txt`, sections 1–20, fourni par le propriétaire. | `LOG-0003` |
| `MEM-BASE-003` | Freeze M0.1 | Le baseline ARET a capturé l’inventaire, les hashes, l’environnement, les résultats pytest, la surface MCP/hook, un bundle de mécanique et un bundle Git pour le commit de référence. | `OBSERVED` | `/home/ubuntu/ARET_MMU_M0_1_BASELINE/BASELINE_REPORT.md` ; manifeste `05e9c126425a27d6440cb5e92c367bcae6676ff04b430fe4b3618c7afff7984d`. | `LOG-0006` |
| `MEM-BASE-004` | Mesures de référence | Le package compte 180 fichiers, 25 fichiers de tests, 90 tests collectés, 6 migrations SQL, 44 outils MCP `aret_*` détectés statiquement et 11 modules de hooks. | `OBSERVED` | Répertoire `ARET_MMU_M0_1_BASELINE/inventory/` et `hashes/`. | `LOG-0006` |
| `MEM-COMP-001` | Registre M0.2 | Seize couplages ARET ont une source, une frontière Core/pack, une stratégie de migration et un test de parité nommés : 14 sont `SPLIT` et 2 (`C07`, `C08`) restent `BLOCKED` par `MEM-WALL-001`. | `OBSERVED` | [Matrice de découplage](../DECOUPLING_MATRIX.md), sections 1–3. | `LOG-0007` |

## 3. Faits d’architecture établis

| ID | Sujet | Fait ou décision | Statut | Source primaire | Journal |
|---|---|---|---|---|---|
| `MEM-ARCH-001` | Frontière | Le Core doit rester installable sans vocabulaire, corpus, binaire, outil, script ou doctrine ARET obligatoire. | `PROVEN` | [Invariants I015](../INVARIANTS.md) ; [matrice](../DECOUPLING_MATRIX.md) | `LOG-0002`, `LOG-0003` |
| `MEM-ARCH-002` | Épistémologie | La mémoire canonique est externe au modèle ; une assertion de modèle, un FIND, un test non authentifié ou une sortie shell brute ne sont pas des preuves suffisantes. | `PROVEN` | Invariants I001, I002, I004 et I006. | `LOG-0002` |
| `MEM-ARCH-003` | Evidence | Une promotion `PROVEN` nécessite une evidence admissible `PASS`, reliée à une exécution et à son environnement. | `PROVEN` | Invariants I004, I006 et spécification, sections 14–15. | `LOG-0003` |
| `MEM-ARCH-004` | Sécurité | Le client ne pourra sélectionner que des capabilities déclarées et lui fournir des paramètres bornés ; aucune entrée ne construira une commande arbitraire. | `PROVEN` | Invariants I007–I008 ; spécification, sections 12–13. | `LOG-0003` |
| `MEM-ARCH-005` | Reprise | La reprise doit être liée à un contrat hashé ; une mémoire importée dans un autre projet doit être rejetée. | `PROVEN` | Invariants I009–I011 ; spécification, sections 17 et 19. | `LOG-0003` |
| `MEM-ARCH-006` | Portabilité | Le futur générateur doit être déterministe : mêmes profile, packs et version de générateur impliquent même sortie canonique et `mcp_build_hash`. | `PROVEN` | Invariant I012 ; spécification, section 25. | `LOG-0003` |

## 4. État actuel vérifié et limites explicites

| ID | Élément | État | Statut | Limite ou condition |
|---|---|---|---|---|
| `MEM-STATE-001` | Package | Le package `vera_mmu` possède une identité de Project Profile déterministe et une CLI `vmmu identity`. | `OBSERVED` | La fondation est intentionnellement minimale ; la production MCP n’existe pas encore. |
| `MEM-STATE-002` | Gouvernance initiale | Les invariants, l’architecture, la matrice de découplage, l’identité et l’audit de nommage existent dans VERA-MMU. | `OBSERVED` | Ces documents doivent être maintenus avec les trois documents de continuité. |
| `MEM-STATE-003` | Persistence universelle | Les migrations SQL universelles, le store générique, les entités, relations, work items, executions, gates et bundles V2 ne sont pas encore implémentés. | `OBSERVED` | Aucun statut d’avancement ne peut les présenter comme partiellement « faits » sans preuves dédiées. |
| `MEM-STATE-004` | Compatibilité ARET | Il n’existe pas encore de pack ARET, d’importeur hors ligne, de lecteur `ARET://` ni de suite de parité dans VERA-MMU. | `OBSERVED` | La compatibilité est une cible critique, non une capacité actuelle. |
| `MEM-STATE-005` | Exécution et UI | Capability Engine, Gate Engine, compilateur MCP, adapters de runtime, CLI complète et Dashboard restent à construire. | `OBSERVED` | Ils doivent être introduits par lots séparés, testés et policy-gated. |
| `MEM-STATE-006` | Core M1 | Le Core contient un Project Profile canonique, `ProjectIdentity` avec fingerprint de topologie, adressage strict `vera://`, résolution mono/multi/no-Git et `RuntimeLocator` confiné. | `OBSERVED` | 21 tests et 14 sous-tests passent ; le Core n’ouvre encore aucun store, gate, evidence, bundle, MCP adapter ou pack. | `LOG-0009` |
| `MEM-STATE-007` | Substrate M2.1 | `SUPERSEDES: MEM-STATE-003` pour le sous-ensemble migrations/store. Le Core dispose d’un store SQLite lié au profile, d’un ledger checksumé, de métadonnées de format, d’audit technique et d’une transaction explicite. | `OBSERVED` | 31 tests et 14 sous-tests passent ; knowledge, entities, relations, evidence, bundles et services métier restent absents. | `LOG-0011` |
| `MEM-STATE-008` | Entity Registry M2.2 | `SUPERSEDES: MEM-STATE-003` pour le sous-ensemble types/entités. Le Core enregistre des types génériques puis crée/lit exactement des entités JSON canoniques avec audit atomique. | `OBSERVED` | 40 tests et 14 sous-tests passent ; relations, symboles, knowledge, evidence, bundles et services métier associés restent absents. | `LOG-0013` |
| `MEM-STATE-009` | Relation Registry M2.3 | `SUPERSEDES: MEM-STATE-003` pour le sous-ensemble relations. Le Core enregistre des types relationnels puis crée/lit exactement des arêtes immuables entre entités, avec contraintes source/cible et audit atomique. | `OBSERVED` | 48 tests et 14 sous-tests passent ; traversal, lifecycle, symboles, knowledge, evidence, bundles et services métier associés restent absents. | `LOG-0015` |
| `MEM-STATE-010` | Knowledge Registry M2.4 | `SUPERSEDES: MEM-STATE-003` pour le sous-ensemble knowledge. Le Core enregistre des types knowledge puis ajoute/lit exactement des assertions append-only hashées avec statuts initiaux sûrs et audit atomique. | `OBSERVED` | 57 tests et 14 sous-tests passent ; `PROVEN`, evidence, FTS/FIND, tags, sources, supersession, bundles et services métier associés restent absents. | `LOG-0017` |
| `MEM-STATE-011` | Knowledge Source Registry M2.5 | `SUPERSEDES: MEM-STATE-010` pour le sous-ensemble provenance déclarative. Le Core attache/lit des références documentaires immuables, hashées et bornées par lignes à une knowledge existante, sans ouvrir le document référencé. | `OBSERVED` | 65 tests et 14 sous-tests passent ; fetch, vérification de document, import, evidence, `PROVEN`, recherche, supersession et bundles restent absents. | `LOG-0019` |

## 5. Décisions actives

| ID | Décision | Statut | Motif | Effet opérationnel | Journal |
|---|---|---|---|---|---|
| `MEM-DEC-001` | Créer VERA-MMU dans un dépôt indépendant sans modifier ARET-MMU. | `DECISION` | Préserver le dépôt de référence et rendre les frontières mesurables. | Toute réutilisation future passe par migration, import explicite ou pack ; aucune copie non tracée. | `LOG-0002` |
| `MEM-DEC-002` | Utiliser `vera://` comme schéma de ressource canonique et conserver `ARET://` seulement en lecture de compatibilité ultérieure. | `DECISION` | Différencier le nouveau Core tout en préservant une voie de migration contrôlée. | Tests de round-trip et lecteur V1 requis avant tout claim de compatibilité. | `LOG-0002` |
| `MEM-DEC-003` | Utiliser ces trois documents comme système de continuité de transition. | `DECISION` | Le store universel n’existe pas encore, mais le chantier exige mémoire, provenance et reprise dès maintenant. | Chaque lot met à jour plan, mémoire et journal avant son commit atomique. | `LOG-0003` |
| `MEM-DEC-004` | Commencer par `M0.1 — Freeze ARET` plutôt que par une extraction de code. | `DECISION` | Toute parité future requiert un baseline mesuré de schéma, tests, hooks, MCP, bundle et dépendances. | Aucun déplacement de primitive ARET avant l’inventaire de compatibilité. | `LOG-0003` |
| `MEM-DEC-005` | Démarrer M1 par les couplages C01, C02 et C11 : adressage VERA, Project Profile/runtime configurable et workspace sûr. | `DECISION` | Ces primitives rendent possible la persistance, les packs et la compilation ultérieurs sans introduire de dépendance ARET dans le Core. | Le premier patch M1 ne doit importer aucun module ARET ni connaître `ARET://`, `.aret-memory`, binaire ou toolchain ARET. | `LOG-0007` |
| `MEM-DEC-006` | Le catalogue initial d’adresses est strictement générique et fermé ; aucune forme d’adresse historique n’est interprétée par le Core. | `DECISION` | Préserver I014/I015 et éviter un renommage cosmétique ou une compatibilité implicite. | `parse_address` accepte exclusivement les URI canoniques `vera://<project>/<resource>/<id>` ; un lecteur historique éventuel est hors M1. | `LOG-0009` |
| `MEM-DEC-007` | Commencer M2 par un substrate SQLite sans objets métier : migrations checksumées, identité de store, audit technique et transactions bornées. | `DECISION` | Établir I001/I010/I011/I014 avant les connaissances, entités, evidence ou bundles. | M2.1 exclut toute taxonomie, migration de données ARET, commande, capability, MCP, pack et compatibilité historique. | `LOG-0010` |
| `MEM-DEC-008` | M2.2 introduit uniquement un registre de types d’entité et des entités génériques créées/lues de façon exacte et auditée. | `DECISION` | Commencer C03 sans emprunter les tables `component`/`function_symbol` ni ouvrir C04/C05/C16 au-delà du nécessaire. | Les entités exigent un type enregistré ; l’API exclut FIND, relations, symboles, knowledge, evidence et toute compatibilité ARET. | `LOG-0012` |
| `MEM-DEC-009` | M2.3 introduit uniquement un registre de types de relation et des arêtes immuables entre entités existantes. | `DECISION` | Établir une relation universelle et typée sans ouvrir le traversal, la supersession, le graphe de travail ou la connaissance. | Les types de relation sont déclaratifs et contraignent les types d’entité ; l’API exclut FIND, lifecycle, relation vers d’autres ressources, knowledge, evidence et toute compatibilité ARET. | `LOG-0014` |
| `MEM-DEC-010` | M2.4 introduit uniquement un registre knowledge append-only avec types déclaratifs, hash de contenu et statuts épistémiques initiaux sûrs. | `DECISION` | Établir I003 et empêcher une promotion sans evidence avant de créer le moteur d’Evidence. | `PROVEN`, supersession, FTS/FIND, tags, sources, relations et toute mutation sont exclus ; les écritures sont append-only, auditables et liées au profile. | `LOG-0016` |
| `MEM-DEC-011` | M2.5 introduit uniquement des références documentaires immuables, hashées et bornées par lignes, attachées à une knowledge existante. | `DECISION` | Établir la provenance déclarative sans créer de fetch, importeur, preuve ou admission `PROVEN`. | Les sources sont validées comme données de référence ; l’API exclut lecture de fichier, vérification de contenu, import, migration batch, evidence et toute mutation/suppression. | `LOG-0018` |

## 6. Risques, incertitudes et blocages

| ID | Risque ou inconnue | Statut | Impact | Réponse requise | Journal |
|---|---|---|---|---|---|
| `MEM-RISK-001` | Les assertions de parité ARET ne disposent pas encore d’un baseline reproductible complet dans VERA-MMU. | `RISK` | Une migration pourrait sembler fonctionnelle sans être démontrée équivalente. | Exécuter `M0.1`, capturer résultats, versions, schéma, hooks, bundle et écarts d’environnement. | `LOG-0003` |
| `MEM-RISK-002` | La spécification cible utilise historiquement `mmu://`, `.mmu/` et `mmu_*`, tandis que VERA-MMU a choisi `vera://`, `.vera-mmu/` et `vera_*`. | `DECISION` avec risque de compatibilité | Les documents et adaptations doivent déclarer les deux couches sans mélange silencieux. | Définir une table de compatibilité et une policy d’alias dans `M1`. | `LOG-0003` |
| `MEM-RISK-003` | Le statut de licence est `LICENSE-PENDING`. | `RISK` | Une extraction ou distribution de code ARET nécessite une décision explicite de gouvernance. | Ne pas copier de code ARET ; documenter provenance, droits et transformation avant tout import. | `LOG-0002` |
| `MEM-RISK-004` | Les règles de preuve sont documentées, mais le mécanisme de capture admissible VERA-MMU n’est pas encore implémenté. | `RISK` | Les preuves actuelles de chantier sont des traces de développement, pas des evidence VERA-MMU admissibles. | Qualifier les résultats `OBSERVED` jusqu’à l’existence du store/evidence engine. | `LOG-0003` |
| `MEM-WALL-001` | Toolchain ARET de baseline incomplète | La suite complète produit 82 passes, 1 échec et 7 skips ; `gcc`, Cargo, Wine, MinGW, Clang, LLD et LLVM DLLTool sont absents, ainsi que le binaire et le script réels de difftest. | `BLOCKED` | `ARET_MMU_M0_1_BASELINE/tests/pytest_full.txt` ; `toolchain/oracle_toolchain_availability.txt`. | Ne pas modifier ARET-MMU ni qualifier les oracles comme validés ; reproduire ultérieurement dans un environnement déclarant cette toolchain. | `LOG-0006` |

## 7. Reprise active

**État de reprise :** `M2.5 — Knowledge Source Registry` est techniquement terminé ; son commit atomique versionne le verdict `LOG-0019`. Aucun sous-lot M2.6 n’est ouvert. `MEM-WALL-001` demeure une précondition ouverte pour les futures assertions d’oracle et de capability ARET.

| Élément | Valeur de reprise |
|---|---|
| État vérifié | C01/C02/C11 disposent de primitives génériques testées : URI VERA canonique, profile/identités hashés, roots contrôlées, no-Git, multi-repo, détection VCS sans appel Git et runtime confiné. M1 est publié au commit `c48efc4ec824a9ec5b1a3742f7022636e9ef082b`. |
| Evidence M1 | `PYTHONPATH=src python3 -m pytest -q` : 21 passés, 14 sous-tests ; build/install wheel et `vmmu inspect` réussis ; `git diff --check` et scan anti-ARET réussis. Hash wheel : `92078ad9018f0a26d5b6999fcfe25f32dd6ca1699b6b49c501b7bc12c8f13e1e`. |
| Baseline M2.1 | Store SQLite canonique, migration checksumée, métadonnées, identité de store, audit technique et transaction, publié au commit `3fc41eff3fb525bab82338287ddde33b3dce9358`. |
| Baseline M2.2 | Registre de types d’entité, entités génériques, JSON canonique, lecture exacte, audit de création et migration M2.1→M2.2, publié au commit `8f367ca5fdf906f48a58e739360af97d1649c40a`. |
| Baseline M2.3 | Registre de types de relation, arêtes immuables entre entités, contraintes déclaratives source/cible, lecture exacte, audit de création et migration M2.2→M2.3, publié au commit `5e68a9694137dd1e49f6a8b4a1700c7ca2e40764`. |
| Baseline M2.4 | Registre knowledge, assertions append-only hashées, statuts initiaux sûrs, lecture exacte, audit de création et migration M2.3→M2.4, publié au commit `a783d3efefafe0b1e80c5454e8649f082858611e`. |
| Périmètre M2.5 | Références documentaires à une knowledge existante : repository, revision, chemin relatif, section, lignes, SHA-256, lecture exacte bornée, audit de création et migration M2.4→M2.5. Aucun fetch, import, evidence, `PROVEN`, FTS/FIND ou mutation n’est autorisé. |
| Limites explicites | Pas encore de fetch/vérification de document, import/migration batch, promotion `PROVEN`, evidence, traversal/lifecycle relationnel, symbole, FTS/FIND, policy, capability, bundle, adapter MCP, dashboard, pack ARET ni compatibilité de lecteur historique. L’absence de vocabulaire ARET du Core ne démontre pas de parité comportementale ARET. |
| Entrées à relire | [Plan](UNIVERSALIZATION_WORKPLAN.md), cette mémoire, [journal](ENGINEERING_LOG.md), [invariants](../INVARIANTS.md), [matrice](../DECOUPLING_MATRIX.md), puis `LOG-0017`, `LOG-0018` et `LOG-0019`. |
| Prochaine action | Vérifier le commit atomique M2.5 ; si le chantier reprend, ouvrir un sous-lot M2.6 distinct avec hypothèse et limites propres, sans lever `MEM-WALL-001`. |

## 8. Protocole de mise à jour append-only

1. Créer une nouvelle entrée avec un identifiant monotone `MEM-…` ; ne pas modifier un record historique sauf correction de forme ne changeant pas le sens.
2. En cas de correction sémantique, ajouter `SUPERSEDES: MEM-…`, citer la source nouvelle et expliquer le motif.
3. Associer chaque record à un ou plusieurs identifiants `LOG-…` du journal.
4. N’utiliser `PROVEN` que lorsqu’une evidence admissible du futur moteur existe ; dans la phase documentaire, préférer `OBSERVED`, `DECISION` ou `HYPOTHESIS`.
5. Mettre à jour la section **Reprise active** à la fin de chaque lot ou avant compaction.

## Références

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — dépôt de référence"
