# Registre de clôture M4 — Domain Pack ARET et compatibilité démontrée

> **Statut :** `ACTIVE` — M4 reste `IN_PROGRESS`.
>
> **État factuel au 26 août 2026 :** M4.1–M4.15 sont `PASS` dans leurs contrats bornés. Le sous-lot M4-A ajoute un resolver runtime read-only avec policy WAL/SHM fail-closed, un ledger Core générique append-only/idempotent, une conformité profonde read-only de la table `component` et une autorisation explicite de page qui importe via ce ledger. La page réelle baseline de 17 composants a été importée dans un store VERA temporaire avec 17 liens de ledger, replay sans écriture, zéro evidence et zéro proof link. Ces faits **ne valent ni compatibilité ARET complète, ni parité, ni M4.EXIT**.
>
> **Source de dérivation :** spécification finale, sections 37–45, 50–58 et annexe B ; matrice C01–C16 ; état M4 publié et M3 terminal. [1] [2] [3]

## 1. Finalité et règle de lecture

Ce registre est la liste contrôlable des gates restant à satisfaire avant d’écrire `M4 = PASS`. Il ne remplace pas la matrice de découplage : il transforme ses couplages en résultats testables, en préconditions, en preuves attendues et en verdicts interdits. Son objectif n’est pas de planifier une réécriture générale, mais de rendre impossible une clôture par ambiguïté.

> Une gate est satisfaite seulement par une exécution réelle, reproductible et archivée qui couvre le contrat annoncé. Une revue de code, une sortie déclarative, une fixture isolée ou un import réussi ne suffit pas à établir la parité.[1]

| Terme | Signification dans ce registre |
|---|---|
| `PASS borné` | Le contrat d’un lot isolé a été exécuté et validé ; aucun périmètre non couvert n’est inféré. |
| `DONE` | L’abstraction, les tests de parité, les invariants et l’absence de dépendance ARET du Core sont démontrés pour une ligne C donnée. [2] |
| `BLOCKED` | Une précondition matérielle ou une evidence est absente. Le statut ne peut pas être converti en `PASS`. |
| `UNKNOWN` | La comparaison requise n’a pas été exécutée ou ne dispose pas de preuve suffisante. |
| `M4.EXIT` | Verdict global autorisé uniquement lorsque toutes les gates `M4-EXIT-*` sont `PASS`, sans gate `BLOCKED` ou `UNKNOWN`. |

## 2. Point de départ certifié et non-déduction

| Élément | Fait actuellement démontré | Ce qui ne peut pas en être déduit |
|---|---|---|
| Baseline source | Snapshot SQLite ARET V1 hashé, manifesté, lu en lecture seule et lié à un dépôt Git propre au commit de référence. | Origine distante/signature, cohérence WAL complète, ni comportement runtime/MCP. |
| Chaîne `component` | Préparation → attestation → identité Git → manifeste SQLite → conformité profonde `component` → page raw → préflight → projection → autorisation de page → ledger Core idempotent → audits ; page baseline de 17 records importée dans un store VERA temporaire avec replay sans écriture. | Cohérence WAL/runtime, import effectif de sources multi-pages, migration des liens ou de toute autre table, compatibilité et parité. |
| M4.15 | Autorisation explicite liée, recheck de collision, création atomique type+entities par le Core, audits `ENTITY_TYPE_REGISTERED`/`ENTITY_CREATED`, rollback sur conflit, état `IMPORTED_NO_PROMOTION`. | Merge, preuve, admission, `PROVEN`, rollback d’un import déjà committé, import dans ARET, ou parité ARET. |
| Core VERA | Core générique sans import du pack ARET ; M1–M3 clos dans leurs contrats. | Compatibilité legacy ; M3 ne doit pas être rouvert. |
| Wall | `MEM-WALL-001` : oracles/toolchain ARET non disponibles pour une exécution de parité. | Aucun `SKIPPED`, `UNKNOWN` ou test synthétique ne permet d’affirmer C07/C08 ou M4.EXIT. |

## 3. Gating obligatoire de M4 — registre exhaustif

Les numéros ci-dessous sont des **gates de clôture**, pas des autorisations d’élargir le write-path. Chaque sous-lot doit conserver le rituel baseline → tests-first → patch minimal → tests ciblés/complets → scans → roue isolée → diff → mémoire/journal → commits fonctionnel et documentaire séparés.

| Gate | Couplages | Livrable vérifiable restant | Preuve minimale d’acceptation | Dépendances et état |
|---|---|---|---|---|
| `M4-EXIT-01` Source admission et identité | C01, C02, C16 | Résolveur runtime ARET V1 borné : `ARET_MEMORY_DIR`/layout par défaut, politique de chemin, identité source, cohérence snapshot/WAL et cycle d’attestation. | Tests read-only de chemin, override, symlink/traversal, WAL/checkpoint selon policy, snapshot stable avant/après ; échecs bruyants et sans écriture source. | Attestation/Git/hash de snapshot et lecture immutable sont prouvés. Le resolver explicite et le refus des sidecars WAL/SHM sont prouvés ; rattachement du resolver override à toute la chaîne d’import et cycle d’attestation complet **restent requis**. |
| `M4-EXIT-02` Conformance profonde du schéma source | C03, C04, C05, C16 | Manifeste V1 étendu aux colonnes, contraintes, index, triggers, séquences, FTS et sémantiques nécessaires à chaque import. | Fixtures portant divergence de colonne/contrainte/index/trigger ; rapport de conformité hashé ; refus avant toute écriture VERA. | Colonnes/ordre/nullabilité/PK/default de `component` sont prouvés ; contraintes profondes et tables restantes **restent requis**. |
| `M4-EXIT-03` Import `component → entity` complet et réexécutable | C03, C16 | Contrat de pagination totale, ledger de batch/import, idempotence sûre, provenance de lot, post-validation, audit de bout en bout et stratégie explicite de non-fusion. | Import multi-pages ; stop/reprise ; second passage ; conflits préexistants et courses ; rollback complet ; conservation exacte des IDs/champs/métadonnées ; aucune écriture ARET. | Ledger Core append-only, page initiale/suivante, idempotence, collision/rollback, audit et import baseline 17 records sont prouvés ; conformance multi-pages source et post-validation exhaustive **restent requis**. |
| `M4-EXIT-04` Import `function_symbol → symbol` | C04, C16 | Lecteur V1 borné, projection vers `symbol`, liaison exacte aux entities importées, unicité et provenance source. | Tests source/cible de colonnes, parent manquant, unicité, pagination, conflit, rollback et reprise ; comparaison de cardinalité et liens. | Mapping M4.5 uniquement ; **non commencé**. |
| `M4-EXIT-05` Import `brick → work_item` | C05, C16 | Lecteur V1 borné, projection de statut/type/priorité/milestone/platforme/parent et liens, avec provenance et politique de statut explicite. | Tests de tous statuts, hiérarchie, ordre roadmap, liens component, cycles/parents impossibles, rollback/reprise et comparaison de cardinalité. | Mapping M4.5 uniquement ; **non commencé**. |
| `M4-EXIT-06` Migration des données et invariants associés | C03–C05, C16 | Contrats isolés pour `knowledge`, `knowledge_source`, tags, relations, proofs/proof links, assets/associations, audit, front, séquences, métadonnées et ledger de migration. | Pour chaque table : mapping versionné, provenance `source_type/repository/revision/import_batch_id`, règles de conflit/non-merge, FK/cycles, cardinalité, no-loss, append-only, refus cross-project et rollback. | Aucun import hors `component` M4.15 ; **non commencé**. |
| `M4-EXIT-07` Preuves et statut épistémique | C16 | Règles d’import des evidence/proofs/proof links, admissibilité et ségrégation avec knowledge, sans raccourci vers `PROVEN`. | Fixtures `PASS/FAIL/ERROR/SKIPPED/UNKNOWN`, HMAC/policy si requis, provenance et liens exacts ; démonstration qu’aucun import n’écrit `PROVEN` sans chaîne admissible. | M4.15 garantit zéro promotion ; **reste requis**. |
| `M4-EXIT-08` Pack capabilities ARET | C06 | Catalogue déclaratif du pack : capacités, paramètres, policies, dépendances, artifacts, validators et versions ; aucun hardcode ARET dans le Core. | Snapshot déterministe du catalogue ; refus de capability/paramètre inconnu, timeout/policy/artifact-hash et dry-run ; scan Core anti-ARET. | M3 fournit le moteur fermé ; pack ARET **non commencé**. |
| `M4-EXIT-09` Oracles et validators ARET réellement exécutables | C07 | Adaptateurs ARET de runner/validator/oracle, normalisation exacte des verdicts et chaîne execution→evidence→validation→admission→proof→gate. | Exécution dans environnement de référence, scripts confinés, artefacts hashés, `SKIPPED ≠ PASS`, preuve/gate réelles et comparaisons baseline. | **`BLOCKED — MEM-WALL-001`** jusqu’à restauration vérifiable des oracles/toolchain. |
| `M4-EXIT-10` Toolchain, préflight et doctor ARET | C08 | Déclaration explicite des binaires/corpus/outils ARET, préflight et rapport de remédiation sans installation implicite. | Image de référence ou environnement restauré ; doctor compare disponibilité/versions/corpus, refuse les manques, produit `SKIPPED` explicite ; Core installable sans toolchain. | **`BLOCKED — MEM-WALL-001`** ; condition de déblocage obligatoire pour M4.EXIT. |
| `M4-EXIT-11` Playbook et instructions de compatibilité | C09, C12 | Contenu ARET packagé, validé, versionné/hashé, injectable sans mutation de mémoire ; doctrine Core distincte. | Contrôles des sections/taille/hash, injection de reprise, snapshots déterministes et aucun texte ARET dans une instance Core sans pack. | Artefact pack possible en M4 ; compilation/intégration effective dépend de M5. |
| `M4-EXIT-12` Surface MCP, aliases et runtime integration | C10, C11, C15 | Manifeste/aliases `aret_*`, adaptateur mono-racine ARET, hooks/resume et politique d’installation non polluante. | Schéma et classification de chaque outil, appels de compatibilité, sessions fresh/PostCompact/Stop, Resume Guard et refus d’identité/chemin invalides. | La plateforme génératrice est M5/M6 ; ces gates **bloquent néanmoins M4.EXIT** jusqu’à leur démonstration. |
| `M4-EXIT-13` VCS et bundles de compatibilité | C13, C14 | Adaptateur VCS et bundles V1/V2 avec checkpoint WAL, scope/policy, non-fusion, identité/profil/packs/hash et restauration. | Git/NoVCS, HEAD détachée, changements hors scope, WAL occupé, bundle altéré, import idempotent, identity mismatch et restauration baseline. | M1/M2 préparent des éléments ; **reste requis**. |
| `M4-EXIT-14` Suite de parité et conformance ARET | C01–C16 | Harnais exécutable qui compare baseline et pack VERA sur les comportements critiques, pas seulement la structure. | Suites source et cible, fixtures, snapshots, diff de surface MCP, imports répétables, no-loss/no-merge/no-cross-project, sécurité, roue/installation propre. | Impossible de conclure avec C07/C08 bloqués ; **reste requis**. |
| `M4-EXIT-15` Contrat public et décision de sortie | Tous | Rapport M4.EXIT, matrice mise à jour, états de parité, compatibilité, limites, migrations, guide opératoire et stratégie de dépréciation. | Aucun C pertinent `SPLIT/BLOCKED/UNKNOWN`; preuves référencées ; revue de diff, publication distante et arbres propres. | **Interdit** avant satisfaction de `M4-EXIT-01` à `M4-EXIT-14`. |

## 4. Macro-lots d’exécution autorisés

Le regroupement accélère les itérations, non les verdicts : chaque ligne de la section 3 conserve sa preuve propre. Un macro-lot n’est publié que lorsque toutes ses gates internes sont satisfaites ou lorsque le blocage est constaté et documenté sans ambiguïté.

| Macro-lot | Gates regroupées | Cohérence technique | Sortie exigée avant le lot suivant | État au 26 août 2026 |
|---|---|---|---|---|
| `M4-A` — admission et migration de composants | `M4-EXIT-01` à `M4-EXIT-03` | Même chaîne runtime → snapshot → schema → lecture → ledger → transaction → post-validation pour `component`. | Source stable/WAL contrôlé, conformité de colonnes, import paginé réexécutable/no-merge, ledger/provenance/audit et reprise démontrés. | `IN_PROGRESS` : runtime default/override borné et WAL/SHM fail-closed, ledger 033, conformité `component`, pages initiale/suivante, rollback/idempotence et baseline 17 records sont prouvés ; cycle d’attestation d’override et preuves multi-pages source/post-validation restent ouverts. |
| `M4-B` — objets structurels liés | `M4-EXIT-04` et `M4-EXIT-05` | `function_symbol` et `brick` sont les deux mappings structurels restants ; ils dépendent des components de `M4-A` et des mêmes politiques de batch/provenance. | Imports `symbol` et `work_item` sans perte, avec FKs/hiérarchie/statuts/liens, rollback et reprise. | `NOT_STARTED`. |
| `M4-C` — données sémantiques et invariants | `M4-EXIT-06` et `M4-EXIT-07` | Knowledge, provenance, relations, assets, audit, front et proof links exigent une décision unique de non-fusion, provenance de lot et barrières épistémiques. | Mappings déclarés table par table, no-loss/no-cross-project, append-only, HMAC/admissibilité et zéro raccourci `PROVEN`. | `NOT_STARTED`. |
| `M4-D` — capacités et contenu ARET | `M4-EXIT-08`, `M4-EXIT-09`, `M4-EXIT-10`, `M4-EXIT-11` | Catalogue, playbook, dépendances et exécutions ARET forment le contenu opérationnel cohérent du pack. Les oracles ne peuvent cependant pas être déduits du catalogue. | Catalogue/version/hash, playbook/hash, doctor et oracles réels dans un environnement de référence ; C07/C08 exécutables. | `BLOCKED` pour les oracles/toolchain par `MEM-WALL-001`; catalogue/playbook peuvent avancer séparément mais ne lèvent pas le blocage. |
| `M4-E` — compatibilité opérationnelle | `M4-EXIT-12` et `M4-EXIT-13` | Aliases, adapter/runtime, hooks, VCS et bundles concernent la session et la portabilité de la mémoire ARET. | Surfaces générées/testées, Resume Guard, policies, WAL, bundles et restauration V1/V2 comparés. | `WAITING_ON_M5_M6` : les plateformes génériques sont hors M4 mais leurs preuves restent des dépendances de M4.EXIT. |
| `M4-F` — parité et sortie | `M4-EXIT-14` et `M4-EXIT-15` | La parité compare les sorties de tous les macro-lots et fonde la seule décision M4.EXIT. | Harnais de comparaison exécutable, écarts expliqués/acceptés, C01–C16 `DONE`, `MEM-WALL-001` levée et audit M4.EXIT. | `NOT_ELIGIBLE`. |

> **Ordre strict :** `M4-A → M4-B → M4-C → M4-D → M4-E → M4-F`. `M4-D` et `M4-E` peuvent préparer leurs artefacts en parallèle conceptuel, mais ni leur verdict ni M4.EXIT ne peut contourner les sorties de `M4-A` à `M4-C`, la wall C07/C08 ou les dépendances M5/M6.

## 5. Règles transverses à chaque gate de migration

| Contrôle transversal | Exigence non négociable |
|---|---|
| Isolation de la source | ARET-MMU reste au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, worktree propre ; toute lecture est explicitement read-only et aucun store cible VERA ne se situe dans le worktree ARET. |
| Identité et provenance | Chaque record importé peut être rattaché au snapshot, au commit/révision, à la table et à l’ID source, au mapping versionné et au batch d’import ; les identités de projet ne sont jamais fusionnées. |
| Transactions et erreurs | Toute écriture VERA est atomique dans son lot, auditable, prévalidée et rollbackée sur conflit ; un batch committé n’est jamais supprimé silencieusement. |
| Non-fusion | Cible non vide, type/ID préexistant, mapping ambigu ou conflit de provenance doivent être refusés par défaut et consignés ; une évolution de politique exige un contrat séparé. |
| Épistémique | Importer des données ne crée pas de preuve et ne promeut pas `PROVEN`. Les verdicts `SKIPPED`, `UNKNOWN`, `ERROR` et `FAIL` restent non promouvables. |
| Sécurité | Pas de shell arbitraire, réseau implicite, lecture hors racines, secret en logs, SQL d’écriture brut du pack, ni contournement des policies/gates. |
| Reproductibilité | Un snapshot, un manifest, un mapping et une cible vide identiques donnent le même résultat et les mêmes hashes/audits attendus ; l’installation de roue isolée reste testée. |

## 6. Frontières M4, M5 et M6

M4 est propriétaire du **contenu ARET** : manifests, runtime adapter de compatibilité, mappings, données, catalogue de capabilities, dépendances/toolchain, playbook, aliases et harnais de parité. M5 est propriétaire de l’infrastructure générique qui compile les manifests en MCP/instructions/hooks/config. M6 est propriétaire de la CLI, de l’installation, de `doctor` et de l’expérience opératoire générique. Aucun lot M4 ne doit réimplémenter ces plateformes dans le pack.

Cependant, une dépendance de réalisation n’efface pas une condition de sortie : les gates M4 relatives aux outils, hooks, installation, doctor et compatibilité n’atteignent `PASS` qu’une fois que M5/M6 rendent leur exécution possible et que le pack ARET fournit les entrées et les comparaisons correspondantes. Il s’agit de **dépendances externes de M4.EXIT**, non d’un transfert de responsabilité qui permettrait de déclarer la compatibilité avant preuve.

| Domaine | Implémentation principale | Bloque M4.EXIT ? | Justification |
|---|---|---|---|
| Import/mapping/provenance/capabilities/toolchain ARET | M4 | Oui | C’est le contenu du Domain Pack et la compatibilité de données. |
| Tool Registry, instructions/hook/config compiler | M5 | Oui, pour C09/C10/C12/C15 | Les surfaces ARET doivent être exécutables et comparées, pas seulement décrites. |
| CLI, install, doctor, création de profile | M6 | Oui, pour C02/C08/C11/C13/C15 | La spécification exige un runtime vérifiable et une installation non polluante. |
| Conformance multi-domaines | M7 | Non pour la parité ARET ciblée ; Oui pour la Definition of Done globale | M4 exige ARET ; l’universalité multi-domaines est une sortie ultérieure du programme. |

## 7. Conditions exactes de `M4.EXIT`

Le verdict `M4 = PASS` est autorisé uniquement si les conditions suivantes sont simultanément vraies.

1. `M4-EXIT-01` à `M4-EXIT-15` sont `PASS`, avec leurs artefacts de comparaison, logs et commits publiés.
2. Chaque ligne C01–C16 pertinente à la compatibilité ARET est `DONE`, ou dispose d’un justificatif de non-applicabilité explicitement accepté dans la matrice. Une ligne `BLOCKED`, `SPLIT` ou `UNKNOWN` interdit la clôture.
3. `MEM-WALL-001` est levée par une exécution documentée dans un environnement de référence avec toolchain/oracles restaurés. C07 et C08 ont alors des verdicts exécutables `PASS`, jamais des substituts déclaratifs.
4. La suite de parité ARET compare les comportements critiques du baseline : FIND/READ, append-only, provenance, HMAC/evidence, `PROVEN` gating, pipelines, playbook, Resume Guard, hooks, bundles, VCS, runtime et MCP. [1]
5. Les imports V1 sont non fusionnels par défaut, reproductibles, audités, provenance-linked, sûrs face aux collisions/courses, et testés jusqu’aux limites des tables supportées.
6. Une roue VERA installée proprement exécute les contrats de compatibilité sans injecter de dépendance ARET dans le Core ; ARET source demeure inchangé et propre.
7. Le rapport final déclare séparément la compatibilité ARET prouvée, les domaines hors compatibilité et la Definition of Done globale, qui reste soumise aux jalons M5–M8.

## 8. Verdict actuel et prochain travail autorisé

| Verdict | État |
|---|---|
| M4.15 | `PASS borné` : premier import atomic autorisé de la page `component` baseline dans un store VERA temporaire ; zéro promotion ; 17 entities créées, 18 audits nouveaux. |
| M4-A extension | `PASS borné` pour le resolver runtime read-only et policy WAL/SHM, le ledger Core 033, la conformité read-only `component` et l’import de page explicite/réexécutable ; baseline 17 records, 17 liens de ledger, replay sans écriture, zéro evidence et zéro proof link dans un store temporaire. |
| M4 global | `IN_PROGRESS`. |
| Parité ARET | `UNKNOWN`. |
| C07 / C08 | `BLOCKED — MEM-WALL-001`. |
| M4.EXIT | `NOT_ELIGIBLE` jusqu’à satisfaction de toutes les gates de la section 3. |
| Prochain lot autorisé | Un unique contrat de migration qui ferme une partie de `M4-EXIT-01` à `M4-EXIT-07`, sans élargir implicitement l’autorisation M4.15 et sans rouvrir M3. |

## Références

[1]: ../../../upload/UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md "Spécification finale d’universalisation fournie — sections 37–45, 50–58 et annexe B"
[2]: ../DECOUPLING_MATRIX.md "Registre de découplage ARET-MMU → VERA-MMU — C01–C16"
[3]: UNIVERSALIZATION_WORKPLAN.md "Plan vivant — M4, frontières M5/M6 et discipline de preuve"
