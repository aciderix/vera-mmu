# M5-M.1 — Plan cloud Claude Code attesté et doctor préinstallé

> **Statut :** `PASS` — commit fonctionnel `940fb7e`.
>
> **Portée :** planification et diagnostic cloud de Claude Code en mode `PREINSTALLED_VERA`. Aucun hook cloud exécutable, bootstrap, téléchargement, secret ou write-path user-scope n’est livré.

## 1. Décision

M5-L a démontré un adapter Claude Code local. Le cloud est différent : une session web se lance dans un environnement cloud où réseau, variables et setup scripts sont des paramètres d’environnement, tandis qu’un dépôt non trusted ne peut pas approuver son propre serveur `.mcp.json` avec une configuration committée.[1] [2]

M5-M.1 ne copie donc pas le script ARET historique. Il introduit le format canonique `vera-claude-code-cloud/v1` qui lie explicitement le runtime, le trust et les snapshots existants. L’implémentation ne porte ni secret, ni Pack, ni shell, ni accès réseau, ni opération d’écriture.

| Élément | M5-M.1 livré | Hors périmètre explicite |
|---|---|---|
| Plan cloud | Compile un JSON canonique lié au projet, au manifeste, aux instructions, aux plans MCP/hooks/revue/lifecycle et au plan local. | Sélection de provider arbitraire ou de commande client. |
| Runtime | Provider unique `PREINSTALLED_VERA`, avec réseau déclaré `FORBIDDEN`. | Roue attestée, `pip`, création de venv, téléchargement, bootstrap réseau ou verrou de préchauffage. |
| Serveur MCP | Déclare l’entry point futur `vmmu-claude-code-cloud-mcp` et le profil/project id attestés. | Distribution de cet entry point ou lancement d’un serveur cloud réel. |
| Trust | Déclare un preview `PREVIEW_ONLY` qui cible le scope user du container. | Lecture, écriture ou approbation de `$HOME/.claude/settings.json`. |
| Secrets | Déclare `EXTERNAL_ONLY` sans requirements, valeurs ni accès. | Lire, imprimer, sérialiser, stocker, générer ou valider la valeur d’un secret. |
| Doctor | Observe le provider, un entry point et un fait de trust fourni par l’hôte. | Réparer, créer un fichier, déclencher une installation ou déclarer une session cloud live. |

## 2. Contrat de plan

Le plan est construit uniquement lorsque tous ses snapshots ont été recomposés et sont identiques aux entrées : manifeste MCP, instructions, config, hooks, revue Claude Code, adapter lifecycle M5-K et plan Claude local M5-L. Toute mutation, obsolescence, identité étrangère ou capability supplémentaire rend le plan invalide.

| Champ | Garantie |
|---|---|
| `format` | `vera-claude-code-cloud/v1`. |
| `project_id` | Identité VERA exacte du Store. |
| Hashes | `mcp_build_hash`, instructions/config/hook/review/lifecycle et `local_plan_hash`. |
| Runtime | Uniquement `{provider: PREINSTALLED_VERA, network: FORBIDDEN}`. |
| Trust | Uniquement preview du target user-scope ; aucune opération n’est encodée. |
| Secrets | Uniquement `EXTERNAL_ONLY`; le JSON ne contient ni nom ni valeur de secret. |
| MCP | Commande fixe VERA, profil attesté et variables non secrètes project/hash-bound. |

Le plan n’autorise pas `NETWORK_BOOTSTRAP`. Les mots, dépendances et mécanismes ARET ne font pas partie du module Core cloud.

## 3. Doctor sans effet de bord

Le doctor reçoit une observation non secrète à deux champs : environnement `CLAUDE_CODE_CLOUD` et trust parmi `TRUST_PENDING`, `TRUSTED`, `DISABLED` ou `UNVERIFIABLE`. Toute autre valeur est refusée. Il vérifie seulement la présence déclarée de l’entry point cloud et ne crée aucun chemin sous le projet ou dans le home.

| Runtime déclaré | Trust observé | Statut doctor |
|---|---|---|
| Entry point absent | Toute valeur valide | `RUNTIME_MISSING` |
| Entry point présent | `TRUST_PENDING` | `TRUST_PENDING` |
| Entry point présent | `DISABLED` | `DISABLED` |
| Entry point présent | `UNVERIFIABLE` | `UNVERIFIABLE` |
| Entry point présent | `TRUSTED` | `RUNTIME_READY` |

> `RUNTIME_READY` signifie seulement que le plan préinstallé et le fait de trust déclaré sont cohérents. Il ne signifie ni que le hook cloud fonctionne, ni que le serveur MCP s’est connecté, ni qu’une session Claude Code web réelle a été validée.

## 4. Preuves M5-M.1

| Contrôle | Verdict |
|---|---|
| Cycle rouge | `4 failed` avant création du module. |
| Tests de plan/doctor | `4 passed`. |
| Matrice Claude locale + cloud concernée | `11 passed`. |
| Suite VERA | `455 passed, 37 subtests passed`. |
| Compilation, scans Core/cloud/shell/réseau/write-path, `git diff --check` | `PASS`. |
| Roue isolée, import du module et entry points existants | `PASS`. |

## 5. Prochaines limites et jalons

M5-M.2 devra apporter, sous contrat distinct, l’adapter cloud réellement distribuable et une preuve dans un environnement Claude Code web. Le préchauffage d’une roue attestée et le bootstrap réseau seront eux-mêmes séparés : la seconde option requiert un lock hashé et un consentement explicite au réseau.

L’écriture de l’approbation dans `$HOME/.claude/settings.json` est un write-path utilisateur cloud sensible. Elle nécessite un preview et deux confirmations explicites au moment de l’opération ; M5-M.1 ne la crée ni ne l’exécute.

## Références

[1]: https://code.claude.com/docs/en/claude-code-on-the-web "Claude Code on the web"
[2]: https://code.claude.com/docs/en/mcp#project-server-approvals-and-workspace-trust "Approbations MCP de projet et workspace trust"
[3]: https://code.claude.com/docs/en/settings#settings-in-cloud-sessions "Settings dans les sessions cloud"
[4]: https://code.claude.com/docs/en/env-vars "Variables d’environnement Claude Code"
