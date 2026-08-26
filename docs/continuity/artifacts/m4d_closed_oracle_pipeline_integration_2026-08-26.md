# Intégration réelle M4-D — pipeline d’oracle ARET fermé — 2026-08-26

**Statut :** observation VERA persistée dans des stores temporaires ; aucune admission, preuve dérivée, gate `PASS` ni promotion `PROVEN` créée.
**Verdict M4.EXIT :** `NOT_ELIGIBLE` inchangé.

## 1. Révision et chaîne exécutée

| Élément | Valeur observée |
|---|---|
| Référence toolkit | `aciderix/Automatic-reverse-engineering-toolkit` — commit `7a0429790bb04d1ad3c1819449e906140ebf4513`, checkout propre |
| Binaire ARET | `/home/ubuntu/aret-toolkit-build/release/aret`, SHA-256 `6ca52f0955266aeda31d235caacf0844e2516f41d67468632f2ddb1bb1e16a19` |
| Commit contrat fermé | `124670e` — catalogue, préflight, confinement de chemin et normalisation |
| Commit Core générique | `d204d28` — migration 037 et `OBSERVED_PROCESS` hash-bound |
| Commit runner Pack | `e5e7ca1` — capability déclarée, Git verrouillé, sandbox réseau, asset Core, execution et evidence |
| Confinement réseau | `unshare --user --map-root-user --net` ; son fonctionnement a été sondé avec succès avant les runs |
| Écriture source ARET-MMU | aucune ; `/home/ubuntu/ARET-MMU` reste hors du pipeline |

Le runner refuse la dérive de commit, un checkout toolkit non propre, un script qui résout hors dépôt, une fixture hors catalogue, une dependency manquante, un binaire externe non hashé et une sandbox réseau indisponible. Le binaire est accepté depuis un chemin externe uniquement lorsqu’il égale le hash épinglé : cette règle évite de rendre le checkout de référence sale avec `target/release/aret`.

## 2. Résultats réellement persistés via VERA

| Run | Runtime VERA temporaire | Résultat normalisé | Evidence | Détails |
|---|---|---|---|---|
| `difftest` complet | `/tmp/vera-aret-closed-difftest` | `PASS` | `PENDING` | `272/272` fonctions, quatre niveaux d’optimisation, 0 instruction non modélisée dans ce corpus. Asset Core SHA-256 `6e94b379cde87de75064ea038a99707fd67e96796427af29d3a6448f58f93d3e`. |
| `winediff win32_username` | `/tmp/vera-aret-closed-winediff` | `PASS` | `PENDING` | Fixture ciblée `1/1` dans le sandbox réseau. Asset Core SHA-256 `0155b815f2c9ab5d898825525dd244ad000f2ebbbd93207265c3612c633c98e7`. |

Chaque run a suivi la chaîne : capability Pack immuable → contrat `OBSERVED_PROCESS` générique → policy `ALLOW` explicite → préflight → sous-processus sandboxé → asset immuable hashé dans le Core → execution append-only liée au hash → evidence `TEST_PROOF` append-only. Les evidence sont à l’état `PENDING` et les comptes `evidence_admission` et `knowledge_proof` sont restés à zéro.

> Ces deux résultats sont des observations de périmètre précis. Le `PASS` de `win32_username` dans un namespace utilisateur/réseau isolé ne contredit pas, ne remplace pas et ne normalise pas le `winediff` global historique à `255/264` exécuté dans un environnement différent.

## 3. Tentative de corpus Wine complet et wall conservée

Une tentative du corpus `winediff` complet a été lancée via le même pipeline avec un timeout externe de 900 secondes. Elle s’est bloquée sur la fixture `win32_winsock` sous namespace réseau isolé. Le processus global a été arrêté par supervision avant de produire une evidence VERA complète ; aucun résultat ne lui est attribué et aucun verdict n’est promu.

| Fait | Classification |
|---|---|
| Le pipeline fermé peut persister un `PASS` et une evidence `PENDING` pour `difftest` complet. | `OBSERVED` |
| Le pipeline fermé peut exécuter une fixture Wine ciblée et persister son résultat. | `OBSERVED` |
| Le corpus Wine complet se termine dans le sandbox réseau avec un verdict comparable au baseline global. | `UNKNOWN` |
| Le corpus Wine complet est `PASS`. | `NON ÉTABLI` |
| Les neuf divergences Wine historiques sont résolues ou acceptées. | `NON ÉTABLI` |

## 4. Effet strict sur C07, C08 et M4.EXIT

| Gate | État après cette intégration | Justification fail-closed |
|---|---|---|
| C07 | `IN_PROGRESS` | Le chemin capability → execution → asset → evidence existe pour deux runs réels, mais la normalisation/exécution du corpus complet, la validation, l’admission HMAC et la gate de parité ne sont pas complètes. |
| C08 | `IN_PROGRESS` | Catalogue de dépendances, préflight, commit/binaire épinglés et sandbox sont implémentés ; le doctor M6, l’image de référence versionnée et la recette opératoire complète restent absents. |
| Parité ARET | `UNKNOWN` | `difftest` est positif, une fixture Wine est positive, mais `winediff` complet sandboxé reste non terminé et le baseline global contient des divergences observées. |
| M4.EXIT | `NOT_ELIGIBLE` | Les autres migrations M4, C01–C16, M5/M6, le doctor, les surfaces MCP/VCS/bundles et la parité complète restent incomplets. |

## 5. Validations de code de cette tranche

La suite locale passe à `390 passed, 17 subtests passed`. Les tests introduits couvrent le catalogue fermé, les refus de traversal/symlink, le préflight sans installation, les verdicts `SKIPPED/FAIL/ERROR/UNKNOWN`, la migration Core 037, la policy `ALLOW`, l’append-only, la sandbox, le checkout Git verrouillé, l’evidence non admise et le binaire externe attesté. Le scan Core anti-ARET, `git diff --check` et l’installation isolée de la roue ont également passé.

## Références

[1]: aret_toolkit_oracle_execution_2026-08-26.md "Exécution contrôlée des oracles ARET restaurés — 2026-08-26"
[2]: ../../M4_COMPLETION_REGISTER.md "Registre canonique de clôture M4"
[3]: ../../../../ARET-MMU/aret-memory/evidence/adapters/oracles.py "Catalogue historique fermé des oracles ARET"
