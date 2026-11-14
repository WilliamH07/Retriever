# `safety_bus_distribution` — cahier des charges v2

**Statut** : spécifiée, rien ne bloque. **Première carte à fabriquer.**
**Exemplaires** : 1 en service, lot de 5.
**Spécification détaillée** : [`README.md`](README.md) (raisons de chaque choix).
**Brochage** : `boards.safety_bus_distribution` et `shared_pinouts` dans
[`hardware/icd.yaml`](../../icd.yaml).
**Cadre commun** : [`../conception-v2.md`](../conception-v2.md).

## 1. Rôle

Porter le bus CAN et la ligne `/SAFE` jusqu'à chaque nœud, et alimenter chacun
en 5 V par sa propre protection. Une dorsale en entrée, huit branches en sortie.
**Aucun microcontrôleur** : rien à flasher, rien qui plante sur le chemin de la
sécurité.

## 2. Connecteurs

| Repère | Rôle | Type |
|---|---|---|
| J1 | Dorsale, entrée | Micro-Fit 3.0, 6 pos |
| J2 | Branche 1 : ESP32 SAFETY (`safety_power`) | Micro-Fit 3.0, 6 pos |
| J3, J4 | Branches 2, 3 : MOTION avant, arrière | Micro-Fit 3.0, 6 pos |
| J5 | Branche 4 : adaptateur USB-CAN du X1 | Micro-Fit 3.0, 6 pos |
| J6–J8 | Branches 5–7 : libres | Micro-Fit 3.0, 6 pos |
| J9 | Branche 8 : banc | Micro-Fit 3.0, 6 pos |
| JP1, JP2 | Terminaisons sélectionnables | cavalier 2,54 mm |

## 3. Blocs et composants

| Bloc | Composant | Valeur | Statut |
|---|---|---|---|
| Terminaison ×2 | 2 × 60 Ω + `CSPLIT` | 2 × 60 Ω (E96 : 60,4 Ω 1 %) ; `CSPLIT` 4,7 nF | `CSPLIT` 📐 convention, à lire sur la fig. 10-2 de la datasheet `TCAN1042HV` |
| Témoin de terminaison | LED bleue par cavalier | | |
| Protection CAN, par branche | `NUP2105L` | 24 V standoff | ✅ transitoires seulement |
| Self de mode commun, par branche | `ACT45B-510-2P-TL003` | 51 µH, 200 mA | ✅ (LCSC **C76584** — C88056 était la version 100 µH) |
| 5 V par branche | `1812L050/30` **ou** `TPS259573` | 500 mA | à trancher (I9) |
| Masse par branche | PPTC série | 500 mA | ✅ |
| Témoin de présence | LED verte par branche | | |
| Protection d'entrée J1 | cellule `input_protection_cell` de l'ICD | | **manquante**, à ajouter |
| Points de test | `TP_CANH`, `TP_CANL`, `TP_SAFE`, `TP_5V`, `TP_GND` | | |

Sérigraphie obligatoire : `STUB MAX 30 cm`, et la recette de terminaison
(60 Ω correct, 120 Ω une seule, 40 Ω trois).

## 4. À corriger ou compléter avant schéma

1. **Protection d'entrée sur J1** : l'ICD l'exige identique sur les trois cartes
   (`input_protection_cell`), la carte n'en a pas.
2. **Budget courant de la dorsale** : chiffrer la somme des nœuds sur la broche 1.
3. **Origine du `5V_LOGIC`** : amont ou aval du contacteur (I3). Elle décide si le
   bus CAN reste vivant contacteur ouvert.
4. **Pull-down 1 MΩ sur `/SAFE`** : la règle « 1 MΩ par carte » s'applique-t-elle à
   une carte passive ? Recommandation : non, la ligne ne fait que transiter.
5. **Mode chaîne** : le README décrit chaîne et étoile ; préciser comment la carte
   s'insère en mode chaîne, ou supprimer ce mode.
6. **Branche 4 (X1)** : l'adaptateur du commerce n'a pas forcément un transceiver
   ±70 V. Spécifier l'adaptateur (D6, isolé) et l'état de sa terminaison
   intégrée, qui doit être désactivée.
7. **Pull-up de banc** pour la recette `/SAFE` : la carte n'en a pas. Prévoir une
   empreinte non peuplée par défaut, sérigraphiée `BENCH ONLY`.

## 5. Recette de mise en route

1. Hors tension, `TP_CANH`–`TP_CANL` : 60 Ω avec JP1 et JP2 posés.
2. 5 V sur J1, rien sur les branches : toutes les LED vertes allumées.
3. Court-circuit 5 V–GND sur une branche : sa LED s'éteint, les sept autres restent.
4. Pull-up de banc posé, `/SAFE` tirée à la masse sur une branche : niveau bas sur
   les huit.
5. Deux ESP32 sur deux branches : trames échangées à 500 kbit/s, aucun `bus-off`
   en dix minutes.

## 6. Dimensions et fabrication

L'ICD prévoit 4 couches. 2 couches suffiraient électriquement (pas de puissance,
500 kbit/s) ; garder 4 si l'écart de prix JLCPCB est faible, pour un plan de masse plein. Trous de fixation M3 aux
quatre coins. Format à fixer avec l'emplacement dans la baie électronique.
