# M7 — Architecture desktop, CLI et distribution VERA

**Date :** 2026-08-27  
**Statut :** `PARTIAL_PASS` : contrat et bridge stdio génériques validés ; packaging Tauri Windows/Linux et exécution hôte réelle restent `NOT_RUN`.  
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
| État local modifié | L’utilisateur, la CLI ou l’agent utilise le workflow Git du projet pour commit/push ; le MCP ne réalise pas de synchronisation réseau en arrière-plan. |
| Conflit Git sur `memory.sqlite` | Refus explicite : aucun merge automatique, aucun choix implicite d’une base binaire. Une procédure ultérieure doit restaurer une base choisie ou reconstruire un bundle VERA attesté. |
| État temporaire SQLite | Les fichiers journaux temporaires ne sont pas des artefacts de partage ; VERA doit fermer/contrôler la base avant une opération Git de sauvegarde. |

Cette distinction préserve la continuité entre sessions sans transformer GitHub en API de contrôle du MCP ni laisser un état concurrent se faire passer pour une mémoire canonique. Les données récupérées conservent leurs statuts : une entrée SQLite ne promeut jamais `UNKNOWN`, `FAIL`, `SKIPPED` ou `ERROR` en `PASS`.

## 7. Packaging et release

Chaque release devra produire, à partir du même tag VERA, au minimum une archive CLI et une application desktop pour Windows x64 et Linux x64. Tauri prend en charge des installateurs Windows MSI ou NSIS, et plusieurs formats Linux dont AppImage, Debian et RPM.[4] La première cible proposée est un installateur NSIS Windows et un AppImage Linux ; la CLI autonome est incluse dans l’application et distribuée séparément pour l’automatisation.

Les binaires Python/Core seront compilés **nativement sur chaque système cible** (par exemple dans une matrice CI Windows et Linux), puis placés comme sidecars correspondant au target triple Tauri. La documentation Tauri impose ce suffixe de target pour les sidecars.[1] Une compilation croisée Windows depuis Linux ne constituera pas une preuve de release : la documentation Tauri la qualifie de moins testée et recommande les machines/CI natives lorsque possible.[5]

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

**Verdict.** `PASS` pour le transport desktop stdio borné et le parcours contrôlé générique. Les routes emploient le catalogue pour les autres Agent Profiles, mais leurs intégrations hôte spécifiques ne sont pas pour autant une preuve live. L’enveloppe Tauri, les artefacts Windows/Linux, la signature et la campagne d’hôtes réels restent des lots distincts.

## Références

[1]: https://v2.tauri.app/develop/sidecar/ "Tauri v2 — Embedding External Binaries"
[2]: https://v2.tauri.app/security/capabilities/ "Tauri v2 — Capabilities"
[3]: https://developer.chrome.com/blog/local-network-access "Chrome for Developers — Local Network Access"
[4]: https://v2.tauri.app/distribute/ "Tauri v2 — Distribute"
[5]: https://v2.tauri.app/distribute/windows-installer/ "Tauri v2 — Windows Installer"
