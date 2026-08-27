# M11 — Audit exhaustif de complétude face à la spécification Universal Dev-MMU

**Date :** 2026-08-27  
**Révision VERA auditée :** `9ac62d972633c04e9daa56723470f8d6ae7cab74`  
**Spécification auditée :** `UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md`, version 1.0 du 2026-08-23, SHA-256 `d8e5d01b673e243e0104a30fb62328bc2a7fc650373ab91b1a103652a1737d75`.[1]  
**Périmètre exclu à la demande du propriétaire :** vérification manuelle ultérieure du démarrage MSI Windows. Elle ne change aucun des constats fonctionnels ci-dessous.

> **Verdict global : `NOT_DONE`.** VERA-MMU contient un Core universel et fortement testé, une chaîne MCP/adapters bornée, une CLI et une application desktop de préparation project-local, ainsi qu’une préversion Linux réellement démarrée. En revanche, la spécification finale impose un produit plus large : import existant avec provenance, bundles/restore, API et CLI complètes, Dashboard éditeur de modèle, générateur documentaire, VCS abstrait, compatibilité ARET de bout en bout et preuves d’hôtes réels. Ces éléments ne sont pas tous livrés. Retirer Windows du périmètre ne les retire pas.

## 1. Méthode et vocabulaire de verdict

L’audit ne déduit jamais une capacité d’un nom de dossier, d’un plan, d’une compilation ou d’un test de fixture. Une exigence est `PASS` seulement lorsqu’une implémentation correspondante et une preuve proportionnée sont présentes. `PARTIAL` signifie qu’une version volontairement bornée existe, mais ne couvre pas l’exigence complète. `MISSING` signifie qu’aucune surface fonctionnelle équivalente n’est exposée. `NOT_PROVEN` signifie qu’un mécanisme est livré, mais que l’événement externe requis n’a pas été observé. `OUT_OF_SCOPE` signifie qu’un contrôle est consciemment retiré du présent verdict et ne peut pas être transformé en `PASS`.

| Statut | Sens strict dans ce registre | Autorise « livré totalement » ? |
|---|---|---|
| `PASS` | Code, contrat et preuve disponible couvrent l’exigence formulée. | Oui, pour cette ligne seulement. |
| `PARTIAL` | Une partie sûre est livrée ; une exigence fonctionnelle explicitement demandée manque encore. | Non. |
| `MISSING` | Aucune surface équivalente n’est livrée ou accessible. | Non. |
| `NOT_PROVEN` | Le mécanisme existe, mais une preuve externe réelle reste différée. | Non, si la spécification exige cette preuve. |
| `OUT_OF_SCOPE` | Contrôle explicitement différé par le propriétaire. | Ne compte ni comme `PASS` ni comme défaut produit. |

La suite VERA de la révision auditée est **verte : `518 passed, 43 subtests passed`**. Le scan indépendant du Core ne trouve aucun vocabulaire ARET hors `domain_packs/aret`. Cette preuve atteste la non-régression du périmètre actuellement implémenté ; elle ne rend pas, par elle-même, les surfaces absentes présentes.[2] [3]

## 2. Registre des livrables d’architecture et de Core

| ID | Exigence de la spécification | État VERA constaté | Statut | Écart ou condition de clôture |
|---|---|---|---|---|
| `A-01` | Core indépendant d’ARET ; spécialisation dans un Domain Pack. §§1–2, 54, 58. | Le Core est sous `src/vera_mmu`; les concepts ARET sont sous `src/vera_mmu/domain_packs/aret`. Le scan de frontière est vert. | `PASS` | Le découplage de code est démontré ; la **parité ARET**, distincte, ne l’est pas. |
| `A-02` | SQLite canonique, knowledge append-only, audit, preuves/admission, gates et fail-closed. §§1, 15, 39, 53, 58. | Les migrations 001→038, services de knowledge, evidence, admission, proof, gate, work et lifecycle existent. La chaîne M3 est exécutée sur un store frais. | `PASS` pour le Core borné | Les bundles, Active Front et migration ARET intégrale sont évalués séparément. |
| `A-03` | Project Profile canonique avec stockage, identité, types, relations, work, capabilities, gates, policies et integrations. §6. | `project.yaml` est validé, hashé et lié au workspace. `init-project` crée un profil minimal avec domaine, workspace, stockage et identité. | `PARTIAL` | Le profil initial ne contient ni taxonomie, relations, Front, catalogues capabilities/gates/policies ni configuration d’intégration détaillée ; les fichiers demandés ne sont pas générés. |
| `A-04` | Taxonomie universelle de knowledge et statuts épistémiques extensibles. §7. | `knowledge_type`, statuts contrôlés, append-only, supersession et audit sont persistés et testés. | `PASS` | Les types projet sont déclarables via le Core ; aucun template métier riche n’est inféré. |
| `A-05` | Registres `entity`, `symbol`, `relation_type` et relations configurables. §§8–9. | Migrations et services `entities.py`, `symbols.py`, `relations.py` sont présents, avec FK, immuabilité et audit. | `PASS` | Le graphe est un mécanisme générique ; l’éditeur visuel correspondant manque encore. |
| `A-06` | Work Graph hiérarchique et Gate Engine relié à des exécutions/preuves réelles. §§10–11. | `work_item`, dépendances, readiness, lifecycle, gates, validations, admissions et preuves sont testés dans la chaîne M3. | `PASS` pour le mécanisme Core | L’édition/import/export de ce graphe par CLI ou Dashboard complet n’est pas livrée. |
| `A-07` | Capability Engine déclaratif avec runners shell/python/MCP/Git/HTTP/Docker/filesystem, policies, timeouts, artefacts et validators. §§12–13. | Catalogue fermé, contrats, policies, schémas de paramètres, timeouts, validators et runners bornés (`NOOP`, evidence hash/fields, process observé) sont livrés. | `PARTIAL` | Aucun runner universel shell/python/HTTP/Docker/filesystem n’est exposé. Le seul process runner est observationnel et les exécutions externes appartiennent au Pack ARET fermé. |
| `A-08` | Execution Store distinct de l’Evidence Store ; résultat normalisé et traçable. §§14–15. | `execution`, `evidence`, `validation`, `admission` et `proof` sont séparés ; seul un `PASS` admissible est promouvable. | `PASS` | La diversité de types de preuves est un mécanisme contrôlé, non un catalogue de connecteurs externes généraliste. |
| `A-09` | Provenance générique documentaire et non Git. §16. | `knowledge_source` enregistre dépôt, révision, chemin, lignes, section et hash avec lecture bornée. | `PARTIAL` | Les formes URL, document externe, dataset et import autonome de documents ne sont pas livrées. |
| `A-10` | Project identity vérifiée à chaque restauration, sans mémoire croisée. §17. | Identité de profil/workspace et checks sont appliqués à l’ouverture du store et aux opérations de Core. | `PASS` | La restauration de **bundle** demandée reste absente. |
| `A-11` | Adressage `mmu://` et lecture de compatibilité `ARET://`. §18, §57. | Adressage strict `vera://`; lecteur syntaxique `ARET://` limité au Pack ARET. | `PARTIAL` | Le schéma cible littéral `mmu://` n’est pas utilisé ; `ARET://` ne lit pas les ressources legacy dans le store et il n’existe pas d’aliases MCP `aret_*`. |
| `A-12` | Active Front configurable, handoff et Resume Template/rituel générique. §19. | Resume Guard, dossier hashé, acquittement contextualisé et lifecycle sont livrés/testés. | `PARTIAL` | Aucun service public de Front actif, handoff persistant ou template de resume configurable n’est trouvé dans la surface VERA. |
| `A-13` | Playbook universel, project-specific, lié au profil sans mutation de mémoire. §20. | Un playbook minimal est créé à l’initialisation et les instructions MCP portent une doctrine Core fixe. | `PARTIAL` | Les instructions ne composent pas le playbook projet, les règles capability/policy ni le protocole resume comme le demande la spécification. |
| `A-14` | Policy Engine en fichier déclaratif global `.mmu/policies.yaml`. §21. | Policies de capability, admission, proof, gates et sync existent dans SQLite/JSON fermé. | `PARTIAL` | Il n’existe pas de fichier global de policies YAML ni d’éditeur/compilateur couvrant filesystem, process, destructive et promotion comme surface projet complète. |
| `A-15` | Abstraction VCS : Git, Mercurial, SVN, NoVCS. §22. | Git est strictement borné à `origin`, branche courante et `.vera-mmu/`; no-Git est supporté pour le Core. | `PARTIAL` | Aucun `VersionControlProvider`, ni provider Mercurial/SVN. La synchronisation Git est volontairement moins générale que le modèle prescrit. |
| `A-16` | Bundle universel exportable/importable, manifest hashé et restauration non fusionnelle. §23. | L’invariant est documenté, mais aucune commande/service VERA public de bundle, export, import ou restore n’est présent. | `MISSING` | Il faut concevoir format, inventaire, import non fusionnel, vérification et restauration, puis les exposer et tester. |

Les lignes `A-01`, `A-02`, `A-04` à `A-06`, `A-08` et `A-10` sont la partie solide de VERA : le mécanisme générique n’est pas une simple renommage d’ARET. Elles ne compensent cependant pas les lignes `PARTIAL` et `MISSING` lorsque le critère est la spécification finale complète.[2] [3] [4]

## 3. Registre des livrables MCP et agents

| ID | Exigence de la spécification | État VERA constaté | Statut | Écart ou condition de clôture |
|---|---|---|---|---|
| `M-01` | API MCP Core couvrant boot/resume, FIND/READ, mémoire, evidence, work, capabilities et transport. §24. | Le serveur expose neuf tools : catalogue, run capability, execution, artifact, validation, admission, gate, acknowledge resume et sync. | `PARTIAL` | Les tools demandés `mmu_boot`, `restore`, `get_front`, `find`, `read`, `append_knowledge`, work CRUD, export/import/bundle et doctor ne sont pas exposés. |
| `M-02` | MCP compiler : profil+packs+catalogues+policies+integration → outils, instructions, hooks, config, docs et package reproductibles. §25. | Manifest, instructions, intégration et hook-plan déterministes sont compilés et hashés depuis le store. | `PARTIAL` | Les Domain Packs, playbook, catalogues de gates/policies externes, outils projet générés, documentation dérivée et package MCP complet ne sont pas compilés. |
| `M-03` | Instructions générées : doctrine + playbook + capability rules + policy summary + resume protocol. §26. | Doctrine Core et capabilities du manifeste sont générées et liées à `mcp_build_hash`. | `PARTIAL` | Le compilateur n’importe volontairement ni playbook, ni Pack, ni profil de policies/resume ; quatre des cinq sources requises manquent. |
| `M-04` | RuntimeAdapter commun, Claude Code, Cursor, Codex, CLI générique et extensibilité. §27. | Adapters déclarés : Claude local/cloud, Codex, Gemini, Antigravity, generic-mcp. Configuration project-local et hooks contractuels sont testés. | `PARTIAL` | Cursor est absent. Les hooks ne sont pas prouvés dans les hôtes réels ; une application supplémentaire exige un adapter explicite dès qu’un lifecycle est voulu. |
| `M-05` | Preuve qu’un client MCP réel charge, truste, démarre et échange avec le serveur. §§27, 43, annexe B. | Un vrai client MCP stdio est utilisé dans les tests VERA ; les adapters sont installables sous preview/confirmation. | `NOT_PROVEN` | Aucun client hôte réel n’a encore été testé. Claude cloud exige, en plus, preview réel puis deux confirmations distinctes juste avant toute écriture user-scope. |
| `M-06` | Hooks cross-runtime : session start, pre/post compact, pre/post tool, stop selon capacités attestées. §27. | Les plans et wrappers d’adapter sont testés avec JSON/stdin-stdout ; chaque coverage est plafonnée (`MCP_ONLY`, `PARTIAL_LOCAL_TOOLS`, etc.). | `PARTIAL` / `NOT_PROVEN` | Le plan générique ne comporte qu’un `SessionStart` déclaratif. Les hooks riches sont spécifiques aux adapters et restent à constater dans chaque hôte. |

Le serveur MCP est **réel et sécurisé**, non un faux prototype : il refuse notamment commande, chemin, stdout, code de sortie, verdict et artefact fournis par le client. L’écart porte sur l’**étendue de l’API, de la compilation et de la preuve hôte**, pas sur l’existence du transport stdio.[5] [6]

## 4. Registre des livrables CLI, scan et application visuelle

| ID | Exigence de la spécification | État VERA constaté | Statut | Écart ou condition de clôture |
|---|---|---|---|---|
| `U-01` | CLI `mmu init, scan, configure, validate, generate, install, serve, doctor, migrate, export, import, dashboard, upgrade`. §28. | CLI `vmmu` : `identity`, `inspect`, `init`, `scan`, `generate`, `install`, `init-project`, `memory-sync`, et sous-commandes `adapter`. | `PARTIAL` | `serve`, `migrate`, `export`, `import`, `dashboard`, `upgrade`, doctor global et validate/configure globaux sont absents. `adapter doctor` est seulement observationnel. |
| `U-02` | `init` crée profil, playbook, catalogues, mémoire, artefacts et installe l’intégration choisie. §28. | `init-project` prévisualise puis crée exactement quatre fichiers sous `.vera-mmu`; `init` ouvre ensuite la SQLite. | `PARTIAL` | L’initialisation ne crée pas catalogues capabilities/gates/policies, artifacts au sens du template, ni intégration d’agent. Elle ne configure pas le modèle complet. |
| `U-03` | Scan de projet large, sans produire `PROVEN` par défaut. §§28, 30. | Scan borné, sans contenu de fichiers ni écriture ; marqueurs Git, CI, langages, Docker, docs et chemins tests sont `OBSERVED`. | `PARTIAL` | Pas de détection exhaustive de frameworks, dépendances, scripts build, linters, datasets, assets, sous-projets ni configuration sémantique. |
| `U-04` | Recommandation automatique de profil/capabilities/gates modifiables. §31. | Six templates sont sélectionnables manuellement ; aucune recommandation n’est dérivée du scan. | `MISSING` | Il faut un moteur de proposition, avec explication, éditabilité et test de non-promotion. |
| `U-05` | Dashboard/IDE : profil, taxonomie, entités, relations, work, capabilities, gates, policies, resume, agents, preview, validate/generate/install/doctor. §29. | L’application Tauri sélectionne un dossier, scanne, choisit un template/agent, prévisualise puis confirme init, stage et installation, doctor et sync. | `PARTIAL` | Les éditeurs de modèle et le parcours complet ne sont pas implémentés. Le Dashboard web séparé est statique : il importe un `ScanReport` mais n’a pas de bridge local. |
| `U-06` | Capability Builder avec validations de commande, chemins, réseau, timeout, dependencies et validator objectif. §32. | Les contrats sont validés dans le Core, mais aucune interface builder ou édition déclarative utilisateur n’existe. | `MISSING` | Il faut l’éditeur visuel/CLI de capability et ses refus avant génération. |
| `U-07` | Gate Builder, distinction validation technique/sémantique/observation. §33. | Les mécanismes Core sont présents ; la console affiche seulement les résultats d’opérations déjà prévues. | `MISSING` | Il faut un éditeur de gates et une visualisation explicite de leurs types et liens. |
| `U-08` | MCP Preview chiffré, alertes et validation de configuration. §34. | VERA affiche les sorties de preview (manifest/instructions/config/hook-plan) et leurs hashes. | `PARTIAL` | Absence de synthèse read/write/sensitive/network, couverture, alertes de risques, validation globale et explication des zones non couvertes. |
| `U-09` | Import de projet existant : README/docs/ADRs/TODO/CI/tests/config/Git history avec provenance, d’abord `OBSERVED`. §35. | Le scanner ne lit aucun contenu ; `knowledge_source` peut porter provenance sur une knowledge déjà créée. | `MISSING` | Aucun importeur de documents/historique, aucune création de knowledge `OBSERVED` ni flux de revue/provenance. |
| `U-10` | Zéro pollution : intégration sous frontière projet, sans modification du code métier. §36. | Les écritures sont prévisualisées, confirmées, atomiques et project-locales ; les tests M8 valident six domaines. | `PARTIAL` | La frontière est `.vera-mmu/`, non `.mmu/`; l’initialisation ne produit pas encore l’arborescence complète spécifiée. Cette différence de nom n’est pas un risque de sûreté, mais reste un écart contractuel. |

Le parcours visuel actuel est donc un **assistant d’installation sécurisé**, non encore l’IDE de configuration décrit dans la spécification. Il est utile et démarrable, mais ne permet pas à un utilisateur de modéliser intégralement un projet inconnu sans modifier de fichiers à la main.[7] [8]

## 5. Registre de migration, conformance et opérations terminales

| ID | Exigence de la spécification | État VERA constaté | Statut | Écart ou condition de clôture |
|---|---|---|---|---|
| `C-01` | Migration ARET progressive/réversible ; ARET profile/pipelines/playbook/runtime et API compatibles. §37, §44, §57. | Pack ARET séparé, readers/imports bornés, quelques mappings et transport de verdicts existent. | `PARTIAL` | Le registre M4 qualifie M4 `IN_PROGRESS` et M4.EXIT `NOT_ELIGIBLE` : imports complets, preuves/relations/front/bundles, playbook, VCS et parité manquent. |
| `C-02` | Migrations SQL proposées et contraintes : PROVEN, append-only, audit, WAL, confinement. §§38–39. | 38 migrations checksummées ; Core assure FK/WAL, immuabilité, audit et confinement dans son périmètre. | `PARTIAL` | Les objets Front/handoff/bundle et les migrations/compatibilités ARET restantes ne sont pas réalisés ; la numérotation diffère de l’exemple sans être le problème principal. |
| `C-03` | Fixtures : empty, software/web/game/research/data/document/hardware/multi-repo/no-Git/existing, avec tout le cycle. §40. | Six domaines, no-Git, mono/multi-repo et clone SQLite passent dans M8. | `PARTIAL` | Les fixtures ne couvrent pas, par domaine, tout le cycle init→scan→configure→validate→generate→boot/find/read/write/proof/promotion/handoff/compact/resume/bundle/restore/doctor. Projet existant/empty complet ne sont pas démontrés. |
| `C-04` | Sécurité : traversal, shell, paramètres, policy/réseau, hash/HMAC/bundle, identity/profile/resume et mémoire croisée. §41. | Les suites couvrent fortement Core/adapters : entrée fermée, symlinks, hash, HMAC, admission, identity, resume et refus. | `PARTIAL` | Les sécurités de bundle/import/export et de surface CLI/Dashboard inexistantes ne peuvent pas être prouvées avant livraison de ces surfaces. |
| `C-05` | Gates non déclaratives et validators d’état/artefact réels. §42. | La chaîne M3 exige execution/evidence/validation/admission pour une gate `PASS`; `echo PASS` n’est pas une preuve. | `PASS` | Les types de validators restent limités au catalogue actuel. |
| `C-06` | Fresh session, compaction, ack expiré et mémoire corrompue avec dégradation bruyante. §43. | Lifecycle et ack contextualisé sont testés en environnement contrôlé. | `PARTIAL` / `NOT_PROVEN` | La séquence doit encore être observée chez les hôtes réels ; Gemini ne promet pas de post-compaction et Codex ne couvre que les outils locaux. |
| `C-07` | `mmu doctor` machine+humain couvrant identité, profile, schema, SQLite/WAL, artifacts, HMAC, catalogues, policies, runtime, MCP, hooks, resume et VCS. §45. | `vmmu adapter doctor` observe seulement runtime/config adapter et marque host/user scope `NOT_OBSERVED`. | `MISSING` | Un Doctor composite, remédiant et vérifié doit être construit. |
| `C-08` | `profile_hash`, `policy_hash`, `capability_catalog_hash`, `gate_catalog_hash`, `mcp_build_hash`, conservés pour reproductibilité. §46. | Identité profil/workspace et hashes `mcp_build`, instructions, config, hook-plan sont produits. | `PARTIAL` | Les hashes de catalogues/policy/gates du profil complet n’existent pas parce que ces catalogues projet complets n’existent pas encore. |
| `C-09` | Générateur de `MMU_SETUP`, `TOOLS`, `GATES`, `POLICIES`, `ARCHITECTURE`, `MAINTENANCE`. §47. | README, contrat de release et continuité sont documentés manuellement. | `MISSING` | Aucun générateur documentaire dérivé d’un profil. |
| `C-10` | Templates Dashboard pour six domaines avec modèles métier. §48. | Six noms de templates et six fixtures sont fournis. | `PARTIAL` | Aucun modèle d’entités/capabilities/gates enrichi n’est livré dans un Dashboard configurateur. |
| `C-11` | Rapport de générateur MCP : surface, coverage et zones non couvertes. §49. | Preview déterministe avec manifests/hashes. | `MISSING` | Il faut calculer la couverture et rendre les manques visibles, sans inventer de capacité. |
| `C-12` | Baseline, matrice de découplage, invariants, lots test-first et traçabilité. §§50–53. | Baseline ARET, `DECOUPLING_MATRIX.md`, `INVARIANTS.md`, workplan, mémoire, journal et commits atomiques sont présents. | `PASS` pour la méthode | Le registre signale lui-même les couplages ARET non clos ; la méthode ne remplace pas leur réalisation. |

## 6. Delivery, compatibilité et Definition of Done

| ID | Exigence de la spécification | État VERA constaté | Statut | Écart ou condition de clôture |
|---|---|---|---|---|
| `D-01` | Au moins cinq domaines, no-Git, multi-repo, projet vide et existant importable. §54. | Six domaines et topologies no-Git/mono/multi/clone sont validés. | `PARTIAL` | L’import réel d’un projet existant et le cycle complet d’un projet vide restent absents. |
| `D-02` | Dashboard génère un profile valide, profil déterministe, MCP reproductible, doctor passe, installation réparable automatiquement. §54. | Bootstrap et preview MCP déterministes, init/stage/install confirmés. | `PARTIAL` | Dashboard complet, doctor composite, réparation et model editor sont absents. |
| `D-03` | Packaging pip/uvx/local, container, standalone, vendored runtime, sans Python requis pour runtime non-Python. §56. | Package Python `vera-mmu`, CLI PyInstaller et app Tauri avec sidecar sont produits ; Linux CLI/AppImage/DEB sont démarrés localement et sur runner Ubuntu. | `PARTIAL` | Le nom est `vera-mmu`/`vmmu`, pas `universal-dev-mmu`/`mmu`; container et mode vendored MCP général ne sont pas fournis ; la preuve Windows MSI est `OUT_OF_SCOPE`. |
| `D-04` | Compatibilité transitionnelle : aliases `aret_*`, `ARET://` lecture, nouveaux `mmu://`. §57. | Parser `ARET://` isolé dans le Pack et adressage nouveau `vera://`. | `PARTIAL` | Pas d’aliases MCP `aret_*`, pas de lecteurs de ressources ARET complètes, pas de `mmu://`; parité non admise. |
| `D-05` | Préversion/release sûre et signature avant diffusion stable. §§54–56. | rc.4 est une GitHub Pre-release publique, hashes/manifests vérifiés, explicitement non signée. | `PARTIAL` | Signature Authenticode et signature Linux, validation utilisateur complète et stable release restent requis. |
| `D-06` | Résultat attendu : projet inconnu → découverte → modèle éditable → validation → MCP déterministe → intégration → tests conformance. §§59–60, annexe B. | Découverte structurelle, template manuel, preview déterministe et intégration project-local sont possibles. | `MISSING` comme parcours complet | Le modèle n’est pas découvert/recommandé/éditable intégralement, les documents ne sont pas importés, la CLI/API et Doctor attendus sont incomplets, et les hôtes réels ne sont pas prouvés. |

## 7. Éléments livrés, lacunes produit et validations différées

### Éléments effectivement livrés et solides

Le Core universel — identité, workspace, SQLite, entités, relations, knowledge, provenance bornée, work graph, gates, execution, evidence, validation, admission et proof — est livré dans un périmètre fail-closed et couvert par la suite actuelle. Les six templates de domaine valident un chemin project-local sans dépendance ARET, y compris sur no-Git et multi-repo. Le compilateur MCP produit un manifeste, des instructions, une intégration et un plan de hook déterministes. L’application desktop assure le parcours local prudent : sélectionner, scanner, initialiser en preview, générer, stage, prévisualiser/installer et diagnostiquer. Enfin, les voies Linux distribuées démarrent réellement sous contrôle.[2] [6] [7] [8]

### Lacunes produit qui empêchent la clôture de la spécification

Le travail restant n’est pas une retouche Windows. Les lacunes structurantes sont : le Project Profile riche et ses catalogues éditables ; les runners génériques déclaratifs ; le bundle/export/import/restore ; l’API MCP et la CLI de gestion de mémoire/work complètes ; le Dashboard configurateur ; l’import de projet existant avec provenance ; Doctor composite ; génération documentaire ; rapport de couverture MCP ; compatibilité/migration ARET complète ; VCS multi-provider et politique de compatibilité `mmu://`/`aret_*`. Ces lignes sont `PARTIAL` ou `MISSING` indépendamment de tout test Windows.

### Validations externes différées, à ne pas confondre avec des lacunes de code

Les adapters Claude local/cloud, Codex, Gemini, Antigravity et generic-mcp ont des contrats testés, mais chaque hôte doit encore démontrer que sa configuration est prise en compte, que le trust est accordé, que le serveur démarre et que les événements lifecycle arrivent. Ces sont des preuves `NOT_PROVEN`, non des prétextes pour déclarer le mécanisme absent. Claude Cloud reste soumis à son protocole de preview et de doubles confirmations avant l’unique écriture user-scope.[9]

| Lot futur | Nature | Premier résultat exigé avant tout `PASS` |
|---|---|---|
| Modèle/CLI/Dashboard | Lacune produit | Sur un projet inconnu : scan, recommandation éditable, validation, génération et installation de l’ensemble déclaré. |
| Bundle/import/export/restore | Lacune produit | Manifest hashé, import non fusionnel, mismatch identity refusé, restauration et tests d’altération. |
| ARET compatibility | Lacune produit et parité | Toutes les gates M4.EXIT vertes ; aucun `SPLIT`, `UNKNOWN` ou import partiel masqué. |
| Hôtes MCP réels | Preuve différée | Trust/configuration, connexion stdio et événement lifecycle observés séparément par hôte. |
| Release stable | Preuve/distribution différée | Signatures propriétaires, vérification de signature et validations système utilisateur. |

## 8. Décision de complétude

La réponse rigoureuse à la question « VERA-MMU est-il livré totalement, hors test Windows ? » est **non**. Il serait exact de le décrire comme une **préversion universelle à Core robuste, intégration MCP/desktop prudente et conformance multi-domaines déclarative**, mais inexact de le présenter comme l’intégralité du produit de la spécification finale.

La prochaine décision n’est pas de lancer des agents réels ni de compléter au hasard. Il faut d’abord choisir l’ordre des lacunes de produit listées au chapitre 7, avec un lot et une gate de sortie propres. Tant que ces lignes restent ouvertes, la Definition of Done de la spécification et son Annexe B ne sont pas satisfaites.[1] [9]

## Références

[1]: ../../../../upload/UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md "Spécification finale Universal Dev-MMU — source propriétaire auditée, SHA-256 ci-dessus"
[2]: ../../../tests/test_m3_exit.py "Chaîne Core terminale M3"
[3]: ../../../docs/INVARIANTS.md "Invariants non régressifs VERA-MMU"
[4]: ../../../src/vera_mmu/project_bootstrap.py "Initialisation project-local et profil minimal"
[5]: ../../../src/vera_mmu/mcp_server.py "Façade MCP réellement exposée"
[6]: ../../../src/vera_mmu/mcp_manifest.py "Manifeste MCP déterministe et hashé"
[7]: ../../../src/vera_mmu/desktop_bridge.py "Bridge desktop fermé et opérations allowlistées"
[8]: ../../../apps/desktop/ui/src/DesktopConsole.tsx "Console Tauri réellement embarquée"
[9]: ../M4_COMPLETION_REGISTER.md "Registre de clôture M4 — compatibilité ARET non achevée"
[10]: ../../../tests/test_m8_domain_conformance.py "Conformance déclarative multi-domaines et topologies"
[11]: ../../../src/vera_mmu/__main__.py "Surface CLI publique réellement distribuée"
[12]: ../../../src/vera_mmu/memory_sync.py "Synchronisation Git project-local bornée"
[13]: ../../../src/vera_mmu/mcp_instructions.py "Instructions MCP actuellement générées"
[14]: ../../../src/vera_mmu/mcp_hooks.py "Plan de hook déclaratif actuellement généré"
