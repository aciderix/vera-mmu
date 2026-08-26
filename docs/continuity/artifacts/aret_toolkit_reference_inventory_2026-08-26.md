# Inventaire de la référence ARET fournie — 26 août 2026

> **État : `OBSERVED`.** Cette branche fournit les sources nécessaires à une étude de restauration contrôlée; elle ne constitue pas encore une toolchain exécutée, ni une preuve de parité, ni une substitution de la baseline ARET-MMU.

| Élément | Valeur observée |
|---|---|
| Dépôt | `aciderix/Automatic-reverse-engineering-toolkit` |
| Branche | `claude/aret-mcp-startup-check-5a13sx` |
| Commit verrouillé | `7a0429790bb04d1ad3c1819449e906140ebf4513` |
| Checkout de référence | `/home/ubuntu/aret-toolkit-reference` |
| État Git | propre après clonage superficiel mono-branche |
| Différence de rôle | Ce dépôt contient le toolkit ARET; il est distinct du checkout ARET-MMU de baseline `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. |

## Artefacts d’oracle observés

| Contrat requis par ARET-MMU | Présence dans la référence |
|---|---|
| `Cargo.toml` et `Cargo.lock` | présents |
| `src/cpudiff.rs` | présent |
| `bench/difftest.sh` | présent |
| `bench/difftest_transpile.sh` | présent |
| `bench/stdcall_audit.sh` | présent |
| `bench/winediff.sh` | présent |
| `bench/winoracle/wine_hashes.sh` | présent |
| `bench/ehdiff.sh` | présent |
| `bench/gnuehdiff.sh` | présent |
| `bench/funcdiff.sh` | présent |
| Corpus de régression sous `bench/` | présent, incluant le corpus Wine et des fixtures de lift/diff. |

Le binaire compilé `target/release/aret` n’est pas versionné, ce qui est attendu : il devra être reconstruit de façon reproductible à partir de ce commit, après vérification des scripts, dépendances et sorties attendues.

## Décision provisoire

La référence fournie est **matériellement pertinente** pour remplacer l’absence auparavant constatée des scripts/corpus/build ARET. La phase suivante doit vérifier que son interface, ses chemins, ses scripts et ses attentes sont compatibles avec le catalogue fermé d’oracles de l’ARET-MMU de baseline. Aucun script ni build n’a encore été exécuté.

## Références

[1]: https://github.com/aciderix/Automatic-reverse-engineering-toolkit/tree/claude/aret-mcp-startup-check-5a13sx "Branche ARET fournie"
[2]: ../../../ARET-MMU/aret-memory/evidence/adapters/oracles.py "Catalogue fermé d’oracles ARET-MMU"
