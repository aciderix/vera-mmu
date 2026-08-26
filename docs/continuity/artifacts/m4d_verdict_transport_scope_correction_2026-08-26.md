# M4-D — Correction de périmètre : transport de verdict VERA, non parité d’oracle — 2026-08-26

> **Décision de portée :** M4 ne doit pas évaluer si ARET atteint localement `272/272`, `271/272` ou un autre score. Il doit vérifier que VERA applique correctement et de manière universelle le contrat associé à chaque résultat.

## 1. Distinction normative

Un oracle de domaine fournit un **verdict normalisé** et un artefact. VERA doit ensuite traiter ce résultat de manière générique : persister l’execution et l’evidence, vérifier l’intégrité de l’artefact, appliquer l’admission, décider la possibilité de proof et mettre à jour une gate selon policy.

| Sujet | Responsable | Exemple |
|---|---|---|
| Calcul du résultat métier | Oracle / Domain Pack | `difftest` écrit `272/272` ou `271/272`; Wine renvoie une divergence. |
| Normalisation domaine | Domain Pack | `272/272 → PASS`; `271/272 → FAIL`; prérequis absent → `SKIPPED`; timeout → `ERROR`; sortie non promouvable → `UNKNOWN`. |
| Transport et traitement de verdict | Core VERA | Evidence, asset, execution, validation, admission, proof et gate suivent la policy. |
| Exposition MCP | M5 | Une vraie surface MCP doit reproduire les mêmes scénarios avec les mêmes réponses et refus. |

Le score `272/272` n’est donc ni un prérequis à l’universalité de VERA ni une condition d’éligibilité de M4. Il est seulement un des exemples de payload possibles du Pack ARET.

## 2. Scénarios de conformance à couvrir

Le même tableau doit être applicable à ARET et à tout autre Domain Pack.

| Scénario fourni par le Pack | Attendu Core VERA | Promotion autorisée |
|---|---|---|
| `PASS` objectif, par exemple `272/272` | Evidence persistée, artifact lié, validation et admission strictes possibles | Seulement après policy/proof/gate applicables |
| `FAIL`, par exemple `271/272` | Evidence et diagnostic conservés; admission refusée | Non |
| `SKIPPED`, prérequis absent | Cause précise persistée; aucune installation implicite | Non |
| `ERROR`, timeout ou sortie illisible | Incident explicite persisté; aucun succès déduit | Non |
| `UNKNOWN`, résultat non promouvable | Observation conservée sans inférence | Non |
| Artifact altéré | Validation d’intégrité `FAIL`; admission refusée | Non |

Les scénarios doivent être testés par des fixtures contractuelles. Les suites ARET réelles restent utiles pour vérifier l’intégration du Pack, mais elles ne sont pas la source de vérité sur le comportement universel de VERA.

## 3. Conséquence pour M4 et M5

M4-D doit livrer et tester le **contrat interne de transport de verdict** : les services VERA et le Pack se comportent correctement pour tous les scénarios. L’absence actuelle de surface MCP de production signifie que les tests client→MCP ne peuvent pas encore être revendiqués; ils deviennent une exigence explicite de M5, non un échec de l’oracle ARET.

Cette correction ne clôt pas M4 à elle seule : les imports restants, playbook/compatibilité, bundles/VCS et les autres gates gardent leurs propres critères. En revanche, `winediff 255/264`, `win32_winsock` et l’environnement Wine ne sont plus des bloqueurs de la **conformité de transport des verdicts**. Ils restent des observations du Pack et, le cas échéant, des sujets distincts de parité ARET.

## Références

[1]: ../M4_COMPLETION_REGISTER.md "Registre de clôture M4"
[2]: ../../DECOUPLING_MATRIX.md "Matrice C01–C16"
[3]: ../../../src/vera_mmu/domain_packs/aret/oracle_contract.py "Normalisation des verdicts ARET"
