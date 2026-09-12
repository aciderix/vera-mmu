# Audit d’écart — Universal Dev-MMU

**Date :** 2026-09-13  
**Dépôt audité :** `aciderix/vera-mmu`  
**Commit audité :** `afc931f`  
**Référence principale :** `docs/UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md`  
**Méthode :** comparaison de la spécification, du handoff, de l’arborescence source, des commandes exposées, des tests présents et des validations réellement exécutées.

## Conclusion exécutive

Le dépôt contient un **Core VERA-MMU substantiel et fortement testé**, ainsi qu’un sous-système de migration physique désormais avancé. La migration Profile couvre les chemins same-filesystem et `COPY_VERIFY_SWITCH`, SQLite/WAL/SHM, les inventaires workspace, les validations hashées, les états de reprise et les retours fail-closed. La régression Python observée est de **633 tests passés et 49 sous-tests passés**.

Cependant, la **Definition of Done globale de la spécification n’est pas satisfaite**. Le document décrit un produit plus large : un Universal Dev-MMU multi-domaines, un compilateur MCP déterministe, un Dashboard configurateur complet, une CLI universelle, des fixtures de conformance multi-domaines, un packaging natif vérifié et une validation Tauri/Rust. Ces éléments sont absents, partiels ou non démontrés.

Le statut correct est donc : **Core livré par sous-lots ; produit Universal Dev-MMU global non livré ; front Tauri non certifié en exécution native**.

## Légende de statut

| Statut | Signification |
|---|---|
| **Livré** | Implémentation présente et preuve de test suffisante dans le périmètre audité. |
| **Partiel** | Une partie existe, mais le contrat de la spécification n’est pas entièrement couvert. |
| **Non livré** | Aucun chemin correspondant au contrat complet n’a été identifié. |
| **Non démontré** | Le code ou la documentation suggère une capacité, mais la preuve requise n’a pas été exécutée ou n’est pas suffisante. |

## Matrice synthétique

| Domaine de la spécification | État | Écart principal |
|---|---|---|
| Core mémoire, preuves, provenance, gates et capacités | **Partiel à livré** | Nombreuses primitives présentes, mais la cible universelle complète et ses invariants de conformance ne sont pas tous démontrés. |
| Séparation Core / Domain Pack | **Partiel** | Un Domain Pack ARET existe, mais les cinq domaines de conformance demandés ne sont pas livrés. |
| Project Profile universel | **Partiel** | Profile project-bound présent, mais le contrat cible de la spécification et l’IDE de configuration ne sont pas complets. |
| MCP Core API | **Partiel** | Plusieurs surfaces sont présentes, mais l’ensemble exact de l’API cible et sa sélection/génération par profil ne sont pas prouvés. |
| MCP Compiler déterministe | **Non livré au niveau spécifié** | Pas de pipeline complet `load → normalize → validate → canonicalize → generate → static validation → package` démontré. |
| CLI universelle `mmu` | **Non livré au niveau spécifié** | Le paquet expose `vmmu`, pas le contrat complet `mmu init/scan/configure/validate/generate/install/serve/doctor/migrate/export/import/dashboard/upgrade`. |
| Dashboard configurateur | **Partiel** | Dashboard sécurisé pour plusieurs surfaces livrées, mais pas l’IDE complet décrit par la spécification. |
| Tauri natif | **Non démontré** | TypeScript/Vite passent ; Cargo et lancement/package natifs n’ont pas été validés. |
| Migration physique Profile | **Livré dans le périmètre couvert** | Sous-système avancé et testé, mais cela ne clôt pas l’universalisation globale. |
| Conformance multi-domaines | **Non livré** | Les fixtures et le parcours complet par domaine ne sont pas présents comme matrice exécutée. |
| Release et packaging | **Partiel / non démontré** | Scripts et workflow existent, mais build natif, artefacts signés, hashes publiés et release propre ne sont pas prouvés. |

## Écarts détaillés

### 1. Universalité multi-domaines

La spécification demande au moins cinq domaines validés, notamment software, game, research, data/ML, hardware et documentation. Le dépôt contient un domaine ARET sous `domains/aret`, mais aucune matrice équivalente de Domain Packs génériques n’a été démontrée pour ces domaines.

Il manque notamment :

- Domain Packs `software`, `game`, `research`, `data`, `hardware` et `documentation` au niveau attendu ;
- profils d’exemple pour ces domaines ;
- génération de capabilities et gates propres à chaque domaine ;
- tests de conformance complets par domaine ;
- preuve qu’un projet non-ARET ne dépend pas d’hypothèses ARET résiduelles.

**Statut : non livré au niveau de la spécification.**

### 2. Project Profile et configuration universelle

Le dépôt possède un Profile YAML project-bound et des validateurs, mais la spécification cible un Profile universel avec taxonomie, entités, relations, work graph, capabilities, gates, policies, playbook, Front, resume et intégrations configurables dans un parcours cohérent.

La structure effectivement utilisée reste centrée sur le contrat VERA existant, notamment `.vera-mmu/project.yaml`, alors que la spécification décrit `.mmu/project.yaml` comme fichier canonique cible. Une décision de compatibilité ou de migration générale entre ces conventions n’est pas livrée.

Il manque ou reste à démontrer :

- éditeur complet et déterministe de toutes les sections du Profile ;
- import, normalisation et génération d’un Profile depuis un projet inconnu ;
- validation des relations entre tous les catalogues ;
- génération reproductible des fichiers d’intégration ;
- migration générale vers le contrat universel décrit.

**Statut : partiel.**

### 3. Dashboard configurateur complet

Le Dashboard actuel expose des surfaces sécurisées, des previews, certaines constructions de capabilities/gates, la documentation, le Doctor et le statut de migration. Il ne constitue pas encore l’IDE de configuration et de génération complet demandé par la spécification.

Le parcours spécifié comporte dix-huit étapes, du scan jusqu’à l’installation et au Doctor. Les éléments suivants ne sont pas livrés comme parcours complet démontré :

- scanner de projet général détectant VCS, langages, frameworks, dépendances, build, tests, linters, CI, Docker, documentation, datasets, assets et sous-projets ;
- recommandation automatique de Profile ;
- édition visuelle de la taxonomie ;
- registre visuel des entités et relations ;
- configuration complète du Work Graph ;
- éditeur complet de policies ;
- configuration visuelle du Resume et des intégrations ;
- MCP Preview avec métriques, hashes et alertes complètes ;
- génération et installation universelles depuis le Dashboard ;
- import général d’un projet existant avec provenance pour README, ADR, TODO, changelog, issues, CI, tests, configuration et historique Git.

Le handoff décrit explicitement le Dashboard comme un assistant sécurisé pour les surfaces livrées, et non comme l’IDE configurateur complet.

**Statut : partiel.**

### 4. Front Tauri natif

Les validations exécutées ont confirmé :

- compilation TypeScript ;
- build Vite ;
- présence du bridge React/Tauri ;
- séparation déclarée entre WebView, bridge et sidecar Python.

Elles n’ont pas confirmé :

- compilation Rust avec Cargo ;
- exécution `tauri dev` ;
- packaging natif Linux ou Windows ;
- lancement de l’artefact paqueté ;
- communication réelle Rust ↔ WebView ↔ sidecar ;
- tests UI/bridge/Tauri automatisés sur l’application native.

`cargo` était indisponible dans l’environnement audité. Le statut correct est donc **Dashboard web compilable, Tauri natif non certifié**.

### 5. MCP Compiler

La spécification exige un compilateur qui charge le Profile et les packs, normalise, valide, canonicalise, calcule les hashes, résout capabilities/gates/policies/intégrations, génère schemas, instructions, hooks, configuration, documentation, exécute une validation statique et produit un package MCP reproductible.

Le dépôt possède plusieurs générateurs et adapters, mais l’audit ne démontre pas un compilateur universel unique satisfaisant l’ensemble de ce contrat. Les points restant à livrer ou à prouver sont :

- pipeline complet et explicitement ordonné ;
- hash `profile`, `policy`, catalogues capability/gate et build MCP ;
- reproductibilité bit-à-bit ou contrat de canonicalisation équivalent ;
- résolution multi-Domain Packs ;
- génération complète des hooks et intégrations ;
- validation statique bloquante avant production du package ;
- package MCP complet testable sur une machine propre.

**Statut : partiel à non démontré.**

### 6. CLI universelle

Le paquet Python expose une commande `vmmu` et plusieurs sous-commandes spécialisées. La spécification décrit une CLI `mmu` avec le contrat suivant :

```text
mmu init
mmu scan
mmu configure
mmu validate
mmu generate
mmu install
mmu serve
mmu doctor
mmu migrate
mmu export
mmu import
mmu dashboard
mmu upgrade
```

La correspondance exacte de toutes ces commandes, leur comportement universel et leur conformance à la spécification ne sont pas livrés. Les opérations existantes sont davantage orientées vers les primitives VERA et les adapters que vers le parcours universel complet.

**Statut : non livré au niveau spécifié.**

### 7. Conformance multi-domaines et projets variés

La spécification demande des fixtures `empty`, `software`, `web`, `game`, `research`, `data`, `document`, `hardware`, `multi-repo`, `no-git` et `existing-project`. Chaque fixture doit exécuter init, scan, configure, validate, generate, boot, find, read, write, proof, promotion, handoff, compact, resume, bundle, restore et doctor.

Le dépôt possède une suite importante de tests unitaires et d’intégration, mais aucune preuve d’exécution de cette matrice complète n’a été trouvée. Les cas suivants restent donc non démontrés :

- projet vide ;
- projet sans Git ;
- projet multi-repo ;
- import d’un projet existant ;
- validation indépendante de cinq domaines ou plus ;
- parcours de génération complet pour chaque fixture.

**Statut : non livré.**

### 8. `mmu doctor` complet

Le Doctor existant fournit des diagnostics et des surfaces project-bound. La spécification exige un rapport machine et humain couvrant au minimum identité, Profile, schéma, intégrité SQLite, WAL, artifacts, HMAC, capabilities, gates, policies, adapter, MCP, hooks, Resume et VCS, avec indication de la réparation associée.

L’existence de modules Doctor ne suffit pas à prouver que cette matrice complète est retournée et réparée comme spécifié sur une machine propre. La couverture exacte du rapport, les réparations guidées et le chemin d’installation complet restent à auditer et à compléter.

**Statut : partiel / non démontré.**

### 9. Sécurité et invariants de la spécification

Le dépôt contient de nombreux tests de sécurité et de gouvernance, notamment pour le confinement, les policies, les preuves, les bundles, l’identité et les migrations. La liste de la spécification est toutefois plus large et doit être prouvée comme matrice de conformance unique.

Restent à consolider dans un lot de conformance dédié :

- injection shell et commande arbitraire dans tous les runners ;
- injection de paramètres ;
- réseau non autorisé ;
- artefact et hash falsifiés dans chaque parcours ;
- HMAC invalide dans chaque transport ;
- promotion `PROVEN` avec preuves `SKIPPED` ;
- mauvais Profile Hash et Resume Hash dans le parcours complet ;
- import inter-projets sur toutes les surfaces ;
- absence de rupture silencieuse sur les adapters et le Dashboard natif.

**Statut : partiel.**

### 10. ARET Domain Pack et compatibilité de référence

Le dépôt contient des tests ARET et un domaine ARET séparé. La spécification exige que les pipelines ARET, gates, preuves, Resume Guard, playbook, roadmap, bundles et hooks soient équivalents ou meilleurs après migration.

La présence de tests ne constitue pas à elle seule la preuve d’équivalence de la matrice historique complète. Il manque un rapport de compatibilité explicitement comparatif entre la référence ARET et le Domain Pack livré.

**Statut : partiel / non démontré.**

### 11. Packaging, installation et release

Les scripts de build sidecar, le manifeste Cargo, la configuration Tauri et un workflow de packaging existent. La preuve de release complète n’est cependant pas établie.

Restent à faire ou à prouver :

- build natif Linux avec Cargo ;
- build Windows natif ;
- tests des bundles AppImage, Debian, NSIS et MSI ;
- installation sur machine propre ;
- vérification du lancement après installation ;
- release signée ;
- hashes publiés ;
- notes de release ;
- test de réparation automatique d’installation.

**Statut : partiel / non démontré.**

### 12. Documentation de clôture et cohérence du handoff

La spécification est maintenant versionnée dans le dépôt et référencée par le handoff. Le handoff conserve néanmoins des paragraphes historiques qui déclarent encore certaines fonctions ouvertes, suivis d’annotations ultérieures indiquant leur livraison. Une réécriture de consolidation est recommandée pour éviter les contradictions de lecture.

Le dépôt distant contient le commit d’intégration documentaire `afc931f`, mais l’audit doit continuer à distinguer :

- les commits publiés ;
- les tests exécutés ;
- les capacités seulement présentes dans le code ;
- les validations natives non exécutées.

**Statut : documentation intégrée, consolidation éditoriale encore recommandée.**

## Ce qui est effectivement livré avec preuve forte

Les éléments suivants sont les plus solidement établis par le code et la régression exécutée :

1. Core VERA-MMU project-bound avec mémoire, provenance, preuves, gates, capabilities, work items et adapters dans le périmètre des tests existants.
2. Tests Python complets : `633 passed, 49 subtests passed`.
3. Migration Profile same-filesystem avec journal, backup, checkpoint SQLite et rollback.
4. Migration `COPY_VERIFY_SWITCH` sélectionnée par le preview lorsque les devices diffèrent, avec copie runtime et workspace par fichier.
5. Validation SQLite, schéma, WAL/SHM, hash, taille et symlink.
6. Reprise prouvée `EXECUTING`/`SWITCHING`, avec `ROLLED_BACK` ou `RECOVERY_REQUIRED` selon la preuve disponible.
7. Build TypeScript/Vite du Dashboard.
8. Scan de frontière Core sans occurrences ARET interdites détectées dans `src/vera_mmu`.
9. Spécification finale intégrée dans `docs/` et publiée sur `origin/main` au commit `afc931f`.

## Priorités de livraison restantes

| Priorité | Lot restant | Critère de sortie |
|---|---|---|
| P0 | Certifier Tauri/Rust | `cargo test`, `tauri build`, lancement natif et test du bridge sur machine cible. |
| P0 | Conformance multi-domaines | Fixtures au moins software, game, research, data, hardware/documentation, plus no-git/multi-repo/empty/existing. |
| P0 | CLI et compiler universels | Parcours `mmu init → scan → configure → validate → generate → install → doctor` reproductible. |
| P1 | Dashboard configurateur complet | Scanner, recommandation, Profile, taxonomie, entités, relations, work graph, policies, Resume, MCP preview, generate/install. |
| P1 | Doctor et release | Rapport complet, réparations guidées, packaging natif, installation propre, hashes et release. |
| P1 | Compatibilité ARET | Rapport comparatif des invariants et pipelines historiques contre le Domain Pack. |
| P2 | Nettoyage documentaire | Réconcilier les paragraphes historiques du handoff et publier une version consolidée du statut global. |

## Verdict

**Le dépôt n’est pas conforme à la totalité de la spécification finale.** Il est conforme à plusieurs sous-lots Core importants, dont la migration physique et la reprise fail-closed. Le Dashboard React/Vite est compilable et propose des surfaces fonctionnelles, mais le front Tauri natif n’est pas certifié et le Dashboard configurateur complet n’est pas livré. Le produit Universal Dev-MMU complet, multi-domaines, compilateur MCP, CLI universelle et release native restent à construire ou à démontrer.

## Références

[1]: ../UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md "Spécification finale Universal Dev-MMU versionnée dans le dépôt"
[2]: ./HANDOFF_NEXT_AGENT.md "Handoff de continuité VERA-MMU"
[3]: ../../README.md "README du dépôt VERA-MMU"
[4]: ../../apps/desktop/README.md "README du Dashboard Desktop/Tauri"
[5]: ../../apps/desktop/package.json "Manifest du Dashboard React/Tauri"
[6]: ../../pyproject.toml "Manifest Python et commandes VERA-MMU"
