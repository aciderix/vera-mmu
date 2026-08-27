# M5-N — Adapter Codex à garde lifecycle bornée

**Date :** 2026-08-27  
**Statut :** `PASS` pour la chaîne contrôlée VERA ; **`NOT_RUN`** pour une session Codex réelle  
**Commit fonctionnel :** `588c886`  
**Portée :** Codex CLI/IDE, configuration **project-local** `.codex/` seulement.

## 1. Décision

M5-N installe un adapter hôte `codex-v1` au-dessus du Core VERA sans modifier le Core, les capacités Pack ni la sémantique de verdict. Il délivre un runtime staged et hashé, des handlers pour `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `PostCompact` et `Stop`, un serveur MCP stdio `DenyRuntimeAdapter`, et une configuration project-local confirmée.

> La garantie est **`PARTIAL_LOCAL_TOOLS`**, non une garantie de blocage totale. La documentation Codex indique que certains outils hosted et chemins spécialisés n’empruntent pas le parcours des hooks. Le système n’étend donc jamais le verdict de la garde aux outils non interceptés.[1]

| Composant | Réalisation M5-N | Garantie | Exclusions |
|---|---|---|---|
| Runtime | `.vera-mmu/runtime/generated/codex-runtime.json`, binding manifeste revalidé | Staging atomique après `--confirm` | Pas d’installation, réseau, bootstrap ou secret |
| Lifecycle | Session project-bound, dossier, garde et réarmement Pre/PostCompact | `HARD` pour les événements et tools locaux effectivement interceptés | Aucun contrôle des hosted tools |
| MCP | `vmmu-codex-mcp --profile …`, seul `mmu_acknowledge_resume` exposé à l’hôte | Aucune capability Pack exécutable | Pas de serveur distant ni d’OAuth |
| Hooks | `.codex/hooks.json`, JSON stdin/stdout | Injection de contexte et blocage local selon le contrat Codex | Hooks hôte à reviewer/truster |
| Config | `.codex/config.toml`, table `[mcp_servers."vera-mmu-…"]` | Ajout sans écraser les tables tiers | Pas de TOML réécrit/reformaté hors append contrôlé |

## 2. Contrat de configuration

Le preview ne modifie aucun fichier :

```bash
vmmu-codex-config --profile project.yaml
```

L’application project-local est distincte et requiert une confirmation explicite :

```bash
vmmu-codex-config --profile project.yaml --apply-project --confirm
```

La configuration MCP est ajoutée dans la table Codex `mcp_servers` et limite le serveur VERA à `mmu_acknowledge_resume` avec `default_tools_approval_mode = "prompt"`. VERA ne génère ni auto-approbation (`approve`), ni transfert d’environnement, ni token.[2]

Les hooks de projet Codex ne s’exécutent qu’après trust du projet et revue/trust de leur définition par le host. Cette approbation est une opération explicitement laissée au host/utilisateur : M5-N ne lit ni n’écrit `~/.codex/`.[1] [3]

## 3. Refus fail-closed

| Condition | Réaction |
|---|---|
| Runtime absent, périmé ou altéré | Refus avant hook/MCP/configuration |
| Staging ou configuration sans `--confirm` | Refus sans écriture |
| `.codex`, `hooks.json`, `config.toml` ou état runtime symlinké/non régulier | Refus sans écriture |
| Hook VERA Codex préexistant divergent | Refus |
| Table `mcp_servers.<id>` VERA divergente ou autre entrée `vmmu-codex-mcp` | Refus |
| Session inconnue ou différente du binding actif | Refus |
| Client MCP tentant une capability | Refus par `DenyRuntimeAdapter` |

## 4. Preuve contrôlée

Le test `tests/test_codex_adapter.py` valide la chaîne suivante avec un vrai processus MCP stdio :

1. staging confirmé sans création de `.codex/` ;
2. preview déterministe et conservation de hooks/TOML tiers ;
3. refus de cible symlinkée et de configuration VERA divergente ;
4. application project-local seulement après confirmation ;
5. `SessionStart` injecte le Resume Dossier ;
6. `PreToolUse` bloque une action locale couverte ;
7. `mmu_acknowledge_resume` est appelé via le client MCP stdio réel ;
8. `PreToolUse` laisse ensuite passer ;
9. `PostCompact` réarme la garde et l’action est de nouveau bloquée.

La présence du client Codex n’a pas été constatée dans l’environnement de validation (`CODEX_PRESENT=NO`). Aucune installation ni connexion n’a été tentée. Il s’agit donc d’une preuve de compatibilité VERA avec le contrat documenté, **pas** d’une preuve d’exécution réelle par Codex.

## 5. Commandes distribuées

| Commande | Action | Écriture |
|---|---|---|
| `vmmu-codex-stage --profile project.yaml --confirm` | Compile et stage le runtime deny-by-default | `.vera-mmu/runtime/` uniquement |
| `vmmu-codex-hook --profile project.yaml --event …` | Traite un unique événement JSON | État lifecycle runtime seulement |
| `vmmu-codex-mcp --profile project.yaml` | Lance le MCP stdio d’acquittement | Aucune config hôte |
| `vmmu-codex-config --profile project.yaml` | Affiche le preview project-local | Aucune |
| `vmmu-codex-config --profile project.yaml --apply-project --confirm` | Applique le preview vérifié | `.codex/` projet et reçu runtime |

## 6. Gate live à venir

La future preuve Codex réelle exige un client Codex identifié, un dépôt test jetable, la revue/trust host visible, puis l’observation des événements `SessionStart`, `PreToolUse`, `PostCompact` et de l’acquittement MCP. Tant qu’elle n’a pas eu lieu, le statut est `NOT_RUN` et la couverture reste bornée à `PARTIAL_LOCAL_TOOLS`.

## Références

[1] [OpenAI — Hooks](https://learn.chatgpt.com/docs/hooks)  
[2] [OpenAI — Model Context Protocol pour Codex](https://learn.chatgpt.com/codex/extend/mcp?surface=cli)  
[3] [OpenAI — Bases de configuration Codex](https://learn.chatgpt.com/docs/config-file/config-basic)
