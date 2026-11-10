# Archive

Travaux remplacés, conservés tels quels pour l'historique. **Rien ici ne fait
foi.** Les liens internes de ces fichiers ne sont pas maintenus et la CI ne les
vérifie pas.

## `pcb-v1/` — première conception des cartes, août–septembre 2026

Remplacé par la reprise des trois PCB à neuf, qui repart de
[`hardware/icd.yaml`](../../hardware/icd.yaml) et des documents
[`09`](../architecture/09-validation-composants.md),
[`10`](../architecture/10-spec-motor-interface.md),
[`11`](../architecture/11-corrections-v1.2.md) et
[`12`](../architecture/12-contacteur-statique.md).

| Fichier | Ce que c'était | Pourquoi archivé |
|---|---|---|
| `HANDOFF-safety_power.md` | Consigne de saisie de schéma pour un agent | Pack « 7,8 Ah » périmé, contrôleur `TPS48111` contraire à `11` (C17) |
| `PLAN-P2-rails-power.md` | Plan de la feuille P2, rails d'alimentation | Dépend du handoff ci-dessus |
| `PLAN-composants-par-feuille.md` | Inventaire des composants par feuille EasyEDA | Dépend du schéma EasyEDA abandonné |
| `AUDIT-EasyEDA-P2-P5-2026-09-26.md` | Audit du schéma EasyEDA, feuilles P2 à P5 | Conclut lui-même que le schéma n'est pas fonctionnel |
| `easyeda-2026-09-26/` | Exports EasyEDA : `.epro2`, netlists, DRC, calculs P2-B | Sources du schéma abandonné |
| `safety_power-README.md`, `safety_power-specification-fr.md` | Ancienne spécification de la carte puissance | Architecture différente de celle de `11` et `12` |
| `motor_interface-4moteurs-README.md`, `motor_interface-4moteurs-specification-fr.md` | Carte 4 moteurs, `SN65HVD230`, `SN74LVC14` | Remplacée par la carte 2 moteurs de `10` |

### Ce qui reste utile

- La passe de calcul P2-B (`easyeda-2026-09-26/P2B-dimensionnement-preliminaire.md`)
  corrige `RT` = 33,2 kΩ pour 300 kHz, et documente l'UVLO et les courants RMS.
- Le décodage du pack dans `safety_power-README.md` est juste (10S4P, 30 à 42 V,
  composants 60 V).
- L'audit liste des pièges de saisie EasyEDA qui vaudront pour n'importe quel
  outil.
