# M8 — Conformance multi-domaines et topologies de projet

**Statut :** `PARTIAL_PASS` — conformance Core/CLI/bridge attestée localement et sur Linux CI. Le premier runner Windows a révélé deux défauts de portabilité dans les **tests** ; ils sont corrigés localement et nécessitent une seconde exécution native avant qualification Windows.

## 1. Objet et frontière

M8 ne cherche pas à prétendre qu’un projet logiciel, data, recherche, documentation, jeu ou matériel possède les mêmes règles métier. Il vérifie une propriété plus limitée et fondamentale : **VERA applique le même contrat project-local à chacun de ces domaines déclaratifs**, sans introduire de vocabulaire, de scanner ou d’installer spécifique dans le Core.

> Une fixture M8 démontre la transportabilité du protocole VERA ; elle ne valide ni les outils, ni les oracles, ni les résultats métier propres au domaine concerné.

## 2. Matrice de fixtures

| Domaine déclaré | Marqueur minimal observé | Voie CLI testée | Voie desktop/bridge testée | Intégration contrôlée |
|---|---|---|---|---|
| `software` | `pyproject.toml` | `scan`, `init-project` en preview | init preview/apply | `generic-mcp` project-local |
| `data` | `requirements.txt` | `scan`, `init-project` en preview | init preview/apply | `generic-mcp` project-local |
| `research` | `README.md` | `scan`, `init-project` en preview | init preview/apply | `generic-mcp` project-local |
| `documentation` | `docs/guide.md` | `scan`, `init-project` en preview | init preview/apply | `generic-mcp` project-local |
| `game` | `package.json` | `scan`, `init-project` en preview | init preview/apply | `generic-mcp` project-local |
| `hardware` | `Cargo.toml` | `scan`, `init-project` en preview | init preview/apply | `generic-mcp` project-local |

Chaque itération vérifie que le scan reste `OBSERVED` et sans écriture, que la CLI ne produit qu’une preview, que le bridge fixe sa racine native et applique uniquement après `confirm: true`, puis que l’adapter `generic-mcp` est résolu par un `Agent Profile` déclaré. La génération, le staging et l’installation sont prévisualisés et revalidés ; seule la configuration project-local `.mcp.json` est écrite à la fin du parcours.

## 3. Topologies et continuité

| Cas | Fait vérifié | Résultat attendu |
|---|---|---|
| Sans Git | Aucun marqueur VCS présent | Workspace valide et `vcs_roots = ()` |
| Mono-repo | Racine Git, deux racines additionnelles internes | Trois racines confinées et une seule racine VCS |
| Multi-repo imbriqué | Racine Git et `vendor/.git` | Deux racines VCS distinctes, sans sortie du projet |
| Clone Git | `.vera-mmu/` committé/poussé vers un bare remote local | Le clone ouvre la même SQLite, retrouve une capability et ne contient pas de WAL transitoire |

Le scénario de clone passe par la policy project-local `vera-memory-sync-policy/v1`. Les trois transactions de seed retournent `SYNCED`; aucun merge SQLite n’est tenté. Le clone est une récupération Git d’un état cohérent, non la réconciliation de deux bases concurrentes.

## 4. Correction de surface MCP associée

La conformance complète a révélé que `mmu_acknowledge_resume` exposait le résultat d’une **seconde** tentative Git après la transaction Core. La première tentative post-commit réussissait, puis la seconde retournait `NO_CHANGES`, masquant le statut `SYNCED` réellement produit. `_mutating_call` renvoie désormais `store.last_sync_status`, soit le statut de la synchronisation automatiquement tentée après le commit SQLite. Il ne relance pas Git.

Cette correction ne transforme aucun verdict métier : une mutation réussie demeure réussie, et une erreur Git reste un statut de synchronisation séparé et observable.

## 5. Résultats attestés

La nouvelle suite `tests/test_m8_domain_conformance.py` passe avec **3 tests et 6 sous-tests**. La suite VERA complète passe avec **504 tests et 43 sous-tests**. Une roue isolée construite depuis ce checkout exécute `vmmu scan` sur un projet temporaire et produit un `vera-scan-report/v1` `OBSERVED`.

Le contrôle de frontière ne détecte aucune référence `ARET`, Wine, Ghidra, MinGW ou PE32 dans `src/vera_mmu/` hors du chemin autorisé `src/vera_mmu/domain_packs/aret/`, ni dans la fixture M8.

## 6. Observation Windows et remédiation

Le run GitHub Actions `33063264121` a validé intégralement Linux x64, y compris la suite VERA avant la construction des bundles. Windows x64 a arrêté la suite avant le packaging, sans atteindre le sidecar ni les installateurs. Les échecs proviennent de deux mécanismes de test rendus visibles par la sémantique de Windows :

| Constat Windows | Cause | Correction | Garantie préservée |
|---|---|---|---|
| Suppression temporaire de `memory.sqlite` refusée | `addCleanup(store.close)` s’exécutait après la sortie de `TemporaryDirectory`; Windows interdit de supprimer une base encore ouverte | fermeture explicite du `MemoryStore` dans un `finally` avant la suppression | fermeture claire sans écriture supplémentaire, WAL et policy inchangés |
| Égalité de `Path` échouée malgré le même fichier | le Core conserve le chemin physique canonique, tandis que la fixture comparait l’alias long temporaire | l’attendu de test est canonisé par `project.resolve()` ou `target.resolve()` | racine canonique, contrôles anti-symlink et confinement inchangés |

Il ne s’agit ni d’un contournement de test, ni d’une modification du Core pour rendre Windows moins strict. Les tests continuent de vérifier les mêmes chemins project-local, écritures et refus ; ils comparent désormais l’identité canonique que le Core utilise déjà pour la sécurité.

La suite complète après correction est de nouveau `504 passed, 43 subtests passed` localement. La seconde matrice CI doit reproduire ce résultat sur Windows et reconstruire les artefacts de vérification avant que M8 soit qualifié sur les deux plateformes.

Le premier push du correctif de tests n’a pas créé de nouvelle matrice car les filtres `paths` du workflow ne couvraient que le Core, le bridge, le packaging et le manifeste Python. Le workflow inclut désormais `tests/**` pour les événements `push` et `pull_request`. Cette correction CI ne modifie ni les tests exécutés, ni le produit, ni les artefacts attendus ; elle garantit qu’un changement de conformance est vérifié sur les mêmes runners natifs que le desktop.

## 7. Limites et suite

M8 n’exécute aucun agent réel, oracle de domaine, installation sur machine utilisateur, merge de SQLite concurrentes ou release. Les tests d’hôtes Claude, Codex, Gemini et Antigravity restent explicitement différés à la campagne finale.

Après la publication du correctif Windows, la matrice GitHub Actions réexécutera cette même suite complète sur Windows et Linux avant le packaging. Une fois les deux runners observés, le lot de conformance pourra être qualifié sur les plateformes ciblées ; la release, les signatures et la migration demeureront M9.
