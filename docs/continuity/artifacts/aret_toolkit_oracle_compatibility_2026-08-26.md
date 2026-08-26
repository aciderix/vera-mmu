# Compatibilité de la branche toolkit ARET avec les contrats d’oracle — 26 août 2026

> **Verdict : `COMPATIBLE_WITH_ONE_NON_BLOCKING_ADAPTER_DELTA`.** La branche fournie contient les scripts, le corpus et le manifest de build auparavant absents. Elle peut servir de référence de restauration contrôlée, mais aucun oracle n’a encore été exécuté.

## Vérification des chemins et signatures

Le catalogue fermé ARET-MMU attend neuf artefacts d’oracle à la racine d’un checkout toolkit et une signature de sortie normalisée.[1] Huit scripts et `src/cpudiff.rs` sont présents aux chemins attendus; le manifest `Cargo.toml` permet une reconstruction du binaire `target/release/aret` qui n’est pas versionné.

| Oracle du catalogue | Chemin attendu | État dans `7a042979` | Signature statique attendue | Compatibilité |
|---|---|---|---|---|
| `difftest` | `bench/difftest.sh` | présent | `differential equivalence:` | oui |
| `transpilediff` | `bench/difftest_transpile.sh` | présent | `transpile-pipeline equivalence:` | oui |
| `stdcall_audit` | `bench/stdcall_audit.sh` | présent | `stdcall-pop audit: PASS` | oui |
| `winediff` | `bench/winediff.sh` | présent | `OS-API (Wine) equivalence:` | oui |
| `ehdiff` | `bench/ehdiff.sh` | présent | `MSVC EH differential:` | oui |
| `gnuehdiff` | `bench/gnuehdiff.sh` | présent | `GNU/Itanium C++ EH differential:` | oui |
| `funcdiff` | `bench/funcdiff.sh` | présent | `funcdiff corpus gate: PASS` | oui |
| `cpudiff` | `src/cpudiff.rs` | présent | test Cargo `ok` | oui |
| `winehash` | `bench/winoracle/wine_hashes.sh` | présent | `OK <sha256>` selon le normaliseur actuel | écart mineur |

L’écart `winehash` est explicite : le script émet `"<fixture> OK <sha256>"`, alors que le normaliseur historique recherche `"OK <sha256>"` sans nom de fixture intermédiaire. Le script documente que ce résultat est une **mesure de comparaison Windows**, jamais une gate et jamais promouvable. L’adaptateur du Domain Pack devra donc accepter `OK` suivi d’un hash après un préfixe de fixture, tout en conservant le verdict `UNKNOWN`; il ne s’agit pas d’un chemin vers `PASS`.[2]

## Limites maintenues

La compatibilité de chemin et de format ne prouve pas que le build, Wine, les corpus, les oracles ou la parité fonctionnent. La reconstruction doit rester isolée du checkout ARET-MMU de baseline, utiliser le commit verrouillé `7a0429790bb04d1ad3c1819449e906140ebf4513`, journaliser les versions et échouer bruyamment si un prérequis manque.

## Références

[1]: ../../../ARET-MMU/aret-memory/evidence/adapters/oracles.py "Catalogue fermé d’oracles ARET-MMU"
[2]: https://github.com/aciderix/Automatic-reverse-engineering-toolkit/blob/claude/aret-mcp-startup-check-5a13sx/bench/winoracle/wine_hashes.sh "Script Wine hash et format de sortie"
