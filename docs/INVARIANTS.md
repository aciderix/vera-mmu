# Invariants non régressifs

Ces invariants constituent le contrat de sûreté de VeriChronicle. Toute évolution du Core doit indiquer lesquels elle affecte et ajouter ou préserver les tests associés. Un profil ou un Domain Pack peut renforcer ce contrat ; il ne peut pas l’affaiblir.

| ID | Invariant | Exigence vérifiable |
|---|---|---|
| I001 | **Le magasin canonique est externe au modèle.** | L’état durable est écrit dans le store et l’audit, jamais déduit d’un texte de conversation. |
| I002 | **FIND est distinct de READ.** | La recherche ne retourne pas le contenu canonique complet et ne vaut jamais preuve. |
| I003 | **Les connaissances sont append-only.** | Une correction crée une nouvelle version et une relation de supersession ; le contenu historique n’est pas réécrit. |
| I004 | **PROVEN exige une preuve admissible PASS.** | Une promotion est refusée sans evidence liée, vérifiable, `PASS` et admise par la policy. |
| I005 | **Les artefacts sont vérifiés avant lecture.** | Le hash stocké est contrôlé avant chaque lecture d’artefact adressée. |
| I006 | **Une sortie de shell brute n’est pas une preuve canonique.** | Seule une execution persistée suivie de l’admission de son evidence peut produire une preuve. |
| I007 | **Le catalogue de capabilities est fermé.** | Chaque capability est déclarée, validée, versionnée et résolue avant exécution. |
| I008 | **Aucune entrée client ne fabrique de commande arbitraire.** | Le moteur accepte des paramètres typés, pas une commande ou un interpréteur libre. |
| I009 | **La reprise est liée à un contrat hashé.** | Un accusé de reprise cesse d’être valide dès que le Front ou le contrat qui l’arme change. |
| I010 | **Les bundles portent une chaîne d’intégrité.** | Manifest, schéma, profil, mémoire et inventaire d’artefacts sont hashés et vérifiés avant import. |
| I011 | **Une mémoire reste liée à son projet.** | Toute restauration vérifie l’identité du projet et refuse l’injection canonique croisée. |
| I012 | **Le runtime généré est traçable.** | Les profiles, policies, catalogues, packs et adaptateurs contribuent à un `mcp_build_hash`. |
| I013 | **Les policies rendent une décision explicite.** | Chaque action contrôlée reçoit `ALLOW`, `DENY` ou `CONFIRM`, avec sa règle et son motif auditable. |
| I014 | **L’incertitude critique échoue bruyamment.** | Une identité, une migration, un hash ou une preuve incohérente ne doit pas se dégrader silencieusement. |
| I015 | **Le Core ignore le domaine.** | Aucun concept métier, binaire, outil, script, corpus ou vocabulaire d’un pack n’est requis pour installer le Core. |

## Convention de test

Chaque nouveau test doit référencer un ou plusieurs identifiants d’invariant dans son nom, sa docstring ou son commentaire. Les tests sont organisés par niveaux : unité, intégration de stockage, sécurité, conformance de profil et compatibilité de pack.

> Un comportement pratique qui contredit un invariant n’est pas une exception utile : il doit être représenté par une policy explicite, un nouveau type de ressource ou une révision documentée de l’invariant.
