# VERA-MMU

[![CI native](https://github.com/aciderix/vera-mmu/actions/workflows/desktop-packaging.yml/badge.svg?branch=main)](https://github.com/aciderix/vera-mmu/actions/workflows/desktop-packaging.yml)
[![Licence Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-0b7285.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](pyproject.toml)
[![Desktop](https://img.shields.io/badge/Desktop-Windows%20x64%20%7C%20Linux%20x64-2f855a.svg)](apps/desktop/README.md)
[![Préversion](https://img.shields.io/badge/Statut-pr%C3%A9version%20contr%C3%B4l%C3%A9e-d97706.svg)](docs/release/RELEASE_CONTRACT.md)

> **VERA-MMU** — *Verifiable Epistemics & Relational Architecture* — est un moteur local de mémoire, provenance et gouvernance vérifiables pour projets assistés par IA.

VERA empêche qu’une affirmation formulée par un agent devienne un fait du projet par simple répétition. L’état canonique est conservé dans le projet, les preuves et décisions restent traçables, et chaque intégration MCP passe par une préparation explicite et non destructive.

**Le produit est en préversion contrôlée.** La chaîne de build Windows/Linux, la CLI autonome et l’application desktop sont validées en CI native. Aucune release GitHub signée n’est encore publiée et les tests réels des fournisseurs d’agents restent volontairement différés jusqu’à la campagne finale.

## Pourquoi VERA-MMU ?

| Problème courant | Réponse VERA |
|---|---|
| Une IA « se souvient » d’un fait non vérifié | Mémoire SQLite canonique, provenance, evidence et décisions explicites. |
| Le contexte se dégrade ou une session redémarre | État project-local `.vera-mmu/`, reprise hashée et dossier de continuité. |
| Un MCP peut modifier le projet de façon opaque | **preview → contrôle de fraîcheur → confirmation → écriture atomique ou refus**. |
| Un agent pourrait obtenir un shell ou un chemin arbitraire | Capabilities, adapters, entrées et opérations strictement allowlistés. |
| Le même moteur doit servir plusieurs domaines | Core générique ; concepts et outils métier confinés aux Project Profiles et Domain Packs optionnels. |
| La mémoire doit suivre le projet Git | Synchronisation opt-in bornée à `.vera-mmu/`, sur `origin` et la branche actuellement checkoutée. |

## Capacités attestées

VERA est testé sur des fixtures **software, data, research, documentation, game et hardware**, ainsi que sur les topologies sans Git, mono-repo, multi-repo et clone Git. La même séquence CLI, bridge desktop et MCP project-local est utilisée dans chaque cas.

| Surface | Ce qui est disponible | Ce qui n’est pas encore revendiqué |
|---|---|---|
| Core Python | SQLite project-bound, migrations, audit, entities, relations, knowledge, evidence, gates et lifecycle | Validation métier externe ou oracle de domaine universel |
| CLI `vmmu` | Scan sans écriture, init project-local, génération, staging, preview/install contrôlé, doctor et memory sync | Une API de commandes libres ou un accès implicite à Git |
| MCP | Façade fermée, modèles d’adapters, reprise et opérations project-local | Preuve live auprès de chaque fournisseur d’agent |
| Desktop | Tauri v2 Windows/Linux, dialogue natif de dossier, bridge Python stdio embarqué | Installation effectivement testée sur une machine utilisateur |
| Mémoire Git | Commit/push optionnels de `.vera-mmu/` sur la branche courante | Pull implicite, merge automatique de SQLite ou staging des fichiers métier |
| Viewer web | Dashboard statique séparé, lecture/import-export de rapports | Installation MCP, accès au disque, shell ou bridge local depuis GitHub Pages |

La suite actuelle compte **508 tests et 43 sous-tests**, passée sur Linux x64 et Windows x64 avec build CLI autonome, sidecar et bundles desktop. Les résultats et limites détaillés figurent dans les [records de conformance M8](docs/continuity/artifacts/m8_multi_domain_conformance_2026-08-27.md) et de [candidats M9](docs/continuity/artifacts/m9_release_candidate_pipeline_2026-08-27.md).

## Installation depuis le source

La première release ne doit pas encore être téléchargée : les artefacts CI sont des candidats de vérification, non des binaires officiels. Pour évaluer le code depuis le source :

```bash
git clone https://github.com/aciderix/vera-mmu.git
cd vera-mmu

python3 -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows PowerShell : .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install .
vmmu --help
```

VERA requiert **Python 3.11 ou plus récent**. L’application desktop de développement nécessite en outre Node.js, pnpm, Rust et les dépendances Tauri propres à la plateforme ; voir le [guide desktop](apps/desktop/README.md).

## Parcours sûr : préparer un projet puis installer un MCP

Le flux ne touche pas le projet avant confirmation. Choisissez l’un des templates : `software`, `data`, `research`, `documentation`, `game` ou `hardware`.

```bash
# 1. Observer seulement : aucun contenu n’est lu et aucun fichier n’est créé.
vmmu scan /chemin/vers/mon-projet

# 2. Générer la preview de l’initialisation : toujours sans écriture.
vmmu init-project /chemin/vers/mon-projet \
  --template software \
  --project-id mon-projet \
  --project-name "Mon projet"

# 3. Appliquer uniquement après relecture de la preview et confirmation explicite.
vmmu init-project /chemin/vers/mon-projet \
  --template software \
  --project-id mon-projet \
  --project-name "Mon projet" \
  --apply --confirm
```

L’étape confirmée crée seulement les fichiers VERA project-local sous `.vera-mmu/`. Elle ne remplace pas un fichier existant, ne suit pas de symlink et refuse une configuration divergente.

```bash
# 4. Consulter les adapters déclarés et générer une configuration MCP en preview.
vmmu adapter matrix
vmmu generate /chemin/vers/mon-projet/.vera-mmu/project.yaml --adapter generic-mcp

# 5. Prévisualiser l’installation, puis l’appliquer explicitement.
vmmu install /chemin/vers/mon-projet/.vera-mmu/project.yaml --adapter generic-mcp
vmmu install /chemin/vers/mon-projet/.vera-mmu/project.yaml \
  --adapter generic-mcp --apply-project --confirm

# 6. Observer l’état sans le modifier.
vmmu adapter doctor --profile /chemin/vers/mon-projet/.vera-mmu/project.yaml --adapter generic-mcp
```

L’installation MCP peut écrire une configuration hôte **project-local** telle que `.mcp.json`, `.claude/`, `.codex/`, `.gemini/` ou `.antigravity/`, selon l’adapter choisi. Un conflit, une cible irrégulière ou un lien symbolique est un refus, jamais un écrasement.

## Application desktop

L’application desktop vise le parcours humain : lancer l’application, choisir un dossier par dialogue natif, scanner, renseigner le template, vérifier la preview puis confirmer l’installation. La fenêtre React n’a aucun plugin générique de filesystem ou de shell.

Le processus Rust parent démarre uniquement le sidecar `vmmu-desktop-bridge` via stdin/stdout. Il conserve la racine sélectionnée et le nonce du bridge ; ni la racine brute, ni un shell, ni un adapter arbitraire, ni une écriture de confiance ne sont fournis par le WebView.

Les formats actuellement construits en CI sont les suivants :

| Plateforme | CLI candidate | Desktop candidate |
|---|---|---|
| Windows x64 | ZIP avec `vmmu.exe` | NSIS `.exe` et MSI `.msi` |
| Linux x64 | TAR.GZ avec `vmmu` | AppImage et paquet Debian `.deb` |

Avant une release, chaque archive sera reconstruite depuis le tag, hashée, signée et décrite dans les notes de version. Consultez le [contrat de release](docs/release/RELEASE_CONTRACT.md) pour les gates exactes.

## Continuité Git et mémoire

La mémoire est dans le projet : `.vera-mmu/memory.sqlite`. Elle peut donc voyager avec le commit Git du projet si le projet choisit de la versionner. VERA ne transforme pas GitHub en API de contrôle du MCP ; un clone récupère simplement la mémoire qui appartient au commit checkouté.

La synchronisation est **opt-in** et pilotée par `.vera-mmu/sync-policy.json`. Après une transaction Core réussie, VERA consolide SQLite puis peut commit/push **uniquement** `.vera-mmu/`, vers le remote littéral `origin`, sur la branche courante (`CURRENT`).

```bash
# Lit la policy project-local ; ne prend aucun remote, branche ou commande Git en entrée.
vmmu memory-sync /chemin/vers/mon-projet/.vera-mmu/project.yaml
```

VERA ne fait jamais de `pull` implicite, ne merge jamais deux bases SQLite, ne stage jamais les fichiers métier du projet et ne rétrograde pas une mutation SQLite réussie si Git échoue. Un conflit ou une policy invalide produit un statut de refus distinct.

## Sécurité et modèle de confiance

| Garantie | Règle appliquée |
|---|---|
| Verdicts | Seul un `PASS` validé peut alimenter admission, proof ou gate. `FAIL`, `SKIPPED`, `ERROR` et `UNKNOWN` ne sont jamais promus. |
| Scan | Ne lit pas le contenu, ne suit pas les symlinks et n’exécute ni processus ni réseau. |
| Écritures | Précédées d’une preview, d’un contrôle de fraîcheur et d’une confirmation ; écritures atomiques ou refus. |
| Frontend desktop | Pas de privilège filesystem/shell générique ; commandes Tauri typées, bridge stdio fermé. |
| Git | Remote, branche, pathspec et opération contrôlés côté Core ; aucune commande Git fournie par le client. |
| Secrets | Aucun secret ne doit être commit, sérialisé dans la mémoire ou transmis par les surfaces UI. |

Les réglages de confiance **au scope utilisateur**, les bootstraps réseau et les secrets ne font pas partie du flux d’installation général. Ils exigent un processus séparé et des confirmations explicites juste avant écriture.

## Développement et vérification

```bash
# Suite complète
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q

# Build local d’un candidat CLI Linux depuis un checkout propre
python3 scripts/build_cli_bundle.py x86_64-unknown-linux-gnu

# Build du sidecar desktop, uniquement pour le triple natif
python3 scripts/build_desktop_sidecar.py x86_64-unknown-linux-gnu
```

La CI GitHub exécute la suite VERA avant les builds de sidecar, de CLI autonome et de desktop sur Linux et Windows. Les builds croisés ne sont pas une preuve de distribution.

## Architecture du dépôt

```text
src/vera_mmu/                 Core Python générique, CLI, MCP, adapters et bridge stdio
src/vera_mmu/domain_packs/    Domain Packs optionnels ; ARET reste isolé dans son pack
apps/desktop/                 Application Tauri v2 et frontend React sans droits locaux génériques
scripts/                      Builders contrôlés de sidecar et de candidats CLI
tests/                        Tests Core, sécurité, bridge, mémoire Git et conformance M8/M9
docs/continuity/              Plan vivant, mémoire factuelle, journal et artefacts de preuve
docs/release/                 Contrat, gates et modèle de notes de release
```

## Statut de roadmap

| Lot | Statut |
|---|---|
| M1–M3 | Core universel, persistence, evidence, gates et lifecycle : livré dans son périmètre borné |
| M4 | Pack ARET de compatibilité : conservé comme pack séparé ; la parité ARET complète n’est pas revendiquée |
| M5–M7 | MCP, adapters, CLI, bridge desktop, Tauri et mémoire Git project-local : livrés et testés |
| M8 | Conformance multi-domaines et topologies Git : `PASS` Linux/Windows |
| M9-A | Candidats CLI natifs, manifests, SHA-256 et CI : `PASS` Linux/Windows |
| Release officielle | En attente de licence, signature, tag, notes remplies et confirmation de publication |
| Agents réels | Claude, Codex, Gemini et Antigravity : volontairement `NOT_RUN` avant la campagne finale |

Les documents de contrôle détaillés sont le [plan vivant](docs/continuity/UNIVERSALIZATION_WORKPLAN.md), la [mémoire factuelle](docs/continuity/PROJECT_MEMORY.md), le [journal d’ingénierie](docs/continuity/ENGINEERING_LOG.md) et la [politique de sécurité](SECURITY.md).

## Contribution

Les contributions sont bienvenues sous **Apache-2.0**. Chaque contribution doit être signée selon le **Developer Certificate of Origin** avec `git commit -s`, respecter les frontières Core/Domain Pack et passer la suite de tests. Les règles complètes figurent dans [CONTRIBUTING.md](CONTRIBUTING.md).

Les futurs imports, portages ou adapters issus d’autres projets doivent documenter leur origine, licence, commit, hashes, crédits et compatibilité. VERA-MMU n’intègre pas implicitement du code source ARET-MMU.

## Licence et marque

Le code de VERA-MMU est distribué sous [Apache License 2.0](LICENSE). Le nom **VERA-MMU**, son développement long, son logo et l’identité des releases officielles sont traités séparément dans la [politique de marque](TRADEMARKS.md). Apache-2.0 ne donne pas le droit de présenter un fork ou un binaire modifié comme une release officielle.

## Liens utiles

- [Architecture de distribution desktop](docs/continuity/artifacts/m7_desktop_distribution_architecture_2026-08-27.md)
- [Conformance multi-domaines M8](docs/continuity/artifacts/m8_multi_domain_conformance_2026-08-27.md)
- [Pipeline de candidats M9](docs/continuity/artifacts/m9_release_candidate_pipeline_2026-08-27.md)
- [Contrat de release](docs/release/RELEASE_CONTRACT.md)
- [Signaler une vulnérabilité](SECURITY.md)
