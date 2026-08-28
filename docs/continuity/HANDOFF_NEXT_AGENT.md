# Handoff — Reprise complète de VERA-MMU

**Document destiné au prochain agent de travail.**

**Date du handoff :** 2026-08-28

**Dépôt actif :** `https://github.com/aciderix/vera-mmu`

**Répertoire local de référence :** `/home/ubuntu/vera_mmu_workspace/vera-mmu`

**Branche :** `main`

**Dernier état publié et vérifié :** `68fa91504a9b153bb57ac6b2417fd7d4cc3e4788`

**Worktree au moment du handoff :** propre.

## 1. Mission et règles non négociables

VERA-MMU doit devenir un **Core Python réellement project-agnostic, proof-oriented et fail-closed**. Il ne s’agit pas de renommer ARET-MMU. Le mécanisme générique doit rester dans `src/vera_mmu`; toute sémantique de reverse engineering doit rester dans `src/vera_mmu/domain_packs/aret/` ou dans des capabilities explicitement séparées.

Les dépôts `ARET-MMU` et `Automatic-reverse-engineering-toolkit` sont des références strictement en lecture seule. Ne jamais les modifier. Ne jamais introduire dans le Core les concepts, outils ou corpus ARET tels que ARET, PE32, Wine, MinGW, Ghidra, lifting, transpilation, binaires ou fonctions machine.

Préserver partout SQLite canonique, migrations checksumées, append-only, audit trail, séparation knowledge/evidence/proof, statuts épistémiques, HMAC/PROVEN, distinction FIND ≠ READ, identité project-bound, politiques/capabilities, bundles, Active Front, handoff/resume, reprise anti-deadlock, transport authentifié, atomicité et refus fail-closed.

Toute écriture sensible suit le cycle obligatoire : **preview → vérification de fraîcheur → confirmation explicite → opération atomique ou refus**. Une erreur, une divergence, un symlink ambigu, une preuve absente ou un état `UNKNOWN` ne doit jamais devenir silencieusement `PASS`.

## 2. État livré et publié

Le commit distant `68fa915` et tous ses ancêtres contiennent les lots réalisés avant ce handoff. Le distant a été vérifié par `git fetch`, `git ls-remote` et l’API GitHub : `HEAD` local et `origin/main` sont identiques à `68fa915`. Le dernier push a été un fast-forward normal; aucune force-push n’a été effectuée.

La dernière régression Python complète observée après les derniers changements validés est **`601 passed in 65.51s`**. Des validations ciblées complémentaires ont également passé, notamment le trajet MCP `mmu://` avec **`9 passed in 10.81s`**, le bridge/workspace avec **`21 passed in 1.30s`**, le build React et les deux tests Tauri natifs.

Les dépôts ARET de référence étaient propres et non modifiés lors du dernier contrôle.

## 3. Capacités déjà livrées

Le Core dispose notamment de `MemoryStore`, de l’identité et du workspace project-bound, des migrations SQLite, knowledge, provenance bornée, entities, symbols, relations, work graph, executions, evidences, validations, admissions, proofs, gates, policies, capabilities et diagnostics.

Les lots M11 déjà livrés comprennent les bundles/import/restore disponibles dans leur périmètre local validé, transports bundle/import/Doctor, lectures exactes H/I/J, traversal relationnel BFS borné K, READ exact symbol L, historiques compacts execution N et evidence O, rapport de couverture dérivé E, bridge `mmu://` input-only FA, statut VCS local FB, vue Dashboard d’état DA, builder Capability DC, builder structure de Gate DD2, builder policy de Gate DD1 et garde/rebind Profile contrôlé.

Le Dashboard/Tauri utilise un bridge Python stdio authentifié par nonce. Les commandes Rust et la WebView ne doivent rester que des façades; la logique métier appartient au Core. La console dispose de previews et confirmations pour les écritures prises en charge, sans exposer au client la fabrication de verdicts, admissions ou preuves.

La documentation dérivée est générée depuis les sources Core et liée à l’identité du projet. Elle est disponible comme lecture via Core, CLI, MCP stdio et Dashboard. Les catalogues absents sont signalés et non inventés.

L’alias `mmu://` est accepté uniquement comme **entrée de lecture** dans le chemin prévu. Les adresses persistées et toutes les sorties restent `vera://`. Il n’existe pas encore de migration générale d’adresses legacy.

## 4. Ce qui reste à terminer globalement

Le statut global de la spécification demeure **`NOT_DONE`**. Les livraisons ci-dessus sont des sous-lots prouvés, pas la clôture intégrale du produit décrit par la spécification.

### 4.1 Dashboard configurateur global

Construire l’éditeur complet du modèle de projet : taxonomie, entities, relation types, relations, work graph, capabilities, gates, policies, playbook, Front, resume, agents, intégrations, previews, validate/generate/install/Doctor. Le Dashboard actuel est un assistant sécurisé pour les surfaces livrées, pas encore l’IDE de configuration complet.

Tout nouvel éditeur doit utiliser des opérations Core canoniques, être project-bound et rester sans privilège implicite. Ajouter des tests UI/bridge/Tauri réels, notamment les champs fermés, l’identité de session, la fraîcheur et l’absence de chemins directs vers SQLite.

### 4.2 Migrations structurelles et physiques du Profile

Le rebind livré couvre l’identité bornée, le nom, le domaine et la description. L’ancrage Profile accepte désormais exactement un emplacement régulier et non symlinké parmi `.vera-mmu/project.yaml` et `project.yaml` racine; deux profils concurrents sont refusés.

La migration physique de `workspace.root`, `workspace.additional_roots`, `storage.memory_dir`, `storage.sqlite_file`, `storage.artifacts_dir` et des catalogues reste à implémenter. Elle doit inclure le Profile, `capabilities.yaml`, `gates.yaml`, `policies.yaml`, `agent-profiles.yaml`, `playbook.md`, `sync-policy.json`, SQLite, WAL/SHM et les sous-répertoires créés ensuite.

Contrat minimum : préflight des racines et cibles sans symlink ni chevauchement; preview complet avec inventaire et hashes; journal durable hors runtime; fermeture SQLite et checkpoint WAL; renommages atomiques same-filesystem; réalignement d’identité audité; reprise Doctor qui ne devine jamais; refus de divergences; validation du nouveau store, FK, intégrité, hashes, audit et absence de source résiduelle. Ne jamais commencer par déplacer des fichiers sans ce protocole et des tests d’interruption.

### 4.3 Doctor composite et reprises

Le Doctor doit couvrir identité, Profile, schema, SQLite/WAL, artefacts, HMAC, catalogues, policies, runtime, MCP, hooks, resume et VCS, avec distinction machine/humain. Les contrôles doivent être read-only par défaut. Une réparation doit être un flux séparé, prévisualisé, confirmé, journalisé et reprenable; aucun chargement de Dashboard ne doit réparer implicitement.

La reprise du journal Profile est livrée dans un périmètre contrôlé. Il faut encore raccorder proprement la reprise physique runtime/storage et prouver les interruptions, les divergences, les fichiers manquants, les cibles déjà occupées et les WAL/SHM incohérents.

### 4.4 Documentation, couverture et génération

Compléter le générateur documentaire pour qu’il couvre de façon déterministe les six documents requis : `MMU_SETUP`, `TOOLS`, `GATES`, `POLICIES`, `ARCHITECTURE`, `MAINTENANCE`, depuis Profile, packs, catalogues et policies réellement disponibles. Ajouter le rapport de générateur MCP avec surface, coverage, risques et zones non couvertes. Produire un export confirmé uniquement lorsque son contrat de chemin, hash, atomicité et reprise est défini.

La documentation ne doit jamais présenter une surface `PARTIAL`, `MISSING` ou `NOT_PROVEN` comme entièrement livrée. Maintenir `PROJECT_MEMORY.md`, `ENGINEERING_LOG.md`, `UNIVERSALIZATION_WORKPLAN.md` et les artefacts de preuve en append-only.

### 4.5 API MCP et CLI complètes

Compléter les surfaces prévues par la spécification : boot/resume, restore, Front, FIND/READ, append knowledge, work CRUD, bundles, export/import, Doctor, serve et configuration. Chaque handler MCP doit rester une façade du Core et appliquer des enveloppes strictes, nonce/session si nécessaire, champs exacts et absence d’entrées client dangereuses.

La CLI `vmmu` actuelle ne couvre pas encore tout le contrat `init`, `scan`, `configure`, `validate`, `generate`, `install`, `serve`, `doctor`, `migrate`, `export`, `import`, `dashboard`, `upgrade`. Ajouter les commandes par petits lots test-first, avec sorties déterministes et refus explicites.

### 4.6 Import de projet existant et provenance

Implémenter l’import project-local des README, documentation, ADR, TODO, CI, tests, configuration et historique quand disponible, avec provenance générique, hash, révision, chemin, lignes/sections et statut initial `OBSERVED`. Ne jamais transformer un document importé en `PROVEN` automatiquement. Prévoir revue, supersession, altération et import non fusionnel.

### 4.7 Capability Engine et Gate Builder complets

Les builders actuels couvrent des déclarations bornées et les Gates existantes/structures/policies prévues. Il reste à fournir l’éditeur complet des capabilities et Gates, incluant validations de commandes, chemins, réseau, timeout, dépendances, validators objectifs et distinction validation technique, sémantique et observationnelle. Aucun client ne doit pouvoir fournir directement commande, verdict, sortie, code de retour, admission ou preuve.

### 4.8 Bundles et restauration complète

Formaliser et exposer le format universel de bundle : manifest hashé, inventaire, identité project-bound, intégrité, import non fusionnel, mismatch refusé, restauration, rollback et tests d’altération. Les opérations doivent couvrir les transports et les erreurs partielles. Un bundle ou artefact présent dans SQLite ne devient pas automatiquement une preuve.

### 4.9 Active Front, playbook et resume

Rendre publics et configurables le Front actif, handoff, playbook project-specific, resume template et rituel générique, tout en conservant Resume Guard, expiration d’acquittement, compact, reprise et statuts épistémiques. Composer doctrine Core et contexte projet sans fusionner les règles ARET dans le Core.

### 4.10 VCS multi-fournisseur — à étudier seulement après les livraisons demandées

Le lot 5 doit être étudié après les travaux de conformité ci-dessus, sans implémentation prématurée. L’étude devra comparer une abstraction `VersionControlProvider` pour Git, Mercurial, SVN et NoVCS, les capacités d’observation locale/distante, les permissions, les erreurs, les états `UNKNOWN/OBSERVED`, les politiques réseau, les preuves et la synchronisation project-local.

Il faudra distinguer clairement observation VCS, opérations locales, opérations distantes et preuve d’hôte réel. Ne pas déduire qu’un provider est disponible parce qu’un exécutable porte le bon nom. Les dépôts ARET restent uniquement des références de comparaison.

## 5. Ordre obligatoire de continuation

Le nouvel agent doit reprendre par une baseline réelle : `git status`, `git log`, `git fetch origin main`, comparaison merge-base, inventaire des tests, vérification des dépôts ARET non modifiés et lecture des registres de continuité.

Ensuite, terminer les sous-lots de modèle/Dashboard et la migration physique Profile/runtime par contrats test-first. Puis compléter API MCP/CLI, import existant, bundles/export/import/restore, Front/playbook/resume, documentation générée et coverage MCP. Les compatibilités legacy doivent être ajoutées uniquement lorsqu’un comportement d’entrée/sortie et une stratégie de migration sont démontrés.

Après chaque sous-lot : tests ciblés, build React, tests Tauri, régression Python complète, `git diff --check`, scan de frontière Core, artefact probatoire, mémoire et journal append-only, puis commits fonctionnel et documentaire séparés. Aucun push ne doit avoir lieu avant le contrôle de divergence et la décision explicite de publication.

## 6. Second contrôle de conformité obligatoire

**Une fois que tout le travail de mise en conformité avec `M11_—_Audit_exhaustif_de_complétude_face_à_la_spéc.md` sera terminé, le nouvel agent doit effectuer un second check complet face à `UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md`.**

Ce second check doit repartir de la spécification source, vérifier chaque ligne `A-*`, `M-*`, `U-*`, `C-*` et `D-*`, recalculer les statuts `PASS`, `PARTIAL`, `MISSING`, `NOT_PROVEN` et `OUT_OF_SCOPE`, vérifier les preuves proportionnées et produire un nouvel artefact daté avec hash de la spécification et commit VERA audité.

Il ne faut pas déduire la conformité d’une compilation, d’un nombre de tests ou d’un nom de fichier. Toute exigence nécessitant une preuve hôte, une signature, un client réel, une migration ou une parité doit rester non close jusqu’à observation correspondante.

## 7. Audit final obligatoire face à ARET-MMU

**Après ce second contrôle de conformité, effectuer un audit comparatif complet face à ARET-MMU afin de vérifier que rien n’a été perdu ou dégradé pendant la transition vers un MCP universel.**

Cet audit doit être séparé du contrôle de conformité à la spécification. Il doit comparer, comportement par comportement et garantie par garantie : mémoire SQLite, migrations, append-only, audit, knowledge/evidence/proof, HMAC/PROVEN, admissions, gates, FIND/READ, Active Front, handoff/resume, compact/reprise, bundles/restore, transports, policies, capabilities, erreurs fail-closed, sécurité des chemins/symlinks, identité project-bound et intégrations MCP.

Pour chaque différence, classer explicitement : garantie conservée; amélioration générique; changement intentionnel documenté; compatibilité temporaire; régression; ou comportement non comparable. Tester les scénarios ARET pertinents avec le dépôt ARET en lecture seule. Ne jamais copier une dépendance ARET dans le Core pour obtenir une comparaison plus facile. Toute régression doit bloquer la déclaration de conformité universelle jusqu’à correction ou décision documentée.

Le résultat attendu est un rapport de non-régression comparatif avec baselines, matrices, preuves, limites et verdict. Le verdict ne doit pas être `PASS` si une garantie essentielle est absente, dégradée ou seulement supposée.

## 8. Règles GitHub et arrêt sûr

Utiliser GitHub via `gh` et respecter le dépôt `aciderix/vera-mmu`. Avant chaque push : `git fetch origin main`; vérifier que `git merge-base HEAD origin/main == origin/main`; vérifier `git status` propre; vérifier les tests et artefacts; pousser sans force; puis vérifier le SHA via `git ls-remote` et l’API GitHub.

Ne jamais pousser `ARET-MMU` ou `Automatic-reverse-engineering-toolkit`. Ne jamais inclure secrets, tokens, mots de passe, cookies ou données personnelles dans le code, les preuves ou les journaux.

## 9. Fichiers de référence prioritaires

| Fichier | Rôle |
|---|---|
| `docs/continuity/PROJECT_MEMORY.md` | Décisions append-only |
| `docs/continuity/ENGINEERING_LOG.md` | Journal append-only |
| `docs/continuity/UNIVERSALIZATION_WORKPLAN.md` | Plan vivant et statuts |
| `docs/continuity/artifacts/m11_specification_completeness_audit_2026-08-27.md` | Audit exhaustif M11 initial |
| `docs/continuity/artifacts/m11_profile_physical_migration_design_2026-08-27.md` | Contrat de conception migration physique |
| `docs/INVARIANTS.md` | Invariants de sécurité et de confiance |
| `UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md` | Spécification finale source à recontrôler |
| `src/vera_mmu/` | Core générique |
| `src/vera_mmu/domain_packs/aret/` | Spécialisation ARET isolée |
| `apps/desktop/` | Tauri, bridge et Dashboard |

## 10. Définition de fin du handoff

Le handoff est réussi si le nouvel agent peut reprendre sans hypothèse cachée, distinguer les sous-lots livrés des lacunes globales, terminer les migrations et surfaces manquantes par preuves, effectuer le second check demandé face à la spécification finale, puis réaliser l’audit comparatif complet face à ARET-MMU avant toute déclaration de transition universelle réussie.
