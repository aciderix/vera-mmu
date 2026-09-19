# Travail restant — VERA-MMU

**Établi le :** 2026-09-14
**Révisé le :** 2026-09-19 — `C07`/`C08` : parité partielle mesurée **sans chaîne d’outils**, les
deux lignes restant `IN_PROGRESS`. Le blocage était plus étroit qu’annoncé — les neuf scripts
d’oracle et l’image de référence existent déjà. Voir `LOG-0322`.
**Révisé le :** 2026-09-19 — run #61 sur `2c6e6eb` : les deux runners verts, `1091 + 312` et `78`
des deux côtés. **`C15` est attesté sur Windows ; les 164 tests de parité le sont tous. Aucune dette
Windows ouverte.**
**Révisé le :** 2026-09-19 — `C15` promu `DONE` : la barrière de reprise, et le premier couplage
dont le test exécute les **hooks** d’ARET. Un état illisible la fait disparaître chez ARET là où
VERA refuse ; un état acquitté se transplante entre mémoires. **Quatorze couplages clos sur seize**,
et il ne reste que `C07`/`C08`.
**Révisé le :** 2026-09-19 — run #59 sur `834ee13` : les deux runners verts, caches chauds. Les
bundles tombent de 324 s à 162 s sur Linux et de 336 s à 144 s sur Windows. Job complet : 7 min 14
et 11 min 55.
**Révisé le :** 2026-09-19 — run #57 sur `29e49cc` : premier run parallélisé, les deux runners
verts. Conformité 248 s → 85 s sur Linux, 696 s → 412 s sur Windows.
**Révisé le :** 2026-09-19 — run #56 sur `e2dbdfb` : les deux runners verts, `1068 + 275` et `78`.
`C12` attesté ; les 141 tests de parité le sont tous. Suite parallélisée : 261 s → 76 s.
**Révisé le :** 2026-09-19 — `C12` promu `DONE` : le playbook. Les deux le tiennent hors de la
mémoire canonique ; le parseur d’ARET écarte en silence un domaine dupliqué ou inventé.
**Treize couplages clos sur seize.**
**Révisé le :** 2026-09-19 — run #55 sur `2806468` : les deux runners verts, `1060 + 256` et `78`
des deux côtés. `C06` est attesté sur Windows ; les 133 tests de parité le sont tous.
**Révisé le :** 2026-09-19 — `C06` promu `DONE` : le catalogue de capabilities. ARET ferme sa liste
de 27 pipelines mais ne déclare aucun schéma de paramètres. **Douze couplages clos sur seize.**
**Révisé le :** 2026-09-19 — run #53 sur `76ef275` : les deux runners verts, `1045 + 211` et `78`
des deux côtés. `C14` est attesté sur Windows après la correction de la fuite de poignées d’ARET.
**Révisé le :** 2026-09-19 — `C14` promu `DONE` : le bundle, avec le `MemoryStore` entier d’ARET
exécuté sur son propre DDL. Sa chaîne d’intégrité tient ; son manifeste ne porte aucune identité de
projet. **Onze couplages clos sur seize.**
**Révisé le :** 2026-09-19 — run #51 sur `c014dbf` : les deux runners verts, `1034 + 196` et `78`
des deux côtés. Les 107 tests de parité sont attestés sur Windows pour la première fois, après
trois causes trouvées au run #50 et corrigées. Dette Windows soldée.
**Révisé le :** 2026-09-19 — `C13` promu `DONE` : la synchronisation Git, et le premier couplage
dont le test **exécute** la source ARET au lieu de la lire. Il a trouvé un défaut dans ARET V1 et
une règle morte dans VERA. **Dix couplages clos sur seize.**
**Révisé le :** 2026-09-19 — `C09`, `C10` et `C11` promus `DONE` : les trois couplages du serveur
MCP d’ARET, largement préparés par la section B. Neuf couplages clos sur seize.
**Révisé le :** 2026-09-19 — `C16` promu `DONE` : le noyau épistémique. La baseline montre I004 en
train de tenir — quatre preuves `PASS`, aucune admissible, zéro promotion sur 532 connaissances.
Six couplages clos sur seize.
**Révisé le :** 2026-09-19 — `C02` promu `DONE` : trois resserrements délibérés prouvés plutôt
qu’affirmés, dont le checkpoint WAL dont le mode de défaillance avait été mesuré au run CI #47.
Cinq couplages clos sur seize.
**Révisé le :** 2026-09-19 — `C05` promu `DONE` : cycle de vie, Front actif, ordre roadmap, liens,
dépendances et import V1, mesurés sur les treize briques réelles. Quatre couplages clos sur seize.
**Révisé le :** 2026-09-19 — `C04` promu `DONE`, après correction d’un défaut d’unicité qu’il a
révélé : la projection de symbole perdait la garantie `UNIQUE` d’ARET. Trois couplages clos sur seize.
**Révisé le :** 2026-09-19 — `C03` promu `DONE` : ses six dimensions sont mesurées contre le DDL réel
d’ARET et les vraies lignes de la baseline. Deux couplages clos sur seize.
**Révisé le :** 2026-09-18 — `C01` promu `DONE` : première ligne mère du registre de découplage à
porter un test de parité exécuté. Le diagnostic « blocage matériel » de C1 est corrigé, il était faux
pour 14 couplages sur 16.
**Révisé le :** 2026-09-18 — run #49 : les deux plateformes attestent `927 + 78` sur `9861450`.
**Révisé le :** 2026-09-18 — A1, B1 à B12 et C2 clos ; section B terminée.
**Révisé le :** 2026-09-18 — A1, B1 à B11 et C2 clos ; B12 ouvert (mesuré pendant B11).
**Révisé le :** 2026-09-18 — A1, B1 à B10 et C2 clos ; B11 ouvert.
**Révisé le :** 2026-09-15 — A1, B1 à B5 et C2 clos ; B6 à B11 ouverts.
**Révisé le :** 2026-09-14 — décision du propriétaire : le Dashboard configurateur est livré
entièrement, il n’est plus hors périmètre.
**Commit de référence :** branche `claude/youthful-fermat-b0h84l`
**Méthode :** chaque ligne est vérifiée contre le code, jamais reprise d’un registre.
**Suite :** `1108 passed, 376 subtests passed` en local sur Linux. L’attestation **sur les deux
plateformes** porte sur `1105 passed, 1 skipped, 365 subtests passed` côté Core et `78 passed` côté
interface, au run `desktop-packaging.yml` #62 sur `ca8a2f3` : chiffres identiques des deux côtés,
zéro échec, aucune occurrence de `WinError`, et l’intégralité des **179 tests de parité**
`C01`–`C16` couverte, `C07`/`C08` inclus pour leurs dimensions sans chaîne d’outils. Les 2 tests
ajoutés depuis (`LOG-0323`) lui sont postérieurs et attendent le prochain run. **Aucune dette
Windows ouverte.**

**Le test sauté est attendu et il est le bon.** `test_i013_a_missing_toolchain_yields_skipped_...`
interroge `required_tools` contre le vrai dépôt `Automatic-reverse-engineering-toolkit`, qui n’est
pas monté sur les runners CI ; il porte un `skipTest` explicite pour ce cas et se saute proprement,
emportant ses 9 sous-tests — d’où `365` en CI contre `374` en local. Un test qui ne peut pas
mesurer ce qu’il annonce se saute en le disant, il ne se contente pas de passer.
**Durée :** en local, **75 s** sur quatre cœurs (`-n auto --dist loadfile`) pour 1106 tests. En CI
au run #62 : conformité **116 s** sur Linux et **643 s** sur Windows ; job complet **7 min 10** et
**16 min 37**.
**Variance : Linux est stable, Windows ne l’est pas, et aucune explication n’est vérifiée.** Côté
Linux, l’étape de conformité tient entre 107 s et 120 s sur cinq runs — les ~12 % relevés en
`LOG-0319`. Côté Windows, la même suite à quelques tests près donne **409 s (#58), 420 s (#59),
342 s (#61) puis 643 s (#62)** : un rapport de **1,9 entre les extrêmes**, sur un code de test
quasi identique et un runner différent à chaque fois. Aucune conclusion de durée ne doit être tirée
d’un seul run Windows ; ces quatre mesures sont consignées telles quelles, sans cause attribuée.

Ce document énumère ce qui reste, dans l’ordre où je le ferais, avec pour chaque tâche son
périmètre exact, son critère de sortie vérifiable et ce qui la bloque s’il y a lieu. Il ne
répète pas ce qui est livré : voir `ENGINEERING_LOG.md` (LOG-0277 à LOG-0284).

## Règle de mise à jour

Une tâche n’est cochée que lorsque son critère de sortie a été **exécuté**, pas lu. Une tâche
partiellement faite reste ouverte avec une note ; elle ne devient jamais « faite en partie ».

---

## A. Clos

### A1 — Matrice native Windows x64 et Linux x64 — **FAIT**

**Run #62 sur `ca8a2f3`, le 19 septembre 2026 : les deux runners sont verts**, et les décomptes sont
identiques — `1105 passed, 1 skipped, 365 subtests passed` côté Core et `78 passed` côté interface,
zéro échec, aucune occurrence de `WinError`. L’attestation couvre l’intégralité des **179 tests de
parité** `C01`–`C16`. **Aucune dette Windows ouverte.** Le seul test sauté l’est par conception :
il interroge le dépôt toolkit, absent des runners, et le dit au lieu de passer en silence.

Conformité 116 s sur Linux et 643 s sur Windows ; jobs complets **7 min 10** et **16 min 37**.

**Historique du #61**, sur `2c6e6eb` : les deux runners verts, `1091 + 312` et `78`, 164 tests de
parité couverts — le run qui a soldé la dette Windows de `C15`. Conformité 118 s et 342 s.

**Le run #60, sur `6e48ce8`, avait échoué sur Windows**, et sa cause valait le détour : elle n’était
ni dans VERA ni dans le test, mais dans la sonde de toolchain d’ARET, qui lance `<outil> --version`
avec `timeout=5` et sans aucune garde — `clang --version` répond en plus de cinq secondes sur ce
runner, et le hook entier tombe sans livrer son dossier de reprise. Voir `LOG-0321` ; l’échec est
devenu la quatrième mesure de `C15`.

**Historique du #59**, sur `834ee13` : les deux runners verts, `1068 + 275` et `78`. Premier run à
**caches chauds**, et le gain tombe exactement là où il était visé : les bundles passent de 324 s à
**162 s** sur Linux et de 336 s à **144 s** sur Windows. Restaurer le cache coûte 10 à 14 s de plus
qu’un cache vide, le sauvegarder ne coûte plus rien quand rien n’a changé. Jobs complets : 7 min 14
et 11 min 55, contre 9 min 31 et 15 min 33 au #58.

**Historique du #57**, sur `29e49cc` : premier run avec la suite **parallélisée**, les deux runners
verts, mêmes décomptes. Conformité **85 s** sur Linux contre 248 s au #56, **412 s** sur Windows
contre 696 s ; jobs complets ~8 min et 15 min 14.

**Historique du #56**, sur `e2dbdfb` : les deux runners verts, mêmes décomptes, mesurés **en série**
— 248,19 s sur Linux et 696,16 s sur Windows. C’est le dernier run avant parallélisation, et c’est
lui qui sert de référence à toute comparaison de durée.

**Historique du #55**, sur `2806468` : les deux runners verts, `1060 passed, 256 subtests passed`
(355,00 s sur Linux, 885,66 s sur Windows) et `78 passed`. Il couvrait les 133 tests de parité,
`C12` excepté.

Le run #54, sur `c78a227`, avait porté **un** échec Windows, et il venait du test : une assertion
comparait `endswith("bench/gauntlet/score.sh")` à un chemin qu’ARET résout et rend sous sa forme
native. Ni ARET ni VERA n’avaient de défaut. Voir `LOG-0317`.

**Historique du #53**, sur `76ef275` : les deux runners verts, décomptes identiques — `1045 passed,
211 subtests passed` côté Core (290,46 s sur Linux, 587,34 s sur Windows) et `78 passed` côté
interface, aucune occurrence de `WinError`. Il couvrait les 118 tests de parité de `C01` à `C16`
hors `C06`.

Le run #52, sur `7c03ddf`, avait porté sept échecs Windows — les sept tests de `C14` qui construisent
un `MemoryStore` ARET, tous en `WinError 32`. La cause est dans la référence et n’y est pas
corrigeable : `_migrate` ouvre sa connexion avec un `with` qui ouvre une transaction sans fermer, et
trois descripteurs restent ouverts. Contourné dans `temporary_root()`. Voir `LOG-0316`.

**Historique du #51**, sur `c014dbf` : les deux runners verts, décomptes identiques — `1034 passed,
196 subtests passed` côté Core (238,25 s sur Linux, 628,06 s sur Windows) et `78 passed` côté
interface. C’était la première attestation deux plateformes à couvrir les 107 tests de parité
`C01`–`C05`, `C09`–`C11`, `C13` et `C16`.

Elle a coûté un run rouge. Le #50, sur `700e011`, portait dix-huit échecs Windows en trois causes,
toutes dans les tests et toutes invisibles sur Linux — Git réécrivait les références épinglées en
CRLF, une racine temporaire restait non canonique derrière un nom court 8.3, et une connexion SQLite
sans nom n’était jamais fermée. Voir `LOG-0313`. La leçon tient en une phrase : cent-sept tests
avaient été écrits entre le #49 et le #50, et dix-huit étaient faux sans que rien ne le signale.

**Historique du #49**, sur `9861450`, le 18 septembre 2026 : les deux runners verts, quinze étapes
chacun, décomptes identiques — `927 passed, 69 subtests passed` côté Core (220,79 s sur Linux,
515,88 s sur Windows) et `78 passed` sur huit fichiers côté interface. C’était la première
attestation couvrant B4 à B12 : le run #48 datait de `14706d92`, et dix commits — 63 fichiers,
8327 lignes ajoutées — n’avaient jamais tourné sur Windows.

L’audit mené avant le run n’a rien trouvé des trois causes racines de septembre : les cinq `fsync`
ajoutés portent tous sur une poignée d’écriture, les deux seules occurrences de barre inverse sont
des validateurs qui la **refusent**, et les connexions SQLite nouvelles ferment en `finally`. Les
cinq écritures atomiques passent `newline="\n"`, sans quoi Windows aurait écrit des CRLF et fait
diverger tous les hachages du projet entre plateformes. Le run l’a confirmé.

**Historique.** Run #47 sur `ec1fd93`, le 15 septembre 2026 : premier passage vert, quatorze étapes
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

**Ce que ces runs autorisent désormais à dire :** le README ne porte plus la restriction « décompte
relevé sur Linux x64 », et plus aucune réserve sur la série de parité. La suite — `1068 passed,
275 subtests passed` et `78 passed` — est attestée sur les deux plateformes au run #56.

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

### B8 — Éditeur de policies (étape 11) — **FAIT**

**Le lot annoncé était « un éditeur » ; un éditeur seul aurait été un écran qui ment.**
`policies.yaml` validait sa forme et presque aucune de ses valeurs. Un projet pouvait écrire
`network: {default: allow}`, `destructive: {default: allow}` ou `promotion: {proven_requires: []}`,
le chargeur acceptait et le Doctor rapportait « valide ». Les valeurs sont donc fermées **dans le
Core, sur le fichier lui-même** — le rappel fail-closed du réseau est tenu par le chargeur, pas par
un menu grisé.

**`proven_requires`, question laissée ouverte par B7, tranchée : elle ne peut pas assouplir.** La
liste enregistre ce que `promote` vérifie — evidence PASS admise **et** validation technique — et
le Core refuse une liste qui en déclare moins, parce qu’elle décrirait un moteur plus permissif que
celui qui tourne.

**`allowed_runners` était de la décoration.** Chaque projet l’expédiait vide pendant que ses
capabilities déclaraient des runners. Le template émet désormais les siens, le chargeur croise les
deux fichiers, et le builder §32 refuse dans son preview plutôt qu’après l’écriture.

**Chaque ligne dit ce qui l’applique :** `ENFORCED` avec le module qui la lit, ou `DECLARED_ONLY`
— `filesystem.read` et `destructive.default`. Et `git.commit` / `git.push`, déclarés ici mais
gouvernés par `sync-policy.json`, deviennent un **veto** : `deny` empêche, rien n’élargit.

**Preuve :** `tests/test_policy_editor.py`, seize tests ; `apps/desktop/ui/src/policy.test.ts`,
six tests. CLI `policies`, bridge `policy.options` / `policy.preview` / `policy.apply`.

### B9 — Configuration du Resume et des intégrations (étapes 12 et 13) — **FAIT**

**Deux serrures sans porte.** `integrations.enabled` gouverne l’étape 13 et commande la génération
MCP ; **rien** ne pouvait l’écrire, donc un projet neuf restait indéfiniment sur cette étape. Et le
contrat de reprise — sections requises, budget partagé — était lu par le Core et éditable par rien.

**Le critère de sortie, prouvé dans ses deux moitiés :** ce que le preview annonce est exactement ce
que `profile_resume_requirements` dérive ; et une garde armée sous l’ancien contrat n’acquitte plus,
tandis que le nouveau hash est accepté. Le preview **nomme les gardes qu’il invalidera** avant toute
écriture — un éditeur qui casserait silencieusement une reprise serait la façon la plus polie de
perdre une session.

**Deux briques trouvées sous l’éditeur, et corrigées.** Toute édition de profil rendait le store
SQLite inouvrable — `project_identity` inclut `profile_hash` — et **B4 avait livré ce défaut** avec
l’éditeur de taxonomie. La machinerie de `profile_rebind` est extraite en `commit_profile_change`
et utilisée par les deux éditeurs. En la corrigeant, une seconde est apparue : `current()` lisait la
dernière révision Front quel que soit son profil, donc après une édition le Front était illisible
*et* inécrivable, sans issue. La requête est bornée au profil courant, tous les refus intacts.

**Preuve :** `tests/test_resume_editor.py`, treize tests ; `apps/desktop/ui/src/resume.test.ts`,
huit tests. CLI `resume-contract`, bridge `resume.options` / `resume.preview` / `resume.apply`.

### B10 — MCP Preview avec métriques et alertes (§34) — étape 14 — **FAIT**

**Rien ne classait les outils.** La façade connaissait ses noms et rien d’autre, donc tout décompte
aurait été inventé à l’écran. `mcp_tool_classes.py` déclare ce que chaque outil fait à l’état
durable ; `mcp_preview.py` **rend** chiffres, hachages et alertes sans en recalculer aucun.

**Le marqueur évident n’était pas le bon.** `_mutating_call` signifie « rapporte le statut de
synchronisation », pas « modifie » : `mmu_export_bundle` et `mmu_sync_memory` écrivent sans passer
par lui. Une classification dérivée de ce marqueur les aurait dits en lecture seule. La table est
déclarée, et un test épingle la seule relation dérivable — tout outil `_mutating_call` est `WRITE`.

**Une dérive trouvée en comptant :** `mmu_get_documentation` était servi par le serveur et absent de
`TOOL_NAMES`. Le manifeste annonçait 46 outils pour 47 servis. Corrigé, et les deux ensembles sont
désormais liés par un test.

**Trois des quatre alertes de §34 ne peuvent plus se déclencher**, fermées à la déclaration par B6
et B8. Elles sont rapportées `NOT_APPLICABLE` **avec la règle qui les a fermées**, pas à zéro : une
alerte impossible n’est pas un silence tranquille, c’est une règle qui a bougé. La quatrième —
validator déclaré mais non enregistré — est atteignable et nomme la capability en cause.

**Preuve :** `tests/test_mcp_preview.py`, douze tests ; `apps/desktop/ui/src/preview.test.ts`, neuf
tests. CLI `mcp-preview`, bridge `mcp.preview`.

### B11 — Valider, générer, installer, Doctor (étapes 15 à 18) — **FAIT**

`journey_outcome` rend la conclusion du parcours : le verdict unique (`INCOMPLETE`, `REFUSED`,
`FAILED`, `COMPLETE`), la ligne de l’étape 15, celle de l’étape 18 avec ses contrôles en échec et
leur réparation, et les étapes encore ouvertes. Tant qu’une étape observable est ouverte, les deux
lignes valent `NOT_REACHED` : un Doctor rendu trop tôt ne dit que « pas encore » et apprend à passer
outre. CLI `conclude` (sortie `0` sur `COMPLETE` seulement), bridge `journey.outcome`, commande Rust
et panneau de console. Quatorze tests Core, quatorze tests interface, dix-huit règles au mordant
vérifié.

Deux règles mortes retirées au passage : `project_validation` portait sa propre copie de deux
relations croisées que `load_project_catalogs` refuse avant qu’elle ne les atteigne. Les tests
épinglent désormais **quelle couche** refuse chaque cas.

---

### B12 — Les étapes 5 à 8 n’ont aucun contrôle dans le Dashboard — **FAIT**

Six commandes Rust (`work_graph_read`, `work_graph_preview`, `work_graph_apply`,
`taxonomy_options`, `taxonomy_preview`, `taxonomy_apply`), leurs méthodes `desktopApi`, et deux
panneaux de console gouvernés par le parcours. `tests/test_desktop_surface_parity.py` ferme la
chaîne Core → bridge → parent Rust → console dans les cinq directions, de sorte que la prochaine
dérive de ce type tombe sur un test au lieu d’attendre une mesure manuelle.

Au passage : l’éditeur de taxonomie n’avait **aucune lecture**. Un écran qui doit envoyer la liste
entière d’une section sans pouvoir apprendre la liste courante ne peut être utilisé que
destructivement. `taxonomy_options` rend les types déclarés et le nombre d’enregistrements que la
mémoire porte déjà sous chacun, pour que ce qu’un retrait orphelinerait soit visible avant le
preview, pas seulement dans son refus.

---

## C. Ce qui décide de ce que le produit a le droit de dire de lui-même

### C1 — Parité ARET : mesurer ou renoncer explicitement — **EN COURS, 13/16**

**Le diagnostic précédent était faux, et c’est mesuré.** Ce document affirmait que « le blocage est
matériel » et qu’il fallait la chaîne d’outils ARET réelle. C’est vrai pour **deux** couplages sur
seize. Les quatorze autres exigent une comparaison de **données et de comportement**, dont les seuls
prérequis sont la source ARET et une mémoire baseline — tous deux disponibles.

**Ce qui est réellement présent, vérifié :** la source ARET-MMU complète (64 fichiers Python, commit
`b9511dcc`), la mémoire baseline `aret_memory.sqlite` de `11 280 384` octets — exactement la taille
que ce registre cite — portant 17 `component`, 9 `function_symbol`, 13 `brick`, 532 `knowledge`,
47 `relation`, 4 `proof` ; la source Rust du toolkit avec `Cargo.toml` ; le corpus `bench` de 97 Mo,
476 fichiers ; `cargo 1.94.1`, `clang 18.1.3`, `gcc 13.3.0`. **Manquent** Wine et MinGW, tous deux
installables par apt (`9.0~repack-4build3`, `13.2.0-6ubuntu1+26.1`).

**`C01` est promu `DONE`** par `tests/test_aret_c01_addressing_parity.py`, qui exécute les deux
implémentations et compare leurs verdicts sur quatre dimensions — écriture, round-trip, corpus réel
de la baseline, et direction du resserrement.

**`C03` est promu `DONE`** par `tests/test_aret_c03_component_parity.py`, qui bâtit sa source en
exécutant le DDL réel d’ARET et la peuple des vraies lignes, puis mesure les six dimensions que le
registre exige — import, unicité, liens de connaissance, intégrité référentielle, bundle, absence de
`component` dans le Core. Il confronte au passage `aret_v1_schema_manifest()` au DDL qu’il prétend
décrire, ce qu’aucun test ne faisait.

**Le défaut trouvé en `C03` vaut d’être retenu pour les suivants :** les fixtures écrivaient leur
propre `CREATE TABLE component`, non `STRICT` et sans `DEFAULT ''`, d’après le contrat qu’elles
servaient à valider. Une fixture écrite d’après un contrat ne peut pas le réfuter. La règle pour les
douze couplages restants est donc : **la source de test se construit avec le DDL d’ARET, jamais avec
un schéma réécrit.**

**`C04` est promu `DONE`**, et c’est le premier couplage dont le test de parité a **trouvé un
défaut au lieu de confirmer une conformité**. ARET garantit `UNIQUE(component_id, module, symbol)` ;
la projection joignait les trois par `-`, admis dans les composantes, donc trois familles de triplets
distincts produisaient le même identifiant VERA. Latent — aucune des neuf lignes réelles ne le
déclenche — mais `module` vaut `''` par défaut dans le schéma ARET. La projection échappe désormais
le séparateur, et les identifiants du corpus réel sont inchangés.

**`C05` est promu `DONE`**, et il illustre le piège inverse de `C04` : `brick.state` est contraint
par un `CHECK` à cinq valeurs, et exiger que le `work_item` importé le porte aurait été **inventer un
défaut**. Le registre énonce l’inverse — métadonnée sous namespace ARET, le Core ne décide pas de la
sémantique legacy — et `work_item.status` est d’ailleurs fixé à `PLANNED` par son propre `CHECK` : le
cycle de vie VERA est événementiel. La parité tient donc en deux claims séparés, tous deux mesurés :
l’état ARET est conservé sans perte, et le cycle de vie de VERA tourne sur un item importé.

**`C02` est promu `DONE`.** Trois resserrements y sont prouvés plutôt qu’affirmés : ARET lit
`os.environ`, VERA exige un mapping ; ARET **crée** ses répertoires, VERA refuse un runtime absent ;
le checkpoint WAL d’ARET ne contrôle que `busy`, VERA lit d’abord puis exige aussi `log == 0`. Ce
dernier n’est pas un choix de style — le mode de défaillance a été mesuré au run CI #47.

**`C16` est promu `DONE`**, et c'est le couplage qui portait le plus de risque : `PROVEN`, HMAC,
append-only, audit. La baseline montre la règle **en train de tenir** — quatre preuves `PASS` et
`exit_code=0`, toutes `admissible=0`, `KN-0011` liée à trois d'entre elles et jamais promue, zéro
`PROVEN` sur 532 connaissances. I004 n'est donc pas une intention de conception mais un comportement
observable en production. Mesuré au passage, en exécutant le DDL d'ARET : son append-only protège le
**contenu** mais laisse passer la suppression d'une connaissance ; VERA refuse les deux.

**`C09`, `C10` et `C11` sont promus `DONE`** — les trois couplages qui portent sur le serveur MCP
d’ARET, et dont la section B avait déjà fait l’essentiel. `C09` : la doctrine d’ARET est une
**constante de module**, la même pour tout projet ; VERA compile les siennes et en publie le hash,
qui bouge avec le projet et avec le playbook. `C10` : ARET écrit 44 outils sans aucune table
d’accès ; VERA en classe 47 de façon exhaustive et partitionnante. `C11` : ARET accepte
`repository_path` sur trois outils et **valide** la valeur ; VERA n’expose ce champ sur aucun des
siens — ne pas avoir le champ est le refus le plus fort, il ne dépend d’aucune comparaison
qu’on pourrait relâcher.

**`C13` est promu `DONE`**, et il change la méthode. Les douze couplages précédents extrayaient
leurs faits ARET d’un arbre syntaxique : c’était juste pour une constante, une table ou une
signature. `C13` porte sur un **comportement** — que fait ce code devant un dépôt réel — et une
lecture n’y répond pas. La référence versionnée est donc chargée comme module et ses fonctions
tournent sur de vrais dépôts Git, à côté de celles de VERA.

Ce que l’exécution a trouvé : **`invoke()` applique `.strip()` à la sortie entière de
`git status --porcelain=v1`**. L’espace de tête de la première ligne disparaît, `changes()` découpe
à position fixe, et le chemin perd son premier caractère. `validate_scope` conclut alors qu’un
fichier **de** la mémoire est **hors** de la mémoire — dans le cas ordinaire, celui où la base est
modifiée en place et rien d’autre. Conséquence mesurée : `automatic_sync` refuse une mémoire
parfaitement propre, et `sync_memory_only` ne commite rien tout en annonçant « aucun changement ».
Un `git add` préalable fait disparaître le symptôme, ce qui explique qu’aucun test ARET ne l’ait vu.
Le défaut n’est **pas corrigé** : la référence est une copie dont le hash est épinglé, et la réparer
reviendrait à mesurer autre chose qu’ARET. VERA y échappe par construction — elle ne réimplémente
pas le format de sortie de Git, elle lui passe un pathspec et ne lit que le vide de la réponse.

Le même test a trouvé une **règle morte dans VERA**, corrigée : `symbolic-ref --quiet` *sort en
erreur* sur une HEAD détachée au lieu de rendre une sortie vide, si bien que le diagnostic dédié
écrit juste en dessous n’était atteignable par aucun chemin. Le refus avait lieu ; il ne disait
simplement pas ce qui s’était passé. C’est la quatrième règle morte trouvée par mutation dans cette
série, après les deux de `B11` et la garde de `C04`.

**Ce que ces promotions ne disent pas :** rien sur les deux couplages restants. Une parité
d’adressage, de store, de composants, de symboles, de briques, de Git, de bundle, de catalogue, de
playbook et de barrière de reprise n’est pas une parité ARET.

**Reste, et il ne reste qu’une chose :**

1. **`C07` et `C08`** — la seule dimension restante est l’**exécution réelle** d’un oracle :
   evidence hashée, promotion `PROVEN`, gate réelle, et exécutabilité mesurée dans l’image de
   référence. Tout le reste de ces deux lignes est désormais mesuré, sans chaîne d’outils, par
   `tests/test_aret_c07_c08_oracle_parity.py` — voir `LOG-0322`.

   **L’état réel du conteneur, vérifié et non repris d’un registre.** Absents : `wine`,
   `i686-w64-mingw32-gcc`, `i686-w64-mingw32-nm`, `winegcc`, `z3` ; `target/release/aret` n’est pas
   construit. Présents, et c’est ce que le registre ne disait pas : **les neuf scripts d’oracle**
   (`bench/*.sh`, `src/cpudiff.rs`, dans `Automatic-reverse-engineering-toolkit` et non dans
   `ARET-MMU`), **l’image de référence** `docker/ci-toolchain/Dockerfile` épinglée à `ubuntu:24.04`,
   **`docker`** lui-même, plus `cargo`, `rustc`, `gcc`, `clang` et `bash`. Mesuré sur le vrai dépôt
   toolkit : `cpudiff` et `funcdiff` n’ont **aucune dépendance manquante** ici.

   **Le chemin le moins cher que j’avais recommandé n’existe pas, et `LOG-0323` dit pourquoi.**
   `cpudiff` et `funcdiff` n’ont pas besoin du binaire `aret` — leur `requires_aret_binary` vaut
   `False` —, mais tous deux exigent `--features unpack`, donc la **libunicorn système**, absente
   ici et déclarée dans aucune des deux specs. Une compilation ne contourne pas cette dépendance.

   Deux chemins restent donc, et un seul est bon marché : fournir `libunicorn` (et alors les deux
   oracles deviennent réellement lançables), ou construire l’image de référence avec `docker` pour
   obtenir Wine, MinGW et libunicorn d’un coup. Le troisième reste d’acter que la parité
   d’exécution ne se mesure pas ici. Le choix revient au propriétaire ; aucune tentative non bornée
   ne sera lancée sans lui.

**Tous les couplages de nature « données et comportement » sont clos** depuis `C15`. Le gabarit,
posé par `C01` et étendu par `C13`, aura tenu jusqu’au bout : une référence ARET versionnée avec son
empreinte, un corpus réel, une parité dirigée — et, quand la question porte sur un comportement, une
référence qui **s’exécute** plutôt qu’elle ne se lit.

*Critère de sortie inchangé :* chaque ligne `DONE` porte son test de parité **exécuté** et son
artefact de comparaison daté. Aucune promotion par lecture de code.

**À ne pas faire :** laisser les lignes restantes pourrir en `SPLIT` silencieux, ni étendre la
promotion de `C01` à des surfaces qu’elle ne touche pas.

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

1. ~~**A1**~~ fait : run #49 sur `9861450`, les deux runners verts, décomptes identiques et aucun
   échec à traiter.
2. ~~**C2** — prouver Zero Pollution~~ — fait.
3. ~~**B2** et **B3**~~ faits : les étapes 1 à 3 du parcours sont livrées côté Core.
4. ~~**B1**~~ fait : dérivation, gouvernail et lanceur de tests d’interface.
5. ~~**B4 à B9**~~ faits : les écrans, dans l’ordre du parcours, chacun avec ses méthodes de bridge
   et ses tests Core.
6. ~~**B10 puis B11**~~ faits : le MCP Preview, puis la conclusion du parcours.
7. ~~**B12**~~ fait : les étapes 5 à 8 sont raccordées au parent natif, avec le test de parité qui
   empêchera la prochaine dérive de ce type. **La section B est terminée.**
8. **C1** — poursuivre la parité ARET : treize couplages sont clos, un seul de données reste
   faisable ici — `C15` — et `C07`/`C08` demandent Wine et MinGW. `C06` étant clos, `C07` n’a plus de
   dépendance ouverte côté catalogue.
9. **C3** — étudier l’abstraction VCS avant d’écrire une ligne.
10. **D1 et D2** — observations hôtes, au fil des occasions réelles, et après chaque lot B.

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
