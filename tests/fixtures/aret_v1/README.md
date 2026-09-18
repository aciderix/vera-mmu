# Références ARET V1 — données de test, jamais du code de production

Ce répertoire contient des **copies de référence** issues du dépôt `aciderix/ARET-MMU`, commit
`b9511dccc811b5fc2efaf26a7a3cfc941c0e5754`. Elles n'existent que pour donner aux tests de parité un
second implémenteur et des données réelles contre lesquels comparer, afin que la comparaison porte
sur le comportement V1 observé et non sur l'idée qu'on s'en fait.

| Fichier | Origine | Rôle |
|---|---|---|
| `addressing_reference.py` | `aret-memory/core/addressing.py`, copie octet pour octet | Second implémenteur du test de parité `C01` |
| `baseline_addresses.json` | 22 adresses `ARET://` extraites de `aret-memory/.aret-memory/aret_memory.sqlite` | Corpus réel du test de parité `C01` |

**Deux règles.**

1. `tests/test_aret_c01_addressing_parity.py` épingle le SHA-256 de `addressing_reference.py` et la
   taille et le SHA-256 de la mémoire baseline dont les adresses proviennent. Si l'une dérive, le
   test échoue plutôt que de comparer VERA à une référence périmée en silence.
2. **Rien dans `src/vera_mmu/` ne doit lire ce répertoire.** Le Core ne connaît pas ARET ; c'est la
   propriété que `C01` doit démontrer, pas une qu'il peut supposer.

La mémoire baseline elle-même n'est pas versionnée ici : 11 Mo de SQLite pour vingt-deux adresses
serait payer cher une donnée que l'on peut extraire et attester par son empreinte.
