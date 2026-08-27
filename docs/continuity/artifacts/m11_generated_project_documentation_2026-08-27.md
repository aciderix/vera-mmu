# M11 — Génération documentaire project-bound

**Verdict :** PASS pour la projection documentaire read-only des sources VERA canoniques.

`compile_project_documentation` produit de façon déterministe six documents : `MMU_SETUP.md`, `TOOLS.md`, `GATES.md`, `POLICIES.md`, `ARCHITECTURE.md` et `MAINTENANCE.md`. La projection agrège uniquement Profile validé, catalogues validés, rapport de couverture et identité du store actif. Elle ne lit ni source métier arbitraire, ni réseau, ni processus.

Le générateur refuse un Profile dont l’identité ne correspond plus au store ouvert. Sa compilation ne crée aucune transaction ni événement d’audit.

| Contrôle | Résultat |
|---|---|
| Contrat déterminisme / absence d’écriture / identité divergente | PASS |
| Régression Python intégrale | `596 passed in 64.40s` |
| `git diff --check` et scan frontière | PASS |

**Limites :** ce lot compile une projection en mémoire et non une écriture de documents dans le projet. L’export confirmé et la liaison UI/CLI/MCP restent des sous-lots distincts.
