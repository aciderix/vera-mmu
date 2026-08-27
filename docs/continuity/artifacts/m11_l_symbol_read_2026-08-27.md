# M11-L — Lecture exacte générique des symboles

**Date :** 2026-08-27  
**Baseline :** `34fffeb` — M11-K livré localement, `550 passed`.  
**Verdict :** `PASS` dans le périmètre M11-L.

## Portée

M11-L rend le type Core générique `symbol` lisible par le READ exact existant. Aucune grammaire d’adresse, commande CLI ou capacité MCP nouvelle n’est créée : `vmmu read <profile> vera://<project>/symbol/<id>` et `mmu_read({address})` délèguent au même `ReadService.read` que les autres ressources exactes.

| Contrat | Garantie effective |
|---|---|
| Identité | Adresse `vera://` canonique et identité du projet actif exigées. |
| Ressource | Uniquement `symbol/<id>` persistant; une adresse absente ou cross-project est refusée. |
| Record | Identifiant, propriétaire, kind déclaratif, path, identifier, signature, metadata JSON, création et adresse canonique sont relus du store. |
| FIND ≠ READ | `symbol` n’est pas ajouté à FIND; aucune description ou contenu de symbole n’est indexé ou retourné par découverte. |
| Core | `ReadService` délègue à `SymbolService.get`; aucune requête venant du client, chemin local, scanner ou résolution dynamique. |
| CLI | La CLI fournit seulement le profile local de lancement et l’adresse exacte, conformément au contrat READ existant. |
| MCP | `mmu_read` conserve un schéma exact `{address}`; aucun `project_id`, profile, commande, path libre ou filtre n’est exposé. |
| Non-mutation | Les lectures Core, CLI et MCP ne créent aucun audit, asset, evidence, execution ou relation. |

## Validation observée

```text
Contrat Core + CLI + MCP M11-L :          3 passed in 2.07s
Régressions lecture/CLI/MCP/symboles :   33 passed in 19.72s
Régression intégrale VERA :             553 passed in 67.48s
```

Le contrat vérifie le round-trip d’un symbole immuable avec metadata JSON, l’absence d’audit de lecture, le refus cross-project et introuvable, l’absence du symbole dans FIND, l’appel CLI réel et un appel MCP stdio réel dont le schéma n’accepte que `address`.

## Limites

Cette tranche ne fournit ni FIND/listing de symboles, ni filtrage par kind ou entité, ni scanning/résolution de code, ni accès de chemin local, ni import, mutation, evidence/proof, capability ou gate. Les alias `mmu://`, la compatibilité externe, le Dashboard et la parité ARET restent des chantiers distincts.
