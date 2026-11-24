# Cahier des charges — `logic_board` (option B, v1.0-draft)

> **v1.0-draft — NE PAS FABRIQUER avant P1, coil voltage, BMS level, and a review by an
> electronics engineer.**

Ce document fixe ce que la carte doit faire. Les choix techniques et leurs raisons sont
dans [`decisions.md`](decisions.md). La comparaison avec la carte unique est dans
[`README.md`](README.md).

## 1. Rôle

William veut **comparer deux options** pour une commande PCBWay bon marché (parrainage de
60 €) :

- **Option A** : la carte unique [`../mainboard/`](../mainboard/) (180 × 150 mm, 2 couches,
  2 oz, elle porte le courant de 30 A des moteurs). Elle est terminée et **on n'y touche
  pas**.
- **Option B** (cette carte) : une petite **carte logique** qui porte tous les circuits
  dont les pièces sont trop petites pour être soudées au fer, assemblée par PCBWay. Tout
  ce qui est gros, chaud ou fort courant sort de la carte, sur des fils et des barrettes
  du commerce.

Objectif de B : le PCB le moins cher possible (petit, 1 oz, 2 couches) sans rendre le
câblage déraisonnable.

## 2. Priorités, dans l'ordre

1. Sécurité : les points obligatoires de [`../mainboard/cahier-des-charges.md`](../mainboard/cahier-des-charges.md)
   §5 restent tous vrais, même quand une partie du circuit sort de la carte.
2. **Jamais de 30 A sur une plaque à trous** : le chemin de 30 A se fait en fils, cosses,
   barrettes et porte-fusibles du commerce.
3. Câblage raisonnable : ce qui demanderait des dizaines de fils (les trois ESP32 et ce
   qui les entoure) reste sur la carte.
4. PCB le plus petit possible, 1 oz, 2 couches, 1,6 mm ; viser ≤ 100 × 100 mm (palier de
   prix).
5. PCBWay ne pose que les pièces « fines » ; William soude le reste.

## 3. Ce qui reste sur la carte

Repris de `mainboard` sans changement de valeur, de référence ni de brochage, sauf quand la
sortie d'une pièce hors carte l'impose (`decisions.md` §3) :

- les trois ESP32-DevKitC V4 sur supports (SAFETY, MOTION AVANT, MOTION ARRIÈRE), antennes
  au bord de la carte, aucun cuivre sous les antennes ;
- le CAN entre eux en pistes : 3 × `TCAN1042HVDR`, 120 Ω sur la carte, connecteur CANable ;
- les deux `TPS54360B` (5 V et 12 V AUX), alimentés par un fil BAT+ protégé par un fusible
  hors carte ;
- le prélèvement Hall (`SN74LVC3G17`, RC, `BAT54S`), VR (DAC + `TLV9062`), DIR, STOP et EL ;
- le verrou du watchdog (`TPL5010` → `74LVC1G74` → `/SAFE`) ;
- la commande du hacheur (`TPS7A4001`, `TLV1701`, `LM4040`, diviseur 0,1 %, `UCC27517`) ;
- les diviseurs VBAT et VBUS, la logique de bobine (`SN74AHCT1G08`), la commande de
  précharge ;
- l'`INA228`, avec un connecteur Kelvin vers un shunt **hors carte** ;
- le connecteur BMS (JST GH), le support de l'IMU (1×10), tous les connecteurs JST XH vers
  les ZS-X11H.

Pour les semi-conducteurs de puissance moyenne (FET P et 10 Ω de précharge, FET de bobine,
FET du hacheur), le choix « sur la carte » ou « hors carte » est fait et justifié dans
`decisions.md` §3.

## 4. Ce qui sort de la carte

Le chemin de 30 A : connecteur batterie, bornes du contacteur, 4 fusibles des moteurs et
leurs porte-fusibles, shunt du bus, cosses M4/M5 ; le module 12 V isolé du PC
(`URB4812YMD-30WR3`) ; les gros condensateurs du chemin de puissance s'il y en a ; la TVS
`SMCJ48CA` si elle appartient au bus.

Remplacement proposé : une distribution de puissance du commerce, la moins chère qui
reste sûre (fusibles cotés ≥ 58 V DC), listée avec son câblage dans le `README.md`.

## 5. Règle d'assemblage

PCBWay pose seulement les pièces « fines » (classement de
[`../../scripts/fab_pcbway.py`](../../scripts/fab_pcbway.py) `--fine-only` : 0603 et plus petit,
SOT-23-5/6, pas de 0,65 mm et moins, boîtiers à pastille thermique, JST GH). William soude
tout le reste. Les passifs déjà en 0603 restent en 0603 ; les pièces soudées par William
gardent leur boîtier.

## 6. Objectifs et livrables

Même méthode que `mainboard` : `scripts/build.py` décrit le circuit une fois et produit
schéma et carte ; routage par Freerouting puis `patchroute` ; `build.sh`, `fab.sh`.

- 2 couches, **1 oz**, 1,6 mm ; ≤ 100 × 100 mm visé, sinon la plus petite taille atteinte
  et pourquoi.
- ERC 0 ; DRC `--schematic-parity --severity-all` : 0 violation, 0 non connecté, 0 écart
  de parité, vérifiés avec `kicad-cli`.
- `fab/` : Gerber zippés, BOM et fichiers de placement (complets et « fins seulement »),
  schéma PDF, plan d'assemblage, rendus dessus et dessous.
- Sérigraphie et cartouche « v1.0-draft – NE PAS FABRIQUER ».
- Estimation de coût (estimations, pas un devis) et tableau de comparaison A / B dans le
  `README.md`.
