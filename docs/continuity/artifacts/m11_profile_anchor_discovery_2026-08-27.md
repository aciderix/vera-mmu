# M11 — Découverte d’ancre Project Profile

**Verdict :** PASS pour la découverte locale non ambiguë préparant les migrations physiques.

Le bridge accepte exactement un Profile régulier et non symlinké situé soit sous `.vera-mmu/project.yaml`, soit à la racine `project.yaml`. La présence de deux profils est refusée fail-closed. Cette évolution ne déplace aucun fichier, ne change aucune identité et n’ouvre aucun chemin client.

| Contrôle | Résultat |
|---|---|
| Bridge et workspace ciblés | `20 passed in 1.29s` |
| Régression Python intégrale | `600 passed in 65.23s` |
| Diff | PASS |

Cette fondation permet de concevoir une migration de runtime, mais n’est pas elle-même une migration physique ou un changement de stockage.
