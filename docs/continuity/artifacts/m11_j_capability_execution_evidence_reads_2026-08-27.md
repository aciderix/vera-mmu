# M11-J — Lectures Capability, Execution et Evidence

**Date :** 2026-08-27  
**Baseline :** `9f2aca153a7323a0e31d51ec5a753141ceb393dd` — M11-I livré localement, `547 passed`.  
**Verdict :** `PASS` pour le périmètre M11-J. L’universalisation globale et la couverture complète de chaque ressource restent `NOT_DONE`.

## Objet et périmètre

M11-J poursuit l’API Core de lecture exacte. Il couvre les enregistrements persistés de capabilities, executions et evidences, sans créer de recherche pleine, de promotion, de validation, de mutation, de capability supplémentaire, de preuve, de gate ou de provider. La lecture de contenu binaire d’asset demeure volontairement sur `AssetService.read` et `mmu_read_artifact`, qui conservent leur vérification hash/taille dédiée.

| Ressource | Exposition | Garantie |
|---|---|---|
| Capability | `ReadService.read(vera://…/capability/<id>)` | Retourne la déclaration immutable et ses schemas depuis `CapabilityService.get`. |
| Execution | `ReadService.read(vera://…/execution/<id>)` | Retourne l’enregistrement persistant, paramètres, environnement, timestamps, hash d’artefact et résultat via le nouveau `ExecutionService.get`. |
| Evidence | `ReadService.read(vera://…/evidence/<id>)` | Retourne l’evidence exacte, son verdict, statut d’admission, contenu canonique et `content_hash` via `EvidenceService.get`. |
| MCP / CLI | `mmu_read`, `vmmu read` déjà existants | L’adresse VERA exacte est l’unique entrée de sélection; le transport ne prend aucun record, contenu, statut, verdict, hash, environnement ou paramètre d’exécution. |
| Assets | `mmu_read_artifact` existant | Restent hors `ReadService` : la lecture binaire garde ses validations cryptographiques spécifiques. |
| Gates | `mmu_evaluate_gate` existant | Restent hors READ : une évaluation est une vue calculée avec une sémantique distincte, non une table exposée implicitement. |

## Contrat de sûreté

> **READ est exact et project-bound.** Toute adresse est d’abord parsée de manière canonique, puis le `project_id` est comparé à l’identité du store avant que le service spécialisé ne soit appelé. Toute ressource absente, incohérente ou non exposée est ramenée à une `ReadApiError` fermée.

| Cas vérifié | Résultat |
|---|---|
| Capability déclarée | Type, version et schemas sont lus depuis l’enregistrement Core exact. |
| Execution réelle | L’exécution NOOP est créée par capability contract + policy et relue avec ses paramètres/état persistants. |
| Evidence réelle | L’evidence est enregistrée via `EvidenceService` et relue avec son contenu et hash canonique. |
| Cross-project / absent | Refus avant résolution ou par erreur API fermée, sans fallback. |
| Non-mutation | Le journal d’audit est identique avant/après trois lectures exactes. |
| MCP | `mmu_read` accepte seulement `address`; aucun payload de record ne peut être injecté par le client. |
| Assets/Gates | Ne sont pas réinterprétés ou dupliqués dans la nouvelle API. |

## Validation observée

```text
Contrat M11-J capability/execution/evidence :  2 passed in 2.05s
Cible evidence/execution/capability/MCP :      30 passed in 17.85s
Régression intégrale VERA :                   549 passed in 63.57s
```

## Limites et suite

Cette tranche ne livre ni `mmu_get_proofs`, ni history/listing d’evidences, ni traversal `related`, ni lecture d’assets hors service hashé, ni lectures de symboles/profile, ni VCS multi-provider, ni Dashboard, ni migration/parité ARET ou hôtes réels. Les gates restent accessibles exclusivement par leur évaluation persistante déjà exposée; leur listing/génération exige un contrat de work graph distinct.
