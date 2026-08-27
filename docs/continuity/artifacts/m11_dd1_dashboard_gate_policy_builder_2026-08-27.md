# M11-D-D1 — Builder Dashboard de policy Gate

**Verdict :** PASS dans le périmètre Policy Gate.

Le builder accepte uniquement `gateId`, `mode` (`ALL`, `ANY`, `AT_LEAST`) et, pour `AT_LEAST`, un seuil entier borné. Il produit un preview non mutateur, hashé sur les exigences existantes; l’application exige confirmation, preview bridge caché et fraîcheur. Elle délègue à `GateService.declare_policy`.

Aucun verdict, admission, evidence, predicate, runner, commande, URL ou chemin ne peut être fourni par le client. L’évaluation reste Core-only.

Validation : Core/bridge `19 passed in 1.41s`; build React PASS; Tauri `2 passed in 0.10s`; intégral Python `576 passed in 66.88s`.

Limites : création structurelle de Gate, édition d’exigences, modification de policy scellée, admission et évaluation restent hors périmètre.
