# Audit de préconditions M4.EXIT — 26 août 2026

> **Verdict de cet audit : `NOT_ELIGIBLE`.** Cet artefact évalue les preuves locales disponibles et ne constitue ni une preuve de parité ARET, ni une clôture M4. Une gate n’est `PASS` que si son contrat de sortie complet est exécuté, reproductible et archivé.[1]

## Méthode

L’audit confronte l’état local après les commits `41594ba`, `88e56d5`, `f0aad88` et `873fad9` au registre canonique M4. Les validations de code disponibles sont la suite locale à **378 tests et 14 sous-tests**, le contrôle de whitespace, le scan de confinement Core et les installations de roues isolées. Les imports réellement observés sont limités à une cible temporaire sous `/tmp`; ils n’écrivent pas ARET.

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
| `M4-EXIT-08` | `IN_PROGRESS` | Moteur Core M3 fermé disponible. | Catalogue ARET déclaratif, snapshot déterministe et dry-run du pack absents. |
| `M4-EXIT-09` | `IN_PROGRESS` | La branche toolkit verrouillée a permis la construction du binaire et l’exécution externe hashée de huit scripts d’oracle ; plusieurs runs passent, mais `winediff` est à `255/264` et `winehash` reste partiel/non normalisé. | Capability ARET fermée, normalisation testée, evidence/admission/proof VERA et verdict exécutable complet manquent ; un `FAIL` Wine interdit `PASS`. |
| `M4-EXIT-10` | `IN_PROGRESS` | Les prérequis ont été installés explicitement dans l’environnement isolé et leurs versions, hashes et logs sont archivés ; le clone de référence est resté propre. | Tool Registry, déclaration de dépendances du pack, doctor M6 et environnement de référence piloté par VERA manquent. |
| `M4-EXIT-11` | `IN_PROGRESS` | Les documents de continuité sont versionnés. | Playbook ARET packagé, hashé, injecté et snapshoté manque; intégration dépend aussi de M5. |
| `M4-EXIT-12` | `BLOCKED — M5/M6` | Aucun faux alias ou hook n’a été introduit dans M4. | Plateforme MCP, aliases, Resume Guard et sessions opératoires exigent M5/M6. |
| `M4-EXIT-13` | `IN_PROGRESS` | Git local, identité source et lecture de snapshot sont contrôlés. | Adaptateur VCS/bundles V1/V2, checkpoint WAL et restauration sont absents. |
| `M4-EXIT-14` | `UNKNOWN` | Les oracles externes exécutables fournissent des observations positives partielles (`difftest`, transpile, `stdcall`, EH, `funcdiff`) et un échec strict Wine (`255/264`). | Le harnais de parité VERA couvre encore aucune chaîne admissible complète et les surfaces M5/M6 restent absentes ; les neuf divergences Wine ne sont ni normalisées ni acceptées. |
| `M4-EXIT-15` | `NOT_ELIGIBLE` | Registre, mémoire et journal déclarent explicitement les limites. | Les gates `01` à `14` ne sont pas toutes `PASS`; C01–C16 ne sont pas tous `DONE`; la publication et le rapport final de compatibilité ne peuvent pas être déclarés. |

## Conclusion de décision

La condition nécessaire de sortie exige que **toutes** les gates `M4-EXIT-01` à `M4-EXIT-15` soient `PASS`, sans `BLOCKED` ni `UNKNOWN`.[1] L’audit constate trois empêchements indépendants : les migrations sémantiques et structurelles sont encore partielles, les prérequis toolkit/oracles ont été restaurés seulement comme observations externes — avec un échec Wine strict à `255/264` — et les surfaces MCP/CLI/doctor/bundles dépendent de M5/M6. La seule décision correcte est donc :

> **`M4.EXIT = NOT_ELIGIBLE` — aucune clôture, aucun claim de parité et aucune publication de sortie M4 ne sont autorisés.**

## Mise à jour d’observation — toolchain restaurée

La branche toolkit fournie a été construite au commit `7a0429790bb04d1ad3c1819449e906140ebf4513` avec un binaire SHA-256 `6ca52f0955266aeda31d235caacf0844e2516f41d67468632f2ddb1bb1e16a19`. Les logs, commandes, versions et hashes ont été préservés dans l’artefact d’exécution.[4] Cette information lève uniquement le constat factuel d’absence de source/toolchain qui motivait `MEM-WALL-001`. Elle ne rend pas C07/C08 `PASS`, car la chaîne capability → evidence → admission → proof VERA et le doctor M6 n’existent pas encore ; elle ne lève pas non plus l’échec Wine observé.

## Références

[1]: ../M4_COMPLETION_REGISTER.md "Registre de clôture M4 — gates obligatoires et conditions exactes de M4.EXIT"
[2]: ../UNIVERSALIZATION_WORKPLAN.md "Plan vivant — frontières M4, M5 et M6"
[3]: ../../DECOUPLING_MATRIX.md "Matrice de découplage — C01 à C16"
[4]: aret_toolkit_oracle_execution_2026-08-26.md "Exécution contrôlée des oracles ARET restaurés — 2026-08-26"
