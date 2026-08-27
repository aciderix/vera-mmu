# M11 — Alias de lecture `mmu://` via MCP

**Verdict :** PASS pour la compatibilité de lecture d’entrée.

Une session MCP stdio réelle transmet une adresse `mmu://` à `mmu_read`. Le Core la parse par la compatibilité fermée et retourne une adresse `vera://` canonique. Ni l’identifiant SQLite, ni les adresses persistées, ni les sorties API ne changent de schéma.

| Contrôle | Résultat |
|---|---|
| Addressing et session MCP stdio | `9 passed in 10.81s` |
| Alias accepté | Lecture exacte uniquement |
| Sortie retournée | `vera://<project>/<resource>/<identifier>` |

Le lot ne fournit pas d’alias de mutation, d’alias de persistance, de migration d’adresse historique ou de parité ARET. Ces frontières restent fermées.
