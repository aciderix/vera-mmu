# M9-A — Pipeline de candidats de release CLI

**Statut :** `PARTIAL_PASS` — builder, manifest, archive et checksums définis et testés localement ; validation native Windows/Linux et toute diffusion publique restent distinctes.

## 1. Portée exacte

M9-A ajoute un **candidat de distribution CLI autonome**, mais ne crée pas de release GitHub, de tag, de signature, de canal de mise à jour ou d’installation utilisateur. Le script `scripts/build_cli_bundle.py` est un outil de build interne et ne change pas les contrats du Core, de la CLI, du MCP ou du bridge.

| Aspect | Contrat M9-A |
|---|---|
| Cibles | exclusivement `x86_64-unknown-linux-gnu` et `x86_64-pc-windows-msvc` |
| Mode de build | refus de compilation croisée : target = hôte Python publié |
| Exécutable | PyInstaller one-file, entrée minimale `scripts/cli_entry.py` vers `vera_mmu.__main__.main` |
| Archive | Linux `tar.gz`, Windows `zip`, nom versionné et déterministe |
| Intégrité | `release-manifest.json` canonique et `SHA256SUMS` dans le répertoire du candidat |
| Publication | aucune : pas de tag, release, signature, upload public ni GitHub Pages |

## 2. Identité contrôlée

Avant de construire, le builder exige un checkout Git propre et vérifie que `pyproject.toml`, `package.json`, `Cargo.toml` et `tauri.conf.json` déclarent la même version. La révision Git complète et le triple natif sont inclus dans `vera-release-manifest/v1`; le hash du binaire est inclus avant l’archivage, puis l’archive et le manifest reçoivent chacun leur SHA-256 dans `SHA256SUMS`.

Cette vérification refuse un arbre sale, une version divergente, une architecture non x64, un système non publié, un target hors allowlist ou un target distinct de l’hôte. Le builder ne prend ni chemin libre, ni remote Git, ni clé de signature, ni entrée de provenance venant d’un client VERA.

## 3. Intégration CI

La matrice `desktop-packaging.yml` exécute dans l’ordre : suite VERA complète, sidecar desktop natif, archive CLI native, puis bundles Tauri. Les fichiers du candidat sont joints aux artefacts de vérification de workflow, avec les installateurs desktop. Ainsi, une archive CLI ne peut pas être produite par cette voie si la suite ou le build desktop de sa plateforme échoue.

| Test local | Résultat |
|---|---|
| Contrat du builder : alignement de version, allowlist Linux/Windows, refus cross-build, JSON canonique | `4 passed` |
| Suite VERA complète après ajout | `508 passed, 43 subtests passed` |

## 4. Gates ouvertes

La production native de l’archive devra être observée sous Linux et Windows au run déclenché par le commit M9-A. Une release est ensuite interdite tant que la licence formelle n’est pas choisie, que la titularité/dépendances ne sont pas vérifiées, que les signatures de plateforme ne sont pas disponibles et que les notes de release ne relient pas leurs affirmations aux hashes et preuves correspondants.

Le [contrat de release](../../release/RELEASE_CONTRACT.md) et le [modèle de notes](../../release/RELEASE_NOTES_TEMPLATE.md) imposent ces limites. Le dashboard WebDev reste hors distribution VERA à ce stade : aucun transfert de source ou déploiement GitHub Pages n’est effectué par M9-A.
