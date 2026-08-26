# Mémoire factuelle du chantier VERA-MMU

> **Statut :** registre canonique de continuité documentaire.
>
> **Règle :** ce document conserve des faits, des décisions, des risques et des références ; la chronologie détaillée est tenue dans le [journal d’ingénierie](ENGINEERING_LOG.md).
>
> **Mise à jour :** append-only ; une correction ajoute un nouveau record qui supersède explicitement le précédent.

## 1. Contrat de la mémoire

Cette mémoire sert à reprendre le chantier sans dépendre d’un contexte conversationnel. Elle ne remplace pas le futur store SQLite de VERA-MMU ; elle est le registre de transition versionné tant que le Core universel ne possède pas encore les primitives de knowledge, evidence, audit et resume complètes.

| Règle | Application documentaire |
|---|---|
| **Fait ≠ hypothèse** | Chaque entrée est classée `PROVEN`, `OBSERVED`, `INFERRED`, `HYPOTHESIS`, `DECISION`, `RISK`, `BLOCKED` ou `SUPERSEDED`. |
| **Recherche ≠ lecture** | Le journal peut indexer ou résumer ; cette mémoire renvoie toujours à une source, un commit, une section ou un identifiant de journal. |
| **Append-only** | Une correction n’écrase pas l’ancien record : elle crée un record `SUPERSEDES: MEM-…`. |
| **Fail loud** | Une absence de preuve, une référence cassée ou une contradiction devient un record `RISK` ou `BLOCKED`, jamais une réussite implicite. |
| **Reprise contrôlée** | Avant modification, relire les sections 2, 5, 6 et 7, puis les entrées de journal citées. |

## 2. Identité, sources et baseline

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-ID-001` | Identité | Le produit s’appelle **VERA-MMU**, pour *Verifiable Epistemics & Relational Architecture*. Les conventions sont `vera-mmu`, `vera_mmu`, `vmmu`, `.vera-mmu/` et `vera://<project>/<resource>/<id>`. | `PROVEN` | [Identité officielle](../IDENTITY.md) | `LOG-0002` |
| `MEM-BASE-001` | Baseline ARET | Le clone local de référence ARET-MMU est à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`, branche `main`, arbre propre au relevé du 25 août 2026. | `OBSERVED` | Commande Git enregistrée ; dépôt [ARET-MMU][1] | `LOG-0001` |
| `MEM-BASE-002` | Baseline VERA | VERA-MMU est à `ef707339c245ee1d36b8a78312d1a441c86296dc`, branche `main`, arbre propre au relevé du 25 août 2026. | `OBSERVED` | `git rev-parse HEAD` et `git status --short` | `LOG-0002` |
| `MEM-SRC-001` | Source | La spécification fournie définit la cible : Core universel, Domain Packs, Project Profiles, Capability/Gate Engine, MCP Compiler, Runtime Adapters et Dashboard. | `OBSERVED` | `UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md`, sections 0–1 et 60, fourni par le propriétaire. | `LOG-0003` |
| `MEM-SRC-002` | Source | La doctrine ARET impose le cycle baseline → patch minimal → run → evidence → comparison → verdict → record, la non-régression et le fail loud. | `OBSERVED` | `pasted_content.txt`, sections 1–20, fourni par le propriétaire. | `LOG-0003` |
| `MEM-BASE-003` | Freeze M0.1 | Le baseline ARET a capturé l’inventaire, les hashes, l’environnement, les résultats pytest, la surface MCP/hook, un bundle de mécanique et un bundle Git pour le commit de référence. | `OBSERVED` | `/home/ubuntu/ARET_MMU_M0_1_BASELINE/BASELINE_REPORT.md` ; manifeste `05e9c126425a27d6440cb5e92c367bcae6676ff04b430fe4b3618c7afff7984d`. | `LOG-0006` |
| `MEM-BASE-004` | Mesures de référence | Le package compte 180 fichiers, 25 fichiers de tests, 90 tests collectés, 6 migrations SQL, 44 outils MCP `aret_*` détectés statiquement et 11 modules de hooks. | `OBSERVED` | Répertoire `ARET_MMU_M0_1_BASELINE/inventory/` et `hashes/`. | `LOG-0006` |
| `MEM-COMP-001` | Registre M0.2 | Seize couplages ARET ont une source, une frontière Core/pack, une stratégie de migration et un test de parité nommés : 14 sont `SPLIT` et 2 (`C07`, `C08`) restent `BLOCKED` par `MEM-WALL-001`. | `OBSERVED` | [Matrice de découplage](../DECOUPLING_MATRIX.md), sections 1–3. | `LOG-0007` |

## 3. Faits d’architecture établis

| ID | Sujet | Fait ou décision | Statut | Source primaire | Journal |
|---|---|---|---|---|---|
| `MEM-ARCH-001` | Frontière | Le Core doit rester installable sans vocabulaire, corpus, binaire, outil, script ou doctrine ARET obligatoire. | `PROVEN` | [Invariants I015](../INVARIANTS.md) ; [matrice](../DECOUPLING_MATRIX.md) | `LOG-0002`, `LOG-0003` |
| `MEM-ARCH-002` | Épistémologie | La mémoire canonique est externe au modèle ; une assertion de modèle, un FIND, un test non authentifié ou une sortie shell brute ne sont pas des preuves suffisantes. | `PROVEN` | Invariants I001, I002, I004 et I006. | `LOG-0002` |
| `MEM-ARCH-003` | Evidence | Une promotion `PROVEN` nécessite une evidence admissible `PASS`, reliée à une exécution et à son environnement. | `PROVEN` | Invariants I004, I006 et spécification, sections 14–15. | `LOG-0003` |
| `MEM-ARCH-004` | Sécurité | Le client ne pourra sélectionner que des capabilities déclarées et lui fournir des paramètres bornés ; aucune entrée ne construira une commande arbitraire. | `PROVEN` | Invariants I007–I008 ; spécification, sections 12–13. | `LOG-0003` |
| `MEM-ARCH-005` | Reprise | La reprise doit être liée à un contrat hashé ; une mémoire importée dans un autre projet doit être rejetée. | `PROVEN` | Invariants I009–I011 ; spécification, sections 17 et 19. | `LOG-0003` |
| `MEM-ARCH-006` | Portabilité | Le futur générateur doit être déterministe : mêmes profile, packs et version de générateur impliquent même sortie canonique et `mcp_build_hash`. | `PROVEN` | Invariant I012 ; spécification, section 25. | `LOG-0003` |

## 4. État actuel vérifié et limites explicites

| ID | Élément | État | Statut | Limite ou condition |
|---|---|---|---|---|
| `MEM-STATE-001` | Package | Le package `vera_mmu` possède une identité de Project Profile déterministe et une CLI `vmmu identity`. | `OBSERVED` | La fondation est intentionnellement minimale ; la production MCP n’existe pas encore. |
| `MEM-STATE-002` | Gouvernance initiale | Les invariants, l’architecture, la matrice de découplage, l’identité et l’audit de nommage existent dans VERA-MMU. | `OBSERVED` | Ces documents doivent être maintenus avec les trois documents de continuité. |
| `MEM-STATE-003` | Persistence universelle | Les migrations SQL universelles, le store générique, les entités, relations, work items, executions, gates et bundles V2 ne sont pas encore implémentés. | `OBSERVED` | Aucun statut d’avancement ne peut les présenter comme partiellement « faits » sans preuves dédiées. |
| `MEM-STATE-004` | Compatibilité ARET | Il n’existe pas encore de pack ARET, d’importeur hors ligne, de lecteur `ARET://` ni de suite de parité dans VERA-MMU. | `OBSERVED` | La compatibilité est une cible critique, non une capacité actuelle. |
| `MEM-STATE-005` | Exécution et UI | Capability Engine, Gate Engine, compilateur MCP, adapters de runtime, CLI complète et Dashboard restent à construire. | `OBSERVED` | Ils doivent être introduits par lots séparés, testés et policy-gated. |
| `MEM-STATE-006` | Core M1 | Le Core contient un Project Profile canonique, `ProjectIdentity` avec fingerprint de topologie, adressage strict `vera://`, résolution mono/multi/no-Git et `RuntimeLocator` confiné. | `OBSERVED` | 21 tests et 14 sous-tests passent ; le Core n’ouvre encore aucun store, gate, evidence, bundle, MCP adapter ou pack. | `LOG-0009` |
| `MEM-STATE-007` | Substrate M2.1 | `SUPERSEDES: MEM-STATE-003` pour le sous-ensemble migrations/store. Le Core dispose d’un store SQLite lié au profile, d’un ledger checksumé, de métadonnées de format, d’audit technique et d’une transaction explicite. | `OBSERVED` | 31 tests et 14 sous-tests passent ; knowledge, entities, relations, evidence, bundles et services métier restent absents. | `LOG-0011` |
| `MEM-STATE-008` | Entity Registry M2.2 | `SUPERSEDES: MEM-STATE-003` pour le sous-ensemble types/entités. Le Core enregistre des types génériques puis crée/lit exactement des entités JSON canoniques avec audit atomique. | `OBSERVED` | 40 tests et 14 sous-tests passent ; relations, symboles, knowledge, evidence, bundles et services métier associés restent absents. | `LOG-0013` |
| `MEM-STATE-009` | Relation Registry M2.3 | `SUPERSEDES: MEM-STATE-003` pour le sous-ensemble relations. Le Core enregistre des types relationnels puis crée/lit exactement des arêtes immuables entre entités, avec contraintes source/cible et audit atomique. | `OBSERVED` | 48 tests et 14 sous-tests passent ; traversal, lifecycle, symboles, knowledge, evidence, bundles et services métier associés restent absents. | `LOG-0015` |
| `MEM-STATE-010` | Knowledge Registry M2.4 | `SUPERSEDES: MEM-STATE-003` pour le sous-ensemble knowledge. Le Core enregistre des types knowledge puis ajoute/lit exactement des assertions append-only hashées avec statuts initiaux sûrs et audit atomique. | `OBSERVED` | 57 tests et 14 sous-tests passent ; `PROVEN`, evidence, FTS/FIND, tags, sources, supersession, bundles et services métier associés restent absents. | `LOG-0017` |
| `MEM-STATE-011` | Knowledge Source Registry M2.5 | `SUPERSEDES: MEM-STATE-010` pour le sous-ensemble provenance déclarative. Le Core attache/lit des références documentaires immuables, hashées et bornées par lignes à une knowledge existante, sans ouvrir le document référencé. | `OBSERVED` | 65 tests et 14 sous-tests passent ; fetch, vérification de document, import, evidence, `PROVEN`, recherche, supersession et bundles restent absents. | `LOG-0019` |
| `MEM-STATE-012` | Knowledge Supersession Registry M2.6 | `SUPERSEDES: MEM-STATE-010` pour le sous-ensemble de remplacement déclaratif. Le Core enregistre/lit une relation directe immutable prédécesseur→successeur entre deux knowledge existantes, avec unicité des endpoints, anti-cycle et audit atomique. | `OBSERVED` | 72 tests et 14 sous-tests passent ; les knowledge restent inchangées. Mutation de statut, `SUPERSEDED`, version counter, traversal/listing, evidence, `PROVEN`, fetch/import, relations génériques et bundles restent absents. | `LOG-0021` |
| `MEM-STATE-013` | Asset Registry M2.7 | Le Core enregistre/lit des bytes binaires dans SQLite sous identifiant `vera://…/asset/…`, avec SHA-256, taille, media type, immuabilité et audit de création ; les bytes ne sont restitués qu’après revérification du hash et de la taille. | `OBSERVED` | 79 tests et 14 sous-tests passent ; chemins/fichiers externes, réseau, import/export, bundle, execution, evidence/proof, `PROVEN`, relation, recherche/listing et mutation/suppression restent absents. | `LOG-0024` |
| `MEM-STATE-014` | Knowledge-Asset Link Registry M2.8 | Le Core enregistre/lit une paire exacte immutable entre une knowledge et un asset existants, avec foreign keys, unicité de paire et audit atomique ; le lien ne lit aucun contenu et ne modifie aucun endpoint. | `OBSERVED` | 85 tests et 14 sous-tests passent ; `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, listing/traversal, lecture indirecte d’asset, fetch, bundle, policy et MCP restent absents. | `LOG-0027` |
| `MEM-STATE-015` | Bounded Knowledge-Asset Index M2.9 | Le Core liste directement, dans un ordre déterministe et une borne explicite, les seules métadonnées de liaisons d’une knowledge ou d’un asset existants ; aucun endpoint n’est lu ni modifié. | `OBSERVED` | 90 tests et 14 sous-tests passent ; `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, recherche libre, traversal, lecture indirecte d’asset, fetch, bundle, policy et MCP restent absents. | `LOG-0030` |
| `MEM-STATE-016` | Asset Source Registry M2.10 | Le Core attache/lit/liste des références documentaires immuables, hashées et bornées par lignes à un asset existant, sans ouvrir le document ni comparer son hash au contenu d’asset. | `OBSERVED` | 96 tests et 14 sous-tests passent ; `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, traversal, lecture d’asset, fetch, comparaison, bundle, policy et MCP restent absents. | `LOG-0033` |
| `MEM-STATE-017` | Bounded Knowledge-Source Hash Index M2.11 | Le Core liste, dans un ordre déterministe et une borne explicite, les références `knowledge_source` partageant un hash déclaré exact ; ni knowledge cible ni document n’est lu. | `OBSERVED` | 100 tests et 14 sous-tests passent ; `PROVEN`, evidence/proof, admission, validator, execution, gate, relation générique, traversal, `KnowledgeService.get`, fetch, comparaison, bundle, policy et MCP restent absents. Le candidat d’index d’assets M2.11 a été rejeté comme redondant. | `LOG-0036`, `LOG-0038` |

## 5. Décisions actives

| ID | Décision | Statut | Motif | Effet opérationnel | Journal |
|---|---|---|---|---|---|
| `MEM-DEC-001` | Créer VERA-MMU dans un dépôt indépendant sans modifier ARET-MMU. | `DECISION` | Préserver le dépôt de référence et rendre les frontières mesurables. | Toute réutilisation future passe par migration, import explicite ou pack ; aucune copie non tracée. | `LOG-0002` |
| `MEM-DEC-002` | Utiliser `vera://` comme schéma de ressource canonique et conserver `ARET://` seulement en lecture de compatibilité ultérieure. | `DECISION` | Différencier le nouveau Core tout en préservant une voie de migration contrôlée. | Tests de round-trip et lecteur V1 requis avant tout claim de compatibilité. | `LOG-0002` |
| `MEM-DEC-003` | Utiliser ces trois documents comme système de continuité de transition. | `DECISION` | Le store universel n’existe pas encore, mais le chantier exige mémoire, provenance et reprise dès maintenant. | Chaque lot met à jour plan, mémoire et journal avant son commit atomique. | `LOG-0003` |
| `MEM-DEC-004` | Commencer par `M0.1 — Freeze ARET` plutôt que par une extraction de code. | `DECISION` | Toute parité future requiert un baseline mesuré de schéma, tests, hooks, MCP, bundle et dépendances. | Aucun déplacement de primitive ARET avant l’inventaire de compatibilité. | `LOG-0003` |
| `MEM-DEC-005` | Démarrer M1 par les couplages C01, C02 et C11 : adressage VERA, Project Profile/runtime configurable et workspace sûr. | `DECISION` | Ces primitives rendent possible la persistance, les packs et la compilation ultérieurs sans introduire de dépendance ARET dans le Core. | Le premier patch M1 ne doit importer aucun module ARET ni connaître `ARET://`, `.aret-memory`, binaire ou toolchain ARET. | `LOG-0007` |
| `MEM-DEC-006` | Le catalogue initial d’adresses est strictement générique et fermé ; aucune forme d’adresse historique n’est interprétée par le Core. | `DECISION` | Préserver I014/I015 et éviter un renommage cosmétique ou une compatibilité implicite. | `parse_address` accepte exclusivement les URI canoniques `vera://<project>/<resource>/<id>` ; un lecteur historique éventuel est hors M1. | `LOG-0009` |
| `MEM-DEC-007` | Commencer M2 par un substrate SQLite sans objets métier : migrations checksumées, identité de store, audit technique et transactions bornées. | `DECISION` | Établir I001/I010/I011/I014 avant les connaissances, entités, evidence ou bundles. | M2.1 exclut toute taxonomie, migration de données ARET, commande, capability, MCP, pack et compatibilité historique. | `LOG-0010` |
| `MEM-DEC-008` | M2.2 introduit uniquement un registre de types d’entité et des entités génériques créées/lues de façon exacte et auditée. | `DECISION` | Commencer C03 sans emprunter les tables `component`/`function_symbol` ni ouvrir C04/C05/C16 au-delà du nécessaire. | Les entités exigent un type enregistré ; l’API exclut FIND, relations, symboles, knowledge, evidence et toute compatibilité ARET. | `LOG-0012` |
| `MEM-DEC-009` | M2.3 introduit uniquement un registre de types de relation et des arêtes immuables entre entités existantes. | `DECISION` | Établir une relation universelle et typée sans ouvrir le traversal, la supersession, le graphe de travail ou la connaissance. | Les types de relation sont déclaratifs et contraignent les types d’entité ; l’API exclut FIND, lifecycle, relation vers d’autres ressources, knowledge, evidence et toute compatibilité ARET. | `LOG-0014` |
| `MEM-DEC-010` | M2.4 introduit uniquement un registre knowledge append-only avec types déclaratifs, hash de contenu et statuts épistémiques initiaux sûrs. | `DECISION` | Établir I003 et empêcher une promotion sans evidence avant de créer le moteur d’Evidence. | `PROVEN`, supersession, FTS/FIND, tags, sources, relations et toute mutation sont exclus ; les écritures sont append-only, auditables et liées au profile. | `LOG-0016` |
| `MEM-DEC-011` | M2.5 introduit uniquement des références documentaires immuables, hashées et bornées par lignes, attachées à une knowledge existante. | `DECISION` | Établir la provenance déclarative sans créer de fetch, importeur, preuve ou admission `PROVEN`. | Les sources sont validées comme données de référence ; l’API exclut lecture de fichier, vérification de contenu, import, migration batch, evidence et toute mutation/suppression. | `LOG-0018` |
| `MEM-DEC-012` | M2.6 introduit uniquement une relation de supersession immuable entre deux knowledge déjà appendées. | `DECISION` | Rendre le remplacement explicitement traçable sans réécrire contenu, statut, métadonnées, provenance ou hash de la connaissance remplacée. | Un prédécesseur a au plus un successeur ; les cycles et self-links sont interdits ; l’API exclut mutation de statut, traversal, version counter, evidence, `PROVEN` et toute compatibilité ARET. | `LOG-0020` |
| `MEM-DEC-013` | M2.7 introduit uniquement un registre d’assets binaires contenus dans SQLite, append-only et hashés avant lecture. | `DECISION` | Établir I005 sans ouvrir le filesystem client, une exécution, une preuve, une admission `PROVEN` ou une policy. | Les assets sont des objets Core génériques ; l’API exclut chemin/fichier externe, réseau, import/export, bundle, listing, relation, mutation/suppression, execution, evidence/proof et vocabulaire ARET. | `LOG-0023` |
| `MEM-DEC-014` | M2.8 introduit uniquement une association immutable entre une knowledge existante et un asset existant. | `DECISION` | Rendre la référence de contenu explicite sans convertir une association en evidence, preuve, résultat ou promotion `PROVEN`. | Le sidecar impose l’existence des deux endpoints et l’unicité de paire ; l’API exclut lecture asset par le lien, listing/traversal, relation générique, status mutation, execution, validator, gate, evidence/proof et vocabulaire ARET. | `LOG-0026` |
| `MEM-DEC-015` | M2.9 introduit uniquement l’index direct, ordonné et borné des associations knowledge–asset pour un endpoint exact. | `DECISION` | Rendre une association déjà persistée découvrable sans renvoyer le contenu canonique, sans recherche libre, sans traversal ni effet de preuve. | Les listes ne retournent que des objets de liaison, exigent un endpoint existant et une limite valide ; l’API exclut contenu, `AssetService.read`, graph traversal, filtre libre, status mutation, evidence/proof, execution, validator, gate et vocabulaire ARET. | `LOG-0029` |
| `MEM-DEC-016` | M2.10 introduit uniquement une provenance documentaire déclarative immutable pour un asset existant. | `DECISION` | Rendre l’origine déclarée d’un contenu explicite sans ouvrir le document, comparer son hash à l’asset, ni qualifier l’asset de preuve ou promotion `PROVEN`. | Le sidecar impose l’existence de l’asset et l’unicité de slice ; l’API exclut lecture/fetch/import, comparaison de hashes, `AssetService.read`, evidence/proof, admission, execution, validator, gate, traversal et vocabulaire ARET. | `LOG-0032` |
| `MEM-DEC-017` | Candidat initial M2.11 d’index d’assets par SHA-256. | `REJECTED` | Le schéma M2.7 impose déjà `content_hash UNIQUE`; une liste multi-résultats par hash serait redondante et ne produit aucune nouvelle capacité. | Aucun patch de production n’est retenu ; le test exploratoire est supprimé. Ne pas présenter ce candidat comme livré. | `LOG-0035`, `LOG-0036` |
| `MEM-DEC-018` | M2.11 introduit uniquement un index exact, ordonné et borné des références `knowledge_source` par SHA-256 déclaré. | `DECISION` | Rendre un même hash de source déclarée découvrable sans lire les knowledge cibles, ouvrir un document, rechercher par texte ou convertir la référence en preuve. | L’API exige un hash complet valide et une limite valide, retourne seulement `KnowledgeSource` sans contenu knowledge, et exclut `KnowledgeService.get`, préfixe/substring, mutation, fetch, evidence/proof, execution, validator, gate et vocabulaire ARET. | `LOG-0037` |

## 6. Risques, incertitudes et blocages

| ID | Risque ou inconnue | Statut | Impact | Réponse requise | Journal |
|---|---|---|---|---|---|
| `MEM-RISK-001` | Les assertions de parité ARET ne disposent pas encore d’un baseline reproductible complet dans VERA-MMU. | `RISK` | Une migration pourrait sembler fonctionnelle sans être démontrée équivalente. | Exécuter `M0.1`, capturer résultats, versions, schéma, hooks, bundle et écarts d’environnement. | `LOG-0003` |
| `MEM-RISK-002` | La spécification cible utilise historiquement `mmu://`, `.mmu/` et `mmu_*`, tandis que VERA-MMU a choisi `vera://`, `.vera-mmu/` et `vera_*`. | `DECISION` avec risque de compatibilité | Les documents et adaptations doivent déclarer les deux couches sans mélange silencieux. | Définir une table de compatibilité et une policy d’alias dans `M1`. | `LOG-0003` |
| `MEM-RISK-003` | Le statut de licence est `LICENSE-PENDING`. | `RISK` | Une extraction ou distribution de code ARET nécessite une décision explicite de gouvernance. | Ne pas copier de code ARET ; documenter provenance, droits et transformation avant tout import. | `LOG-0002` |
| `MEM-RISK-004` | Les règles de preuve sont documentées, mais le mécanisme de capture admissible VERA-MMU n’est pas encore implémenté. | `RISK` | Les preuves actuelles de chantier sont des traces de développement, pas des evidence VERA-MMU admissibles. | Qualifier les résultats `OBSERVED` jusqu’à l’existence du store/evidence engine. | `LOG-0003` |
| `MEM-WALL-001` | Toolchain ARET de baseline incomplète | La suite complète produit 82 passes, 1 échec et 7 skips ; `gcc`, Cargo, Wine, MinGW, Clang, LLD et LLVM DLLTool sont absents, ainsi que le binaire et le script réels de difftest. | `BLOCKED` | `ARET_MMU_M0_1_BASELINE/tests/pytest_full.txt` ; `toolchain/oracle_toolchain_availability.txt`. | Ne pas modifier ARET-MMU ni qualifier les oracles comme validés ; reproduire ultérieurement dans un environnement déclarant cette toolchain. | `LOG-0006` |

## 7. Reprise active

**État de reprise :** `M2.11 — Bounded Knowledge-Source Hash Index` a atteint son verdict technique `PASS` dans `LOG-0038` et est publié au commit `34d9c2595ab93c1e041c88fb213451b2b1794929`, vérifié par `LOG-0039`. Le rejet documenté du candidat asset redondant (`LOG-0036`) demeure une contrainte de reprise. Le prochain sous-lot n’est pas ouvert : il exige un nouveau rituel d’hypothèse. `MEM-WALL-001` demeure une précondition ouverte pour les futures assertions d’oracle et de capability ARET.

| Élément | Valeur de reprise |
|---|---|
| État vérifié | C01/C02/C11 disposent de primitives génériques testées : URI VERA canonique, profile/identités hashés, roots contrôlées, no-Git, multi-repo, détection VCS sans appel Git et runtime confiné. M1 est publié au commit `c48efc4ec824a9ec5b1a3742f7022636e9ef082b`. |
| Evidence M1 | `PYTHONPATH=src python3 -m pytest -q` : 21 passés, 14 sous-tests ; build/install wheel et `vmmu inspect` réussis ; `git diff --check` et scan anti-ARET réussis. Hash wheel : `92078ad9018f0a26d5b6999fcfe25f32dd6ca1699b6b49c501b7bc12c8f13e1e`. |
| Baseline M2.1 | Store SQLite canonique, migration checksumée, métadonnées, identité de store, audit technique et transaction, publié au commit `3fc41eff3fb525bab82338287ddde33b3dce9358`. |
| Baseline M2.2 | Registre de types d’entité, entités génériques, JSON canonique, lecture exacte, audit de création et migration M2.1→M2.2, publié au commit `8f367ca5fdf906f48a58e739360af97d1649c40a`. |
| Baseline M2.3 | Registre de types de relation, arêtes immuables entre entités, contraintes déclaratives source/cible, lecture exacte, audit de création et migration M2.2→M2.3, publié au commit `5e68a9694137dd1e49f6a8b4a1700c7ca2e40764`. |
| Baseline M2.4 | Registre knowledge, assertions append-only hashées, statuts initiaux sûrs, lecture exacte, audit de création et migration M2.3→M2.4, publié au commit `a783d3efefafe0b1e80c5454e8649f082858611e`. |
| Baseline M2.5 | Références documentaires à une knowledge existante : repository, revision, chemin relatif, section, lignes, SHA-256, lecture exacte bornée, audit de création et migration M2.4→M2.5, publié au commit `fc34cccf867c3044203085ca1618b9095c2cfa44`. |
| Baseline M2.6 | Supersession directe immutable entre knowledge existantes : unicité de prédécesseur/successeur, anti-cycle, lecture exacte dans les deux sens et audit de création, avec migration M2.5→M2.6. Verdict technique `PASS` dans `LOG-0021`, publié au commit `e6afb43e1f840cbf5c909f6522d65c351ae62411` et vérifié dans `LOG-0022`. |
| Baseline M2.7 | Registre d’assets binaires stockés dans SQLite : identifiant VERA `asset`, SHA-256, taille, media type, lecture exacte vérifiant le hash et audit atomique, avec migration M2.6→M2.7. Verdict technique `PASS` dans `LOG-0024`, publié au commit `f4b878061dfaa1dd4f22b6b6f21a18f49ec5a1f8` et vérifié dans `LOG-0025`. |
| Baseline M2.8 | Sidecar `knowledge_asset_link` immutable entre une knowledge et un asset existants : lecture d’une paire exacte, unicité de paire et audit atomique, avec migration M2.7→M2.8. Aucun contenu de l’asset n’est lu par ce lien, qui n’est pas une evidence. Verdict technique `PASS` dans `LOG-0027`, publié au commit `8982b7855e09db8ed009ca2081021b9210bc8088` et vérifié dans `LOG-0028`. |
| Baseline M2.9 | Index direct, ordonné et borné de liaisons knowledge–asset pour une knowledge ou un asset exacts, avec migration M2.8→M2.9. Les résultats ne contiennent que les métadonnées de liaison ; aucun contenu d’endpoint n’est lu ou exposé. Verdict technique `PASS` dans `LOG-0030`, publié au commit `c888958cc184c621b5cf02b95defa0d3fb706b56` et vérifié dans `LOG-0031`. |
| Baseline M2.10 | Sidecar `asset_source` immutable attachant à un asset existant repository, revision, chemin relatif, section, lignes et hash de source, avec migration M2.9→M2.10. Les références restent déclaratives et ne sont ni ouvertes ni comparées au contenu de l’asset. Verdict technique `PASS` dans `LOG-0033`, publié au commit `e568cd5fe8bda80b4d9434836a9173ad0195d9f0` et vérifié dans `LOG-0034`. |
| Baseline M2.11 | Index direct, ordonné et borné de références `knowledge_source` pour un SHA-256 déclaré complet exact, avec migration M2.10→M2.11. Les résultats sont des métadonnées déclaratives et ne lisent ni knowledge ni document. Le candidat initial d’index d’assets a été rejeté comme redondant. Verdict technique `PASS` dans `LOG-0038`, publié au commit `34d9c2595ab93c1e041c88fb213451b2b1794929` et vérifié dans `LOG-0039`. |
| Limites explicites | Pas encore de fetch/vérification de document, import/migration batch, mutation de statut/supersession complète, promotion `PROVEN`, evidence, traversal/lifecycle relationnel, symbole, FTS/FIND, policy, capability, bundle, adapter MCP, dashboard, pack ARET ni compatibilité de lecteur historique. L’absence de vocabulaire ARET du Core ne démontre pas de parité comportementale ARET. |
| Entrées à relire | [Plan](UNIVERSALIZATION_WORKPLAN.md), cette mémoire, [journal](ENGINEERING_LOG.md), [invariants](../INVARIANTS.md), [matrice](../DECOUPLING_MATRIX.md), puis `LOG-0036`, `LOG-0038` et `LOG-0039`. |
| Prochaine action | Ne pas ouvrir M2.12 sans nouveau rituel d’hypothèse explicitement borné ; vérifier d’abord les limites résiduelles, le rejet `LOG-0036` et `MEM-WALL-001`. |

## 8. Protocole de mise à jour append-only

1. Créer une nouvelle entrée avec un identifiant monotone `MEM-…` ; ne pas modifier un record historique sauf correction de forme ne changeant pas le sens.
2. En cas de correction sémantique, ajouter `SUPERSEDES: MEM-…`, citer la source nouvelle et expliquer le motif.
3. Associer chaque record à un ou plusieurs identifiants `LOG-…` du journal.
4. N’utiliser `PROVEN` que lorsqu’une evidence admissible du futur moteur existe ; dans la phase documentaire, préférer `OBSERVED`, `DECISION` ou `HYPOTHESIS`.
5. Mettre à jour la section **Reprise active** à la fin de chaque lot ou avant compaction.

## Références

[1]: https://github.com/aciderix/ARET-MMU "ARET-MMU — dépôt de référence"

## 9. Addendum de reprise — cadrage terminal M2

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-DEC-019` | Frontière M2/M3 | M2 est désormais borné par le contrat **Universal Schema** de la spécification : entity registry, relation registry, symbol, work item, execution et capability registry. Les deux premiers sont livrés ; les quatre derniers doivent être fermés par trois macro-lots cohérents, puis une gate terminale. Le nombre de micro-lots n’est plus un critère de progression. | `DECISION` | Spécification fournie, §8, §10, §12, §14 et §55 ; [workplan](UNIVERSALIZATION_WORKPLAN.md). | `LOG-0040` |
| `MEM-DEC-020` | Limite épistémique | Une `execution` est le fait persistant qu’une action s’est produite ; elle n’est ni une proof ni une evidence admissible. L’Evidence Store, HMAC, validators, runners, gates, policy, admission et la promotion `PROVEN` sont explicitement différés à M3. | `DECISION` | Spécification fournie, §11–15 ; invariants I004, I006–I008, I013. | `LOG-0040` |
| `MEM-DEC-021` | Anti-redondance | Aucun ajout M2 ne peut être admis s’il ne ferme pas une ressource du contrat Universal Schema, une contrainte d’intégrité nécessaire à cette ressource, ou une dépendance strictement démontrée de M3. Le rejet de l’index asset par hash (`MEM-DEC-017`) est le précédent contrôlant de cette règle. | `DECISION` | `MEM-DEC-017`, `LOG-0036`, `LOG-0040`. | `LOG-0040` |
| `MEM-STATE-018` | Reprise active | Après M2.11, aucun patch M2.12 n’est ouvert. La prochaine action technique, seulement après publication de ce cadrage, est une hypothèse autonome pour le macro-lot `M2.12 — Symbol Registry`. La baseline ARET exhaustive reste `UNKNOWN` sous `MEM-WALL-001` et ne peut être requalifiée par la gate M2. | `OBSERVED` | État de dépôt avant cadrage et décision de feuille de route. | `LOG-0039`, `LOG-0040` |

> **Reprise prioritaire.** Lire `MEM-DEC-019` à `MEM-DEC-021`, puis `LOG-0040`, avant toute proposition de code M2. Les exclusions M3 sont des limites de périmètre, non des fonctionnalités implicites ou partielles.

## 10. Addendum de reprise — résultat M2.12

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-019` | Symbol Registry M2.12 | `SUPERSEDES: MEM-STATE-018` pour la reprise active. Le Core expose `SymbolService` et `Symbol` pour créer/lire exactement des symboles déclaratifs immuables liés par FK à une entity existante. Chaque record contient `kind`, locator `path`, identifiant, signature, metadata JSON canonique, URI `vera://…/symbol/…` et audit atomique. L’unicité `(entity_id, path, identifier)` et les triggers SQLite refusent duplication sémantique, UPDATE et DELETE. | `OBSERVED` | Migration `012_symbol_registry.sql`, `symbols.py`, `tests/test_symbols.py`; validation M2.12. | `LOG-0041`, `LOG-0042` |
| `MEM-DEC-022` | Limite M2.12 | Le `path` de symbole est un locator déclaratif canonique : il n’est jamais ouvert, résolu, scanné ni interprété comme chemin de fichier. Un symbole ne confère ni relation automatique, ni evidence, ni execution, ni admission `PROVEN`. | `DECISION` | Invariants I001, I002, I003, I011, I014, I015 ; contrat M2.12. | `LOG-0041`, `LOG-0042` |
| `MEM-STATE-020` | Prochaine reprise | Après M2.12, le prochain macro-lot est `M2.13 — Work-Item Backbone`; il exige sa propre baseline et hypothèse. `MEM-WALL-001` demeure `BLOCKED`, et la parité ARET exhaustive demeure `UNKNOWN`. | `OBSERVED` | Gate M2.12 passée sous limites documentées. | `LOG-0042` |

## 11. Addendum de reprise — résultat M2.13

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-021` | Work-Item Backbone M2.13 | `SUPERSEDES: MEM-STATE-020` pour la reprise active. Le Core expose `WorkItemService` et `WorkItem` pour créer/lire exactement des unités de travail immuables de type fermé, au statut initial `PLANNED`, avec parent optionnel préexistant, priorité/assignee déclaratifs, metadata JSON, URI `vera://…/work-item/…` et audit atomique. Les triggers SQLite refusent UPDATE et DELETE. | `OBSERVED` | Migration `013_work_item_registry.sql`, `work_items.py`, `tests/test_work_items.py`; validation M2.13. | `LOG-0044`, `LOG-0045` |
| `MEM-DEC-023` | Limite M2.13 | Le parent structure un enregistrement existant mais n’induit ni traversal, ni dépendance, ni transition. `PLANNED` est le seul statut M2.13 et `updated_at` reste identique à `created_at`; aucune assignation active, `DONE`, Front, resume, gate, execution ou preuve n’est introduite. | `DECISION` | Invariants I001, I002, I003, I009, I011, I014, I015 ; contrat M2.13. | `LOG-0044`, `LOG-0045` |
| `MEM-STATE-022` | Prochaine reprise | Après M2.13, le prochain macro-lot est `M2.14 — Capability Declaration & Execution Schema`; il exige sa propre baseline et hypothèse. `MEM-WALL-001` demeure `BLOCKED`, et la parité ARET exhaustive demeure `UNKNOWN`. | `OBSERVED` | Gate M2.13 passée sous limites documentées. | `LOG-0045` |

## 12. Addendum de reprise — résultat M2.14

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-023` | Capability / Execution Schema M2.14 | `SUPERSEDES: MEM-STATE-022` pour la reprise active. Le Core expose `CapabilityService` pour déclarer/lire exactement des capabilities immuables, typées et versionnées avec schémas JSON. Il possède aussi une table `execution` sous FK capability, append-only et non exposée par service M2. | `OBSERVED` | Migration `014_capability_execution_schema.sql`, `capabilities.py`, `tests/test_capabilities.py`. | `LOG-0047`, `LOG-0048` |
| `MEM-DEC-024` | Limite M2.14 | Une capability M2 ne contient ni runner, commande, policy, réseau, timeout, validator, artefact ni secret. Une execution M2 n’est ni produite/lue opérationnellement ni une proof; M3 seul pourra ajouter runner, validator, Evidence Store, admission et `PROVEN`. | `DECISION` | Invariants I004, I006–I008, I013–I015 ; contrat M2.14. | `LOG-0047`, `LOG-0048` |

## 13. Addendum terminal — M2.EXIT

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-024` | Gate M2.EXIT | `SUPERSEDES: MEM-STATE-023` pour la reprise active. Le contrat **Universal Schema M2** est passé : migrations 001–014, substrat/audit, entités/relations, knowledge/assets, symboles, work items, capabilities déclaratives et structure execution ont été validés. | `OBSERVED` | Upgrade indépendant 001→014, suite 126 tests + 14 sous-tests, roue isolée M2.14 et scans M2. | `LOG-0049` |
| `MEM-DEC-025` | Frontière terminale M2 | M2.EXIT ne valide ni runner, ni validator, ni Evidence Store, ni admission, ni HMAC, ni `PROVEN`, ni gate, ni work graph. Ces capacités restent exclusivement M3; une execution n’est pas une proof. | `DECISION` | Invariants I004, I006–I008, I013–I015. | `LOG-0049` |
| `MEM-WALL-001` | Baseline ARET | Statut inchangé : l’exécution exhaustive/parité ARET reste `UNKNOWN` à cause de la toolchain et des oracles absents; M2.EXIT ne convertit aucun `UNKNOWN`/`SKIPPED` en `PASS`. | `BLOCKED` | Baseline M0.1. | `LOG-0006`, `LOG-0049` |


## 14. Addendum de reprise — tranche opérationnelle M3.1–M3.6

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-025` | Tranche M3 livrée | `SUPERSEDES: MEM-STATE-024` pour la reprise active. Les migrations 015–019 fournissent des contrats de capability fermés, le seul runner `NOOP` sans réseau, une execution immutable, une evidence JSON hashée liée à cette execution, une décision d’admission immutable, une preuve dérivée `PROVEN` sans réécriture de knowledge, et des dépendances directes/gates de work items fondées sur une admission existante. | `OBSERVED` | Commits publiés M3.1–M3.6; tests terminaux : 139 tests et 14 sous-tests `PASS`; wheel isolé et upgrade 001→019 vérifiés. | `LOG-0051`, `LOG-0055`, `LOG-0058`, `LOG-0061`, `LOG-0067`, `LOG-0069` |
| `MEM-DEC-026` | Portée de gate | La gate `M3.S1.EXIT` ne peut valider que la **tranche verticale opérationnelle minimale** décrite par `MEM-STATE-025`. Elle exige les migrations 001→019, la suite complète, une distribution isolée, la frontière execution≠evidence≠preuve, l’absence de shell arbitraire/réseau implicite et l’immutabilité d’ARET. Elle ne constitue ni une clôture de M3 global, ni une validation de parité ARET. | `DECISION` | Invariants I004–I008, I013–I015; contrôles terminaux M3. | `LOG-0070` |
| `MEM-STATE-026` | Reprise active | M3 reste `IN_PROGRESS` après `M3.S1.EXIT`. Restent explicitement hors tranche : validation typée complète du schema de paramètres, catalogue de décisions `ALLOW`/`DENY`/`CONFIRM`, runners sûrs additionnels, framework de validators, policy HMAC de projet, gates multi-evidence, traversal/lifecycle de work graph, CLI/MCP et tout pack ARET. | `OBSERVED` | Revue de portée après M3.6; aucun test ou contrat de ces capacités n’est livré. | `LOG-0070` |
| `MEM-WALL-001` | Baseline ARET | Statut inchangé : les oracles et la toolchain ARET manquants maintiennent la parité/exécution exhaustive ARET à `UNKNOWN`. Les contrôles de non-modification d’ARET ne créent aucune preuve de parité. | `BLOCKED` | Baseline M0.1 et contrôle Git terminal M3. | `LOG-0006`, `LOG-0070` |

> **Reprise prioritaire.** Relire `MEM-STATE-025`, `MEM-DEC-026`, `MEM-STATE-026`, `MEM-WALL-001`, puis `LOG-0070` avant tout lot M3 ultérieur. Le prochain patch doit choisir un seul manque explicite de `MEM-STATE-026` avec une hypothèse et une gate propres.


## 15. Addendum de reprise — M3.7 validation de paramètres

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-027` | Validation de paramètres | `SUPERSEDES: MEM-STATE-026` pour cette exclusion précise. Les contrats de capability acceptent désormais un sous-ensemble fermé : root `object`, propriétés scalaires, `required` et `additionalProperties`. Le runner `NOOP` valide les paramètres avant toute insertion d’execution; les erreurs ne créent ni execution ni audit. | `OBSERVED` | `parameter_validation.py`, `capability_contracts.py`, `executions.py`, tests M3.7; 141 tests et 14 sous-tests, wheel isolé. | `LOG-0072`, `LOG-0073` |
| `MEM-DEC-027` | Frontière M3.7 | Le sous-ensemble de paramètres n’est pas un moteur JSON Schema général : `enum`, array, object imbriqué, callbacks, imports dynamiques et validators externes restent exclus. Ce refus de généralité conserve une validation déterministe, locale et sans capacité d’exécution. | `DECISION` | Contrat M3.7 et invariants I006–I008, I013–I015. | `LOG-0072`, `LOG-0073` |
| `MEM-STATE-028` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : catalogue de décisions `ALLOW`/`DENY`/`CONFIRM`, framework de validators, runners sûrs additionnels, policy HMAC de projet, gates multi-evidence, lifecycle/traversal de work graph, CLI/MCP et pack ARET. La validation des paramètres n’est plus une exclusion ouverte. | `OBSERVED` | Revue post-M3.7; aucun contrat ou test de ces capacités n’est livré. | `LOG-0073` |

> **Reprise prioritaire.** Relire `MEM-STATE-027`, `MEM-DEC-027`, `MEM-STATE-028`, `MEM-WALL-001`, puis `LOG-0072`–`LOG-0073` avant tout lot M3 ultérieur.


## 16. Addendum de reprise — M3.8 policy explicite

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-029` | Policy d’exécution | `SUPERSEDES: MEM-STATE-028` pour cette exclusion précise. Une policy immutable liée à une capability porte une décision fermée `ALLOW`/`DENY`/`CONFIRM`, un motif et un audit. Le runner `NOOP` exige `ALLOW` avant validation des paramètres ou insertion d’execution; absence, `DENY` et `CONFIRM` refusent sans effet de runner. | `OBSERVED` | Migration `020_capability_policies.sql`, `capability_policies.py`, `executions.py`, tests M3.8; 143 tests et 14 sous-tests, wheel isolé. | `LOG-0075`, `LOG-0076` |
| `MEM-DEC-028` | Frontière de confirmation | `CONFIRM` est un refus persistant et explicite, non une autorisation différée. Aucun flux interactif, override, expiration, révision ou changement de policy n’est déduit de cette décision append-only. | `DECISION` | Contrat M3.8 et invariants I007, I008, I013–I015. | `LOG-0075`, `LOG-0076` |
| `MEM-STATE-030` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : framework de validators, runners sûrs additionnels, policy HMAC de projet, gates multi-evidence, lifecycle/traversal de work graph, CLI/MCP et pack ARET. `ALLOW`/`DENY`/`CONFIRM` fermés sont livrés, mais la confirmation interactive et la mutabilité de policy ne le sont pas. | `OBSERVED` | Revue post-M3.8; aucun contrat ou test de ces capacités n’est livré. | `LOG-0076` |

> **Reprise prioritaire.** Relire `MEM-STATE-029`, `MEM-DEC-028`, `MEM-STATE-030`, `MEM-WALL-001`, puis `LOG-0075`–`LOG-0076` avant tout lot M3 ultérieur.


## 17. Addendum de reprise — M3.9 policy HMAC de projet

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-031` | Policy de preuve | `SUPERSEDES: MEM-STATE-030` pour cette exclusion précise. Une policy singleton immutable de projet déclare `HMAC_SHA256` et `hmac_required`, sans secret. Toute preuve dérivée exige cette policy; lorsqu’elle requiert HMAC, le secret bytes demeure en mémoire et seul le digest est persisté. | `OBSERVED` | Migration `021_proof_policies.sql`, `proof_policies.py`, `proofs.py`, tests M3.9; 146 tests et 14 sous-tests, wheel isolé. | `LOG-0078`, `LOG-0079` |
| `MEM-DEC-029` | Secret HMAC | L’absence de policy, un secret manquant lorsque requis, ou un secret fourni lorsque non requis sont des erreurs fail-loud. La policy, les audits et les records de preuve ne portent aucun secret, encodage, hint ou longueur de secret. | `DECISION` | Contrat M3.9 et invariants I004, I006–I008, I013–I015. | `LOG-0078`, `LOG-0079` |
| `MEM-STATE-032` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : framework de validators, runners sûrs additionnels, gates multi-evidence, lifecycle/traversal de work graph, CLI/MCP et pack ARET. La rotation/révocation/expiration de secret et les algorithmes alternatifs restent hors M3.9. | `OBSERVED` | Revue post-M3.9; aucun contrat ou test de ces capacités n’est livré. | `LOG-0079` |

> **Reprise prioritaire.** Relire `MEM-STATE-031`, `MEM-DEC-029`, `MEM-STATE-032`, `MEM-WALL-001`, puis `LOG-0078`–`LOG-0079` avant tout lot M3 ultérieur.


## 18. Addendum de reprise — M3.10 validator d’intégrité

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-033` | Validation locale | `SUPERSEDES: MEM-STATE-032` pour cette exclusion précise. Un registre immutable contient uniquement `EVIDENCE_HASH`; un résultat append-only compare le hash stocké d’une evidence avec SHA-256 de son JSON canonique et produit `PASS` ou `FAIL`. Le résultat ne modifie ni evidence, ni admission, ni knowledge. | `OBSERVED` | Migration `022_validators.sql`, `validators.py`, tests M3.10; 148 tests et 14 sous-tests, wheel isolé. | `LOG-0081`, `LOG-0082` |
| `MEM-DEC-030` | Frontière validator | Un verdict de validator est un fait d’intégrité local, non une admission, une preuve, une promotion ou une autorisation d’execution. Un seul résultat par `(validator, evidence)` est admis afin d’empêcher les répétitions ambiguës. | `DECISION` | Contrat M3.10 et invariants I004–I008, I013–I015. | `LOG-0081`, `LOG-0082` |
| `MEM-STATE-034` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : validators de contenu explicitement bornés, runners sûrs additionnels, gates multi-evidence, lifecycle/traversal de work graph, CLI/MCP et pack ARET. Aucun oracle externe, fichier, URL ou réseau n’est livré par M3.10. | `OBSERVED` | Revue post-M3.10; aucun contrat ou test de ces capacités n’est livré. | `LOG-0082` |

> **Reprise prioritaire.** Relire `MEM-STATE-033`, `MEM-DEC-030`, `MEM-STATE-034`, `MEM-WALL-001`, puis `LOG-0081`–`LOG-0082` avant tout lot M3 ultérieur.


## 19. Addendum de reprise — M3.11 gates multi-evidence

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-035` | Gates d’admission | `SUPERSEDES: MEM-STATE-034` pour cette exclusion précise. Une gate conserve son evidence principale et peut recevoir des exigences additionnelles append-only. Son évaluation pure retourne `PASS` seulement si chaque evidence requise a une admission `ADMITTED`; sinon elle retourne `FAIL`. | `OBSERVED` | Migration `023_multi_evidence_gates.sql`, `gates.py`, tests M3.11; 149 tests et 14 sous-tests, wheel isolé. | `LOG-0084`, `LOG-0085` |
| `MEM-DEC-031` | Sémantique de gate | Les exigences M3.11 forment une conjonction fixe. Une gate ne lance rien, ne crée aucune evidence ou admission, ne modifie aucun work item ou knowledge, et ne devient ni un quorum ni un lifecycle. | `DECISION` | Contrat M3.11 et invariants I004–I008, I013–I015. | `LOG-0084`, `LOG-0085` |
| `MEM-STATE-036` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : validators de contenu explicitement bornés, runners sûrs additionnels, lifecycle/traversal de work graph, politiques/gates plus riches sous lot séparé, CLI/MCP et pack ARET. Aucun oracle externe, fichier, URL, réseau ou shell n’est livré par M3.11. | `OBSERVED` | Revue post-M3.11; aucun contrat ou test de ces capacités n’est livré. | `LOG-0085` |

> **Reprise prioritaire.** Relire `MEM-STATE-035`, `MEM-DEC-031`, `MEM-STATE-036`, `MEM-WALL-001`, puis `LOG-0084`–`LOG-0085` avant tout lot M3 ultérieur.


## 20. Addendum de reprise — M3.12 lifecycle dérivé

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-037` | Lifecycle de work item | `SUPERSEDES: MEM-STATE-036` pour cette exclusion précise. Des événements append-only `START`/`COMPLETE`/`CANCEL` dérivent l’état `PLANNED`/`ACTIVE`/`COMPLETED`/`CANCELLED`; `work_item.status` reste historiquement `PLANNED`. | `OBSERVED` | Migration `024_work_lifecycle.sql`, `work_lifecycle.py`, tests M3.12; 151 tests et 14 sous-tests, wheel isolé. | `LOG-0087`, `LOG-0088` |
| `MEM-DEC-032` | Frontière lifecycle | Une transition de lifecycle est un fait de travail, non une execution, admission, preuve, promotion `PROVEN` ou validation de gate. Les transitions sont fermées et terminales; l’état et l’historique sont lus sans effet. | `DECISION` | Contrat M3.12 et invariants I004–I008, I013–I015. | `LOG-0087`, `LOG-0088` |
| `MEM-STATE-038` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : validator de contenu explicitement borné, runners sûrs additionnels, politiques/gates avancées sous lot séparé, CLI/MCP et pack ARET. Pause/reprise, réouverture, propagation et orchestration de lifecycle restent hors M3.12. | `OBSERVED` | Revue post-M3.12; aucun contrat ou test de ces capacités n’est livré. | `LOG-0088` |

> **Reprise prioritaire.** Relire `MEM-STATE-037`, `MEM-DEC-032`, `MEM-STATE-038`, `MEM-WALL-001`, puis `LOG-0087`–`LOG-0088` avant tout lot M3 ultérieur.


## 21. Gate de tranche — M3.S2

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-039` | Gate M3.S2 | La tranche M3.S2 couvre M3.7–M3.12 : paramètres fermés, policies de capability et de preuve, validator local, gate conjonctive multi-evidence et lifecycle dérivé. Son intégration isolée migrations 001→024 est validée. | `OBSERVED` | Wheel isolé, profil neuf et chaîne complète; 151 tests et 14 sous-tests. | `LOG-0090` |
| `MEM-DEC-033` | Signification de sortie | `M3.S2.EXIT = PASS` signifie uniquement que la tranche M3.7–M3.12 est intégrée et validée. Il ne signifie ni M3 global terminé, ni parité ARET, ni levée de `MEM-WALL-001`. | `DECISION` | Scope/contrôles M3.S2. | `LOG-0090` |
| `MEM-STATE-040` | Reprise active | M3 reste `IN_PROGRESS`. Les prochaines décisions doivent choisir un lot séparé parmi validator de contenu borné, runner sûr additionnel, politiques/gates avancées, CLI/MCP ou pack ARET; aucune capacité absente ne doit être supposée livrée. | `OBSERVED` | Exclusions explicites de M3.S2. | `LOG-0090` |

> **Reprise prioritaire.** Lire `MEM-STATE-039`, `MEM-DEC-033`, `MEM-STATE-040`, `MEM-WALL-001` et `LOG-0090` avant tout lot M3 suivant.


## 22. Addendum de reprise — M3.13 policy d’admission validée

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-041` | Policy d’admission | Une policy singleton immutable offre `PASS_EVIDENCE` et `VALIDATED_PASS_EVIDENCE`. En mode strict, une décision `ADMITTED` exige une evidence `PASS` et un résultat de validator `PASS` existant; la policy ne déclenche aucune validation. | `OBSERVED` | Migration `025_admission_policies.sql`, services d’admission/policy, tests M3.13; 154 tests et 14 sous-tests, wheel isolé. | `LOG-0092`, `LOG-0093` |
| `MEM-DEC-034` | Frontière admission | L’admission est une décision humaine/persistée, non une exécution de validator. Le mode strict refuse sans résultat `PASS`; `REJECTED` demeure un fait diagnostique sans exigence de validation. | `DECISION` | Contrat M3.13 et invariants I004–I008, I013–I015. | `LOG-0092`, `LOG-0093` |
| `MEM-STATE-042` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : validator de contenu explicitement borné, runner sûr additionnel, politiques/gates avancées, CLI/MCP et pack ARET. Aucun oracle externe ou capacité de réseau/shell n’est livré par M3.13. | `OBSERVED` | Revue post-M3.13; aucun contrat ou test de ces capacités n’est livré. | `LOG-0093` |

> **Reprise prioritaire.** Relire `MEM-STATE-041`, `MEM-DEC-034`, `MEM-STATE-042`, `MEM-WALL-001`, puis `LOG-0092`–`LOG-0093` avant tout lot M3 ultérieur.

## 23. Addendum de reprise — M3.14 runner local `EVIDENCE_HASH`

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-043` | Runner local fermé | `SUPERSEDES: MEM-STATE-042` pour l’exclusion des runners. Le catalogue de contrats admet seulement `NOOP` et `EVIDENCE_HASH`; sous `DENY_NETWORK`, `yields_proof=false`, policy `ALLOW` et paramètres exacts `validator_id`/`evidence_id`, `run_evidence_hash` enregistre atomiquement un résultat de validation hash local et une execution `COMPLETED`. | `OBSERVED` | Migration `026_evidence_hash_runner.sql`, services execution/validator, tests M3.14; 159 tests et 14 sous-tests, wheel isolé. | `LOG-0096` |
| `MEM-DEC-035` | Frontière runner | Une execution `EVIDENCE_HASH` est un fait local de validation d’intégrité, non une evidence, admission, preuve, mutation de knowledge, oracle de contenu ou autorisation de processus/fichier/réseau. Les verdicts `PASS` et `FAIL` sont persistés sans promotion implicite; un refus ou duplicat rollbacke entièrement les écritures du runner. | `DECISION` | Contrat M3.14, migration 025→026 et contrôles transactionnels. | `LOG-0096` |
| `MEM-STATE-044` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : validator de contenu explicitement borné ou oracle sous politique séparée, runners sûrs additionnels, politiques/gates avancées, CLI/MCP et pack ARET. Aucun shell, réseau, accès fichier externe, admission automatique ou parité ARET n’est livré par M3.14. | `OBSERVED` | Revue post-M3.14; `MEM-WALL-001` demeure actif. | `LOG-0096` |

> **Reprise prioritaire.** Relire `MEM-STATE-043`, `MEM-DEC-035`, `MEM-STATE-044`, `MEM-WALL-001`, puis `LOG-0095`–`LOG-0096` avant tout lot M3 suivant.

## 24. Addendum de reprise — M3.15 policies de gate

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-045` | Policies de gate | `SUPERSEDES: MEM-STATE-044` pour les gates avancées. Une policy immutable optionnelle par gate offre `ALL`, `ANY` ou `AT_LEAST`; une gate sans policy conserve `ALL`. `AT_LEAST` est borné par la population d’evidences figée à la déclaration de policy. | `OBSERVED` | Migration `027_admission_gate_policies.sql`, `GateService`, tests M3.15; 164 tests et 14 sous-tests, upgrade 026→027 et wheel isolée. | `LOG-0098` |
| `MEM-DEC-036` | Frontière de gate | Une évaluation de gate est une lecture pure d’admissions `ADMITTED` déjà persistées. Elle ne déclenche ni capability, execution, validator, evidence, admission, preuve, mutation knowledge ou mutation work item. Les exigences sont gelées après policy afin de préserver le contrat compté. | `DECISION` | Contrat M3.15 et contrôles de pureté/refus atomique. | `LOG-0098` |
| `MEM-STATE-046` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : validator de contenu ou oracle explicitement policy-gated, runner sûr additionnel, gates pondérées/temporelles seulement sous lot distinct, lifecycle/graph avancés, CLI/MCP et pack ARET. Aucun oracle externe, réseau, shell, admission automatique ou parité ARET n’est livré par M3.15. | `OBSERVED` | Revue post-M3.15; `MEM-WALL-001` demeure actif. | `LOG-0098` |

> **Reprise prioritaire.** Relire `MEM-STATE-045`, `MEM-DEC-036`, `MEM-STATE-046`, `MEM-WALL-001`, puis `LOG-0098` avant tout lot M3 suivant.

## 25. Addendum de reprise — M3.16 readiness et démarrage strict

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-047` | Readiness de work item | `SUPERSEDES: MEM-STATE-046` pour le démarrage contrôlé. La readiness `READY`/`BLOCKED` est dérivée en lecture seule des dependencies `COMPLETED` et des gates `PASS`; elle n’écrit pas `work_item.status`. | `OBSERVED` | `work_readiness.py`, tests M3.16; 168 tests et 14 sous-tests, upgrade 027→028 et wheel isolée. | `LOG-0100` |
| `MEM-DEC-037` | Frontière de démarrage | Une policy singleton immutable `OPEN`/`REQUIRE_READY` est optionnelle. Le mode strict refuse seulement `START` avant insertion/audit si le work item n’est pas prêt; il ne planifie rien, ne complète rien et ne crée ni execution, evidence, admission ou preuve. | `DECISION` | Migration `028_work_start_policies.sql`, lifecycle transactionnel et contrôles de rollback. | `LOG-0100` |
| `MEM-STATE-048` | Reprise active | M3 reste `IN_PROGRESS`. Restent prioritaires : lifecycle/graph avancé sous lot distinct, validator de contenu ou oracle policy-gated, runner sûr additionnel, CLI/MCP et pack ARET. Aucun scheduler, orchestration, oracle externe, réseau, shell, admission automatique ou parité ARET n’est livré par M3.16. | `OBSERVED` | Revue post-M3.16; `MEM-WALL-001` demeure actif. | `LOG-0100` |

> **Reprise prioritaire.** Relire `MEM-STATE-047`, `MEM-DEC-037`, `MEM-STATE-048`, `MEM-WALL-001`, puis `LOG-0100` avant tout lot M3 suivant.


## 26. Addendum de reprise — M3.17 validator de champs d’evidence

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-049` | Validator local | `EVIDENCE_FIELDS` valide localement la présence de clés explicitement déclarées dans un objet JSON d’evidence; il persiste seulement un verdict `PASS`/`FAIL`, sans admission ni preuve. | `OBSERVED` | Migration 029, tests M3.17, 170 tests et 14 sous-tests, wheel isolée. | `LOG-0102` |
| `MEM-DEC-038` | Frontière validator | Les clés requises sont bornées, immuables et syntaxiquement fermées. Leur présence n’est pas un oracle de contenu, une vérité métier ou une promotion; JSON Schema général demeure hors scope. | `DECISION` | Contrat et refus M3.17. | `LOG-0102` |
| `MEM-STATE-050` | Reprise active | M3 reste `IN_PROGRESS`. Restent validator/oracle métier sous policy distincte, runner sûr additionnel, lifecycle/graph avancé, CLI/MCP et pack ARET; `MEM-WALL-001` demeure actif. | `OBSERVED` | Revue post-M3.17. | `LOG-0102` |


## 27. Addendum de reprise — M3.18 runner `EVIDENCE_FIELDS`

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-051` | Runner local | Le catalogue de runners admet `NOOP`, `EVIDENCE_HASH` et `EVIDENCE_FIELDS`. Sous contrat exact et policy `ALLOW`, le runner de champs persiste atomiquement un verdict de validator local et une execution `COMPLETED`. | `OBSERVED` | Migration 030, tests M3.18, 171 tests et 14 sous-tests, wheel isolée. | `LOG-0104` |
| `MEM-DEC-039` | Frontière runner | `EVIDENCE_FIELDS` ne lance aucun processus, ne lit aucun fichier et ne contacte aucun réseau. Une execution est distincte de l’evidence, de l’admission et de la preuve; aucun verdict ne promeut knowledge. | `DECISION` | Contrat runner M3.18 et contrôles transactionnels. | `LOG-0104` |
| `MEM-STATE-052` | Reprise active | M3 reste `IN_PROGRESS`. Restent validator/oracle métier sous policy distincte, runners sûrs additionnels, lifecycle/graph avancé, CLI/MCP et pack ARET; `MEM-WALL-001` demeure actif. | `OBSERVED` | Revue post-M3.18. | `LOG-0104` |


## 28. Addendum de reprise — M3.19 diagnostic de dépendances

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-053` | Diagnostic work graph | `WorkBlockerService` expose les dépendances directes non `COMPLETED` d’un work item, avec statut lifecycle dérivé, sans aucune écriture. | `OBSERVED` | Service/tests M3.19, 172 tests et 14 sous-tests, wheel isolée. | `LOG-0106` |
| `MEM-DEC-040` | Frontière graph | Le diagnostic ne traverse pas transitivement le graph, ne résout pas les gates et n’orchestré aucune transition; il reste une lecture de blocages directs. | `DECISION` | Contrat M3.19. | `LOG-0106` |
| `MEM-STATE-054` | Reprise active | M3 reste `IN_PROGRESS`. Restent graph/lifecycle avancé sous lot distinct, validator/oracle métier policy-gated, runner sûr additionnel, CLI/MCP et pack ARET. | `OBSERVED` | Revue post-M3.19; `MEM-WALL-001` demeure actif. | `LOG-0106` |


## 29. Addendum de reprise — M3.20 diagnostic transitif de dépendances

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-055` | Diagnostic graph | `WorkBlockerService.diagnose_transitive` retourne, dans un ordre stable et sans doublon, les prérequis transitifs non `COMPLETED` d’un work item. | `OBSERVED` | Service/tests M3.20, 173 tests et 14 sous-tests, wheel isolée. | `LOG-0108` |
| `MEM-DEC-041` | Frontière graph | Le traversal est purement informatif. Il ne diagnostique pas les gates, n’orchestré aucune transition et ne crée ni audit ni fait persistant. | `DECISION` | Contrat M3.20. | `LOG-0108` |
| `MEM-STATE-056` | Reprise active | M3 reste `IN_PROGRESS`. Restent graph/lifecycle avancé sous lot distinct, validator/oracle métier policy-gated, runner sûr additionnel, CLI/MCP et pack ARET. | `OBSERVED` | Revue post-M3.20; `MEM-WALL-001` demeure actif. | `LOG-0108` |


## 30. Addendum de reprise — M3.21 diagnostic de gates

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-057` | Diagnostic gates | `GateBlockerService` expose les gates directes non `PASS` d’un work item avec leurs compteurs d’admissions, sans aucune écriture. | `OBSERVED` | Service/tests M3.21, 174 tests et 14 sous-tests, wheel isolée. | `LOG-0110` |
| `MEM-DEC-042` | Frontière gates | Le diagnostic ne crée pas d’admission, n’exécute aucune capability et ne combine pas encore les blockers de dépendance et de gate; il est purement informatif. | `DECISION` | Contrat M3.21. | `LOG-0110` |
| `MEM-STATE-058` | Reprise active | M3 reste `IN_PROGRESS`. Restent diagnostic composite/graph-lifecycle avancé, validator/oracle métier policy-gated, runner sûr additionnel, CLI/MCP et pack ARET. | `OBSERVED` | Revue post-M3.21; `MEM-WALL-001` demeure actif. | `LOG-0110` |


## 31. Décision de portée — contrat M3.EXIT approuvé

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-DEC-043` | Portée M3 | Le périmètre restant de M3 est fini par approbation : M3.22 rapport composite de blockers, M3.23 policy de complétion, M3.24 binding admission-validation, M3.25 catalogue de compatibilité locale, puis M3.EXIT. | `DECISION` | Approbation utilisateur et contrat du workplan. | `LOG-0112` |
| `MEM-STATE-059` | Clôture conditionnelle | M3 demeure `IN_PROGRESS` jusqu’au passage de chacune des gates M3.22–M3.25 et de M3.EXIT. Aucun lot ne peut promouvoir C05/C06/C16, C07 ou la parité ARET. | `OBSERVED` | Contrat M3.EXIT. | `LOG-0112` |


## 32. Addendum de reprise — M3.22 rapport composite de blockers

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-060` | Diagnostic composite | `WorkBlockerReportService` compose les blockers transitifs de dépendance et les gates directes non `PASS`, sans doublon de dépendance ni écriture. | `OBSERVED` | Service/tests M3.22, 175 tests et 14 sous-tests, wheel isolée. | `LOG-0113` |
| `MEM-DEC-044` | Frontière de diagnostic | Le rapport est passif : il n’orchestre, ne planifie, ne déclenche aucune execution et ne modifie aucun fait métier. | `DECISION` | Contrat M3.22. | `LOG-0113` |


## 33. Addendum de reprise — M3.23 policy de complétion optionnelle

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-061` | Policy de complétion | `WorkCompletionPolicyService` persiste une policy singleton immutable `OPEN` ou `REQUIRE_READY_FOR_COMPLETE`. En mode strict, seul `COMPLETE` est refusé avant événement/audit lorsque la readiness dérivée est `BLOCKED`; sans policy ou en `OPEN`, le lifecycle historique est conservé. | `OBSERVED` | Migration 031, tests M3.23 : `180 passed, 14 subtests passed`; upgrade 030→031 et wheel isolée validés. | `LOG-0115` |
| `MEM-DEC-045` | Frontière de complétion | La policy ne complète rien automatiquement et ne modifie ni `START` ni `CANCEL`. Elle ne crée aucune execution, evidence, admission ou preuve; le refus strict rollbacke intégralement l’événement et l’audit. | `DECISION` | Contrat M3.23 et contrôles transactionnels ciblés. | `LOG-0115` |
| `MEM-STATE-062` | Reprise active | M3 reste `IN_PROGRESS`. Le seul prochain lot autorisé est M3.24, binding admission-validation strict; `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et la parité ARET `UNKNOWN` sont inchangés. | `OBSERVED` | Contrat M3.EXIT approuvé. | `LOG-0115` |


## 34. Addendum de reprise — M3.24 binding admission-validation strict

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-063` | Admission stricte | Sous `VALIDATED_PASS_EVIDENCE`, une admission `ADMITTED` exige désormais un `validation_id` explicite, `PASS` et lié à la même evidence. Le binding persistant est FK/unique/append-only; le mode `PASS_EVIDENCE` reste permissif et sans binding. | `OBSERVED` | Migration 032, tests M3.24 : `184 passed, 14 subtests passed`; upgrade 031→032 et wheel isolée validés. | `LOG-0117` |
| `MEM-DEC-046` | Frontière admission-validation | Le binding ne déclenche jamais de validation, n’admet pas automatiquement et ne crée ni execution, evidence, knowledge ni preuve. Les refus absent/cross-evidence/`FAIL`/duplicat sont atomiques avant admission, binding et audit. | `DECISION` | Contrat M3.24, triggers SQL et contrôles transactionnels. | `LOG-0117` |
| `MEM-STATE-064` | Reprise active | M3 reste `IN_PROGRESS`. Le seul prochain lot autorisé est M3.25, catalogue fermé runner-validator-schema; `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et la parité ARET `UNKNOWN` sont inchangés. | `OBSERVED` | Contrat M3.EXIT approuvé. | `LOG-0117` |


## 35. Addendum de reprise — M3.25 catalogue fermé runner-validator-schema

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-065` | Compatibilité runner-validator | Le catalogue local accepte uniquement `EVIDENCE_HASH` avec validator `EVIDENCE_HASH` et `EVIDENCE_FIELDS` avec validator `EVIDENCE_FIELDS`, sous le schéma exact `validator_id`/`evidence_id`. Les deux runners vérifient ce catalogue avant toute validation ou execution. | `OBSERVED` | Module/tests M3.25 : `186 passed, 14 subtests passed`; wheel isolée validée. | `LOG-0119` |
| `MEM-DEC-047` | Frontière catalogue | Le catalogue ne constitue ni un runner générique, ni JSON Schema général, ni un oracle. Les incompatibilités profile/kind/schema échouent atomiquement et ne créent ni validation, execution, evidence, admission ni preuve. | `DECISION` | Contrat M3.25 et contrôles de rollback. | `LOG-0119` |
| `MEM-STATE-066` | Reprise active | M3.25 est le dernier lot fonctionnel autorisé. Seule M3.EXIT reste à exécuter; `MEM-WALL-001`, C05/C06/C16 `SPLIT`, C07 `BLOCKED` et la parité ARET `UNKNOWN` sont inchangés. | `OBSERVED` | Contrat M3.EXIT approuvé. | `LOG-0119` |


## 36. Verdict terminal — M3.EXIT

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-067` | Clôture M3 | M3 est `PASS` pour le Core local, fermé et policy-gated de capabilities, evidence, validation, admission, proof, gates, work graph et lifecycle dérivé. Fresh install 032, upgrade historique 001→032, chaîne intégrée complète, checksums, suite Core, scans et wheel isolée passent. | `OBSERVED` | `tests/test_m3_exit.py`, `188 passed, 14 subtests passed`, intégration wheel M3.EXIT. | `LOG-0121` |
| `MEM-DEC-048` | Frontière de clôture | Le `PASS` M3 ne revendique ni parité ARET, ni oracle métier, shell, réseau, filesystem externe, runner générique, JSON Schema général, CLI/MCP, dashboard, pack/importeur, HMAC rotation, gates pondérées/temporelles/révocables ou orchestration. Aucun nouveau lot M3 n’est autorisé. | `DECISION` | Contrat terminal M3.EXIT approuvé et contrôles de frontière. | `LOG-0121` |
| `MEM-STATE-068` | Reprise post-M3 | Les suites autorisées relèvent de M4+ seulement. C05/C06/C16 restent `SPLIT`; C07 reste `BLOCKED` sous `MEM-WALL-001`; la parité ARET reste `UNKNOWN` jusqu’à M4. ARET-MMU demeure intact à `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. | `OBSERVED` | Matrice de découplage, contrôle Git terminal ARET et contrat M3.EXIT. | `LOG-0121` |


## 37. Addendum — M4.1 compatibilité d’adressage ARET en lecture

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-069` | Compatibilité ARET | Le Domain Pack `vera_mmu.domain_packs.aret` fournit un parseur/constructeur strict de la surface V1 fermée : `knowledge`, `component`, `function`, `brick`, `proof`, `relation`, `asset`, `pipeline` et le singleton `front/current`. Il accepte uniquement la forme canonique `ARET://` pour lecture de compatibilité. | `OBSERVED` | `test_aret_address_compatibility.py`, suite Core `192 passed, 14 subtests passed`, wheel isolée. | `LOG-0123` |
| `MEM-DEC-049` | Frontière M4.1 | M4.1 ne résout aucune adresse dans un store, ne lit ni n’écrit ARET/VERA, ne migre ni ne convertit d’ID, et ne rend pas `ARET://` générable par le Core. Le module est isolé du Core et ne contient aucune dépendance de toolchain ARET. | `DECISION` | Contrat M4.1 et scans de frontière. | `LOG-0123` |
| `MEM-STATE-070` | État M4 | M4 est `IN_PROGRESS`. C01 reste `SPLIT` : les fixtures de round-trip canonique sont couvertes, mais lecteur connecté au store, import de données et parité historique restent non prouvés. C02/C03–C16, `MEM-WALL-001` et la parité ARET restent inchangés. | `OBSERVED` | Matrice de découplage et verdict M4.1. | `LOG-0123` |


## 38. Addendum — M4.2 manifeste déclaratif du runtime ARET V1

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-071` | Runtime ARET | Le Domain Pack expose un manifeste immutable des conventions V1 : override `ARET_MEMORY_DIR`, runtime `.aret-memory`, base `aret_memory.sqlite`, répertoires `artifacts` et `exports`. Il ne résout ni variable ni chemin. | `OBSERVED` | `test_aret_runtime_manifest.py`, suite Core `194 passed, 14 subtests passed`, wheel isolée. | `LOG-0125` |
| `MEM-DEC-050` | Frontière M4.2 | Le manifeste est une description de compatibilité, pas un `StoreLocator`, un adaptateur de migration, une policy ou une lecture de secret. Il ne crée aucun dossier, n’ouvre aucune SQLite et ne connecte pas le runtime V1 au Core VERA. | `DECISION` | Contrat M4.2 et scans de frontière. | `LOG-0125` |
| `MEM-STATE-072` | État M4 | M4 reste `IN_PROGRESS`. C02 reste `SPLIT` : conventions de layout déclarées, mais résolution bornée, WAL/checkpoint, doctor, store V1 et parité sont non implémentés/non prouvés. Les autres couplages et `MEM-WALL-001` sont inchangés. | `OBSERVED` | Matrice de découplage et verdict M4.2. | `LOG-0125` |


## 39. Addendum — M4.3 manifeste déclaratif du schéma ARET V1

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-073` | Schéma ARET | Le Domain Pack expose un manifeste immutable du schéma applicatif V1 observé : migrations 001–006 et dix-huit tables applicatives, sans les tables internes FTS. | `OBSERVED` | Baseline SQLite lue en `mode=ro`, `test_aret_schema_manifest.py`, suite Core `196 passed, 14 subtests passed`, wheel isolée. | `LOG-0127` |
| `MEM-DEC-051` | Frontière M4.3 | Le manifeste est une description de compatibilité; il n’ouvre aucune SQLite, ne lit ni n’importe de ligne, ne crée aucune entité VERA et ne requalifie aucune donnée ou table historique comme compatible. | `DECISION` | Contrat M4.3 et scans de frontière. | `LOG-0127` |
| `MEM-STATE-074` | État M4 | M4 reste `IN_PROGRESS`. C03/C04/C05/C06/C16 restent `SPLIT` : les noms de schéma historique sont connus, mais toute lecture de données, mapping explicite, import, evidence/proof, audit et parité restent non implémentés/non prouvés. `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.3. | `LOG-0127` |


## 40. Addendum — M4.4 profil déclaratif de compatibilité ARET V1

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-075` | Profil ARET | Le Domain Pack expose `aret-v1-compatibility`, un profil immutable qui compose les contrats d’adressage, runtime et schéma M4.1–M4.3. Il n’autorise que `parse_address`, `describe_runtime` et `describe_schema`. | `OBSERVED` | `test_aret_compatibility_profile.py`, suite Core `198 passed, 14 subtests passed`, wheel isolée. | `LOG-0129` |
| `MEM-DEC-052` | Frontière M4.4 | Le profil déclare explicitement `resolve_runtime`, `read_sqlite`, `import_data` et `write_vera` comme hors scope. Il ne devient ni Project Profile VERA validé, ni runtime adapter, ni importeur, ni surface MCP. | `DECISION` | Contrat M4.4 et scans de frontière. | `LOG-0129` |
| `MEM-STATE-076` | État M4 | M4 reste `IN_PROGRESS`. M4.1–M4.4 définissent seulement une frontière de compatibilité descriptive. Toutes les interactions avec les données, pipelines, preuves, playbook, hooks, toolchain et parité ARET restent non implémentées/non prouvées; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.4. | `LOG-0129` |


## 41. Addendum — M4.5 registre de mappings structurels ARET V1

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-077` | Mapping ARET | Le Domain Pack déclare exactement trois correspondances structurelles V1 : `component→entity` de type `COMPONENT`, `function_symbol→symbol` et `brick→work_item`. | `OBSERVED` | `tests/test_aret_structural_mappings.py`, suite Core `200 passed, 14 subtests passed`, wheel isolée. | `LOG-0131` |
| `MEM-DEC-053` | Frontière M4.5 | Chaque correspondance porte `requires_explicit_import=True`. Les tables de données/opérationnelles, notamment `knowledge`, `proof`, `relation`, `asset`, `audit_event`, `front_state`, `pipeline_run` et `bundle_import`, ne sont pas mappées. Le registre ne lit ni ne convertit aucune ligne. | `DECISION` | Contrat M4.5, schéma V1 inspecté et scans de frontière. | `LOG-0131` |
| `MEM-STATE-078` | État M4 | M4 reste `IN_PROGRESS`. Les mappings structurels sont déclarés, mais n’établissent aucune compatibilité de données, d’import, de preuve, d’audit ou de parité. C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.5. | `LOG-0131` |

## 42. Addendum — M4.6 pré-contrat fail-closed d’import de composant ARET V1
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-079` | Préparation d’import | Le Domain Pack expose une unique préparation `component→entity` de type `COMPONENT`. Elle lie une `ProjectIdentity` VERA explicite, un SHA-256 source syntaxiquement canonique, un identifiant de demande et un acteur; son état est `PREPARED_NOT_EXECUTED`. | `OBSERVED` | `tests/test_aret_component_import_preparation.py`, suite Core `210 passed, 14 subtests passed`, wheel isolée. | `LOG-0133` |
| `MEM-DEC-054` | Frontière M4.6 | L’empreinte de source est une déclaration non attestée (`UNVERIFIED_DECLARATION`), non un hash calculé ou vérifié. Le contrat n’accepte aucun chemin de source et n’ouvre ni SQLite, ni fichier, ni store VERA; il ne lit, convertit ni écrit aucune ligne. | `DECISION` | Contrat M4.6 et scans de frontière. | `LOG-0133` |
| `MEM-STATE-080` | État M4 | M4 reste `IN_PROGRESS`. M4.6 ne livre ni admission de source, ni transaction/rollback, ni provenance/audit de lot, ni collision/non-fusion, ni evidence/proof, ni validation post-import, ni parité. C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.6. | `LOG-0133` |

## 43. Addendum — M4.7 attestation bornée du snapshot ARET V1
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-081` | Attestation source | Le Domain Pack atteste, pour une préparation M4.6 strictement non exécutée, les bytes du seul fichier attendu `.aret-memory/aret_memory.sqlite` sous une racine absolue, existante, canonique et non liée. Il vérifie que le SHA-256 calculé correspond au SHA-256 déclaré, et retourne taille, chemin et version V1 manifestée. | `OBSERVED` | `tests/test_aret_source_attestation.py`, suite Core `219 passed, 14 subtests passed`, wheel isolée; attestation ponctuelle de la baseline au hash `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5`, taille `11280384` bytes. | `LOG-0135` |
| `MEM-DEC-055` | Frontière M4.7 | La constante de baseline fixe la référence attendue, mais le module ne vérifie ni commit/répertoire Git, ni contenu ou migrations SQLite, ni identité/provenance du fichier au-delà de son chemin et de ses bytes stables durant la lecture. Il ne crée aucune écriture, transaction, audit, evidence, proof ou import VERA. | `DECISION` | Contrat M4.7 et scans de frontière. | `LOG-0135` |
| `MEM-STATE-082` | État M4 | M4 reste `IN_PROGRESS`. M4.7 ne livre ni admission de source, ni inspection SQLite, ni lecture/mapping de lignes, ni collision/non-fusion, ni transaction/rollback, ni provenance/audit de lot, ni validation post-import ou parité. C02/C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.7. | `LOG-0135` |

## 44. Addendum — M4.8 identité Git read-only de la source ARET V1
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-083` | Identité source | Le Domain Pack lie une attestation M4.7 au dépôt Git contenant sa racine source : racine Git canonique, `HEAD` strictement égal à la baseline V1 et arbre propre, puis conserve le hash de snapshot déjà attesté. Les seules requêtes Git sont `rev-parse --show-toplevel`, `rev-parse HEAD` et `status --porcelain=v1 --untracked-files=all`. | `OBSERVED` | `tests/test_aret_git_source_identity.py`, suite Core `224 passed, 14 subtests passed`, wheel isolée; vérification ponctuelle de `/home/ubuntu/ARET-MMU` au commit et hash de snapshot enregistrés dans `LOG-0137`. | `LOG-0137` |
| `MEM-DEC-056` | Frontière M4.8 | Les requêtes Git sont fixes, sans shell, avec hooks, configuration globale/système et locks optionnels désactivés. Le contrat ne vérifie ni remote, ni signature/auteur du commit, ni contenu SQLite/migrations, ni preuve de provenance externe; il ne crée aucune écriture, transaction, audit, evidence, proof ou import VERA. | `DECISION` | Contrat M4.8 et scans de frontière. | `LOG-0137` |
| `MEM-STATE-084` | État M4 | M4 reste `IN_PROGRESS`. M4.8 ne livre ni admission de source, ni inspection SQLite, ni lecture/mapping de lignes, ni collision/non-fusion, ni transaction/rollback, ni provenance/audit de lot, ni validation post-import ou parité. C02/C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.8. | `LOG-0137` |

## 45. Addendum — M4.9 inspection SQLite read-only du manifeste ARET V1
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-085` | Manifeste SQLite | Le Domain Pack ouvre le snapshot M4.7/M4.8 uniquement via SQLite `mode=ro&immutable=1`, active `query_only`, lit les versions de `schema_migrations` et les noms de tables applicatives de `sqlite_schema`, puis exige l’égalité avec le manifeste V1 immutable. | `OBSERVED` | `tests/test_aret_sqlite_schema_inspection.py`, suite Core `229 passed, 14 subtests passed`, wheel isolée; inspection ponctuelle baseline avec hash inchangé. | `LOG-0139` |
| `MEM-DEC-057` | Frontière M4.9 | L’inspection n’exécute que des `SELECT` nominatives de métadonnées. Elle ne lit aucune ligne applicative, colonne, contrainte, index, trigger ni FTS détaillé; elle ne crée aucune écriture, transaction VERA, audit, evidence, proof, import ou conversion. | `DECISION` | Contrat M4.9 et scans de frontière. | `LOG-0139` |
| `MEM-STATE-086` | État M4 | M4 reste `IN_PROGRESS`. M4.9 ne livre ni admission de source, ni lecture/mapping de données, ni collision/non-fusion, ni transaction/rollback, ni provenance/audit de lot, ni validation post-import ou parité. C02/C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.9. | `LOG-0139` |

## 46. Addendum — M4.10 lecture paginée brute de composants ARET V1
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-087` | Lecture source | Le Domain Pack observe seulement des pages keyset de `component`, ordonnées par `id`, bornées à 100 et liées au snapshot M4.9 par hash avant/après. Chaque record reste une ligne source brute avec `id`, `title`, `description`, `created_at`, `created_by`; aucun champ VERA n’est construit. | `OBSERVED` | `tests/test_aret_component_source_reader.py`, suite Core `238 passed, 14 subtests passed`, wheel isolée; lecture ponctuelle de 17 composants baseline sans affichage de leur contenu. | `LOG-0141` |
| `MEM-DEC-058` | Frontière M4.10 | La lecture est exclusivement SQLite `mode=ro&immutable=1` + `query_only`, `SELECT` paramétrée de `component` et pagination keyset. Le contrat exclut explicitement mapping, normalisation, collision/non-fusion, import, transaction/rollback, provenance/audit, evidence/proof, admission et toute autre table. | `DECISION` | Contrat M4.10 et scans de frontière. | `LOG-0141` |
| `MEM-STATE-088` | État M4 | M4 reste `IN_PROGRESS`. M4.10 ne livre ni conversion vers `entity`, ni écriture VERA, ni lot réversible, ni validation post-import ou parité. C02/C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.10. | `LOG-0141` |

## 47. Addendum — M4.11 préflight fail-closed d’import component ARET V1
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-089` | Préflight import | Le Domain Pack lie une préparation M4.6, une inspection M4.9 et une page M4.10 portant le même hash source. Le résultat porte identité VERA cible, plage source et politiques fixes : rejet d’existant, non-fusion, zéro promotion, zéro écriture et rollback/audit/provenance requis avant toute écriture future. | `OBSERVED` | `tests/test_aret_component_import_preflight.py`, suite Core `243 passed, 14 subtests passed`, wheel isolée; préflight baseline 17 records en `PREFLIGHT_NOT_EXECUTABLE`. | `LOG-0143` |
| `MEM-DEC-059` | Frontière M4.11 | Un préflight est une contrainte déclarative fail-closed et non une autorisation. Il n’ouvre ni source ni store VERA et n’effectue aucune projection, collision, merge, transaction, rollback, audit, provenance, evidence, proof, admission ou écriture. | `DECISION` | Contrat M4.11 et scans de frontière. | `LOG-0143` |
| `MEM-STATE-090` | État M4 | M4 reste `IN_PROGRESS`. M4.11 ne livre ni mapping vers `entity`, ni recherche effective de collision, ni write-path transactionnel/réversible/audité, ni validation post-import ou parité. C02/C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.11. | `LOG-0143` |

## 48. Addendum — M4.12 projection non écrivable de brouillons entity ARET V1
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-091` | Projection cible | Le Domain Pack projette chaque component préflighté en brouillon entity déterministe : identifiant `aret-component--<source_id>`, adresse `vera://`, type `component` à enregistrer ultérieurement et métadonnées source (pack, table, ID, hash, création). Le résultat reste `PROJECTED_NOT_WRITABLE`. | `OBSERVED` | `tests/test_aret_component_entity_projection.py`, suite Core `247 passed, 14 subtests passed`, wheel isolée; projection baseline de 17 brouillons sans enregistrement. | `LOG-0145` |
| `MEM-DEC-060` | Frontière M4.12 | La projection est pure : elle appelle seulement la validation d’adresse Core et ne crée aucun `entity_type`, `entity`, lookup de collision, transaction, rollback, audit, provenance, evidence, proof, admission ou import. Les champs source non compatibles avec le contrat textuel/identifiant VERA sont refusés plutôt que normalisés. | `DECISION` | Contrat M4.12 et scans de frontière. | `LOG-0145` |
| `MEM-STATE-092` | État M4 | M4 reste `IN_PROGRESS`. M4.12 ne livre ni enregistrement de type entity, ni collision effective, ni write-path transactionnel/réversible/audité, ni validation post-import ou parité. C02/C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.12. | `LOG-0145` |

## 49. Addendum — M4.13 contrôle read-only des collisions cible ARET V1
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-093` | Contrôle cible | Le Domain Pack vérifie, dans un `MemoryStore` VERA déjà ouvert et à identité exactement égale à la projection, l’absence du type `component` et de chaque identifiant de draft. Le résultat clair porte `ABSENT_REQUIRED` et `TARGET_CLEAR_NOT_WRITABLE`; tout existant est refusé. | `OBSERVED` | `tests/test_aret_component_target_collision_check.py`, suite Core `252 passed, 14 subtests passed`, wheel isolée; contrôle baseline de 17 drafts avec audit cible invariant. | `LOG-0147` |
| `MEM-DEC-061` | Frontière M4.13 | M4.13 n’appelle que deux lectures SQL exactes et n’ouvre aucune transaction. Il ne crée pas le store, le type ou l’entité; il n’ajoute aucun audit et n’exécute ni rollback, provenance, evidence, proof, admission ni import. Une cible claire est une précondition, jamais une autorisation d’écriture. | `DECISION` | Contrat M4.13 et scans de frontière. | `LOG-0147` |
| `MEM-STATE-094` | État M4 | M4 reste `IN_PROGRESS`. M4.13 ne livre ni enregistrement de type, ni création transactionnelle/réversible/auditée des entities, ni validation post-import ou parité. C02/C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.13. | `LOG-0147` |

## 50. Addendum — M4.14 batch atomique générique Core
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-095` | Primitive Core | `EntityService.register_type_and_create_batch` enregistre dans une transaction unique un type générique absent et 1–100 entités validées, avec audit de type et d’entités. Tout conflit/échec rollbacke intégralement les insertions et audits du batch. | `OBSERVED` | `tests/test_entity_atomic_batch.py`, suite Core `256 passed, 14 subtests passed`, wheel isolée. | `LOG-0149` |
| `MEM-DEC-062` | Frontière M4.14 | Le primitif appartient au Core, sans terme/import de pack. Il ne lit aucune source externe et son rollback est transactionnel en cas d’échec uniquement : il ne fournit pas une suppression/réversion d’un batch déjà committé ni un droit d’invocation ARET. | `DECISION` | Contrat M4.14, scan Core sans ARET et tests de rollback. | `LOG-0149` |
| `MEM-STATE-096` | État M4 | M4 reste `IN_PROGRESS`. M4.14 ne relie pas le primitif à la demande/préflight/projection ARET, ne transfère aucune provenance et ne livre ni import effectif, post-validation ou parité. C02/C03/C04/C05/C06/C16 restent `SPLIT`; `MEM-WALL-001` reste actif. | `OBSERVED` | Matrice de découplage et verdict M4.14. | `LOG-0149` |

## 51. Addendum — M4.15 premier import atomique explicitement autorisé de composants ARET V1
| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-097` | Import autorisé | Le Domain Pack crée une autorisation explicite, sans effet d’écriture propre, liée exactement au préflight M4.11, à la projection M4.12 et au clear-check M4.13. Le write-path recontrôle la collision puis appelle exclusivement le batch Core générique : une page baseline de 17 composants crée atomiquement le type `component`, 17 entities et 18 audits, avec état `IMPORTED_NO_PROMOTION`. | `OBSERVED` | `tests/test_aret_component_authorized_import.py` (`5 passed`), suite Core `261 passed, 14 subtests passed`, intégration dans un store VERA temporaire, rollback de conflit et wheel isolée; commit `034efaf9f6d845742d2209c89099d10dd5fc4ad0`. | `LOG-0151` |
| `MEM-DEC-063` | Frontière M4.15 | L’autorisation utilisateur est consommée uniquement par ce contrat borné : une page pré-projetée `component→entity` vers une cible VERA identitaire et claire. Le module n’ouvre aucune source ARET, n’utilise ni SQL brut/source I/O/shell/réseau, ne fusionne rien, ne crée aucune evidence/proof/admission/promotion et ne fournit ni reprise/idempotence globale ni suppression d’un import déjà committé. | `DECISION` | Contrat M4.15, scans de frontière et autorisation explicite du propriétaire. | `LOG-0151` |
| `MEM-STATE-098` | État M4 | M4 reste `IN_PROGRESS`; la parité ARET reste `UNKNOWN`. Le registre versionné `M4_COMPLETION_REGISTER.md` énumère les gates restantes, dont runtime/source, conformance de schéma, imports `function_symbol`/`brick` et tables associées, capabilities, oracles/toolchain, playbook, MCP/hooks, bundles/VCS et suite de parité. C07/C08 restent `BLOCKED` par `MEM-WALL-001`; aucun `M4.EXIT` n’est éligible. | `OBSERVED` | Registre M4, matrice C01–C16, spécification finale et verdict M4.15. | `LOG-0153` |

## 52. Addendum — M4-A migration paginée `component` ledger-backed

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-099` | Ledger générique | `SUPERSEDES: MEM-STATE-098` pour la reprise active de l’import `component`. Le Core expose désormais un batch atomique sur type déjà enregistré et la migration 033, qui crée `import_batch`/`import_batch_entity` append-only. `ImportBatchService` lie le batch à un fingerprint canonique, refuse un même ID divergent, rejoue un batch exact sans écriture, et rollbacke type, entités, liens et audits sur conflit. | `OBSERVED` | `tests/test_entity_existing_type_batch.py`, `tests/test_entity_import_batches.py`, migrations 001→033, suite complète et roues isolées ; commits `1ea116faeac58958311e6f135a6c68df8e6a5a53` et `e3105b00a6d6152c5a833d0b7bafcd579442062c`. | `LOG-0154` |
| `MEM-STATE-100` | Conformité et import de page | Le pack ARET vérifie en lecture SQLite immutable les cinq colonnes `component` attendues avant l’import, puis autorise explicitement une page seulement si son préflight, sa projection, son hash source, sa conformité et sa série cible correspondent. L’écriture passe exclusivement par le ledger. La page baseline de 17 composants a créé 17 entités et 17 liens de ledger dans un store VERA temporaire; le replay exact n’a créé aucune écriture, evidence ni proof link. | `OBSERVED` | `tests/test_aret_component_schema_conformance.py`, `tests/test_aret_component_page_import_series.py`, vérification intégrée du snapshot baseline, suite `284 passed, 14 subtests passed`, scans et roues isolées ; commits `cdf65f7150023d6dd57739f991db8c1ac93aeba2` et `8263d40b709acce40b946bd575cf8f648ae842b3`. | `LOG-0154` |
| `MEM-DEC-064` | Frontière M4-A | Le ledger est une capacité Core générique. Le write-path ARET ne lit aucune source et n’écrit ni SQL brut, preuve, evidence, admission ou promotion ; la source est lue séparément par les contrats read-only M4.7–M4.12. Une page suivante ne peut suivre qu’une série ARET V1 de même snapshot/mapping/type, jamais un type manuel ou une série de hash divergent. | `DECISION` | Contrat M4-A, scans Core/pack et tests de type incompatible, binding divergent, collision tardive et replay. | `LOG-0154` |
| `MEM-STATE-101` | Limite M4 | M4 reste `IN_PROGRESS` et M4-A reste partiel : la policy runtime/WAL, la conformance profonde hors `component`, les sources réelles multi-pages et la post-validation exhaustive demeurent ouvertes. Les imports `function_symbol`, `brick`, knowledge, preuves, relations, assets, audit/front et séquences ne sont pas livrés. C01–C06/C16 restent `SPLIT`; C07/C08 restent `BLOCKED — MEM-WALL-001`; la parité ARET reste `UNKNOWN`. | `OBSERVED` | Registre M4, matrice C01–C16, plan vivant et validation M4-A. | `LOG-0155` |

> **Reprise prioritaire.** Relire `MEM-STATE-099` à `MEM-STATE-101`, le registre M4 et `LOG-0154`/`LOG-0155` avant tout sous-lot M4-B ou toute tentative de déclarer une sortie M4.

## 53. Addendum — M4-A2 resolver runtime et safety WAL/SHM

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-102` | Runtime ARET V1 | `SUPERSEDES: MEM-STATE-101` pour le sous-ensemble runtime. Le Domain Pack résout sans création ni environnement implicite le layout ARET V1 par défaut ou un unique override fourni explicitement sous `ARET_MEMORY_DIR`. Les racines, runtime et snapshot doivent être absolus, canoniques, existants et non liés. | `OBSERVED` | `tests/test_aret_runtime_resolution_safety.py`; commit `c18d08c675c1bd69602471c082efc1c978b643e1`. | `LOG-0156` |
| `MEM-DEC-065` | Policy WAL | Avant toute lecture SQLite immutable, le pack exige un snapshot régulier et stable sans sidecar `-wal` ni `-shm`. Il refuse bruyamment ces sidecars ou liens au lieu de checkpoint, d’ouvrir SQLite ou de modifier ARET. Cette policy est une gate de sécurité de lecture, non une preuve de parité du journal legacy. | `DECISION` | Contrat M4-A2 et tests de sidecar/symlink/stabilité. | `LOG-0156` |
| `MEM-STATE-103` | Baseline runtime | Sur la baseline ARET immuable, le resolver retourne `DEFAULT_RUNTIME_LAYOUT`, la safety gate retourne `NO_WAL_SIDECARS` et la taille du snapshot est `11280384` bytes. La suite VERA passe `298 passed, 14 subtests passed`; la roue isolée et les scans de frontière passent. | `OBSERVED` | Vérification ponctuelle read-only et validation M4-A2. | `LOG-0156` |
| `MEM-STATE-104` | Limite M4-A | Le resolver et la policy WAL sont livrés de façon bornée, mais l’override explicite n’est pas encore lié à l’ensemble attestation → identité Git → inspection → reader → import. Le checkpoint externe, les sources multi-pages réelles et la post-validation exhaustive restent ouverts. M4 reste `IN_PROGRESS`; C01–C06/C16 `SPLIT`; C07/C08 `BLOCKED — MEM-WALL-001`; parité `UNKNOWN`. | `OBSERVED` | Registre M4 et plan vivant. | `LOG-0157` |

## 54. Addendum — M4-A3 chaînage runtime default/override

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-105` | Chaîne source | `SUPERSEDES: MEM-STATE-104` pour le binding runtime. Une résolution runtime+safety explicitement liée peut désormais traverser l’attestation M4.7, l’identité Git M4.8, l’inspection SQLite M4.9 et le lecteur `component` M4.10. Sans override, le layout `.aret-memory/aret_memory.sqlite` historique demeure exigé exactement. | `OBSERVED` | `tests/test_aret_runtime_resolution_chain.py`; commit `4f9d1ed0c881d41b7e98a01e228f05903e65a408`. | `LOG-0158` |
| `MEM-STATE-106` | Intégration override | Sur une copie temporaire du snapshot baseline, `ARET_MEMORY_DIR_OVERRIDE` a produit `NO_WAL_SIDECARS`, une attestation, une identité Git propre, une inspection de schéma et une lecture de 17 composants. Aucun fichier ARET n’a été modifié. | `OBSERVED` | Vérification intégrée M4-A3 et contrôle Git ARET. | `LOG-0158` |
| `MEM-DEC-066` | Binding source | Un snapshot custom n’est acceptée par l’identité Git que si l’attestation porte explicitement la base `ARET_MEMORY_DIR_OVERRIDE`; une attestation `DEFAULT_RUNTIME_LAYOUT` doit rester liée au chemin legacy exact. L’inspection et le reader suivent uniquement le chemin attesté, jamais une reconstruction implicite du layout. | `DECISION` | Contrat M4-A3, tests de path binding et fixtures de régression M4.7–M4.10. | `LOG-0158` |
| `MEM-STATE-107` | Limite M4 | Le chaînage runtime résout une partie de M4-EXIT-01 mais ne remplace pas la conformance profonde de toutes les tables, la migration structurelle `function_symbol`/`brick`, les données sémantiques, toolchain/oracles, intégrations M5/M6 ni la parité. M4 reste `IN_PROGRESS`; C01–C06/C16 `SPLIT`; C07/C08 `BLOCKED — MEM-WALL-001`; parité `UNKNOWN`. | `OBSERVED` | Registre M4 et validation M4-A3. | `LOG-0159` |

## 55. Addendum — M4-A post-validation de page component

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-108` | Post-validation | Après import autorisé, le pack relit sans écriture le batch générique, ses liens `source_identifier→entity_id` et les entités composant. Il exige l’égalité exacte avec les drafts : type, titre, description, métadonnées et provenance source. Le résultat est `POST_VALIDATED_NO_PROMOTION`. | `OBSERVED` | `tests/test_aret_component_post_validation.py`; commit `2d237f05e762dd9cffc89a1c1c9a8c9be1da5ea9`. | `LOG-0160` |
| `MEM-STATE-109` | Limite M4-A | Cette preuve couvre une page autorisée et son ledger, non une source réelle multi-pages ni une validation exhaustive de tous les lots. Elle ne crée ni audit supplémentaire, ni evidence, ni knowledge proof, ni admission, ni promotion. M4 et la parité ARET demeurent ouverts/inconnus. | `OBSERVED` | Contrat M4-A post-validation et registre de clôture. | `LOG-0160` |

## 56. Addendum — M4-B lecteurs structurels

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-110` | M4-B | Les tables ARET V1 `function_symbol` et `brick` disposent désormais de lecteurs paginés/hashés en SQLite immutable, liés au snapshot inspecté et sans write-path. Aucun symbole ni work item n’est encore projeté ou importé. | `OBSERVED` | Tests readers, commit `fb5a04db57f3dd00feca81724157df08502eb0ca`. | `LOG-0162` |

| `MEM-STATE-111` | M4-B projection | La projection `function_symbol→symbol` est déterministe, relie chaque fonction à `aret-component--<component_id>`, conserve module/symbole/convention dans la provenance et retourne `PROJECTED_NOT_WRITABLE`. Aucun symbole VERA n’est écrit. | `OBSERVED` | Tests projection, commit `e0a75c441c617000334cc2b275b5dcdd68e2bbcf`. | `LOG-0163` |
| `MEM-STATE-112` | M4-B projection | La projection `brick→work_item` est déterministe : identifiant cible, priorité, description et toutes les sémantiques legacy (`state`, composant, milestone, plateforme) sont conservées en provenance sous `PROJECTED_NOT_WRITABLE`. Aucun work item VERA n’est écrit. | `OBSERVED` | Tests projection, commit `568d9fb296c2d8a03f525f3c1312260eb6287b83`. | `LOG-0164` |


## 60. Addendum — primitive Core 034 de batches de ressources

| ID | Catégorie | Énoncé | Statut | Provenance | Journal |
|---|---|---|---|---|---|
| `MEM-STATE-113` | Ledger Core de ressources | Le Core possède désormais la migration 034 et `ImportBatchService.commit_resource_import_batch` pour créer atomiquement, auditer et lier à un ledger append-only les seuls kinds fermés `SYMBOL` et `WORK_ITEM`. Un batch canonique est fingerprinté ; le replay exact est sans écriture ; une réutilisation divergente, un kind/payload inconnu, un parent absent ou un conflit sémantique échoue avec rollback. La création passe exclusivement par les services Core respectifs, et les transactions imbriquées composent par savepoint. | `OBSERVED` | Migration 034, `import_batches.py`, `store.py`, `tests/test_resource_import_batches.py`, `tests/test_store.py`; suite `325 passed, 14 subtests passed`; wheel isolée et scan Core anti-ARET. | `LOG-0165` |
| `MEM-DEC-064` | Frontière Core 034 | Le primitive ne contient aucun terme ni I/O ARET et ne remplace aucun contrat du Domain Pack. Il ne lit aucune source, ne choisit aucun mapping, ne vérifie aucune conformance source, n’autorise aucune écriture legacy et ne crée ni evidence, admission, proof/proof link ni promotion. `SYMBOL` et `WORK_ITEM` sont des resources Core fermées, non des synonymes des tables ARET. | `DECISION` | Contrat Core 034, scan anti-ARET et registre M4. | `LOG-0165` |
| `MEM-STATE-114` | Reprise M4-B | `SUPERSEDES: MEM-STATE-112` pour la disponibilité du write-path Core, mais non pour les imports ARET. Les lecteurs/projections `function_symbol` et `brick` restent read-only/purs ; le prochain sous-lot requis est la conformance source et le préflight propre à chaque mapping, suivis de contrats distincts de collision, autorisation, import et post-validation. `M4-B`/M4 restent `IN_PROGRESS`; C04/C05/C16 restent `SPLIT`; C07/C08 restent `BLOCKED — MEM-WALL-001`; parité ARET `UNKNOWN`. | `OBSERVED` | Registre M4, matrice de découplage, commit `77591e586d8dfa60bb0b49dd06f1c056d11658a0` publié et vérifié. | `LOG-0165`, `LOG-0166` |
| `MEM-STATE-115` | Durcissement Core 034 | `SUPERSEDES: MEM-STATE-113` pour le résultat final du primitive. Le préflight refuse désormais explicitement toute coercition implicite des champs textuels de payload avant transaction ; un scalaire non textuel ne peut devenir valide par conversion. Les commits `77591e586d8dfa60bb0b49dd06f1c056d11658a0` et `8e0d56692c3f1a5b19d9e2ac1d40678f10c7c7fc` sont publiés ; la suite finale est `326 passed, 14 subtests passed`. Les frontières et exclusions de `MEM-DEC-064` demeurent intégrales. | `OBSERVED` | Test tests-first de coercition, contrat ciblé, suite complète, scan Core anti-ARET et publication distante vérifiée. | `LOG-0165`, `LOG-0167` |
| `MEM-STATE-116` | Conformance/préflight structurels M4-B | `SUPERSEDES: MEM-STATE-114` pour les prérequis read-only. Le pack vérifie les métadonnées source de `function_symbol` et `brick` contre le snapshot inspecté, puis lie préparation explicitement gated, inspection, conformité et page observée à un préflight `PREFLIGHT_NOT_EXECUTABLE`. Il impose l’ID fonction stable, les contraintes brick d’état/priorité/index et la conservation de l’état legacy uniquement comme métadonnée future. | `OBSERVED` | Modules/tests M4-B, suite `340 passed, 14 subtests passed`, wheel isolée et commit `8d6e4fc2ec674ac3d2be8297ad3b3f9868239eaa` publié/vérifié. | `LOG-0168` |
| `MEM-DEC-065` | Frontière du préflight structurel | Le préflight ne lit ni snapshot, ni store VERA ; il ne confère aucune autorisation et sa politique de write/merge/promotion reste `FORBID`. Pour les bricks, `ACTIVE` n’est pas assimilé à un status cible : il reste un fait legacy à préserver, et la garde Front/lifecycle est explicitement hors contrat jusqu’à une décision propre. | `DECISION` | Contrat M4-B, registre de clôture et tests de refus. | `LOG-0168`, `LOG-0169` |
| `MEM-STATE-117` | Reprise M4-B | Les prochains contrats sont collision/non-fusion et autorisation explicite distinctes pour `function_symbol→symbol` et `brick→work_item`, liées au Core 034 et aux préflights. Aucun import structurel ARET n’a encore eu lieu. M4-B/M4 restent `IN_PROGRESS`; C04/C05/C16 `SPLIT`; C07/C08 `BLOCKED — MEM-WALL-001`; parité `UNKNOWN`. | `OBSERVED` | Registre M4 et publication du lot read-only. | `LOG-0169` |
| `MEM-STATE-118` | Collision et autorisation M4-B | `SUPERSEDES: MEM-STATE-117` pour les prérequis d’écriture. Les checks structurels refusent toute cible ressource non vide, exigent les entities component pour les symboles et relisent les bindings avant l’autorisation. Les autorisations sont explicites, mapping-scopées, non fusionnelles, zéro-write et `FORBID` pour promotion. Elles ne créent encore aucun symbol/work item. | `OBSERVED` | Tests M4-B, suite `349 passed, 14 subtests passed`, wheel isolée, commit `3f21200cc0ca31119e752b5a785dc54170fa15ce` publié/vérifié. | `LOG-0170` |
| `MEM-DEC-066` | Frontière du premier write-path structurel | Un write-path futur doit consommer l’autorisation exacte, revalider la collision au point d’écriture, passer uniquement par `ImportBatchService.commit_resource_import_batch`, porter audit/ledger et rester sans evidence, proof/proof link, admission ni promotion. Toute série ultérieure doit être définie par contrat séparé ; elle n’est pas autorisée par le check initial cible-vide. | `DECISION` | Contrats Core 034 et M4-B. | `LOG-0170`, `LOG-0171` |
| `MEM-STATE-119` | Reprise import M4-B | Le prochain sous-lot est l’import structurel atomique et la post-validation read-only, distincts pour symbol/work item. M4-B/M4 restent `IN_PROGRESS`; C04/C05/C16 restent `SPLIT`; C07/C08 restent `BLOCKED — MEM-WALL-001`; parité `UNKNOWN`; `M4.EXIT` `NOT_ELIGIBLE`. | `OBSERVED` | Registre M4 et publication collision/autorisation. | `LOG-0171` |
