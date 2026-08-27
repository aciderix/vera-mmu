# M11-O — Historique d’evidences borné

**Date :** 2026-08-27  
**Baseline :** `684c9ed` — M11-N livré localement, `555 passed`.  
**Verdict :** `PASS` dans le périmètre M11-O.

## Portée

M11-O ajoute une projection compacte de l’historique persistant d’evidences du projet courant. Elle est fournie par `ReadService.evidence_history`, la CLI `vmmu list-evidence <profile> --max-items N` et le tool MCP `mmu_list_evidence({max_items})`, inscrit au manifeste hashé.

| Contrat | Garantie effective |
|---|---|
| Source | Seule la table SQLite canonique `evidence` est lue; aucun runtime, fichier, réseau ou état de session n’est consulté. |
| Identité | Le store est project-bound; chaque résultat porte une adresse VERA canonique du projet actif. |
| Borne | `max_items` est le seul paramètre métier; entier strict de 1 à 100, défaut 20. |
| Ordre | `created_at DESC, id DESC` impose un ordre total déterministe. |
| Projection | Seulement `address`, `id`, `execution_id`, `evidence_type`, `verdict`, `content_hash`, `admission_status`, `created_at`. |
| Exclusions | Aucun `content`, `created_by`, parameters/environment/result d’execution, stdout/stderr, filtre, SQL ou record client. |
| CLI | La commande n’accepte que le profile local de lancement et `--max-items`. |
| MCP | Le schéma de `mmu_list_evidence` est exactement `{max_items}`; aucun project/profile/path/status/verdict/record ne peut être sélectionné par le client. |
| Non-mutation | La lecture n’ouvre aucune transaction, ne crée aucun audit et ne déclenche aucune execution, admission, proof, gate ou sync. |

## Validation observée

```text
Contrat Core + CLI + MCP M11-O :         13 passed in 15.61s
Régressions evidence/lecture/CLI/MCP :   27 passed in 17.87s
Régression intégrale VERA :             557 passed in 67.38s
```

Le contrat crée trois executions et trois evidences canoniques, vérifie la borne, l’ordre, la projection sans contenu ni acteur, l’absence d’audit et le refus des bornes invalides. Il appelle ensuite la CLI réelle et un serveur/client MCP stdio réel, qui refuse une borne supérieure à 100.

## Limites

Cette tranche ne fournit ni recherche ni filtre d’evidence, pagination/cursor, contenu de preuve, export, mutation, admission/proof/gate, statut de session de reprise ou compatibilité `mmu://`. Ces sujets restent séparés.
