# M4-D — Chaîne universelle de verdict, admission, preuve et gate — 2026-08-26

> **Statut :** mécanisme universel observé et testé ; aucune parité ARET globale n’est déduite.
>
> **Verdict M4.EXIT :** `NOT_ELIGIBLE` inchangé.

## 1. Objet borné

Cette tranche vérifie que VERA traite correctement les **classes de résultat** d’une capability externe, sans corriger, filtrer ni réinterpréter l’oracle de domaine. Le Pack ARET continue de normaliser strictement la sortie de ses scripts ; le Core ne reçoit que le verdict et vérifie génériquement sa traçabilité jusqu’à l’artefact persistant.

Le commit fonctionnel `7365ba8` ajoute le validator Core fermé `EVIDENCE_ASSET`. Il vérifie simultanément que l’evidence déclare un asset existant, que son hash déclaré correspond au hash de cet asset, et que l’execution liée porte le même `artifact_hash`. Le Core ne contient aucun terme, dépendance ou script ARET.

## 2. Matrice de décision vérifiée

| Verdict d’evidence | Lien asset/execution valide | Admission stricte possible | Proof dérivée possible | Contribution à une gate | Décision |
|---|---:|---:|---:|---:|---|
| `PASS` | Oui | Oui, seulement avec validation `PASS` de la même evidence | Oui, seulement après policy de preuve et secret HMAC si exigé | Oui, seulement après admission | Chemin autorisé, explicite et audité |
| `PASS` | Non ou altéré | Non : validation `FAIL` | Non | Non | Refus fail-closed |
| `FAIL` | Oui ou non | Non | Non | Non admise, gate `FAIL` | Non promouvable |
| `ERROR` | Oui ou non | Non | Non | Non admise, gate `FAIL` | Non promouvable |
| `SKIPPED` | Oui ou non | Non | Non | Non admise, gate `FAIL` | Non promouvable |
| `UNKNOWN` | Oui ou non | Non | Non | Non admise, gate `FAIL` | Non promouvable |

Les tests créent délibérément une evidence `PASS` dont le hash d’asset déclaré est altéré : son validator retourne `FAIL`, puis l’admission stricte la refuse. Inversement, les quatre verdicts non-`PASS` disposent d’un artefact correctement lié, mais restent non admissibles. L’intégrité de stockage ne remplace donc jamais le verdict fonctionnel de l’outil.

## 3. Exécution réelle ARET, limitée au mécanisme

Le scénario `difftest` a été exécuté dans un store temporaire VERA neuf, avec le toolkit verrouillé au commit `7a0429790bb04d1ad3c1819449e906140ebf4513`, le binaire externe attesté et le runner Pack sandboxé réseau. Il a produit `PASS 272/272`.

| Étape | Résultat observé |
|---|---|
| Normalisation Pack ARET | `PASS` |
| Asset d’exécution | `difftest-execution-artifact`, SHA-256 `aba12da0f0279ffcb2b834df6aba0db8a0966d271b288e1c368dc3c5286911fe` |
| Validation Core `EVIDENCE_ASSET` | `PASS` |
| Admission | `ADMITTED` sous `VALIDATED_PASS_EVIDENCE` |
| Proof dérivée | `PROVEN` dans le store de test, avec policy HMAC explicite |
| Gate | `PASS` |

> Cette proof concerne **l’execution contrôlée `difftest` dans le runtime temporaire**. Elle ne prouve ni la compatibilité complète ARET, ni le corpus Wine, ni M4.EXIT. Elle démontre seulement que la voie canonique ne bloque pas un `PASS` réellement validé, tout en refusant les autres classes de résultats.

Le runtime utilisé est `/tmp/vera-aret-universal-chain`; il ne se situe pas dans ARET-MMU et n’écrit aucune source ARET.

## 4. Validation et limites

La matrice test-first couvre `PASS`, `FAIL`, `ERROR`, `SKIPPED`, `UNKNOWN` et le `PASS` à asset altéré. La suite complète passe à `391 passed, 21 subtests passed`; la migration continue `038`, le scan Core anti-ARET, le contrôle de whitespace et l’installation isolée de roue passent également.

Cette tranche ne corrige aucun oracle ARET. Elle ne rend pas le corpus Wine global concluant : le résultat historique `winediff 255/264` reste `FAIL`, le run sandboxé complet interrompu sur `win32_winsock` reste sans verdict, et la parité ARET reste `UNKNOWN`.

## 5. Conséquence de plan

C07 progresse sur la chaîne complète de traitement d’un `PASS` validé. C08 conserve ses limites de doctor/image de référence. Les prochaines actions légitimes sont la définition du doctor reproductible, la conservation contrôlée des evidence de non-`PASS` produites par des runs réels, et l’investigation des divergences Wine sans modifier les fixtures ou le normaliseur.

## Références

[1]: ../M4_COMPLETION_REGISTER.md "Registre de clôture M4"
[2]: m4d_closed_oracle_pipeline_integration_2026-08-26.md "Pipeline ARET fermé"
[3]: ../../DECOUPLING_MATRIX.md "Matrice C07/C08"
