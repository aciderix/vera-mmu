# M6-C — Initialisation guidée et Agent Profiles déclaratifs

**Date :** 2026-08-27  
**Statut :** `PASS` pour la préparation project-local contrôlée ; agents réels et dashboard `NOT_RUN` / `NOT_DELIVERED`  
**Commit fonctionnel :** `5cd679a`

## Objet

M6-C permet de créer, pour un répertoire existant explicitement choisi, une configuration VERA minimale **sans modifier le code métier**. Il ajoute un registre de profils d’agents déclaratifs et l’opération :

```bash
vmmu init-project <racine> --template <domaine> --project-id <id> --project-name <nom>
```

La commande ne crée rien par défaut : elle retourne un preview. L’écriture des fichiers exige `--apply --confirm`.

## Sorties project-locales

| Fichier | Rôle | Source de vérité |
|---|---|---|
| `.vera-mmu/project.yaml` | Identité, domaine, workspace et stockage VERA | Project Profile revu par le projet |
| `.vera-mmu/playbook.md` | Doctrine universelle proposée à adapter | Vue projet, non une preuve |
| `.vera-mmu/agent-profiles.yaml` | Profils d’agents disponibles, événements et limites déclarés | Registre VERA validé |

Les templates disponibles sont `software`, `data`, `research`, `documentation`, `game` et `hardware`. Ils sont des propositions de domaine, non une capacité autorisée, une policy, une gate ou une conclusion prouvée.

## Agent Profiles

Un `AgentProfile` déclare seulement une identité, un adapter déjà allowlisté, un mode, une couverture maximale et des événements réellement supportés. Il ne contient ni commande, ni chemin libre, ni module à charger, ni secret, ni code exécutable.

| Profil | Niveau déclaré | Limite conservée |
|---|---|---|
| Claude Code local | `COMPACTION_AWARE` | Le comportement dépend toujours du host réel. |
| Claude Code cloud | `CLOUD_STAGED_NOT_LIVE` | Trust et observation web réels restent distincts. |
| Codex | `PARTIAL_LOCAL_TOOLS` | Les outils non interceptés restent hors garde. |
| Gemini CLI | `TOOL_GUARD_NO_POST_COMPACTION` | Aucun réarmement post-compaction n’est déclaré. |
| Antigravity | `TURN_GUARD_HARD` | Pas de session durable inventée. |
| MCP générique | `MCP_ONLY` | Aucune automatisation lifecycle. |

## Refus et non-destruction

L’initialisation refuse une racine ou une cible symlinkée, un template absent, une identité mal formée, un preview altéré, une absence de confirmation et toute cible préexistante dont le contenu diverge. Elle est idempotente seulement lorsque les trois contenus attendus sont identiques.

Les opérations ne consultent aucun réseau, secret, home user-scope ni client hôte, et ne lancent aucun processus. Elles ne prouvent donc ni la disponibilité d’un agent, ni une installation hôte, ni un fonctionnement de hook réel.

## Validation contrôlée

Trois tests rouges ont précédé l’implémentation. Les tests verts couvrent le registre et ses champs interdits, la borne de couverture par adapter, la stabilité du preview, l’absence d’écriture avant application, la confirmation, l’idempotence, le refus de divergence et de symlink. La suite complète atteint `488 passed, 37 subtests passed`; compilation, scans de frontière et roue isolée passent.

> M6-C rend le futur Dashboard possible : il pourra proposer et éditer ces mêmes objets. Il ne lui donnera pas le droit de créer une configuration ou d’activer un adapter hors des validations du Core.
