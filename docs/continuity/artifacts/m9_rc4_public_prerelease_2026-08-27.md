# M9.EXIT — Publication de VERA-MMU v0.1.0-rc.4

**Statut :** `PARTIAL_PASS` — la préversion publique gratuite est publiée, avec fichiers, manifests et SHA-256 vérifiés. Elle reste non signée et ne constitue pas une validation d’hôtes réels.

## Publication

La [GitHub Pre-release v0.1.0-rc.4](https://github.com/aciderix/vera-mmu/releases/tag/v0.1.0-rc.4) est publiée le 27 août 2026. Elle porte le tag annoté `v0.1.0-rc.4` sur la révision `3519f760497c03d4744448f416b9e7deaafae790`.

Elle est explicitement marquée **Pre-release** et **non signée**. Les notes expliquent que Windows peut afficher un éditeur non vérifié et demandent de vérifier les hashes avant toute exécution.

## Contrôles de provenance et d’intégrité

Le run de tag [33078499592](https://github.com/aciderix/vera-mmu/actions/runs/33078499592) est vert. Linux x64 (job `98538971733`) passe `512 passed, 43 subtests passed` en 96,84 s ; Windows x64 (job `98538972155`) passe `512 passed, 43 subtests passed` en 244,72 s. Les deux jobs passent ensuite sidecar, CLI, bundles desktop, assembleur de candidat et upload d’artefact.

Les artefacts CI `9649277094` (Linux) et `9649499388` (Windows) sont téléchargés passivement puis vérifiés par `sha256sum -c SHA256SUMS`. Chaque entrée des deux candidats est `OK`. Les manifests CLI et release restent distincts dans rc.4 ; le manifest public global relie les dix assets de plateforme et de provenance, tandis que `SHA256SUMS` vérifie ces dix assets et le manifest global.

| Plateforme | Binaires publiés | Documents publiés |
|---|---|---|
| Linux x64 | CLI `.tar.gz`, AppImage, `.deb` | manifest CLI, manifest plateforme |
| Windows x64 | CLI `.zip`, NSIS `.exe`, MSI `.msi` | manifest CLI, manifest plateforme |
| Commun | — | manifest global et `SHA256SUMS` |

La page de release contient douze assets ajoutés, auxquels GitHub ajoute ses deux archives source standard. Le hash de l’asset public `SHA256SUMS` est `012aa9a9f3a0a2281756e1e429822fc5da19f5cc8baa4c9eb8ba3c3643bb56fd`.

## Limites résiduelles

Cette publication ne signe ni les exécutables Windows ni les fichiers Linux. Elle ne couvre pas macOS, ARM, mise à jour automatique, viewer GitHub Pages, installation sur ordinateur utilisateur ou comportement live avec Claude, Codex, Gemini et Antigravity. Les tags rc.1, rc.2 et rc.3 restent historiques et non publiables ; aucun asset ne leur a été attaché.
