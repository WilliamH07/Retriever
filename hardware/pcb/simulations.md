# Simulations électriques — 14 novembre 2026

Blocs analogiques sensibles des cartes v2, simulés avec **ngspice 47** à partir des
valeurs de `scripts/build.py`. Une simulation vérifie le calcul, pas la carte :
les modèles de composants sont simplifiés, et les résultats restent à confirmer
en recette.

| Bloc | Carte | Résultat |
|---|---|---|
| Hacheur de freinage | `safety_power` | ❌ **défaut trouvé**, correction simulée |
| Précharge | `safety_power` | ✅ conforme, une consigne logiciel à respecter |
| Prélèvement Hall | `motor_interface` | ✅ conforme jusqu'à 0,5 V de bruit de masse |
| Consigne VR | `motor_interface` | ✅ conforme (calcul) |
| Limites des eFuses | les trois | ✅ conformes à la datasheet (calcul) |

Rejouer : `ngspice -b <fichier>.cir`, ou les scripts Python indiqués. ngspice
s'installe par `brew install ngspice`.

## 1. Hacheur — `safety_power/sim/hacheur.cir`

**Défaut.** Le calcul de `decisions.md` §4 suppose que la sortie du comparateur
monte à 11,9 V. En réalité, la LED `D10` (par `R33` 4,7 kΩ) et le diviseur
`R31`/`R32` chargent le pull-up de 10 kΩ, et la sortie ne monte qu'à **4,8 V**.

| | Prévu (§4) | Simulé |
|---|---|---|
| Sortie haute `CH_CMD` | 11,9 V | **4,8 V** |
| Seuil ON | 42,50 V | 42,50 V |
| Seuil OFF | 41,80 V | **42,21 V** (hystérésis 0,28 V au lieu de 0,70 V) |
| `CHOP_ACT` lu par le TCA9555 | ≈ 3 V | **1,19 V**, sous le seuil haut de 2,31 V : **le logiciel ne voit jamais le hacheur actif** |
| Dispersion, résistances 1 % (`corners.py`) | ± 0,4 V | **± 0,9 V** : OFF entre 41,34 et 43,10 V |

**Correction proposée (v2.1), simulée** — `hacheur_v21.cir` :

- la LED passe sur la sortie du pilote `CH_DRV` (12 V), avec 10 kΩ ;
- `R25` + `R26` → une seule 6,19 kΩ ; `R27` → 1,58 MΩ ;
- `R23` à `R26` en **0,1 %**.

| | v2.1 nominal | v2.1 pire cas (0,1 %) |
|---|---|---|
| Seuil ON | 42,96 V | 42,79 à 43,13 V |
| Seuil OFF | 42,26 V | **42,08 à 42,43 V** : toujours au-dessus du pack plein (42,0 V) |
| `CHOP_ACT` | 2,78 V | lu haut par le TCA9555 |

Cette correction règle aussi la question ouverte n° 1 de `decisions.md` (seuil bas
sous la pleine charge). Elle change le routage autour de `D10` : **la carte doit être
régénérée**.

## 2. Précharge — `safety_power/sim/precharge.cir`

Bus de 10 mF supposé (étude 12, à confirmer par M10), résistance 10 Ω hors carte.

| | Batterie 42 V | Batterie 30 V |
|---|---|---|
| Bus à 95 % | **0,32 s** (exigence < 1,5 s) | 0,33 s |
| Courant crête | 4,1 A | 2,9 A |
| Énergie dans la résistance | 8,6 J (crête 171 W) | 4,4 J |
| `VGS` de `Q3` | −11,9 V (zener 12 V) | −9,4 V |
| Énergie de commutation de `Q3` | 37 mJ | 19 mJ |

Le bus finit 0,4 V sous la batterie, à cause de la diode `D7`.

**Consigne pour le logiciel (calcul, non simulé).** Fermer le contacteur sur un écart
ΔV entre batterie et bus donne un pic de courant ΔV / R_boucle. Avec 4 à 10 mΩ de
boucle (2 FET, shunt, câbles), le pic dépasse le seuil de court-circuit de 99 A
pendant plus de 100 µs dès que ΔV dépasse environ 3 à 4 V. **Fermer quand
`VBUS ≥ VBAT − 1 V`**, pas sur un pourcentage. À 42 V, cela prend environ 0,4 s.

## 3. Prélèvement Hall — `motor_interface/sim/hall.cir`, `hall_run.py`

Une voie : pull-up 2,2 kΩ, 2,2 kΩ série, 10 nF, `BAT54S`, `SN74LVC3G17` à 3,3 V.
Hall à 144,5 Hz (pleine vitesse à vide). Les seuils de Schmitt sont pris en trois jeux
(bas, typique, haut), approchés depuis la datasheet. Le bruit de hachage à 16 kHz est
injecté sur `GND_MOT` par rapport à la masse logique.

- **Retards** : 30 à 52 µs sur front descendant, 14 à 26 µs sur front montant, soit
  au plus 4,5 % de l'intervalle de 1,15 ms entre transitions. Sans effet sur le comptage.
- **Bruit de masse** :

| Bruit crête | Fronts parasites |
|---|---|
| 0,5 V | aucun, dans les trois jeux de seuils |
| 1 V | doubles fronts près des transitions (seuils bas et typiques) |
| 2 V | inutilisable |

Passer à 22 nF n'améliore pas le résultat.

**À faire** : le logiciel valide la séquence Hall et ignore un second front pendant
environ 100 µs. La mesure M7 doit relever le bruit réel entre `GND_MOT` et la masse
logique.

## 4. Consigne VR — calcul

`MCP4728` en 3,3 V, référence 2,048 V, `TLV9062` gain 2,5 :
2,048 × 2,5 = 5,12 V, écrêté à ≈ 4,98 V. Les codes 0 à ≈ 3980 sont linéaires.
Au connecteur (100 Ω série, 10 kΩ à la masse), cela donne ≈ 4,93 V à fond.
DAC non alimenté : l'entrée de l'ampli est tenue à 0 par 100 kΩ, donc `VR` = 0.

## 5. eFuses — calcul, datasheet TPS2595x, équation 4

Formule : I_LIM = 2000 / R_ILM + 0,04 A, à ± 6 % selon la table des
caractéristiques électriques.

| Carte | Sortie | R_ILM | I_LIM |
|---|---|---|---|
| `safety_bus_distribution` | 5 V par branche | 2,2 kΩ | 0,95 A |
| `safety_power` | 12V_AUX (`TPS259573`) | 1,05 kΩ | 1,94 A |
| `safety_power` | 5V_LOGIC | 1,4 kΩ | 1,47 A |
| `safety_power` | 5V_LED | 2,2 kΩ | 0,95 A |
| `safety_power` | 5V_BRAKE AV / AR | 4,42 kΩ | 0,49 A |

Seuils de la broche EN :

- **UVLO des sorties 5 V** : 1,2 V × 147/47 = 3,75 V.
- **OVLO du 12V_AUX** : 1,2 V × 134/10 = 16,1 V. Le `TPS259573` est bien la variante
  à broche EN/OVLO active basse (table des variantes de la datasheet).

## Ce que ces simulations ne couvrent pas

- Les boucles des deux régulateurs `TPS54360B`.
- La commutation du contacteur et ses surtensions.
- Le court-circuit franc pendant 100 µs.
- La thermique.

Ces points relèvent de la relecture experte et de la recette.
