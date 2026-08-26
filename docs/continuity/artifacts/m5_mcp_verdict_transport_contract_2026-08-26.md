# M5 — Contrat MCP de transport des verdicts — 2026-08-26

> **Statut :** contrat de préparation M5. Aucune surface MCP de production n’existe encore dans VERA-MMU.

## 1. But

M5 doit exposer les services VERA déjà vérifiés par les tests internes, sans modifier leur sémantique. Un client MCP doit pouvoir déclencher une capability déclarée, obtenir l’execution et l’evidence correspondantes, puis constater la décision de policy. Il ne doit jamais pouvoir fournir directement un verdict, une commande ou un artefact à promouvoir.

## 2. Surface minimale

| Outil MCP | Entrées bornées | Sortie obligatoire | Interdits |
|---|---|---|---|
| `mmu_get_capability_catalog` | Aucun ou filtre déclaré | Capabilities, schémas, policy, timeout et version | Commande shell brute |
| `mmu_run_capability` | `capability_id` et paramètres validés par schéma | `execution_id`, `evidence_id`, verdict, asset hash, statut preflight | `verdict`, `stdout`, `exit_code`, commande ou chemin arbitraires fournis par le client |
| `mmu_get_execution` | `execution_id` exact | Execution, result et lien d’artefact | Inférence de succès à partir d’un texte |
| `mmu_read_artifact` | `asset_id` autorisé | Octets hashés ou référence bornée | Lecture hors artifact store |
| `mmu_validate_evidence` | `validator_id`, `evidence_id` | Validation persistée | Bypass de validator |
| `mmu_decide_admission` | evidence/validation/policy déclarées | Décision ou erreur explicite | Admission d’un non-`PASS` |
| `mmu_evaluate_gate` | `gate_id` exact | Statut dérivé des admissions | Gate `PASS` sans admission |

## 3. Matrice de conformance MCP

Le serveur de test M5 utilisera un **adapter de scénario déclaré dans le test**, non une entrée contrôlée par le client. Le client appelle exactement la même capability que dans un usage normal; seul le runtime de test produit les sorties contractuelles.

| Scénario produit par l’adapter | Réponse `mmu_run_capability` | Admission demandée | Gate |
|---|---|---|---|
| Résumé `272/272` | Verdict `PASS`, execution/evidence/asset liés | Autorisée seulement après validation `PASS` | Peut devenir `PASS` |
| Résumé `271/272` | Verdict `FAIL`, asset présent | Refusée avec erreur explicite | `FAIL` |
| Dépendance absente | Verdict `SKIPPED` et cause exacte | Refusée | `FAIL` |
| Timeout | Verdict `ERROR`, timeout visible | Refusée | `FAIL` |
| Sortie non reconnue | Verdict `ERROR` | Refusée | `FAIL` |
| Format non promouvable | Verdict `UNKNOWN` | Refusée | `FAIL` |
| Asset altéré | Validation `FAIL` | Refusée | `FAIL` |

## 4. Invariants de transport

Le MCP doit être une façade mince : le résultat retourné par le serveur doit être identique à celui des services, et les IDs doivent référer aux enregistrements persistés. Les réponses doivent être déterministes pour un même store. Une erreur d’admission ou de paramètres est une réponse MCP structurée et audible, pas un succès masqué.

Les tests M5 doivent démarrer un vrai serveur MCP et appeler ses outils via un client MCP/stdio. Ils ne doivent ni appeler directement les services en remplacement du transport, ni injecter des scores dans les arguments d’outil. Les suites ARET réelles restent séparées : elles vérifient un Pack et son environnement, pas la conformité de l’API VERA.

## 5. Hors de M4

Le générateur de manifeste, le Tool Registry, le runtime adapter, les hooks et le serveur MCP font partie de M5. L’absence de cette surface empêche aujourd’hui de revendiquer la conformance **MCP**; elle ne remet pas en cause la matrice de services vérifiée en M4.

## Références

[1]: m4d_verdict_transport_scope_correction_2026-08-26.md "Correction de périmètre"
[2]: ../../../src/vera_mmu/domain_packs/aret/oracle_contract.py "Normalisation Pack"
[3]: ../../../tests/test_aret_verdict_transport.py "Matrice de transport interne"
