# Registre de découplage ARET-MMU → VERA-MMU

> **Statut :** registre M0.2, complété par l’avancement M1 pour C01/C02/C11 — couplages cartographiés ; **aucun code ARET n’a été déplacé**.
>
> **Baseline :** ARET-MMU `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, capturé dans `/home/ubuntu/ARET_MMU_M0_1_BASELINE/`.
> **Wall active :** `MEM-WALL-001` interdit toute affirmation de parité pour les oracles qui requièrent la toolchain ARET absente.

## 1. Règles du registre

Une ligne `SPLIT` signifie que le couplage est analysé, sa frontière Core/pack est définie et sa preuve de parité est nommée ; **elle ne signifie pas qu’il est implémenté**. Une ligne ne devient `DONE` que lorsque l’abstraction cible existe, que le test de parité est exécuté, que les invariants sont préservés et que le Core démontre son absence de dépendance ARET. Une ligne `BLOCKED` reste visible et ne peut pas être transformée en `DONE`, `PASS` ou équivalent par interprétation.

| Statut | Signification opérationnelle |
|---|---|
| `SPLIT` | Découpage et chemin de migration établis ; aucune extraction de code déclarée. |
| `BLOCKED` | Une précondition ou une evidence manque ; l’extraction peut être préparée mais la parité ne peut être conclue. |
| `TODO` | Couplage connu mais analyse de découplage insuffisante. |
| `DONE` | Abstraction, tests, evidence et non-dépendance ARET du Core sont démontrées. |

## 2. Registre de compatibilité détaillé

| ID | Surface et couplage ARET | Sources de référence | Abstraction VERA/MMU cible | Stratégie de migration sans big bang | Parité et evidence à exiger | Invariants | État |
|---|---|---|---|---|---|---|---|
| `C01` | `ARET://` accepte seulement les ressources ARET fermées (`knowledge`, `component`, `function`, `brick`, `proof`, `relation`, `asset`, `pipeline`) et `front/current`. | `core/addressing.py:8–60`; baseline `inventory/mcp_server_static_surface.txt`. | `vera://<project>/<resource>/<id>` avec registre de types ; lecteur d’adresses `ARET://` V1 uniquement en compatibilité de lecture. | Introduire un parseur strict générique en M1 ; encapsuler le parseur ARET actuel dans `domains/aret/compat/addressing.py`; ne pas modifier les adresses existantes. | Fixtures de round-trip VERA et ARET, encodage d’identifiants, rejet de schéma/type/injection non canoniques ; `tests/test_relation_addressing_and_wal.py` comme référence de comportement. | I002, I011, I014, I015 | `SPLIT` |
| `C02` | Le store se résout depuis `ARET_MEMORY_DIR` ou `.aret-memory`, crée `aret_memory.sqlite`, `artifacts/`, `exports/` et active WAL. | `core/repository.py:122–180`; `ops/git_memory.py:30–64`; `integration/INSTALL.md:7–10`. | `ProjectProfile.runtime_dir`, `WorkspaceResolver` et `StoreLocator` ; runtime `.vera-mmu/` configurable par profil. | Créer le resolver VERA sans supprimer le constructeur ARET ; faire adapter le pack ARET vers ses chemins existants ; introduire les aliases en lecture lors de M4. | Initialisation VERA, override borné, no-Git, multi-repo, traversal, WAL checkpoint et doctor ; références `tests/test_repository.py`, `tests/test_relation_addressing_and_wal.py`. | I001, I005, I010, I011, I014, I015 | `SPLIT` |
| `C03` | `component` est une table et un type métier de reverse engineering ; `knowledge.component_id` le référence directement. | `schema/001_initial.sql:20–26,49–70`; `core/repository.py` opérations `register_component`; `tests/test_repository.py`. | `entity_type` déclaratif + `entity`, avec le type `COMPONENT` fourni par le pack ARET. | Ajouter les tables universelles dans une migration VERA nouvelle ; importer les composants ARET comme entités sans réécrire la base V1. | Import de composant, unicité, liens de connaissance, intégrité référentielle, export/import bundle et absence de `component` dans le Core. | I001, I003, I011, I014, I015 | `SPLIT` |
| `C04` | `function_symbol` impose un parent `component` et une unicité `(component,module,symbol)` ; ses adresses sont `ARET://function`. | `schema/001_initial.sql:28–37`; `core/repository.py` opérations `register_function`; baseline `hashes/schema_sha256.txt`. | `symbol` technique optionnellement lié à une entité ; type et contraintes déclarés par profil/pack. | Ajouter `symbol` universel ; créer un importeur V1 `function_symbol → symbol` en conservant les IDs source dans la provenance. | Import exact, unicité configurable, relations vers entité, lecteur V1, rollback de migration de données. | I001, I003, I011, I014, I015 | `SPLIT` |
| `C05` | `brick` encode la roadmap ARET, son état et un lien composant ; la migration 005 ajoute milestone, plateforme et priorité. | `schema/001_initial.sql:39–47`; `schema/005_roadmap_bricks.sql:1–10`; `core/repository.py` opérations `register_brick`/`update_brick`; `tests/test_roadmap.py`. | `work_item` typé, hiérarchique et relié au Work Graph ; `ROADMAP_BRICK` devient un type de pack ARET. | Introduire `work_item` et son état universel ; importer les briques avec leur métadonnée sous namespace ARET ; conserver le Front V1 lisible. | Cycle de vie, Front actif, ordre roadmap, liens, ajout de dépendance/cycle et import V1. | I001, I003, I009, I011, I014, I015 | `SPLIT` |
| `C06` | `PIPELINES` est un dictionnaire Python fermé de noms, runners, policies, dépendances et timeouts ; les vocabulaires reflètent les besoins ARET. | `evidence/adapters/pipelines.py:26–183`; `schema/006_pipeline_assets.sql:19–40`; `tests/test_pipeline_adapters.py`. | `CapabilityCatalog` déclaratif versionné, avec schéma de paramètres, policy, runner et validator ; les capacités ARET deviennent un pack. | Construire le moteur de catalogue fermé avant d’importer une première capability ARET read-only ; garder `PIPELINES` comme adaptateur de compatibilité jusqu’à parité. | Rejet capability inconnue, paramètres hors schéma, timeout, policy, artifact hash, dry-run et snapshot de catalogue. | I004–I008, I012–I015 | `SPLIT` |
| `C07` | `ORACLES` sélectionne scripts/commandes fermés, dépendances et normalise `PASS/FAIL/ERROR/SKIPPED/UNKNOWN` en preuves. | `evidence/adapters/oracles.py:32–245`; `tests/test_execution_confinement.py`; baseline `tests/pytest_full.txt`. | `Validator` et `CapabilityRunner` séparés ; evidence/execution génériques reliées à une Gate. | Extraire d’abord interfaces, normalisation et artefact ; encapsuler les specs ARET dans `domains/aret/oracles.py`; conserver l’HMAC et l’admissibilité. | Confinement de repository/script, absence de commande arbitraire, evidence hashée, distinction `SKIPPED`/`PASS`, promotion `PROVEN` et gate réelle. | I004–I008, I013–I015 | `BLOCKED` — `MEM-WALL-001` |
| `C08` | Le binaire `target/release/aret`, `bench/*`, Wine, MinGW, GCC, Cargo, Clang et corpus sont des préconditions ARET. | `evidence/adapters/oracles.py:44–53`; `evidence/adapters/pipelines.py:47–183`; baseline `toolchain/oracle_toolchain_availability.txt`. | `DomainPack.dependencies` + `CapabilityPreflight` ; le Core ne connaît aucun exécutable, corpus ou toolchain ARET. | Déclarer les dépendances par capability dans le pack ; faire produire à `doctor` un verdict et une recette, jamais une installation implicite. | Core installable sans toolchain ; doctor précise les manques ; exécutabilité mesurée dans une image de référence ; tests `SKIPPED` explicites. | I006–I008, I013–I015 | `BLOCKED` — `MEM-WALL-001` |
| `C09` | `SERVER_INSTRUCTIONS` contient doctrine ARET, règles MCP, Front, handoff et industrialisation sous forme de texte Python statique. | `aret_mmu_server.py:19–34`; `config/playbook.md:2–85`. | Doctrine Core courte + instructions dérivées du profile, packs, policy et état de reprise, avec hash de build. | Isoler les instructions VERA stables ; compiler les instructions de projet ; conserver le texte ARET dans son pack et comparer en snapshot. | Même entrée de profile/packs = même instruction/hash ; aucune instruction ARET dans une instance Core sans pack ; snapshots ARET. | I001, I004, I009, I012, I014, I015 | `SPLIT` |
| `C10` | Les 44 outils `aret_*` sont écrits manuellement dans le serveur MCP ; la surface mélange Core, compatibilité et capacités ARET. | `aret_mmu_server.py:62+`; baseline `inventory/mcp_server_static_surface.txt`. | API Core minimale `vera_*` + Tool Registry compilé pour les outils de projet ; aliases `aret_*` temporaires dans le pack ARET. | Définir d’abord les contrats Core read/write/confirm ; générer un manifeste ; ajouter les aliases à la fin de la compatibilité, sans supprimer la façade V1. | Schémas de chaque outil, surface minimale, classification read/write/sensitive/network, snapshots et appels de compatibilité. | I002, I004, I007, I008, I012–I015 | `SPLIT` |
| `C11` | Le serveur dérive une racine unique du store et refuse toute autre `repository_path`; l’intégration suppose un paquet vendored. | `aret_mmu_server.py:37–49`; `integration/INSTALL.md:7–40,115–125`. | `Workspace` multi-racines + `ProjectIdentity` ; le pack ARET fournit un resolver mono-racine de compatibilité. | Construire le resolver générique avant la migration d’intégration ; garder le rejet V1 dans l’adaptateur ARET, pas dans le Core. | No-Git, mono-repo, multi-repo, symlink/traversal, identité mismatched, installation non polluante. | I008, I011, I014, I015 | `SPLIT` |
| `C12` | Le playbook Markdown ARET est une source autorée hors SQLite, injectée dans la reprise, avec cinq domaines obligatoires et une borne de taille. | `config/playbook.md:2–16`; `core/repository.py:42–55`; `tests/test_operational_extensions.py`. | `ProjectPlaybook` versionné et hashé, issu d’un profile ou d’un Domain Pack ; doctrine Core distincte. | Conserver le playbook ARET tel quel comme contenu de pack ; fournir un parseur/validateur générique qui ne l’ingère pas silencieusement en mémoire. | Cinq sections ARET, taille, hash, injection de reprise, changement du playbook sans mutation de l’état canonique. | I001, I009, I012, I014, I015 | `SPLIT` |
| `C13` | Git sync exige `aret-memory/.aret-memory`, checkpoint WAL, scope strict et policy JSON ; le sync de fin de tour a une sémantique plus permissive. | `ops/git_memory.py:30–229`; `tests/test_operational_extensions.py:118–136`. | `VersionControlProvider` + policy explicite `CONFIRM`/`ALLOW`/`DENY`; runtime dir fourni par le profile. | Extraire les opérations Git abstraites ; reproduire checkpoint/scope ; interdire au Core de pousser sans policy et confirmation. | NoVCS, Git, changements hors scope, WAL occupé, HEAD détachée, refus de push et policy invalide. | I005, I010, I013–I015 | `SPLIT` |
| `C14` | Bundle V1 capture mémoire, artefacts et métadonnées d’import, avec non-fusion, idempotence et détection d’altération. | `core/repository.py:2326–2510`; `schema/003_bundle_imports.sql`; `tests/test_operational_extensions.py:138–170`; baseline `bundle/bundle_result.json`. | Bundle V2 : identité projet, profile/packs/hashes, mémoire, migrations, artefacts et policy d’import. | Ajouter un format V2 distinct ; conserver l’import V1 en lecture/convertisseur explicite ; ne jamais fusionner une mémoire non vide. | Manifest/hash chain, altération, import idempotent, incompatibilité d’identité, non-fusion et restauration du bundle M0.1. | I005, I010, I011, I014 | `SPLIT` |
| `C15` | Hooks SessionStart/PostCompact/PreToolUse/Stop et Resume Guard stockent un état éphémère sous `.aret-memory/runtime/`, lié à un hash de contrat et à six champs rituels. | `hooks/resume_guard.py:25–274`; `hooks/common.py`; `integration/INSTALL.md:13–40`; `tests/test_resume_guard*.py`, `tests/test_resume_observations_v13.py`. | `RuntimeAdapter` généré + `ResumeContract` hashé ; état de session séparé de la mémoire canonique ; kill-switch policy-gated. | Modéliser la machine d’état avant de générer les hooks ; conserver les wrappers ARET comme adapter de compatibilité jusqu’aux tests de reprise VERA. | Fresh session, PostCompact, mode dégradé, acknowledgement expiré, identité absente, kill-switch et Stop one-shot. | I001, I009, I011–I014 | `SPLIT` |
| `C16` | Knowledge, proof, relation, audit et règles `PROVEN`/append-only sont implémentés avec tables, triggers et méthodes ARET. | `schema/001_initial.sql:49–200`; `core/repository.py:1477–1800`; `tests/test_repository.py`, `tests/test_relation_*.py`. | Evidence Store, audit append-only, relation registry et knowledge registry universels ; taxonomies ARET déplacées dans le pack/profil. | Extraire les invariants et migrations avant les vocabulaires ; importer les types/relations ARET dans des registries déclaratifs sans affaiblir les triggers. | Promotion sans preuve, HMAC, hash d’artefact, rewrite append-only, relation lifecycle/supersession, audit et import croisé refusé. | I001–I006, I010, I011, I014, I015 | `SPLIT` |

### 2.1. Avancement observé M1 — sous-ensembles C01/C02/C11

| Couplage | Surface VERA désormais observée | Evidence M1 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C01` | Construction et parsing stricts de `vera://<project>/<resource>/<id>` ; ressources Core génériques fermées ; rejet des URI non canoniques. | `tests/test_addressing.py` ; 21 tests et 14 sous-tests au total ; scan Core anti-ARET ; `LOG-0009`. | Lecteur `ARET://`, fixtures de round-trip historique et parité avec les adresses V1. | `SPLIT` |
| `C02` | Profile normalisé/hashé, roots contrôlées et `RuntimeLocator` confinant runtime, SQLite et artefacts sous `.vera-mmu/` configurable. | `tests/test_runtime.py`, `tests/test_workspace.py` ; wheel installé et `vmmu inspect` validé ; `LOG-0009`. | Création du store, WAL, checkpoint, doctor, override de store et comportement de stockage ARET. | `SPLIT` |
| `C11` | Workspace mono/multi/no-Git, détection de marqueur VCS sans exécuter Git, fingerprint topologique et rejet traversal/symlink. | `tests/test_workspace.py` ; 21 tests et 14 sous-tests ; `LOG-0009`. | Adaptateur d’intégration mono-racine ARET, identité mismatched contre store et installation MCP non polluante. | `SPLIT` |

> Ces preuves autorisent le verdict technique M1 mais ne satisfont pas les preuves de parité complètes exigées par les lignes mères. Aucun `SPLIT` ne devient `DONE` au titre de ce lot.

### 2.2. Avancement observé M2.1 — substrate SQLite

| Couplage | Surface VERA désormais observée | Evidence M2.1 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C02` | `MemoryStore` ouvre uniquement le runtime validé par M1, active foreign keys/WAL/timeout et lie le store à `ProjectIdentity`. | `tests/test_store.py`, `tests/test_cli.py` ; wheel installé et `vmmu init` validé ; `LOG-0011`. | Override de store, exports, doctor, checkpoint/WAL policy complète, intégration ARET et comportement V1. | `SPLIT` |
| `C14` | Ledger de migrations ordonnées, continues et checksumées ; métadonnée de format et audit technique de migration. | Initialisation, idempotence, checksum altéré, trou de version et rollback SQL testés ; `LOG-0011`. | Format de bundle, chaîne d’intégrité, import/export, non-fusion, restauration et parité bundle M0.1. | `SPLIT` |
| `C16` | Métadonnées canoniques du store, audit technique et transaction atomique existent sans taxonomie métier. | Tests de rollback, identité croisée et SQL invalide atomique ; `LOG-0011`. | Knowledge append-only, relations, preuves, admission `PROVEN`, audit métier et import croisé de mémoire. | `SPLIT` |

> M2.1 établit un substrate mais ne met en œuvre aucun objet de persistance métier. Les lignes C02, C14 et C16 restent donc `SPLIT` et la parité ARET reste `UNKNOWN`.

### 2.3. Avancement observé M2.2 — registre d’entités

| Couplage | Surface VERA désormais observée | Evidence M2.2 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C03` | Migration `002`, `entity_type` et `entity` génériques ; `EntityService` exige un type enregistré, produit une adresse `vera://` exacte et ne dépend d’aucun concept `component`/`function`. | `tests/test_entities.py` : migration 1→2, type/ID inconnus ou dupliqués, lecture exacte ; wheel installé et vérifié ; `LOG-0013`. | Symboles, `function_symbol`→`symbol`, migration de données V1, composants historiques, relations et parité fonctionnelle ARET. | `SPLIT` |
| `C16` | Création de type et d’entité accompagnée d’un audit dans la même transaction ; rollback testé si l’audit est refusé. | Tests audit/rollback et contrôles de duplication ; `LOG-0013`. | Knowledge append-only, audit des autres mutations métier, relation/proof, import de mémoire et règles de non-réécriture. | `SPLIT` |

> M2.2 apporte un premier objet métier universel mais ne crée ni chemin de migration ARET ni modèle relationnel complet. Les lignes C03 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

### 2.4. Avancement observé M2.3 — registre relationnel entre entités

| Couplage | Surface VERA désormais observée | Evidence M2.3 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C16` | Migration `003`, `relation_type` déclaratif et `relation` immuable entre entités ; contraintes de type source/cible, unicité d’arête, lecture exacte et audit atomique. | `tests/test_relations.py` : migration 2→3, contraintes endpoint, duplication, audit/rollback, rewrite/delete SQL refusés ; wheel vérifié ; `LOG-0015`. | Traversal/FIND, lifecycle/supersession, relations vers knowledge/evidence/symbol, relation types de pack, audit de toute mutation métier, preuves et import croisé. | `SPLIT` |
| `C03` | Les relations s’appuient uniquement sur `entity_type`/`entity` M2.2, sans réintroduire `component` ni dépendance technique. | Tests de contraintes `report`→`dataset` et rejection d’entité/type inconnus ; `LOG-0015`. | Import de composants V1, symboles, liens de connaissance et parité fonctionnelle ARET. | `SPLIT` |

> M2.3 établit des arêtes génériques mais n’implémente ni graphe de traversal ni lifecycle historique. Les lignes C03 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

### 2.5. Avancement observé M2.4 — knowledge append-only

| Couplage | Surface VERA désormais observée | Evidence M2.4 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C16` | Migration `004`, `knowledge_type` déclaratif et `knowledge` append-only avec hash SHA-256, JSON canonique, statuts initiaux sûrs, lecture exacte et audit atomique. | `tests/test_knowledge.py` : migration 3→4, hash, statuts, `PROVEN` refusé par API et SQL, rewrite/delete refusés, audit/rollback ; wheel vérifié ; `LOG-0017`. | Evidence/proof/artifact, admission de `PROVEN`, FTS/FIND, tags, sources, supersession, relations vers knowledge, audit de toute mutation métier, import croisé. | `SPLIT` |
| `C03` | Les connaissances restent génériques et ne portent aucun lien `component` ou `function`; leur type est enregistré dans le Core. | Tests de type inconnu/dupliqué et d’adresse VERA exacte ; `LOG-0017`. | Import des composants V1, liens de connaissance, symboles, migration de données et parité fonctionnelle ARET. | `SPLIT` |

> M2.4 établit une connaissance append-only vérifiable par hash mais ne fournit ni preuve admissible, ni recherche, ni lifecycle. Les lignes C03 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

### 2.6. Avancement observé M2.5 — provenance documentaire déclarative

| Couplage | Surface VERA désormais observée | Evidence M2.5 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C16` | Migration `005`, `knowledge_source` immutable attachée à une knowledge existante : repository, revision, chemin relatif, section, lignes et SHA-256 ; lecture exacte ou liste bornée et audit atomique. | `tests/test_provenance.py` : migration 4→5, confinement de chemins, lignes/hash, duplicat de slice, lecture bornée, rewrite/delete refusés, audit/rollback ; wheel vérifié ; `LOG-0019`. | Fetch/validation de document, importeur/migration batch, sources non documentaires, evidence/proof/artifact, admission de `PROVEN`, FTS/FIND, supersession, relations vers knowledge, audit de toute mutation métier. | `SPLIT` |
| `C03` | Les sources restent attachées à une knowledge générique et n’introduisent aucun lien `component`/`function`, symbole ni import technique. | Tests de knowledge inconnue et adresse VERA exacte ; `LOG-0019`. | Import des composants V1, liens de connaissance, symboles, migration de données et parité fonctionnelle ARET. | `SPLIT` |

> M2.5 établit une provenance déclarative sans ouvrir le document, sans importer son contenu et sans rendre une assertion `PROVEN`. Les lignes C03 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

## 3. Ordre d’extraction autorisé

L’ordre ne suit pas la taille des fichiers, mais les dépendances de sûreté. Les premiers changements d’implémentation autorisés dans VERA-MMU relèvent de **M1** et doivent rester indépendants de tout pack : identité de projet, profile, résolution de workspace, adressage strict `vera://` et répertoire de runtime configuré. Les tables universelles, evidence, catalogues, gates et adapters ne doivent suivre qu’après les tests correspondants.

| Ordre | Lot futur | Couplages préparés | Précondition non négociable |
|---|---|---|---|
| 1 | `M1` — identité/Core | C01, C02, C11 | Aucune référence ARET dans le namespace Core ; tests no-Git, multi-repo et traversal. |
| 2 | `M2` — persistence | C03, C04, C05, C14, C16 | Migrations checksumées, append-only et identité de projet. |
| 3 | `M3` — capabilities/gates | C06, C07, C08 | `MEM-WALL-001` reste ouverte ; aucune validation d’oracle réelle sans toolchain. |
| 4 | `M4` — pack ARET | C01, C04–C16 | Import explicite, lecteurs/aliases compatibles et parité mesurée contre M0.1. |
| 5 | `M5` — compilateur/adapters | C09, C10, C12, C15 | Snapshots déterministes, ResumeContract et manifest hashé. |

## 4. Discipline de mise à jour

Chaque lot qui touche une ligne doit ajouter les fichiers VERA modifiés, les invariants affectés, les tests nouveaux, les artefacts de comparaison au baseline M0.1, le verdict et le commit atomique. Une ligne ayant une source mais pas de test reste `SPLIT`; une ligne dont la précondition manque reste `BLOCKED`; aucune ligne ne peut devenir `DONE` par lecture de code ou par test unitaire isolé.

## Références

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — dépôt de référence"
[2]: continuity/PROJECT_MEMORY.md "Mémoire factuelle du chantier VERA-MMU"
[3]: continuity/ENGINEERING_LOG.md "Journal d’ingénierie VERA-MMU"

### 2.7. Avancement observé M2.6 — supersession knowledge déclarative

| Couplage | Surface VERA désormais observée | Evidence M2.6 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C16` | Migration `006` et sidecar `knowledge_supersession` immutable entre deux knowledge existantes ; unicité de prédécesseur/successeur, self-link et cycle refusés, lectures exactes dans les deux sens et audit atomique. | `tests/test_supersession.py` : migration 5→6, inconnus, self-link, duplicats, cycle, lecture exacte, rewrite/delete SQL refusés, audit/rollback ; wheel vérifié ; `LOG-0021`. | Mutation de statut ou `SUPERSEDED`, version counter, création automatique, traversal/listing de lignée, integration à `RelationService`, evidence/proof/artifact, admission `PROVEN`, FTS/FIND, import croisé et parité historique. | `SPLIT` |
| `C03` | La supersession porte uniquement les identifiants de knowledge génériques existantes ; elle n’introduit aucun `component`, `function`, symbole ou vocabulaire technique. | Validation d’identifiants VERA et de l’existence des deux knowledge ; scan ciblé du nouveau Core ; `LOG-0021`. | Import des composants V1, liens de connaissance spécialisés, symboles, migration de données et parité fonctionnelle ARET. | `SPLIT` |

> M2.6 rend un remplacement explicite traçable sans réécrire les assertions knowledge et sans reproduire le lifecycle historique. Les lignes C03 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

### 2.8. Avancement observé M2.7 — registre d’assets binaires hashés

| Couplage | Surface VERA désormais observée | Evidence M2.7 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C02` | Migration `007` et table `asset` SQLite stricte ; le contenu binaire appartient au store lié au ProjectIdentity, sans chemin ou fichier externe. | `tests/test_assets.py` : migration 6→7, enregistrement/lecture exacte, hash/taille/type, immuabilité et rollback ; wheel vérifié ; `LOG-0024`. | Runtime de fichiers, checkpoint/policy de filesystem, exports, doctor, comportement de stockage V1 et parité ARET. | `SPLIT` |
| `C16` | `AssetService` écrit un asset append-only avec SHA-256, taille et media type, puis ne restitue les bytes qu’après revérification de hash et taille ; audit atomique `ASSET_RECORDED`. | Tests de hash altéré, duplicat, rewrite/delete SQL refusés et audit/rollback ; scan ciblé et wheel isolé ; `LOG-0024`. | Evidence/proof, execution/validator, admission `PROVEN`, HMAC, relation avec knowledge, import croisé, bundle et parité historique. | `SPLIT` |

> M2.7 établit un contenu binaire canonique vérifié avant lecture sans ouvrir de filesystem externe ni de sémantique d’evidence. Les lignes C02 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

### 2.9. Avancement observé M2.8 — association knowledge–asset déclarative

| Couplage | Surface VERA désormais observée | Evidence M2.8 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C16` | Migration `008` et sidecar `knowledge_asset_link` immutable entre une knowledge et un asset existants ; foreign keys, unicité de paire, lecture exacte de l’association et audit atomique. | `tests/test_knowledge_asset_links.py` : migration 7→8, endpoints/identifiants invalides, duplicat, immuabilité SQL, absence de mutation des endpoints et audit/rollback ; wheel vérifié ; `LOG-0027`. | Evidence/proof, admission `PROVEN`, validator/execution/gate, relation générique, listing/traversal, lecture de contenu par liaison, HMAC, import croisé, bundle et parité historique. | `SPLIT` |
| `C03` | Les associations portent exclusivement les identifiants génériques de knowledge et d’asset ; elles n’introduisent aucun `component`, `function`, symbole ou vocabulaire technique. | Validation des deux endpoints VERA, scan ciblé du nouveau Core et wheel isolé ; `LOG-0027`. | Import des composants V1, liens de connaissance spécialisés, symboles, migration de données et parité fonctionnelle ARET. | `SPLIT` |

> M2.8 rend la référence knowledge–asset explicite sans qualifier l’asset de preuve, sans mutation de knowledge et sans ouvrir de graph traversal. Les lignes C03 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

### 2.10. Avancement observé M2.9 — index borné des associations knowledge–asset

| Couplage | Surface VERA désormais observée | Evidence M2.9 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C16` | Migration `009` et index inversé de `knowledge_asset_link` ; listes directes, ordonnées et bornées par knowledge ou asset existant, retournant uniquement les métadonnées de liaison. | `tests/test_knowledge_asset_index.py` : migration 8→9, ordre, borne, endpoints/limites invalides, endpoint sans lien et absence de contenu ; wheel vérifié ; `LOG-0030`. | Evidence/proof, admission `PROVEN`, validator/execution/gate, relation générique, recherche libre, traversal multi-sauts, lecture de contenu par index, HMAC, import croisé, bundle et parité historique. | `SPLIT` |
| `C03` | L’index n’expose que des identifiants génériques de knowledge et d’asset ; il n’introduit aucun `component`, `function`, symbole ou vocabulaire technique. | Validation d’endpoints VERA, scan ciblé du nouveau Core et wheel isolé ; `LOG-0030`. | Import des composants V1, liens de connaissance spécialisés, symboles, migration de données et parité fonctionnelle ARET. | `SPLIT` |

> M2.9 rend observables les associations directes d’un endpoint exact sans ouvrir de recherche libre, de traversal ou de lecture de contenu. Les lignes C03 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

### 2.11. Avancement observé M2.10 — provenance documentaire déclarative des assets

| Couplage | Surface VERA désormais observée | Evidence M2.10 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C02` | Migration `010` et table stricte `asset_source` attachant à un asset existant repository, revision, chemin relatif, lignes, section et SHA-256 déclarés ; aucune ressource externe n’est ouverte. | `tests/test_asset_provenance.py` : migration 9→10, attache/lecture/liste, données/endpoints invalides, duplicat, immuabilité SQL, rollback et asset inchangé ; wheel vérifié ; `LOG-0033`. | Runtime de fichiers, comparaison de contenu source↔asset, checkpoint/policy filesystem, exports, doctor, comportement de stockage V1 et parité ARET. | `SPLIT` |
| `C16` | `AssetSourceService` enregistre des références documentaires immuables et hashées, avec audit atomique ; les références restent déclaratives et ne confèrent aucune preuve. | Tests de confinement de chemin, hash/plage invalides, rewrite/delete SQL refusés et audit/rollback ; scan ciblé et wheel isolé ; `LOG-0033`. | Evidence/proof, admission `PROVEN`, execution/validator/gate, HMAC, relation générique, traversal, lecture d’asset, import croisé, bundle et parité historique. | `SPLIT` |

> M2.10 rend l’origine documentaire d’un asset explicitement déclarable sans ouvrir le document, vérifier son contenu ou le convertir en preuve. Les lignes C02 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

### 2.12. Avancement observé M2.11 — index exact des sources knowledge par hash

| Couplage | Surface VERA désormais observée | Evidence M2.11 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C16` | Migration `011` et index `knowledge_source(source_hash, knowledge_id, id)` ; liste directe, ordonnée et bornée des références déclaratives partageant un hash exact, sans lire aucune knowledge ou document. | `tests/test_knowledge_source_hash_index.py` : migration 10→11, hash partagé sur knowledge distinctes, ordre, borne, hash/limites invalides, résultat vide et absence d’audit ; wheel vérifié ; `LOG-0038`. | Evidence/proof, admission `PROVEN`, validator/execution/gate, ouverture/fetch/import de document, comparaison de hash, recherche textuelle, préfixe de hash, traversal, HMAC, bundle et parité historique. | `SPLIT` |
| `C03` | L’index ne retourne que des références génériques `knowledge_source` et des identifiants knowledge ; il n’introduit aucun `component`, `function`, symbole ou vocabulaire technique. | Validation SHA-256/bornes, scan ciblé du nouveau Core et wheel isolé ; `LOG-0038`. Le candidat d’index d’assets a été rejeté comme redondant dans `LOG-0036`. | Import des composants V1, liens de connaissance spécialisés, symboles, migration de données et parité fonctionnelle ARET. | `SPLIT` |

> M2.11 rend découvrables les références déclaratives qui partagent un hash exact sans lire les knowledge liées, ouvrir un document ou assimiler cette corrélation à une preuve. Les lignes C03 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.

### 2.13. Avancement observé M2.12 — Symbol Registry générique

| Couplage | Surface VERA désormais observée | Evidence M2.12 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C04` | Migration `012` et `symbol` immutable, obligatoirement rattaché à une `entity`, avec `kind`, locator déclaratif `path`, `identifier`, signature et metadata JSON. L’unicité `(entity_id, path, identifier)`, la lecture exacte et l’audit atomique sont établis sans type `component` ni modèle `function_symbol`. | `tests/test_symbols.py` : migration 11→12, création/lecture exacte, URI, owner inconnu, doublon sémantique, entrées invalides, rollback d’audit et refus SQL des UPDATE/DELETE ; suite complète et wheel isolé validés ; `LOG-0042`. | Import V1 `function_symbol → symbol`, conservation des IDs/source provenance, relation ou type configurable de pack, scan/résolution de code, lecteur `ARET://function`, rollback de migration de données et parité fonctionnelle ARET. | `SPLIT` |
| `C16` | Le registre ajoute une mutation métier append-only : FK d’owner, audit dans la même transaction et triggers anti-réécriture/suppression. | `tests/test_symbols.py` : doublon, FK, audit/rollback, immuabilité SQL ; `LOG-0042`. | Audit des couches Evidence/Execution/Gate, import/bundle et parité historique. | `SPLIT` |

> M2.12 ferme une ressource déclarative `symbol` du schéma universel ; il ne lit pas de fichier, ne recherche pas, ne résout pas de code et ne constitue aucune compatibilité ou preuve ARET. Les lignes C04 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.
