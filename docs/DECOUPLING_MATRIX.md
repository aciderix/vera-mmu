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
| `C04` | `function_symbol` impose un parent `component` et une unicité `(component,module,symbol)` ; ses adresses sont `ARET://function`. | `schema/001_initial.sql:28–37`; `core/repository.py` opérations `register_function`; baseline `hashes/schema_sha256.txt`. | `symbol` technique optionnellement lié à une entité ; type et contraintes déclarés par profil/pack. | Ajouter `symbol` universel ; créer un importeur V1 `function_symbol → symbol` en conservant les IDs source dans la provenance. Le Core 034 peut enregistrer un batch générique `SYMBOL`, sans interpréter la source legacy. | Import exact, unicité configurable, relations vers entité, lecteur V1, rollback de migration de données. | I001, I003, I011, I014, I015 | `SPLIT` |
| `C05` | `brick` encode la roadmap ARET, son état et un lien composant ; la migration 005 ajoute milestone, plateforme et priorité. | `schema/001_initial.sql:39–47`; `schema/005_roadmap_bricks.sql:1–10`; `core/repository.py` opérations `register_brick`/`update_brick`; `tests/test_roadmap.py`. | `work_item` typé, hiérarchique et relié au Work Graph ; `ROADMAP_BRICK` devient un type de pack ARET. | Introduire `work_item` et son état universel ; importer les briques avec leur métadonnée sous namespace ARET ; conserver le Front V1 lisible. Le Core 034 peut enregistrer un batch générique `WORK_ITEM`, sans décider de la sémantique legacy. | Cycle de vie, Front actif, ordre roadmap, liens, ajout de dépendance/cycle et import V1. | I001, I003, I009, I011, I014, I015 | `SPLIT` |
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

### 2.7. Avancement observé M4.1 — compatibilité d’adressage ARET V1 en lecture

| Couplage | Surface VERA désormais observée | Evidence M4.1 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C01` | `vera_mmu.domain_packs.aret.addressing` parse et construit la surface V1 fermée `ARET://` sous forme strictement canonique, sans lookup, import, mutation ni conversion en `vera://`. | `tests/test_aret_address_compatibility.py` : round-trip des ressources fermées, encodage canonique, rejet type/schéma/forme invalide et absence de dépendance du Core ; suite `192 passed, 14 subtests passed` et wheel isolée ; `LOG-0123`. | Fixtures historiques connectées au store, lecteur de ressources V1, conversion explicite, import de données, comportement MCP et parité baseline ARET. | `SPLIT` |

> M4.1 établit seulement un lecteur de syntaxe V1 dans le Domain Pack. Il ne rend aucune ressource ARET lisible dans VERA, ne migre aucune donnée et ne peut justifier une parité ARET.

### 2.8. Avancement observé M4.2 — manifeste du runtime ARET V1

| Couplage | Surface VERA désormais observée | Evidence M4.2 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C02` | `vera_mmu.domain_packs.aret.runtime` déclare sans I/O les conventions V1 : override `ARET_MEMORY_DIR`, `.aret-memory`, `aret_memory.sqlite`, `artifacts` et `exports`. | `tests/test_aret_runtime_manifest.py` : valeurs exactes, immuabilité, membres relatifs et indépendance du Core ; suite `194 passed, 14 subtests passed` et wheel isolée ; `LOG-0125`. | Résolution bornée, override contrôlé, création de runtime, ouverture du store V1, WAL/checkpoint, doctor, migration, compatibilité de données et parité baseline ARET. | `SPLIT` |

> M4.2 décrit le layout V1 seulement. Il ne consulte pas l’environnement, ne résout ni ne crée de chemin et ne peut constituer une preuve de compatibilité de runtime ou de store.

### 2.9. Avancement observé M4.3 — manifeste du schéma applicatif ARET V1

| Couplages | Surface VERA désormais observée | Evidence M4.3 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C03`, `C04`, `C05`, `C06`, `C16` | `vera_mmu.domain_packs.aret.schema` déclare les migrations 001–006 et l’inventaire fermé des dix-huit tables applicatives V1, sans tables FTS internes. | Baseline inspectée une fois en SQLite `mode=ro`; `tests/test_aret_schema_manifest.py` vérifie migrations, tables, exclusion FTS et indépendance du Core; suite `196 passed, 14 subtests passed` et wheel isolée; `LOG-0127`. | Lecture de lignes, mapping `component`/`function_symbol`/`brick` vers les ressources universelles, import non fusionnel, provenance, evidence/proof, audit, FTS, store/runtime et parité ARET. | `SPLIT` |

> M4.3 est un inventaire de noms seulement. Il ne rend aucune table ni donnée compatible, ne lit aucune SQLite en production et ne fournit aucune conversion ni garantie de parité.

### 2.10. Avancement observé M4.4 — profil de compatibilité ARET V1

| Couplages | Surface VERA désormais observée | Evidence M4.4 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C01`–`C06`, `C16` | `vera_mmu.domain_packs.aret.profile` compose les manifestes M4.1–M4.3 sous `aret-v1-compatibility`, limité à `parse_address`, `describe_runtime` et `describe_schema`; le profil déclare runtime, lecture SQLite, import et écriture VERA interdits. | `tests/test_aret_compatibility_profile.py` : composition exacte, opérations permises/interdites et indépendance du Core; suite `198 passed, 14 subtests passed` et wheel isolée; `LOG-0129`. | Adapter de profil opérationnel, configuration de projet, runtime/store, mappings de ressources et données, import non fusionnel, pipelines, playbook, proof/evidence, hooks, toolchain et parité ARET. | `SPLIT` |

> M4.4 formalise le contrat de non-opérationnalité des surfaces de compatibilité initiales. Il ne crée aucune capacité d’accès, de migration ou de conversion supplémentaire.

### 2.11. Avancement observé M4.5 — mappings structurels explicitement import-gated

| Couplages | Surface VERA désormais observée | Evidence M4.5 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C03`, `C04`, `C16` | `vera_mmu.domain_packs.aret.mapping` déclare seulement `component→entity` (`COMPONENT`), `function_symbol→symbol` et `brick→work_item`; chaque entrée exige un import explicite. | `tests/test_aret_structural_mappings.py` : triplet fermé, immuabilité, exclusion des tables de données/opérationnelles et indépendance du Core; suite `200 passed, 14 subtests passed` et wheel isolée; `LOG-0131`. | Politique/source d’import, lecture de lignes, conversion de champs et statuts, identité/provenance de lot, rollback, audit, preuves, validation post-import et parité ARET. | `SPLIT` |

> M4.5 n’est pas un importeur. Le registre marque les seules formes structurelles déjà revues et laisse toutes les sémantiques de données en refus explicite jusqu’à un lot ultérieur.

### 2.12. Avancement observé M4.6 — préparation fail-closed d’un import de composant

| Couplages | Surface VERA désormais observée | Evidence M4.6 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C03`, `C04`, `C16` | `vera_mmu.domain_packs.aret.import_preparation` construit exclusivement une demande `component→entity` de type `COMPONENT`, liée à un `ProjectIdentity`, un SHA-256 source déclaré, un identifiant de demande et un acteur. | `tests/test_aret_component_import_preparation.py` : liaison explicite, refus des entrées non canoniques/non liées, état `PREPARED_NOT_EXECUTED` et attestation `UNVERIFIED_DECLARATION`; suite `210 passed, 14 subtests passed` et wheel isolée; `LOG-0133`. | Localisation/lecture de source, vérification de l’empreinte, mapping de lignes/champs/statuts, transaction VERA, provenance/audit, collisions, rollback, evidence/proof, validation post-import et parité ARET. | `SPLIT` |

> M4.6 n’ouvre ni source ni store VERA. Le SHA-256 est une déclaration syntaxiquement contrôlée, non une attestation calculée ou vérifiée; aucune ligne `component` n’est lue, convertie ou écrite.

### 2.13. Avancement observé M4.7 — attestation bornée d’un snapshot ARET V1

| Couplages | Surface VERA désormais observée | Evidence M4.7 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C02`, `C03`, `C16` | `vera_mmu.domain_packs.aret.source_attestation` lit uniquement les bytes du fichier attendu `.aret-memory/aret_memory.sqlite` sous une racine absolue, existante, canonique et non liée; il vérifie le SHA-256 déclaré par M4.6 et refuse toute dérive stable de fichier. | `tests/test_aret_source_attestation.py` : hash/size, référence baseline fixe, racine/fichier liés ou absents, préparation modifiée et refus de capacités interdites; suite `219 passed, 14 subtests passed`, wheel isolée; attestation read-only ponctuelle de la baseline; `LOG-0135`. | Vérification du commit/répertoire Git source, ouverture/inspection SQLite et version réellement stockée, lecture de lignes, mapping de champs/statuts, transaction VERA, provenance/audit, collisions, rollback, evidence/proof, validation post-import et parité ARET. | `SPLIT` |

> M4.7 atteste seulement un snapshot de bytes dont la localisation respecte la convention V1. La référence de baseline est contrôlée contre une constante de pack, mais aucune identité Git ni contenu de schéma n’est vérifié par le module; aucune ligne n’est lue, convertie ou écrite.

### 2.14. Avancement observé M4.8 — identité Git read-only de la source attestée

| Couplages | Surface VERA désormais observée | Evidence M4.8 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C02`, `C03`, `C16` | `vera_mmu.domain_packs.aret.git_identity` vérifie que la racine source M4.7 appartient à une racine Git canonique, que `HEAD` égale la baseline V1 fixée et que l’arbre est propre. Les seules commandes sont les requêtes Git fixes `rev-parse --show-toplevel`, `rev-parse HEAD` et `status --porcelain=v1 --untracked-files=all`, sans shell, hooks, configuration globale/système ni locks optionnels. | `tests/test_aret_git_source_identity.py` : liaison à M4.7, commit attendu, dépôt propre, racine/attestation divergentes et capacités interdites; suite `224 passed, 14 subtests passed`, wheel isolée; vérification ponctuelle de la baseline; `LOG-0137`. | Signature ou origine distante du commit, vérification cryptographique de provenance, inspection SQLite/migrations, lecture de lignes, mapping de champs/statuts, transaction VERA, provenance/audit de lot, rollback, evidence/proof, validation post-import et parité ARET. | `SPLIT` |

> M4.8 établit une identité Git locale, propre et explicitement figée pour un snapshot déjà attesté. Elle ne rend pas le contenu SQLite lisible, ne certifie pas l’auteur/le remote/la signature du commit et ne déclenche aucun import.

### 2.15. Avancement observé M4.9 — inspection SQLite read-only du manifeste V1

| Couplages | Surface VERA désormais observée | Evidence M4.9 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C02`, `C03`, `C04`, `C05`, `C16` | `vera_mmu.domain_packs.aret.sqlite_schema` ouvre seulement le snapshot M4.7/M4.8 via `mode=ro&immutable=1`, active `query_only`, lit les versions de `schema_migrations` et les seuls noms de tables applicatives de `sqlite_schema`, puis exige l’égalité exacte avec le manifeste V1. | `tests/test_aret_sqlite_schema_inspection.py` : manifest exact, hash divergent, migrations/tables divergentes, liaison d’identité et SQL fermé; suite `229 passed, 14 subtests passed`, wheel isolée; inspection ponctuelle de la baseline, hash stable; `LOG-0139`. | Colonnes, contraintes, index, triggers, FTS détaillé, toutes lignes métier, mapping de champs/statuts, transaction VERA, provenance/audit, collisions, rollback, evidence/proof, validation post-import et parité ARET. | `SPLIT` |

> M4.9 vérifie une structure de manifeste, pas les données qui s’y trouvent. Il n’exécute que des requêtes `SELECT` de métadonnées nominatives; aucune ligne des tables applicatives, aucun contenu de connaissance, preuve, composant ou brick n’est lu, converti ou écrit.

### 2.16. Avancement observé M4.10 — lecture paginée brute de `component`

| Couplages | Surface VERA désormais observée | Evidence M4.10 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C03`, `C04`, `C05`, `C16` | `vera_mmu.domain_packs.aret.component_reader` lit exclusivement les colonnes source `id`, `title`, `description`, `created_at`, `created_by` de `component`, via pages keyset strictement ordonnées par `id`, bornées à 100 et liées à l’inspection M4.9 ainsi qu’au hash de snapshot stable. | `tests/test_aret_component_source_reader.py` : page brute, ordre/pagination, limites/cursor, hash/inspection/chemin divergents et interdictions mapping/import; suite `238 passed, 14 subtests passed`, wheel isolée; lecture ponctuelle de 17 composants baseline sans afficher le contenu; `LOG-0141`. | Mapping vers `entity`, politique de collision/non-fusion, normalisation de champs, identité VERA cible, transaction/rollback, provenance/audit, evidence/proof, admission, écriture de lot, autres tables et parité ARET. | `SPLIT` |

> M4.10 rend observables des lignes legacy brutes, non des entités VERA. Chaque champ est retourné tel que lu depuis `component`; aucune décision de conversion, de qualité, de statut, de fusion, d’admission ou de promotion n’est prise.

### 2.17. Avancement observé M4.11 — préflight `component→entity` fail-closed

| Couplages | Surface VERA désormais observée | Evidence M4.11 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C03`, `C04`, `C05`, `C06`, `C16` | `vera_mmu.domain_packs.aret.component_import_preflight` lie une demande M4.6, une inspection M4.9 et une page M4.10 au même hash source. Il impose `REJECT_EXISTING_TARGET`, `FORBID` merge/promotion/write et exige rollback/audit/provenance avant toute écriture future. | `tests/test_aret_component_import_preflight.py` : liaison complète, préparation/page/inspection dérivées, ordre, acteur/ID et interdictions I/O/écriture; suite `243 passed, 14 subtests passed`, wheel isolée; préflight ponctuel baseline de 17 composants en état `PREFLIGHT_NOT_EXECUTABLE`; `LOG-0143`. | Projection de champs vers entity, identifiants cibles, recherche de collisions dans VERA, transaction de batch, rollback effectif, audit/provenance effectifs, evidence/proof, admission, écriture/import et parité ARET. | `SPLIT` |

> M4.11 est une contrainte de sécurité ex ante, non une permission d’écrire. Il prépare l’obligation de contrôler collision, rollback, audit et provenance avant un futur write-path; aucune de ces opérations n’est encore exécutée ni démontrée.

### 2.18. Avancement observé M4.12 — projection non écrivable `component→entity`

| Couplages | Surface VERA désormais observée | Evidence M4.12 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C03`, `C04`, `C05`, `C06`, `C16` | `vera_mmu.domain_packs.aret.component_entity_projection` projette chaque ligne brute préflightée en brouillon générique d’entity, avec identifiant `aret-component--<source_id>`, adresse `vera://`, type `component` à enregistrer ultérieurement et métadonnées de source explicites. | `tests/test_aret_component_entity_projection.py` : déterminisme, adresse/metadata, preflight/page/hash divergents, texte/ID non canoniques et interdictions store/écriture; suite `247 passed, 14 subtests passed`, wheel isolée; projection ponctuelle de 17 brouillons baseline en `PROJECTED_NOT_WRITABLE`; `LOG-0145`. | Enregistrement de type entity, collision cible, création transactionnelle, rollback, audit/provenance effectifs, evidence/proof, admission, écriture/import et parité ARET. | `SPLIT` |

> M4.12 définit une représentation cible vérifiable sans créer de cible. Le type `component`, les identifiants et les métadonnées sont des drafts soumis aux contrôles futurs du Core; aucun `entity_type` ni `entity` n’est enregistré par ce lot.

### 2.19. Avancement observé M4.13 — contrôle read-only des collisions cible

| Couplages | Surface VERA désormais observée | Evidence M4.13 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C03`, `C04`, `C05`, `C06`, `C16` | `vera_mmu.domain_packs.aret.component_target_collision` vérifie dans un store VERA existant et identitaire l’absence exacte du type `component` et de tout identifiant de draft projeté. Toute existence est rejetée; un résultat clair reste `TARGET_CLEAR_NOT_WRITABLE`. | `tests/test_aret_component_target_collision_check.py` : cible claire, type existant, entité existante, identité/état divergents et SQL uniquement `SELECT`; suite `252 passed, 14 subtests passed`, wheel isolée; contrôle baseline de 17 brouillons et audit cible invariant; `LOG-0147`. | Enregistrement du type, création transactionnelle d’entity, rollback, audit/provenance effectifs, evidence/proof, admission, écriture/import et parité ARET. | `SPLIT` |

> M4.13 constate l’absence de collisions dans un store ouvert par le caller; il ne crée pas ce store et n’ouvre aucune transaction. L’absence d’un type/ID n’est pas une permission d’écrire : c’est seulement une précondition bornée pour un lot ultérieur distinct.

### 2.20. Avancement observé M4.14 — primitif Core générique de batch atomique

| Couplages | Surface VERA désormais livrée | Evidence M4.14 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C03`, `C04`, `C05`, `C06`, `C16` | `EntityService.register_type_and_create_batch` enregistre un type générique absent et 1–100 entités validées dans une transaction unique, avec audit de type/entités. Tout conflit ou échec rollbacke type, entités et audits de ce batch. Le Core ne référence aucun pack ni domaine. | `tests/test_entity_atomic_batch.py` : succès, audits, doublons avant écriture, conflit à mi-lot avec rollback et type déjà existant; suite `256 passed, 14 subtests passed`, wheel isolée; `LOG-0149`. | Liaison de cette primitive à M4.11–M4.13, provenance de source, input package, write-path ARET, vérification post-import, rollback métier sélectif, evidence/proof, admission et parité ARET. | `SPLIT` |

> M4.14 fournit une capacité transactionnelle universelle, non un importeur. Une transaction annulée garantit l’absence de création partielle en cas d’échec; elle ne confère ni droit à l’invocation depuis un pack, ni suppression/réversion d’un batch déjà validé.

### 2.21. Avancement observé M4.15 — premier import autorisé `component→entity`

| Couplages | Surface VERA désormais livrée | Evidence M4.15 | Dimensions toujours inconnues | État des lignes mères |
|---|---|---|---|---|
| `C03`, `C16` | `vera_mmu.domain_packs.aret.component_authorized_import` crée une autorisation explicite et sans effet propre, liée à M4.11–M4.13, puis appelle exclusivement `EntityService.register_type_and_create_batch`. L’import recontrôle les collisions au write-path, crée type+entities/audits dans une transaction et retourne `IMPORTED_NO_PROMOTION`. | `tests/test_aret_component_authorized_import.py` : autorisation sans écriture, liaisons divergentes refusées, création exacte/audit, collision relue et rollback ; suite Core `261 passed, 14 subtests passed` ; intégration de la page baseline de 17 composants dans un store VERA temporaire ; scans Core/pack et wheel isolée ; commit `034efaf9f6d845742d2209c89099d10dd5fc4ad0`. | Pagination totale/idempotence/ledger, import des liens et autres tables, provenance de lot persistée, post-validation, réversion explicite, runtime/WAL, preuves/admission, `function_symbol`, `brick`, capabilities, toolchain, MCP/hooks/bundles/VCS et parité ARET. | `SPLIT` ; parité `UNKNOWN` ; C07/C08 restent `BLOCKED` sous `MEM-WALL-001`. |

> M4.15 est un premier write-path autorisé, borné à une page pré-projetée de composants et à une cible VERA vide. Il ne fusionne pas, ne crée aucune proof, ne promeut aucun état et ne modifie jamais ARET-MMU. Le [registre de clôture M4](continuity/M4_COMPLETION_REGISTER.md) rend explicites les gates restantes avant tout `M4.EXIT`.

### 2.22. Avancement observé M4-A — migration `component` ledger-backed

| Sous-lot | Couplages | Surface VERA désormais livrée | Evidence | Dimensions toujours inconnues | État |
|---|---|---|---|---|---|
| Resolver runtime et safety WAL/SHM | `C02`, `C16` | `resolve_aret_v1_runtime` accepte seulement une racine source existante/canonique et un mapping explicite `ARET_MEMORY_DIR` ou le layout V1 par défaut, sans consulter l’environnement global ni créer de chemin. La safety gate refuse tout `-wal`/`-shm` actif ou lié au lieu d’ouvrir SQLite ou de checkpoint. | `tests/test_aret_runtime_resolution_safety.py` : default/override, répertoires et symlinks invalides, snapshot/sidecars, stabilité et scan read-only ; baseline réelle `DEFAULT_RUNTIME_LAYOUT`, `NO_WAL_SIDECARS`, taille `11280384`; suite `298 passed, 14 subtests passed` et roue isolée ; commit `c18d08c675c1bd69602471c082efc1c978b643e1`. | Lifecycle de checkpoint externe, conformance runtime élargie et parité runtime V1. | `SPLIT` |
| Batch Core sur type déjà enregistré | `C03`, `C16` | `EntityService.create_batch_for_registered_type` crée 1–100 entités pour un type générique existant, en transaction unique avec audit par entité et rollback intégral. | `tests/test_entity_existing_type_batch.py` : type absent, doublons, conflit tardif et rollback ; suite complète et roue isolée ; commit `1ea116faeac58958311e6f135a6c68df8e6a5a53`. | Import, provenance de lot et compatibilité ARET. | `SPLIT` |
| Ledger générique d’import 033 | `C03`, `C16` | Migration 033 ajoute `import_batch`/`import_batch_entity` append-only ; `ImportBatchService` fingerprinte canoniquement le batch, refuse la réutilisation divergente, rejoue exactement sans écriture et crée type/entités/liens/audit atomiquement. | `tests/test_entity_import_batches.py` : commit, idempotence, fingerprint divergent, type compatible/incompatible et rollback ; migration historique 001→033, suite complète et roue isolée ; commit `e3105b00a6d6152c5a833d0b7bafcd579442062c`. | Ledger de tous les types de données ARET, rollback d’un batch déjà committé et parité. | `SPLIT` |
| Conformité source `component` | `C03`, `C16` | Le pack inspecte en `mode=ro&immutable=1` les cinq colonnes `component`, leur ordre/type/nullabilité/PK/default, avec hash avant/après et refus de dérive. | `tests/test_aret_component_schema_conformance.py` : conformant, colonnes manquantes/nullable/extra, inspection divergente et scan read-only ; vérification baseline ; roue isolée ; commit `cdf65f7150023d6dd57739f991db8c1ac93aeba2`. | Contraintes/index/triggers/FTS/séquences et schémas des autres tables. | `SPLIT` |
| Chaînage runtime override | `C02`, `C03`, `C16` | L’attestation M4.7 accepte une résolution+safety liées, M4.8 porte le snapshot attesté, puis M4.9 et M4.10 suivent ce snapshot exact au lieu de reconstruire le layout par défaut. Le layout historique par défaut reste strict. | `tests/test_aret_runtime_resolution_chain.py` : override→attestation, inspection/reader override, mismatch de racine; intégration sur copie temporaire de la baseline : override, `NO_WAL_SIDECARS`, 17 records; suite `301 passed, 14 subtests passed`, roue isolée ; commit `4f9d1ed0c881d41b7e98a01e228f05903e65a408`. | Import via override, conformance de toutes les sources et parité runtime complète. | `SPLIT` |
| Post-validation de page component | `C03`, `C16` | Après import, relit sans écriture le batch, ses liens source→cible et les entités, puis exige l’égalité exacte avec les drafts autorisés ; résultat `POST_VALIDATED_NO_PROMOTION`. | `tests/test_aret_component_post_validation.py` : succès, request divergent, projection/ledger divergent, zéro audit/evidence/proof; suite `305 passed, 14 subtests passed`, roue isolée ; commit `2d237f05e762dd9cffc89a1c1c9a8c9be1da5ea9`. | Post-validation exhaustive/multi-pages et tous les autres mappings. | `SPLIT` |
| Import de page `component` en série | `C03`, `C16` | Le pack lie préflight/projection/conformité/identité à une autorisation de page explicite, exige une cible initiale vide ou une série ARET identique, puis délègue exclusivement au ledger ; aucun proof/evidence/promotion. | `tests/test_aret_component_page_import_series.py` : première/suivante page, idempotence, type manuel refusé, binding divergent, collision tardive/rollback ; baseline réelle : 17 records, 17 liens ledger, replay sans écriture, zéro evidence/proof link dans une cible temporaire ; roue isolée ; commit `8263d40b709acce40b946bd575cf8f648ae842b3`. | Source réelle multi-pages, cohérence WAL/runtime, post-validation exhaustive, autres tables, compatibilité et parité. | `SPLIT` ; `M4-A IN_PROGRESS` |

> **Verdict M4-A courant :** les mécanismes de page et de reprise sont prouvés sur fixtures et sur la page baseline disponible ; ils ne ferment pas `M4-EXIT-01` à `M4-EXIT-03`, car la policy WAL/runtime et les preuves de sources réellement multi-pages restent absentes.

### 2.23. Avancement observé M4-B — primitive Core de ressources structurelles

| Sous-lot | Couplages | Surface VERA désormais livrée | Evidence | Dimensions toujours inconnues | État |
|---|---|---|---|---|---|
| Ledger Core générique 034 | `C04`, `C05`, `C16` | Migration 034 ajoute `resource_import_batch`/`resource_import_batch_record` append-only. `ImportBatchService.commit_resource_import_batch` accepte exclusivement `SYMBOL`/`WORK_ITEM`, fingerprint le payload canonique, crée la cible via le service Core validé, lie le record, audite le commit, refuse l’incompatibilité et rejoue exactement sans écriture. Les transactions imbriquées utilisent des savepoints. | `tests/test_resource_import_batches.py` : success, kind inconnu, parent absent, conflit sémantique, rollback, replay, fingerprint divergent, upgrade 033→034 et triggers append-only ; `tests/test_store.py` : savepoints ; suite initiale Core `326 passed, 14 subtests passed` ; conformité/préflight M4-B : `340 passed, 14 subtests passed`, scans pack/Core et wheel isolée ; commits Core `77591e586d8dfa60bb0b49dd06f1c056d11658a0`/`8e0d56692c3f1a5b19d9e2ac1d40678f10c7c7fc` et commit pack `8d6e4fc2ec674ac3d2be8297ad3b3f9868239eaa`. | Collision de série, autorisation, import/post-validation ARET, cardinalité réelle, liens component, Front/statut et parité. La conformité source et le préflight lié sont désormais prouvés sans write-path. | `SPLIT` ; `M4-B IN_PROGRESS` |

> Le ledger 034 est une capacité Core **nécessaire mais non suffisante**. Il ne lit aucune source ARET, ne confère aucune autorisation et ne produit ni evidence, admission, proof/proof link ni promotion. Les états C04/C05/C16 et la parité ARET restent inchangés.

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

### 2.14. Avancement observé M2.13 — Work-Item Backbone

| Couplage | Surface VERA désormais observée | Evidence M2.13 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C05` | Migration `013` et `work_item` immutable, avec type fermé (`GOAL`, `EPIC`, `WORK_ITEM`, `SUBTASK`), statut initial `PLANNED`, parent optionnel déjà existant, priorité/assignee déclaratifs, metadata JSON et URI exacte. Les triggers refusent UPDATE/DELETE; aucun lifecycle ni work graph n’est ouvert. | `tests/test_work_items.py` : migration 12→13, création/lecture exacte, URI, types invalides, parent inconnu/self-parent, statut initial, rollback d’audit et refus SQL des UPDATE/DELETE ; suite complète et wheel isolé validés ; `LOG-0045`. | Migration V1 `brick → work_item`, milestones/plateformes/priorités ARET, lifecycle, Front, ordre roadmap, dépendances/cycles, gates/executions/evidence, import V1 et parité fonctionnelle ARET. | `SPLIT` |
| `C16` | Le backbone ajoute une mutation métier append-only : parent FK, statut initial SQL fermé, timestamps identiques, audit dans la même transaction et triggers anti-réécriture/suppression. | `tests/test_work_items.py` : FK/self-parent, statut, audit/rollback et immuabilité SQL ; `LOG-0045`. | Audit des couches Capability/Execution/Evidence/Gate, import/bundle et parité historique. | `SPLIT` |

> M2.13 ferme la ressource structurelle `work-item` du schéma universel ; il ne contient aucun cycle de vie, work graph, Front, reprise, gate, exécution ou preuve. Les lignes C05 et C16 restent `SPLIT`, et toute parité ARET reste `UNKNOWN`.


### 2.15. Avancement observé M2.14 et M3.S1 — contracts, preuve dérivée et gates bornées

| Couplage | Surface VERA désormais observée | Evidence M3.S1 | Dimension toujours inconnue | État de la ligne mère |
|---|---|---|---|---|
| `C05` | Migration `019` ajoute des dépendances directes append-only de `work_item` avec refus de cycle et des gates immuables reliées à une evidence. M3.11 ajoute des exigences supplémentaires append-only; M3.12 ajoute des événements de lifecycle `START`/`COMPLETE`/`CANCEL` qui dérivent un état sans réécrire le work item. M3.15 ajoute une policy immutable de gate `ALL`/`ANY`/`AT_LEAST`, lue uniquement sur admissions existantes; les exigences sont gelées après policy. M3.16 ajoute une readiness dérivée et un démarrage strict optionnel, sans réécrire `work_item`. L’évaluation de gate et le lifecycle ne modifient aucun knowledge. | `tests/test_work_graph_gates.py`, `tests/test_gate_policies.py`, `tests/test_work_lifecycle.py` : dépendance, refus de cycle, gate simple/multi-evidence, modes `ALL`/`ANY`/`AT_LEAST`, upgrade 026→027, readiness/démarrage strict, lecture pure et lifecycle `PLANNED`→`ACTIVE`→`COMPLETED` avec work item historique inchangé; suite de 168 tests et 14 sous-tests, wheel isolé; `LOG-0068`, `LOG-0070`, `LOG-0085`, `LOG-0088`, `LOG-0098`, `LOG-0100`. | Front, ordre roadmap, traversal, pause/réouverture/orchestration, propagation parent/enfant, pondération/expiration/révocation de gate, import V1 `brick`, exécution réelle ARET et parité fonctionnelle. | `SPLIT` |
| `C06` | Migration `015` apporte un contrat fermé, immutable et versionné sur une capability existante : runner profile, policy réseau, timeout, schéma JSON et `yields_proof`. M3.7 valide localement un sous-ensemble fermé de paramètres (`object`, propriétés scalaires, `required`, `additionalProperties`). M3.8 ajoute une policy append-only `ALLOW`/`DENY`/`CONFIRM`. M3.14 étend le catalogue SQL uniquement à `NOOP` / `EVIDENCE_HASH` sous `DENY_NETWORK`; les deux runners exigent `ALLOW` avant toute écriture et n’exécutent aucune commande ni accès réseau. | `tests/test_capability_contracts.py`, `tests/test_noop_execution_runner.py`, `tests/test_evidence_hash_runner.py`, `tests/test_capability_policies.py`; publications `LOG-0051`, `LOG-0055`; contrôles M3.S1 `LOG-0070`, M3.7 `LOG-0073`, M3.8 `LOG-0076` et M3.14 `LOG-0096` (migration 025→026, suite, wheel isolé). | JSON Schema général, confirmation interactive/révision de policy, dry-run, artefacts, runners additionnels, catalogue/adaptateur ARET et parité de `PIPELINES`. | `SPLIT` |
| `C07` | Migrations `016`–`018` fournissent evidence JSON hashée liée à une execution, admission immutable ne permettant `ADMITTED` que pour `PASS`, et preuve dérivée immutable reliée à knowledge/evidence/admission. M3.9 ajoute une policy de projet singleton `HMAC_SHA256` avec exigence HMAC optionnelle; le secret ne quitte jamais la mémoire et seul le digest est persisté. M3.10 ajoute le validator local `EVIDENCE_HASH`. M3.13 ajoute une policy d’admission : `VALIDATED_PASS_EVIDENCE` exige un résultat `PASS` préexistant sans déclencher de validation. M3.14 encapsule cette validation d’intégrité dans un runner local fermé : `PASS` ou `FAIL` reste un résultat persistant sans admission ni preuve implicite. | `tests/test_evidence_store.py`, `tests/test_evidence_admission.py`, `tests/test_knowledge_proof.py`, `tests/test_proof_policies.py`, `tests/test_validators.py`, `tests/test_admission_policies.py`, `tests/test_evidence_hash_runner.py`; publications `LOG-0058`, `LOG-0061`, `LOG-0067`; contrôles M3.S1 `LOG-0070`, M3.9 `LOG-0079`, M3.10 `LOG-0082`, M3.S2 `LOG-0090`, M3.13 `LOG-0093` et M3.14 `LOG-0096`. | Validators de contenu/oracles, rotation/révocation de secret, capture d’artefacts, runner ARET, toolchain/oracles réels et validation de parité. `MEM-WALL-001` bloque toujours ces dimensions. | `BLOCKED` — `MEM-WALL-001` |
| `C16` | Les couches execution, evidence, admission, preuve dérivée et gate sont séparées et append-only : execution≠evidence, evidence `PASS`≠admission, admission≠preuve, et la preuve ne réécrit pas knowledge. M3.14 confirme qu’une execution de validation hash `PASS` ou `FAIL` ne crée ni evidence, admission, preuve ni mutation de knowledge. M3.15 confirme qu’une policy/evaluation de gate lit seulement des admissions existantes et ne déclenche aucune écriture adjacente. M3.16 confirme que readiness et refus de démarrage strict n’écrivent rien tant que `START` est bloqué. | Migrations 014–019, 026–028, tests M3.S1/M3.14/M3.15/M3.16, triggers d’immutabilité et wheel isolé; `LOG-0070`, `LOG-0096`, `LOG-0098`, `LOG-0100`. | Relations/lifecycle complets, import croisé, bundles, policy de preuve de projet, validators/exécutions externes et parité historique ARET. | `SPLIT` |

> M3.S1 prouve des primitives universelles bornées, non une compatibilité ARET. En particulier, `C07` reste `BLOCKED` pour les oracles réels et `C08` reste inchangé sous `MEM-WALL-001`; aucun statut `SPLIT` n’est promu en `DONE`.
