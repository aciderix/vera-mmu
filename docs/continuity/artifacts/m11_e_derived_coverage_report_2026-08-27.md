# M11-E — Rapport de couverture dérivé

**Date :** 2026-08-27  
**Baseline :** `ba0ef4b` — M11-O livré localement, `557 passed`.  
**Verdict :** `PASS` dans le périmètre M11-E limité au rapport de couverture public.

## Portée

M11-E introduit `compile_coverage_report`, une projection déterministe de la surface publique VERA actuellement déclarée. Elle lit seulement les contrats statiques de Core : identité project-bound du store, `TOOL_NAMES` MCP, types FIND/READ et bornes d’historique. Elle ne scanne pas le workspace, ne lit pas le profile source, n’ouvre aucune transaction et ne transforme pas le rapport en attestation de parité ou de disponibilité hôte.

| Sortie | Garantie effective |
|---|---|
| Format | `vera-coverage-report/v1`, avec hash SHA-256 de la projection canonique. |
| Identité | `project_id`, hashes d’identité et version du profile issus du store actif seulement. |
| MCP | Liste triée des tools du manifeste fermé, incluant le rapport lui-même. |
| READ/FIND | Listes triées des ressources exactes et découvrables déjà déclarées dans le Core. |
| Historiques | Bornes effectives d’execution et d’evidence, sans inventaire des données stockées. |
| Manques | Dashboard, écriture documentaire générée, alias `mmu://`, VCS multi-provider, migration/parité ARET et preuve d’hôte réel sont explicitement listés. |
| CLI | `vmmu coverage <profile>` compile la même vue non mutatrice. |
| MCP | `mmu_get_coverage_report()` a un schéma vide; ni profile, chemin, hôte, secret, filtre ou identifiant ne vient du client. |

## Validation observée

```text
Contrat Core + CLI + MCP M11-E :         14 passed in 16.88s
Régression intégrale VERA :             559 passed in 71.67s
```

Le contrat vérifie le déterminisme, l’identité du projet, l’inclusion des surfaces `symbol` et historiques, la liste FIND, l’absence de chemin de workspace/profile et l’absence d’audit. Les transports CLI et MCP sont appelés réellement; le tool MCP est sans entrée.

## Limites

Ce lot ne livre pas l’ensemble des générateurs `MMU_SETUP`, `TOOLS`, `GATES`, `POLICIES`, `ARCHITECTURE` et `MAINTENANCE` demandé par la cible finale. Il ne calcule pas des pourcentages de couverture métier, ne valide aucun runtime hôte, ne résout ni alias `mmu://`, ni VCS, ni migration/parité ARET. Le rapport rend ces limites visibles; il ne les transforme pas en conformité.
