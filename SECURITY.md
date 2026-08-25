# Politique de sécurité

## Portée actuelle

La fondation actuelle ne lance pas encore de processes, ne lit pas de secrets, ne contacte pas le réseau et ne fournit pas de serveur MCP opérationnel. Les exigences ci-dessous sont néanmoins des contraintes de conception non négociables pour les versions qui introduiront ces capacités.

## Principes de sûreté

| Surface | Exigence minimale |
|---|---|
| Commandes | Aucune commande shell libre reçue du client, du modèle ou d’un profil. |
| Paramètres | Validation typée, bornée et versionnée avant toute résolution. |
| Chemins | Racines autorisées explicites, résolution anti-traversal et contrôle des liens symboliques. |
| Réseau | Refus par défaut ; destination, méthode et consentement explicitement déclarés. |
| Écriture | Policy explicite et confirmation séparée pour les effets sensibles ou destructifs. |
| Secrets | Jamais sérialisés dans les profils, manifests, evidence, artefacts ou sorties MCP. |
| Artefacts | Hash de contenu vérifié avant lecture et inventaire dans chaque bundle. |
| Preuves | Admissibilité déterminée par policy, runner et validator ; une affirmation de modèle ne vaut pas preuve. |
| Dégradation | Incohérences de hash, identité, migration et signature signalées explicitement. |

## Signalement responsable

Ne publiez pas de vulnérabilité exploitable dans une issue publique. Utilisez le canal de contact du mainteneur indiqué par le propriétaire du dépôt lorsqu’il sera établi, en fournissant une reproduction minimale, l’impact et une suggestion de correction si possible.

## Secrets accidentellement exposés

Un jeton, mot de passe, clé privée ou secret publié doit être considéré comme compromis. Révoquez-le ou faites-le tourner immédiatement, puis supprimez sa trace des emplacements contrôlés lorsque cela est possible. Une suppression de fichier ne garantit pas l’effacement de l’historique ou des journaux tiers.
