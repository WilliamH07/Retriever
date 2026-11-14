# `safety_bus_distribution` v2.0 — décisions de conception

**Date** : 11 novembre 2026
**Statut** : schéma et routage générés, ERC et DRC propres. **Non fabriquée.**
William a délégué les choix ; chacun est justifié ici pour pouvoir être contesté.

Sources : [`cahier-des-charges.md`](cahier-des-charges.md), [`README.md`](README.md),
`hardware/icd.yaml`, datasheets citées. Disponibilité LCSC relevée le 11 novembre 2026
par recherche ; **à revérifier la semaine de la commande**.

## Ce que fait la carte, en une phrase

Elle reçoit la dorsale (5 V, CAN, `/SAFE`, masse, blindage) sur J1 et la redistribue à
huit nœuds, chacun avec son 5 V limité en courant, sa masse fusible, sa self de mode
commun et sa protection ESD. Aucune puce programmable.

## Décisions

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| B1 | Protection du 5 V par branche (I9) | **eFuse `TPS259531DSGR`** (C2155674), pas une PPTC | Une PPTC met des secondes à déclencher : pendant ce temps le court-circuit d'un nœud écroule le 5 V des sept autres. L'eFuse limite en microsecondes. Variante 31 : écrêtage à 5,7 V, réarmement automatique, ~1,7 k en stock. Le `TPS259573` initialement prévu n'avait que 19 pièces |
| B2 | Limite de courant par branche | **≈ 0,95 A** (R_ILM = 2,2 kΩ) | Interpolé de la table de la datasheet TI SLVSE57C : 1,78 kΩ → 1,17 A, 4,42 kΩ → 0,49 A. Un nœud MOTION consomme ~0,3 A ; marge ×3, et reste sous le maintien de la PPTC de masse |
| B3 | Seuil de sous-tension | **3,75 V** (100 k / 47 k sur EN/UVLO, seuil 1,2 V) | Coupe la branche si la dorsale s'effondre, au lieu de laisser un ESP32 en brown-out |
| B4 | Démarrage progressif | **1 nF sur dVdt** | Limite l'appel de courant dans les condensateurs du nœud au branchement |
| B5 | Protection d'entrée J1 | **P-MOSFET `AO3401A`** (C15127, basic) **+ TVS `SMAJ6.0A`** (C223993) **+ 2 × 10 µF + 100 nF** | Le MOSFET bloque une inversion de polarité. La TVS est **après** lui, sinon elle conduirait en inverse. 6,0 V de tension de veille plutôt que 5,0 V : moins de fuite au nominal |
| B6 | Surtension sur l'entrée | **par les eFuses**, pas de comparateur OVLO séparé | Chaque eFuse écrête sa sortie à 5,7 V. Un défaut 42 V permanent détruira la TVS (qui se met en court-circuit) et les eFuses (20 V max) : c'est accepté, la carte protège alors les nœuds en se sacrifiant |
| B7 | Fusible de masse par branche | **PPTC 1,1 A / 48 V** `1812L110/48QR` (C19723490) | Le cahier des charges demandait 500 mA, mais le courant normal du nœud revient par cette masse : il faut un maintien **au-dessus** de la limite de l'eFuse. 48 V parce qu'une PPTC déclenchée supporte toute la tension du défaut ; les modèles 6 V et 16 V courants ne tiendraient pas un 42 V |
| B8 | Self de mode commun | **`ACT45B-510-2P-TL003`** (**C76584**) | ⚠️ Le cahier des charges citait C88056, qui est la version **100 µH** (`-101`). Enroulements 1→4 et 2→3 (datasheet TDK, schéma de principe), côté bus sur 1/2 |
| B9 | ESD CAN | **`NUP2105L`** (C14486 ; second source C2890118) | Inchangé. Protège des transitoires, pas d'un 42 V permanent (voir README) |
| B10 | ESD `/SAFE` | **une `ESD5Z3.3`** (C5252448) sur le réseau commun | La ligne est un seul réseau de cuivre sur la carte : une diode protège toutes les branches |
| B11 | Pull-down 1 MΩ sur `/SAFE` | **aucun** | La règle « 1 MΩ par carte » vise les cartes qui lisent `/SAFE`. Celle-ci ne fait que la transporter |
| B12 | Terminaisons | **deux terminaisons fendues** 2 × 60,4 Ω + 4,7 nF C0G, sur cavaliers JP1/JP2 | Inchangé. **Pas de LED bleue** : une LED ne peut pas savoir passivement si le cavalier est posé. La recette au multimètre (60 Ω) est sérigraphiée et suffit |
| B13 | Blindage | **traversant**, liaison à la masse **non montée** (R7 0 Ω, C6 4,7 nF) | L'ICD relie le blindage d'un seul côté, côté X1. Les empreintes permettent de changer d'avis sans refaire la carte |
| B14 | Pull-up de banc | **non monté** : R8 1 kΩ vers 5 V, R9 1,8 kΩ vers la masse → 3,2 V | Permet de tester `/SAFE` sur établi sans `safety_power`. Sur le robot, il fausserait le diviseur 1 k / 10 k : à ne jamais monter |
| B15 | Connecteurs | **Molex 43650-0615**, vertical (C505231) | Le vertical est le seul 6 positions en stock. Neuf connecteurs coudés n'auraient pas tenu sur trois bords |
| B16 | Points de test | **pastilles nues** 1,5 mm | Rien à assembler, accessibles à la pointe et au clip |
| B17 | Couches | **2 couches**, 1,6 mm | Pas de puissance, 500 kbit/s : un plan de masse sur chaque face suffit. L'ICD disait 4 ; 2 coûte moins et se relit à l'œil |
| B18 | Format | **110 × 72 mm**, 4 trous M3 | 4 branches sur le bord haut, 4 sur le bas, la dorsale à gauche |
| B19 | Règles | piste 0,25 mm (signal), 0,4 mm (5 V, masse), isolation 0,15 mm, via 0,7/0,3 mm | Dans les capacités JLCPCB 2 couches avec marge. 0,4 mm sur cuivre 1 oz porte ~1,2 A (IPC-2152) |
| B20 | Repères des composants | **sur la couche de fabrication**, pas la sérigraphie | Sur une carte dense ils tombaient sur les pastilles. Le plan d'assemblage les garde |

## Règles de câblage qui découlent de la carte

- **Branche 1 (SAFETY) et branche 4 (adaptateur USB du X1) : ne pas câbler la broche 1
  (5 V)** côté nœud. `safety_power` est la source du 5 V ; l'adaptateur USB a le sien.
- L'adaptateur USB-CAN du X1 : **CANable Pro 1.1** (isolé 5 kV, firmware candleLight →
  pilote `gs_usb`), terminaison intégrée **retirée** (cavalier). Repli moins cher :
  MKS CANable Pro (isolé 2,5 kV, ADM3053).
- Les deux terminaisons de la carte restent posées tant que la carte est au bout du bus.

## Ce qui n'est pas vérifié

- Disponibilité réelle et prix : à revérifier à la commande (stocks relevés par recherche).
- Datasheet de la PPTC LUTE `1812L110/48QR` : maintien et tension relevés sur la fiche
  LCSC, pas sur la datasheet du fabricant.
- Valeur de `CSPLIT` : 4,7 nF est la convention du secteur, la figure de la datasheet
  `TCAN1042HV` n'a pas été lue.
- Aucune simulation : le circuit est simple (diviseurs, eFuse en configuration
  datasheet), mais la limite de courant est interpolée, pas calculée par l'équation.
