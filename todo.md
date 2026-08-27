# Suivi — livraison desktop VERA

- [x] Documenter l’architecture desktop Windows/Linux, la séparation GitHub Pages et les frontières UI/Core.
- [x] Définir le contrat local fermé : sélection native de racine, opérations versionnées, preview, confirmation et refus.
- [x] Écrire les tests rouges du bridge local sans commande, chemin, adapter ou résultat de confiance fourni par l’interface.
- [x] Implémenter le bridge local autour des opérations VERA existantes et les tests de non-régression.
- [x] Concevoir la mémoire SQLite VERA project-local versionnable par GitHub, ses artefacts portables et une stratégie explicite de refus/résolution des conflits binaires.
- [x] Restaurer un push Git automatique policy-gated limité aux chemins mémoire VERA, avec refus des changements hors périmètre, conflits, remote ambigu ou échec réseau.
- [x] Créer l’enveloppe desktop Tauri et son interface d’installation project-local non destructive.
- [x] Construire et inspecter les distributions Linux x64 AppImage et Debian avec sidecar autonome embarqué.
- [x] Déclencher et vérifier la matrice native CI Windows/Linux (NSIS, MSI, AppImage, Debian) avant toute release.
- [x] Vérifier sur la matrice native les archives CLI Windows/Linux candidates, leurs manifests et leurs SHA-256 ; aucune release avant résultat des deux runners.
- [ ] Choisir une licence formelle, vérifier les droits de distribution et traiter `LICENSE-PENDING.md` avant toute release publique.
- [ ] Définir et exécuter la politique de signature Windows/Linux avec les clés du propriétaire, hors dépôt et après confirmation explicite.
- [x] Définir les fixtures de conformance VERA pour software, data, research, documentation, game et hardware.
- [x] Vérifier le parcours CLI/bridge project-local sur chaque fixture sans vocabulaire ni comportement propre au domaine dans le Core.
- [x] Vérifier no-Git, mono-repo, multi-repo et continuité de mémoire SQLite project-local via clone Git sans fusion binaire implicite.
- [x] Rejouer la matrice native Windows/Linux après le correctif de fermeture SQLite et d’alias de chemins Windows ; qualifier M8 uniquement avec les deux runners explicites.
- [x] Définir le contrat de release, la version unique, le modèle de notes et la séparation viewer GitHub Pages sans publication automatique.
