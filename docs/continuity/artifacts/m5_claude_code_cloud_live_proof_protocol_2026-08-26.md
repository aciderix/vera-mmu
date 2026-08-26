# M5-M.2 — Protocole de preuve Claude Code web/cloud

> **Statut :** protocole préparé ; **pas une preuve live**.
>
> **Précondition :** `vera-mmu` est déjà installé dans l’image/session cloud. Ce protocole n’autorise ni téléchargement, ni bootstrap réseau, ni variable secrète.

## 1. Ce qui est déjà prouvé hors cloud web

La preuve automatisée M5-M.2 couvre une chaîne distribuée réelle dans un environnement contrôlé : staging confirmé sous le runtime de projet, hook Claude JSON sur stdin/stdout, serveur MCP stdio, acquittement dont le client ne fournit que les sections, puis autorisation de `PreToolUse`. La compaction réarme ensuite la garde.

Cette preuve n’est pas une preuve que Claude Code web déclenche effectivement les hooks ou approuve le serveur de projet : ces comportements relèvent du host cloud et de son trust.[1] [2]

## 2. Préconditions à constater dans une session cloud fraîche

| Contrôle | Commande ou observation | Verdict attendu | Effet si absent |
|---|---|---|---|
| Runtime préinstallé | `vmmu-claude-code-cloud-stage --help` | Commande présente. | `RUNTIME_MISSING`; ne pas installer depuis le hook. |
| Profil VERA | `project.yaml` est présent à la racine du projet. | Profil lisible, identité déterministe. | Refus du staging. |
| Catalogue | Le Store contient des capabilities `ALLOW`. | Compilation manifest possible. | Refus fail-closed. |
| Trust | Le host rapporte le serveur projet comme approuvé au scope adapté. | `TRUSTED` observé. | `TRUST_PENDING`; ne pas prétendre que MCP est actif. |
| Secrets | Aucun secret requis par M5-M.2. | Absence de consultation de secrets. | N/A : ne jamais ajouter une valeur dans le setup. |

## 3. Staging explicite autorisé

Le seul write-path M5-M.2 est project-local et doit être appelé explicitement :

```bash
vmmu-claude-code-cloud-stage --profile project.yaml --confirm
```

Cette commande crée ou vérifie seulement :

```text
.vera-mmu/runtime/generated/claude-code-cloud-runtime.json
```

Elle ne modifie pas `.claude/`, `.mcp.json`, `$HOME`, le trust, les dépendances ou le réseau. Sans `--confirm`, elle doit refuser.

## 4. Configuration hôte à préparer mais non appliquer dans M5-M.2

Un lot ultérieur devra produire un preview attesté des deux déclarations hôte suivantes. M5-M.2 les documente seulement ; il ne les écrit pas.

| Cible | Déclaration attendue | Raison de la non-application |
|---|---|---|
| Hooks projet Claude | Commandes fixes `vmmu-claude-code-cloud-hook --profile <profil> --event <événement>` pour `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `PostCompact`, `Stop`. | Écriture `.claude/settings.json` à traiter séparément, avec fusion, conflits et trust host. |
| MCP projet | Commande fixe `vmmu-claude-code-cloud-mcp --profile <profil>`. | La mise à jour `.mcp.json` et l’approbation user-scope doivent être previewées et confirmées. |
| Approbation user-scope cloud | Serveur VERA projet reconnu par l’hôte. | Écriture sous `$HOME/.claude/settings.json` sensible, jamais déclenchée par un hook. |

> Les identités de session, adapter, hash de dossier, résultat d’acquittement et bindings ne sont jamais des paramètres de ces commandes ni des données configurées par le client MCP.

## 5. Séquence de preuve live future

Lorsque le lot de configuration/trust séparé sera validé, une session Claude Code web fraîche doit démontrer les étapes suivantes, dans cet ordre.

| Étape | Observation admissible | Refus attendu si incomplète |
|---|---|---|
| Démarrage | `SessionStart` injecte un Resume Dossier cloud. | Aucun `additionalContext` : `FAIL`, ne pas déclarer la garde active. |
| Avant tool | Un tool ordinaire est refusé avant l’acquittement. | Tool autorisé : `FAIL` critique. |
| MCP | Seul `mmu_acknowledge_resume(sections)` est visible ; le hash/session restent serveur. | Entrées supplémentaires : `FAIL` critique. |
| Après ack | Un tool ordinaire devient autorisé. | Refus persistant : `ERROR`/wall de corrélation à qualifier. |
| Compaction | `PostCompact` injecte un nouveau dossier et réarme le refus. | Action autorisée sans second ack : `FAIL` critique. |
| Nouvelle session | Une session cloud distincte n’hérite pas de l’acquittement précédent. | Réutilisation silencieuse : `FAIL` critique. |

## 6. Limites M5-M.2

M5-M.2 distribue le hook, le serveur MCP et le staging, mais **ne peut pas encore être présenté comme compatible Claude Code web de bout en bout**. La lacune est explicitement la configuration hôte attestée et le trust user-scope, pas l’absence de transport MCP ou de cycle lifecycle testés.

Le prochain lot doit fournir : preview des modifications, fusion non destructive, refus de symlink/conflit, double confirmation pour user-scope, doctor post-installation et preuve réelle dans une session cloud. Le bootstrap par roue et toute action réseau restent ultérieurs.

## Références

[1]: https://code.claude.com/docs/en/claude-code-on-the-web "Claude Code on the web"
[2]: https://code.claude.com/docs/en/mcp#project-server-approvals-and-workspace-trust "Approbations MCP de projet et workspace trust"
[3]: https://code.claude.com/docs/en/settings#settings-in-cloud-sessions "Settings dans les sessions cloud"
