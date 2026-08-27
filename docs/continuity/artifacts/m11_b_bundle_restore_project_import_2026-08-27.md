# M11-B — Bundle, restauration non fusionnelle et import documentaire observé

**Date :** 2026-08-27  
**Baseline Git :** `bb3606ae1ad390cd437e2e89e66d5986bfd67030` (`HEAD = origin/main = merge-base` avant modification)  
**Statut :** livré et vérifié localement ; surface CLI/MCP publique réservée au lot M11-C.

## Objet

Ce lot livre les primitives Core project-agnostic nécessaires à l’export et à la restauration d’une mémoire VERA, ainsi qu’un import explicite et non fusionnel de documents déjà présents dans un projet. Il ne crée aucune dépendance conceptuelle envers ARET et ne modifie pas les dépôts de référence.

| Surface | Contrat livré |
|---|---|
| `BundleService.export` | Génère un ZIP sous `.vera-mmu/bundles/<bundle-id>.zip` après confirmation explicite et contrôle de `filesystem.write`. Le bundle contient un manifest canonique, le snapshot SQLite, les déclarations runtime, les artefacts, le ledger de migrations et les SHA-256 correspondants. |
| `restore_bundle` | Vérifie la structure ZIP, l’absence de traversal/symlink, les bornes de taille, chaque hash, l’intégrité SQLite, les clés étrangères, le ledger de migrations et l’identité de projet. La restauration exige une cible vide ; elle est idempotente uniquement si la cible est déjà exactement égale au bundle. |
| Permutation runtime | Prépare un staging isolé puis permute le runtime de façon contrôlée. En cas d’échec de la permutation finale, le runtime antérieur est remis en place. |
| `preview_project_document_import` | Lit uniquement une liste explicite de documents UTF-8 réguliers, bornés et situés dans les racines de workspace. Le preview est hashé et lié aux octets relus. |
| `apply_project_document_import` | Refuse toute fusion, exige la confirmation/policy d’écriture, revalide le preview, enregistre les documents comme knowledge `OBSERVED`, et attache une provenance immuable avec chemin, lignes et SHA-256. Un replay exact ne crée aucune écriture supplémentaire. |

## Invariants et garanties contrôlés

| Invariant | Contrôle du lot |
|---|---|
| I003 — knowledge append-only | L’import documentaire passe par les ledgers append-only existants et n’effectue aucune réécriture de knowledge. |
| I010 — bundle / chaîne de hash | Le manifest canonique inventorie tous les membres, les artefacts et le hash du snapshot mémoire ; toute altération est refusée avant mutation cible. |
| I011 — identité projet | Le manifest, le profil cible et le `store_metadata.project_identity` du SQLite doivent être strictement identiques. |
| I013 — filesystem policy | Export, restauration et import demandent `confirm=True` et respectent la décision déclarée de `filesystem.write`. |
| I014 — confinement | Les membres ZIP, le runtime, les documents source et le staging refusent traversal, symlink et chemins non réguliers. |
| Non-fusion | Un runtime contenant déjà une mémoire divergente est refusé. Un import documentaire n’accepte qu’une cible knowledge vide, sauf replay exact du ledger existant. |

## Validation observée

Les sept tests de contrat ajoutés couvrent l’export/restauration de bout en bout, l’altération du ZIP, l’identité de projet divergente, la cible non vide, l’idempotence exacte, la confirmation explicite, le rollback de la permutation runtime, l’import documentaire `OBSERVED`, la provenance, les symlinks, le preview périmé et la non-fusion.

```text
Tests ciblés M11-B + surfaces adjacentes : 54 passed in 3.31s
Régression complète VERA :              536 passed in 52.96s
Diff whitespace :                       git diff --check = PASS
Couplage ARET dans les nouveaux modules : absent (contrôle lexical ciblé = PASS)
```

## Limites explicites

Le lot n’expose pas encore `mmu_export_bundle`, `mmu_import_bundle` ou `mmu_restore` via la CLI ou le MCP : cette intégration publique demeure dans M11-C. Il n’importe pas automatiquement l’intégralité d’un projet ni des sources réseau ; seuls des chemins documentaires explicitement fournis sont admis, sans exécution ni promotion `PROVEN`.

> Le lot fournit un mécanisme Core vérifié. Il ne prétend pas achever les surfaces de transport, le Dashboard, les importeurs de sources supplémentaires ou la parité de migration ARET.
