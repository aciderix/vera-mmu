# Plan vivant d’universalisation de VERA-MMU

> **Statut :** actif — document de contrôle évolutif.
>
> **Dernière revue factuelle :** 27 août 2026 — l’audit M11 contre la spécification finale (artefact `m11_specification_completeness_audit_2026-08-27.md`) conclut `NOT_DONE`, hors validation MSI Windows explicitement différée. Le Core générique, la conformance déclarative, le MCP stdio, les adapters, la CLI de préparation et la console Tauri sont présents. Le modèle de projet riche, bundles/import/restore, API/CLI complète, Dashboard configurateur, Doctor composite, documentation/coverage, VCS multi-provider et parité ARET restent partiels ou absents. M4.EXIT demeure `NOT_ELIGIBLE` : C07/C08 sont `IN_PROGRESS`, les couplages restent `SPLIT` et la parité est `UNKNOWN`.
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
| `M5` | Compilateur MCP et adapters | M5-A livre la façade MCP stdio et la matrice client→execution→evidence→admission→gate; M5-B livre le manifeste immuable, `mcp_build_hash` et sa vérification; M5-C livre le registry d’objets hôte; M5-D livre l’adapter et l’hôte ARET Pack; M5-E livre les instructions générées et vérifiées; M5-F la config prévisualisée; M5-G le plan SessionStart; M5-H l’adapter de revue Claude Code; M5-I l’installateur MCP opt-in. M5-J livre le Lifecycle Core, M5-K le registry/plan attesté et l’acquittement MCP contextualisé, M5-L l’adapter Claude Code local, M5-M.1 le plan/doctor cloud préinstallé, M5-M.2 l’adapter cloud staged, M5-M.3a la configuration project-local attestée et M5-M.3b le mécanisme d’approbation user-scope. M5-N livre l’adapter Codex staged/configuré project-local avec garde `PARTIAL_LOCAL_TOOLS`; M5-O livre l’adapter Gemini CLI avec garde `TOOL_GUARD_NO_POST_COMPACTION`; M5-P livre l’adapter Antigravity avec garde `TURN_GUARD_HARD`; M5-Q livre le fallback MCP générique `MCP_ONLY`; l’acte réel Claude Web reste une gate séparée. | Même entrée = mêmes `mcp_build_hash`, `instructions_hash`, `config_hash`, `hook_plan_hash` et `plan_hash`; vrai serveur/client MCP, snapshots et matrice client→execution→evidence→admission→gate passent sans injection client de commande/verdict/artefact. Les futurs niveaux lifecycle ne peuvent être déclarés que lorsque les capacités d’hôte correspondantes sont testées. L’audit M10-B sépare les mécanismes contrôlés des essais host `NOT_RUN`. | I007–I009, I011–I015 | `IN_PROGRESS` — M5-A `PASS` (`5ffe182`), M5-B `PASS` (`5de260d`), M5-C `PASS` (`50cc79a`), M5-D `PASS` (`e073fa2`), M5-E `PASS` (`9010293`), M5-F `PASS` (`5dab574`), M5-G `PASS` (`ea7235a`), M5-H `PASS` (`8b38b1b`), M5-I `PASS` (`674929c`), cadrage lifecycle `PASS` (`LOG-0191`), M5-J `PASS` (`e576b1a`), M5-K `PASS` (`df73425`), M5-L `PASS` (`45fe9af`), M5-M.1 `PASS` (`940fb7e`), M5-M.2 `PASS` (`f79415b`), M5-M.3a `PASS` (`ed9f2e8`, `LOG-0197`), M5-M.3b `PASS` pour mécanisme (`3f26dad`, `LOG-0198`), M5-N `PASS` pour chaîne contrôlée (`588c886`, `LOG-0199`, garde `PARTIAL_LOCAL_TOOLS`), M5-O `PASS` pour chaîne contrôlée (`7ca437e`, `LOG-0200`, garde `TOOL_GUARD_NO_POST_COMPACTION`), M5-P `PASS` pour chaîne contrôlée (`df03100`, `LOG-0201`, garde `TURN_GUARD_HARD`), M5-Q `PASS` pour fallback contrôlé (`00f6cee`, `LOG-0202`, `MCP_ONLY`), preuves host Claude/Codex/Gemini/Antigravity et client MCP tiers `NOT_RUN`; voir `artifacts/m10_mcp_remaining_work_audit_2026-08-27.md`. |
| `M6` | CLI et Dashboard | **M6-A livré :** façade `vmmu adapter` avec matrix, doctor observationnel, validate, stage et configure project-local. **M6-B livré :** contrats partagés scan/génération/install, scan `OBSERVED`, preview déterministe et installation routée project-local. **M6-C livré :** init guidé project-local, templates de domaine proposés et Agent Profiles déclaratifs bornés. | M6-A/B/C routent les contrôles du Core/adapters sans pollution ; le scan ne lit ni contenu ni symlink, generate ne touche pas l’hôte, install/init conservent preview/confirmation et refusent user-scope générale, commandes libres ou profils sur-capables. | I002, I007, I011, I013, I014 | `PASS` dans le périmètre contrôlé — M6-A `17a2bba` (`LOG-0203`), M6-B `8d59939` (`LOG-0204`), M6-C `5cd679a` (`LOG-0205`) |
| `M7` | Dashboard, bridge desktop et distribution | Dashboard React statique M7-A ; bridge stdio M7-B ; application Tauri versionnée, sidecar PyInstaller et synchronisation Git automatique limitée à `.vera-mmu/` M7-C ; builder natif et matrice CI de vérification M7-D. | Aucun frontend ne contrôle chemin, shell, adapter brut, verdict, contenu, remote ou branche ; le sidecar stdio réutilise le Core ; la mémoire SQLite project-local est consolidée, commitée et poussée seulement selon sa policy fermée, sans fusion binaire implicite. | I001, I004, I007–I011, I013–I015 | `PARTIAL_PASS` — dashboard M7-A `OBSERVED` (checkpoint WebDev `f28ac0fa`), bridge M7-B `PASS` (`57279e1`, `LOG-0206`), M7-C `PASS` pour Tauri/sync, M7-D `PASS` : CI native `33061136241` verte pour Linux x64 (AppImage/Debian) et Windows x64 (NSIS/MSI), artefacts de vérification non signés ; release, GitHub Pages et hôtes réels `NOT_RUN` |
| `M8` | Conformance multi-domaines | Fixtures software, game, research, data, documentation/hardware, no-Git, mono/multi-repo et reprise Git project-local. | Les six domaines passent la même preview CLI, bridge fermé et intégration MCP déclarative ; Git reste optionnel et le clone récupère la mémoire SQLite project-bound sans merge binaire. | Tous, spécialement I009, I011 et I015 | `PASS` — local `3 passed, 6 subtests passed`, suite `504 passed, 43 subtests passed`, roue isolée et scan de frontière ; run CI `33065626744` vert avec suite `504 passed, 43 subtests passed` et packaging sous Linux x64/Windows x64. Oracles de domaines/hôtes réels, release/signature et installation utilisateur `NOT_RUN`. |
| `M9` | Release contrôlée | Packaging, migration, documentation dérivée, hashes/signatures et garanties de compatibilité. | Definition of Done globale satisfaite et rapport d’écarts nul ou accepté explicitement. | Tous | `PARTIAL_PASS` — `v0.1.0-rc.4` publiée comme GitHub Pre-release non signée avec six binaires, quatre manifests, manifest global et SHA-256. Tag/run `33078499592` vert : Linux et Windows `512 passed, 43 subtests passed`; assets passivement retéléchargés et vérifiés. rc.1 (MSI), rc.2 (checksum auto-référent) et rc.3 (collision manifests) restent non publiables. Signature stable/diffusion large, viewer versionné, installation utilisateur et hôtes réels `NOT_RUN`/`PENDING`. |
| `M10` | Smoke d’exécution des distributions | Checksums de candidat, CLI extraite et lancement contrôlé des applications/paquets sur runners natifs. | La CLI répond et reste observationnelle ; AppImage/.deb démarrent puis s’arrêtent sans résidu ; NSIS/CLI Windows ont atteint leur smoke. Aucun résultat ne dépasse ce contrôle de démarrage. | I009, I011, I015 | `PARTIAL_PASS` — Linux local : `517 passed, 43 subtests passed`, puis runner Ubuntu natif `33089780117` vert : intégrité, CLI, AppImage et payload Debian démarrés/arrêtés. Windows `33089780117` : CLI/NSIS atteints ; MSI retourne `0` mais son exécutable n’a pas été retrouvé, donc démarrage MSI `NOT_RUN` et laissé à vérification manuelle du propriétaire. Installation utilisateur et hôtes agents réels `NOT_RUN`. |

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

## 11. Audit de complétude M11 — spécification finale

L’audit M11 est une gate de vérité : il ne rouvre ni le Core ni M10 et n’autorise aucune promotion des états d’hôte. Il constate que la livraison complète définie par la spécification n’est pas atteinte, même en retirant le démarrage MSI Windows de l’évaluation.

| Groupe d’écarts | Statut | Prochain lot obligatoire |
|---|---|---|
| Profile et modèle projet déclaratif riche | `PASS` | M11-A clos ; preuve `m11_a_project_profile_catalogs_2026-08-27.md` |
| Front/handoff persistants, Resume Dossier configurable et policy projet | `PASS` | M11-AF clos ; preuve `m11_af_front_handoff_resume_policy_2026-08-27.md` |
| Bundle, export/import/restore et import projet avec provenance | `PASS` | M11-B clos ; preuve `m11_b_bundle_restore_project_import_2026-08-27.md` |
| Transport bundle/import, CLI associée et Doctor composite | `PASS` dans le périmètre M11-C | M11-C clos |
| Boot, FIND et READ exact/batch pour knowledge/entity/work-item | `PASS` dans le périmètre M11-H | M11-H clos |
| Lectures Front/handoff courants et READ relation/front/handoff exact | `PASS` dans le périmètre M11-I | M11-I clos |
| READ exact capability/execution/evidence | `PASS` dans le périmètre M11-J | M11-J clos |
| Parcours relationnel `related` entité-à-entité borné | `PASS` dans le périmètre M11-K | M11-K clos ; profile, historiques/listings et traversals spécialisés → lots dédiés |
| READ exact du symbole Core | `PASS` dans le périmètre M11-L | M11-L clos ; FIND/listing, filtres, scan/résolution et profile → lots dédiés |
| Historique d’executions compact et borné | `PASS` dans le périmètre M11-N | M11-N clos ; filtres, pagination, payloads et reprise → lots dédiés |
| Historique d’evidences compact et borné | `PASS` dans le périmètre M11-O | M11-O clos ; filtres, pagination, contenu de preuve et reprise → lots dédiés |
| Vue Dashboard d’état projet dérivée | `PASS` dans le périmètre M11-D-A | Couverture/VCS visibles après initialisation ; builders Profile/Capability/Gate et templates enrichis restent ouverts |
| Builder Dashboard de déclaration de Capability | `PASS` dans le périmètre M11-D-C | Preview/fraîcheur/confirmation validés ; runner, policy, Gate et modification restent ouverts |
| Garde d’identité avant édition Project Profile | `PASS` | Toute modification sémantique est refusée sans rebind durable; test dédié + intégral validés |
| Dashboard configurateur et builders | `PARTIAL` / `MISSING` | M11-D-B Profile requiert preview/fraîcheur, rebind profile+SQLite durable, rollback et reprise Doctor ; M11-D reste ouvert au-delà de D-A/C |
| Rapport de couverture dérivé (Core/CLI/MCP) | `PASS` dans le périmètre M11-E | Rapport M11-E clos ; générateurs `MMU_SETUP`/`TOOLS`/`GATES`/`POLICIES`/`ARCHITECTURE`/`MAINTENANCE` restent ouverts |
| Bridge d’adresse `mmu://` pour lecture | `PASS` dans le périmètre M11-F-A | Alias input-only validé ; migration canonique, aliases `aret_*`, lecteur legacy et VCS multi-provider restent ouverts |
| Diagnostic VCS local Git/no-VCS | `PASS` dans le périmètre M11-F-B | Observation sans commande validée ; providers Mercurial/SVN et opérations VCS restent ouverts |
| Adresse/compatibilité/VCS | `PARTIAL` | M11-F reste ouvert au-delà de M11-F-A/B |
| Migration et parité ARET | `PARTIAL` / `NOT_ELIGIBLE` | M11-G |
| Hôtes agents réels | `NOT_PROVEN` | Campagne distincte, après autorisation et gates requises |

La référence est `artifacts/m11_specification_completeness_audit_2026-08-27.md`, reliée à `MEM-DEC-177` et `LOG-0230`.

### 11.1 M11-A — Project Profile et catalogues déclaratifs : `PASS`

Les sept fichiers initialisés, le profile enrichi, le Front/resume, les taxonomies, les catalogues capabilities/gates/policies/agents, les six modèles de domaine et les quatre hashes de génération sont maintenant produits et validés sous `.vera-mmu`. Les contraintes de chemin, format, schéma, lien gate/capability et agent activé sont fail-closed. La preuve détaillée est `artifacts/m11_a_project_profile_catalogs_2026-08-27.md`; le lot n’inclut pas l’exécution de capability ni un éditeur de profil, qui restent des phases M11 distinctes.

### 11.2 M11-AF — Front, handoff, reprise configurable et policy projet : `PASS`

Le Front est maintenant un snapshot project-profile-bound, hashé et append-only; le handoff est lié au Front courant et au Resume Dossier compilé depuis les sections de reprise exigées par le profile. Les mutations sont précédées de la policy project-local fermée : `deny`, catalogue invalide/absent et absence de confirmation refusent avant transaction; `allow` n’écarte pas la confirmation explicite. La migration checksummée 039 est testée sur une base 038 existante avec conservation d’identité et triggers append-only exercés.

Les adapters Claude local/cloud, Codex, Gemini et Antigravity consomment le dossier dérivé du profile sous leurs garanties déjà déclarées; cela ne qualifie aucun hôte réel. Les preuves ciblées atteignent `15 passed`, les suites adapters/MCP `63 passed, 12 subtests passed`, et la suite intégrale `529 passed, 43 subtests passed`. La preuve détaillée est `artifacts/m11_af_front_handoff_resume_policy_2026-08-27.md`. La pause M11-B a été levée par une instruction explicite ultérieure du propriétaire.

### 11.3 M11-B — Bundle, restauration et import documentaire : `PASS`

Le Core dispose d’un export ZIP placé sous `.vera-mmu/bundles`, avec manifest JSON canonique, checkpoint WAL, snapshot SQLite, ledger de migrations, inventaire SHA-256 et artefacts runtime. La restauration contrôle l’archive, les hashes, le schéma, l’intégrité SQLite et l’identité de projet avant toute permutation ; une cible non vide est refusée sauf si elle est exactement identique, et un échec de permutation remet en place le runtime antérieur.

L’import de projet est volontairement restreint à une liste explicite de documents réguliers UTF-8 situés dans les racines de workspace. Il relit le preview hashé avant l’écriture, enregistre des knowledge `OBSERVED` uniquement et attache la provenance immuable. Toute fusion de knowledge est refusée, sauf replay exact. Les validations donnent 7 tests M11-B, 54 tests ciblés et `536 passed` en régression intégrale. La preuve détaillée est `artifacts/m11_b_bundle_restore_project_import_2026-08-27.md`.

> **Frontière conservée.** M11-B ne publie pas encore de commande CLI ni d’outil MCP de bundle/import/restore, n’automatise pas l’indexation d’un projet et n’importe aucune source réseau. Ces surfaces restent M11-C et les lots dédiés suivants.


### 11.4 M11-C.1 — Transport public bundle/import : `PASS` ; M11-C global `IN_PROGRESS`

La CLI fournit désormais `bundle-export`, `bundle-restore` et `project-import`. Le MCP expose un export Core-owned sans chemin client, un preview documentaire sans contenu et un import explicite qui requiert le hash de preview recalculé ainsi qu’une confirmation. Ces transports délèguent aux services M11-B et ne réimplémentent ni bundle, ni restauration, ni provenance.

La restauration demeure exclusivement disponible via CLI : un serveur MCP actif ne peut pas remplacer le runtime et le SQLite qu’il garde ouverts. Cette restriction est délibérée et conserve les garanties d’atomicité et de non-fusion. Les trois outils ajoutés, ainsi que `mmu_sync_memory`, sont inclus dans la liste canonique et le hash du manifeste MCP. Les contrats CLI/MCP/manifeste/lifecycle passent, et la régression intégrale atteint `538 passed in 58.99s`.

> **Limite historique de M11-C.1.** Le Doctor composite était encore requis après cette sous-tranche. Il est livré par M11-C final ci-dessous. Les API Core de boot/lecture, les commandes universelles complémentaires et les intégrations de production restent séparées. Voir `MEM-DEC-181` et `LOG-0233`.


### 11.5 M11-C — Transports publics et Doctor composite : `PASS`

M11-C est clos dans le périmètre de santé Core et de transport des primitives M11-B. `vmmu doctor` et `mmu_doctor` produisent le rapport `vera-doctor-report/v1`, avec contrôles profil, workspace, catalogues, identité, runtime, intégrité SQLite, ledger, WAL, artefacts, reprise, runtime MCP et VCS. Le diagnostic est explicitement non mutateur : SQLite est ouvert en lecture seule, aucun store n’est initialisé ou migré et les tests comparent le hash SQLite ainsi que le journal d’audit avant/après son exécution.

Les commandes `bundle-export`, `bundle-restore` et `project-import`, ainsi que les tools MCP `mmu_export_bundle`, `mmu_preview_project_documents` et `mmu_import_project_documents`, restent contrôlés par confirmation, confinement et preview hashé. `mmu_doctor` ne prend aucune entrée client et fait partie du manifeste MCP canonique. Une restauration via MCP reste interdite : le mécanisme CLI hors store actif conserve l’atomicité de restauration non fusionnelle.

La validation atteint `27 passed` sur les contrats M11-B/M11-C et **`541 passed in 64.78s`** en régression intégrale. L’artefact de preuve est `artifacts/m11_c_composite_doctor_2026-08-27.md`; voir `MEM-DEC-182` et `LOG-0235`.

> **Prochain travail non couvert :** M11-H traite séparément les API universelles de boot/FIND/READ et les commandes de produit associées. M11-D, M11-E, M11-F et M11-G restent inchangés; ce verdict ne prétend ni Dashboard complet, ni parité ARET, ni hôte agent réel.


### 11.6 M11-H — Boot, FIND et READ universels : `PASS`

Le service Core `ReadService` fournit désormais `boot`, `find`, `read` et `read_batch`, puis les expose de manière cohérente par CLI (`boot`, `find`, `read`, `read-batch`) et MCP (`mmu_boot`, `mmu_find`, `mmu_read`, `mmu_read_batch`). Le boot retourne uniquement l’identité de projet persistante et les références Front/handoff disponibles; aucune garde n’est armée ou acquittée. Les quatre tools figurent dans le manifeste canonique.

FIND est intentionnellement limité à la découverte sans contenu pour `knowledge`, `entity` et `work-item`; les résultats sont déterministes, bornés à 100 et ne portent ni contenu ni description. READ exige une adresse `vera://` canonique liée au projet en cours et relit l’objet par son service Core exact. READ batch est limité à 32 adresses. Les tests couvrent l’identité croisée, les bornes, la séparation FIND/READ, l’absence d’audit lors de la lecture, la CLI et une session MCP stdio. La validation atteint `27 passed` en cible et **`544 passed in 62.63s`** en régression intégrale.

> **Frontière conservée :** il ne s’agit pas encore d’une API universelle totale. La lecture d’autres ressources, `related`, le resume status/brief détaillé, les mutations mémoire/Front/handoff, les API evidence/work, les commandes de produit restantes et toute recherche de contenu sont exclus de M11-H. Preuve : `artifacts/m11_h_boot_find_read_2026-08-27.md`; mémoire : `MEM-DEC-183`; journal : `LOG-0237`.


### 11.7 M11-I — Lectures spécialisées Front, handoff et relation : `PASS`

`ReadService` couvre désormais les snapshots Front, les handoffs et les relations par `read` exact. Les nouveaux pointeurs `current_front` et `latest_handoff` ne sélectionnent jamais une version depuis le client : ils lisent le snapshot ou handoff le plus récent validé par le store. Ils sont exposés par CLI (`get-front`, `get-handoff`) et MCP (`mmu_get_front`, `mmu_get_handoff`) sans paramètres. `handoff` est ajouté aux types du contrat d’adressage VERA, et son payload JSON déjà validé est retourné de façon structurée. Les erreurs de lecture exacte sont normalisées sous une erreur API fermée.

Aucune de ces ressources ne rejoint FIND : celui-ci reste une découverte par titre des seules ressources déjà indexées. Les tests couvrent Front/handoff réels, relation déclarée, adresses canoniques, refus cross-project/inexistant, absence d’audit, commandes CLI et session MCP stdio. La cible atteint `30 passed` et la régression intégrale **`547 passed in 63.06s`**.

> **Frontière conservée :** assets, preuves/evidence, capabilities, gates, executions, symboles, profil, `related`, resume brief/status détaillé et mutations n’ont pas été généralisés par M11-I. Preuve : `artifacts/m11_i_specialized_front_handoff_relation_reads_2026-08-27.md`; mémoire : `MEM-DEC-184`; journal : `LOG-0239`.


### 11.8 M11-J — Lectures capability, execution et evidence : `PASS`

La lecture exacte de `capability`, `execution` et `evidence` est maintenant intégrée à `ReadService`. Les capabilities sont lues depuis leur registre immutable, les executions via `ExecutionService.get` (avec parsing strict de paramètres, environnement et résultat persistants), et les evidences via `EvidenceService.get` avec contenu, hash, verdict et statut d’admission associés. La sélection reste une unique adresse VERA canonique project-bound sur `vmmu read` et `mmu_read`; aucun record, verdict, hash ou payload ne vient du client.

Les assets restent intentionnellement sur la lecture dédiée `mmu_read_artifact`, qui contrôle hash et taille du contenu binaire. Les gates continuent d’utiliser leur évaluation dédiée, car elles sont des vues de gouvernance et non un accès table générique. La cible atteint `30 passed` et la régression intégrale **`549 passed in 63.57s`**.

> **Frontière conservée :** listing/history de preuves et evidences, assets au travers de READ, gates/work graph, symboles, profile, `related`, resume détaillé et mutations restent des lots distincts. Preuve : `artifacts/m11_j_capability_execution_evidence_reads_2026-08-27.md`; mémoire : `MEM-DEC-185`; journal : `LOG-0241`.


### 11.9 M11-K — Parcours relationnel `related` borné : `PASS`

Le Core fournit maintenant un parcours en largeur depuis une entité VERA canonique. La direction est fermée (`INBOUND`, `OUTBOUND`, `BOTH`), la profondeur est limitée à trois sauts et le nombre de voisins à cinquante. Les relations sont lues dans l’ordre d’identifiant, les voisins dédupliqués, et les cycles ne peuvent pas se propager. La réponse comporte des références compactes d’entités et d’arêtes, sans description ou contenu d’entité.

La CLI `related` et le MCP `mmu_get_related` délèguent au même contrat Core; le MCP n’accepte ni SQL, ni filtre libre, ni identité de projet, ni record. La validation atteint `27 passed` en cible et **`550 passed in 68.70s`** en régression intégrale.

> **Frontière conservée :** aucun traversal work/evidence, filtrage relationnel, pagination, recherche sémantique, mutation, capacité ou gate n’est introduit. Lectures de symbol/profile et historiques/listings restent à traiter séparément. Preuve : `artifacts/m11_k_bounded_related_traversal_2026-08-27.md`; mémoire : `MEM-DEC-186`; journal : `LOG-0243`.

## Addendum de suivi — M11-D-D1

| Sous-lot | Statut | Preuve et limite |
|---|---|---|
| `M11-D-D1` — Builder Dashboard de policy Gate existante | `PASS` dans le périmètre borné | Preview non mutateur, fraîcheur, confirmation, modes fermés et seuil `AT_LEAST` borné; `576 passed`, build React et tests Tauri passants. Ne crée pas de Gate, n’édite pas les exigences, ne produit pas verdict/admission/evidence et ne modifie pas une policy scellée. |
| `M11-D-D2` — Builder de structure de Gate | `NEXT` | À ouvrir séparément : work-item, evidence principale et exigences exactes avant scellement, avec preview/fraîcheur/confirmation/atomicité et sans policy ni verdict client. |

Le Dashboard global reste `PARTIAL`; l’édition directe du Project Profile demeure `NOT_ELIGIBLE` jusqu’à l’existence d’un protocole durable de rebind profile filesystem + metadata SQLite, rollback et reprise Doctor.
