# M11-D-A — Vue Dashboard d’état projet dérivée

**Date :** 2026-08-27  
**Baseline :** `97ee6fd` — M11-F-B livré localement, `561 passed`.  
**Verdict :** `PASS` dans le périmètre M11-D-A.

## Portée

M11-D-A relie le Dashboard Tauri existant à une nouvelle opération bridge de lecture `project.status`. Après initialisation VERA confirmée, l’interface affiche un état dérivé du Core : le nombre de tools MCP déclarés dans le rapport de couverture et le statut VCS local minimal. Cette vue ne devient pas une seconde source de vérité et elle ne donne ni filesystem, ni shell, ni VCS aux composants React.

| Contrat | Garantie effective |
|---|---|
| Bridge | `project.status` accepte exactement `{}` et réutilise le profile project-local déjà validé. |
| Données | Compose `compile_coverage_report(store)` et `ReadService(store).vcs_status()`; aucun chemin, secret, profile brut, remote ou donnée métier n’est retourné. |
| Frontend | `desktopApi.projectStatus()` passe uniquement par la commande Tauri `project_status`, qui ne reçoit aucun argument WebView. |
| État UI | Le statut d’initialisation est un état explicite, initialement faux et mis à vrai seulement après application confirmée réussie. |
| Affichage | Le panneau de vérification affiche VCS et nombre de tools MCP uniquement après initialisation; son actualisation est une lecture sans écriture. |
| Écriture | Preview/confirmation/staleness de l’initialisation et de l’installation restent inchangés. |

## Validation observée

```text
Bridge desktop Python :                  7 passed in 1.04s
Build React TypeScript / Vite :          PASS
Tests natifs Tauri / Rust :              2 passed in 0.14s
Régression Python intégrale VERA :       562 passed in 65.34s
```

La validation Tauri a requis un toolchain Rust stable récent, PyInstaller et les dépendances GTK/WebKit de build; le sidecar natif généré est ignoré par Git et n’est pas livré comme modification source. La première tentative a révélé l’absence de ces prérequis, qui ont été provisionnés avant la validation finale.

## Limites

Ce lot ne livre pas les builders visuels complets de Project Profile, capabilities ou gates, les six templates enrichis, un Dashboard web, l’exécution dans un hôte utilisateur réel, la migration/parité ARET, ni l’ensemble des documents dérivés. Il ajoute seulement une vue project-bound d’observation à l’interface Tauri existante.
