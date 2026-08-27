# M11-F-B — Diagnostic VCS local minimal

**Date :** 2026-08-27  
**Baseline :** `781a3a7` — M11-F-A livré localement, `560 passed`.  
**Verdict :** `PASS` dans le périmètre M11-F-B.

## Portée

M11-F-B introduit `inspect_vcs`, une observation Core transport-neutral strictement locale. Elle ne lance aucune commande VCS et ne connaît ni revision, branche, remote, chemin ou données de dépôt. Le résultat est disponible par `ReadService.vcs_status`, `vmmu vcs-status <profile>` et `mmu_get_vcs_status()` inscrit au manifeste MCP.

| Contrat | Garantie effective |
|---|---|
| États | `GIT/OBSERVED` si `.git` project-local est un répertoire régulier; `NONE/NO_VCS` si absent. |
| Refus | Marqueur `.git` symlinké ou non-répertoire : refus fermé `VcsError`. |
| Source | Seul le marqueur sous `workspace.project_root` est observé. |
| Données exclues | Aucun chemin retourné, revision, branche, remote, log, utilisateur, statut de fichiers ou contenu de configuration. |
| Effets | Aucun `subprocess`, réseau, transaction SQLite, audit, commit, push, pull ou mutation filesystem. |
| MCP | `mmu_get_vcs_status` n’accepte aucune entrée client et appartient au manifeste hashé. |

## Validation observée

```text
Contrat Core + manifeste/CLI/MCP :       13 passed in 14.56s
Régression intégrale VERA :             561 passed in 67.71s
```

Les tests contrôlent no-VCS, Git marker régulier, symlink ambigu refusé et l’absence d’audit. Les vérifications de manifeste et de transport sont incluses dans la cible; le lot ne lance pas Git.

## Limites

Il ne s’agit pas encore d’un `VersionControlProvider` multi-implémentations. Mercurial, SVN, identification de revision, états/staging, log, remote, sync, commit/push et VCS legacy restent hors lot. La synchronisation Git project-local existante n’est pas modifiée.
