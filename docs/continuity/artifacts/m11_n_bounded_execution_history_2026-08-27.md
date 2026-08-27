# M11-N — Historique d’executions borné

**Date :** 2026-08-27  
**Baseline :** `0ce7615` — M11-L livré localement, `553 passed`.  
**Verdict :** `PASS` dans le périmètre M11-N.

## Portée

M11-N ajoute une projection compacte de l’historique persistant d’executions du projet courant. Elle est fournie par `ReadService.execution_history`, la CLI `vmmu list-executions <profile> --max-items N` et le tool MCP `mmu_list_executions({max_items})` inscrit dans le manifeste hashé.

| Contrat | Garantie effective |
|---|---|
| Source | Seule la table SQLite canonique `execution` est lue; aucun runtime, adapter, fichier, réseau ou session n’est consulté. |
| Identité | Le store est déjà project-bound; chaque résultat porte une adresse VERA canonique du projet actif. |
| Borne | `max_items` est le seul paramètre métier; entier strict de 1 à 100, défaut 20. |
| Ordre | `started_at DESC, id DESC` assure un ordre total déterministe, y compris pour des timestamps identiques. |
| Projection | Seulement `address`, `id`, `capability_id`, `status`, `started_at`, `finished_at`, `artifact_hash`. |
| Exclusions | Aucun `parameters`, `environment`, `result`, stdout/stderr, contenu d’evidence, record client, filtre ou SQL libre. |
| CLI | La commande n’accepte que le profile local de lancement et la borne `--max-items`. |
| MCP | Le schéma de `mmu_list_executions` est exactement `{max_items}` : aucun project/profile/path/status/capability/record ne peut être sélectionné par le client. |
| Non-mutation | La lecture n’ouvre aucune transaction, ne crée aucun audit et ne déclenche aucune execution, evidence, admission, proof, gate ou sync. |

## Validation observée

```text
Contrat Core + CLI + MCP M11-N :         13 passed in 16.27s
Régressions execution/lecture/CLI/MCP :  24 passed in 18.63s
Régression intégrale VERA :             555 passed in 70.43s
```

Le contrat crée trois executions `NOOP` canoniques, vérifie la borne, l’ordre, la projection sans payload, l’absence d’audit et le refus des bornes invalides. Il appelle ensuite la CLI réelle et un serveur/client MCP stdio réel, qui refuse une borne supérieure à 100.

## Limites

Cette tranche ne fournit ni recherche ni filtrage d’historique, pagination/cursor, listing d’evidences, contenu de résultat, export, mutation, admission/proof/gate, lecture de session de reprise ou compatibilité `mmu://`. Ces sujets restent des lots séparés.
