# Audit de préconditions M4.EXIT — 26 août 2026

> **Verdict de cet audit : `NOT_ELIGIBLE`.** Cet artefact évalue les preuves locales disponibles et ne constitue ni une preuve de parité ARET, ni une clôture M4. Une gate n’est `PASS` que si son contrat de sortie complet est exécuté, reproductible et archivé.[1]

## Méthode

L’audit confronte l’état local après les commits M4-C/M4-D jusqu’à `7365ba8` au registre canonique M4. Les validations de code disponibles sont la suite locale à **391 tests et 21 sous-tests**, le contrôle de whitespace, le scan de confinement Core et les installations de roues isolées. Les imports et runs réellement observés sont limités à des cibles/runtimes temporaires sous `/tmp`; ils n’écrivent pas ARET.

| État | Interprétation appliquée |
|---|---|
| `PASS borné` | Une primitive ou un sous-contrat a été démontré, sans extension au périmètre de la gate. |
| `IN_PROGRESS` | Du code ou une evidence existe, mais les preuves de sortie de la gate restent incomplètes. |
| `BLOCKED` | Une dépendance externe obligatoire est absente; aucun substitut déclaratif ne peut la convertir en `PASS`. |
| `NOT_ELIGIBLE` | Verdict obligatoire tant qu’une gate est `IN_PROGRESS`, `BLOCKED` ou `UNKNOWN`. |

## Résultat gate par gate

| Gate | État audité | Preuve locale constatée | Écart qui interdit `PASS` |
|---|---|---|---|
| `M4-EXIT-01` | `IN_PROGRESS` | Runtime source borné, attestation Git/hash et refus WAL/SHM déjà exercés. | Conformance runtime opérationnelle complète et comparaison de compatibilité absentes. |
| `M4-EXIT-02` | `IN_PROGRESS` | Conformance explicite de `component`, `function_symbol` et `brick`; lecteurs knowledge/provenance hashés. | Contraintes, triggers, séquences, FTS et tables restantes ne disposent pas de conformance profonde complète. |
| `M4-EXIT-03` | `IN_PROGRESS` | Import temporaire, replay et post-validation de la page baseline des 17 components. | Série source exhaustive, conflits/courses et réconciliation complète ne sont pas démontrés. |
| `M4-EXIT-04` | `IN_PROGRESS` | 9 symbols importés en 3 pages, avec replay/post-validation. | Conflits/courses indépendants, réconciliation exhaustive et parité absents. |
| `M4-EXIT-05` | `IN_PROGRESS` | 13 work items importés en 5 pages, avec relation parent component et statut Core borné. | Lifecycle/Front, hiérarchie/cycles, conflits/courses et compatibilité absents. |
| `M4-EXIT-06` | `IN_PROGRESS` | 532 knowledge en 6 pages importées sans promotion; ledgers Core 035/036; provenance lue/projetée. | Attache réelle `knowledge_source`, tags, relations, lineage, proofs, audit, Front, assets et no-loss table par table ne sont pas prouvés. |
| `M4-EXIT-07` | `IN_PROGRESS` | Barrière sans `PROVEN`, evidence ni proof lors des imports knowledge. | Import/admissibilité des evidence/proofs/proof links, HMAC et verdicts complets absents. |
| `M4-EXIT-08` | `IN_PROGRESS` | Catalogue Pack fermé de neuf oracles, capabilities/policies immuables à la demande, schémas de paramètres, préflight et assets hashés sont testés. | Snapshot déterministe exhaustif, validators, versions de corpus et dry-run public du pack restent absents. |
| `M4-EXIT-09` | `IN_PROGRESS` | `EVIDENCE_ASSET` lie evidence→asset→execution. La matrice couvre `272/272 PASS`, `271/272 FAIL`, timeout/sortie inconnue `ERROR`, dépendance absente `SKIPPED`, format non promouvable `UNKNOWN` et asset altéré; seul `PASS` validé est admis. M5-A/B expose cette même matrice par client MCP stdio sous manifeste canonique vérifié. | Couverture Pack complète, registry/adapters de production et snapshots restent à livrer. Les scores Wine et `win32_winsock` sont des observations de Pack, non des critères du transport VERA. |
| `M4-EXIT-10` | `IN_PROGRESS` | Le doctor Pack réel est `READY` : commit/propreté, binaire SHA-256, neuf préflights et sandbox `unshare` sont mesurés sans installation. Un outil ou sandbox manquant dégrade/refuse le statut. | Image/corpus versionnés exhaustifs, Tool Registry/doctor M6, recette de remédiation et environnement de référence piloté par VERA restent requis. |
| `M4-EXIT-11` | `IN_PROGRESS` | Les documents de continuité sont versionnés. | Playbook ARET packagé, hashé, injecté et snapshoté manque; intégration dépend aussi de M5. |
| `M4-EXIT-12` | `BLOCKED — M5/M6` | Aucun faux alias ou hook n’a été introduit dans M4. | Plateforme MCP, aliases, Resume Guard et sessions opératoires exigent M5/M6. |
| `M4-EXIT-13` | `IN_PROGRESS` | Git local, identité source et lecture de snapshot sont contrôlés. | Adaptateur VCS/bundles V1/V2, checkpoint WAL et restauration sont absents. |
| `M4-EXIT-14` | `UNKNOWN` | Le harnais de transport VERA couvre les scénarios principaux d’un Pack ARET via services et vrai MCP sous manifeste vérifié, sans exiger qu’ARET réussisse localement. | Conformance VERA des imports et de l’ensemble de la matrice Pack, registry/adapters et compatibilités M5/M6 restent absents. La parité fonctionnelle intrinsèque ARET est une piste distincte. |
| `M4-EXIT-15` | `NOT_ELIGIBLE` | Registre, mémoire et journal déclarent explicitement les limites. | Les gates `01` à `14` ne sont pas toutes `PASS`; C01–C16 ne sont pas tous `DONE`; la publication et le rapport final de compatibilité ne peuvent pas être déclarés. |

## Conclusion de décision

La condition nécessaire de sortie exige que **toutes** les gates `M4-EXIT-01` à `M4-EXIT-15` soient `PASS`, sans `BLOCKED` ni `UNKNOWN`.[1] L’audit constate trois empêchements indépendants : les migrations sémantiques et structurelles sont encore partielles, la couverture contractuelle du Pack et de ses imports reste incomplète, et les surfaces registry/adapters/CLI/compatibilité/bundles M5/M6 restent à livrer. Le transport MCP de verdict sous manifeste vérifié est désormais démontré, mais ne clôture pas ces autres gates. Les scores obtenus par ARET dans un environnement donné ne sont pas des critères de transport VERA. La seule décision correcte est donc :

> **`M4.EXIT = NOT_ELIGIBLE` — aucune clôture, aucun claim de parité et aucune publication de sortie M4 ne sont autorisés.**

## Mise à jour d’observation — toolchain restaurée

La branche toolkit fournie a été construite au commit `7a0429790bb04d1ad3c1819449e906140ebf4513` avec un binaire SHA-256 `6ca52f0955266aeda31d235caacf0844e2516f41d67468632f2ddb1bb1e16a19`. Les logs, commandes, versions et hashes ont été préservés dans l’artefact d’exécution.[4] Le runner M4-D consomme désormais cette référence via un commit propre, un binaire externe attesté et un sandbox réseau. La chaîne universelle complète est démontrée pour un `difftest PASS` réel : validator asset/execution, admission stricte, proof HMAC et gate.[5] Cette information lève uniquement le constat factuel d’absence de source/toolchain et démontre le mécanisme; elle ne rend pas C07/C08 `PASS`, car doctor, couverture/parité et corpus Wine complet restent incomplets; elle ne lève ni l’échec Wine historique ni le blocage du corpus sandboxé complet.

## Références

[1]: ../M4_COMPLETION_REGISTER.md "Registre de clôture M4 — gates obligatoires et conditions exactes de M4.EXIT"
[2]: ../UNIVERSALIZATION_WORKPLAN.md "Plan vivant — frontières M4, M5 et M6"
[3]: ../../DECOUPLING_MATRIX.md "Matrice de découplage — C01 à C16"
[4]: aret_toolkit_oracle_execution_2026-08-26.md "Exécution contrôlée des oracles ARET restaurés — 2026-08-26"
[5]: m4d_universal_verdict_chain_2026-08-26.md "M4-D — chaîne universelle de verdict, admission, preuve et gate — 2026-08-26"
