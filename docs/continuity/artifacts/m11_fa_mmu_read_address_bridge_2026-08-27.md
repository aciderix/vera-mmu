# M11-F-A — Bridge d’adresse `mmu://` pour lecture

**Date :** 2026-08-27  
**Baseline :** `b51c8fd` — M11-E livré localement, `559 passed`.  
**Verdict :** `PASS` dans le périmètre M11-F-A.

## Portée

M11-F-A ajoute `parse_compat_address`, une couche de transition explicite qui accepte une adresse de lecture strictement canonique sous le schéma `mmu://` et la normalise vers l’adresse VERA persistée `vera://`. Le parseur canonique `parse_address` reste strictement VERA, ce qui évite de diluer la grammaire de stockage et la validation des écritures.

| Contrat | Garantie effective |
|---|---|
| Schémas admis | `vera://` canonique historique et `mmu://` canonique de transition en entrée de lecture seulement. |
| Normalisation | Une entrée `mmu://<project>/<resource>/<id>` valide produit l’objet Address canonique VERA; toutes les sorties restent `vera://`. |
| Validation | Type de ressource fermé, project id, identifiant, encodage percent et absence de traversal sont revalidés par le parseur VERA existant. |
| Refus | `ARET://`, majuscules, type inconnu, `%2F`, forme non canonique, segment absent et toute autre grammaire restent refusés. |
| Surface | `ReadService.read`, `read_batch` par délégation et `related` acceptent le bridge; CLI `read` et MCP `mmu_read` l’exercent. |
| Écriture | `make_address`, identités, migrations et addresses persistées restent `vera://`; aucune écriture ne reçoit l’alias. |
| VCS | Aucune extension VCS, sync, remote, branche ou push n’est introduite. |

## Validation observée

```text
Adressage + lectures Core/CLI/MCP :      12 passed in 3.09s
Régression intégrale VERA :             560 passed in 68.01s
```

Les tests couvrent la forme `mmu://` canonique et les refus syntaxiques. Une lecture Core, une CLI réelle et un appel MCP stdio réel utilisent le bridge et retournent l’adresse VERA persistée. Le bridge ne produit aucune mutation.

## Limites

Ce lot ne migre pas le schéma canonique de stockage vers `mmu://`, n’ajoute aucun alias `aret_*`, ne lit pas les ressources legacy `ARET://`, ne fournit aucune parité ARET et ne crée pas `VersionControlProvider` Git/Mercurial/SVN. La synchronisation Git project-local existante reste inchangée.
