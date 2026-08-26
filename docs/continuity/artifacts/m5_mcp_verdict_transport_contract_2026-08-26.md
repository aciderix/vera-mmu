# M5 — Façade MCP et manifeste de transport des verdicts — jalons M5-A/B — 2026-08-26

> **Statut :** `M5-A/B PASS` — façade MCP stdio dans `5ffe182`, compilateur/vérificateur de manifeste dans `5de260d`.
> **Portée :** transport universel fermé et manifeste déterministe attesté. Les adapters configurés de production, les instructions/hooks générés et la configuration d’installation restent hors des jalons réalisés.

## 1. Décision de portage

ARET-MMU était déjà un serveur MCP opérationnel : catalogue fermé, transport `stdio` et HTTP, enveloppes d’erreur structurées et test de bout en bout par un vrai client. VERA-MMU n’a donc **pas** réimplémenté le protocole MCP. Le jalon M5-A porte ce socle de transport et ses garde-fous, puis le raccorde au Core universel livré par M1–M3 et aux Domain Packs isolés par M4.

> La façade MCP est un adaptateur : elle ne réinterprète jamais un verdict et ne remplace jamais les policies du Core.

| Référence ARET-MMU | Portage M5-A VERA | Décision |
|---|---|---|
| Serveur MCP, `stdio`, réponses structurées et client réel | `src/vera_mmu/mcp_server.py`, SDK `mcp>=2.0,<3.0`, entry point `vmmu-mcp` | Porté et adapté. |
| Catalogue fermé / paramètres bornés | Sept outils publics exactement, schémas MCP générés par le SDK | Porté comme invariant. |
| Oracles et pipelines ARET | Adapter de fixture déclaré côté serveur uniquement | Gardé hors du Core ; l’adapter réel relève d’un manifest/Pack postérieur. |
| Front, handoff, knowledge, hooks spécifiques ARET | Aucun portage mécanique | À généraliser dans les lots M5/M6 suivants. |
| Services universels capability, evidence, validation, admission et gate | Appelés par la façade sans dupliquer leur sémantique | Réutilisés. |
| Catalogue/policies/contracts/adapters déclarés | `mcp_manifest.py` compile une forme canonique liée au projet et aux migrations | Ajouté en M5-B, sans shell ni runtime implicite. |

## 2. Surface M5-A livrée

| Outil MCP | Entrées client bornées | Sortie persistée ou dérivée | Interdits structurels |
|---|---|---|---|
| `mmu_get_capability_catalog` | aucune | capabilities `ALLOW`, contrats, policies et schémas | shell, URL ou chemin. |
| `mmu_run_capability` | `capability_id`, `parameters` | `execution_id`, `evidence_id`, `asset_id`, `verdict`, `gate_id` | verdict, score, `stdout`, `stderr`, `exit_code`, commande ou artifact client. |
| `mmu_get_execution` | `execution_id` exact | execution persistée et résultat enregistré | inférence de succès à partir d’un texte. |
| `mmu_read_artifact` | `asset_id` exact | bytes vérifiés, hash, taille et MIME | lecture hors Asset Store. |
| `mmu_validate_evidence` | `evidence_id` exact | validation persistée `PASS` ou `FAIL` | validator client ou bypass. |
| `mmu_decide_admission` | `evidence_id`, `validation_id` exacts | admission `ADMITTED` ou refus structuré | promotion d’un non-`PASS`. |
| `mmu_evaluate_gate` | `gate_id` exact | statut dérivé des admissions persistées | gate `PASS` synthétique. |

La façade n’importe aucun Domain Pack. Elle n’exécute aucun subprocess, n’ouvre aucun réseau et n’utilise aucun shell. Lorsqu’un manifeste est fourni, celui-ci est recompilé et vérifié contre l’identité du store, ses migrations, ses capabilities, contrats et policies; son catalogue borne les tools et chaque capability doit correspondre à l’identifiant de l’**adapter configuré côté serveur**. Sans adapter, l’entry point générique `vmmu-mcp` refuse l’exécution : il est volontairement fail-closed.

## 3. Matrice de conformance exécutée

Le test `tests/test_mcp_stdio_verdict_transport.py` démarre `tests/mcp_verdict_fixture_server.py` comme sous-processus `stdio`, initialise une vraie `ClientSession` MCP, inspecte le catalogue et appelle les sept outils. L’adapter choisit son scénario uniquement au démarrage du serveur ; le client appelle toujours la même capability et ne reçoit aucun droit de fournir un résultat.

| Scénario produit côté serveur | Verdict transporté | Validation asset | Admission | Gate |
|---|---:|---:|---:|---:|
| Résumé `272/272` | `PASS` | `PASS` | `ADMITTED` | `PASS` |
| Résumé `271/272` | `FAIL` | `PASS` | refusée | `FAIL` |
| Prérequis absent | `SKIPPED` | `PASS` | refusée | `FAIL` |
| Timeout | `ERROR` | `PASS` | refusée | `FAIL` |
| Sortie inconnue | `ERROR` | `PASS` | refusée | `FAIL` |
| Format Wine hashé non promouvable | `UNKNOWN` | `PASS` | refusée | `FAIL` |
| Asset déclaré avec hash altéré | `PASS` | `FAIL` | refusée | `FAIL` |

Le test vérifie aussi que le schéma de `mmu_run_capability` ne déclare que `capability_id` et `parameters`. Une tentative de transmettre `parameters.verdict = "PASS"` retourne `VERA_ERROR`; elle ne crée aucune réussite ni admission implicite.

## 4. Corrections et garde-fous observés

Le SDK MCP exécute les handlers synchrones dans un thread distinct. Le Store SQLite VERA restant volontairement attaché à son thread propriétaire, les handlers de la façade sont asynchrones : ils restent sur le thread du serveur, sans désactiver le garde-fou SQLite. Ce correctif porte sur le transport ; les règles Core de persistance et de policy ne sont pas modifiées.

Les erreurs métier sont retournées sous l’enveloppe stable `{ok, operation, error}` avec le code `VERA_ERROR`. Une exception ne peut pas se convertir en verdict positif, et le client ne peut pas faire tomber le serveur pour contourner un refus.

## 5. Preuves de jalon

| Contrôle | Résultat |
|---|---|
| Rouge initial | SDK MCP absent, puis dépendance explicitement ajoutée au paquet. |
| Matrice MCP réelle | `2 passed, 7 subtests passed`. |
| Régressions ciblées Pack/Core | `5 passed, 15 subtests passed`. |
| Suite complète VERA | `404 passed, 32 subtests passed` après M5-B. |
| Frontière Core | Aucun import ARET/Pack, subprocess, shell ou réseau dans `mcp_server.py`. |
| Intégrité Git | `git diff --check` : `PASS`. |
| Packaging | Roues isolées M5-A et M5-B construites ; `vmmu --help`, `vmmu-mcp --help` et inclusion de `mcp_manifest.py` : `PASS`. |
| Manifeste M5-B | Canonique quel que soit l’ordre des bindings, lié à l’identité projet et aux checksums de migrations; toute divergence de catalogue, policy, binding ou projet est refusée. |

## 6. Limites et suite M5

`M5-A/B` ne prétend pas que le serveur générique peut déjà exécuter ARET en production. La fixture ne sert qu’à prouver le **transport MCP** à partir des mêmes contrats que M4 ; elle n’est ni installée dans le paquet ni utilisable par un client.

M5-B livre `vera-mcp-manifest/v1` : une compilation canonique de l’identité de projet, des checksums de migrations, des tools, capabilities `ALLOW`, contracts, policies et bindings symboliques d’adapter. Le SHA-256 du JSON canonique est le `mcp_build_hash`; le serveur refuse un manifeste étranger, périmé, altéré ou associé à un adapter différent. Les tranches suivantes devront compiler instructions/hooks/config et fournir un registry/adapters de production explicitement déclarés par ce manifest. M6 fournira ensuite CLI, installation, doctor et expérience opératoire. Aucune de ces capacités ne peut être déduite de M5-A/B.

## Références

[1]: ../../../src/vera_mmu/mcp_server.py "Façade MCP universelle fermée"
[2]: ../../../tests/test_mcp_stdio_verdict_transport.py "Conformance stdio par client MCP réel"
[3]: ../../../tests/mcp_verdict_fixture_server.py "Adapter de scénario serveur réservé aux tests"
[4]: ../../../src/vera_mmu/domain_packs/aret/closed_oracle_runner.py "Runner Pack ARET fermé"
[5]: ../../../src/vera_mmu/validators.py "Validation `EVIDENCE_ASSET`"
[6]: ../../../src/vera_mmu/admission.py "Admission policy-gated"
[7]: ../../../src/vera_mmu/gates.py "Évaluation de gate dérivée"
[8]: ../../../src/vera_mmu/mcp_manifest.py "Compilation et vérification de manifeste MCP"
[9]: ../../../tests/test_mcp_manifest.py "Conformance I007/I008/I011/I012 du manifeste"
