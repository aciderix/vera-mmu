# M5-P — Adapter Antigravity à garde par invocation

**Date :** 2026-08-27  
**Statut :** `PASS` pour la chaîne contrôlée VERA ; **`NOT_RUN`** pour Antigravity réel  
**Commit fonctionnel :** `df03100`  
**Portée :** configuration **project-local** `.antigravity/settings.json` et garde d’une invocation identifiée.

## 1. Décision

M5-P fournit l’adapter `antigravity-v1` au-dessus du Core VERA. Il commence son cycle à `PreInvocation`, applique la garde à `PreToolUse`, observe `PostToolUse`, puis libère l’état à `Stop`. Le MCP stdio reste adossé à `DenyRuntimeAdapter` et ne présente que l’acquittement lifecycle.

La surface documentée Antigravity fournit des points d’extension d’invocation et d’outil, sans équivalent attesté à la restauration de contexte ou à la compaction. VERA n’en invente aucun.[1]

> La garantie est **`TURN_GUARD_HARD`** : les actions livrées à `PreToolUse` sont bloquées pendant une invocation identifiée jusqu’à l’acquittement validé. Ce n’est ni une mémoire de session durable, ni une garantie de reprise, ni une couverture des opérations qui n’atteignent pas ce hook.

| Composant | Réalisation | Exclusions |
|---|---|---|
| Runtime | `.vera-mmu/runtime/generated/antigravity-runtime.json`, bindings revalidés | Réseau, bootstrap, secrets, installation externe |
| Lifecycle | `PreInvocation`, `PreToolUse`, `PostToolUse`, `Stop` | `SessionStart`, `PreCompact`, `PostCompact` absents |
| MCP | `vmmu-antigravity-mcp` et seul acquittement VERA | Capability Pack, OAuth, serveur distant |
| Config | preview/fusion confirmée de `.antigravity/settings.json` | home, auto-trust, réglage global |

## 2. Commandes distribuées

| Commande | Effet | Écriture éventuelle |
|---|---|---|
| `vmmu-antigravity-stage --profile project.yaml --confirm` | Stage le runtime deny-by-default | Runtime projet seulement |
| `vmmu-antigravity-hook --profile project.yaml --event …` | Traite un événement JSON fermé | État lifecycle VERA projet |
| `vmmu-antigravity-mcp --profile project.yaml` | Démarre le MCP stdio d’acquittement | Aucune configuration host |
| `vmmu-antigravity-config --profile project.yaml` | Affiche le preview | Aucune |
| `vmmu-antigravity-config --profile project.yaml --apply-project --confirm` | Applique le preview vérifié | `.antigravity/settings.json` et reçu runtime |

La fusion garde les extensions tierces, mais refuse les JSON non objets, une configuration VERA divergente, un symlink, un preview périmé et une application non confirmée.

## 3. Preuve contrôlée et limites

Les trois tests M5-P couvrent staging, config non destructive, conflits, symlink, `PreInvocation` injectant le dossier, `PreToolUse` refusant avant acquittement, vrai client MCP stdio, autorisation après acquittement et `Stop` libérant la liaison. La suite VERA passe à `476 passed, 37 subtests passed`; compilation, scans de frontières et roue isolée à quatre commandes passent.

Aucun exécutable Antigravity n’est disponible dans l’environnement (`ANTIGRAVITY_PRESENT=NO`). Aucune installation, connexion ou écriture hors projet n’a été tentée. Le trust hôte, la consommation réelle des hooks et la couverture de toute action host restent donc `NOT_RUN`.

## Références

[1] [Google Antigravity — Hooks](https://antigravity.google/docs/hooks/)  
[2] [Google Antigravity — MCP](https://antigravity.google/docs/mcp/)
