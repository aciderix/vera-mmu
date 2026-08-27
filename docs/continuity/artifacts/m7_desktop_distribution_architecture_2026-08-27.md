# M7 — Architecture desktop, CLI et distribution VERA

**Date :** 2026-08-27  
**Statut :** `PARTIAL_PASS` : contrat, bridge stdio, enveloppe Tauri et paquet Debian de développement validés ; build Windows natif, AppImage, signature et exécution hôte réelle restent `NOT_RUN`.
**Portée :** application desktop humaine, CLI automatisable, état project-local non destructif et dashboard statique sans privilège local.

## 1. Décision

VERA sera livré sous trois formes complémentaires qui partagent le même Core Python et les mêmes contrats d’opération : une **CLI `vmmu`** pour les développeurs et agents locaux, une **application desktop Tauri v2** pour les personnes, et un **viewer statique** exportable pour GitHub Pages. Le produit desktop embarque le Core VERA sous forme de sidecar natif. L’utilisateur ne doit donc pas installer Python, les dépendances MCP ni le serveur VERA à la main. Tauri prévoit explicitement l’embarquement d’exécutables externes, y compris des applications Python préparées pour la distribution.[1]

> L’application rend l’installation facile ; elle ne rend jamais l’écriture implicite. Toute opération qui change le projet reste `preview` → contrôle de fraîcheur → confirmation explicite → écriture atomique ou refus.

## 2. Séparation des responsabilités

| Surface | Public principal | Autorité | Interdictions |
|---|---|---|---|
| `vmmu` | développeur, CI, agent local | opérations VERA versionnées et contrôlées | pas de commande libre dans les entrées VERA, pas de user-scope implicite |
| Application desktop | humain | sélection native de projet puis appels typés au sidecar | pas de plugin filesystem ou shell exposé au frontend ; pas de chemin saisi librement |
| Sidecar `vmmu-desktop-bridge` | processus VERA embarqué | exécute uniquement les opérations fermées du Core pour la racine sélectionnée | pas de socket réseau, pas de serveur HTTP, pas de MCP démarré à la demande du frontend |
| GitHub Pages / viewer statique | consultation portable | import/export de contrats VERA sérialisés | aucun accès au disque, au shell, au bridge, aux secrets ou au MCP local |

La mémoire SQL canonique de VERA reste **project-local** sous `.vera-mmu/memory.sqlite`. Lorsque ce fichier est versionné dans le dépôt du projet, une session ou machine qui récupère le commit correspondant retrouve la mémoire, les preuves, l’Active Front et les données de reprise de ce projet. Le MCP installé project-local relit cette mémoire dans son clone local ; il n’a pas à interroger GitHub pour reprendre.

L’interface React ne reçoit aucun accès direct aux systèmes de fichiers ni au spawn de processus. Les permissions Tauri sont des capacités explicites par fenêtre/WebView ; le frontend réduit doit rester sans plugin `fs` ni `shell` et les commandes enregistrées doivent être limitées à la liste VERA.[2]

## 3. Choix du transport local : stdio parent–sidecar

Pour l’application desktop, la voie locale ne sera **pas** une API HTTP ouverte sur `127.0.0.1`. Le processus Rust Tauri démarre un sidecar VERA par `stdin`/`stdout` et conserve le canal lui-même. Cela évite l’exposition d’un port local à d’autres pages ou processus, la gestion CORS et l’évolution des permissions navigateur d’accès au réseau local.

Un dashboard déployé en HTTPS et un bridge HTTP loopback restent un mode possible ultérieur pour une intégration hors application, mais ce mode exige des protections supplémentaires et dépend des politiques de permission du navigateur. Chrome qualifie désormais explicitement l’accès d’un site public à un service loopback d’accès au réseau local soumis à permission.[3] Il ne constitue pas la voie d’écriture principale de M7.

Le transport desktop suit le protocole `vera-desktop-bridge/v1` : lignes JSON de taille bornée, objet strictement validé, version obligatoire, opération fermée et réponses JSON normalisées. Le parent Rust fournit un nonce de démarrage au sidecar via un canal privé ; le nonce n’est jamais rendu à React. Un processus redémarré efface la racine sélectionnée et tout cache de preview.

## 4. Contrat d’opérations du bridge

La sélection de dossier est déclenchée par un dialogue natif Tauri. Le frontend ne saisit aucun chemin et ne transmet aucun chemin aux opérations suivantes. Le sidecar valide néanmoins la racine à chaque écriture avec les garde-fous VERA existants : racine réelle, répertoire, pas de symlink, confinement project-local et écritures atomiques.

| Opération `v1` | Entrée frontend admissible | Autorité interne | Sortie | Écriture |
|---|---|---|---|---|
| `project.select` | aucune | dialogue natif puis état Rust | identité et état de sélection | aucune |
| `project.scan` | aucune | racine sélectionnée | `ScanReport/v1` | aucune |
| `project.init.preview` | `template`, `projectId`, `projectName` strictement validés | racine sélectionnée | `ProjectInitializationPreview/v1` | aucune |
| `project.init.apply` | `previewHash`, `confirm: true` | preview caché côté bridge, racine revalidée | résultat d’initialisation | project-local seulement |
| `agents.list` | aucune | profils VERA intégrés | Agent Profiles déclaratifs | aucune |
| `adapter.generate` | `agentProfileId` | mapping profil VERA → adapter allowlisté | `GenerationPreview/v1` | aucune |
| `adapter.stage` | `agentProfileId`, `confirm: true` | adapter allowlisté et plan VERA attesté | résultat de staging | runtime VERA project-bound seulement |
| `adapter.install.preview` | `agentProfileId` | adapter allowlisté et profile project-local | preview de configuration | aucune |
| `adapter.install.apply` | `previewHash`, `confirm: true` | preview caché, adapter résolu côté bridge, revalidation adapter | reçu project-local | project-local seulement |
| `adapter.doctor` | `agentProfileId` | adapter allowlisté et profile local | `DoctorReport/v1` | aucune |
| `memory.sync` | aucune | policy `.vera-mmu/sync-policy.json` validée par le Core | statut de synchronisation mémoire | commit/push limité à `.vera-mmu/` si autorisé |

Le navigateur ou le WebView ne peut jamais fournir un shell, un chemin, un adapter brut, un hash de confiance, un verdict, un artifact, un code de sortie ou un contenu à écrire. Les entrées présentes dans ce tableau sont des sélecteurs et confirmations ; les données sensibles sont dérivées ou revalidées côté VERA.

## 5. Installation MCP project-local

L’initialisation écrit la configuration et l’état VERA sous `.vera-mmu/`. Une intégration MCP peut aussi devoir écrire une petite configuration à l’emplacement project-local imposé par l’hôte (`.mcp.json`, `.claude/`, `.codex/`, `.gemini/` ou `.antigravity/`). Ce n’est jamais une permission d’écraser : un fichier divergent, irrégulier ou symlinké provoque un refus explicite. Les opérations communes M6-B/M6-C restent les autorités de génération et d’application ; le bridge ne les réimplémente pas.

L’application desktop et la CLI montrent les mêmes previews. Le dashboard statique peut lire ou transporter un rapport, mais reste incapable de l’appliquer sur le disque.

## 6. Organisation du code et versionnement

Le dashboard M7-A WebDev constitue la première interface validée. Avant le premier packaging, sa source utile sera introduite de façon explicite dans le dépôt VERA sous `apps/desktop/`, avec :

```text
apps/desktop/
├── ui/                  # React partagé : viewer statique et fenêtre Tauri
├── src-tauri/           # commandes Rust fermées, pas de plugin fs/shell frontend
├── bridge-contract/     # schémas opérationnels v1 et fixtures interopérables
└── package.json
src/vera_mmu/
└── desktop_bridge.py    # serveur stdio borné, Core VERA seulement
```

Les rapports `ScanReport/v1`, previews et bundles exportables sont les seuls formats échangés entre le viewer statique et l’application. Cette structure versionne l’UI desktop avec le Core sans cacher du code produit dans le répertoire WebDev.

## 6.1 Mémoire VERA et GitHub

GitHub est le transport de l’état **que le projet décide de versionner**. Dans le mode de continuité ARET préservé par VERA, `.vera-mmu/memory.sqlite` est donc un fichier project-local qui peut suivre les commits, branches, clones et restaurations du dépôt au même titre que la configuration VERA. Un nouveau conteneur ou une nouvelle session reprend sur la mémoire contenue dans le checkout réellement récupéré.

| Situation Git | Règle VERA |
|---|---|
| Clone ou checkout d’un commit connu | Le MCP ouvre la mémoire SQLite de ce checkout après validation de l’identité du projet. |
| Transaction Core réussie et policy active | VERA consolide WAL puis committe seulement `.vera-mmu/`; si `auto_push=true`, il pousse `origin` sur la branche courante. Le MCP ne reçoit ni commande, ni remote, ni branche, ni chemin. |
| État local modifié hors mutation Core | L’utilisateur ou le workflow Git du projet conserve le contrôle. La CLI `vmmu memory-sync`, le tool MCP sans argument et l’action desktop peuvent demander un essai contrôlé selon la même policy. |
| Conflit Git sur `memory.sqlite` | Refus explicite : aucun merge automatique, aucun choix implicite d’une base binaire. Une procédure ultérieure doit restaurer une base choisie ou reconstruire un bundle VERA attesté. |
| État temporaire SQLite | Les fichiers journaux temporaires ne sont pas des artefacts de partage ; VERA doit fermer/contrôler la base avant une opération Git de sauvegarde. |

Cette distinction préserve la continuité entre sessions sans transformer GitHub en API de contrôle du MCP ni laisser un état concurrent se faire passer pour une mémoire canonique. Les données récupérées conservent leurs statuts : une entrée SQLite ne promeut jamais `UNKNOWN`, `FAIL`, `SKIPPED` ou `ERROR` en `PASS`.

### 6.2 Synchronisation automatique restreinte

L’initialisation VERA prévisualise et écrit, après confirmation, une policy project-local `vera-memory-sync-policy/v1`. Elle active `auto_commit` et `auto_push`, impose le remote littéral `origin` et la branche courante (`CURRENT`). Toute clé inconnue, fichier irrégulier/symlinké, racine Git hors projet, base SQLite non consolidable, HEAD détachée ou absence de remote est un statut de refus explicite. Aucun de ces cas ne transforme la transaction SQLite déjà committée en échec métier : le résultat de synchronisation est conservé pour diagnostic.

Le pathspec Git est toujours `.vera-mmu/`. Des changements métier parallèles restent dans le working tree et ne sont jamais ajoutés au commit mémoire. La façade MCP appelle l’essai automatique seulement après ses opérations mutantes qui ont déjà réussi ; ses lectures, previews et refus ne déclenchent aucun accès Git. Les surfaces manuelles — CLI, MCP et desktop — ne prennent aucune donnée Git du client.

## 7. Packaging et release

Chaque release devra produire, à partir du même tag VERA, au minimum une archive CLI et une application desktop pour Windows x64 et Linux x64. Tauri prend en charge des installateurs Windows MSI ou NSIS, et plusieurs formats Linux dont AppImage, Debian et RPM.[4] La première cible proposée est un installateur NSIS Windows et un AppImage Linux ; la CLI autonome est incluse dans l’application et distribuée séparément pour l’automatisation.

Les binaires Python/Core seront compilés **nativement sur chaque système cible** (par exemple dans une matrice CI Windows et Linux), puis placés comme sidecars correspondant au target triple Tauri. La documentation Tauri impose ce suffixe de target pour les sidecars.[1] Une compilation croisée Windows depuis Linux ne constituera pas une preuve de release : la documentation Tauri la qualifie de moins testée et recommande les machines/CI natives lorsque possible.[5]

Le builder versionné `scripts/build_desktop_sidecar.py` accepte exclusivement `x86_64-unknown-linux-gnu` ou `x86_64-pc-windows-msvc` et refuse un triplet différent de l’hôte. Le script POSIX historique délègue à ce même builder. La matrice `.github/workflows/desktop-packaging.yml` reconstruit le sidecar sur chaque runner natif, produit AppImage/Debian sous Linux et NSIS/MSI sous Windows, puis téléverse seulement des **artefacts de vérification** de workflow. Elle ne crée ni tag, ni release GitHub, ni publication GitHub Pages.[8]

Les releases publieront le hash SHA-256 de chaque artefact, les notes de version, les limites d’hôte attestées et, avant diffusion générale, une stratégie de signature de code. Tauri indique que la signature renforce l’intégrité et l’identité des exécutables distribués.[4]

## 8. Gates de M7

| Gate | Critère de passage |
|---|---|
| `G-DESKTOP-01` | le protocole stdio refuse version, opération, JSON, clé, taille, nonce ou état de projet invalides |
| `G-DESKTOP-02` | aucun chemin, shell, adapter brut, verdict ou contenu de fichier ne vient du frontend |
| `G-DESKTOP-03` | preview → confirmation → revalidation → application réutilise les opérations VERA existantes |
| `G-DESKTOP-04` | l’UI Tauri ne reçoit ni permission filesystem ni permission shell générique |
| `G-DESKTOP-05` | le viewer statique fonctionne par import/export et ne contient aucune voie locale privilégiée |
| `G-DESKTOP-06` | les builds Windows et Linux sont construits nativement, testés et hachés avant une release |

Les tests réels Claude Web, Codex, Gemini et Antigravity restent hors de cette tranche. Une configuration écrite dans un scope utilisateur, un trust hôte, un bootstrap réseau ou un secret reste soumis au protocole de confirmation séparé défini précédemment.

## 9. Résultat contrôlé du premier lot de bridge

Le commit fonctionnel `57279e1` introduit `vmmu-desktop-bridge`, un sidecar **stdio seulement** et un catalogue immuable d’adapters partagé avec la CLI. Le bridge fixe sa racine dans son parent natif, valide une enveloppe JSON `vera-desktop-bridge/v1`, impose un nonce privé, limite les messages et refuse tout champ imprévu. Il route uniquement les opérations fermées de scan, initialisation preview/apply, liste d’Agent Profiles, génération, staging, preview/install et doctor.

Les tests rouges ont précédé l’implémentation. Les tests verts valident notamment l’absence de racine fournie par l’interface, le refus de nonce/opération/champ/volume invalides, l’installation d’une initialisation uniquement depuis le preview caché et confirmé, ainsi que le parcours MCP générique génération → staging confirmé → preview → contrôle de fraîcheur → application. Une modification de `.mcp.json` après affichage provoque `PREVIEW_STALE`, sans écrasement. La suite VERA passe à `493 passed, 37 subtests passed`; une roue isolée contient et exécute `vmmu-desktop-bridge` sur stdin/stdout.

**Verdict.** `PASS` pour le transport desktop stdio borné et le parcours contrôlé générique. Les routes emploient le catalogue pour les autres Agent Profiles, mais leurs intégrations hôte spécifiques ne sont pas pour autant une preuve live. L’enveloppe Tauri et le paquet Debian debug ont depuis été vérifiés ; les artefacts Windows, AppImage, la signature et la campagne d’hôtes réels restent des lots distincts.

## 10. Prérequis de build et compatibilité des artefacts

Le build de développement Tauri sous Debian/Ubuntu requiert notamment `libwebkit2gtk-4.1-dev`, les outils C, `libssl-dev`, `libxdo-dev`, `libayatana-appindicator3-dev` et `librsvg2-dev`.[6] Ces paquets sont requis par la machine de construction Linux ; ils ne constituent pas une permission supplémentaire pour le WebView VERA ni une dépendance installée dans le projet de l’utilisateur.

Le paquet Debian produit par Tauri déclare les dépendances d’exécution WebKitGTK/GTK correspondantes. Pour préserver la compatibilité, les binaires Linux doivent être construits à partir de la plus ancienne base supportée qui fournit WebKitGTK 4.1, et non seulement depuis la dernière distribution disponible.[7] Cette exigence sera encodée dans la matrice CI de release.

Le premier assemblage de développement `VERA-MMU_0.1.0_amd64.deb` a été produit localement. Son contenu contient le sidecar autonome `usr/bin/vmmu-desktop-bridge`, et ce sidecar extrait a répondu à une requête `project.scan` sur stdin/stdout. Cela atteste l’inclusion du Core dans l’artefact Linux de développement, non une release signée ou une validation d’installation sur une machine utilisateur.

Le même lot a produit un AppImage Linux x64 qui contient également le sidecar dans son image squashfs. Les tests Rust et la compilation release ne produisent plus d’avertissement. Les résultats Windows doivent toutefois être observés sur le runner natif avant de qualifier la matrice comme passée.

### 10.1 Première exécution CI et correction

La première exécution GitHub Actions `33059343692` a échoué avant toute compilation : `actions/setup-node` cherchait l’exécutable `pnpm` pour son cache alors qu’aucune étape ne l’avait encore installé. Aucun artefact Linux ou Windows n’a donc été produit, et ce résultat ne qualifie ni un échec de Tauri ni un échec du sidecar. Le commit `a542660` installe `pnpm/action-setup@v4` avant `actions/setup-node`.

La seconde exécution `33059519088` a ensuite produit et téléversé les artefacts Linux x64. Le runner Windows a construit le sidecar mais s’est arrêté dans `tauri-build` parce que `icons/icon.ico` était absent, fichier requis pour la ressource Windows. Aucun bundle Windows n’a été produit dans ce run. L’icône VERA a été générée au format `.ico` depuis le PNG versionné, les builds locaux React/Rust Linux passent et une troisième exécution native doit désormais vérifier NSIS/MSI.

[6]: https://v2.tauri.app/start/prerequisites/ "Tauri v2 — Prerequisites"
[7]: https://v2.tauri.app/distribute/debian/ "Tauri v2 — Debian distribution"
[8]: https://v2.tauri.app/distribute/pipelines/github/ "Tauri v2 — GitHub pipelines"

## Références

[1]: https://v2.tauri.app/develop/sidecar/ "Tauri v2 — Embedding External Binaries"
[2]: https://v2.tauri.app/security/capabilities/ "Tauri v2 — Capabilities"
[3]: https://developer.chrome.com/blog/local-network-access "Chrome for Developers — Local Network Access"
[4]: https://v2.tauri.app/distribute/ "Tauri v2 — Distribute"
[5]: https://v2.tauri.app/distribute/windows-installer/ "Tauri v2 — Windows Installer"
