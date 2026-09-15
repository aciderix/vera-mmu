# Travail restant — VERA-MMU

**Établi le :** 2026-09-14
**Révisé le :** 2026-09-15 — A1, C2, B2 et B3 clos.
**Révisé le :** 2026-09-14 — décision du propriétaire : le Dashboard configurateur est livré
entièrement, il n’est plus hors périmètre.
**Commit de référence :** branche `claude/youthful-fermat-b0h84l`
**Méthode :** chaque ligne est vérifiée contre le code, jamais reprise d’un registre.
**Suite :** `782 passed, 69 subtests passed`. Le décompte `750` était attesté sur Linux x64 **et**
Windows x64 (run `desktop-packaging.yml` #47, 2026-09-15) ; les six ajouts de C2 restent à
attester sur Windows.

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
