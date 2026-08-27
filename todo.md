# Suivi — livraison desktop VERA

- [x] Documenter l’architecture desktop Windows/Linux, la séparation GitHub Pages et les frontières UI/Core.
- [x] Définir le contrat local fermé : sélection native de racine, opérations versionnées, preview, confirmation et refus.
- [x] Écrire les tests rouges du bridge local sans commande, chemin, adapter ou résultat de confiance fourni par l’interface.
- [x] Implémenter le bridge local autour des opérations VERA existantes et les tests de non-régression.
- [x] Concevoir la mémoire SQLite VERA project-local versionnable par GitHub, ses artefacts portables et une stratégie explicite de refus/résolution des conflits binaires.
- [x] Restaurer un push Git automatique policy-gated limité aux chemins mémoire VERA, avec refus des changements hors périmètre, conflits, remote ambigu ou échec réseau.
- [x] Créer l’enveloppe desktop Tauri et son interface d’installation project-local non destructive.
- [ ] Préparer et vérifier les distributions CLI et desktop Windows/Linux reproductibles.
