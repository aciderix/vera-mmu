# M11-C.1 — Surface publique CLI/MCP pour bundle et import documentaire

**Date :** 2026-08-27
**Baseline :** `986f28d20ed3b9ebee10bbbdabd0fccafb5e7a2c` — M11-B livré localement, arbre propre, `536 passed`.
**Statut :** `PASS` pour la sous-tranche de transport public. M11-C global reste `IN_PROGRESS`.

## Objet

Cette sous-tranche expose les primitives M11-B sans réimplémenter leur logique métier dans les transports. La CLI et le MCP appellent le Core existant et conservent les contrôles de policy, identité, non-fusion, preview, hash et provenance. Aucun outil ne construit une commande, n’accepte de contenu à persister, ni ne reçoit un chemin de sortie de bundle.

| Surface | Interface livrée | Garantie de sûreté |
|---|---|---|
| CLI | `vmmu bundle-export <profile> --bundle-id <id> --confirm` | L’identifiant est validé par le Core; la sortie est confinée sous `.vera-mmu/bundles`. |
| CLI | `vmmu bundle-restore <profile> --bundle <archive> --confirm` | Restauration hors serveur MCP, vers une cible vide et de même identité seulement. |
| CLI | `vmmu project-import <profile> --document <relative> ... [--apply --confirm]` | Sans `--apply`, produit un preview sans contenu. Avec `--apply`, relit les fichiers et importe uniquement `OBSERVED`. |
| MCP | `mmu_export_bundle(bundle_id, confirm)` | Aucun champ de chemin client; le Core produit le bundle dans le runtime du projet. |
| MCP | `mmu_preview_project_documents(documents, batch_id, knowledge_type_id, knowledge_type_label)` | Lecture explicite et confinée, sans mutation ni retour du contenu source. |
| MCP | `mmu_import_project_documents(..., preview_hash, confirm)` | Recalcule le preview depuis le disque et exige son hash exact avant l’import. Aucun statut, contenu, provenance ou chemin absolu client n’est admis. |
| Manifest MCP | `TOOL_NAMES` inclut les trois nouveaux outils et `mmu_sync_memory` | La surface publique fait partie du hash canonique `mcp_build_hash`. |

## Décision de périmètre

La restauration n’est pas exposée par le serveur MCP actif : remplacer le runtime hébergeant le serveur pendant que sa base SQLite est ouverte créerait une surface de concurrence et de disponibilité non justifiée. La restauration est donc proposée via la CLI, qui appelle le mécanisme Core avant l’ouverture d’un store cible. Cette frontière conserve l’atomicité et le refus de fusion de M11-B.

> Une absence de surface MCP de restauration n’est pas une absence de mécanisme de restauration : c’est une restriction délibérée du transport pour préserver l’intégrité du store actif.

## Validation observée

```text
Tests M11-C.1 CLI/MCP ciblés : 17 passed in 15.27s
Régression complète VERA :       538 passed in 58.99s
M11-B déjà couvert :             7 tests dédiés, inclus dans la suite complète
```

Les scénarios exercés couvrent la confirmation obligatoire, l’absence de chemin client dans le schéma MCP d’export, le preview sans contenu, le binding `preview_hash`, l’import `OBSERVED`, le manifest MCP canonique et les régressions stdio/lifecycle préexistantes.

## Limites explicites

M11-C reste ouvert pour le Doctor composite, les autres commandes universelles, les API de lecture/boot supplémentaires et les surfaces d’intégration complètes. Le lot n’ajoute pas de Dashboard, d’import automatique, de sources réseau, de Git history, d’issues, de migration/parité ARET ni de publication distante.
