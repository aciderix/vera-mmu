# M10 — Contrat de smoke tests d’exécution de distribution

**Statut :** `PARTIAL_PASS` — démarrage Linux attesté localement puis sur runner Ubuntu natif ; chaîne Windows CLI/NSIS observée, mais démarrage MSI laissé à une vérification manuelle distincte. Aucun de ces résultats ne requalifie la préversion rc.4, qui demeure non signée.

**Objet.** Compléter les validations de compilation/package existantes par une preuve bornée que les exécutables réellement produits peuvent démarrer sur les runners natifs. Ce lot ne prétend pas reproduire une machine d’utilisateur, un compte réel ni un agent réel.

| Plateforme | Binaire / paquet contrôlé | Action | Succès | Limite explicite |
|---|---|---|---|---|
| Linux x64 | CLI `.tar.gz` | extraction sûre, `--help`, `scan` sur projet temporaire | aide répond, scan `OBSERVED`, aucune `.vera-mmu/` créée | pas une installation système |
| Linux x64 | AppImage | lancement sous Xvfb, observation huit secondes, arrêt | processus vivant avant arrêt contrôlé | pas de clic ni sélection dossier réelle |
| Linux x64 | `.deb` | extraction du payload, lancement sous Xvfb, arrêt | exécutable payload vivant | pas de `dpkg -i` sur un poste réel |
| Windows x64 | CLI `.zip` | extraction, `--help`, scan observationnel | commandes répondent, zéro écriture VERA | pas un shell utilisateur réel |
| Windows x64 | NSIS `.exe` | installation silencieuse dans dossier runner, lancement, arrêt | installateur retourne 0 et application vivante | pas de test UI humain |
| Windows x64 | MSI `.msi` | installation silencieuse temporaire, lancement, arrêt | `msiexec` 0/3010 et application vivante | pas de persistance machine utilisateur |

Avant toute exécution, les scripts recalculent les hashes du manifest de candidat et de `SHA256SUMS`; ils refusent les symlinks, noms ambigus, archives CLI à entrées non régulières, checksum auto-référent ou toute sortie absente. La CLI lance uniquement `--help` et `scan`, qui est contractuellement observationnel. Les applications sont arrêtées après huit secondes : aucun chemin de sélection, bridge, MCP, installation project-local ou réseau n’est fourni.

Les smoke tests sont ajoutés à `release-candidate.yml` avant l’upload des candidats. Une version de release n’obtient donc un verdict de démarrage que si les tests VERA, les builds, l’assemblage et ces checks réussissent sur les deux runners.

> Ces tests attestent « le paquet démarre dans un runner natif ». Ils n’attestent pas « l’application est fonctionnelle pour un utilisateur », ce dernier verdict requiert une installation manuelle sur machines réelles et un parcours preview → confirm → install observé.

## Observation locale Linux

Le candidat Linux courant a été reconstruit depuis le commit propre M10 : sidecar PyInstaller, CLI autonome, AppImage et Debian. La CLI a été extraite de son archive avant exécution ; l’AppImage et le binaire `vera-mmu-desktop` extrait du `.deb` ont été lancés sous Xvfb, observés vivants huit secondes, puis arrêtés par groupe de processus.

| Contrôle local | Résultat |
|---|---|
| Tests helper smoke + assembleur | `9 passed` |
| Suite VERA après durcissement | `517 passed, 43 subtests passed` |
| Intégrité du candidat | manifest + `SHA256SUMS` valident toutes les entrées |
| CLI extraite | `vmmu --help` et `vmmu scan` `OBSERVED`, aucune `.vera-mmu/` ajoutée |
| AppImage | démarrage sous Xvfb confirmé, arrêt propre |
| Payload Debian | extraction et démarrage de `vera-mmu-desktop` sous Xvfb confirmés, arrêt propre |
| Résidus | aucun processus VERA-MMU / Xvfb après le smoke corrigé |

Le premier essai a fait apparaître deux erreurs du **smoke test**, non du paquet : un ancien `.deb` dans `target/release/bundle` rendait la découverte ambiguë, et Xvfb pouvait laisser le processus enfant d’une exécution antérieure vivant après l’arrêt du wrapper. L’assembleur filtre désormais les bundles par version courante et le smoke utilise une session/groupe de processus puis `killpg`. Le paquet Debian utilise le vrai exécutable `vera-mmu-desktop`, non le nom d’affichage ni le sidecar.

## Matrice native M10 et décision de périmètre

| Run GitHub Actions | Révision | Résultat utile | Interprétation exacte |
|---|---|---|---|
| `33088157116` | `0ab1f2b` | Linux réussi ; Windows arrêté avant exécution par une erreur de parseur PowerShell. | Le défaut portait sur le script de smoke, pas sur un binaire Windows : une apostrophe typographique pouvait fermer une chaîne PowerShell. Aucun démarrage Windows ne peut être déduit de ce run. |
| `33089780117` | `1f81421` | Linux x64 réussi en 9 min 17 s ; le smoke Linux a pris 18 s après build et assemblage natifs. | Le runner Ubuntu a reconstruit le candidat, validé son intégrité puis exécuté la CLI, l’AppImage et le payload Debian. Cette preuve complète la vérification locale indépendante. |
| `33089780117` | `1f81421` | Windows a passé tests, build, assemblage, CLI et chemin NSIS ; `msiexec` retourne `0`, puis le smoke ne retrouve pas le répertoire temporaire supposé. | Le script n’a donc pas lancé l’exécutable issu du MSI. Il ne faut pas qualifier le démarrage MSI `PASS`. La vérification est volontairement laissée au propriétaire sur une machine Windows. |

La correction du parseur est confinée à `scripts/smoke_windows_release.ps1`, avec une régression qui interdit les apostrophes typographiques dans les chaînes PowerShell. Les tests ciblés passent (`5 passed`) puis la suite complète passe à **`518 passed, 43 subtests passed`**. Cette correction ne change ni le Core, ni le bridge, ni le contenu des installateurs.

> **Décision opérationnelle du propriétaire.** À ce stade, le seuil recherché est uniquement « le livrable démarre ». Il n’est pas demandé de poursuivre l’automatisation MSI ni de tester une UX, une installation utilisateur complète, le bridge, le MCP ou un agent. Le MSI sera démarré manuellement sur une machine Windows ; la présente documentation conserve donc son statut `PARTIAL_PASS` au lieu d’inventer une réussite.

## Verdict M10

Le démarrage des voies Linux distribuées est **`PASS` au niveau smoke** : CLI, AppImage et payload Debian sont exécutés localement et sur un runner Ubuntu GitHub Actions neuf. La CLI reste observationnelle et les applications sont arrêtées après observation contrôlée. La chaîne Windows est **partiellement observée** : CLI et NSIS ont atteint leur contrôle de démarrage dans le runner, tandis que le MSI n’a pas été lancé faute de localisation fiable de son répertoire réel après une installation silencieuse pourtant retournée avec succès.

Cette conclusion ne prétend pas démontrer la qualité interactive ou une installation utilisateur. Elle ne transforme pas la préversion `v0.1.0-rc.4` en release stable, et ne retire pas les prérequis de signature et de validation manuelle.
