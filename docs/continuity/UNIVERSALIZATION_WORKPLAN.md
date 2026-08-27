# Plan vivant d’universalisation de VERA-MMU

> **Statut :** actif — document de contrôle évolutif.
>
> **Dernière revue factuelle :** 26 août 2026 — M4-A importe la page baseline de `component` dans un store temporaire ; M4-B a ensuite importé et post-validé la série source complète de 9 `function_symbol` en 3 pages et de 13 `brick` en 5 pages ; M4-C a importé 532 `knowledge` en 6 pages et livré le ledger/projection read-only de `knowledge_source`. La branche toolkit fournie a restauré la précondition source/toolchain et permis des exécutions externes hashées, mais `winediff` échoue à `255/264`. L’audit M4.EXIT reste donc `NOT_ELIGIBLE` : C07/C08 sont `IN_PROGRESS`, les couplages restent `SPLIT` et la parité est `UNKNOWN`.
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
| Révision VERA-MMU | M5-M.3a est publié jusqu’à `f3e0e6f`; M5-M.3b fonctionnel est committé localement à `3f26dad` avant sa continuité documentaire. Les jalons fonctionnels `5ffe182`, `5de260d`, `50cc79a`, `e073fa2`, `9010293`, `5dab574`, `ea7235a`, `8b38b1b`, `674929c`, `e576b1a`, `df73425`, `45fe9af`, `940fb7e`, `f79415b`, `ed9f2e8` et `3f26dad` portent façade, manifeste, registries runtime/lifecycle, adapter/hôte Pack, instructions, config, hooks, plan hôte, installateur, Lifecycle Core, acquittement MCP contextualisé, adapter Claude local, plan/doctor cloud, adapter cloud staged, configuration project-local et mécanisme user-scope cloud. | `OBSERVED` ; le mécanisme user-scope testé reste distinct de toute écriture réelle et de toute preuve Claude Code web live. | `LOG-0182` à `LOG-0198` et artefacts M5 des 26–27 août 2026. |
| Révision ARET-MMU de référence | `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4` sur `main`, arbre propre lors du contrôle terminal M3. | `OBSERVED` | Journal `LOG-0001`, `LOG-0070`. |
| Capacité actuelle | M1, M2 et M3 fournissent le Core; M4-D transporte les verdicts Pack→Core; M5-A expose la chaîne par vrai serveur/client MCP stdio; M5-B la lie à un manifeste canonique vérifié; M5-C résout capability→adapter dans un registry fermé; M5-D assemble un adapter ARET Pack; M5-E attache des instructions; M5-F prévisualise une config; M5-G compile un plan SessionStart; M5-H traduit en plan Claude Code; M5-I installe la config MCP; M5-J fournit le Resume Dossier et la garde locale hard/soft universels; M5-K lie un adapter lifecycle attesté à MCP et acquitte le seul dossier armé; M5-L traduit ce lifecycle en hooks Claude Code locaux, installation opt-in, serveur MCP local et doctor observationnel; M5-M.1 compile un plan Claude cloud lié à tous ces snapshots et diagnostique seulement un runtime préinstallé/trust observé; M5-M.2 distribue le staging cloud confirmé, le hook cloud et le serveur MCP lifecycle cloud, tous runtime-confined et deny-by-default; M5-M.3a prévisualise, fusionne et applique après confirmation les réglages cloud project-local depuis ce runtime; M5-M.3b prévisualise et fusionne l’approbation user-scope, avec deux confirmations distinctes pour son unique écriture. | `OBSERVED` : migrations 001→038, suite `465 passed, 37 subtests passed`, roue isolée. Les payloads contractuels atteignent admission/gate seulement pour `PASS` validé; manifest/adapter/instruction/config/hook-plan/plan hôte/lifecycle-plan étranger, périmé ou ambigu est refusé; l’adapter Pack refuse les résultats ou commandes du client. Le dossier/état lifecycle est project-bound, runtime-confiné et transport-neutre. Le score effectivement obtenu par ARET est hors de cette conformance VERA. | `LOG-0182` à `LOG-0198`; artefacts M4-D et M5-A/B/C/D/E/F/G/H/I/J/K/L/M.1/M.2/M.3a/M.3b des 26–27 août 2026. |
| Exclusions actuelles | Aucun shell arbitraire, réseau implicite, accès fichier externe libre, validator métier, admission/proof/promotion automatique, quorum pondéré, expiration/fenêtre temporelle ou révocation de gate, CLI complète, merge, pack de compatibilité complet ou dashboard. M5-L fournit l’adapter/hook Claude Code local; M5-M.2 fournit le staging, hook et MCP cloud sous runtime VERA; M5-M.3a fournit la configuration cloud project-local confirmée; M5-M.3b prépare seulement le write-path user-scope sous double confirmation. Aucun home settings/trust **réellement appliqué**, setup, roue/bootstrap, réseau, sync/push, Pack réel, preuve Claude Code web live ou autre hôte n’est livré. Une seule session par adapter et projet est supportée; les conflits sont refusés. La façade MCP M5-A/B/C/D/E/F/G/H/I vérifie manifeste, registry et instructions mais refuse toute execution sans hôte de Pack explicite; M5-I installe seulement `.mcp.json` après confirmation et ne modifie pas `.claude`; le seul runner externe Core est `OBSERVED_PROCESS`, qui n’exécute rien ; le pack ARET ne lance que son catalogue fermé sous namespace réseau isolé. Les imports M4-A/M4-B restent non fusionnels et temporaires. | `OBSERVED` | `LOG-0182` à `LOG-0198`; registre M4 et tests du runner fermé. |
| Baseline M0.1 | Inventaire, hashes, tests, surface statique, hooks/reprise, bundle et bundle Git capturés dans `ARET_MMU_M0_1_BASELINE/`. | `OBSERVED` ; exécution exhaustive `UNKNOWN` | Journal `LOG-0006` ; mémoire `MEM-BASE-003`. |
| Précondition toolchain ARET | La branche toolkit verrouillée fournit sources/scripts/corpus ; le binaire externe SHA-256 est épinglé. Le préflight/doctor Pack vérifie commit, propreté, scripts, dépendances et sandbox sans installer. | `OBSERVED_RESTORED` ; C07/C08 restent `IN_PROGRESS`. La disponibilité de cette toolchain ne préjuge pas d’un score ou d’une parité ARET. | `artifacts/m4d_real_verdict_matrix_and_doctor_2026-08-26.md`. |
| Registre M0.2 | Seize couplages documentés avec sources, frontière Core/pack, stratégie et tests de parité ; C07/C08 disposent maintenant de runner/préflight Pack et d’une chaîne universelle validator→admission/proof/gate. Doctor et parité complète restent absents. | `PASS` pour la cartographie ; parité `UNKNOWN` | [Matrice](../DECOUPLING_MATRIX.md) ; artefact de chaîne universelle M4-D du 26 août 2026. |
| Lot suivant | M4.EXIT reste `NOT_ELIGIBLE` pour ses imports, playbook, bundles/VCS et compatibilités restants. M5-A/B/C/D/E/F/G/H/I ont validé transport, manifeste, registry, adapter Pack, instructions, config, hook plan, plan hôte et installateur MCP. M5-J livre le Lifecycle Core, M5-K la liaison MCP/registry attestée, M5-L le premier adapter Claude Code local opt-in, M5-M.1 le plan/doctor cloud préinstallé, M5-M.2 l’adapter cloud staged, M5-M.3a la configuration project-local contrôlée et M5-M.3b le mécanisme user-scope à double confirmation. Le prochain acte autorisé est opératoire, pas un patch : présenter le preview réel, recueillir deux confirmations explicites juste avant l’écriture trust user-scope, puis vérifier le host dans une session Claude Code web fraîche ; ni bootstrap réseau ni setup ne sont autorisés. Les divergences Wine restent des observations ARET distinctes. | `M5_IN_PROGRESS` ; M5-J/K/L/M.1/M.2/M.3a/M.3b `PASS` pour leurs périmètres testés, trust réel/preuve web `NOT_RUN`; parité ARET hors conformance de transport | `LOG-0182` à `LOG-0198`; contrats MCP M5-A/B/C/D/E/F/G/H/I/J/K/L/M.1/M.2/M.3a/M.3b des 26–27 août 2026. |

## 6. Roadmap de transformation et gates de sortie

| ID | Lot | Objectif borné | Gate minimale de sortie | Invariants principaux | État |
|---|---|---|---|---|---|
| `M0.1` | Freeze ARET | Figer commit, dépendances, schéma, tests, hooks, comportement MCP et bundle de référence. | Inventaire hashé et baseline reproductible ; écarts connus explicitement listés. | I001, I004, I010, I014 | `CAPTURED` ; exécution exhaustive `UNKNOWN` (wall M0.1-W001) |
| `M0.2` | Registre de compatibilité | Compléter la matrice de découplage par source, portée, test de parité et stratégie de migration. | Chaque couplage ARET est `TODO`, `BLOCKED` ou `SPLIT`, jamais implicite. | I014, I015 | `PASS` pour la cartographie ; 14 `SPLIT`, 2 `BLOCKED`, parités `UNKNOWN` |
| `M1` | Core d’identité | Project Profile validé, identité de projet avec fingerprint de workspace, workspace multi-racines/no-Git, runtime confiné et adressage `vera://`. | Tests de stabilité, URI canonique, traversal/symlink/lecteur Windows, no-Git, multi-repo ; wheel et CLI isolés ; scan anti-ARET. | I008, I009, I011, I012, I014, I015 | `PASS` pour les gates techniques ; parité ARET explicitement `UNKNOWN` |
| `M2` | **Universal Schema** fini | Livré : M2.1–M2.14 (substrate, entités/relations, knowledge/provenance/supersession, assets/associations, Symbol Registry, Work-Item Backbone et Capability/Execution Schema). Aucun lot M2 ne reste. | **M2.EXIT** : toutes les six ressources de la spécification M2 existent avec migrations vérifiées, services de persistance exacts et bornés, FKs/immuabilité/audit/rollback testés ; fresh install et upgrade 001→courant, tests complets, wheel isolé, scans anti-ARET/no-shell/no-network/no-`PROVEN` passent. La gate ne revendique ni parité ARET ni preuve métier. | I001–I006, I010, I011, I014, I015 ; frontière I004, I007–I008, I013 | `PASS` — M2.1–M2.14 et M2.EXIT `PASS`; parité ARET `UNKNOWN` |
| `M3` | Capability / Evidence / Gates | M3.1–M3.25 et M3.EXIT livrent et auditent le Core local fermé de capability/evidence/validation/admission/proof/gate/work graph/lifecycle. | Fresh 032, upgrade 001→032, chaîne complète, suite Core, scans de frontière, checksums et wheel isolée passent. Le verdict n’infère ni parité ARET ni fonctionnalités post-M3. | I004–I008, I013, I014, I015 | `PASS` — M3 borné terminé; C05/C06/C16 `SPLIT`, C07 `BLOCKED`, parité ARET `UNKNOWN` |
| `M4` | Pack ARET et primitive Core | M4.1–M4.15 livrent les surfaces déclaratives et le premier write-path. M4-D transporte les verdicts contractuels du Pack vers les services génériques : `272/272→PASS`, `271/272→FAIL`, prérequis absent→`SKIPPED`, timeout/sortie inconnue→`ERROR`, format non promouvable→`UNKNOWN`. Conformance globale, imports restants, playbook, bundles/VCS et compatibilités restent dans le [registre de clôture M4](M4_COMPLETION_REGISTER.md). | Les fixtures de transport valident que seul `PASS` validé peut atteindre admission/proof/gate; les autres verdicts sont persistés puis refusés. Suite `397 passed, 25 subtests passed`, scans et roue isolée passent. Les runs ARET réels sont des smoke tests du Pack; leurs scores ne conditionnent pas cette conformance VERA. | I002, I004, I006–I008, I015 | `IN_PROGRESS` — M4-A `PASS` borné ; M4-B/C observés, C01–C06/C16 `SPLIT`, C07/C08 `IN_PROGRESS` avec matrice de transport interne; exposition MCP requise en M5 et `M4.EXIT` `NOT_ELIGIBLE` |
| `M5` | Compilateur MCP et adapters | M5-A livre la façade MCP stdio et la matrice client→execution→evidence→admission→gate; M5-B livre le manifeste immuable, `mcp_build_hash` et sa vérification; M5-C livre le registry d’objets hôte; M5-D livre l’adapter et l’hôte ARET Pack; M5-E livre les instructions générées et vérifiées; M5-F la config prévisualisée; M5-G le plan SessionStart; M5-H l’adapter de revue Claude Code; M5-I l’installateur MCP opt-in. M5-J livre le Lifecycle Core, M5-K le registry/plan attesté et l’acquittement MCP contextualisé, M5-L l’adapter Claude Code local, M5-M.1 le plan/doctor cloud préinstallé, M5-M.2 l’adapter cloud staged, M5-M.3a la configuration project-local attestée et M5-M.3b le mécanisme d’approbation user-scope. M5-N livre l’adapter Codex staged/configuré project-local avec garde `PARTIAL_LOCAL_TOOLS`; M5-O livre l’adapter Gemini CLI avec garde `TOOL_GUARD_NO_POST_COMPACTION`; M5-P livre l’adapter Antigravity avec garde `TURN_GUARD_HARD`; l’acte réel Claude Web et MCP générique restent après. | Même entrée = mêmes `mcp_build_hash`, `instructions_hash`, `config_hash`, `hook_plan_hash` et `plan_hash`; vrai serveur/client MCP, snapshots et matrice client→execution→evidence→admission→gate passent sans injection client de commande/verdict/artefact. Les futurs niveaux lifecycle ne peuvent être déclarés que lorsque les capacités d’hôte correspondantes sont testées. | I007–I009, I011–I015 | `IN_PROGRESS` — M5-A `PASS` (`5ffe182`), M5-B `PASS` (`5de260d`), M5-C `PASS` (`50cc79a`), M5-D `PASS` (`e073fa2`), M5-E `PASS` (`9010293`), M5-F `PASS` (`5dab574`), M5-G `PASS` (`ea7235a`), M5-H `PASS` (`8b38b1b`), M5-I `PASS` (`674929c`), cadrage lifecycle `PASS` (`LOG-0191`), M5-J `PASS` (`e576b1a`), M5-K `PASS` (`df73425`), M5-L `PASS` (`45fe9af`), M5-M.1 `PASS` (`940fb7e`), M5-M.2 `PASS` (`f79415b`), M5-M.3a `PASS` (`ed9f2e8`, `LOG-0197`), M5-M.3b `PASS` pour mécanisme (`3f26dad`, `LOG-0198`), M5-N `PASS` pour chaîne contrôlée (`588c886`, `LOG-0199`, garde `PARTIAL_LOCAL_TOOLS`), M5-O `PASS` pour chaîne contrôlée (`7ca437e`, `LOG-0200`, garde `TOOL_GUARD_NO_POST_COMPACTION`), M5-P `PASS` pour chaîne contrôlée (`df03100`, `LOG-0201`, garde `TURN_GUARD_HARD`), trust/revue et preuves Codex/Gemini/Antigravity réels `NOT_RUN`, trust Claude Web/preuve web `NOT_RUN` |
| `M6` | CLI et Dashboard | Init, scan, configure, validate, generate, install, doctor et éditeur initial. | Installation sans pollution du code métier ; scan seulement `OBSERVED`. | I002, I011, I013, I014 | `PLANNED` |
| `M7` | Conformance multi-domaines | Fixtures software, game, research, data, documentation/hardware, no-Git et multi-repo. | Au moins cinq domaines satisfont le protocole de conformance. | Tous, spécialement I011 et I015 | `PLANNED` |
| `M8` | Release contrôlée | Packaging, migration, documentation dérivée et garanties de compatibilité. | Definition of Done globale satisfaite et rapport d’écarts nul ou accepté explicitement. | Tous | `PLANNED` |

### 6.1. Contrat terminal de M2 — macro-lots et exclusions

| ID | Résultat persistant cohérent | Critère d’admission du lot | Exclus explicitement | Gate propre du lot |
|---|---|---|---|---|
| `M2.12` | **Symbol Registry** : table, migration, modèle et service append-only pour un symbole générique attaché à une entity existante, avec `kind`, `path`, `identifier`, signature déclarative et métadonnées canoniques. | Le symbole satisfait une ressource `symbol` prévue par la spécification M2 et évite de faire de `function_symbol` ARET un concept du Core. | Scan de source, résolution de fichier, FTS/FIND, import ARET, relation automatique, graphe ou preuve. | `PASS` : création/lecture exacte, unicité sémantique, FK, immuabilité, audit et rollback ; migration fresh/historique et wheel isolé vérifiés (`LOG-0042`). |
| `M2.13` | **Work-Item Backbone** : table, migration, modèle et service append-only pour une unité de travail générique, son parent optionnel, ses types/statuts sûrs, metadata et audit. | `work_item` est une ressource du schéma M2 ; le backbone est une dépendance structurelle du futur work graph sans en présumer le comportement. | Lifecycle mutable, dépendances, traversal, assignation active, gate, exécution, evidence, proof et `DONE` automatique. | `PASS` : création/lecture exacte, parent FK/self-parent, types/statut sûrs, immuabilité/audit/rollback ; migration fresh/historique et wheel isolé vérifiés (`LOG-0045`). |
| `M2.14` | **Capability Declaration & Execution Schema** : registre immutable de capability purement déclarative, ajout de la ressource URI canonique `capability`, et migration de l’entité `execution` conforme au schéma universel ; aucun comportement de moteur. | `capability registry` et `execution` ferment les deux ressources M2 restantes ; l’execution rend traçable un fait ultérieur sans être assimilée à une preuve. | Runner, shell, réseau, policy, validator, écriture/lecture opérationnelle d’execution, artefact dynamique, Evidence Store, HMAC, admission, gate, `PROVEN`. | Schémas, URI, références, JSON canonique, immuabilité/audit et migrations sont testés ; les tests démontrent expressément l’absence de runner et de promotion. |
| `M2.EXIT` | **Universal-Schema Gate** : audit transversal du contrat M2 achevé. | Tous les trois macro-lots sont `PASS`, sans relaxation d’un invariant ni ajout hors contrat. | Extension opportuniste, index non requis, raccourci M3, affirmation de parité ARET ou de preuve métier. | Gate détaillée à la ligne M2 de la roadmap, rapportée dans journal/mémoire, commit/push vérifiés. |

> **Règle anti-redondance.** Une hypothèse M2 est recevable uniquement si elle ferme une ressource expressément listée ci-dessus, une contrainte d’intégrité indispensable à cette ressource, ou une dépendance M3 prouvée par son contrat. Un index seul, une optimisation spéculative ou une capacité déjà garantie par une contrainte existante est rejeté. `MEM-DEC-017` / `LOG-0036` — l’index asset par hash déjà couvert par `UNIQUE(content_hash)` — constitue le cas de référence.

> **Frontière M2/M3.** M2 persiste des données déclaratives et immuables. M3 exécute, valide, admet et gouverne. En particulier, `execution` décrit un événement ; **seule** une evidence admissible `PASS` peut ultérieurement contribuer à une promotion `PROVEN`. Cette séparation conserve I004 et interdit que le schéma soit traité comme une preuve.

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


## 10. Contrat terminal approuvé de M3 — M3.EXIT

**Décision de périmètre.** M3 est pleinement livré lorsque le Core fournit un moteur local, fermé et policy-gated de capabilities, evidence, validation, admission, proof, gates, work graph et lifecycle dérivé. Cette clôture ne revendique ni parité ARET, ni oracle métier, ni shell, réseau, filesystem externe, CLI/MCP de production ou Domain Pack.

| ID | Résultat persistant cohérent | Exclusions explicites | Gate propre du lot |
|---|---|---|---|
| `M3.22` | Rapport composite de blocage réunissant dépendances directes/transitives et gates directes non `PASS`, en ordre canonique et lecture pure. | Scheduler, orchestration, traversal de gates, mutation, audit, execution, admission, preuve. | Graph linéaire/diamant, déduplication, ordre stable, modes `ALL`/`ANY`/`AT_LEAST`, zéro écriture/audit, wheel isolé. |
| `M3.23` | Policy singleton immutable `OPEN` / `REQUIRE_READY_FOR_COMPLETE`; le mode strict refuse `COMPLETE` avant écriture si readiness `BLOCKED`. | Complétion automatique, planification, execution, evidence, admission, preuve, orchestration. | Compatibilité `OPEN`, refus strict, satisfactions dependency/gate, rollback event/audit, migration et wheel isolée. |
| `M3.24` | Binding explicite entre admission `ADMITTED` et validation `PASS` de la même evidence en mode strict. | Validation déclenchée implicitement, validator/oracle additionnel, mutation de knowledge, preuve automatique. | FKs/unicité, refus cross-evidence/`FAIL`/absent/duplicat, rollback, compatibilité permissive, wheel isolée. |
| `M3.25` | Catalogue fermé vérifiant la compatibilité profile de runner / kind de validator / schéma de paramètres pour `EVIDENCE_HASH` et `EVIDENCE_FIELDS`. | JSON Schema général, interprétation métier, oracle, fichier, réseau, shell, runner générique. | Matrice complète profile×validator×schema×policy, `PASS`/`FAIL`, refus cross-kind, rollback et wheel isolée. |
| `M3.EXIT` | Audit cumulatif des capacités M3.1–M3.25 et décision terminale. | Toute extension opportuniste de surface ; parité ARET ; pack, CLI, MCP, dashboard, runner externe, oracle métier. | Fresh install et upgrades 001→courant ; chaîne capability→execution→evidence→validation→admission→proof→gate→readiness→lifecycle ; tests Core, scans no-shell/no-network/no-filesystem/no-ARET/no-secret, wheel isolée, checksums, docs et publication vérifiés. |

> **Règle de clôture.** M3 passe `PASS` uniquement si `M3.22` à `M3.25` sont `PASS` et si `M3.EXIT` satisfait toutes ses gates cumulatives. Les états C05/C06/C16 et la parité ARET ne sont pas déduits de M3.EXIT : C05/C06/C16 restent `SPLIT`, C07 reste `BLOCKED` sous `MEM-WALL-001` et la parité reste `UNKNOWN` jusqu’à M4.

> **Transfert explicite.** Les oracles et runners externes relèvent de Domain Packs post-M3 ; la confirmation interactive, CLI, MCP et intégrations relèvent de M5/M6/M7 ; la rotation HMAC, les gates pondérées/temporelles/révocables sont des évolutions post-M3 sous contrats séparés.
