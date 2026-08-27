# M10-B — Audit du travail MCP restant

**Date :** 2026-08-27  
**Statut :** inventaire factuel ; **aucun agent réel n’a été lancé**  
**Objet :** distinguer exactement le produit VERA déjà implémenté et testé dans un environnement contrôlé des preuves qui restent à acquérir sur les logiciels hôtes réels.

> **Résumé vulgarisé.** Le moteur MCP de VERA est construit, verrouillé et exercé avec de vrais échanges stdio. Ce qui manque n’est pas « refaire un MCP » : il faut encore vérifier que chaque application d’IA réelle charge la configuration, accepte ses hooks, se connecte effectivement au serveur MCP et respecte le cycle prévu dans une session réelle.

## 1. Ce qui est déjà produit et contractuellement testé

Le catalogue distribué contient six adapters immuables : Claude Code local, Claude Code cloud, Codex, Gemini CLI, Antigravity et le fallback `generic-mcp`. Chaque adapter est project-local, lié à des snapshots hashés, prévisualisé avant écriture et refuse les conflits, symlinks, états périmés ou confirmations absentes. Le serveur MCP est en stdio ; le client ne peut pas fournir une commande, un chemin, un verdict, un artefact, un hash de dossier ou une identité de session de confiance.

| Surface | Ce qui est réellement exercé dans VERA | Ce que cela prouve | Ce que cela ne prouve pas |
|---|---|---|---|
| Transport MCP | Un vrai `ClientSession` stdio ouvre le serveur, inspecte le catalogue et appelle les outils autorisés dans les tests. | Le protocole, le démarrage du serveur et les refus VERA sont opérationnels dans le processus distribué. | Qu’un client MCP tiers réel ait adopté la configuration, trusté le serveur ou le démarre dans son propre environnement. |
| Lifecycle | Les hooks sont exercés par sous-processus JSON stdin/stdout ; `SessionStart`/équivalent arme, l’outil est refusé, `mmu_acknowledge_resume` est appelé, puis la garde est levée ou réarmée selon le contrat. | Les adapters appliquent correctement le lifecycle VERA pour les événements contractuels reçus. | Que l’hôte génère effectivement ces événements, au même format et au moment attendu. |
| Configuration | Preview déterministe puis fusion confirmée dans les seules cibles project-local attestées. | VERA ne remplace pas les réglages tiers et refuse une configuration VERA conflictuelle ou ambiguë. | Que l’hôte accepte ces fichiers, les lit sur l’environnement visé ou leur accorde le trust requis. |
| Sécurité | Runtimes project-bound, `DenyRuntimeAdapter`, aucune capability Pack exécutable, aucune écriture home implicite, aucun bootstrap, secret ou réseau. | Le serveur ne devient pas une porte d’exécution arbitraire par simple configuration MCP. | Une autorisation utilisateur ou hôte externe, qui doit toujours être demandée au moment où elle est nécessaire. |

Les commandes et comportements exacts sont déclarés dans le [catalogue immutable des adapters](../../../src/vera_mmu/adapter_catalog.py) et leurs suites de conformance. Le fallback générique prouve surtout la compatibilité de transport : il ne fabrique volontairement ni session, ni reprise, ni interception avant action.[1]

## 2. Inventaire par hôte : fait, limite de produit, preuve restante

| Hôte / adapter | Implémenté et testé | Limite de produit assumée | Travail restant pour une preuve réelle |
|---|---|---|---|
| **MCP générique** | Runtime `MCP_ONLY`, `.mcp.json` project-local, serveur stdio, lecture du catalogue, refus des capabilities et refus d’ack sans contexte lifecycle. | Pas de hooks, session ou compaction inventés. Cette absence est le contrat, pas un bug. | Choisir un client MCP réel précis, appliquer le preview confirmé dans un dépôt jetable, confirmer le trust/chargement par ce client et observer la connexion stdio. Toute automation lifecycle nécessite ensuite un adapter dédié à cet hôte. |
| **Claude Code local** | Hooks `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `PostCompact`, `Stop`, configuration `.claude/settings.json` et `.mcp.json` project-local, hook subprocess et client MCP stdio testés. | Une session active par projet ; pas de cloud, pas de `~/.claude`, pas de bootstrap, réseau ou auto-trust. | Sur une installation Claude Code locale identifiée et un dépôt jetable : accepter la revue/trust hôte, constater le chargement des hooks et du MCP, puis observer startup → refus avant outil → ack → autorisation → réarmement après compaction et isolation d’une nouvelle session.[2] |
| **Claude Code cloud** | Staging, hooks, MCP et config project-local testés ; preview/fusion user-scope préparés et testés seulement sous home simulé. | Le mécanisme refuse de toucher `$HOME` sans `confirm_preview` **et** `confirm_user_scope` distincts ; il n’installe ni dépendance ni secret et n’emploie aucun bootstrap réseau. | Présenter un preview réel de `$HOME/.claude/settings.json`, recueillir deux confirmations immédiates et distinctes, seulement alors écrire ce fichier fixe, puis vérifier dans une session cloud fraîche : trust, connexion MCP, `SessionStart`, refus/ack/autorisation, `PostCompact` et non-réutilisation de l’ack dans une nouvelle session.[3] [4] |
| **Codex** | Runtime staged, `.codex/hooks.json`, `.codex/config.toml`, hooks session/pre/post-tool/compaction/stop et MCP stdio testés. | `PARTIAL_LOCAL_TOOLS` : les outils hosted ou chemins qui ne passent pas par les hooks ne sont pas couverts. VERA ne prétend pas les bloquer. | Avec un client Codex réel : revue/trust visible des hooks, chargement de la config, connexion MCP et observation exacte de `SessionStart → PreToolUse refusé → ack → autorisé → PostCompact réarmé`. La couverture doit rester qualifiée `PARTIAL_LOCAL_TOOLS` après le test.[5] |
| **Gemini CLI** | Runtime, `.gemini/settings.json`, hooks `SessionStart`/`BeforeTool`/`AfterTool`/`PreCompress`/`SessionEnd`, MCP stdio et fusion confirmée testés. | `TOOL_GUARD_NO_POST_COMPACTION` : `PreCompress` est seulement un avis ; VERA n’invente pas de `PostCompact`. | Avec Gemini CLI réel : consentement/trust hôte, chargement des hooks, connexion MCP et chemin `SessionStart → BeforeTool refusé → ack → autorisé`. Constater explicitement que la garde après compaction **n’est pas couverte**, au lieu de la présenter comme réarmée.[6] |
| **Antigravity** | Runtime, `.antigravity/settings.json`, `PreInvocation`/`PreToolUse`/`PostToolUse`/`Stop`, MCP stdio et garde par invocation testés. | `TURN_GUARD_HARD`, pas de session durable ni de reprise/compaction : la surface hôte ne les atteste pas. | Avec Antigravity réel : trust de projet, chargement de la config et des hooks, connexion MCP, puis une invocation identifiable avec refus avant ack, autorisation après ack et libération au `Stop`. Aucun élargissement à la compaction ne peut être inféré.[7] |

## 3. Les gaps de produit, distincts des preuves manquantes

Le **gap principal est une preuve d’intégration hôte**, pas un manque du moteur MCP générique. Les six adapters déclarés disposent d’un contrat et d’une conformance contrôlée. Il serait erroné de les déclarer « fonctionnels dans Claude/Codex/Gemini/Antigravity » avant les observations listées ci-dessus ; il serait tout aussi erroné d’affirmer qu’ils sont non implémentés.

Deux limites de produit restent intentionnelles et doivent rester visibles même après des essais hôtes réussis : Gemini ne possède pas de réarmement post-compaction attesté, et Codex ne couvre que les outils locaux qui atteignent réellement ses hooks. Le mode générique n’apporte aucune garde automatique parce qu’aucun lifecycle hôte n’est connu. Ces limites ne doivent pas être corrigées par simulation ou par promesse ; un changement de couverture exigerait un contrat d’hôte, des tests dédiés et une preuve réelle.

Enfin, un nouvel assistant populaire n’obtient pas automatiquement un adapter complet parce qu’il sait parler MCP. Il peut utiliser `generic-mcp` pour le transport ; dès qu’il faut démarrage de session, hooks, compaction ou contrôle avant action, un adapter hôte distinct et son protocole de preuve sont requis.

## 4. Ordre de travail conseillé lorsque les essais réels seront autorisés

Les essais agents étant explicitement différés, aucune action de cette section n’est réalisée dans ce lot. L’ordre le plus sûr est de commencer par un dépôt jetable et un seul hôte, de conserver les sorties et versions, puis de comparer chaque observation à l’état contractuel attendu. Claude Code cloud reste le seul cas où un fichier user-scope pourrait être modifié ; il ne peut être abordé qu’après preview réel et deux confirmations immédiatement antérieures à l’écriture. Les autres hôtes restent project-local et conservent leur propre acte de revue/trust côté utilisateur.

| Priorité | Preuve à obtenir | Verdict à enregistrer |
|---|---|---|
| 1 | Client MCP générique sélectionné et connecté au serveur VERA project-local. | `PASS` de transport pour ce client seulement, sans lifecycle implicite. |
| 2 | Claude Code local ou Codex sur dépôt jetable, avec hooks/MCP effectivement visibles. | `PASS`/`FAIL` par événement ; ne pas étendre Codex aux outils hosted. |
| 3 | Gemini et Antigravity, chacun sur un dépôt jetable. | `PASS`/`FAIL` au niveau de garde réellement offert par le host, sans compaction ajoutée. |
| 4 | Claude Code cloud après les doubles confirmations requises. | `PASS` seulement si trust, connexion et cycle complet sont observés dans une session fraîche. |

## Références

[1]: m5_generic_mcp_adapter_2026-08-27.md "M5-Q — fallback MCP générique"
[2]: m5_claude_code_local_adapter_2026-08-26.md "M5-L — adapter Claude Code local"
[3]: m5_claude_code_cloud_user_trust_2026-08-27.md "M5-M.3b — trust user-scope Claude Code cloud"
[4]: m5_claude_code_cloud_live_proof_protocol_2026-08-26.md "M5-M.2 — protocole de preuve Claude Code web/cloud"
[5]: m5_codex_adapter_2026-08-27.md "M5-N — adapter Codex"
[6]: m5_gemini_cli_adapter_2026-08-27.md "M5-O — adapter Gemini CLI"
[7]: m5_antigravity_adapter_2026-08-27.md "M5-P — adapter Antigravity"
