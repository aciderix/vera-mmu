# M5-M.3b — Trust MCP Claude Code cloud au user-scope

> **Statut :** mécanisme préparé et testé sous home simulé — commit fonctionnel `3f26dad` ; **aucune écriture user-scope réelle n’a été exécutée** dans ce lot. L’approbation effective et la preuve Claude Code web restent **`NOT_RUN`**.
>
> **Périmètre :** produire puis, seulement après deux confirmations explicites indépendantes, pouvoir appliquer une fusion minimale de `enabledMcpjsonServers` dans le fichier fixe `$HOME/.claude/settings.json` de l’environnement cible.

## 1. Fait hôte et décision

Un serveur déclaré dans `.mcp.json` reste en attente d’approbation dans un workspace non trusted. Une déclaration committée dans le projet ne peut pas s’auto-approuver ; la documentation officielle cite les réglages user, managed et `--settings` parmi les sources d’approbation disponibles dans ce cas.[1] Par conséquent, M5-M.3b ne traite pas le projet comme la source du trust : il vérifie d’abord que M5-M.3a a appliqué et attesté la configuration project-local, puis prépare la seule entrée d’approbation correspondante.

La portée user est normalement propre à une machine et non une preuve que la même configuration atteint une session cloud. Cette différence impose que tout résultat de M5-M.3b soit qualifié de **préparation locale/user-scope**, jamais de trust cloud effectif.[2]

| Élément | Règle M5-M.3b |
|---|---|
| Cible | Chemin fixe résolu par `Path.home() / ".claude/settings.json"`; l’API et la CLI ne reçoivent aucun chemin user-scope. |
| Précondition | Runtime M5-M.2 staged et reçu M5-M.3a appliqué, cohérent avec les fichiers project-local actuels. |
| Entrée ajoutable | Exactement l’identifiant MCP cloud VERA attesté dans `enabledMcpjsonServers`. |
| Entrées préservées | Tous réglages tiers et approbations tierces demeurent inchangés. |
| Conflit | Une occurrence dans `disabledMcpjsonServers`, une liste malformée ou dupliquée, un reçu M5-M.3a manquant/divergent ou un symlink produit un refus sans écriture. |
| Exclusions | Aucun secret, setup, bootstrap, réseau, installation de dépendance ou lancement de session web. |

## 2. Deux confirmations transactionnelles

La fonction qui écrit le user-scope reçoit deux booléens nominaux distincts : `confirm_preview=True` et `confirm_user_scope=True`. Une confirmation générique ne peut pas les remplacer ; une valeur absente ou fausse refuse avant toute écriture. La CLI expose la même séparation :

```bash
# Prévisualisation seulement : lecture du fichier user-scope cible, zéro écriture.
vmmu-claude-code-cloud-config --profile project.yaml --preview-user-scope

# Chemin d’écriture, à ne jamais exécuter sans deux confirmations obtenues au moment précis :
vmmu-claude-code-cloud-config --profile project.yaml \
  --apply-user-scope --confirm-preview --confirm-user-scope
```

> **Règle opératoire VERA.** Le code empêche la fusion des deux gates. L’agent opérant doit, en plus, demander deux confirmations utilisateur explicites et séparées après présentation du preview réel, immédiatement avant l’exécution de la seconde commande. Aucune instruction antérieure, aucune variable d’environnement, aucun hook et aucun setup script ne vaut l’une de ces confirmations.

La simulation testée ne se substitue pas à cette règle : le home est patché vers un répertoire temporaire pour chaque test ; le `$HOME` de la session d’ingénierie n’est ni lu ni écrit.

## 3. Chaîne attestée

| Étape | Contrôle | Verdict de test |
|---|---|---|
| Configuration projet | Le reçu M5-M.3a correspond aux fichiers `.claude/settings.json` et `.mcp.json` actuels. | `PASS`. |
| Preview user-scope | Fusion canonique, stable et sans écriture ; conservation de `theme` et des serveurs tiers. | `PASS`. |
| Conflit de rejet | Le serveur VERA déjà présent dans `disabledMcpjsonServers` refuse. | `PASS`. |
| Précondition absente | Sans configuration project-local attestée, le preview refuse. | `PASS`. |
| Symlink | Un `settings.json` user-scope symlinké refuse sans suivre la cible. | `PASS`. |
| Double confirmation | Une confirmation sur deux refuse ; les deux sont nécessaires pour l’écriture simulée. | `PASS`. |
| CLI de preview | `--preview-user-scope` retourne le preview et ne crée pas le répertoire home simulé. | `PASS`. |

Le mécanisme compare le preview présenté à l’état user-scope courant juste avant d’écrire. Toute divergence entre les deux étapes invalide le preview et bloque la mutation. L’écriture, si l’opérateur a obtenu les deux confirmations nécessaires, est atomique et limitée au fichier fixe.

## 4. Ce qui n’est pas prouvé

| Assertion | Statut |
|---|---|
| Le fichier user-scope du **vrai** environnement cloud a été modifié | `NOT_RUN`. |
| Claude Code cloud lit cette configuration dans la session cible | `NOT_RUN`. |
| Le serveur `.mcp.json` est approuvé ou connecté par le host | `NOT_RUN`. |
| Les hooks host `SessionStart` / `PreToolUse` / compaction sont effectivement déclenchés | `NOT_RUN`. |
| La chaîne lifecycle cloud réelle résiste à une session fraîche | `NOT_RUN`. |

La documentation Claude Code on the web indique que les réglages d’une session cloud passent par l’environnement ou des fichiers committés dans le dépôt ; elle ne permet pas de promouvoir une simple écriture locale comme une observation du host cloud.[3] La preuve reste donc le protocole M5 web, à exécuter après le write-path réel doublement confirmé et après observation du statut MCP par le host.

## 5. Validation technique

| Contrôle | Résultat |
|---|---|
| Cycle rouge initial | `3 failed` : opérations user-scope absentes. |
| Tests runtime cloud | `11 passed`. |
| Suite VERA complète | `465 passed, 37 subtests passed`. |
| Compilation, `git diff --check`, scans de frontière | `PASS`. |
| Roue isolée et commande `--help` | `PASS`. |
| Home réel d’ingénierie | Ni lu ni écrit par les tests ou les validations de cette tranche. |

## Références

[1]: https://code.claude.com/docs/en/mcp#project-server-approvals-and-workspace-trust "Claude Code — Project server approvals and workspace trust"
[2]: https://code.claude.com/docs/en/settings#settings-in-cloud-sessions "Claude Code — Settings in cloud sessions"
[3]: https://code.claude.com/docs/en/claude-code-on-the-web "Claude Code — Use Claude Code on the web"
[4]: ../../../src/vera_mmu/claude_code_cloud.py "Préparation et application user-scope M5-M.3b"
[5]: ../../../tests/test_claude_code_cloud_runtime.py "Conformance M5-M.3b sous home simulé"
