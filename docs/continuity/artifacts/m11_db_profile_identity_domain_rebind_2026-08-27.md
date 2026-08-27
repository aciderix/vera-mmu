# M11-D-B2 — Rebind structurel d’identifiant et domaine

**Verdict :** PASS pour les mutations structurelles `project.id` et `project.domain` sans déplacement physique du workspace ou du runtime.

Le preview inclut les identités avant/après et exige les quatre champs explicites `projectId`, `projectName`, `projectDomain` et `projectDescription`. Le bridge refuse tout champ de storage, workspace, catalogue, policy ou chemin. Après confirmation et contrôle de fraîcheur, le Core réaligne l’identité SQLite et les adresses dérivées utilisent le nouvel identifiant de projet.

| Contrôle | Résultat |
|---|---|
| Core / bridge ciblés | `15 passed in 1.42s` |
| Build React | PASS |
| Tests Tauri | `2 passed in 0.10s` |
| Régression Python intégrale | `595 passed in 64.98s` |
| Diff et scan frontière | PASS |

**Limites :** `workspace`, `storage.memory_dir`, `storage.sqlite_file`, `storage.artifacts_dir` et catalogues restent des migrations physiques de runtime distinctes. Elles ne sont ni masquées ni autorisées par ce lot.
