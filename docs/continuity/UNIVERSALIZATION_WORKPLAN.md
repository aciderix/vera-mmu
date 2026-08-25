# Plan vivant d’universalisation de VERA-MMU

> **Statut :** actif — document de contrôle évolutif.
>
> **Dernière revue factuelle :** 25 août 2026.
>
> **Sources de vérité complémentaires :** [mémoire factuelle](PROJECT_MEMORY.md) et [journal d’ingénierie](ENGINEERING_LOG.md).

## 1. Objet et règle de gouvernance

Ce document pilote la transformation de la fondation **VERA-MMU** en un moteur universel de mémoire, provenance, preuve, reprise et gouvernance. Il ne remplace ni les invariants, ni la matrice de découplage, ni les sources de référence. Il établit l’ordre des travaux, les conditions d’entrée et de sortie de chaque lot, ainsi que la manière obligatoire de consigner les preuves.

> **Règle suprême :** ne jamais croire le résultat ; mesurer, comparer, prouver, enregistrer — et ne déclarer gagné que ce qui a passé les gates sans régression.

Aucune ligne ne passe à `DONE` sur la base d’une intention, d’une compilation, d’une sortie déclarative ou d’un test superficiel. La séquence normative est : **hypothèse → changement minimal → exécution réelle → preuve admissible → comparaison au baseline → verdict → enregistrement**.[1] [2]

## 2. Hiérarchie des sources et frontières

| Rang | Source | Rôle normatif | Usage obligatoire |
|---|---|---|---|
| 1 | [Invariants VERA-MMU](../INVARIANTS.md) | Propriétés non régressives du Core. | Toute modification cite les invariants affectés et leurs tests. |
| 2 | [Matrice de découplage](../DECOUPLING_MATRIX.md) | Registre des dépendances ARET à extraire ou isoler. | Toute extraction ou migration met à jour la ligne correspondante. |
| 3 | Spécification Universal Dev-MMU fournie | Architecture cible, périmètre, migration, conformance et Definition of Done. | Toute décision de conception indique la section source pertinente. |
| 4 | Doctrine ARET fournie | Discipline d’ingénierie : preuve, baseline, fail loud, non-régression et reprise. | Tout lot suit le rituel décrit à la section 4. |
| 5 | [Mémoire factuelle](PROJECT_MEMORY.md) | Faits établis, décisions, risques, sources et état courant. | Lire avant tout travail après reprise ou compression. |
| 6 | [Journal d’ingénierie](ENGINEERING_LOG.md) | Chronologie indexable des inspections, changements, exécutions, preuves et handoffs. | Ajouter une entrée à chaque événement significatif. |

Le Core reste indépendant des concepts, outils et corpus ARET ; ARET devient un **Domain Pack de compatibilité** et non une dépendance d’installation.[1]

## 3. Cycle obligatoire d’un lot de travail

| Étape | Action | Preuve ou trace attendue | Interdiction |
|---|---|---|---|
| `BASELINE` | Lire les sources applicables, vérifier Git, les limites, les tests et l’état connu. | Référence de commit, résultats de référence et entrée de journal. | Partir d’un souvenir conversationnel. |
| `HYPOTHESIS` | Formuler une cause, une cible et un invariant testable. | Énoncé explicitement qualifié `HYPOTHESIS`. | Présenter l’hypothèse comme un fait. |
| `PATCH` | Réaliser un changement minimal et isolé. | Diff Git borné et fichiers ciblés. | Mélanger plusieurs causes, un refactoring opportuniste ou une amélioration non liée. |
| `RUN` | Exécuter les validations ciblées, puis Core et conformance appropriées. | Commandes, versions, artefacts et sorties capturés. | Considérer un texte « PASS » comme une preuve. |
| `EVIDENCE` | Hacher, stocker et relier les artefacts nécessaires. | Execution, evidence, receipt et provenance lorsque le moteur le permet. | Promouvoir `PROVEN` sans evidence admissible `PASS`. |
| `COMPARISON` | Comparer dimensions pertinentes au baseline. | Tableau baseline / résultat / divergence. | Comparer uniquement à la dernière exécution. |
| `VERDICT` | Conclure `PASS`, `FAIL` ou `UNKNOWN`. | Motif et limites explicites. | Convertir `UNKNOWN`, `SKIPPED` ou une erreur en `PASS`. |
| `RECORD` | Mettre à jour mémoire, journal, matrice et handoff. | Liens croisés et commit atomique. | Laisser un changement non traçable. |

Une *wall* n’est ni une réussite ni un échec à masquer : elle devient une observation qualifiée, une cause à investiguer et, si nécessaire, un nouveau work item.[2]

## 4. Rituel de reprise et de pré-modification

Avant tout outil de modification, en particulier après une compaction, une interruption ou un changement de session, lire dans cet ordre :

1. le présent plan et sa section **État actif** ;
2. les invariants applicables et la matrice de découplage ;
3. la section **Reprise active** de la mémoire ;
4. les entrées de journal référencées ;
5. l’état Git, les commits de baseline, les limites de périmètre et les outils disponibles ;
6. les gates, preuves et risques encore ouverts.

Le rituel se termine par une confirmation explicite : **ce qui est prouvé, observé, inféré, hypothétique et inconnu est distingué ; le prochain changement est borné ; le baseline est identifié.** Sans cette confirmation, il faut s’arrêter et journaliser le blocage.[2]

## 5. État actif

| Champ | Valeur actuelle | Statut | Source de contrôle |
|---|---|---|---|
| Produit | VERA-MMU — *Verifiable Epistemics & Relational Architecture*. | `PROVEN` par le contenu du dépôt. | [Identité](../IDENTITY.md) ; journal `LOG-0002`. |
| Révision VERA-MMU | `ef707339c245ee1d36b8a78312d1a441c86296dc` sur `main`, arbre propre au relevé initial. | `OBSERVED` | Journal `LOG-0002`. |
| Révision ARET-MMU de référence | `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4` sur `main`, arbre propre au relevé initial. | `OBSERVED` | Journal `LOG-0001`. |
| Capacité actuelle | Core d’identité universel : Profile normalisé/hashé, ProjectIdentity, URI `vera://` strictes, roots contrôlées, no-Git/multi-repo et runtime local confiné. | `OBSERVED` : 21 tests et 14 sous-tests passent ; wheel isolé et `vmmu inspect` validés. | Journal `LOG-0009` ; mémoire `MEM-STATE-006`. |
| Exclusions actuelles | Pas encore de serveur MCP de production, Capability Engine générique, importeur ARET, migration SQL universelle ou dashboard. | `OBSERVED` | [README](../../README.md) ; mémoire `MEM-STATE-001`. |
| Baseline M0.1 | Inventaire, hashes, tests, surface statique, hooks/reprise, bundle et bundle Git capturés dans `ARET_MMU_M0_1_BASELINE/`. | `OBSERVED` ; exécution exhaustive `UNKNOWN` | Journal `LOG-0006` ; mémoire `MEM-BASE-003`. |
| Wall active | Toolchain des oracles ARET indisponible dans l’environnement de baseline ; ne pas confondre `SKIPPED` et validation. | `BLOCKED` | Mémoire `MEM-WALL-001` ; journal `LOG-0006`. |
| Registre M0.2 | Seize couplages documentés avec sources, frontière Core/pack, stratégie et tests de parité ; C07/C08 restent bloqués par la toolchain. | `PASS` pour la cartographie ; parité `UNKNOWN` | [Matrice](../DECOUPLING_MATRIX.md) ; journal `LOG-0007`. |
| Lot suivant | Aucun lot actif ; M2 ne peut être armé que par un rituel séparé après vérification du commit M1. | `READY_FOR_M2_RITUAL` ; `MEM-WALL-001` préservée | Journal `LOG-0009` ; mémoire section 7. |

## 6. Roadmap de transformation et gates de sortie

| ID | Lot | Objectif borné | Gate minimale de sortie | Invariants principaux | État |
|---|---|---|---|---|---|
| `M0.1` | Freeze ARET | Figer commit, dépendances, schéma, tests, hooks, comportement MCP et bundle de référence. | Inventaire hashé et baseline reproductible ; écarts connus explicitement listés. | I001, I004, I010, I014 | `CAPTURED` ; exécution exhaustive `UNKNOWN` (wall M0.1-W001) |
| `M0.2` | Registre de compatibilité | Compléter la matrice de découplage par source, portée, test de parité et stratégie de migration. | Chaque couplage ARET est `TODO`, `BLOCKED` ou `SPLIT`, jamais implicite. | I014, I015 | `PASS` pour la cartographie ; 14 `SPLIT`, 2 `BLOCKED`, parités `UNKNOWN` |
| `M1` | Core d’identité | Project Profile validé, identité de projet avec fingerprint de workspace, workspace multi-racines/no-Git, runtime confiné et adressage `vera://`. | Tests de stabilité, URI canonique, traversal/symlink/lecteur Windows, no-Git, multi-repo ; wheel et CLI isolés ; scan anti-ARET. | I008, I009, I011, I012, I014, I015 | `PASS` pour les gates techniques ; parité ARET explicitement `UNKNOWN` |
| `M2` | Persistence universelle | Schéma générique, services séparés et migrations append-only. | Migrations checksumées, intégrité référentielle et audit validés. | I001–I006, I010, I014 | `PLANNED` |
| `M3` | Capability / Evidence / Gates | Catalogue fermé, runners bornés, executions persistées, validators et gates. | Aucun shell arbitraire ; une gate ne passe que sur une exécution et une preuve réelles. | I004–I008, I013, I014 | `PLANNED` |
| `M4` | Pack ARET | Compatibilité de lecture, import hors ligne, pipelines, playbook et toolchain ARET isolés. | Parité ARET mesurée contre baseline, Core installable sans dépendance ARET. | I004, I006–I008, I015 | `PLANNED` |
| `M5` | Compilateur MCP et adapters | Manifeste immuable, API stable, instructions/hook/config générés. | Même entrée = même `mcp_build_hash` ; doctor et snapshots passent. | I009, I012–I014 | `PLANNED` |
| `M6` | CLI et Dashboard | Init, scan, configure, validate, generate, install, doctor et éditeur initial. | Installation sans pollution du code métier ; scan seulement `OBSERVED`. | I002, I011, I013, I014 | `PLANNED` |
| `M7` | Conformance multi-domaines | Fixtures software, game, research, data, documentation/hardware, no-Git et multi-repo. | Au moins cinq domaines satisfont le protocole de conformance. | Tous, spécialement I011 et I015 | `PLANNED` |
| `M8` | Release contrôlée | Packaging, migration, documentation dérivée et garanties de compatibilité. | Definition of Done globale satisfaite et rapport d’écarts nul ou accepté explicitement. | Tous | `PLANNED` |

## 7. Definition of Done par work item

Un work item n’est `DONE` que si toutes les réponses applicables sont **oui**, avec références vérifiables dans le journal.

| Contrôle | Question de sortie |
|---|---|
| Périmètre | Le changement correspond-il à une hypothèse et un lot uniques ? |
| Invariants | Les invariants affectés sont-ils cités et testés ? |
| Baseline | Le commit et les mesures de référence sont-ils identifiés ? |
| Validation | Les tests ciblés, Core, sécurité, conformance et ARET requis ont-ils été exécutés ? |
| Comparaison | Le résultat est-il au moins équivalent au baseline sur les dimensions pertinentes ? |
| Evidence | Les artefacts, hashes, sorties et receipts requis sont-ils attachés ou référencés ? |
| Décision | Le verdict est-il `PASS`, `FAIL` ou `UNKNOWN`, sans langage ambigu ? |
| Traçabilité | La mémoire, le journal, la matrice et le handoff sont-ils à jour ? |
| Git | Le diff est-il expliqué, minimal, propre et committé atomiquement ? |

## 8. Règles de mise à jour de ce document

Chaque session qui modifie le projet met à jour au minimum : le statut du lot actif, le prochain travail non bloqué, les gates réalisées ou manquantes et les liens vers les entrées du journal. Une modification de statut sans preuve associée est interdite. Les décisions de conception durables sont d’abord consignées dans la mémoire, puis résumées ici si elles changent le plan.

Toute divergence entre ce document, la mémoire et le journal est une condition `UNKNOWN` : le travail s’arrête jusqu’à lecture des sources, correction append-only de la mémoire et nouvelle entrée de journal.

## Sources de travail non publiques

La spécification Universal Dev-MMU et la doctrine de travail ARET mentionnées dans ce document ont été fournies par le propriétaire du projet dans cette session. Elles constituent des sources de travail traçables dans le registre de mémoire, mais ne sont pas publiées dans ce dépôt tant qu’une décision explicite de diffusion n’a pas été prise.

## Références

[1]: ../INVARIANTS.md "Invariants non régressifs de VERA-MMU"
[2]: #sources-de-travail-non-publiques "Doctrine de travail ARET fournie par le propriétaire du projet"
[3]: https://github.com/aciderix/ARET-MMU "ARET-MMU — dépôt de référence"
[4]: ../DECOUPLING_MATRIX.md "Registre de découplage ARET-MMU → VERA-MMU"
[5]: ../IDENTITY.md "Identité officielle de VERA-MMU"
