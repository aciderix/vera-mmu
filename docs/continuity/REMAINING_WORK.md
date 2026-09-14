# Travail restant — VERA-MMU

**Établi le :** 2026-09-14
**Commit de référence :** branche `claude/youthful-fermat-b0h84l`
**Méthode :** chaque ligne est vérifiée contre le code, jamais reprise d’un registre.
**Suite au moment de l’établissement :** `749 passed, 55 subtests passed` sur Linux x64.

Ce document énumère ce qui reste, dans l’ordre où je le ferais, avec pour chaque tâche son
périmètre exact, son critère de sortie vérifiable et ce qui la bloque s’il y a lieu. Il ne
répète pas ce qui est livré : voir `ENGINEERING_LOG.md` (LOG-0277 à LOG-0284).

## Règle de mise à jour

Une tâche n’est cochée que lorsque son critère de sortie a été **exécuté**, pas lu. Une tâche
partiellement faite reste ouverte avec une note ; elle ne devient jamais « faite en partie ».

---

## A. En cours de vérification

### A1 — Matrice native Windows x64

**État :** workflow `desktop-packaging.yml` déclenché manuellement sur la branche.
**Ce qu’il prouve s’il passe :** la suite complète sur Windows, plus le sidecar, l’archive CLI
et les installeurs NSIS et MSI construits sur un vrai runner.
**Critère de sortie :** run vert sur les deux runners de la matrice.
**Si rouge :** l’historique du dépôt montre deux classes d’échec Windows déjà rencontrées — un
alias de chemins et un MSI refusant un identifiant de préversion textuel. Commencer par là.
**Ensuite :** retirer du README la restriction « décompte relevé sur Linux x64 » et dater le
passage Windows dans le journal.

---

## B. Priorité haute — ce qui change ce que le produit peut revendiquer

### B1 — Parité ARET : mesurer ou renoncer explicitement

**Pourquoi c’est premier :** `DECOUPLING_MATRIX.md` suit 16 couplages, **aucun n’est `DONE`**
(14 `SPLIT`, 2 `IN_PROGRESS`). La Definition of Done §54 exige que les pipelines, gates,
preuves et Resume Guard d’ARET soient « équivalents ou meilleurs » après migration. Tant que
rien n’est mesuré, cette phrase ne peut pas être prononcée.

**Le blocage est matériel, pas logiciel.** Les abstractions génériques existent toutes. Ce qui
manque est la référence : les lignes `C07` et `C08` butent sur `MEM-WALL-001`, qui exige la
chaîne d’outils ARET réelle — binaire `aret`, Wine, MinGW, GCC, Cargo, Clang et corpus. Le
registre note que le corpus Wine historique échoue à `255/264` et que le corpus sandboxé
complet n’est pas terminé.

**Deux issues légitimes, à trancher par le propriétaire :**

1. **Mesurer.** Reconstituer un environnement ARET reproductible, rejouer les pipelines des
   deux côtés, comparer verdict par verdict, puis promouvoir les lignes une à une.
   *Critère de sortie :* chaque ligne `DONE` porte son test de parité exécuté et son artefact
   de comparaison daté. Aucune promotion par lecture de code.
2. **Renoncer formellement.** Déclarer le registre remplacé, et le pack ARET comme une
   compatibilité best-effort non certifiée.
   *Critère de sortie :* décision écrite dans `PROJECT_MEMORY.md`, en-tête du registre mis à
   jour, et toute mention de parité retirée du README et de la spécification de référence.

**À ne pas faire :** laisser les 16 lignes pourrir en `SPLIT` silencieux. C’est l’état actuel,
et c’est le seul qui soit indéfendable.

### B2 — Scanner de projet complet (§30)

**Écart mesuré :** la spécification exige au minimum quinze catégories d’observation. Le
scanner en produit environ sept : VCS, CI, langages via manifestes de dépendances,
documentation, conteneur, chemins de test.

**Manquent :** frameworks, scripts de build, linters, datasets, assets, sous-projets et
fichiers de configuration comme catégories distinctes.

**Contrainte à respecter :** le scan ne lit pas le contenu, ne suit pas les symlinks, n’exécute
ni processus ni réseau, et produit des observations, jamais des vérités. Détecter un framework
signifie donc reconnaître un marqueur de fichier, pas analyser du code.

**Critère de sortie :** une fixture par catégorie, et un test qui échoue si une catégorie
exigée par la spécification cesse d’être détectée.

### B3 — Recommandation automatique de profil (§31)

**État :** absente. C’est la suite directe de B2 : sans les catégories manquantes, une
recommandation n’aurait pas de quoi se fonder.

**Périmètre :** depuis un rapport de scan, proposer un template, un jeu de capabilities et un
jeu de gates, **modifiables**. La spécification insiste : « l’utilisateur peut modifier chaque
élément ». Une recommandation n’est pas une décision.

**Critère de sortie :** une recommandation déterministe pour un même rapport de scan, exposée
en CLI et par le bridge, et un test prouvant qu’aucune recommandation n’écrit quoi que ce soit.

**Dépend de :** B2.

---

## C. Priorité moyenne — surfaces déclarées mais incomplètes

### C1 — Abstraction VCS (§22)

**État :** `vcs.py` expose une seule fonction d’observation, `inspect_vcs`. La spécification
demande une hiérarchie `VersionControlProvider` avec `GitProvider`, `MercurialProvider`,
`SVNProvider` et `NoVCSProvider`, et pose que « le Core ne doit jamais supposer que Git
existe ».

**Nuance importante :** le Core ne suppose déjà pas Git — le parcours no-Git est vert et
`doctor` le classe `INFO`. Ce qui manque est l’abstraction, pas la tolérance.

**Avant d’implémenter :** le handoff historique demandait explicitement que ce lot soit
**étudié** avant d’être écrit, et cette prudence reste juste. Mercurial et SVN sans utilisateur
réel produiraient du code non exercé. Une étude honnête peut conclure à
`GitProvider` + `NoVCSProvider` et documenter les deux autres comme non retenus.

**Critère de sortie :** décision écrite, puis soit l’abstraction avec ses tests par provider,
soit la note expliquant pourquoi elle reste à deux providers.

### C2 — Builders visuels : compléter ou requalifier (§32, §33)

**État réel :** `capability_builder`, `gate_policy_builder` et `gate_structure_builder`
exposent chacun deux fonctions, prévisualisation et application, et le bridge desktop les
expose sous `capability.*` et `gate.*`. Ce sont des constructeurs déclaratifs bornés, pas les
éditeurs visuels complets décrits par la spécification.

**Deux issues :** compléter l’édition visuelle dans le Dashboard, ou requalifier ces sections
comme couvertes par une édition déclarative assistée. La seconde est défendable si elle est
écrite ; elle ne l’est pas aujourd’hui.

### C3 — Zero Pollution : le prouver (§36)

**État :** le comportement semble respecté — l’installation n’écrit que sous `.vera-mmu/` et la
configuration hôte project-local — mais aucun test ne le **prouve** comme invariant.

**Critère de sortie :** un test qui initialise, génère et installe dans un projet témoin, puis
vérifie qu’aucun fichier hors `.vera-mmu/` et hors configuration hôte déclarée n’a été créé ou
modifié, et que `*.sqlite-wal`, `*.sqlite-shm` et `runtime/` restent ignorés.

**Coût :** faible. **Valeur :** c’est une promesse centrale du README, actuellement non gardée
par la suite.

---

## D. Hors périmètre MCP — décision produit attendue

### D1 — Dashboard configurateur visuel (§29 à §34)

**État :** non livré, et **volontairement hors du lot de finalisation MCP**. L’application
desktop est un assistant d’installation : sélection de dossier, scan, preview, confirmation,
installation. La spécification décrit un IDE de configuration en dix-huit étapes, avec éditeur
de taxonomie, registre visuel des entités et relations, configuration du work graph, éditeur de
policies, configuration du resume et des intégrations, et preview MCP avec métriques et
alertes.

**Ce n’est pas une dette du MCP.** C’est un autre produit, de l’ordre de plusieurs semaines de
travail d’interface. Il doit être planifié comme tel ou retiré de la cible.

**Recommandation :** trancher avant d’en écrire une ligne. Un demi-Dashboard coûte plus cher
qu’aucun.

---

## E. À faire par le propriétaire — hors de portée d’un agent

### E1 — Révoquer le jeton GitHub exposé

`todo.md` porte une ligne non cochée demandant la révocation d’un jeton jetable exposé lors
d’une session antérieure. **C’est le seul point de tout ce document qui présente un risque
aujourd’hui**, et non une dette de preuve. Deux minutes dans les réglages GitHub. À faire avant
tout le reste.

### E2 — Observer le parcours desktop interactif

**Déjà prouvé :** `tauri build --bundles deb` passe, le paquet contient l’application et le
sidecar, l’application démarre sous affichage virtuel, et le sidecar empaqueté répond en stdio
avec ses refus de nonce et de confirmation.

**Non prouvé :** le dialogue WebView ↔ Rust ↔ sidecar déclenché par la sélection humaine d’un
dossier. Le parent Rust ne démarre le sidecar qu’à cette action, qui ne peut pas être simulée
honnêtement en conteneur.

**Critère de sortie :** installer le `.deb`, lancer, choisir un dossier, vérifier que le scan
remonte dans la fenêtre. Dix minutes sur une machine avec écran.

### E3 — Preuves hôtes réelles par fournisseur

La barrière de reprise est câblée sur cinq adapters — Claude Code local et cloud, Codex, Gemini,
Antigravity — et rend un refus effectif, pas un avertissement. Ce qui manque est la preuve
qu’un hôte réel appelle bien ces hooks. Chaque fournisseur exige un verdict séparé. Pour Claude
Code cloud, la spécification impose un preview réel puis **deux confirmations distinctes** avant
la seule écriture user-scope.

---

## Ordre recommandé

1. **E1** — révocation du jeton, immédiat et indépendant de tout.
2. **A1** — laisser la CI Windows conclure ; traiter ses échecs s’il y en a.
3. **B1** — trancher la parité ARET, car c’est elle qui décide de ce que le produit a le droit
   de dire de lui-même.
4. **C3** — prouver Zero Pollution : coût faible, promesse centrale aujourd’hui non gardée.
5. **B2 puis B3** — scanner complet, puis recommandation qui s’appuie dessus.
6. **C1 et C2** — étudier avant d’écrire ; une décision documentée vaut mieux qu’un provider
   non exercé.
7. **D1** — décider du Dashboard, et ne commencer que si la décision est de le faire entièrement.
8. **E2 et E3** — observations hôtes, au fil des occasions réelles.

## Ce qu’il ne faut pas faire

- Promouvoir une ligne du registre de découplage sans test de parité exécuté.
- Recréer une mémoire SQLite absente dans la réparation : cela masquerait une base perdue.
- Compléter le scanner en lisant le contenu des fichiers : le scan reste une observation de
  surface, sans lecture, sans exécution, sans réseau.
- Écrire un provider VCS sans utilisateur réel pour l’exercer.
- Revendiquer le Dashboard configurateur tant que le parcours en dix-huit étapes n’existe pas.
