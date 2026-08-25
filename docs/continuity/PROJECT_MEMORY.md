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

## 5. Décisions actives

| ID | Décision | Statut | Motif | Effet opérationnel | Journal |
|---|---|---|---|---|---|
| `MEM-DEC-001` | Créer VERA-MMU dans un dépôt indépendant sans modifier ARET-MMU. | `DECISION` | Préserver le dépôt de référence et rendre les frontières mesurables. | Toute réutilisation future passe par migration, import explicite ou pack ; aucune copie non tracée. | `LOG-0002` |
| `MEM-DEC-002` | Utiliser `vera://` comme schéma de ressource canonique et conserver `ARET://` seulement en lecture de compatibilité ultérieure. | `DECISION` | Différencier le nouveau Core tout en préservant une voie de migration contrôlée. | Tests de round-trip et lecteur V1 requis avant tout claim de compatibilité. | `LOG-0002` |
| `MEM-DEC-003` | Utiliser ces trois documents comme système de continuité de transition. | `DECISION` | Le store universel n’existe pas encore, mais le chantier exige mémoire, provenance et reprise dès maintenant. | Chaque lot met à jour plan, mémoire et journal avant son commit atomique. | `LOG-0003` |
| `MEM-DEC-004` | Commencer par `M0.1 — Freeze ARET` plutôt que par une extraction de code. | `DECISION` | Toute parité future requiert un baseline mesuré de schéma, tests, hooks, MCP, bundle et dépendances. | Aucun déplacement de primitive ARET avant l’inventaire de compatibilité. | `LOG-0003` |
| `MEM-DEC-005` | Démarrer M1 par les couplages C01, C02 et C11 : adressage VERA, Project Profile/runtime configurable et workspace sûr. | `DECISION` | Ces primitives rendent possible la persistance, les packs et la compilation ultérieurs sans introduire de dépendance ARET dans le Core. | Le premier patch M1 ne doit importer aucun module ARET ni connaître `ARET://`, `.aret-memory`, binaire ou toolchain ARET. | `LOG-0007` |
| `MEM-DEC-006` | Le catalogue initial d’adresses est strictement générique et fermé ; aucune forme d’adresse historique n’est interprétée par le Core. | `DECISION` | Préserver I014/I015 et éviter un renommage cosmétique ou une compatibilité implicite. | `parse_address` accepte exclusivement les URI canoniques `vera://<project>/<resource>/<id>` ; un lecteur historique éventuel est hors M1. | `LOG-0009` |

## 6. Risques, incertitudes et blocages

| ID | Risque ou inconnue | Statut | Impact | Réponse requise | Journal |
|---|---|---|---|---|---|
| `MEM-RISK-001` | Les assertions de parité ARET ne disposent pas encore d’un baseline reproductible complet dans VERA-MMU. | `RISK` | Une migration pourrait sembler fonctionnelle sans être démontrée équivalente. | Exécuter `M0.1`, capturer résultats, versions, schéma, hooks, bundle et écarts d’environnement. | `LOG-0003` |
| `MEM-RISK-002` | La spécification cible utilise historiquement `mmu://`, `.mmu/` et `mmu_*`, tandis que VERA-MMU a choisi `vera://`, `.vera-mmu/` et `vera_*`. | `DECISION` avec risque de compatibilité | Les documents et adaptations doivent déclarer les deux couches sans mélange silencieux. | Définir une table de compatibilité et une policy d’alias dans `M1`. | `LOG-0003` |
| `MEM-RISK-003` | Le statut de licence est `LICENSE-PENDING`. | `RISK` | Une extraction ou distribution de code ARET nécessite une décision explicite de gouvernance. | Ne pas copier de code ARET ; documenter provenance, droits et transformation avant tout import. | `LOG-0002` |
| `MEM-RISK-004` | Les règles de preuve sont documentées, mais le mécanisme de capture admissible VERA-MMU n’est pas encore implémenté. | `RISK` | Les preuves actuelles de chantier sont des traces de développement, pas des evidence VERA-MMU admissibles. | Qualifier les résultats `OBSERVED` jusqu’à l’existence du store/evidence engine. | `LOG-0003` |
| `MEM-WALL-001` | Toolchain ARET de baseline incomplète | La suite complète produit 82 passes, 1 échec et 7 skips ; `gcc`, Cargo, Wine, MinGW, Clang, LLD et LLVM DLLTool sont absents, ainsi que le binaire et le script réels de difftest. | `BLOCKED` | `ARET_MMU_M0_1_BASELINE/tests/pytest_full.txt` ; `toolchain/oracle_toolchain_availability.txt`. | Ne pas modifier ARET-MMU ni qualifier les oracles comme validés ; reproduire ultérieurement dans un environnement déclarant cette toolchain. | `LOG-0006` |

## 7. Reprise active

**État de reprise :** `M1 — Core d’identité` est techniquement terminé ; son commit atomique versionne ce verdict. Aucun lot M2 n’est ouvert et `MEM-WALL-001` demeure une précondition ouverte pour les futures assertions d’oracle et de capability ARET.

| Élément | Valeur de reprise |
|---|---|
| État vérifié | C01/C02/C11 disposent de primitives génériques testées : URI VERA canonique, profile/identités hashés, roots contrôlées, no-Git, multi-repo, détection VCS sans appel Git et runtime confiné. |
| Evidence M1 | `PYTHONPATH=src python3 -m pytest -q` : 21 passés, 14 sous-tests ; build/install wheel et `vmmu inspect` réussis ; `git diff --check` et scan anti-ARET réussis. Hash wheel : `92078ad9018f0a26d5b6999fcfe25f32dd6ca1699b6b49c501b7bc12c8f13e1e`. |
| Limites explicites | Pas de store, migration, evidence, policy, capability, bundle, adapter MCP, dashboard, pack ARET ni compatibilité de lecteur historique. L’absence de vocabulaire ARET du Core ne démontre pas de parité comportementale ARET. |
| Entrées à relire | [Plan](UNIVERSALIZATION_WORKPLAN.md), cette mémoire, [journal](ENGINEERING_LOG.md), [invariants](../INVARIANTS.md), [matrice](../DECOUPLING_MATRIX.md), puis `LOG-0008` et `LOG-0009`. |
| Prochaine action | Vérifier le commit atomique M1 ; seulement ensuite, si le chantier reprend, effectuer le rituel complet d’un lot M2 séparé sans lever `MEM-WALL-001`. |

## 8. Protocole de mise à jour append-only

1. Créer une nouvelle entrée avec un identifiant monotone `MEM-…` ; ne pas modifier un record historique sauf correction de forme ne changeant pas le sens.
2. En cas de correction sémantique, ajouter `SUPERSEDES: MEM-…`, citer la source nouvelle et expliquer le motif.
3. Associer chaque record à un ou plusieurs identifiants `LOG-…` du journal.
4. N’utiliser `PROVEN` que lorsqu’une evidence admissible du futur moteur existe ; dans la phase documentaire, préférer `OBSERVED`, `DECISION` ou `HYPOTHESIS`.
5. Mettre à jour la section **Reprise active** à la fin de chaque lot ou avant compaction.

## Références

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — dépôt de référence"
