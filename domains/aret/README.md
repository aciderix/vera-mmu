# ARET Domain Pack — statut de conception

ARET est le premier **client de compatibilité** envisagé pour VeriChronicle. Ce répertoire ne contient volontairement aucun code, script, corpus, binaire ni document provenant d’ARET-MMU.

Le futur pack devra fournir, dans un format déclaré et versionné :

| Élément | Rôle dans le pack |
|---|---|
| Profil ARET | Taxonomie, Front, reprise, policies et intégration correspondant au projet ARET. |
| Lecteur de migration V1 | Import explicite et hors ligne de sources/bundles ARET, avec rapport de transformation. |
| Compatibilité d’adresses | Lecture transitoire des adresses `ARET://…`; toute nouvelle écriture utilise `mmu://…`. |
| Capabilities | Pipelines, validators et exigences de toolchain ARET, entièrement confinés au pack. |
| Gates | Critères de validation ARET fondés sur des executions et evidence réelles. |
| Playbook | Doctrine métier ARET distincte de la doctrine universelle. |
| Suite de parité | Tests qui démontrent que les propriétés ARET retenues restent équivalentes ou meilleures. |

## Contrat de non-dépendance

Le Core doit s’installer et fonctionner avec le seul profil minimal, sans connaître PE32, Win32, DLL, Wine, MinGW, Unicorn, x87, calling conventions, reverse engineering, `target/release/aret`, `bench/*`, ni les documents et identifiants historiques ARET.

Toute future extraction doit respecter les droits de réutilisation applicables et consigner une provenance de source explicite. Le pack ne sera ajouté qu’après validation de cette gouvernance et après définition du mécanisme d’import sans écriture dans le dépôt source.
