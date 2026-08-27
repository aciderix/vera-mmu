# M10 — Contrat de smoke tests d’exécution de distribution

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
