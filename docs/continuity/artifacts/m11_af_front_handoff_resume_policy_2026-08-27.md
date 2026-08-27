# M11-AF — Front, handoff, reprise configurable et policy projet

**Date :** 2026-08-27
**Périmètre :** clôture du sous-lot M11-AF uniquement
**Verdict du sous-lot :** `PASS`
**Commit fonctionnel :** `43e027a5aa17f0f91f144f5abde826015580875e`

> Ce verdict établit les mécanismes M11-AF et leurs régressions locales. Il ne qualifie ni M11-B ni la conformité complète à `UNIVERSAL_DEV_MMU_SPECIFICATION_FINALE.md`.

## 1. Objet et frontières

M11-AF rend persistants et traçables le **Front** et le **handoff** annoncés par le Project Profile enrichi de M11-A. Il relie également le rituel de reprise à la configuration déclarative du profil et fait respecter la policy project-local avant toute mutation de Front ou handoff.

| Élément | Décision livrée | Frontière explicitement conservée |
|---|---|---|
| Front | Snapshots complets, versionnés, hashés, liés au `profile_hash` et append-only. | Aucun éditeur graphique ou import de Front n’est ajouté. |
| Handoff | Snapshot append-only lié au Front courant et au `ResumeDossier` contrôlé. | Aucun export, import ou restore n’est ajouté. |
| Resume | Les exigences sont dérivées des seules sections `resume.sections` marquées `required: true`; le budget provient de `storage.max_resume_bytes`. | Le mécanisme ne prouve pas un hôte agent réel ni un post-compaction absent du client. |
| Policy projet | Les mutations exigent toujours `confirm=True`; `filesystem.write=deny` refuse avant transaction; policy absente/invalide est refusée. | `allow` ne contourne pas la confirmation explicite des opérations mutantes M11-AF. |
| SQLite | Migration continue et checksummée `039_front_handoff.sql`, avec tables, FKs, indexes et triggers anti-`UPDATE`/`DELETE`. | Aucune restauration/fusion SQLite n’est ajoutée. |

## 2. Implémentation vérifiée

La migration `039_front_handoff.sql` crée `front_revision` et `handoff`. Les deux tables sont immuables au niveau SQLite par des triggers de refus des mises à jour et suppressions. Les services `FrontService` et `HandoffService` calculent respectivement les hashes canoniques des champs et du payload, vérifient l’identité/profile hash et inscrivent leurs audits dans la même transaction que l’écriture métier.

`profile_resume.py` adapte le mécanisme Core existant de `session_lifecycle` au Project Profile : seules les sections requises composent le contrat de reprise, les profils antérieurs sans bloc `resume` conservent les deux sections de compatibilité prévues, et les adapters Claude local/cloud, Codex, Gemini et Antigravity consomment ce dossier compilé. Cette intégration reste une garantie de configuration et de transport local : elle ne transforme pas un adapter en preuve d’hôte réel.

La fonction fermée `require_project_write` charge le catalogue project-local validé avant mutation. Elle exige une confirmation booléenne explicite dans tous les cas, accepte ensuite seulement `allow` ou `confirm`, et refuse `deny`, les catalogues absents/incohérents ainsi que toute décision étrangère au contrat fermé. Les services encapsulent ce refus dans leurs erreurs publiques sans atteindre leur transaction d’écriture.

## 3. Preuves exécutées

| Contrôle | Commande ou scénario | Résultat observé |
|---|---|---|
| Front, handoff et reprise | `pytest -q tests/test_front_handoff.py tests/test_profile_resume.py tests/test_session_lifecycle.py` | `15 passed` |
| Adapters, hooks et transport MCP concernés | Suite des 17 fichiers Claude/Codex/Gemini/Antigravity/MCP ciblés | `63 passed, 12 subtests passed` |
| Migration historique | Mémoire créée avec migrations 001–038, réouverte après ajout de 039 | Format `39`, identité conservée, Front/handoff insérables, triggers append-only exercés |
| Policy de mutation | `deny`, `allow` sans confirmation, handoff sans confirmation | Refus avant ligne Front/handoff et avant audit; `allow` avec confirmation écrit une révision |
| Régression intégrale | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q` | `529 passed, 43 subtests passed` en 108,67 s |
| Hygiène du diff | `git diff --check` avant index puis contrôle de l’index | Aucun défaut de whitespace signalé |

## 4. Cas de refus démontrés

Les régressions couvrent l’absence de confirmation Front, la policy `deny` sans ligne ni audit, `allow` sans confirmation, les champs Front étrangers, l’absence de Front courant, le handoff non confirmé, un Resume Dossier de profil hash altéré, les sections de reprise manquantes ou étrangères, les modifications/suppressions SQL directes et le rollback d’audit déjà garanti par les transactions de service.

Le test d’upgrade 038→039 constitue la preuve indépendante que la migration n’est pas seulement exercée sur une mémoire fraîche : il vérifie le maintien de `project_identity`, l’avancement de format, les nouvelles tables et le verrouillage append-only après reprise d’une base antérieure.

## 5. Limites et suite interdite sans instruction

Le produit global reste `NOT_DONE` au regard de la spécification finale. En particulier, bundle/export/import/restore, import projet avec provenance, surfaces CLI/MCP/Doctor complètes, Dashboard configurateur, documentation dérivée, rapport de couverture, politique de compatibilité/VCS, M4.EXIT et preuves d’hôtes réels ne sont pas déduits de ce sous-lot.

La campagne d’hôtes réels reste différée. Claude Cloud conserve strictement la séquence preview réel puis deux confirmations indépendantes juste avant toute écriture user-scope; aucune telle écriture n’a été exécutée ici. La préversion publique `v0.1.0-rc.4` demeure non signée et ne devient pas une release stable.

**Pause obligatoire :** après le push documentaire associé, aucun travail M11-B ou ultérieur ne doit être engagé sans nouvelle instruction explicite du propriétaire.
