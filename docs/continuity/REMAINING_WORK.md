# Travail restant — VERA-MMU

**Établi le :** 2026-09-14
**Révisé le :** 2026-09-15 — A1 clos par un run vert sur les deux runners.
**Révisé le :** 2026-09-14 — décision du propriétaire : le Dashboard configurateur est livré
entièrement, il n’est plus hors périmètre.
**Commit de référence :** branche `claude/youthful-fermat-b0h84l`
**Méthode :** chaque ligne est vérifiée contre le code, jamais reprise d’un registre.
**Suite :** `750 passed, 55 subtests passed`, attestée sur Linux x64 **et** Windows x64
(run `desktop-packaging.yml` #47, 2026-09-15).

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

### B1 — Socle : le parcours en dix-huit étapes

**Périmètre :** transformer la page unique en un parcours ordonné. Chaque étape porte un
identifiant, un critère d’entrée (ce qui doit exister avant d’y accéder), un état
(`BLOCKED`, `AVAILABLE`, `COMPLETED`) et une sortie observable. L’état du parcours se dérive du
projet, jamais d’un drapeau conservé dans l’interface : rouvrir l’application sur un projet à
moitié configuré doit retrouver exactement la même étape.

**À ajouter au bridge :** une méthode `wizard.state` qui rend, pour un projet, l’état des
dix-huit étapes et la raison de chaque blocage.

**Critère de sortie :** un test Python sur la dérivation des dix-huit états à partir d’un projet
donné, et la navigation exercée dans la suite TypeScript.

### B2 — Scanner de projet complet (§30) — étapes 1 et 2

**Écart mesuré :** la spécification exige au minimum quinze catégories d’observation. Le scanner
en produit environ sept : VCS, CI, langages via manifestes de dépendances, documentation,
conteneur, chemins de test.

**Manquent :** frameworks, scripts de build, linters, datasets, assets, sous-projets et fichiers
de configuration comme catégories distinctes.

**Contrainte à respecter :** le scan ne lit pas le contenu, ne suit pas les symlinks, n’exécute
ni processus ni réseau, et produit des observations `DETECTED`, jamais des vérités. Détecter un
framework signifie donc reconnaître un marqueur de fichier, pas analyser du code.

**Critère de sortie :** une fixture par catégorie, et un test qui échoue si une catégorie exigée
par la spécification cesse d’être détectée.

### B3 — Recommandation automatique de profil (§31) — étape 3

**État :** absente. Suite directe de B2 : sans les catégories manquantes, une recommandation
n’aurait pas de quoi se fonder.

**Périmètre :** depuis un rapport de scan, proposer un template, un jeu de capabilities et un jeu
de gates, **modifiables**. La spécification insiste : « l’utilisateur peut modifier chaque
élément ». Une recommandation n’est pas une décision.

**Critère de sortie :** une recommandation déterministe pour un même rapport de scan, exposée en
CLI et par le bridge, et un test prouvant qu’aucune recommandation n’écrit quoi que ce soit.

**Dépend de :** B2.

### B4 — Taxonomie, entités et relations (§29, étapes 5 à 7)

**Périmètre :** éditer les types de connaissance déclarés par le profil, les types d’entités et
les types de relations. Le Core sait déjà les déclarer et les synchroniser
(`write_api.sync_profile_knowledge_types`) ; ce qui manque est l’écran et les méthodes de bridge
de prévisualisation et d’application.

**Piège à éviter :** les identifiants déclaratifs sont en majuscules et les identifiants de
stockage en minuscules. L’interface édite le déclaratif ; la conversion reste dans le Core.

**Critère de sortie :** un type ajouté dans l’écran apparaît dans le catalogue après confirmation
et dans lui seul ; un type retiré est refusé s’il porte déjà de la connaissance, et le refus est
affiché tel quel.

### B5 — Configuration du Work Graph (étape 8)

**Périmètre :** déclarer les états de work item, les transitions autorisées et les dépendances.
Le Core porte déjà le cycle de vie append-only et le graphe (`work_graph`) ; l’écran les rend
éditables et lisibles.

**Critère de sortie :** un graphe déclaré dans l’interface se relit identique via `work_graph`,
et une transition non déclarée est refusée par le Core, pas seulement grisée dans l’écran.

### B6 — Capability Builder visuel complet (§32) — étape 9

**Écart :** le builder actuel ne saisit que l’identifiant, le nom, le type, la version et la
description. §32 exige un contrat complet : nom, type, runner, commande ou API, entrées, sorties,
timeout, policy, artifacts, validator, admissibilité comme preuve, confirmation requise.

**Et sept refus explicites**, que le Dashboard doit opposer : commande non bornée ; chemins hors
racines ; réseau sans policy ; capability sans timeout ; sortie non interprétable quand elle sert
de gate ; dépendance inexistante ; placeholder présenté comme validator.

**Point de tension à trancher dans le lot :** §32 parle d’une « commande », et I008 interdit
qu’un client fournisse une commande. Les deux se concilient d’une seule façon : l’interface
choisit parmi les profils de runner déclarés et leurs paramètres bornés, et n’envoie jamais une
chaîne de commande. Ce choix doit être écrit dans le lot, pas supposé.

**Critère de sortie :** un test par refus, côté Core, qui prouve que la déclaration est rejetée
même si l’interface est contournée.

### B7 — Gate Builder (§33) — étape 10

**Écart :** les deux builders existants — structure et policy — couvrent les exigences et le mode
d’agrégation, mais pas la distinction que §33 impose d’afficher clairement entre **validation
technique**, **appréciation sémantique** et **simple observation**.

**Pourquoi cette distinction compte plus que l’écran :** c’est elle qui empêche qu’une opinion
soit rangée comme une preuve. Elle doit donc être portée par le modèle de données et vérifiée par
le Core, pas seulement colorée dans l’interface.

**Critère de sortie :** une gate dont l’exigence est classée « appréciation sémantique » ne peut
pas créer de proof, et un test le prouve.

### B8 — Éditeur de policies (étape 11)

**Périmètre :** éditer les policies déclarées — réseau, système de fichiers, timeouts,
confirmations — avec preview et confirmation. Le Core les applique déjà ; l’écran les rend
visibles et modifiables.

**Rappel fail-closed :** la seule policy réseau déclarable reste `DENY_NETWORK`. Si l’écran
suggère autre chose, il ment sur ce que le Core acceptera.

### B9 — Configuration du Resume et des intégrations (étapes 12 et 13)

**Périmètre :** l’étape 13 existe partiellement — le choix d’un agent profile et de son adapter.
L’étape 12 n’existe pas : le contrat de reprise, ses sections requises et sa barrière doivent
être éditables et prévisualisables.

**Critère de sortie :** un contrat de reprise édité dans l’écran produit exactement le même
hachage que celui que la barrière exige à l’exécution. Un contrat modifié invalide la reprise en
cours, visiblement.

### B10 — MCP Preview avec métriques et alertes (§34) — étape 14

**Périmètre :** avant génération, afficher le décompte des tools Core et projet, lecture seule,
écriture, sensibles, réseau, gates et capabilities, ainsi que le profile hash et le policy hash.
Puis les alertes de §34 : capability sans validator objectif (`ERROR`), gate dépendant d’une
capability réseau (`WARNING`), chemin de sortie hors périmètre (`ERROR`), PROVEN activé sans
secret HMAC configuré (`WARNING`).

**Ce lot est le plus proche de l’existant :** le compilateur MCP produit déjà le paquet, les
hachages et une validation statique bloquante. Il s’agit de rendre ces chiffres, pas de les
inventer — et de ne jamais les recalculer côté interface.

**Critère de sortie :** les métriques affichées proviennent du paquet compilé, et un test vérifie
que chaque alerte de §34 est levée sur un projet qui la déclenche.

### B11 — Valider, générer, installer, Doctor (étapes 15 à 18)

**État :** les quatre actions existent et sont exercées. Reste à les rattacher au parcours comme
des étapes avec critère d’entrée, plutôt que comme des boutons indépendants, et à afficher le
Doctor final comme la sortie du parcours et non comme un outil de côté.

**Critère de sortie :** un parcours complet, du dossier vide au Doctor vert, exercé de bout en
bout par un test d’interface, chaque étape refusant de s’ouvrir tant que la précédente n’est pas
satisfaite.

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

### C2 — Zero Pollution : le prouver (§36)

**État :** le comportement semble respecté — l’installation n’écrit que sous `.vera-mmu/` et la
configuration hôte project-local — mais aucun test ne le **prouve** comme invariant.

**Critère de sortie :** un test qui initialise, génère et installe dans un projet témoin, puis
vérifie qu’aucun fichier hors `.vera-mmu/` et hors configuration hôte déclarée n’a été créé ou
modifié, et que `*.sqlite-wal`, `*.sqlite-shm` et `runtime/` restent ignorés.

**Coût :** faible. **Valeur :** c’est une promesse centrale du README, actuellement non gardée par
la suite. À faire avant le Dashboard, puisque le Dashboard écrira davantage.

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
2. **C2** — prouver Zero Pollution avant d’ajouter des écrans qui écrivent.
3. **B2 puis B3** — scanner complet, puis recommandation : ce sont les étapes 1 à 3 du parcours
   et la matière de tout le reste du Dashboard.
4. **B1** — le socle du parcours, une fois qu’il a de quoi remplir ses premières étapes.
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
