# Plan vivant d’universalisation de VERA-MMU

> **Statut :** actif — document de contrôle évolutif.
>
> **Dernière revue factuelle :** 26 août 2026 — M4.5 validé; M4 est `IN_PROGRESS`, les couplages restent `SPLIT` et la parité `UNKNOWN`.
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
| Révision VERA-MMU | `55d184b87f7242cf36bd45767df9825bfe5cf357` sur `main`, registre de mappings structurels ARET V1 M4.5 publié et vérifié. | `OBSERVED` | Journal `LOG-0132`. |
| Révision ARET-MMU de référence | `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4` sur `main`, arbre propre lors du contrôle terminal M3. | `OBSERVED` | Journal `LOG-0001`, `LOG-0070`. |
| Capacité actuelle | M1, M2 et M3 sont publiés dans leurs périmètres contractuels. M4.1–M4.4 décrivent adresse, runtime, schéma et profil V1; M4.5 déclare les trois mappings structurels explicitement revus, tous soumis à import séparé. | `OBSERVED` : migrations 001→032, `200 passed, 14 subtests passed`, wheels M4.1–M4.5 et frontières de pack validées. | Mémoire `MEM-STATE-077`; journal `LOG-0131`. |
| Exclusions actuelles | Aucun shell arbitraire, réseau implicite, accès fichier externe, runner autre que `NOOP`/`EVIDENCE_HASH`/`EVIDENCE_FIELDS`, validator métier ou oracle externe, quorum pondéré, expiration/fenêtre temporelle ou révocation de gate, pause/reprise/réouverture ou orchestration de lifecycle, CLI/MCP de production, importeur ARET, pack ARET fonctionnel au-delà des surfaces déclaratives M4.1–M4.5, ou dashboard. Le sous-ensemble de paramètres ne devient pas JSON Schema général; `CONFIRM` ne devient pas une confirmation interactive; HMAC ne couvre ni rotation/révocation/expiration ni algorithme alternatif; aucun runner ou policy ne devient admission/proof automatique. | `OBSERVED` | Mémoire `MEM-DEC-045`; journal `LOG-0115`. |
| Baseline M0.1 | Inventaire, hashes, tests, surface statique, hooks/reprise, bundle et bundle Git capturés dans `ARET_MMU_M0_1_BASELINE/`. | `OBSERVED` ; exécution exhaustive `UNKNOWN` | Journal `LOG-0006` ; mémoire `MEM-BASE-003`. |
| Wall active | Toolchain des oracles ARET indisponible dans l’environnement de baseline ; ne pas confondre `SKIPPED` et validation. | `BLOCKED` | Mémoire `MEM-WALL-001` ; journal `LOG-0006`. |
| Registre M0.2 | Seize couplages documentés avec sources, frontière Core/pack, stratégie et tests de parité ; C07/C08 restent bloqués par la toolchain. | `PASS` pour la cartographie ; parité `UNKNOWN` | [Matrice](../DECOUPLING_MATRIX.md) ; journal `LOG-0007`. |
| Lot suivant | M4 est ouvert. M4.1–M4.5 sont `PASS`; le prochain lot doit cibler une policy d’import ou une ressource mappée sous un contrat séparé. Aucun verdict ne clôture C01–C16, `MEM-WALL-001` ou la parité ARET. | `M4_IN_PROGRESS` ; `MEM-WALL-001` préservée | Journal `LOG-0131`; mémoire `MEM-STATE-078`. |

## 6. Roadmap de transformation et gates de sortie

| ID | Lot | Objectif borné | Gate minimale de sortie | Invariants principaux | État |
|---|---|---|---|---|---|
| `M0.1` | Freeze ARET | Figer commit, dépendances, schéma, tests, hooks, comportement MCP et bundle de référence. | Inventaire hashé et baseline reproductible ; écarts connus explicitement listés. | I001, I004, I010, I014 | `CAPTURED` ; exécution exhaustive `UNKNOWN` (wall M0.1-W001) |
| `M0.2` | Registre de compatibilité | Compléter la matrice de découplage par source, portée, test de parité et stratégie de migration. | Chaque couplage ARET est `TODO`, `BLOCKED` ou `SPLIT`, jamais implicite. | I014, I015 | `PASS` pour la cartographie ; 14 `SPLIT`, 2 `BLOCKED`, parités `UNKNOWN` |
| `M1` | Core d’identité | Project Profile validé, identité de projet avec fingerprint de workspace, workspace multi-racines/no-Git, runtime confiné et adressage `vera://`. | Tests de stabilité, URI canonique, traversal/symlink/lecteur Windows, no-Git, multi-repo ; wheel et CLI isolés ; scan anti-ARET. | I008, I009, I011, I012, I014, I015 | `PASS` pour les gates techniques ; parité ARET explicitement `UNKNOWN` |
| `M2` | **Universal Schema** fini | Livré : M2.1–M2.14 (substrate, entités/relations, knowledge/provenance/supersession, assets/associations, Symbol Registry, Work-Item Backbone et Capability/Execution Schema). Aucun lot M2 ne reste. | **M2.EXIT** : toutes les six ressources de la spécification M2 existent avec migrations vérifiées, services de persistance exacts et bornés, FKs/immuabilité/audit/rollback testés ; fresh install et upgrade 001→courant, tests complets, wheel isolé, scans anti-ARET/no-shell/no-network/no-`PROVEN` passent. La gate ne revendique ni parité ARET ni preuve métier. | I001–I006, I010, I011, I014, I015 ; frontière I004, I007–I008, I013 | `PASS` — M2.1–M2.14 et M2.EXIT `PASS`; parité ARET `UNKNOWN` |
| `M3` | Capability / Evidence / Gates | M3.1–M3.25 et M3.EXIT livrent et auditent le Core local fermé de capability/evidence/validation/admission/proof/gate/work graph/lifecycle. | Fresh 032, upgrade 001→032, chaîne complète, suite Core, scans de frontière, checksums et wheel isolée passent. Le verdict n’infère ni parité ARET ni fonctionnalités post-M3. | I004–I008, I013, I014, I015 | `PASS` — M3 borné terminé; C05/C06/C16 `SPLIT`, C07 `BLOCKED`, parité ARET `UNKNOWN` |
| `M4` | Pack ARET | M4.1 livre le lecteur `ARET://` V1 strictement canonique; M4.2 déclare le layout runtime; M4.3 inventorie le schéma applicatif; M4.4 compose ces contrats sous un profil fermé; M4.5 déclare trois mappings structurels explicitement import-gated; M4.6 prépare une seule demande `component→entity`, liée à une identité VERA, une empreinte source déclarée, un ID et un acteur, et marquée non exécutée/non attestée; M4.7 vérifie cette empreinte contre le seul snapshot V1 régulier attendu, sous une racine absolue/non liée; M4.8 lie cette attestation à une racine Git locale propre et au commit baseline attendu via trois requêtes Git fixes; M4.9 ouvre ce snapshot uniquement en SQLite read-only et vérifie migrations/tables applicatives contre le manifeste V1; M4.10 observe des pages raw `component` keyset-bornées; M4.11 lie demande, inspection et page à un préflight fail-closed; M4.12 projette ces pages en brouillons d’entity déterministes; M4.13 vérifie l’absence du type et des IDs cible dans un store VERA identitaire via `SELECT` uniquement. Enregistrement de type, création transactionnelle, rollback/audit/provenance effectifs, autres tables, pipelines, playbook, toolchain et parité restent à contractualiser séparément. | M4.1–M4.13 : surfaces déclaratives ou d’attestation/inspection/lecture/préflight/projection/contrôle bornées, Core sans dépendance pack, refus non-canonique, aucune écriture/import, suite Core et wheels. La parité ARET reste mesurée uniquement contre une baseline exécutable. | I002, I004, I006–I008, I015 | `IN_PROGRESS` — M4.1–M4.13 `PASS`; C01–C06/C16 `SPLIT`, parité `UNKNOWN` |
| `M5` | Compilateur MCP et adapters | Manifeste immuable, API stable, instructions/hook/config générés. | Même entrée = même `mcp_build_hash` ; doctor et snapshots passent. | I009, I012–I014 | `PLANNED` |
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
