# Architecture de départ

## Intention

VeriChronicle est un moteur de continuité de projet qui sépare les mécanismes vérifiables des spécialisations de domaine. Le modèle ou l’IDE est un client du système ; il n’est ni le registre canonique ni l’autorité de preuve.

```text
Project Profile + Domain Packs + Capability Catalog + Policies
                              │
                              ▼
                    Compiler / Validator
                              │
                              ▼
                 Immutable Runtime Manifest
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
         MCP Core API    Runtime Adapter   Generated Docs
              │               │                │
              └───────────────┼────────────────┘
                              ▼
          Memory / Evidence / Work / Gate / Audit Core
                              │
                              ▼
                         SQLite + Artifacts
```

## Responsabilités

| Couche | Responsabilité | Interdictions |
|---|---|---|
| **Core** | Adressage, identité de projet, transactions, mémoire, audit, evidence, bundle, policies et contrats abstraits. | Connaître un outil, un corpus, une doctrine ou un vocabulaire d’un domaine. |
| **Project Profile** | Déclarer le projet, l’espace de travail, les taxonomies, les capacités sélectionnées, les gates, les policies et les intégrations. | Introduire du code exécutable arbitraire ou contredire les invariants Core. |
| **Domain Pack** | Fournir des types, templates, capabilities, validators et documentation propres à un domaine. | Écrire dans le Core ou rendre des dépendances métier obligatoires pour d’autres profils. |
| **Capability Engine** | Résoudre une capability de liste fermée, valider ses paramètres, appliquer une policy, lancer un runner sûr et persister l’execution. | Accepter une commande client, un chemin non borné ou une URL arbitraire. |
| **Gate Engine** | Évaluer des predicates objectifs sur executions/evidence/artefacts et calculer l’état d’un travail. | Marquer une gate satisfaite à partir d’une déclaration non vérifiée. |
| **MCP Compiler** | Normaliser les entrées, calculer les hashes et produire un manifeste de runtime, des instructions, des hooks, une configuration et des documents. | Générer un serveur non contrôlé qui exécute du code de profil. |
| **Runtime Adapter** | Installer, générer et valider l’intégration d’un runtime agent/IDE. | Modifier le code métier du projet sans policy et confirmation explicites. |
| **Dashboard** | Éditer des déclarations, prévisualiser la surface et appeler la même validation que la CLI. | Devenir une seconde source de vérité ou contourner la compilation déterministe. |

## Décisions initiales

Le package Python est `verichronicle`, le nom de distribution envisagé est `verichronicle`, et la CLI publique envisagée est `mmu`. La configuration du projet résidera sous `.mmu/`; le format canonique prévu est `.mmu/project.yaml`. Les nouveaux objets utiliseront le schéma d’adressage `mmu://<project>/<resource>/<id>`.

Le serveur MCP ne doit pas être généré comme un nouveau programme Python pour chaque projet. La compilation produit un manifeste immuable et des fichiers d’intégration ; un serveur universel charge ce manifeste et ne résout que des capacités et outils enregistrés. Cette approche réduit la surface de code généré et permet au doctor de détecter les divergences de profil, de pack ou d’adaptateur.

## Décision d’implémentation immédiate

La première tranche porte seulement sur le profil, l’identité, l’adressage et les contrats de données. Les migrations de schéma, le store SQLite complet, les runners, les gates et les hooks seront introduits après avoir défini leurs tests de sécurité et de conformance.

## Correctif de rendu

Le diagramme textuel ci-dessus est conceptuel. La relation attendue est : les entrées déclaratives sont validées et compilées en manifeste ; les adaptateurs et l’API MCP consomment ce manifeste ; tous les chemins persistants reposent sur le Core et sur le store canonique.
