# M5-O — Adapter Gemini CLI à garde sans post-compaction

**Date :** 2026-08-27  
**Statut :** `PASS` pour la chaîne contrôlée VERA ; **`NOT_RUN`** pour une session Gemini CLI réelle  
**Commit fonctionnel :** `7ca437e`  
**Portée :** Gemini CLI, configuration **project-local** `.gemini/settings.json` seulement.

## 1. Décision

M5-O ajoute `gemini-cli-v1` en réutilisant exclusivement le Core lifecycle VERA. Le runtime est staged et hashé ; le MCP stdio repose sur `DenyRuntimeAdapter`; la configuration Gemini est prévisualisée puis appliquée dans le projet uniquement après confirmation.

La documentation Gemini distingue `SessionStart`, `BeforeTool`, `AfterTool`, `PreCompress` et la configuration MCP/hooks, mais le point `PreCompress` est une notification avant réduction de contexte et non un événement de restauration après compaction.[1] [2]

> Le niveau déclaré est **`TOOL_GUARD_NO_POST_COMPACTION`**. VERA peut armer, injecter et appliquer une garde sur les actions livrées au hook `BeforeTool`; il ne réarme pas la garde sur la seule notification `PreCompress`, et ne prétend pas couvrir un contexte restauré sans événement hôte attesté.

| Composant | Réalisation | Limite explicite |
|---|---|---|
| Runtime | `.vera-mmu/runtime/generated/gemini-cli-runtime.json`, bindings manifeste revalidés | Aucun download, bootstrap, réseau ou secret |
| Lifecycle | `SessionStart`, `BeforeTool`, `AfterTool`, `PreCompress`, `SessionEnd` | Pas de `PostCompact` synthétique |
| MCP | `vmmu-gemini-mcp` expose seulement `mmu_acknowledge_resume` | Aucune capability Pack exécutée |
| Config | `.gemini/settings.json` avec hooks VERA + serveur MCP | Pas de home/user scope, pas d’auto-trust |

## 2. Commandes

| Commande | Action | Écriture |
|---|---|---|
| `vmmu-gemini-stage --profile project.yaml --confirm` | Stage le runtime deny-by-default | `.vera-mmu/runtime/` |
| `vmmu-gemini-hook --profile project.yaml --event …` | Traite un événement JSON du host | État lifecycle runtime seulement |
| `vmmu-gemini-mcp --profile project.yaml` | Lance le serveur MCP stdio d’acquittement | Aucune configuration hôte |
| `vmmu-gemini-config --profile project.yaml` | Affiche le preview project-local | Aucune |
| `vmmu-gemini-config --profile project.yaml --apply-project --confirm` | Applique le preview contrôlé | `.gemini/settings.json` et reçu runtime |

La fusion conserve les clés et hooks tiers. Elle refuse les JSON non objets, les hooks VERA Gemini divergents, les serveurs MCP VERA divergents, les symlinks, les previews périmés et toute application non confirmée.

## 3. Preuve contrôlée

`tests/test_gemini_adapter.py` valide : staging sans configuration préalable ; conservation de réglages tiers ; refus de conflit et de symlink ; application project-local confirmée ; `SessionStart` injectant le Resume Dossier ; `BeforeTool` refusant avant acquittement ; vrai client MCP stdio acquittant les sections ; autorisation ultérieure ; et `PreCompress` produisant uniquement un avis sans réarmement.

La suite VERA passe à `473 passed, 37 subtests passed`; la compilation, les scans no-ARET/no-network/no-bootstrap/no-home et la roue isolée avec les quatre entry points Gemini passent. Aucun binaire Gemini n’est présent dans l’environnement (`GEMINI_PRESENT=NO`) et aucune installation ou connexion n’a été tentée.

## 4. Gates non exécutées

Le trust du host, le chargement des hooks par une session Gemini réelle, la connexion MCP réelle et l’observation de l’interface client restent `NOT_RUN`. Une future preuve doit utiliser un dépôt jetable, obtenir le consentement requis par Gemini, puis observer exactement le chemin SessionStart → BeforeTool refusé → MCP ack → BeforeTool autorisé. Elle doit surtout vérifier que le comportement après compaction reste **non couvert**, plutôt que de le présenter comme réarmé.

## Références

[1] [Google — Gemini CLI Hooks](https://geminicli.com/docs/hooks/)  
[2] [Google — Gemini CLI MCP servers](https://geminicli.com/docs/tools/mcp-server/)  
[3] [Google — Gemini CLI Settings](https://geminicli.com/docs/get-started/configuration/)
