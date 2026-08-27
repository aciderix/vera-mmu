# M11 — Documentation générée : surface CLI

**Verdict :** PASS pour la compilation documentaire project-bound via `vmmu documentation`.

La commande ouvre le store lié au Profile et renvoie le bundle déterministe de six documents, avec son hash. Si les catalogues référencés ne sont pas encore configurés, la projection conserve leur statut `NOT_CONFIGURED` dans les documents concernés plutôt que d’inventer une configuration ou d’échouer sur un Profile minimal valide.

| Contrôle | Résultat |
|---|---|
| Générateur, CLI et catalogues absents | `3 passed in 0.25s` |
| Régression Python intégrale | `597 passed in 65.16s` |
| Diff et scan frontière | PASS |

La commande est read-only : elle n’écrit aucun fichier de documentation. L’export atomique confirmé et les surfaces Dashboard/MCP restent explicitement ouverts.
