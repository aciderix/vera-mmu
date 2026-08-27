# M11-C — Surface publique et Doctor composite

**Date :** 2026-08-27
**Baseline :** `d3b992f4c00ab62f154f97ab4c988e5d0ab7fbf7` — M11-C.1 enregistré localement, arbre propre, `538 passed`.
**Verdict :** `PASS` pour le périmètre M11-C défini ci-dessous. L’universalisation globale reste `NOT_DONE`.

## Objet et périmètre

M11-C termine les transports publics nécessaires aux primitives M11-B et ajoute un diagnostic composite de l’installation VERA. Le changement ne modifie ni le schéma, ni le mécanisme d’export/restauration/import déjà validé. Il ne démarre aucun serveur ou adapter, n’exécute aucune capability et n’écrit pas dans la mémoire pendant un diagnostic.

| Surface | Résultat livré | Contrat de sûreté |
|---|---|---|
| CLI | `vmmu bundle-export`, `vmmu bundle-restore`, `vmmu project-import` | Confirmations explicites, preview hashé et chemins confinés réutilisent les services M11-B. |
| MCP | Export bundle, preview/import documentaire et `mmu_doctor` | Les schémas sont fermés. `mmu_doctor` ne prend aucun argument; ni chemin, hôte, adapter, runtime, commande, contenu, statut ni provenance ne sont client-controlled. |
| Doctor Core | `diagnose_project(profile_path)` | Lit profile/catalogues et SQLite via une URI `mode=ro`; aucune initialisation, migration, transaction, audit, capability ou serveur MCP n’est lancé. |
| Doctor CLI | `vmmu doctor <project.yaml>` | Le rapport structuré est renvoyé; un contrôle `FAIL` entraîne un code de sortie `2`. |
| Manifeste MCP | `mmu_doctor` est ajouté à `TOOL_NAMES` | Toute dérive de cette surface change le manifeste canonique et son `mcp_build_hash`. |

## Contrôles du Doctor

Le rapport `vera-doctor-report/v1` contient les checks canoniques suivants : `project_identity`, `profile`, `workspace`, `catalogs`, `runtime`, `sqlite_integrity`, `migration_ledger`, `wal`, `artifact_store`, `resume`, `mcp_transport` et `vcs`.

Un état d’option légitime, notamment l’absence de VCS ou de fichiers d’artefacts externes, est rendu comme `INFO` ou `PASS` avec une explication. Une ambiguïté ou corruption est toujours `FAIL` avec une remédiation explicite. Le statut global est `FAIL` si et seulement si au moins un contrôle est `FAIL`.

> Le Doctor ne prétend pas attester un hôte agent réel, une configuration intégrée installée, une clé HMAC secrète, une parité ARET ou une exécution de capability. Ces vérifications nécessitent des providers/hôtes et des lots dédiés; elles ne sont jamais transformées en succès local.

## Scénarios de sûreté démontrés

| Scénario | Résultat vérifié |
|---|---|
| Projet VERA bootstrapé, sans Git ni artefact externe | `PASS`; l’absence de VCS/artefacts est distinguée d’une erreur. |
| Diagnostic répété | Hash SQLite et audit technique inchangés : le diagnostic ne mute ni ne migre. |
| Répertoire d’artefacts symlinké | `FAIL` explicite de `artifact_store`. |
| SQLite corrompu | `FAIL` explicite de `sqlite_integrity`, `migration_ledger` et `wal`. |
| `mmu_doctor` MCP | Tool présent, schéma d’entrée vide, rapport du projet déjà lié au serveur. |
| Manifest MCP | Tool Doctor inclus dans la liste canonique vérifiée. |

## Validation observée

```text
Doctor ciblé :                        3 passed in 2.17s
M11-B/M11-C CLI-MCP ciblés :          27 passed in 19.39s
Régression intégrale VERA :         541 passed in 64.78s
```

Les tests de non-mutation comparent le SHA-256 SQLite et les enregistrements d’audit avant/après diagnostic. Les tests négatifs exercent un artifact store symlinké et une base SQLite invalide. Les tests MCP réalisent une session stdio réelle.

## Limites et prochain travail

M11-C est clos pour le transport de bundle/import et le Doctor de santé Core. Les API universelles de boot/FIND/READ, les commandes CLI restantes, le Dashboard configurateur, la documentation dérivée/coverage, VCS multi-provider, migration/parité ARET et la campagne d’hôtes réels restent hors de M11-C et ne sont pas promus par ce verdict.
