# M11 — Documentation générée : surface MCP

**Verdict :** PASS pour la projection documentaire project-bound sur une session MCP stdio réelle.

`mmu_get_documentation` ne prend aucun argument client. Il utilise le chemin de Profile effectivement lié au workspace du store, compile les six documents dérivés et retourne le bundle hashé. Une première hypothèse incorrecte d’emplacement `runtime/project.yaml` a été détectée par le test de session MCP puis corrigée : le Core n’infère plus ce chemin.

| Contrôle | Résultat |
|---|---|
| Session MCP stdio réelle, générateur et CLI | PASS |
| Régression Python intégrale | `598 passed in 67.00s` |
| `git diff --check` et scan frontière | PASS |

L’outil reste lecture seule, sans chemin ou contenu fourni par le client. L’export confirmé vers le projet demeure un lot séparé.
