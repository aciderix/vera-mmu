# M4-D — Matrice réelle de verdicts et doctor ARET — 2026-08-26

> **Statut :** mécanisme fail-closed étendu et doctor Pack observé.
>
> **Verdict :** `M4.EXIT = NOT_ELIGIBLE` inchangé.

## 1. Résultats réels conservés par VERA

Les runs suivants utilisent le toolkit propre et verrouillé, les scripts ARET réels et des runtimes VERA temporaires distincts. Aucun script, fixture ou normaliseur ARET n’a été modifié.

| Cas | Source du verdict | Evidence / asset | Admission | Proof / gate |
|---|---|---|---|---|
| `PASS` | `difftest 272/272` | Lien asset/execution validé | `ADMITTED` | Proof HMAC et gate `PASS` dans le runtime de démonstration |
| `UNKNOWN` | `winehash` réel, format non promouvable | `EVIDENCE_ASSET=PASS` | Refusée | `0` proof, aucune gate |
| `SKIPPED` | `difftest` préflight sans `target/release/aret` dans le checkout propre | `EVIDENCE_ASSET=PASS` | Refusée | `0` proof, aucune gate |
| `FAIL` | `winediff user32_paint` réel | `EVIDENCE_ASSET=PASS` | Refusée | `0` proof, aucune gate |

Le `SKIPPED` est produit par le préflight réel : le clone de référence est volontairement propre et ne contient pas le binaire compilé; le binaire externe attesté est une précondition explicite du run qui doit l’utiliser. L’absence est donc visible et n’est ni compensée ni installée par VERA.

Le `FAIL` est produit par la fixture existante `user32_paint`, qui fait partie des divergences Wine historiques. Son asset a le SHA-256 `abb71efd27a9d288aa9de79790c13d4494e76c1165e1169b71a5a28aff906bf4`; malgré ce lien physique correct, l’admission stricte renvoie `Seule une evidence PASS est admissible.`

## 2. Cas `ERROR`

Le contrat de normalisation et les tests couvrent `ERROR` pour timeout ou sortie non reconnue; ces cas sont refusés par la même policy d’admission. Aucun `ERROR` runtime supplémentaire n’a été forcé artificiellement dans cette tranche : provoquer un timeout en modifiant une limite, un script ou une sortie ne constituerait pas une observation comparable de l’oracle. L’absence d’observation runtime `ERROR` reste donc explicitement déclarée, sans être transformée en couverture réelle.

## 3. Doctor ARET Pack

Le commit fonctionnel `4e30eeb` ajoute `inspect_aret_toolchain` dans le Pack ARET. Le doctor est purement observationnel : il ne télécharge rien, n’installe rien et ne lance aucun oracle. Il vérifie la racine, le commit Git, la propreté, le binaire SHA-256 externe, les préflights des neuf oracles et la présence de `unshare`, exigée par le runner `DENY_NETWORK`.

Le doctor réel a relevé : référence au commit `7a0429790bb04d1ad3c1819449e906140ebf4513`, checkout propre, binaire externe SHA-256 `6ca52f0955266aeda31d235caacf0844e2516f41d67468632f2ddb1bb1e16a19`, sandbox réseau disponible et neuf oracles `READY`. Son statut est `READY`; ses `install_actions` sont vides.

> `READY` signifie que les préconditions contrôlées sont disponibles. Il ne signifie ni que tout oracle passe, ni que Wine est sans divergence, ni que la parité ARET est établie.

## 4. Vérification et limites

Le doctor est test-first : référence/binaire cohérents, outil manquant, référence sale ou divergente et sandbox réseau absente. La suite complète atteint `395 passed, 21 subtests passed`; le scan Core anti-ARET, `git diff --check` et l’installation isolée de roue passent.

C07/C08 restent `IN_PROGRESS`. Il manque toujours la couverture complète et reproductible des oracles, la parité des sorties, l’analyse des divergences Wine, les surfaces M5/M6 et les autres gates M4. L’état `ERROR` est contractuellement testé mais pas encore observé lors d’un run externe contrôlé; cette limite reste visible.

## Références

[1]: m4d_universal_verdict_chain_2026-08-26.md "Chaîne universelle positive"
[2]: m4d_real_unknown_verdict_2026-08-26.md "Scénario réel UNKNOWN"
[3]: ../M4_COMPLETION_REGISTER.md "Registre de clôture M4"
