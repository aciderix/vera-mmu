# M11-D Doctor Recovery — Reprise contrôlée de Profile

**Verdict :** PASS dans le périmètre de reprise Profile.

Le Doctor reste observationnel : il détecte un journal de rebind inachevé et le signale en échec `profile_rebind`. Le Dashboard peut ensuite seulement produire un preview de reprise; l’application exige confirmation, recalcule le journal et le hash de Profile, puis délègue au Core. Aucune réparation n’est implicite.

| Contrôle | Résultat |
|---|---|
| Tests ciblés Profile / bridge / Doctor | `16 passed in 2.49s` |
| Build React | PASS |
| Tests Tauri | `2 passed in 0.10s` |
| Régression Python complète | `593 passed in 64.28s` |
| `git diff --check` et scan frontière | PASS |

La reprise refuse tout journal multiple, illisible, symlinké ou divergent. Aucun champ client ne contrôle un chemin, une identité, le contenu de journal, une admission ou un verdict.
