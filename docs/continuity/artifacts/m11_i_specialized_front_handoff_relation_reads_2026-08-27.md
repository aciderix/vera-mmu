# M11-I — Lectures spécialisées : Front, handoff et relation

**Date :** 2026-08-27  
**Baseline :** `5d3b9b7d7c5d8f30badbe6c95cd87c34362b8653` — M11-H livré localement, arbre propre, `544 passed`.  
**Verdict :** `PASS` pour la tranche M11-I définie ci-dessous. L’API universelle complète et l’universalisation globale restent `NOT_DONE`.

## Objet et périmètre

M11-I prolonge `ReadService` sans modifier les services métier existants. Les mécanismes de Front, handoff et relation continuent de valider eux-mêmes leurs hashes, profils, adresses d’entités et contraintes de persistance. Cette tranche ne crée ni migration, ni table, ni index, ni capacité, ni preuve, ni mutation de mémoire.

| Ressource | Entrée publique | Résultat et garde-fou |
|---|---|---|
| Front courant | `ReadService.current_front`, `vmmu get-front`, `mmu_get_front` | Résout uniquement le snapshot le plus récent persistant; aucun identifiant de Front ne provient du client. |
| Handoff courant | `ReadService.latest_handoff`, `vmmu get-handoff`, `mmu_get_handoff` | Résout uniquement le dernier handoff validé par le store; aucun dossier, hash, session ou chemin client n’est accepté. |
| Front exact | `ReadService.read(vera://…/front/<id>)` | Retourne une révision Front immutable après validation de l’adresse et du `project_id`. |
| Handoff exact | `ReadService.read(vera://…/handoff/<id>)` | Retourne le handoff exact et son payload JSON déjà vérifié par `HandoffService`, sous forme structurée. |
| Relation exacte | `ReadService.read(vera://…/relation/<id>)` | Retourne l’arête immutable et les deux adresses d’entités canoniques calculées par `RelationService`. |
| Adressage | `CORE_RESOURCE_TYPES` | `handoff` devient un type d’adresse VERA accepté; les adresses sont toujours générées/validées par `make_address` et `parse_address`. |
| Manifeste | `TOOL_NAMES` | `mmu_get_front` et `mmu_get_handoff` modifient le manifeste canonique et donc le `mcp_build_hash`. |

## Contrat de sûreté

> **Le MCP ne sélectionne jamais le pointeur persistant.** Les tools `mmu_get_front` et `mmu_get_handoff` ne prennent aucun paramètre. Les lectures de versions ou de relations historiques ne sont possibles que via `mmu_read` et une adresse canonique exacte liée au projet déjà ouvert par le serveur.

| Cas vérifié | Résultat |
|---|---|
| Front/handoff exacts | Les identifiants, hashes et payloads récupérés correspondent aux enregistrements persistants. |
| Relation exacte | Les adresses `from_address` et `to_address` sont des adresses d’entités VERA canoniques. |
| Projet distinct | Une adresse associée à un autre `project_id` est refusée avant résolution. |
| Handoff absent / identifiant inexistant | Le refus de service devient une `ReadApiError` fermée, sans détail de stockage. |
| Lecture | Aucune modification du journal d’audit avant/après les lectures de Front, handoff et relation. |
| MCP | Les nouveaux tools n’exposent ni `profile_path`, ni identifiant, ni session, ni hash, ni chemin contrôlés par le client. |
| FIND | Les nouvelles ressources restent volontairement hors FIND : elles n’ont ni titre libre ni mécanisme d’indexation introduit par ce lot. |

## Validation observée

```text
Contrat M11-I spécialisé :                   3 passed in 2.17s
Cible M11-H/Front/relations/MCP/CLI :        30 passed in 17.45s
Régression intégrale VERA :                 547 passed in 63.06s
```

Les tests créent un profile documentaire, un Front strictement profilé, un Resume Dossier réel, un handoff, deux entités et une relation configurée. Ils contrôlent les trois lectures exactes, les pointeurs sans sélection client, les erreurs cross-project/inexistantes, l’absence d’audit nouveau, la CLI et une session MCP stdio réelle.

## Limites et prochain travail

Cette tranche ne transforme pas READ en accès global à chaque table. Les assets, preuves, evidence, capabilities, gates, executions, symboles, profile et les parcours `related` nécessitent des contrats dédiés compte tenu de leurs formats, règles d’admission, données binaires, politiques ou dépendances. Les vues resume détaillées, les mutations memory/Front/handoff, l’API work/evidence, le Dashboard, la compatibilité/parité ARET, les hôtes réels et les providers VCS restent hors scope.
