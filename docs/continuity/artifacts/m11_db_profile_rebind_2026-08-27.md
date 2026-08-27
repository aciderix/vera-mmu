# M11-D-B — Rebind contrôlé du Project Profile

**Verdict :** PASS dans le périmètre explicitement borné.

Le Dashboard autorise uniquement la modification du nom et de la description du Project Profile. Il obtient un preview non mutateur, contenant les hashes avant/après ainsi que les identités avant/après. Son application exige un preview bridge nonce-scopé, une confirmation explicite et un recalcul de fraîcheur.

La mutation est durablement récupérable. Avant la modification, le Core écrit une sauvegarde locale et un journal de rebind à permissions restreintes. Il aligne l’identité SQLite dans une transaction auditée puis remplace le Profile par écriture atomique. Une interruption entre les deux étapes laisse un journal détecté par Doctor; `recover_project_profile_rebind` termine uniquement la transition journalisée et refuse toute divergence ambiguë.

| Contrôle | Résultat observé |
|---|---|
| Tests ciblés rebind / bridge / Doctor | `17 passed in 2.59s` |
| Build React | PASS |
| Tests Tauri natifs | `2 passed in 0.10s` |
| Régression Python intégrale | `593 passed in 63.09s` |
| `git diff --check` | PASS |
| Scan frontière du rebind | PASS : aucun concept/outillage ARET, shell, processus ou réseau |

**Limites :** aucun identifiant de projet, domaine, workspace, chemin de storage, catalogue, policy, capability, gate, evidence, admission ou verdict ne peut être changé par ce builder. Doctor est observationnel : il signale le journal de rebind mais n’exécute jamais une réparation implicite. Toute récupération est une opération Core distincte et fail-closed.
