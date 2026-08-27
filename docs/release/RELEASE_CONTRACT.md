# Contrat de release VERA-MMU

**Statut :** `M9_PREPARATION` — Apache-2.0, DCO et politique de marque sont versionnés ; aucune release, aucun tag de release et aucune signature ne sont créés par ce document.
**Mise à jour rc.4 :** la préversion gratuite non signée est publiée après validation native, conformément à l’exception explicitement autorisée. Les exigences de signature restent applicables à toute release stable ou diffusion élargie.

## 1. Objet et règle de sûreté

Ce contrat décrit la seule chaîne admissible pour distribuer VERA-MMU aux personnes et aux agents locaux. Il sépare strictement la vérification CI, les artefacts publiables et l’installation effective. Une archive de CI, même produite sur un runner natif, **n’est pas une release** tant que les gates de cette section ne sont pas satisfaites.

> La distribution ne confère aucune nouvelle autorité : la CLI et l’application desktop conservent les opérations VERA fermées, les écritures project-local en preview → fraîcheur → confirmation → atomicité/refus, et l’UI n’obtient jamais de capacité filesystem ou shell générique.

## 2. Identité et version unique

Une release porte un tag annoté `vMAJEUR.MINEUR.CORRECTIF`, sans préfixe alternatif. La version sans `v` doit être identique dans les quatre manifestes suivis : `pyproject.toml`, `apps/desktop/package.json`, `apps/desktop/src-tauri/Cargo.toml` et `apps/desktop/src-tauri/tauri.conf.json`.

| Élément | Règle de release | État au démarrage M9 |
|---|---|---|
| Version produit | Une SemVer unique, sans divergence de manifeste | `0.1.0` dans les manifestes inspectés |
| Tag Git | Tag annoté sur un commit `main` propre et déjà validé | Aucun tag de release créé |
| Révision source | SHA complet intégré au manifest de chaque archive | À produire par le builder M9 |
| Notes | Fichier `docs/release/RELEASE_NOTES_TEMPLATE.md` complété à partir de faits attestés | Template seulement |

La préversion corrigée est `v0.1.0-rc.4`. Le tag lisible utilise cette convention, tandis que les manifestes desktop portent l’identité MSI-compatible `0.1.0-4` et le paquet Python la forme PEP 440 équivalente `0.1.0rc4`. Le builder normalise uniquement cette forme Python vers `0.1.0-4`, puis refuse toute autre divergence. Cette dissociation est nécessaire car le bundle MSI exige un identifiant de préversion numérique ne dépassant pas `65535`. Aucun tag n’est créé automatiquement par CI.

## 3. Artefacts minimaux et noms canoniques

Chaque build est **natif** au système ciblé. Les archives CLI sont indépendantes des bundles Tauri, afin que les agents et les utilisateurs de terminal n’aient ni WebView ni runtime Python à installer. Les quatre artefacts primaires sont obligatoires ; Debian/MSI sont des variantes complémentaires de l’application desktop.

| Surface | Windows x64 | Linux x64 | Contenu/usage |
|---|---|---|---|
| CLI primaire | `vera-mmu-cli_<version>_windows_x64.zip` | `vera-mmu-cli_<version>_linux_x64.tar.gz` | `vmmu.exe` ou `vmmu` autonome, pour opérations VERA contrôlées |
| Desktop primaire | `VERA-MMU_<version>_x64-setup.exe` | `VERA-MMU_<version>_amd64.AppImage` | Tauri + sidecar `vmmu-desktop-bridge` embarqué |
| Desktop complémentaire | `VERA-MMU_<version>_x64_en-US.msi` | `VERA-MMU_<version>_amd64.deb` | Variante d’installation native, même Core et même tag |
| Intégrité | `SHA256SUMS` et `release-manifest.json` | `SHA256SUMS` et `release-manifest.json` | Version, SHA source, triple cible, hash et liste de fichiers |

Les binaires de CLI et le sidecar Tauri ne deviennent jamais des serveurs HTTP, ne reçoivent pas de shell ou de chemin à travers un client, et n’exécutent pas d’installation sans confirmation explicite. La release contient des binaires ; elle n’exécute aucun onboarding automatique, bootstrap réseau, réglage user-scope ou trust hôte.

## 4. Chaîne de build et contrôles

Le workflow de vérification M9 exécute la suite VERA complète **avant** de construire les artefacts. Il produit les archives et leurs manifests comme artefacts CI temporaires, sans appeler d’API de release et sans publication GitHub Pages.

Le workflow `release-candidate.yml` ne se déclenche que pour un tag `v*` ou manuellement sur une référence donnée. Il assemble, pour chaque runner natif, le ZIP/TAR.GZ CLI, les deux bundles desktop, leurs hashes et un manifest `vera-release-candidate/v1`. Son token n’a que la permission GitHub `contents: read` et il ne contient aucune étape de création de release, de signature ou de téléversement public.

| Gate | Preuve obligatoire | Refus si absent ou divergent |
|---|---|---|
| `REL-01` — version | quatre manifestes alignés et tag validé lors d’une release | version/titre/tag divergents |
| `REL-02` — source | checkout du tag, branche `main` et SHA dans chaque manifest | HEAD ambigu, source non suivie ou dirty |
| `REL-03` — qualité | suite VERA complète verte sur Windows x64 et Linux x64 | test, sous-test ou build rouge |
| `REL-04` — intégrité | SHA-256 de chaque archive et manifest exact | fichier absent, hash absent ou manifest non canonique |
| `REL-05` — plateformes | CLI native plus AppImage/NSIS ; variantes Debian/MSI selon matrice | build croisé ou target non autorisé |
| `REL-06` — licence | licence formelle, droits et avis de tiers approuvés | `LICENSE-PENDING.md` encore ouvert |
| `REL-07` — signature | politique et clés disponibles, signature vérifiée sur les binaires ciblés | clé absente, certificat expiré ou signature non vérifiable |
| `REL-08` — notes | notes factuelles, limites de preuve et procédure de rollback | promesse d’hôte réel ou garantie non attestée |

La gate `REL-06` est satisfaite par `LICENSE`, `NOTICE`, `CONTRIBUTING.md` et `TRADEMARKS.md`, sous réserve que le propriétaire conserve la responsabilité de la titularité des contributions présentes et futures. La gate `REL-07` reste obligatoire avant toute diffusion stable ou élargie : les clés de signature ne seront ni demandées, ni créées, ni stockées dans le dépôt. Toute opération de signature exige un environnement de secrets adapté, une clé contrôlée par le propriétaire et une confirmation explicite juste avant usage.

### Exception autorisée : préversion gratuite non signée

Le propriétaire a autorisé une unique voie de préversion publique gratuite : `v0.1.0-rc.4` peut être distribuée **sans signature**, exclusivement comme GitHub Pre-release, après une matrice de candidats verte sur le tag exact. Cette exception ne vaut ni pour une release stable, ni pour un canal d’entreprise, ni pour une diffusion présentée comme prête à un large public.

Les notes et la release doivent porter, de façon visible, les mentions suivantes : « préversion expérimentale », « binaires non signés », « éditeur non vérifié par Windows », « SHA-256 et manifest fournis » et « hôtes agents réels non encore validés ». Le tag, les hashes et les manifests sont obligatoires ; les artefacts CI sont récupérés puis publiés comme fichiers attachés de la release. Toute version suivante doit réévaluer `REL-07` sans hériter silencieusement de cette exception.

## 5. Politique de signature

La première release publique doit documenter, par plateforme, l’identité vérifiable de l’éditeur et une procédure indépendante de vérification. Sous Windows, cela implique une signature Authenticode valide pour les exécutables/installateurs distribués. Sous Linux, la release doit fournir une signature détachée de `SHA256SUMS` associée à une clé publique stable et documentée. Les signatures de mises à jour Tauri ne sont pas activées par défaut par le simple fait de bundler l’application ; leur activation sera une décision distincte, avec les clés et le canal de mise à jour correspondants.

Avant cette décision, les sorties de CI restent des **candidats de vérification non signés**, jamais des téléchargements recommandés. Les hashes seuls détectent une altération lorsqu’ils proviennent d’un canal authentifié ; ils ne remplacent pas la signature de l’éditeur.

## 6. Viewer statique et GitHub Pages

**Décision M9 :** le dashboard WebDev M7-A reste une démonstration statique séparée, référencée par son checkpoint `f28ac0fa`, et n’est pas un composant publiable de VERA tant que ses sources ne sont pas importées explicitement dans un futur `apps/viewer/` versionné par VERA. Aucun code n’est copié silencieusement entre les projets.

La future publication GitHub Pages ne peut provenir que de cette source versionnée, avec un build reproductible par tag. Elle pourra importer/exporter localement des rapports sérialisés et proposer des liens de téléchargement vérifiés ; elle ne pourra jamais sélectionner un dossier, lancer la CLI/le bridge, configurer MCP, lire un disque, accéder au shell, manipuler des secrets ou écrire une configuration hôte. GitHub Pages n’est donc pas une voie d’installation.

## 7. Processus humain avant publication

La publication propre suit le séquencement ci-dessous. Le workflow de vérification peut construire des candidats ; aucune étape automatisée ne crée de release GitHub ou ne téléverse de binaire public.

1. Aligner les versions, documenter le changelog et sélectionner une licence formelle.
2. Réconcilier les droits de distribution et les dépendances, puis préparer les clés de signature hors dépôt.
3. Créer un commit de release propre, revalider Windows/Linux natifs et vérifier les archives/manifests/hashes.
4. Demander une confirmation explicite du propriétaire pour le tag, la signature et la publication GitHub Release.
5. Créer le tag annoté, construire depuis ce tag, signer avec les clés autorisées et faire vérifier les signatures.
6. Publier les notes, les hashes, les signatures et les artefacts ; conserver la procédure de rollback et les versions précédentes.

Le test d’installation sur machine utilisateur et la campagne Claude/Codex/Gemini/Antigravity restent après la complétion du produit et leur protocole de confirmation propre. Ils ne peuvent pas être remplacés par les tests de packaging ou de conformance M8.
