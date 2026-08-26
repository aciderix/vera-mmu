# Vérification de restauration de la toolchain ARET — 26 août 2026

> **Verdict : `BLOCKED — MEM-WALL-001` confirmé.** Cette vérification est passive : aucun paquet, binaire, script, checkout ou artefact ARET n’a été installé, exécuté ou modifié.

## Périmètre contrôlé

Le catalogue fermé des oracles ARET exige au minimum les exécutables et artefacts suivants : `gcc`, Cargo, Wine, les cross-compilateurs MinGW 32 bits, Clang/LLVM, `zstd`, le binaire `target/release/aret`, les scripts `bench/*` et, pour `cpudiff`, `Cargo.toml`/`src/cpudiff.rs`.[1]

| Classe | Résultat local | Conséquence |
|---|---|---|
| Exécutables de base | `bash` et `python3` présents; `gcc`, Cargo, Wine, MinGW, Clang/LLVM et `zstd` absents. | Les oracles ne peuvent pas démarrer. |
| Artefacts ARET d’oracle | `target/release/aret`, les huit scripts `bench/*`, `Cargo.toml` et `src/cpudiff.rs` absents du checkout propre au commit `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`. | Même une installation de paquets ne rétablirait pas une exécution reproductible. |
| Hook de session | Le hook versionné ne fait que bootstrapper le venv MCP; son script n’installe que `mcp`. | Il ne constitue pas une procédure de restauration de Wine/MinGW/Cargo/corpus. |
| Références Git locales | Les branches locales et de suivi disponibles ne contiennent ni `bench/`, ni `Cargo.toml`, ni `src/cpudiff.rs`. | Aucune restauration possible depuis l’historique déjà présent. |
| Références GitHub publiques | Les quatre branches publiques accessibles (`main` et trois branches de travail) ont été vérifiées par leur arbre Git; aucune ne contient les artefacts manquants. | Aucune référence officielle publiquement accessible ne permet un checkout attestable des oracles. |

## Décision

Installer des dépendances systèmes ou recopier des scripts issus d’une source non attestée créerait une toolchain différente de la baseline et ne satisferait pas les gates C07/C08. La seule récupération admissible nécessite un **bundle ou une révision ARET attestée** qui fournisse simultanément le corpus, les scripts, le binaire ou ses instructions de build reproductible, ainsi que les versions attendues des dépendances.

> Tant que cet artefact de référence n’est pas fourni, `M4-EXIT-09` et `M4-EXIT-10` restent `BLOCKED`, la parité reste `UNKNOWN` et `M4.EXIT` reste `NOT_ELIGIBLE`.

## Références

[1]: ../../../ARET-MMU/aret-memory/evidence/adapters/oracles.py "Catalogue fermé des neuf oracles ARET et dépendances"
[2]: ../../../ARET-MMU/aret-memory/docs/CONTRAT_ORACLES.md "Contrat des adaptateurs d’oracles ARET"
[3]: ../M4_COMPLETION_REGISTER.md "Gates M4-EXIT-09 et M4-EXIT-10"
