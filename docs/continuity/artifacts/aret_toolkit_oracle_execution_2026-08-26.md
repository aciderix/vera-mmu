# Exécution contrôlée des oracles ARET restaurés — 2026-08-26

**Statut documentaire :** observation externe reproductible ; **non admissible comme preuve VERA**.
**Verdict de compatibilité :** `M4.EXIT = NOT_ELIGIBLE` inchangé.

## 1. Objet et frontière de preuve

Ce rapport documente la première exécution réelle des scripts d’oracle issus de la branche toolkit fournie par l’utilisateur. Son objectif est strictement de vérifier si `MEM-WALL-001` — l’absence antérieure de source, scripts, corpus et toolchain — correspondait à une indisponibilité matérielle restaurable. Il ne transforme pas une sortie shell en `evidence`, `admission`, `proof`, gate `PASS` ou connaissance `PROVEN` dans VERA.

> Les scripts ont été exécutés directement depuis le clone de référence isolé. Comme C07/C08 ne disposent pas encore du runner/capability/doctor ARET intégré et autorisé dans VERA, les résultats ci-dessous sont des **observations externes hashées**. Toute promotion exigerait ultérieurement une chaîne VERA autorisée, normalisée, auditée et admissible.

La baseline `/home/ubuntu/ARET-MMU` n’a été ni modifiée ni utilisée comme worktree d’exécution. Le clone toolkit est resté propre au commit verrouillé après la construction et les runs.

## 2. Identité de la référence et reproductibilité

| Élément | Valeur observée |
|---|---|
| Dépôt de référence | `aciderix/Automatic-reverse-engineering-toolkit` [1] |
| Branche fournie | `claude/aret-mcp-startup-check-5a13sx` [1] |
| Commit exécuté | `7a0429790bb04d1ad3c1819449e906140ebf4513` |
| État Git du clone à la clôture | propre (`git status --porcelain` vide) |
| Rust/Cargo de build | `rustc 1.85.0`, `cargo 1.85.0` |
| Hash `Cargo.lock` | `61ddff98a7c8f4cf02945dd9a98bb5bc0794f178678bf1e9547194ff3e47739f` |
| Binaire reconstruit | `/home/ubuntu/aret-toolkit-build/release/aret` |
| SHA-256 du binaire | `6ca52f0955266aeda31d235caacf0844e2516f41d67468632f2ddb1bb1e16a19` |
| Répertoire de build | externe au clone : `/home/ubuntu/aret-toolkit-build` |
| Préfixe Wine | temporaire : `/tmp/aret-toolkit-wineprefix-20260826` |

Le système Ubuntu fournissait GCC avec support 32 bits, MinGW i686, Wine 9.0, Clang/LLD 18, zstd et `libunicorn-dev`. La liste exacte des versions de paquets, hashes des scripts, commandes, sorties et sommes de contrôle est préservée dans [`aret_toolkit_oracle_run_2026-08-26/`](aret_toolkit_oracle_run_2026-08-26/).

## 3. Construction et incident de version Rust

Le Cargo fourni par Ubuntu (`1.75`) ne peut pas lire le lockfile v4. Rust/Cargo `1.79` lit le lockfile mais échoue sur la dépendance `clap_lex 1.1.0`, qui requiert l’édition Rust 2024. La construction a donc été exécutée explicitement avec Rust/Cargo `1.85.0`, première version stable sélectionnée ici compatible avec ce lockfile et cette édition.

| Étape | Résultat | Interprétation |
|---|---|---|
| `cargo 1.75 --locked --release` | refus de lockfile v4 | prérequis trop ancien ; pas un résultat ARET |
| `cargo 1.79 --locked --release` | refus de l’édition 2024 dans `clap_lex` | prérequis trop ancien ; pas un résultat ARET |
| `rustup run 1.85.0 cargo build --locked --release` | succès ; 4 avertissements `dead_code` | binaire construit de manière verrouillée |

Aucune modification n’a été apportée au `Cargo.lock`, aux scripts ni au corpus. L’échec de `funcdiff` lors du premier run provenait du même choix implicite de Cargo 1.79 ; la relance avec `RUSTUP_TOOLCHAIN=1.85.0` est explicitement consignée et a remplacé ce `SKIP` par une exécution effective.

## 4. Résultats des scripts fermés

| Oracle/script | Résultat brut | Statut épistémique ici | Observation déterminante |
|---|---:|---|---|
| `bench/difftest.sh` | `272/272`, exit 0 | `OBSERVED_PASS` | 68 fonctions équivalentes pour chacun de `-O0`, `-O1`, `-O2`, `-O3`; aucune instruction non modélisée dans ce corpus. |
| `bench/difftest_transpile.sh` | `4/4`, exit 0 | `OBSERVED_PASS` | 58 fonctions ; hash de référence `19acad982194bf07` pour chaque niveau d’optimisation. |
| `bench/stdcall_audit.sh` | `PASS`, exit 0 | `OBSERVED_PASS` | 1 335 shims, 865 décorations `__stdcall` prouvées ; 0 `@N` manquant. |
| `bench/ehdiff.sh` | `6/6`, exit 0 | `OBSERVED_PASS` | Différentiel d’exceptions MSVC sur les six fixtures disponibles. |
| `bench/gnuehdiff.sh` | `7/7`, exit 0 | `OBSERVED_PASS` | Différentiel C++ GNU/Itanium ; les DLL runtime MinGW attendues ont été trouvées et utilisées. |
| `bench/funcdiff.sh` avec Cargo 1.79 implicite | `SKIP`, exit 0 | `SKIPPED` | Échec de build masqué par le script ; confirmé ensuite comme incompatibilité de version Rust/Cargo. |
| `bench/funcdiff.sh` avec `RUSTUP_TOOLCHAIN=1.85.0` | `PASS`, exit 0 | `OBSERVED_PASS` | 22 672 fonctions liftées et 11 602 optimisées ; 0 divergence dans le corpus BusyBox/SQLite. |
| `bench/winoracle/wine_hashes.sh` | exit 0 | `OBSERVED_PARTIAL` | 155 lignes `OK`, 14 `BUILD-FAIL` et 90 `SKIP` explicitement signalés. La forme de sortie reste incompatible avec le normaliseur historique : `<fixture> OK <hash>` au lieu de `OK <hash>`. |
| `bench/winediff.sh` | `255/264`, exit 1 | `OBSERVED_FAIL` | 9 divergences ; l’oracle strict échoue et ne peut donc pas être normalisé en `PASS`. |

Les sorties brutes et leur SHA-256 figurent dans le dossier d’artefacts associé. Aucun `SKIP`, `BUILD-FAIL`, résultat partiel ou `FAIL` n’a été reclassé en succès.

## 5. Analyse bornée de l’échec Wine

`winediff.sh` a produit neuf divergences : `gui_paint_text`, `ole_mlang`, `user32_classex`, `user32_dbuffer`, `user32_erasebg`, `user32_menu2`, `user32_paint`, `user32_sdlwindow` et `win32_username`.

| Groupe | Nombre | Fait observé | Conclusion autorisée |
|---|---:|---|---|
| Fixtures graphique / User32 | 8 | Les divergences concernent les fenêtres, menus, peinture et buffers dans une session Wine sans affichage interactif. | Hypothèse environnementale plausible ; **pas** une exemption ni une normalisation automatique. |
| Identité utilisateur | 1 | `win32_username` compare notamment `root` sous Wine à `ubuntu` côté natif. | Sortie dépendante de l’environnement ; **FAIL** maintenu tant qu’une normalisation contractuelle n’est ni définie ni validée. |
| DLL runtime MinGW | 0 blocage confirmé | Le différentiel GNU C++ a passé `7/7` après résolution des DLL `libstdc++-6.dll`, `libgcc_s_dw2-1.dll` et `libwinpthread-1.dll`. | L’absence globale de DLL runtime ne constitue pas l’explication des neuf divergences Wine. |

Les 14 `BUILD-FAIL` du script de hashes Wine ne sont pas assimilés à des DLL manquantes. Le script émet aussi des sauts explicitement catégorisés (`SKIP-gui`, `SKIP-nodisplay`, `SKIP-gcc-only`). Une investigation future doit distinguer, fixture par fixture, les contraintes de compilation des exigences de runtime avant toute adaptation de normaliseur.

## 6. Effet exact sur MEM-WALL-001, C07 et C08

La sous-partie factuelle de `MEM-WALL-001` relative à l’absence de la source toolkit, des scripts, du corpus, des compilateurs et du binaire construit est **levée en observation** : le commit fourni a été construit et les scripts ont réellement été exécutés. La wall n’est toutefois **pas clôturée au sens VERA**.

| Élément | État après run | Motif fail-closed |
|---|---|---|
| Disponibilité de la référence / toolchain | `OBSERVED_RESTORED` | Source, corpus, scripts et binaire existent et ont été utilisés à une révision verrouillée. |
| C08 — préconditions / doctor / recette de dépendances | `IN_PROGRESS` | Le pack ARET ne déclare pas encore ces dépendances dans un `DomainPack.dependencies` et M6 ne fournit pas le `doctor` générique requis. |
| C07 — capability / normalisation / evidence | `IN_PROGRESS` | Aucune capability VERA autorisée n’a exécuté, normalisé, hashé et admis ces sorties. Le delta `winehash` n’est pas corrigé/testé. |
| Oracle Wine de parité | `OBSERVED_FAIL` | `winediff` est à `255/264` ; aucune exception n’est approuvée. |
| Parité ARET | `UNKNOWN` | Les oracles partiels ne couvrent pas toutes les surfaces contractuelles, notamment la chaîne VERA, hooks, bundles, VCS, runtime et MCP. |
| `M4.EXIT` | `NOT_ELIGIBLE` | Des gates M4, C01–C16, M5/M6 et la parité globale restent incomplètes ; un seul `FAIL` Wine suffit de toute façon à interdire `PASS`. |

Cette évolution est **un déblocage de prérequis observé**, non une clôture de C07, C08, M4-D, M4-F ou M4.EXIT. Elle ne modifie ni l’état `PROVEN` de VERA ni la source ARET-MMU.

## 7. Prochaines actions autorisées

La suite techniquement légitime consiste à créer, dans le Domain Pack ARET et sous contrat test-first, une déclaration fermée de dépendances/outils et une capability qui ne reçoit aucune commande arbitraire. Elle devra conserver le commit, les hashes de scripts/binaire, le corpus, le timeout, l’environnement, stdout/stderr et un normaliseur strict des verdicts. Le cas `winehash` devra accepter son format réel ou le refuser explicitement, par tests ; il restera non promouvable tant qu’un contrat d’admissibilité ne l’autorise pas.

Parallèlement, les neuf divergences Wine doivent être reproduites fixture par fixture dans un environnement d’affichage et d’identité contrôlé. Aucun filtrage, suppression de fixture ou comparaison affaiblie ne peut être adopté sans contrat de normalisation, baseline et test de non-régression. M5/M6 restent nécessaires pour fournir le runner, le doctor, le registre d’outils, les hooks, l’installation et les surfaces de comparaison exigées par la sortie M4.

## Références

[1]: https://github.com/aciderix/Automatic-reverse-engineering-toolkit/tree/claude/aret-mcp-startup-check-5a13sx "Branche toolkit ARET fournie, commit exécuté 7a042979"
[2]: ../M4_COMPLETION_REGISTER.md "Registre canonique des gates M4 et conditions de M4.EXIT"
[3]: ../DECOUPLING_MATRIX.md "Matrice C01–C16 et définition de MEM-WALL-001"
[4]: aret_toolkit_oracle_run_2026-08-26/ "Logs, métadonnées, versions et SHA-256 de l’exécution contrôlée"
