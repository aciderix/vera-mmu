# Travail restant — VERA-MMU

**Établi le :** 2026-09-14
**Révisé le :** 2026-09-18 — A1, B1 à B7 et C2 clos ; B8 à B11 ouverts.
**Révisé le :** 2026-09-15 — A1, B1 à B5 et C2 clos ; B6 à B11 ouverts.
**Révisé le :** 2026-09-14 — décision du propriétaire : le Dashboard configurateur est livré
entièrement, il n’est plus hors périmètre.
**Commit de référence :** branche `claude/youthful-fermat-b0h84l`
**Méthode :** chaque ligne est vérifiée contre le code, jamais reprise d’un registre.
**Suite :** `856 passed, 69 subtests passed` côté Core et `30 passed` côté interface. Le décompte
`798 + 10` est attesté sur Linux x64 **et** Windows x64 (run `desktop-packaging.yml` #48) ; les
ajouts de B4 à B7 restent à attester sur Windows.

Ce document énumère ce qui reste, dans l’ordre où je le ferais, avec pour chaque tâche son
périmètre exact, son critère de sortie vérifiable et ce qui la bloque s’il y a lieu. Il ne
répète pas ce qui est livré : voir `ENGINEERING_LOG.md` (LOG-0277 à LOG-0284).

## Règle de mise à jour

Une tâche n’est cochée que lorsque son critère de sortie a été **exécuté**, pas lu. Une tâche
partiellement faite reste ouverte avec une note ; elle ne devient jamais « faite en partie ».

---

## A. Clos

### A1 — Matrice native Windows x64 et Linux x64 — **FAIT**

**Run #47 sur `ec1fd93`, le 15 septembre 2026 : les deux runners sont verts**, quatorze étapes
chacun — suite de conformité, sidecar natif, archive CLI autonome, AppImage et `.deb` côté Linux,
NSIS et MSI côté Windows. C’est le premier passage vert de ce workflow.

Le rouge était antérieur à ce lot — Linux tombait déjà sur les mêmes trois tests sur `main` au
commit `afc931f`, et Windows y portait seize échecs. Quatre causes racines l’expliquaient.

1. **`os.fsync` sur une poignée en lecture seule** — huit échecs Windows. `bundles.py` rouvrait
   l’archive en `"rb"` avant de la remplacer ; Windows ne valide qu’une poignée ouverte en
   écriture, et l’`OSError` remontait en « Écriture atomique du bundle impossible », masquant sa
   propre cause. *Corrigé :* `"rb+"`.
2. **Séparateur natif écrit dans un format déclaré portable** — quatre échecs plus une transition
   en cascade. `_relative()` refuse la barre inverse dans `copy_progress.path`, et l’écrivain
   émettait pourtant `os.sep` : le module refusait son propre journal. *Corrigé :* six sites en
   `as_posix()`, et un test épingle que tout chemin journalisé repasse son validateur.
3. **Poignées SQLite laissées ouvertes par les fixtures** — cinq `WinError 32`. `with
   sqlite3.connect(...)` valide la transaction mais **ne ferme pas** la connexion. *Corrigé :*
   six fixtures par `closing()`. J’ai d’abord cru que cette fuite expliquait aussi Linux ; la
   mesure a montré que non, et c’est pour cela que le refus a été instrumenté plutôt que conclu.
4. **Le checkpoint WAL repliait sur rien** — les trois échecs Linux. Le refus instrumenté a rendu
   `busy=0, log=-1, checkpointed=-1`, la réponse de SQLite quand le pager ne détient aucun objet
   WAL : déclarer `journal_mode=WAL` ne l’ouvre pas, il faut une lecture. Le checkpoint retournait
   donc `OK` sans rien replier, indistinguable d’un vrai repli pour qui n’examine que `busy`.

**La quatrième portait plus loin que son test.** Trois sites checkpointaient. `bundles` n’examinait
que `busy` — un bundle pouvait être pris par-dessus un WAL jamais replié, contre I010.
`memory_sync` checkpointait sur une connexion neuve avant toute lecture — il pouvait committer
dans Git une mémoire incomplète. Aucun des deux ne faisait échouer de test : ils rendaient un
verdict faux en silence, ce qui est pire qu’un rouge. *Corrigé :* un `checkpoint_wal()` unique
dans `store.py` ouvre le WAL par une lecture avant de replier, et les trois appelants refusent
tout ce qui n’est pas `busy == 0` **et** `log == 0`.

**Ce que ce run autorise désormais à dire :** le README ne porte plus la restriction « décompte
relevé sur Linux x64 ». La suite — `750 passed, 55 subtests passed` — est attestée sur les deux
plateformes.

---

## B. Dashboard configurateur complet (§29 à §34)

**Décision actée :** le Dashboard est livré **entièrement**. Les sections §29 à §34 ne sont plus
une cible optionnelle ni une dette d’un autre produit : elles sont du travail planifié ci-dessous.

**État réel du départ.** `apps/desktop/ui/src/DesktopConsole.tsx` est une console d’une seule
page, huit panneaux, ~207 lignes, adossée à 24 méthodes de bridge. Elle couvre aujourd’hui, du
parcours en dix-huit étapes : 1 et 2 (scan), 4 partiellement (choix d’un template au moment de
l’initialisation), 9 et 10 sous forme déclarative bornée, 13 (choix d’un agent profile et de son
adapter), et 15 à 18 (générer, installer, doctor). Le reste n’existe pas.

**Manquent donc :** l’étape 3 (recommandation de profil), 5 à 7 (taxonomie, entités, relations),
8 (Work Graph), 11 (policies), 12 (Resume), 14 (MCP Preview avec métriques et alertes), et la
forme complète de 9 et 10 décrite par §32 et §33.

**Trois règles qui tiennent pour tous les lots ci-dessous.**

1. Aucun écran n’écrit directement. Chaque mutation passe par une méthode de bridge et par le
   cycle **preview → vérification de fraîcheur → confirmation explicite → écriture atomique ou
   refus**. Un écran qui écrirait sans preview serait un contournement, pas une commodité.
2. L’interface ne fournit jamais une commande, un chemin, une URL ou un profil de runner libre.
   Elle compose des déclarations à partir de ce que le Core expose (I008).
3. Toute logique de validation vit dans le Core et est testée en Python. L’interface l’affiche ;
   elle ne la réimplémente pas en TypeScript, sans quoi les deux divergeront.

**Le préalable des huit étapes visuelles est le socle B1 :** sans machine à états, les écrans
ajoutés s’empileraient dans la page unique actuelle et le parcours resterait implicite.

### B1 — Socle : le parcours en dix-huit étapes — **FAIT**

**La dérivation.** `wizard.py` déclare les dix-huit étapes de §29.2 dans l’ordre, chacune avec son
critère d’entrée et l’évidence qui la termine, et dérive leur état **du projet lui-même** :
Project Profile, catalogues, `generated/`, configuration hôte. Aucun drapeau conservé nulle part.
Exposé en CLI (`wizard`), bridge (`wizard.state`), commande Rust, et panneau de console.

**Un quatrième état, contre ce que ce document annonçait.** Il prévoyait `BLOCKED`, `AVAILABLE`,
`COMPLETED`. Six étapes — scanner, détecter, proposer, prévisualiser, valider, diagnostiquer — ne
laissent **aucune trace sur le disque**. Les dire `COMPLETED` aurait inventé la seule chose qu’on
ne peut pas voir. Elles sont `NOT_OBSERVABLE`.

**Le gouvernail.** Quatre panneaux — capabilities, structure de gate, policy de gate, intégration
MCP — se ferment désormais quand leur étape est `BLOCKED`, en affichant **la raison du Core**, et
leurs boutons sont désactivés. Ce n’est plus une page de panneaux indépendants.

**Le lanceur de tests d’interface, qui manquait.** `apps/desktop` n’en avait aucun ; `vitest` est
installé, `pnpm test` ajouté, et `build` enchaîne désormais `tsc --noEmit && vitest run && vite
build`. Comme `beforeBuildCommand` vaut `pnpm build`, la CI l’exécute déjà sur les deux runners ;
une étape explicite a été ajoutée au workflow pour échouer tôt plutôt qu’au moment du bundle.
Le verrou de dépendances a été vérifié par `rm -rf node_modules && pnpm install --frozen-lockfile`
— exactement ce que consomme la CI.

**La seule logique de parcours que l’interface a le droit de porter** vit dans `journey.ts` :
lire le payload, et dire quel panneau une étape ouvre. Tout le reste est dérivé côté Core et
seulement affiché — le réimplémenter en TypeScript laisserait les deux diverger, et c’est
l’interface qui finirait par mentir.

**Deux refus épinglés par les tests d’interface :** un état inconnu dans le payload est lu
`BLOCKED` et non comme une progression, et un parcours **non encore lu ne ferme aucun panneau** —
verrouiller sans avoir demandé serait agir sur une information absente.

**Preuve :** `tests/test_wizard.py`, seize tests côté Core — ordre des étapes, ce que
l’initialisation termine réellement, installation bloquée puis disponible puis terminée, absence
d’écriture, état **redérivé à l’identique** après suppression du runtime, catalogue cassé qui
bloque son étape sans faire tomber le parcours, racine symlinkée refusée. Et
`apps/desktop/ui/src/journey.test.ts`, dix tests côté interface, dont le mordant a été vérifié en
cassant la règle de blocage : le test tombe. `tsc --noEmit`, `vitest run`, `vite build` et
`cargo check` passent.

**Une ligne morte retirée en chemin :** un garde sur le parcours vide que le cas suivant absorbait
déjà. Le constat vient de la vérification de mordant — le test ne tombait pas en la supprimant,
parce que le comportement était identique.

### B2 — Scanner de projet complet (§30) — étapes 1 et 2 — **FAIT**

**Correction d’une erreur de ce document.** Il annonçait « au minimum quinze catégories ». §30 en
énumère **quatorze** : gestionnaire de version, langages, frameworks, gestionnaires de
dépendances, scripts de build, suites de tests, linters, CI, Docker, documentation, datasets,
assets, sous-projets, fichiers de configuration. Le décompte vient d’être fait sur le texte.

**Écart mesuré au départ : six sur quatorze.** VCS, CI, documentation, conteneur, chemins de test,
et les langages — mais déduits d’un manifeste de dépendances, donc confondus avec la catégorie
« gestionnaires de dépendances » que §30 énumère séparément. Frameworks, scripts de build,
linters, datasets, assets, sous-projets et fichiers de configuration n’existaient pas.

**Livré.** Le scanner vit dans `project_scan.py`, en tables déclaratives : marqueurs de
répertoire, marqueurs de nom exact, motifs de nom, extensions de source, extensions non-source,
manifestes imbriqués. Une catégorie manquante se voit en lisant une table, pas en dépliant des
conditions.

**Deux distinctions que §30 impose et que le code porte maintenant.** Un manifeste n’est pas un
langage : `package.json` seul déclare un gestionnaire de dépendances et **aucun** langage ; c’est
l’extension d’un fichier source qui nomme le langage. Et un manifeste imbriqué est un
sous-projet, celui de la racine non.

**Modèle du rapport, passé en `vera-scan-report/v2`.** `kind` porte la catégorie, `marker` ce qui
a été reconnu, `occurrences` combien de fois. Une ligne par marqueur, pas par fichier : quarante
modules Python font **une** observation sur Python portant son compte. Le rapport reste borné,
comparable d’un run à l’autre, et exploitable tel quel par §31.

**Ce que le scanner reste.** Il ne lit aucun contenu — un test le prouve en réécrivant les
fichiers et en exigeant un rapport identique —, ne suit aucun symlink, ne démarre aucun processus,
n’atteint aucun réseau, et n’émet que des `OBSERVED`.

**Preuve :** `tests/test_project_scan.py`, une fixture par catégorie et douze tests. Le test de
couverture échoue dès qu’une catégorie exigée cesse d’être détectée — vérifié en retirant les
marqueurs de framework. Passé sur ce dépôt : vingt-sept observations, dix catégories, les quatre
absentes l’étant réellement.

### B3 — Recommandation automatique de profil (§31) — étape 3 — **FAIT**

**Livré :** `project_recommendation.py` lit un `ScanReport/v2` et propose un template, un jeu de
capabilities et les gates que ces capabilities pourraient satisfaire. Exposé en CLI (`recommend`)
et par le bridge (`project.recommend`).

**Ce que la spécification impose et que le code porte.** «L’utilisateur peut modifier chaque
élément» : le payload est `PROPOSED`, `mutation: NONE`, et chaque proposition porte
`editable: true`. Chaque élément cite les observations qui le soutiennent — une recommandation
qui ne peut pas dire pourquoi est une opinion.

**Trois refus explicites, plus intéressants que les propositions elles-mêmes.**

1. **Aucune commande, aucun chemin, aucune URL, aucun runner.** Nommer une capability `lint`
   n’est pas dire ce que `lint` exécute : la première est une observation sur la forme du projet,
   la seconde une décision que seul son propriétaire prend (I008). Un test parcourt tout le
   payload et échoue sur la moindre clé interdite.
2. **Rien n’est déduit que le scan n’ait observé.** L’exemple de §31 propose un `build` pour un
   arbre dont l’étape de build vit dans les scripts d’un manifeste — or lire ce manifeste est
   exactement ce que §30 interdit au scanner. `build` n’est donc proposé que si un marqueur de
   build a réellement été vu, et l’écart est **inscrit dans `notes`** au lieu d’être comblé par
   une supposition.
3. **Le template `research` n’est jamais recommandé automatiquement.** Aucun nom de fichier ne
   distingue un projet de recherche d’un autre. Il reste disponible au choix, et le rapport le dit.

**Et un aveu porté par le format :** un template retenu faute de mieux se présente comme un
défaut, pas comme une déduction. Un test l’exige littéralement.

**Preuve :** `tests/test_project_recommendation.py`, quatorze tests — l’exemple de §31 rejoué tel
qu’il est écrit, déterminisme, absence d’écriture, absence de clé de commande, un gate jamais
proposé sans sa capability, quatre templates, et le lien au `report_hash` du scan lu. Passé sur ce
dépôt : template `software`, capabilities `install`, `build`, `test`, `typecheck`, quatre gates.
Suite : `782 passed, 69 subtests passed`.

### B4 — Taxonomie, entités et relations (étapes 5 à 7) — **FAIT**

**Livré :** `profile_taxonomy.py`, sous le même cycle que toute écriture sensible — preview,
vérification de fraîcheur, confirmation explicite, écriture atomique ou refus. Exposé en CLI
(`taxonomy`) et par le bridge (`taxonomy.preview` / `taxonomy.apply`).

**Le refus qui porte le lot.** Retirer un type qui porte déjà de la connaissance, des entités ou
des relations rendrait orphelin ce que le projet a enregistré. C’est **compté contre la mémoire
elle-même** — `COUNT(*)` sur `knowledge`, `entity`, `relation`, en lecture seule — et refusé **par
le Core**, pas grisé dans un écran : une règle tenue seulement par l’interface cesse d’exister dès
que quoi que ce soit d’autre écrit. Le refus dit combien d’enregistrements seraient orphelins, et
un type inutilisé se retire sans difficulté — deux tests, pour que le compteur ne puisse pas être
faussement toujours nul.

**Le piège des identifiants, tranché comme annoncé.** Le déclaratif est en majuscules, le stockage
en minuscules à tirets. L’écran n’édite que le déclaratif ; la conversion reste dans le Core, et un
identifiant minuscule est refusé à la saisie.

**Deux autres refus :** une section `knowledge` vide — un projet sans type de connaissance ne peut
rien mémoriser — et un preview périmé, rejoué à l’identique avant écriture.

**Preuve :** `tests/test_profile_taxonomy.py`, quatorze tests.

### B5 — Configuration du Work Graph (étape 8) — **FAIT, avec un périmètre corrigé**

**Ce document annonçait :** « déclarer les états de work item, les transitions autorisées et les
dépendances ». **Ce n’était pas tenable, et c’est la mesure qui l’a montré.** Le cycle de vie est
fermé dans le Core — quatre états, trois événements, transitions fixes dans `work_lifecycle.py`.
Laisser un projet déclarer une machine à états que le Core n’applique pas produirait **un graphe
qui ment** : l’écran offrirait une transition que le moteur refuse. Le graphe est donc *rapporté*,
depuis les constantes mêmes que le Core applique, et ce qu’un projet configure est la **sévérité
de la barrière** sur une transition.

**Livré :** `work_graph_config.py` — lecture du cycle de vie et des policies déclarées, puis
déclaration des policies de démarrage et de complétion sous preview et confirmation. CLI
`work-graph-config`, bridge `work.graph.read` / `work.graph.preview` / `work.graph.apply`.

**Deux services qui n’avaient aucun appelant.** `WorkStartPolicyService.declare` et
`WorkCompletionPolicyService.declare` existaient, testés, et rien ne pouvait les atteindre —
le même défaut que le diagnostic initial avait nommé. Ils ont maintenant une porte.

**Une irréversibilité dite à voix haute.** Une policy de transition se déclare **une seule fois** :
sa table tient une ligne unique et refuse `UPDATE` comme `DELETE` par trigger. C’est une garantie
voulue — un projet ne peut pas assouplir sa propre règle après coup pour faire passer un élément
gênant — et le preview l’énonce, parce qu’un assistant qui laisserait cliquer là-dessus dans un
formulaire ordinaire cacherait une décision définitive.

**Une policy absente est rapportée `NOT_DECLARED`, jamais comme un défaut.** Le moteur traite
l’absence comme non contrainte, mais écrire « OPEN » là où le store ne tient rien rapporterait une
décision que personne n’a prise.

**Un test qui aurait passé par accident, corrigé.** « `REQUIRE_READY` bloque le démarrage » est
faux tel quel : un élément sans prérequis **est** prêt, et démarrerait policy ou pas. La preuve
exige une dépendance non satisfaite, et son pendant — un élément sans prérequis démarre quand
même — pour que la policy soit prouvée dans les deux sens.

**Une collision de nom rattrapée par la suite complète.** La commande s’appelait d’abord
`work-graph`, nom déjà pris par la lecture des items : 55 tests sont tombés d’un coup. Renommée
`work-graph-config`.

**Preuve :** `tests/test_work_graph_config.py`, quatorze tests. Suite : `826 passed, 69 subtests`.

### B6 — Capability Builder visuel complet (§32) — étape 9 — **FAIT**

**Le défaut était plus grave que « des champs manquants ».** L’ancien builder écrivait cinq champs
directement dans SQLite. Une capability déclarée ainsi ne porte **ni contrat ni policy** : aucun
runner ne l’exécute — `capability_contract` est absente —, aucune décision ne la couvre, et aucun
hash déclaratif ne la voit, puisque `capability_catalog_hash` porte sur `capabilities.yaml`, que
cette voie ne touchait jamais. L’écran annonçait un succès ; le moteur tenait un objet inerte.

**Le contrat est écrit là où il existe.** `.vera-mmu/capabilities.yaml` est la seule source qui
porte le contrat entier — runner, policy projet, timeout, entrées, sorties, artefacts, validator,
admissibilité, confirmation. `load_project_catalogs` la valide, `capability_catalog_hash` la hache,
`sync-capabilities` la matérialise en une capability, un contrat et une décision de policy.

**La tension §32 / I008, tranchée par la lecture du code.** Le Core ne borne pas une commande :
**il n’a aucun champ de commande.** `capability_contract` tient un *profil* de runner choisi parmi
quatre, et aucun ne lance de processus depuis une chaîne fournie par le projet — `OBSERVED_PROCESS`
enregistre qu’un processus a eu lieu ailleurs. La ligne « Commande / API » est donc rapportée
`NOT_APPLICABLE` avec son motif : afficher un champ vide inviterait à le remplir.

**Les sept refus, chacun avec son code stable**, et chacun prouvé **deux fois** — par le builder,
et contre le fichier déclaratif lui-même, pour qu’écrire `capabilities.yaml` à la main ne change
rien : `COMMAND_NOT_BOUNDED`, `PATH_OUTSIDE_ROOTS`, `NETWORK_WITHOUT_POLICY`, `MISSING_TIMEOUT`,
`OUTPUT_NOT_INTERPRETABLE`, `DEPENDENCY_MISSING`, `PLACEHOLDER_VALIDATOR`.

**Un test qui épinglait l’inverse.** `test_project_bootstrap` déclarait une capability
`yields_proof: True` avec `outputs: []` adossée à une gate, et vérifiait que le catalogue
**chargeait**. Or tous les runners refusent `yields_proof`, et une gate lit `expected.verdict`
qu’aucune sortie ne rendait : ce test attestait comme valide une déclaration que le moteur ne peut
ni exécuter ni évaluer. Il est corrigé.

**Preuve :** `tests/test_capability_builder.py`, dix-neuf tests ; `apps/desktop/ui/src/contract.test.ts`,
treize tests. CLI `capability-contract`, bridge `capability.options` / `capability.preview` /
`capability.apply`, commande Rust et panneau de console complet.

### B7 — Gate Builder (§33) — étape 10 — **FAIT**

**Le trou mesuré.** Rien dans la chaîne de promotion ne regardait ce qu’une evidence *était*. Une
`HUMAN_ASSERTION` enregistrée `PASS` et admise promouvait une connaissance en `PROVEN` exactement
comme un `TEST_PROOF`. Une opinion rangée comme preuve — la seule chose que ce produit existe pour
empêcher (I004, I006).

**Les trois classes vivent dans le modèle, pas dans une couleur.** `evidence_classes.py` classe les
dix types fermés de `evidence.TYPES` : **validation technique** (verdict rejouable — `COMMAND_PROOF`,
`TEST_PROOF`, `CI_PROOF`, `API_PROOF`, `HASH_PROOF`, `FILE_PROOF`), **simple observation** (fait
enregistré dont le Core n’a dérivé aucun verdict — `METRIC_PROOF`, `EXTERNAL_ATTESTATION`),
**appréciation sémantique** (jugement qu’aucune réexécution ne reproduit — `HUMAN_ASSERTION`,
`MODEL_EVALUATION`). La classe est **dérivée** du type stocké plutôt que stockée à côté : une
seconde colonne pourrait le contredire, et c’est celle qu’on lirait qui déciderait si une opinion
compte comme preuve.

**Les dents.** `ProofService.promote` refuse toute evidence qui n’est pas une validation technique,
en nommant sa classe. Un test épingle le critère de sortie : une gate satisfaite par une
appréciation admise `PASS` est bien `PASS`, et la promotion derrière elle est refusée **par le
Core**. Le pendant est épinglé aussi — une validation technique promeut toujours — sans quoi le
refus pourrait être un blocage général ne prouvant rien.

**Une gate d’appréciations n’est pas refusée, elle est rapportée.** Une gate de relecture humaine
est une chose légitime à déclarer ; elle ne peut simplement jamais fonder une promotion. Le
builder et le rapport le disent avant la déclaration, plutôt que de le faire découvrir au moment
de promouvoir.

**L’écran §33, dérivé.** `gate_reports.py` rend gate, capability, exigences classées et les deux
lignes « peut satisfaire la gate » / « peut créer une proof ». La capability est lue par la chaîne
evidence → execution → capability, jamais redéclarée. CLI `gate-report`, bridge `gate.report`,
commande Rust et panneau de console.

**Preuve :** `tests/test_evidence_classes.py`, douze tests ; `apps/desktop/ui/src/gate.test.ts`,
sept tests.

**Trouvé en passant, laissé ouvert :** `policies.yaml` déclare `promotion.proven_requires:
[admissible_pass]` dans tous les projets, et **rien ne le lit**. C’est une serrure sans porte de
plus. Elle n’est pas ouverte ici à dessein : laisser un projet déclarer la condition de promotion
lui permettrait de déclarer que les opinions prouvent, ce que ce lot ferme. Le raccordement — s’il
a lieu — appartient à B8, l’éditeur de policies, et doit d’abord trancher ce que `proven_requires`
a le droit d’assouplir.

### B8 — Éditeur de policies (étape 11)

**Périmètre :** éditer les policies déclarées — réseau, système de fichiers, timeouts,
confirmations — avec preview et confirmation. **Rappel fail-closed :** la seule policy réseau
déclarable reste `DENY_NETWORK` ; un écran qui suggérerait autre chose mentirait sur ce que le
Core acceptera.

### B9 — Configuration du Resume et des intégrations (étapes 12 et 13)

**État :** l’étape 13 existe partiellement (choix d’un agent profile et de son adapter). L’étape 12
n’existe pas : le contrat de reprise, ses sections requises et sa barrière doivent être éditables.

**Critère de sortie :** un contrat édité produit exactement le hash que la barrière exige à
l’exécution, et un contrat modifié invalide visiblement la reprise en cours.

### B10 — MCP Preview avec métriques et alertes (§34) — étape 14

**Périmètre :** avant génération, afficher les décomptes de tools Core et projet, lecture seule,
écriture, sensibles, réseau, gates et capabilities, plus profile hash et policy hash. Puis les
alertes de §34 : capability sans validator objectif (`ERROR`), gate dépendant d’une capability
réseau (`WARNING`), chemin de sortie hors périmètre (`ERROR`), PROVEN activé sans secret HMAC
(`WARNING`).

**Le plus proche de l’existant :** le compilateur produit déjà paquet, hachages et validation
statique bloquante. Il s’agit de **rendre** ces chiffres, jamais de les recalculer côté interface.

### B11 — Valider, générer, installer, Doctor (étapes 15 à 18)

**État :** les quatre actions existent et sont exercées ; elles sont désormais gouvernées par le
parcours. Reste à afficher le Doctor final comme la sortie du parcours et non comme un outil de
côté.

---

## C. Ce qui décide de ce que le produit a le droit de dire de lui-même

### C1 — Parité ARET : mesurer ou renoncer explicitement

**Le fait :** `DECOUPLING_MATRIX.md` suit 16 couplages, **aucun n’est `DONE`** (14 `SPLIT`,
2 `IN_PROGRESS`). La Definition of Done §54 exige que les pipelines, gates, preuves et Resume
Guard d’ARET soient « équivalents ou meilleurs » après migration. Tant que rien n’est mesuré,
cette phrase ne peut pas être prononcée.

**Le blocage est matériel, pas logiciel.** Les abstractions génériques existent toutes. Ce qui
manque est la référence : les lignes `C07` et `C08` butent sur `MEM-WALL-001`, qui exige la
chaîne d’outils ARET réelle — binaire `aret`, Wine, MinGW, GCC, Cargo, Clang et corpus. Le
registre note que le corpus Wine historique échoue à `255/264` et que le corpus sandboxé complet
n’est pas terminé.

**Deux issues légitimes, à trancher par le propriétaire :**

1. **Mesurer.** Reconstituer un environnement ARET reproductible, rejouer les pipelines des deux
   côtés, comparer verdict par verdict, puis promouvoir les lignes une à une.
   *Critère de sortie :* chaque ligne `DONE` porte son test de parité exécuté et son artefact de
   comparaison daté. Aucune promotion par lecture de code.
2. **Renoncer formellement.** Déclarer le registre remplacé, et le pack ARET comme une
   compatibilité best-effort non certifiée.
   *Critère de sortie :* décision écrite dans `PROJECT_MEMORY.md`, en-tête du registre mis à
   jour, et toute mention de parité retirée du README et de la spécification de référence.

**À ne pas faire :** laisser les 16 lignes pourrir en `SPLIT` silencieux. C’est l’état actuel, et
c’est le seul qui soit indéfendable.

### C2 — Zero Pollution (§36) — **FAIT**

**Ce que la mesure a montré.** L’empreinte tenait : une installation complète sur un projet
témoin ne crée rien hors `.vera-mmu/` sauf la configuration hôte déclarée, et ne touche aucun
fichier métier. La seconde moitié de la promesse ne tenait pas : la synchronisation automatique
stageait `.vera-mmu/` en bloc, donc **`memory.sqlite-wal` et `memory.sqlite-shm` étaient commités
dans le dépôt de l’utilisateur**, ce que §36 interdit explicitement.

**Corrigé en deux endroits, parce qu’un seul n’aurait pas suffi.** L’initialisation écrit
désormais `.vera-mmu/.gitignore` — les règles vivent là où Git les voit, donc elles couvrent aussi
un `git add -A` fait à la main. Et `memory_sync` exclut les sidecars de son pathspec sur le
`status`, le `add` **et** le `commit` : `commit --only` prend son contenu dans l’arbre de travail,
donc un pathspec qui les nommait encore les aurait versionnés même laissés hors index.

**Le cas que les règles ne peuvent pas régler.** Une règle ajoutée après coup ne désuit pas un
fichier : une installation antérieure garde ses sidecars versionnés. Le Doctor porte donc une
ligne `zero_pollution` qui **interroge Git** au lieu de déduire — elle nomme les fichiers volatils
suivis et donne le `git rm --cached` correspondant. Quand elle ne peut pas interroger Git, elle
répond `INFO`, jamais un `PASS` qu’elle n’a pas vérifié.

**Reste ouvert, volontairement hors de ce lot :** retirer ces fichiers de l’index est une écriture
dans l’historique de l’utilisateur. Elle doit passer par un cycle preview → confirmation, donc par
`repair`, et non par une correction silencieuse. Le Doctor le signale ; personne ne le fait à sa
place.

**Preuve :** `tests/test_zero_pollution.py`, six tests mesurés sur un projet témoin sous Git —
empreinte, code métier intact, sidecars non versionnés y compris après un `git add -A` de
l’utilisateur, mémoire et profil restés versionnables, installation ancienne signalée, et absence
de `PASS` non vérifié. Suite : `756 passed, 55 subtests passed`.

### C3 — Abstraction VCS (§22)

**État :** `vcs.py` expose une seule fonction d’observation, `inspect_vcs`. La spécification
demande une hiérarchie `VersionControlProvider` avec `GitProvider`, `MercurialProvider`,
`SVNProvider` et `NoVCSProvider`, et pose que « le Core ne doit jamais supposer que Git existe ».

**Nuance importante :** le Core ne suppose déjà pas Git — le parcours no-Git est vert et `doctor`
le classe `INFO`. Ce qui manque est l’abstraction, pas la tolérance.

**Avant d’implémenter :** le handoff historique demandait explicitement que ce lot soit **étudié**
avant d’être écrit, et cette prudence reste juste. Mercurial et SVN sans utilisateur réel
produiraient du code non exercé. Une étude honnête peut conclure à `GitProvider` + `NoVCSProvider`
et documenter les deux autres comme non retenus.

**Critère de sortie :** décision écrite, puis soit l’abstraction avec ses tests par provider, soit
la note expliquant pourquoi elle reste à deux providers.

---

## D. À observer par le propriétaire — hors de portée d’un agent

### D1 — Observer le parcours desktop interactif

**Déjà prouvé :** `tauri build --bundles deb` passe, le paquet contient l’application et le
sidecar, l’application démarre sous affichage virtuel, et le sidecar empaqueté répond en stdio
avec ses refus de nonce et de confirmation.

**Non prouvé :** le dialogue WebView ↔ Rust ↔ sidecar déclenché par la sélection humaine d’un
dossier. Le parent Rust ne démarre le sidecar qu’à cette action, qui ne peut pas être simulée
honnêtement en conteneur.

**Critère de sortie :** installer le `.deb`, lancer, choisir un dossier, vérifier que le scan
remonte dans la fenêtre. Dix minutes sur une machine avec écran.

**Devient plus important avec le Dashboard :** chaque lot B ajoute des écrans qui ne seront
réellement exercés que par ce parcours.

### D2 — Preuves hôtes réelles par fournisseur

La barrière de reprise est câblée sur cinq adapters — Claude Code local et cloud, Codex, Gemini,
Antigravity — et rend un refus effectif, pas un avertissement. Ce qui manque est la preuve qu’un
hôte réel appelle bien ces hooks. Chaque fournisseur exige un verdict séparé. Pour Claude Code
cloud, la spécification impose un preview réel puis **deux confirmations distinctes** avant la
seule écriture user-scope.

---

## Ordre recommandé

1. **A1** — laisser la CI Windows conclure ; traiter ses échecs s’il y en a.
2. ~~**C2** — prouver Zero Pollution~~ — fait.
3. ~~**B2** et **B3**~~ faits : les étapes 1 à 3 du parcours sont livrées côté Core.
4. ~~**B1**~~ fait : dérivation, gouvernail et lanceur de tests d’interface.
5. **B4 à B9** — les écrans, dans l’ordre du parcours ; chacun avec ses méthodes de bridge et ses
   tests Core.
6. **B10 puis B11** — le MCP Preview, puis le raccordement des quatre dernières étapes.
7. **C1** — trancher la parité ARET.
8. **C3** — étudier l’abstraction VCS avant d’écrire une ligne.
9. **D1 et D2** — observations hôtes, au fil des occasions réelles, et après chaque lot B.

## Ce qu’il ne faut pas faire

- Ajouter un écran du Dashboard qui écrit sans passer par preview, fraîcheur et confirmation.
- Réimplémenter en TypeScript une validation que le Core doit porter : les deux divergeront, et
  c’est l’interface qui mentira.
- Laisser le Capability Builder accepter une chaîne de commande libre au prétexte que §32 affiche
  un champ « commande ». Le champ se compose de paramètres bornés, ou il n’existe pas.
- Afficher dans le MCP Preview des métriques recalculées côté interface plutôt que celles du
  paquet compilé.
- Promouvoir une ligne du registre de découplage sans test de parité exécuté.
- Recréer une mémoire SQLite absente dans la réparation : cela masquerait une base perdue.
- Compléter le scanner en lisant le contenu des fichiers : le scan reste une observation de
  surface, sans lecture, sans exécution, sans réseau.
- Écrire un provider VCS sans utilisateur réel pour l’exercer.
