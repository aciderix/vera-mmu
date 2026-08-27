# Conception — migration physique Project Profile et runtime

**État :** `DESIGN_REQUIRED`, sans mutation produite.

Les changements `workspace.root`, `workspace.additional_roots`, `storage.memory_dir`, `storage.sqlite_file`, `storage.artifacts_dir` et catalogues ont une portée physique : ils modifient l’ancre de résolution, l’emplacement de la SQLite WAL, les artefacts et les fichiers de configuration. Ils ne peuvent pas être ajoutés au rebind d’identité courant comme une édition YAML.

| Étape exigée | Garantie minimale |
|---|---|
| Préflight | Ancienne/nouvelle racine confinées, sans symlink, chemins non chevauchants, cibles absentes ou identiques. |
| Preview | Plan complet de déplacements, hashes de profile et d’identité avant/après, inventaire des fichiers persistants. |
| Journal durable | Journal hors runtime déplacé, sauvegarde et état monotone avant le premier déplacement. |
| Transition | SQLite fermée, identité réalignée dans transaction auditée, profile préparé, renommages atomiques même filesystem seulement. |
| Reprise | Détection Doctor read-only; reprise confirmée qui achève uniquement l’état journalisé, refuse divergences et ne devine jamais une cible. |
| Validation | Ouverture du store au nouveau profil, WAL/intégrité/FK, hashes et audit, absence de source résiduelle. |

La résolution actuelle infère l’ancre uniquement quand `project.yaml` réside sous `.vera-mmu/`. Avant toute migration de `storage.memory_dir`, elle doit être généralisée avec une preuve de non-régression de cette inférence. Aucun déplacement ne sera implémenté avant cette fondation et ses tests d’interruption.


## Inventaire observé du runtime initialisé

Une initialisation canonique crée : `project.yaml`, `capabilities.yaml`, `gates.yaml`, `policies.yaml`, `agent-profiles.yaml`, `playbook.md` et `sync-policy.json` sous le runtime. Une migration physique doit inclure cet ensemble ainsi que SQLite, WAL/SHM et les sous-répertoires générés créés ultérieurement. Cet inventaire a été observé sur un projet temporaire initialisé par la CLI puis supprimé.
