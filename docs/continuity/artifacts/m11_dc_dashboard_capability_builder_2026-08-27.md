# M11-D-C — Builder Dashboard de déclaration de Capability

**Date :** 2026-08-27  
**Baseline :** `877adec` — M11-D-A livré localement, `562 passed`.  
**Verdict :** `PASS` dans le périmètre M11-D-C.

## Portée

M11-D-C ajoute un builder limité à la déclaration immuable d’une Capability générique. Il ne crée pas de runner, contrat d’exécution, policy, gate, URL, commande ou chemin. Le Core produit d’abord un preview hashé lié au catalogue courant; le bridge conserve ce preview, demande une confirmation explicite et le réévalue juste avant la création atomique par `CapabilityService`.

| Contrat | Garantie effective |
|---|---|
| Champs | `identifier`, `name`, `kind`, `version`, `description` seulement. |
| Catalogue | `kind` est limité aux `CAPABILITY_KINDS` Core; l’identifiant et la version sont validés par les règles existantes. |
| Preview | Non mutateur, hashé, lié à un snapshot déterministe du catalogue de capabilities. |
| Fraîcheur | Toute modification du catalogue entre preview et application rend le preview périmé et l’écriture est refusée. |
| Confirmation | L’application requiert `confirm=true`, un hash caché par le bridge et un preview exact. |
| Écriture | La seule mutation est `CapabilityService.create`, donc une transaction SQLite atomique et un audit `CAPABILITY_DECLARED`. |
| UI | Formulaire React restreint aux cinq champs, preview affichable et case de confirmation; aucun champ runner, commande, chemin, URL ou policy. |
| Transports | React → Tauri → bridge stdio à nonce → Core. Le WebView ne sélectionne ni root ni profile. |

## Validation observée

```text
Builder Core + bridge desktop :          9 passed in 1.12s
Build React TypeScript / Vite :          PASS
Tests Tauri / Rust natifs :              2 passed in 0.10s
Régression Python intégrale VERA :       564 passed in 64.55s
```

## Dépendance de l’édition Profile

M11-D-B reste différé. Dans le modèle actuel, `profile_hash` participe à l’identité persistée du store; modifier le Project Profile sans protocole de rebind/migration atomique rendrait l’ouverture ultérieure du store fail-closed. Aucun contournement de cette identité n’est introduit.

## Limites

Le lot ne livre pas l’édition de Project Profile, un builder de contrat/runner/policy, un builder de Gate, la modification/suppression d’une capability, un import/export de catalogue ni un Dashboard d’hôte réel.
