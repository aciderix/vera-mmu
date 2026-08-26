# M5-L — Adapter Claude Code local attesté

> **Statut :** `PASS` — commit fonctionnel `45fe9af`.
>
> **Portée :** un projet VERA local, son fichier `.claude/settings.json`, son fichier `.mcp.json` et son runtime `.vera-mmu`. Le cloud, les réglages home, le trust/setup, le bootstrap, le réseau, la synchronisation et les autres IA sont explicitement exclus.

## 1. Décision

M5-J avait livré le mécanisme de reprise universel et M5-K l’acquittement MCP contextualisé. M5-L est la première traduction vers un hôte réel : **Claude Code local**. Elle s’appuie sur des événements officiels où Claude transmet un `session_id`, un `cwd`, l’événement et, avant une action, le nom et les paramètres du tool. `SessionStart` accepte notamment les sources `startup`, `resume`, `clear`, `compact` et `fork`; `PreToolUse` peut refuser une action par décision de permission.[1]

Le résultat n’est pas un script ARET porté sous un nouveau nom. Il s’agit d’un module VERA (`claude_code_local.py`) qui compose les contrats M5-B/E/F/G/H/J/K et ne connaît aucun Pack. Le seul comportement d’exécution de capability reste le refus du runtime générique.

| Élément | Implémentation M5-L | Limite de sécurité |
|---|---|---|
| Plan hôte | `vera-claude-code-local/v1`, hashé et lié aux snapshots manifest/instructions/config/hooks/revue/lifecycle. | Plan stale, altéré ou project-bound différent : refus. |
| Hooks | `SessionStart`, `PreToolUse`, `PostToolUse` ciblé, `PreCompact`, `PostCompact`, `Stop`. | Commandes fixes vers l’entry point VERA ; aucune commande issue de stdin, aucun script projet généré. |
| Serveur MCP | `vmmu-claude-code-local-mcp`, configuré à la place du seul serveur VERA M5-I. | `DenyRuntimeAdapter` conserve le refus de toute capability ; seul l’acquittement est utilisable. |
| Session | Liaison locale project-bound sous runtime, créée seulement au `SessionStart`. | Une seule session locale active par projet ; conflit = refus sans écrasement. |
| Installation | `confirm=True`, fusion JSON atomique et non destructive. | Symlink, JSON non objet, hooks ou serveur VERA divergent, état divergent : refus. |
| Doctor | Observation de plan, fichiers et entry points. | Ne crée aucun fichier, n’installe/répare/télécharge/approuve rien. |

## 2. Protocole lifecycle local

| Événement Claude | Action VERA | Résultat Claude |
|---|---|---|
| `SessionStart` | Crée ou retrouve la liaison de session, compile le Resume Dossier et arme la garde M5-J. La source `resume` conserve un acquittement vivant ; les autres sources réarment. | `additionalContext` contient le dossier borné et l’instruction d’utiliser `mmu_acknowledge_resume`. |
| `PreToolUse` | Consulte la garde. | Refus `permissionDecision: deny` tant que le dossier n’est pas acquitté. Le seul tool exempté est le nom MCP exact de `mmu_acknowledge_resume`. |
| `PostToolUse` de l’acquittement | Relit la garde persistée. | Retourne un contexte de reprise si l’acquittement n’a pas réellement levé la garde. |
| `PreCompact` | Réarme avec `CONTEXT_PREPARE`. | Contexte borné indiquant que la reprise devra être renouvelée. |
| `PostCompact` | Réarme avec `CONTEXT_RESTORED` et réinjecte le dossier. | `additionalContext` contenant le nouveau dossier à acquitter. |
| `Stop` | Produit un nudge si nécessaire puis libère uniquement la liaison de la session courante. | Aucun push, sync ou persistance externe. |

> La documentation Claude indique que `PreToolUse` intervient avant le traitement du tool et permet une décision d’autorisation/refus, tandis que `PostToolUse` arrive après l’exécution. M5-L n’emploie donc `PreToolUse` que pour bloquer et ne prétend pas annuler une action dans `PostToolUse`.[1]

## 3. Installation et diagnostic

L’installation n’est jamais implicite. Après recompilation et vérification de tous les snapshots, `install_claude_code_local(..., confirm=True)` peut fusionner les six groupes de hooks VERA dans `<projet>/.claude/settings.json`, remplacer dans `<projet>/.mcp.json` **seulement** l’ancien serveur générique VERA par le serveur local attesté, puis enregistrer le plan exact sous le runtime VERA. Les clés, hooks et serveurs tiers sont préservés.

| Cas | Décision |
|---|---|
| Confirmation absente | Refus avant toute écriture. |
| Fichier absent | Création atomique des seules cibles attestées. |
| Cible VERA déjà identique | `UNCHANGED`, octets non réécrits. |
| Cible VERA/groupe hook divergent | Refus, aucune fusion partielle intentionnelle. |
| Symlink ou JSON invalide | Refus fail-closed. |
| Doctor avant installation | `NOT_INSTALLED`, sans créer `.claude` ni état runtime. |
| Entry point absent après installation | `DEGRADED`, jamais `READY`. |
| État, hooks, serveur et entry points exacts | `READY`. |

Les configurations installées n’emploient que les entry points Python distribués `vmmu-claude-code-local-hook` et `vmmu-claude-code-local-mcp`. Il n’y a ni `pip`, ni `curl`, ni `git`, ni shell arbitraire, ni communication réseau dans le module.

## 4. Preuves exécutées

La matrice de tests couvre la compilation stable, les snapshots stale, la garde hard, l’exception d’acquittement, le réarmement autour de compaction, les conflits de session, la fusion, l’idempotence, les symlinks et le doctor observationnel. Deux vérifications dépassent la simple simulation : le point d’entrée de hook reçoit le JSON sur stdin et produit sa réponse Claude sur stdout ; puis un vrai client MCP stdio appelle `mmu_acknowledge_resume`, après quoi le hook `PreToolUse` laisse effectivement l’action suivante passer.

| Contrôle | Verdict |
|---|---|
| Tests M5-L ciblés | `7 passed` |
| Suite VERA complète | `451 passed, 37 subtests passed` |
| Compilation et scans Core/hôte/réseau/shell/bootstrap | `PASS` |
| `git diff --check` | `PASS` |
| Roue isolée et quatre entry points | `PASS` |

## 5. Limites non négociables

M5-L ne supporte pas le cloud, les sessions concurrentes, `~/.claude`, les actions de trust/setup, l’installation de dépendances, le bootstrap de container, le réseau, la synchronisation, le push ou un Pack réel. Il ne supporte pas Codex, Gemini, Antigravity ou un autre hôte. Aucun de ces supports ne peut être inféré de l’existence des hooks locaux.

Le prochain incrément autorisé est **M5-M**, un adapter Claude Code cloud distinct, à spécifier et valider séparément.

## Références

[1]: https://code.claude.com/docs/en/hooks "Claude Code — Hooks"
[2]: ../../../src/vera_mmu/claude_code_local.py "Adapter Claude Code local"
[3]: ../../../tests/test_claude_code_local_adapter.py "Plan, installation, garde et doctor"
[4]: ../../../tests/test_claude_code_local_hook_cli.py "Conformance stdin/stdout de hook"
[5]: ../../../tests/test_claude_code_local_mcp_runtime.py "Conformance vrai MCP stdio"
