# M6-B — Contrat commun Scan / Generate / Preview / Install

**Date :** 2026-08-27  
**Statut :** `PASS` pour les opérations contrôlées M6-B ; opérations hôte réelles `NOT_RUN`  
**Commit fonctionnel :** `8d59939`  
**Portée :** opérations Core réutilisables par la CLI, un bridge local ultérieur et le Dashboard ; aucune logique VERA dans le frontend.

## 1. Principe

M6-B introduit des **contrats d’opérations**, pas une seconde implémentation de la logique VERA.

```text
CLI ─────────┐
             ├── opérations VERA versionnées ── Core / adapters attestés
Bridge local ┤
             │
Dashboard ───┘
```

| Contrat | Entrées acceptées | Sortie | Écriture | Statut épistémique |
|---|---|---|---|---|
| `ScanReport/v1` | racine locale explicitement choisie | observations déterministes, bornées et triées | aucune | `OBSERVED` seulement |
| `GenerationPreview/v1` | profile VERA validé + adapter allowlisté | manifest, instructions, intégration et hooks compilés/hachés | aucune | preview, non installé |
| `InstallPlan/v1` | preview attesté + confirmation | changement project-local exact et reçu | seulement après confirmation | `APPLIED_PROJECT_LOCAL` ou refus |
| `DoctorReport/v1` | profile + adapter allowlisté | état constaté des artefacts | aucune | `NOT_OBSERVED` pour le host réel |

## 2. Scanner

Le scanner ne suit aucun symlink, ne lit aucun secret, ne lance aucune commande, ne consulte aucun réseau et n’ouvre aucun fichier de contenu métier. Il inspecte uniquement une liste bornée de noms, extensions et marqueurs de configuration sous une racine réelle explicitement fournie.

Les résultats sont des constats portant sur les fichiers eux-mêmes : présence de Git, descripteur Python/Node/Rust/etc., marqueur de CI, documentation ou test. Une observation n’est ni une capability, ni une policy, ni une preuve, ni une décision de profil.

## 3. Génération et installation

La génération réutilise les compilateurs VERA existants. Une même entrée profile/store/adapters génère les mêmes hashes. La sortie reste un preview jusqu’à ce qu’un installateur spécialisé, project-local et confirmé l’applique.

L’opération générale ne reçoit jamais de commande shell, capability, verdict, hash à faire confiance, nom de fichier cible libre, chemin home, secret ou réseau. Elle peut sélectionner uniquement un adapter installé dans le registre statique VERA.

> Le Dashboard n’écrit pas dans le projet. Il demande au bridge local d’exécuter un `InstallPlan` déjà affiché et confirmé ; le bridge applique les mêmes refus que la CLI.

## 4. Compatibilité Dashboard / GitHub Pages

Un frontend statique peut afficher les quatre contrats ou recevoir un `ScanReport` exporté. Il ne devient pas un fichier de configuration exécutable et ne peut pas installer seul. Un bridge local futur sera lié à loopback, appairé explicitement et limité aux opérations versionnées de ce contrat.

## 5. Gates M6-B

1. Scan identique sur même arborescence, aucune écriture et refus de racine symlinkée.
2. Génération déterministe depuis le même profile/store, sans modification de `.mcp.json` ni config hôte.
3. Installation seulement par adapter allowlisté, preview encore courant et confirmation explicite.
4. Aucune voie user-scope, hôte live, réseau, bootstrap ou secret dans les opérations communes.
5. Les erreurs de structure restent des refus ; elles ne sont jamais converties en preview ou en `PASS`.

## 6. Résultat contrôlé

Trois tests rouges ont précédé l’implémentation. Les tests verts couvrent le scan déterministe sans écriture ni suivi de symlink, le `GenerationPreview` déterministe sans fichier de configuration hôte, et l’installation MCP générique project-local avec preview, confirmation et refus d’adapter inconnu. La suite VERA passe à `485 passed, 37 subtests passed`; compilation, scans de frontière et roue isolée passent. Le scanner ne lit aucun contenu de fichier et n’exécute aucune commande.

Les installations dans des hôtes réels restent `NOT_RUN`. M6-B prépare les contrats et les aperçus ; les adapters conservent leurs propres gates et ne sont pas promus à une preuve host par cette CLI.
