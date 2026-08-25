# Audit de nommage — VERA / VERA-MMU

**Objet :** évaluer les collisions et la confusion potentielle autour de VERA, VERA-MMU et du schéma d’adressage `vera://` pour un moteur MCP de mémoire, de provenance et de preuve.

## Faits déjà vérifiés

| Source | Fait établi | Risque de confusion |
|---|---|---|
| [Vera Language](https://veralang.dev/) | Vera est un langage de programmation actif, explicitement conçu pour les LLM, fondé sur des contrats obligatoires, des effets typés et la vérification. Le site renvoie à un CLI, un langage server, un outil de benchmark et des documents destinés aux agents. | **Élevé.** Même audience d’agents/LLM, même registre de vérifiabilité, conflit de nom de CLI `vera` et risque élevé pour `vera://`. |
| [aallan/vera](https://github.com/aallan/vera) | Dépôt de référence du langage Vera conçu pour les LLM. | **Élevé.** Collision directe dans la recherche GitHub et la documentation d’outillage IA. |
| [VERA — Virtual Engine Reasoning Agent](https://www.fab.com/listings/e713a106-64e2-49cf-86f8-e03c7c3e9c31) | Projet d’agent destiné à surveiller les erreurs d’Unreal Engine ; les résultats publics indiquent une intégration MCP. | **Moyen à élevé.** Produit différent mais même catégorie « agent / MCP ». |
| [NVIDIA Vera CPU](https://www.nvidia.com/en-us/data-center/vera-cpu/) | Marque de processeur d’infrastructure IA NVIDIA. | **Moyen.** Très forte présence attendue dans l’écosystème IA/infrastructure. |

## Disponibilité de la forme composée

Le 25 août 2026, des requêtes publiques non authentifiées ont répondu `404` pour `aciderix/vera-mmu` dans l’API GitHub, `vera-mmu` dans l’API PyPI et `vera-mmu` dans le registre npm. Cela suggère que le **slug** et les noms de package composés ne sont pas publiquement occupés dans ces trois espaces au moment du contrôle. Une réponse `404` GitHub ne révèle pas l’existence éventuelle d’un dépôt privé, et aucun de ces contrôles ne vaut recherche de marque.

## Décision de différenciation

VERA est un nom fort, mais il n’est pas propre dans l’écosystème ciblé. Le projet adopte néanmoins la forme composée **VERA-MMU** afin de bénéficier de sa mémorisation et de sa différenciation de dépôt/package. Cette décision est assumée : elle ne signifie ni absence de collision, ni exclusivité sur le terme VERA.

La stratégie de différenciation est la suivante : employer systématiquement **VERA-MMU** comme nom public ; employer `vera-mmu` pour le dépôt et la distribution ; employer `vera_mmu` pour le namespace Python ; employer `vmmu` pour la CLI ; et réserver `vera://` au schéma canonique de ressources du projet. Toute évolution publique doit conserver cette forme composée et éviter de se présenter comme un langage, un moteur de raisonnement généraliste, un outil de recherche de code ou une plateforme matérielle.

## Références

[1]: https://veralang.dev/ "Vera — A programming language designed for LLMs to write"
[2]: https://github.com/aallan/vera "aallan/vera"
[3]: https://www.fab.com/listings/e713a106-64e2-49cf-86f8-e03c7c3e9c31 "VERA — Virtual Engine Reasoning Agent"
[4]: https://www.nvidia.com/en-us/data-center/vera-cpu/ "NVIDIA Vera CPU"
