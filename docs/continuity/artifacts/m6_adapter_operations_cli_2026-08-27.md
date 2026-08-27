# M6-A — CLI unifiée et doctor observationnel des adapters

**Date :** 2026-08-27  
**Statut :** `PASS` pour le socle CLI/doctor  
**Commit fonctionnel :** `17a2bba`  
**Portée :** façade opératoire `vmmu adapter`, sans nouvelle règle Core ni mutation hôte implicite.

## 1. Décision

M6-A transforme les commandes d’adapter séparées en une façade contrôlée : `vmmu adapter matrix`, `doctor`, `validate`, `stage` et `configure`. La CLI route vers les entry points déjà attestés ; elle ne réimplémente ni la compilation, ni le lifecycle, ni la fusion de configuration.

> Une CLI pratique ne doit jamais devenir un bypass : la confirmation requise par chaque write-path est conservée, et la voie user-scope Claude cloud est explicitement **refusée** par cette façade. Elle reste réservée à la commande spécialisée avec deux confirmations indépendantes.

| Sous-commande | Nature | Mutation | Limites |
|---|---|---|---|
| `vmmu adapter matrix` | Matrice statique des six adapters et de leur couverture | Aucune | Ne prouve pas un host réel |
| `vmmu adapter doctor --profile … --adapter …` | Observe runtime et configuration project-local | Aucune | Host/trust/user-scope = `NOT_OBSERVED` |
| `vmmu adapter validate --profile … --adapter …` | Valide profile, workspace, identité et couverture déclarée | Aucune | N’installe ni ne teste l’hôte |
| `vmmu adapter stage --profile … --adapter … --confirm` | Route le staging déjà défini par l’adapter | Selon l’adapter, runtime projet seulement | Confirmation toujours requise |
| `vmmu adapter configure --profile … --adapter …` | Preview, ou application project-local avec `--apply-project --confirm` | Selon l’adapter, projet seulement | User-scope refusé par conception |

## 2. Matrice livrée

| Adapter | Couverture déclarée | État hôte réel |
|---|---|---|
| `claude-code-local` | `COMPACTION_AWARE` | Host local non réobservé dans M6 |
| `claude-code-cloud` | `CLOUD_STAGED_NOT_LIVE` | trust réel et preuve web `NOT_RUN` |
| `codex` | `PARTIAL_LOCAL_TOOLS` | client/trust réels `NOT_RUN` |
| `gemini` | `TOOL_GUARD_NO_POST_COMPACTION` | client/trust réels `NOT_RUN` |
| `antigravity` | `TURN_GUARD_HARD` | host/trust réels `NOT_RUN` |
| `generic-mcp` | `MCP_ONLY` | pas de lifecycle par conception |

## 3. Garanties et refus

La CLI refuse un adapter inconnu, un profil/workspace invalide et toute cible doctor symlinkée. Les routes stage/configure relaient les contrôles de l’adapter, y compris la revalidation de preview, le refus de conflit et la confirmation. Les entrées utilisateur ne choisissent jamais l’adapter runtime interne, une capability, un verdict, une session, un hash de dossier, une commande shell ou un chemin de fichier hôte.

La CLI **ne route jamais** `--apply-user-scope` vers Claude cloud. Cette restriction bloque une élévation accidentelle de portée à partir d’une commande générale. L’acte sensible demeure séparé, visible et protégé par le protocole M5-M.3b.

## 4. Preuve contrôlée

Trois tests red→green vérifient la matrice bornée, un doctor sur runtime manquant sans création de configuration, le stage non confirmé, le refus de la voie user-scope générale et le refus d’un adapter inconnu. La suite VERA passe à `482 passed, 37 subtests passed`; la roue isolée exécute `vmmu --help`, `vmmu adapter matrix` et un entry point MCP générique.

## 5. Hors M6-A

Le **dashboard visuel**, la gestion de projets multi-utilisateurs, un serveur web, l’installation automatique d’hôtes, l’application de trust user-scope, les tests de clients hôte réels et les writes cloud restent hors M6-A. Ils exigent des lots et des confirmations distincts ; aucun de ces éléments ne peut être déduit de cette CLI.
