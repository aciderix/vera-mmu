# M11-K — Parcours relationnel `related` borné

**Date :** 2026-08-27  
**Baseline :** `6b8b526` — M11-J livré localement, `549 passed`.  
**Verdict :** `PASS` dans le périmètre M11-K.

## Portée

M11-K ajoute `ReadService.related`, la commande CLI `related` et le tool MCP `mmu_get_related`. Le parcours est réservé aux entités VERA exactes du projet courant. Il ne crée, modifie ou évalue aucun objet; il ne déclenche aucune capability, gate, synchronisation ou recherche de contenu.

| Contrat | Garantie effective |
|---|---|
| Racine | Une adresse `vera://…/entity/<id>` strictement canonique et project-bound est requise. |
| Direction | `INBOUND`, `OUTBOUND` ou `BOTH` exclusivement. |
| Profondeur | Bornée à 1–3 sauts. |
| Cardinalité | Bornée à 1–50 entités voisines. |
| Algorithme | Parcours en largeur (BFS), relations SQL triées par identifiant et voisins dédupliqués. |
| Cycles | Une entité déjà rencontrée n’est jamais revisitée ou retournée deux fois. |
| Sortie | Racine, paramètres appliqués, entités compactes (adresse/id/type/titre) et arêtes compactes (id/type/adresses), dont les deux extrémités figurent dans racine + nœuds retournés. |
| Transport | CLI et MCP reçoivent seulement l’adresse, la direction et les deux bornes; aucune requête, filtre SQL, record ou identité ne vient du client. |
| Manifest | `mmu_get_related` appartient à l’ensemble de tools MCP canonique hashé. |

## Validation observée

```text
Contrat M11-K :                           1 passed in 0.16s
Cible relations/lecture/CLI/MCP :        27 passed in 17.29s
Régression intégrale VERA :             550 passed in 68.70s
```

Le test forme un cycle `a → b → c → a` et une branche `b → d`. Il vérifie BFS, déduplication, ordre stable, profondeur, cardinalité — y compris l’exclusion des arêtes vers un voisin non admis par `max_nodes` —, refus d’une racine knowledge ou cross-project et absence d’événement d’audit à la lecture.

## Limites

`related` ne remplace pas une requête de graphe générale : aucun filtre de type de relation, pagination, traversal work/evidence, recherche sémantique, mutation, preuve, capability ou policy ne lui est ajouté. La lecture de symbol/profile, l’historique/listing d’evidences et les autres surfaces de produit restent des lots séparés.
