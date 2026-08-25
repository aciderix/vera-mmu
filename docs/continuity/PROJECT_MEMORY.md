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

## 5. Décisions actives

| ID | Décision | Statut | Motif | Effet opérationnel | Journal |
|---|---|---|---|---|---|
| `MEM-DEC-001` | Créer VERA-MMU dans un dépôt indépendant sans modifier ARET-MMU. | `DECISION` | Préserver le dépôt de référence et rendre les frontières mesurables. | Toute réutilisation future passe par migration, import explicite ou pack ; aucune copie non tracée. | `LOG-0002` |
| `MEM-DEC-002` | Utiliser `vera://` comme schéma de ressource canonique et conserver `ARET://` seulement en lecture de compatibilité ultérieure. | `DECISION` | Différencier le nouveau Core tout en préservant une voie de migration contrôlée. | Tests de round-trip et lecteur V1 requis avant tout claim de compatibilité. | `LOG-0002` |
| `MEM-DEC-003` | Utiliser ces trois documents comme système de continuité de transition. | `DECISION` | Le store universel n’existe pas encore, mais le chantier exige mémoire, provenance et reprise dès maintenant. | Chaque lot met à jour plan, mémoire et journal avant son commit atomique. | `LOG-0003` |
| `MEM-DEC-004` | Commencer par `M0.1 — Freeze ARET` plutôt que par une extraction de code. | `DECISION` | Toute parité future requiert un baseline mesuré de schéma, tests, hooks, MCP, bundle et dépendances. | Aucun déplacement de primitive ARET avant l’inventaire de compatibilité. | `LOG-0003` |

## 6. Risques, incertitudes et blocages

| ID | Risque ou inconnue | Statut | Impact | Réponse requise | Journal |
|---|---|---|---|---|---|
| `MEM-RISK-001` | Les assertions de parité ARET ne disposent pas encore d’un baseline reproductible complet dans VERA-MMU. | `RISK` | Une migration pourrait sembler fonctionnelle sans être démontrée équivalente. | Exécuter `M0.1`, capturer résultats, versions, schéma, hooks, bundle et écarts d’environnement. | `LOG-0003` |
| `MEM-RISK-002` | La spécification cible utilise historiquement `mmu://`, `.mmu/` et `mmu_*`, tandis que VERA-MMU a choisi `vera://`, `.vera-mmu/` et `vera_*`. | `DECISION` avec risque de compatibilité | Les documents et adaptations doivent déclarer les deux couches sans mélange silencieux. | Définir une table de compatibilité et une policy d’alias dans `M1`. | `LOG-0003` |
| `MEM-RISK-003` | Le statut de licence est `LICENSE-PENDING`. | `RISK` | Une extraction ou distribution de code ARET nécessite une décision explicite de gouvernance. | Ne pas copier de code ARET ; documenter provenance, droits et transformation avant tout import. | `LOG-0002` |
| `MEM-RISK-004` | Les règles de preuve sont documentées, mais le mécanisme de capture admissible VERA-MMU n’est pas encore implémenté. | `RISK` | Les preuves actuelles de chantier sont des traces de développement, pas des evidence VERA-MMU admissibles. | Qualifier les résultats `OBSERVED` jusqu’à l’existence du store/evidence engine. | `LOG-0003` |

## 7. Reprise active

**Work item actif :** `M0.1 — Freeze ARET et inventaire de compatibilité`.

| Élément | Valeur de reprise |
|---|---|
| Objectif immédiat | Obtenir un baseline ARET complet, reproductible et relié à `MEM-BASE-001`, sans modifier ARET-MMU. |
| Entrées à relire | [Plan](UNIVERSALIZATION_WORKPLAN.md), cette mémoire, [journal](ENGINEERING_LOG.md), [invariants](../INVARIANTS.md), [matrice](../DECOUPLING_MATRIX.md). |
| Préconditions | Clone ARET propre, commit identifié, environnement de test documenté, répertoire d’évidence de baseline séparé de tout dépôt source. |
| Sorties attendues | Inventaire de fichiers et dépendances, résultats de tests qualifiés, schéma/migrations hashés, surface MCP/hooks décrite, bundle d’exemple si la précondition d’environnement est satisfaite. |
| Gates de travail | Aucun `PASS` sans commande, sortie, environnement et comparaison enregistrés ; tout échec environnemental devient une wall qualifiée. |
| Prochaine action | Ouvrir `LOG-0005`, définir le périmètre exact du freeze et capturer les versions/outils avant toute exécution. |

## 8. Protocole de mise à jour append-only

1. Créer une nouvelle entrée avec un identifiant monotone `MEM-…` ; ne pas modifier un record historique sauf correction de forme ne changeant pas le sens.
2. En cas de correction sémantique, ajouter `SUPERSEDES: MEM-…`, citer la source nouvelle et expliquer le motif.
3. Associer chaque record à un ou plusieurs identifiants `LOG-…` du journal.
4. N’utiliser `PROVEN` que lorsqu’une evidence admissible du futur moteur existe ; dans la phase documentaire, préférer `OBSERVED`, `DECISION` ou `HYPOTHESIS`.
5. Mettre à jour la section **Reprise active** à la fin de chaque lot ou avant compaction.

## Références

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — dépôt de référence"
