# Notes de release VERA-MMU — modèle factuel

> **Statut :** modèle non publiable. Compléter chaque champ avec des faits reliés à un commit, une matrice native et des hashes de release ; supprimer ce bandeau seulement après satisfaction de `REL-01` à `REL-08`.

## Version et intégrité

| Champ | Valeur à compléter |
|---|---|
| Version / tag | `v…` |
| Commit source | SHA complet |
| Date de publication | ISO 8601 UTC |
| Licence | Identifiant et texte versionné |
| SHA-256 | Lien vers `SHA256SUMS` |
| Signatures | Empreintes, algorithmes et procédure de vérification |

## Ce qui est livré

Décrire les surfaces et changements effectivement présents. Distinguer les fonctionnalités du Core, de la CLI, du desktop et du viewer. Relier chaque affirmation technique à une preuve de build ou de test.

## Artefacts

| Plateforme | Fichier | SHA-256 | Signature | Statut de vérification |
|---|---|---|---|---|
| Windows x64 | À compléter | À compléter | À compléter | À compléter |
| Linux x64 | À compléter | À compléter | À compléter | À compléter |

## Limites connues et non-promesses

Préciser notamment le statut réel des agents/hôtes, du viewer GitHub Pages, de l’installation user-scope, des mises à jour automatiques, des domaines métier et des plateformes non distribuées. Ne jamais convertir une couverture de fixture, un build CI ou une signature en preuve d’intégration hôte réelle.

## Vérification et rollback

Donner la commande de vérification du hash, de la signature, la procédure de désinstallation, les chemins project-local concernés et la stratégie de retour à la version précédente. Toute écriture MCP reste précédée de sa preview, de son contrôle de fraîcheur et de sa confirmation explicite.
