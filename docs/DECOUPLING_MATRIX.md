# Registre de découplage ARET-MMU → VERA-MMU

Ce registre est une feuille de contrôle, non une liste de souhaits. Une ligne ne passe à `DONE` que lorsque l’abstraction cible, les tests et la preuve de non-dépendance sont disponibles dans ce dépôt.

| Élément observé dans ARET-MMU | Couplage actuel | Abstraction cible | Destination prévue | Validation requise | Statut |
|---|---|---|---|---|---|
| `ARET://…` | Schéma d’adressage et ressources ARET fermées | `vera://<project>/<resource>/<id>` ; lecteur V1 en compatibilité | `core/addressing.py` | Round-trip, rejet des ressources inconnues, lecture V1 | TODO |
| `.aret-memory` / `ARET_MEMORY_DIR` | Répertoire et variables de store | `.vera-mmu/` / configuration de profil | `core/config.py`, CLI | Profil minimal, override borné, doctor | TODO |
| `component` | Entité de reverse engineering dans SQL | `entity` déclarée par type | `storage/schema`, `memory/entities.py` | Migration et intégrité référentielle | TODO |
| `function_symbol` | Symbole obligatoirement lié à un composant | `symbol` technique optionnel sur entité | `memory/symbols.py` | Migration V1, unicité configurable | TODO |
| `brick` | Unité fixe de roadmap | `work_item` avec type et hiérarchie | `work/` | Graphe, cycle de vie, garde du Front | TODO |
| `PIPELINES` Python | Catalogue fermé mais ARET-spécifique | Capability catalog déclaratif | `capabilities/` | Paramètres, confinement, timeout, policy | TODO |
| `ORACLES` Python | Oracles/scripts ARET fermés | Validators et capability runners de pack | `capabilities/`, `domains/aret/` | Evidence/execution/gate parity | TODO |
| `target/release/aret`, `bench/*`, Wine, MinGW, Unicorn | Toolchain et corpus métier | Dependencies déclarées par Domain Pack | `domains/aret/` | Core installable sans ces dépendances | TODO |
| `SERVER_INSTRUCTIONS` | Instructions MCP ARET statiques | Doctrine Core + policy/profile/resume générés | `compiler/instructions.py` | Snapshot déterministe lié au hash | TODO |
| Outils `aret_*` | Surface MCP écrite manuellement | API `vera_*` stable et registry contrôlée | `server/`, `compiler/` | Schémas, aliases temporaires, conformance | TODO |
| Racine de dépôt unique | Server et runners supposent un seul dépôt ARET | Workspace multi-racines et VCS optionnel | `core/workspace.py` | Projet no-git, multi-repo, traversal | TODO |
| Playbook ARET | Lois et sections métier codées en pratique | Playbook de projet + doctrine Core courte | `profiles/`, `domains/aret/` | Profil résolu, hash, reprise | TODO |
| Git autosync `.aret-memory` | Git obligatoire et portée ARET | `VersionControlProvider`, policy explicite | `adapters/vcs/` | NoVCS, Git, policy CONFIRM | TODO |
| Bundle V1 | Manifest centré sur objets ARET | Bundle V2 avec identity, profile et packs | `storage/bundle.py` | Altération, import non fusionnel, identité | TODO |

## Discipline

Chaque changement qui déplace une ligne de ce tableau doit inclure : les fichiers changés, les invariants affectés, les tests nouveaux ou mis à jour, une démonstration d’absence de dépendance ARET dans le Core et un commit atomique.
