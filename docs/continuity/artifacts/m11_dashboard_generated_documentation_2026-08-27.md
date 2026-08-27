# M11-D — Documentation générée dans le Dashboard

**Verdict :** PASS pour la consultation de la documentation project-bound dans la console Desktop.

Le bridge ajoute une opération allowlistée sans entrée, `project.documentation`. Tauri ne fait que déléguer au bridge stdio authentifié. La WebView affiche le bundle hashé dans un bloc inspectable et ne propose ni chemin de destination, ni export, ni modification de document.

| Contrôle | Résultat |
|---|---|
| Bridge, générateur, CLI et MCP ciblés | `17 passed in 10.34s` |
| Build React | PASS |
| Tests Tauri | `2 passed in 0.10s` |
| `git diff --check` | PASS |

L’affichage reste read-only. Les documents ne sont pas écrits dans le projet et cette absence reste un état explicite, non un export implicite.
