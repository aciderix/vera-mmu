# M5-Q — Adapter MCP générique sans automation lifecycle

**Date :** 2026-08-27  
**Statut :** `PASS` pour le fallback MCP contrôlé  
**Commit fonctionnel :** `00f6cee`  
**Portée :** tout client MCP stdio compatible ; aucune supposition de hooks, de session ou de compaction.

## 1. Décision

M5-Q fournit un mode `MCP_ONLY` pour les hôtes qui savent lancer un serveur MCP mais ne présentent aucune surface lifecycle attestée. Il stage un runtime project-bound, prévisualise/fusionne un seul serveur dans `.mcp.json` après confirmation, et lance une façade MCP réelle avec `DenyRuntimeAdapter`.

> **MCP disponible ne signifie pas lifecycle disponible.** Le client peut consulter le catalogue et appeler les outils publiés, mais le fallback ne fabrique ni identité de session, ni Resume Dossier, ni interception avant action, ni acquittement valide automatique.

| Surface | État M5-Q | Refus / limite |
|---|---|---|
| Serveur MCP | stdio, manifeste et instructions attestés | Pas d’URL, OAuth, réseau ou exécution Pack |
| `mmu_get_capability_catalog` | Accessible avec catalogue déterministe | Lecture du catalogue seulement |
| `mmu_run_capability` | Refusé par `DenyRuntimeAdapter` | Aucune capability ne devient exécutable |
| `mmu_acknowledge_resume` | Exposé mais refusé sans contexte lifecycle attesté | Pas de session ou hash choisi par le client |
| Config | `.mcp.json` project-local, preview puis confirmation | Pas de home, trust ou auto-approbation |

## 2. Commandes

| Commande | Action | Écriture |
|---|---|---|
| `vmmu-generic-mcp-stage --profile project.yaml --confirm` | Stage le runtime MCP-only | `.vera-mmu/runtime/` |
| `vmmu-generic-mcp --profile project.yaml` | Lance la façade MCP stdio | Aucune configuration hôte |
| `vmmu-generic-mcp-config --profile project.yaml` | Affiche le preview `.mcp.json` | Aucune |
| `vmmu-generic-mcp-config --profile project.yaml --apply-project --confirm` | Applique une unique entrée attestée | `.mcp.json` et reçu runtime |

Le preview et l’application refusent un runtime absent/altéré, JSON non objet, conflit du serveur VERA, symlink, preview périmé ou absence de confirmation.

## 3. Preuve contrôlée

Les tests red→green couvrent le staging confirmé, la conservation d’un serveur tiers, les conflits/symlinks, un vrai `ClientSession` MCP stdio, l’accès au catalogue, ainsi que les refus de `mmu_acknowledge_resume` sans contexte et de `mmu_run_capability`. La suite VERA atteint `479 passed, 37 subtests passed`; la roue isolée rend les trois commandes disponibles.

Ce mode n’attend pas de client spécifique : il est volontairement indépendant d’un host. Son contrat ne peut donc jamais être utilisé comme une preuve qu’un client a installé, trusted ou exécuté le serveur ; ces faits restent de la responsabilité de l’adapter ou de l’opération hôte correspondante.

## 4. Rapport de compatibilité

| Catégorie de client | Mode VERA admissible | Condition supplémentaire |
|---|---|---|
| Client MCP sans hooks | `MCP_ONLY` | Dossier/reprise traités par une procédure explicite ; aucune garde automatique |
| Client avec hooks sans post-compaction | Adapter dédié de type Gemini | Déclarer l’absence de réarmement post-compaction |
| Client avec invocation/tool hooks | Adapter dédié de type Antigravity | Borner la garde à une invocation |
| Client avec session, pré/post-tool et compaction | Adapter dédié de type Codex ou Claude | Prouver chaque événement sur le host réel |

## Références

[1] [Model Context Protocol — Specification](https://modelcontextprotocol.io/specification/2025-06-18)  
[2] [Model Context Protocol — Architecture](https://modelcontextprotocol.io/docs/learn/architecture)
