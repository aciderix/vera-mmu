# M11-H — Boot, FIND et READ universels

**Date :** 2026-08-27
**Baseline :** `b71cde9984f472c4579e605fdcc2308db383f127` — M11-C clos, arbre propre, `541 passed`.
**Verdict :** `PASS` pour le périmètre M11-H ci-dessous. L’universalisation globale reste `NOT_DONE`.

## Objet et périmètre

M11-H établit une première surface Core de lecture universelle. Elle ne crée ni migration, ni schema, ni capacité, ni preuve, ni promotion, ni relation. Les opérations sont implémentées par `ReadService`, puis adaptées par la CLI et le MCP : la façade ne contient aucune requête SQL métier ni logique de résolution d’adresse.

| Opération | Surface livrée | Garantie principale |
|---|---|---|
| Boot | `ReadService.boot`, `vmmu boot`, `mmu_boot` | Retourne l’identité calculée du store, le Front et handoff persistants disponibles et l’état `NOT_ARMED`; aucun armement/acknowledgement de resume n’est tenté. |
| FIND | `ReadService.find`, `vmmu find`, `mmu_find` | Recherche seulement les titres de `knowledge`, `entity`, `work-item`; renvoie des références compactes, jamais `content` ni `description`. |
| READ | `ReadService.read`, `vmmu read`, `mmu_read` | Exige une adresse `vera://` canonique, dont `project_id` doit correspondre exactement à l’identité du store. |
| READ batch | `ReadService.read_batch`, `vmmu read-batch`, `mmu_read_batch` | Exige entre 1 et 32 adresses canoniques et conserve l’ordre explicite du client. |
| Manifeste | `TOOL_NAMES` étendu | `mmu_boot`, `mmu_find`, `mmu_read` et `mmu_read_batch` modifient le manifeste canonique et donc le `mcp_build_hash`. |

## Invariants exercés

> **FIND ≠ READ.** FIND utilise exclusivement les titres et retourne le type, l’identifiant, l’adresse et les attributs minimaux de classement. Le contenu et les descriptions ne sont accessibles que par READ, après validation de l’adresse exacte.

| Cas | Résultat vérifié |
|---|---|
| Recherche multi-ressources | Résultats ordonnés de manière déterministe par type de ressource et identifiant. |
| Adresse d’un autre projet | Refus `ReadApiError`; aucune résolution ou fallback inter-projets. |
| Adresse non canonique/inconnue | Refus fail-closed. |
| Requête FIND trop courte | Refus ; la borne est de 2 à 256 caractères canoniques. |
| Liste/ressource non autorisée | Refus ; le catalogue de ressources recherchables est fermé. |
| Batch trop grand | Refus au-delà de 32 lectures exactes. |
| Exécution READ Core | Aucun événement d’audit nouveau dans le test de non-mutation. |
| MCP | `mmu_boot` sans entrée ; tools de lecture sans `profile_path`, `project_id`, chemin, hôte, shell, verdict ou contenu fourni par client. |

Les ressources explicitement couvertes sont `knowledge`, `entity` et `work-item`. Les autres objets conservant déjà des services exacts (assets, preuves, relations, Front, handoff, capability, gate, execution) ne sont **pas** implicitement exposés par cette tranche. Ils exigent des contrats dédiés, notamment lorsque le contenu est binaire, soumis à admission, lié à une capacité ou dépendant d’un provider.

## Validation observée

```text
Contrat M11-H boot/FIND/READ :       3 passed in 2.04s
Cible CLI/MCP/M11-B/M11-C :         27 passed in 20.45s
Régression intégrale VERA :        544 passed in 62.63s
```

Les tests M11-H initialisent un projet documentaire et y créent une knowledge `OBSERVED`, une entity et un work item génériques. Ils vérifient le contenu absent de FIND, présent seulement dans READ, l’identité de projet, les bornes, la non-mutation du journal d’audit, la CLI et une session MCP stdio réelle.

## Limites et prochain travail

M11-H ne prétend pas livrer la totalité de l’API de la spécification : `mmu_get_front`, resume brief/status, related/traversal, append/update Front/handoff, preuves, work graph/gates, listing d’executions, alias de compatibilité, VCS multi-provider, Dashboard et intégrations hôtes restent des lots distincts. Les objets supportés par `ReadService` ne constituent pas une sémantique de recherche globale ou une indexation de contenu.
