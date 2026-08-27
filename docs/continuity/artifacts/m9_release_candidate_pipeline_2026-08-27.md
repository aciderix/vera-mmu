# M9-A — Pipeline de candidats de release CLI

**Statut :** `PARTIAL_PASS` — candidats CLI et desktop de vérification attestés ; M9-B ajoute le workflow final par tag, l’assembleur et la documentation Apache/DCO. Toute signature, création de tag et diffusion publique restent distinctes et non exécutées.

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
| Candidat Linux extrait : `tar.gz`, `SHA256SUMS`, manifest et `vmmu scan` | archive et manifest `OK`; scan `OBSERVED` |

La construction locale Linux produit `vera-mmu-cli_0.1.0_linux-x64.tar.gz`. Les deux entrées de `SHA256SUMS` valident l’archive et `release-manifest.json`; l’archive contient uniquement `vmmu` et son manifest. Après extraction dans un répertoire temporaire indépendant, `vmmu scan <projet-vide>` retourne une enveloppe réussie avec `vera-scan-report/v1` et `status: OBSERVED`. Le manifest référence la révision source `98080dbc684245a9ab485b4ba78f3dc4868d61cc`, le triple Linux x64 et le SHA-256 du binaire emballé.

## 4. Gates ouvertes

Le run GitHub Actions `33067150688` est intégralement vert pour la révision `c9f67f1`. Chaque job exécute `508 passed, 43 subtests passed`, construit le sidecar, l’archive CLI native, les bundles desktop et téléverse l’archive de vérification.

| Runner | Job | Suite VERA | Candidat CLI | Artefact de vérification |
|---|---:|---|---|---|
| Linux x64 | `98499947163` | `508 passed, 43 subtests passed` en 74,67 s | `PASS` : archive `tar.gz`, manifest et SHA-256 | `9644430339`, 214 364 237 octets |
| Windows x64 | `98499946792` | `508 passed, 43 subtests passed` en 198,53 s | `PASS` : archive `zip`, manifest et SHA-256 | `9644534152`, 89 113 204 octets |

Les archives de workflow réunissent le candidat CLI et les bundles desktop ; elles restent temporaires et non signées. Une release est donc toujours interdite tant que la licence formelle n’est pas choisie, que la titularité/dépendances ne sont pas vérifiées, que les signatures de plateforme ne sont pas disponibles et que les notes de release ne relient pas leurs affirmations aux hashes et preuves correspondants.

## 5. M9-B — candidat final par tag et documentation publique

Le workflow `release-candidate.yml` prépare désormais une vérification à partir d’un tag `v*`, avec les mêmes deux runners natifs. Après les tests, il construit le sidecar, la CLI autonome et les deux bundles desktop de la plateforme, puis `assemble_release_candidate.py` réunit les quatre fichiers du target avec un manifest `vera-release-candidate/v1` et `SHA256SUMS`. Il refuse un candidat CLI ou desktop incomplet, une cible hors liste, un artefact absent/symlinké ou des noms ambigus.

Le workflow ne possède qu’une permission `contents: read`, puis téléverse un artefact de vérification. Il ne signe pas, ne crée pas de tag, ne crée pas de release GitHub et ne publie pas GitHub Pages. Son contrat statique et celui du builder CLI sont couverts par six tests ; toute la suite locale passe à `510 passed, 43 subtests passed`.

La préversion possède également son README public, `LICENSE` Apache-2.0, `NOTICE`, règles DCO `CONTRIBUTING.md` et politique de marque `TRADEMARKS.md`. Le retrait de `LICENSE-PENDING.md` est corroboré par les métadonnées de roue : `License: Apache-2.0` et classifieur OSI Apache. La titularité de droit demeure une responsabilité du propriétaire et des contributeurs ; le DCO structure les contributions futures mais ne remplace pas un audit juridique.

Le run manuel `33070861267`, sur la révision `b5b41b954634fcad08790b3bf159b9329a3d22bc`, a passé intégralement : Linux x64 (`98512443152`) exécute `510 passed, 43 subtests passed` en 77,18 s ; Windows x64 (`98512443367`) exécute le même total en 265,58 s. Les deux jobs passent ensuite la construction sidecar/CLI, les bundles desktop, l’assemblage final non signé et le téléversement.

| Plateforme | Artefact CI candidat | Taille | Statut |
|---|---:|---:|---|
| Linux x64 | `9645991442` | 214 368 098 octets | présent, non expiré, non signé |
| Windows x64 | `9646108111` | 89 111 512 octets | présent, non expiré, non signé |

Une tentative de téléchargement local du ZIP Linux d’artefact s’est interrompue en transport (`unexpected EOF`) sans exécuter son contenu. Ce défaut de téléchargement local ne contredit pas les étapes CI `Assemble` et `Upload` réussies, mais la vérification finale devra re-télécharger les artefacts **issus du tag exact** et valider leurs `SHA256SUMS` avant publication.

Le [contrat de release](../../release/RELEASE_CONTRACT.md) et le [modèle de notes](../../release/RELEASE_NOTES_TEMPLATE.md) imposent ces limites. Le dashboard WebDev reste hors distribution VERA à ce stade : aucun transfert de source ou déploiement GitHub Pages n’est effectué par M9-A.
