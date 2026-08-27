# M11-A — Project Profile et catalogues déclaratifs complets

**Date :** 2026-08-27  
**Statut :** `PASS` dans le périmètre M11-A  
**Révision de clôture :** `fb6a1ac2b091cbe662cf0036000d596f770133a9`

## Objet

M11-A ferme la lacune de configuration déclarative identifiée par l’audit M11. Un nouveau projet VERA possède désormais un **Project Profile structuré**, les catalogues qu’il référence et une validation fermée avant utilisation dans un preview MCP. Cette livraison ne lance aucun runner, ne configure aucun hôte réel et ne modifie jamais le code métier du projet cible.

| Élément exigé | Livraison M11-A | Preuve |
|---|---|---|
| Identité, workspace, storage et identité hashée | Conservés et normalisés, avec chemins relatifs confinés. | `identity.py`, tests identité/workspace existants. |
| Description et domaine du projet | `project.description` canonique et `project.domain` déclaratif. | Bootstrap déterministe et test de chargement. |
| Resume et Front configurables | `resume.template`, sections structurées `id`/`required`, et `front.fields` non vides, sans doublon. | Régressions `test_project_bootstrap.py`. |
| Taxonomies | Knowledge, entity et relation types déclarés, non vides, canoniques et sans doublon. | Validation de profil et six taxonomies de domaine. |
| Work, capabilities, gates et policies | Références explicites vers les catalogues project-local sous `.vera-mmu/`. | Chargeur `project_catalogs.py`, hash canonique et refus de chemins hors runtime. |
| Intégrations | Catalogue `agent-profiles.yaml` validé et sélection `integrations.enabled` explicite, sans doublon ni adapter absent. | Régression catalogue d’agents et validation liée. |
| Modèles de domaine | Templates distincts Software, Game, Research, Data, Hardware et Documentation. | Test de six initialisations indépendantes. |

## Contrat de sécurité et déterminisme

Le bootstrap génère sept fichiers prévisualisés, hashés et écrits atomiquement après confirmation : `project.yaml`, `playbook.md`, `capabilities.yaml`, `gates.yaml`, `policies.yaml`, `agent-profiles.yaml` et `sync-policy.json`. Les chemins de catalogues doivent rester sous le runtime `.vera-mmu`; un symlink, une absence, un fichier non régulier, une clé YAML dupliquée, un format inconnu ou un document volumineux est refusé.

Les capability declarations et gate declarations sont validées avec schémas fermés. Une capability ne peut contenir aucune clé `command`, ni type, runner, policy réseau, validator, timeout, schéma de paramètres ou liste d’artefacts non déclarés. Une gate ne peut référencer qu’une capability déclarée dans le même catalogue. Cette validation n’est pas une exécution : les runners restent le lot M11 suivant et demeurent fail-closed.

Le preview MCP charge maintenant ces catalogues avant de compiler. Il publie et incorpore dans son hash les valeurs `profile_hash`, `capability_catalog_hash`, `gate_catalog_hash` et `policy_hash`. Un catalogue absent ou invalide empêche donc la génération au lieu d’être ignoré.

## Preuves exécutées

| Contrôle | Résultat |
|---|---|
| Régressions bootstrap, profil, catalogues et génération | `PASS` — création, normalisation, liens, YAML dupliqué, path traversal, symlink, command libre, gate non liée, catalogue absent et agent absent sont couverts. |
| Initialisation CLI temporaire | `PASS` — les sept fichiers sont créés uniquement sous `.vera-mmu`, puis le profil Research est chargé avec cinq sections de reprise. |
| Six modèles de domaine | `PASS` — chaque template charge sa taxonomie distincte. |
| Suite VERA intégrale | `PASS` — `523 passed, 43 subtests passed` après les commits M11-A. |
| Publications fonctionnelles | `PASS` — `e92edf7`, `1d9d8a8`, `88af9aa`, `a0e09cf` et `fb6a1ac` poussés linéairement sur `main`. |

## Frontières conservées

M11-A ne prétend pas que les catalogues déclenchent une capability, réparent une installation ou administrent un adapter. Les **runners sûrs** restent M11 phase 4, les **bundles/import/export** phase 5, la **CLI/Doctor globale** phase 7 et les **éditeurs visuels** phase 8. Les preuves des hôtes agents réels restent différées et Claude Cloud conserve ses deux confirmations user-scope distinctes.

## Références

[1]: ../../../src/vera_mmu/identity.py "Validation canonique du Project Profile"
[2]: ../../../src/vera_mmu/project_catalogs.py "Catalogues project-local et hashes"
[3]: ../../../src/vera_mmu/project_bootstrap.py "Bootstrap prévisualisé et atomique"
[4]: ../../../tests/test_project_bootstrap.py "Régressions M11-A"
[5]: ../../../tests/test_project_operations.py "Preview MCP lié aux catalogues"
