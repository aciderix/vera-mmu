# M4-D — Scénario réel `UNKNOWN` et refus d’admission — 2026-08-26

> **Statut :** observation réelle de traitement non positif, archivée.
>
> **Verdict global :** `M4.EXIT = NOT_ELIGIBLE` inchangé.

## Objet

Après le scénario positif `difftest`, ce run vérifie que VERA ne promeut pas un résultat non concluant, même si son artefact et sa liaison à l’execution sont techniquement corrects. Il ne corrige ni le script Wine hashé, ni son corpus, ni son format de sortie.

## Exécution réelle

Le runner Pack fermé a exécuté `winehash` depuis le toolkit ARET propre et verrouillé. L’oracle a produit l’output réel du corpus Wine. Le normaliseur Pack l’a classé `UNKNOWN` conformément au contrat : l’écriture fournie est reconnue comme une sortie hashée, mais elle ne possède pas la signature promouvable du contrat historique.

| Étape | Résultat |
|---|---|
| Execution | `COMPLETED` |
| Verdict normalisé Pack | `UNKNOWN` |
| Asset | SHA-256 `70aa80f03a37ef6e6232249273546f61ec527a5b58f2d4757eaae6a7f57cb63f` |
| Validator Core `EVIDENCE_ASSET` | `PASS` |
| Tentative d’admission stricte | Refusée : `Seule une evidence PASS est admissible.` |
| Evidence admissions | `0` |
| Proofs | `0` |

Cette combinaison est volontairement importante : le validator certifie seulement le **lien physique** evidence → asset → execution. Il ne transforme pas une conclusion `UNKNOWN` en `PASS`. La policy d’admission conserve donc la sémantique de l’oracle et bloque toute proof ou gate.

> Une trace intégralement liée mais épistémiquement non concluante reste non concluante.

## Limites conservées

Ce run ne constitue pas un verdict global Wine et ne classe pas `winehash` comme `FAIL`. Il valide uniquement la gestion universelle d’un `UNKNOWN` réel. Les divergences Wine `255/264`, le blocage sandboxé `win32_winsock`, le doctor, la couverture complète des oracles et la parité ARET restent ouverts.

## Références

[1]: m4d_universal_verdict_chain_2026-08-26.md "Chaîne universelle positive"
[2]: ../M4_COMPLETION_REGISTER.md "Registre de clôture M4"
