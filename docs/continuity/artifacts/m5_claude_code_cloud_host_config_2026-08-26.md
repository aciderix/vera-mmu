# M5-M.3a — Configuration hôte Claude Code cloud project-local

> **Statut :** `PASS` pour le preview, la fusion et l’application **project-local** contrôlés — commit fonctionnel `ed9f2e8` ; **`NOT_RUN`** pour le trust user-scope et pour toute preuve Claude Code web live.
>
> **Périmètre :** à partir d’un runtime cloud M5-M.2 déjà staged, produire un preview déterministe des hooks et du serveur MCP cloud, puis appliquer seulement ce preview sous la racine du projet après confirmation explicite.

## 1. Décision

M5-M.3a ajoute `vmmu-claude-code-cloud-config`. Sans `--apply-project`, la commande prévisualise la fusion. Avec `--apply-project --confirm`, elle peut écrire exclusivement les trois fichiers project-bound suivants :

| Cible | Nature | Effet autorisé |
|---|---|---|
| `.claude/settings.json` | Réglages de projet Claude | Ajout des six hooks cloud VERA attestés. |
| `.mcp.json` | Serveurs MCP de projet | Remplacement contrôlé de l’entrée MCP générique VERA par le serveur cloud attesté. |
| `.vera-mmu/runtime/generated/claude-code-cloud-host-config.json` | État runtime VERA | Trace hashée des deux JSON appliqués et de l’absence de user-scope. |

Claude Code on the web peut charger les hooks et serveurs MCP committés dans le dépôt, alors que les réglages utilisateur locaux ne sont pas lus par une session cloud.[1] [2] Les déclarations project-local sont donc une préparation nécessaire, mais elles **ne constituent pas** une approbation du serveur de projet ni un fait de trust.

## 2. Contrat fermé de preview

Le preview exige le runtime `vera-claude-code-cloud-runtime/v1` M5-M.2. Il recharge et vérifie le manifeste, les instructions, le plan cloud et les bindings depuis le runtime VERA ; les hooks et la commande MCP ne viennent jamais du client.

| Élément généré | Valeur contrôlée |
|---|---|
| Hooks | `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `PostCompact`, `Stop`. |
| Commande hook | `vmmu-claude-code-cloud-hook --profile <profil attesté> --event <événement fixe>`. |
| Commande MCP | `vmmu-claude-code-cloud-mcp --profile <profil attesté>`. |
| Environnement MCP | Uniquement l’identité projet et les hashes non secrets du plan attesté. |
| Fusion | Les entrées tierces sont conservées ; l’entrée MCP VERA générique correspondante est remplacée par l’entrée cloud attestée. |
| Conflit | Toute entrée VERA lifecycle/MCP divergente, JSON non objet, snapshot absent, état divergent ou symlink est refusé sans écriture. |
| Empreinte | `SHA-256(settings JSON canonique + NUL + mcp JSON canonique)`. |

> Les identités de session, adapter, bindings, hash de dossier et résultat d’acquittement ne sont ni des options de la commande ni des données configurables par le client.

## 3. Application project-local explicitement confirmée

L’application ne peut se produire que lorsque le preview présenté correspond exactement à l’état courant des deux cibles. Un changement entre preview et application produit un refus fail-closed. L’écriture est atomique et les symlinks sont refusés pour le répertoire `.claude`, les deux fichiers de configuration et l’état runtime.

| Appel | Résultat attendu |
|---|---|
| `vmmu-claude-code-cloud-config --profile project.yaml` | `PREVIEW`, zéro écriture. |
| `vmmu-claude-code-cloud-config --profile project.yaml --apply-project` | Refus : confirmation absente. |
| `vmmu-claude-code-cloud-config --profile project.yaml --apply-project --confirm` | `APPLIED_PROJECT_LOCAL` ou `UNCHANGED`, seulement dans le projet. |

Cette confirmation protège un write-path de projet. Elle n’autorise pas et ne prépare pas implicitement une écriture sous le home de l’utilisateur.

## 4. Frontière user-scope et trust

| Objet | Statut M5-M.3a | Justification |
|---|---|---|
| Lecture de `$HOME/.claude/settings.json` | `NOT_DELIVERED` | Le module n’évalue pas un home ni ne lit de réglage utilisateur. |
| Écriture de `$HOME/.claude/settings.json` | `NOT_DELIVERED` | Le code ne possède aucun paramètre ou chemin user-scope. |
| Approbation MCP de projet | `NOT_RUN` | L’hôte cloud doit rapporter le trust effectif ; un dépôt non trusted ne peut pas s’auto-approuver.[2] |
| Secrets / variables cloud | `NOT_DELIVERED` | Les environnements cloud n’ont pas de store de secrets dédié et les valeurs y sont visibles aux utilisateurs de l’environnement.[3] |
| Setup, roue ou bootstrap réseau | `NOT_DELIVERED` | Aucun téléchargement, installation ou accès réseau n’est ajouté. |
| Preuve Claude Code web fraîche | `NOT_RUN` | Aucun environnement cloud réel ni trust effectif n’est actionné dans ce lot. |

M5-M.3b isole désormais la preview de trust, la fusion user-scope et la barrière de **double confirmation explicite au moment de l’opération**. Son mécanisme est distinct de M5-M.3a et ne peut pas être déclenché par un hook ; une écriture réelle puis la preuve web contrôlée restent des actes opératoires séparés.

## 5. Preuves contrôlées

| Contrôle | Verdict |
|---|---|
| Cycle test-first | `3 failed` avant implémentation ; import des opérations absent. |
| Preview déterministe et conservation des entrées tierces | `PASS`. |
| Refus d’un hook VERA divergent et d’un serveur VERA divergent | `PASS`. |
| Refus d’une cible `.claude/settings.json` symlinkée | `PASS`. |
| Application sans confirmation | `PASS` : refus. |
| Application confirmée | `PASS` : écrit seulement project-local, état runtime attesté. |
| Runtime M5-M.2, hook/MCP lifecycle et compaction | `PASS` : non-régressions ciblées. |
| Suite VERA | `462 passed, 37 subtests passed`. |
| Roue isolée | `PASS` : quatre entry points cloud (`stage`, `hook`, `mcp`, `config`). |

Cette preuve est une simulation contrôlée de fichiers de projet et de stdin/stdout. Elle ne démontre pas que le service Claude Code web charge les fichiers, déclenche les hooks ou approuve le MCP dans une session fraîche.

## Références

[1]: https://code.claude.com/docs/en/hooks "Claude Code — Hooks : emplacements et exécution cloud"
[2]: https://code.claude.com/docs/en/mcp#project-server-approvals-and-workspace-trust "Claude Code — Approbations de serveurs de projet et workspace trust"
[3]: https://code.claude.com/docs/en/cloud-environments "Claude Code — Environnements cloud, réseau et variables"
[4]: ../../../src/vera_mmu/claude_code_cloud.py "Preview et application project-local M5-M.3a"
[5]: ../../../tests/test_claude_code_cloud_runtime.py "Conformance cloud staged, preview et fusion"
