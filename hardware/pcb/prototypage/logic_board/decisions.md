# Décisions de conception — `logic_board` v1.0-draft (option B)

> **v1.0-draft — NE PAS FABRIQUER avant P1, coil voltage, BMS level, and a review by an
> electronics engineer.**

Option B de la comparaison PCBWay : une petite carte « logique » qui garde tous les
circuits à petites pièces de [`../mainboard/`](../mainboard/) (option A, inchangée) et
sort le chemin de 30 A sur des fils et des pièces du commerce. Le cahier des charges est
dans [`cahier-des-charges.md`](cahier-des-charges.md), la comparaison chiffrée et le
câblage dans [`README.md`](README.md).

> ⚠️ **Routage inachevé** : la carte routée garde **48 éléments non connectés** (31 liaisons de
> signal, 17 morceaux de plan GND isolés) et 12 avertissements « piste en l'air ». ERC 0,
> parité schéma 0. Les Gerber de `fab/` servent à relire et à faire un devis, **pas à
> commander** (§9).

Tout ce qui suit est **calculé, rien n'est mesuré**. ERC 0 et DRC 0 disent que le schéma
est cohérent et que la carte respecte les règles de fabrication ; ils ne disent pas que le
circuit marche.

## Sommaire

1. [La carte en une phrase](#1-la-carte-en-une-phrase)
2. [Ce qui sort de la carte](#2-ce-qui-sort-de-la-carte)
3. [Décisions](#3-décisions)
4. [Cuivre 1 oz](#4-cuivre-1-oz)
5. [Distribution de puissance hors carte](#5-distribution-de-puissance-hors-carte)
6. [GPIO et firmware](#6-gpio-et-firmware)
7. [Budget des rails](#7-budget-des-rails)
8. [Fabrication PCBWay et coût estimé](#8-fabrication-pcbway-et-coût-estimé)
9. [Ce qui n'est pas vérifié](#9-ce-qui-nest-pas-vérifié)
10. [Questions ouvertes pour William](#10-questions-ouvertes-pour-william)

---

## 1. La carte en une phrase

Un connecteur JST VH à 5 broches amène sur la carte un BAT+ protégé par un fusible de
7,5 A (amont du contacteur), la masse, un BUS+ protégé par un fusible de 7,5 A (aval du
contacteur) et le retour de la résistance du hacheur ; la carte en tire les rails 5 V et
12 V AUX, la précharge (vers le bus, par le même fil BUS), la commande et le MOSFET du
hacheur, et garde les trois ESP32-DevKitC, le CAN, la chaîne de sécurité, les
connecteurs des variateurs, de l'IMU et du BMS ; le courant des moteurs ne la traverse
jamais.

**Format : 100 × 140 mm, 2 couches, cuivre 1 oz, 1,6 mm**, 4 trous M3. Bande du haut :
connecteurs des variateurs (3 rangées de 4), les deux alimentations, la précharge, le
hacheur, une rangée avec les quatre prélèvements Hall, puis une rangée avec les blocs
CAN/VR des deux MOTION et les pièces côté connecteurs de SAFETY ; en bas, les trois DevKitC côte à côte, antennes au bord inférieur ; à droite,
les connecteurs SAFETY, l'IMU et l'`INA228`. Les petits CMS de chaque nœud sont entre les
rangées de supports, sous le module (comme `mainboard` M35), mais seulement les étages de commande
(MOTION) et la logique de sécurité (SAFETY), espacés.

## 2. Ce qui sort de la carte

| Élément de `mainboard` | Où il va | Pourquoi |
|---|---|---|
| XT30 `J1`, TVS `D1` sur BAT_P, `C1`/`C2` | connecteur batterie sur fil (XT60 proposé, §5) ; `D1`, `C1`, `C2` restent sur la carte, à l'entrée BAT_F | Le 30 A ne passe plus par la carte |
| Bornes M5 du contacteur `J2` | fils directs batterie → contacteur → shunt | idem |
| Shunt `RS1` 1 mΩ | shunt du commerce 50 A / 75 mV (1,5 mΩ) sur le bus, prises Kelvin vers `J2` de la carte | Le shunt est dans le chemin de 30 A |
| 4 fusibles MINI 58 V + Keystone 3568, bornes M4 `J3`–`J6` | 4 porte-fusibles MINI en ligne sur une barrette BUS+, cosses | idem |
| Bornes M4 du hacheur `J12` | la résistance de 22 Ω se branche entre la barrette BUS+ (fusible 5 A) et `J1`-4 | Le MOSFET reste sur la carte (L3) |
| Fusible hôtel `F5` (NANO2 5 A, CMS) | fusible MINI 58 V 7,5 A en ligne, à la barrette BAT+ | Le fil BAT_F part d'une pièce à 30 A : il doit être protégé à son départ, pas à son arrivée |
| Module 12 V PC `PS1`, `C19`, `C20`, `J7`, `D15`, `R41` | module hors carte alimenté par son propre fusible de 3 A sur la barrette BAT+ | L4 |
| Cuivre 2 oz, polygones 30 A | rien | 1 oz suffit (§4) |

## 3. Décisions

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| L1 | Entrée de puissance | **JST VH 5 broches (`B5P-VH`, 3,96 mm, 10 A par contact)** : 1 BAT_F, 2 GND, 3 BUS, 4 CHOP_N, 5 GND | Un seul connecteur détrompé pour tous les fils « 42 V » de la carte. Courants : BAT_F ≤ 5,1 A en pointe (précharge 4,2 A + hôtel 0,9 A), BUS ≤ 4,2 A en pointe, CHOP_N ≤ 1,9 A, les deux GND ensemble ≤ 3,5 A. Le JST XH (3 A) serait trop juste pour la précharge |
| L2 | Précharge | **Reste sur la carte** : `SUD50P10-43L`, `MMBT5551`, zener, `SS510C` et la **résistance 10 Ω 5 W montée debout** (même `SQP500JB-10R`, empreinte verticale au pas de 10,16 mm) ; la sortie va au bus par `J1`-3 | Hors carte, il faudrait deux fils de plus et un montage en l'air ; sur la carte, la pointe de 4,2 A pendant 0,3 s passe par une piste de 1,2 mm (1 oz : ≈ 3,7 A en continu pour 20 °C, largement assez pour 0,3 s). Debout, la résistance prend 16 × 10 mm au lieu de 33 × 10 mm. Elle chauffe peu (8,6 J par précharge) mais elle est haute (≈ 25 mm) : la garder loin des fils |
| L3 | MOSFET du hacheur | **Reste sur la carte** (`IRL540N` TO-220 + roue libre `SS510C`) ; la résistance 22 Ω / 100 W est hors carte, entre la barrette BUS+ (fusible 5 A) et `J1`-4 | Hors carte, il faudrait faire passer la grille (12 V, 10 Ω) sur un fil et monter un TO-220 à la main sur la résistance. Sur la carte : 1,9 A par `J1`-4 et retour par les GND de `J1`, 0,2 W dans le MOSFET, pas de radiateur. La boucle de roue libre passe par le fil BUS : elle reste fermée tant que le fusible BUS est bon |
| L4 | 12 V PC (`URB4812YMD-30WR3`) | **Hors carte**, module sur une petite plaquette ou monté en l'air, alimenté par son propre fusible de 3 A à la barrette BAT+ | Il prend ≈ 25 × 35 mm (module + bornier) : 10 % d'une carte de 100 × 100. Il ne parle à rien sur la carte (broche Ctrl en l'air) ; le passer par la carte ajouterait 0,9 A dans le connecteur sans rien gagner. Une empreinte non montée garderait la place sans l'utiliser. 2,5 A en 12 V sur une plaquette, ce n'est pas 30 A : c'est acceptable. Les modules isolés du commerce testés ne conviennent pas : Mean Well `RSD-60H-12` démarre à 40 V (trop haut pour une batterie à 30–42 V), `RSD-60G-12` s'arrête à 36 V |
| L5 | TVS `SMCJ48CA` | **Sur la carte, à l'entrée BAT_F** (avec `C1`, `C2`) | Elle protège ce qu'il y a de fragile (deux `TPS54360B`, la logique). Le bus des moteurs a les condensateurs des variateurs et le hacheur, qui écrête la surtension de freinage (cause principale) à 43 V. Une TVS sur la barrette du bus devrait être montée en l'air : pas mieux |
| L6 | Fusible des rails | Supprimé de la carte (`F5`), remplacé par le fusible de 7,5 A du fil BAT_F (§5) | Le fusible protège un fil : il se met au départ du fil. 7,5 A et non 5 A parce que la précharge passe aussi par ce fil (5,1 A en pointe ; un fusible rapide de 5 A serait à 100 % de son calibre) |
| L7 | Anti-inversion des rails (`Q6`) | Gardé | Le connecteur VH est détrompé, mais c'est William qui sertit le fil |
| L8 | Shunt du bus | **Hors carte : shunt du commerce 50 A / 75 mV (1,5 mΩ, type FL-2)**, sur le BUS+ entre le contacteur et la barrette ; prises Kelvin (petites vis du shunt) vers `J2` par une paire torsadée courte ; les filtres 10 Ω (`R1`, `R2`) restent près de l'`INA228` | À 30 A : 45 mV, dans la gamme ±163,84 mV de l'`INA228` (ADCRANGE = 0) ; la gamme ±40,96 mV ne suffit plus (le firmware change : §6). 1,35 W dans le shunt à 30 A. ⚠️ Les deux fils Kelvin sont au potentiel du bus et **sans fusible** : un fil pincé contre le châssis met le bus en court-circuit par un fil fin. Les gainer, les garder courts (< 30 cm) et loin des arêtes ; voir §9 |
| L9 | Connecteur Kelvin | JST XH 2 broches (`J2`) | Courant nul ; détrompé |
| L10 | Cuivre | **1 oz** des deux côtés | Le courant le plus fort de la carte est la précharge (4,2 A pendant 0,3 s) ; tout le reste est ≤ 1,9 A (§4) |
| L11 | Taille | **100 × 140 mm** au lieu de 100 × 100 | Voir ci-dessous |
| L12 | Place des modules | Trois DevKitC côte à côte (pas de 28,7 mm), antennes au bord inférieur, en porte-à-faux de 3 mm, zone sans cuivre sous la partie de l'antenne qui reste au-dessus de la carte (comme `mainboard` M34) | Les trois largeurs (3 × 28,4 mm) tiennent dans 100 mm ; la colonne de droite (13 mm) reçoit les connecteurs SAFETY |
| L13 | Trous de fixation | 4 × M3 : deux en haut, un en bas à droite, un sur le bord gauche (y = 55,6 mm) | Les coins du bas sont pris par les rangées de supports |
| L14 | Méthode | Comme `mainboard` (M36) : un `scripts/build.py` copié de celui de `mainboard`, mêmes valeurs ; placement par « boîtes » (coin du contour de pièce) et groupes rangés avec l'écart le plus grand qui tient (2 mm à 0,4 mm). **GND n'est pas routé par Freerouting** : une via GND est posée à côté de chaque pastille CMS de masse avant le routage (183 vias), les deux faces sont coulées en GND après, puis des vias de couture et de jonction relient les morceaux de plan (`stitch`, `join`, `islands`, `gndvias`). Signaux et fils 42 V : Freerouting (20 passes, **une seule instance, `-Xmx3g`, un fil d'exécution** : sans limite, un routage prenait ≈ 14 Go de mémoire), nettoyage par [`scripts/patchroute_lb.py`](scripts/patchroute_lb.py) (copie de `patchroute_mb.py` sans bande de puissance) | Avec GND routé comme un signal, Freerouting n'aboutissait pas ; sans GND et sans vias posées d'avance, les plans se coupaient en îlots. Aucune modification des cartes existantes ni des scripts partagés. Le routage n'est pas déterministe : un nouveau `./build.sh` donne une carte équivalente, pas identique |
| L15 | Broche GND J3-7 des DevKitC | **Reliée à GND** (laissée en l'air sur `mainboard`) | C'est une broche de masse du module : une liaison de masse traversante de plus sous chaque module, sans effet sur le circuit |

**Pourquoi pas 100 × 100 mm.** La surface des pièces placées sans les modules fait
≈ 5 700 mm² de contours (dont 1 600 mm² pour les 12 connecteurs des variateurs, 1 300 mm²
pour les deux alimentations avec leurs selfs de 13,5 × 12,5 mm reprises telles quelles,
et ≈ 2 000 mm² de petits CMS). Sur 100 × 100 mm, il reste ≈ 9 000 mm² une fois les
supports retirés, mais les zones sous les modules ne reçoivent que des CMS bas : la bande
du haut (y < 50 mm) aurait dû porter ≈ 4 500 mm² de pièces sur 5 000 mm², sans place pour
router. Essais :

- **100 × 110 mm**, tous les petits CMS rangés sous les modules : tout se place, mais
  Freerouting laisse encore 73 liaisons non routées après 12 passes (sous les modules
  MOTION, 66 pièces chacun entre les rangées de supports). Abandonné.
- **100 × 120 mm**, prélèvements Hall sortis de dessous les modules : Freerouting arrive à
  ≈ 18–35 liaisons non routées, mais surtout **les plans GND des deux faces se coupent en
  40 à 100 îlots** : sous les modules, les rangées de supports et les pistes qui les longent
  enferment des zones de masse sur les deux faces à la fois, qu'aucune via ne peut plus
  rejoindre. Abandonné.
- **100 × 140 mm** : sous les modules ne restent que les étages DIR/STOP/EL (MOTION) et la
  logique de sécurité (SAFETY), espacés de 2 mm ; les blocs CAN/VR et les pièces côté
  connecteurs de SAFETY passent dans une rangée au-dessus des modules. C'est la taille
  retenue.

Pour revenir vers 100 × 100, il faudrait des selfs plus petites dans les deux
`TPS54360B` (≈ 7 × 7 mm, conçues pour le courant réel ≈ 1 A au lieu de 3,5 A) et une
quatrième couche ou des CMS des deux côtés : nouvelle conception d'alimentation et coût
d'assemblage plus élevé, non faits ici. Une carte 4 couches (plan de masse interne)
tiendrait probablement dans 100 × 110 mm, mais le cahier des charges impose 2 couches. À
100 × 140 mm, la carte fait 52 % de la surface de `mainboard`.

## 4. Cuivre 1 oz

Formule externe d'IPC-2221B, `I = 0,048 × ΔT^0,44 × A^0,725` (A en mil², 1 oz = 1,37 mil),
ΔT = 20 °C, piste externe ; du côté prudent par rapport à IPC-2152 (même méthode que
`mainboard` §4).

| Classe | Réseaux | Largeur | Courant admissible (20 °C) | Courant réel |
|---|---|---|---|---|
| PWR42 | BAT_F, BUS, PRE_P, PRE_N, CHOP_N | 1,2 mm | ≈ 3,7 A en continu | précharge 4,2 A pendant 0,3 s ; hacheur 1,9 A |
| SW | nœuds de commutation des deux buck | 1,0 mm | ≈ 3,2 A | ≤ 1,7 A crête |
| HV_RAIL | HOTEL_IN, bobine | 0,8 mm | ≈ 2,7 A | ≤ 1 A |
| RAIL | 5 V, 12 V AUX, 5V_BRAKE | 0,6 mm | ≈ 2,2 A | ≤ 1,3 A |
| RAIL_LO | 3V3, CH_12V | 0,3 mm | ≈ 1,3 A | ≤ 0,3 A |

La pointe de précharge dépasse le courant continu admissible de la piste de 1,2 mm, mais
dure 0,3 s : la constante de temps thermique d'une piste est de l'ordre de la seconde,
l'échauffement reste de quelques degrés. Le retour de la masse passe par les deux plans
GND.

Isolements : 0,5 mm pour PWR42 (comme `mainboard` HV_PWR), 0,3 mm pour SW et HV_RAIL,
0,2 mm ailleurs ; 0,15 mm minimum entre les pattes des boîtiers fins.

## 5. Distribution de puissance hors carte

### 5.1 Ce que je propose

**Barrettes de distribution + porte-fusibles MINI en ligne + fusibles Littelfuse MINI
58 V.**

- Les fusibles « blade » auto ordinaires (ATO, ATC, MINI standard) sont cotés **32 V DC** :
  **à ne pas utiliser** sur 42 V (C-S3).
- La série **Littelfuse MINI 58 V (`0997`)** existe de 2 à 30 A (2, 3, 4, 5, 7,5, 10, 15,
  20, 25, 30 A), coupe 1 000 A sous 58 V DC, et a une forme qui empêche de la remplacer
  par un fusible de tension plus basse. C'est la même série que `mainboard` M5.
- Porte-fusible : le **Littelfuse MINI FHM** en ligne (`0FHM0002ZXJ`, fils 12 AWG, 30 A ;
  `0FHM0001ZXJ`, 14 AWG, 20 A) est donné compatible avec les fusibles MINI 32 V **et
  MINI 58 V**. ⚠️ Le boîtier lui-même est marqué 32 V : à 42 V, c'est le fusible qui coupe
  l'arc (coté 58 V), le boîtier ne fait qu'isoler ; à faire confirmer à la relecture. Les
  boîtes à fusibles « 6 voies » d'automobile (32 V) et les porte-fusibles génériques sans
  marque sont moins chers mais rien ne garantit leur tenue : je ne les propose pas.
- Je n'ai pas trouvé de boîte à fusibles toute faite cotée ≥ 58 V DC à un prix de loisir :
  les barrettes + porte-fusibles en ligne sont la solution la moins chère qui reste cotée.

### 5.2 Câblage

```
                      fil 12 AWG (30 A)                         fil 18 AWG (≤ 7,5 A)
 BATTERIE + ──XT60──[ DISJONCTEUR ]──● BAT+ (borne du contacteur côté batterie)
                                     │
                                     ├──[F5  7,5 A]────────────────► J1-1  BAT_F   (carte)
                                     ├──[F8  3 A]──────────────────► module 12 V PC (+ entrée)
                                     │
                              [ CONTACTEUR ]  (bobine : J13 de la carte, NF ARU en série : J11)
                                     │
                              [ SHUNT 50 A / 75 mV ]──vis Kelvin──► J2-1 SNS_P / J2-2 SNS_N (paire torsadée)
                                     │
                         ════ BARRETTE BUS+ ════
                           │    │    │    │    │                  │
                        [F1] [F2] [F3] [F4] [F6 7,5 A]──────────► J1-3  BUS
                         25A  25A  25A  25A   │
                           │    │    │    │  [F7 5 A]──[ R 22 Ω 100 W ]──► J1-4  CHOP_N
                       AV_G AV_D AR_G AR_D    (ZS-X11H, + puissance)
                           │    │    │    │
 BATTERIE − ──XT60──── ════ BARRETTE GND ════ ──────────────────► J1-2 et J1-5  GND
                                     └──────► module 12 V PC (− entrée) ; sortie isolée → PC
```

Règles :

1. **Chaque fil qui part d'une barrette passe d'abord par son fusible**, monté au plus près
   de la barrette (le fusible protège le fil qui le suit).
2. Fils de 30 A (batterie, contacteur, shunt, barrettes) : 12 AWG silicone au moins, cosses
   serties (pince à sertir, pas soudées seules), vis serrées avec rondelle éventail.
3. Fils vers les variateurs : 12 ou 14 AWG (25 A de fusible : 12 AWG).
4. Fils vers la carte : 18 AWG pour `J1`, 22–24 AWG torsadés pour `J2`.
5. Le négatif n'est jamais commuté ; la barrette GND est le point étoile (remplace la
   pastille « − » du XT30 de `mainboard`).
6. **Jamais de 30 A sur une plaque à trous.** La plaquette du module 12 V PC ne porte que
   1,1 A en entrée et 2,5 A en sortie.

### 5.3 Connecteur batterie

Hors carte, rien n'impose plus le XT30 : je propose un **XT60** (fil 12 AWG), coté pour le
courant des moteurs, ce qui **supprime la limite de 15 A** de `mainboard` §2. C'était une
décision de William pour la carte (XT30 pour CI) : à confirmer (question n° 1). Avec un
XT30 sur fil, la limite de 15 A et la règle logicielle de `mainboard` §2 restent.

### 5.4 Calibres

| Fusible | Calibre | Fil protégé | Courant normal | Pourquoi ce calibre |
|---|---|---|---|---|
| F1–F4 | 25 A MINI 58 V (`0997025.WXN`) | variateur | ≤ 7,5 A typique | comme `mainboard` M5 : protection contre le court-circuit franc |
| F5 | 7,5 A MINI 58 V | BAT_F (rails + précharge) | 0,9 A, 5,1 A pendant 0,3 s | L6 |
| F6 | 7,5 A MINI 58 V | BUS vers la carte | mA (mesure, commande du hacheur) ; 4,2 A pendant la précharge | même raison |
| F7 | 5 A MINI 58 V | résistance du hacheur | 1,9 A quand il hache | 2,6 fois le courant normal. ⚠️ Fusible fondu = hacheur hors service : le firmware le voit (VBUS > 43 V sans baisse) et ouvre `/SAFE` |
| F8 | 3 A MINI 58 V | module 12 V PC | 1,1 A à 30 V | appel de courant au branchement |

## 6. GPIO et firmware

Les tables de GPIO sont **celles de `mainboard` §7, sans changement** (mêmes signaux sur
les mêmes broches pour les trois ESP32 ; IMU câblée comme `board_config.h` : SPI3, SCLK 18,
MISO 19, MOSI 23, CS 22, INT 25, RST 33, PS0 26, PS1 au 3V3).

Changements pour le firmware SAFETY :

- **Shunt de 1,5 mΩ** (au lieu de 1 mΩ) et **ADCRANGE = 0** (±163,84 mV) dans l'`INA228` ;
  recalculer `SHUNT_CAL` ; vérifier la vraie valeur du shunt acheté (classe 0,5 % en
  général).
- Le hacheur a maintenant un fusible (F7) : VBUS > 43 V qui ne redescend pas pendant
  quelques centaines de ms → défaut, `/SAFE` bas.
- Avec un XT60 (si William l'accepte), la limite de 13 A de `mainboard` §2 n'est plus
  nécessaire ; garder une limite à 30 A continus (fusibles et fils).
- Les règles de précharge de `mainboard` §6.1 restent toutes vraies.

## 7. Budget des rails

| Rail | Charges | Courant | Source |
|---|---|---|---|
| 5 V | comme `mainboard` §8 | ≈ 0,5 A typique, ≈ 1,0 A pointe | `TPS54360B` |
| 12 V AUX | bobine (≤ 1 A si 12 V), ventilateur (≈ 0,2 A) | ≤ 1,3 A | `TPS54360B` |
| 12 V PC | hors carte | ≤ 2,5 A | module sur F8 |
| HOTEL_IN (42 V) | 5 V (≈ 6 W), 12 V AUX (≈ 18 W), rendements 85–88 % | **≈ 0,7 A à 42 V, ≈ 0,9 A à 30 V** | F5 (7,5 A) |

## 8. Fabrication PCBWay et coût estimé

### 8.1 Ce que PCBWay reçoit (`fab/`, produit par `fab.sh`)

| Fichier | Contenu |
|---|---|
| `logic_board_gerbers.zip` | Gerber 2 couches + perçage Excellon |
| `bom_pcbway_fine.csv`, `centroid_pcbway_fine.csv` | **commande proposée** : PCBWay pose seulement les pièces « fines » (`fab_pcbway.py --fine-only`) |
| `bom_pcbway.csv`, `centroid_pcbway.csv` | variante : PCBWay pose tous les CMS |
| `schematic.pdf`, `assembly_top.pdf`, `render_top.png`, `render_bottom.png` | schéma, plan d'assemblage, rendus |

Paramètres de commande : 2 couches, FR-4 TG150, 1,6 mm, **cuivre 1 oz**, vernis vert,
sérigraphie blanche, HASL sans plomb, 100 × 140 mm, 5 cartes, assemblage d'une seule carte.

**Avec `--fine-only` : PCBWay pose 190 pièces (≈ 492 pastilles, 49 lignes) ; William soude
105 pièces** (28 traversantes : connecteurs, supports, IRL540N ×2, 10 Ω 5 W, 2200 µF,
cavalier ; et 77 CMS plus gros : SMC/SMA, SOD-123, SOT-23 à 3 pattes, SOIC-8, 0805, 1206,
1210, DPAK, selfs, condensateurs électrolytiques). 102 lignes de BOM au total (dont R67
non montée). Variante « tous les CMS » : 267 pièces posées, 74 lignes.

Pour `mainboard` (option A), les mêmes scripts donnent 192 pièces / 50 lignes posées en
`--fine-only` (273 / 78 en tous CMS) : **le nombre de pièces posées est presque le même**,
puisque toutes les petites pièces sont sur les deux cartes.

### 8.2 Coût estimé — **estimations, pas un devis**

Même méthode et mêmes réserves que `mainboard` §10.2 (ordres de grandeur, tarifs publiés
de JLCPCB pour l'assemblage). **Faire un devis en ligne avec chaque dossier `fab/`.**

| Poste | A : `mainboard` (§10.2, en `--fine-only`) | B : `logic_board` |
|---|---|---|
| PCB 5 ex. | 40–80 € (180 × 150, 2 oz) | 10–30 € (100 × 140, 1 oz ; au-dessus du palier 100 × 100) |
| Assemblage d'1 carte (≈ 500 joints) | 30–80 € | 30–80 € |
| Pièces fines pour 1 carte | 30–50 € | 30–50 € |
| Port DHL | 20–35 € | 20–35 € |
| **Commande PCBWay** | **≈ 120–245 €** | **≈ 90–190 €** |
| Pièces propres à l'option, achetées par William | ≈ 15–25 € (XT30, 4 Keystone 3568, NANO2 5 A, boulonnerie M4/M5, bornier 12 V PC) | ≈ 60–140 € (distribution hors carte : `README.md`) |

Les pièces communes aux deux options (CMS plus gros, connecteurs, supports, module 12 V PC,
résistance de 22 Ω / 100 W, fils vers les variateurs, DevKitC) ne changent pas la
comparaison.

**Verdict.** B coûte ≈ 30–55 € de moins chez PCBWay (le PCB nu), mais ≈ 35–115 € de plus
en pièces hors carte achetées par William, et plus de câblage. Aucune des deux options ne
tient dans 60 €. Le vrai gain de B est technique : plus de 30 A sur le PCB, plus de 2 oz,
plus de limite de 15 A du XT30 (si le XT60 est accepté).

## 9. Ce qui n'est pas vérifié

- **Routage inachevé** (vérifié par `kicad-cli pcb drc --schematic-parity --severity-all`
  le 24/11/2026) : 48 éléments non connectés — 31 liaisons de signal (surtout les
  commandes VR/DIR/EL/STOP qui remontent des modules vers les connecteurs du haut, BUS,
  CHOP_N, CANH, SPI de l'IMU, BMS) et 17 morceaux de plan GND coupés du reste — et 12 pistes
  en l'air. Aucun court-circuit ni défaut d'isolement. Quatre routages complets ont été
  essayés (≈ 2 h chacun, une seule instance de Freerouting à 3 Go) ; Freerouting plafonne à
  18–40 liaisons et le nettoyage `patchroute` n'en rattrape qu'une partie. Il reste à finir
  à la main dans KiCad, ou à passer en 4 couches (plan GND interne), ce que le cahier des
  charges exclut.

- Tout ce que liste `mainboard` §11 et qui concerne les circuits repris (P1, `SQP500JB-10R`
  en surcharge, compensation des `TPS54360B`, références LCSC des `SN74…DCTR`, pouvoir de
  coupure du contact NF, DAC de l'ESP32, niveau des capteurs Hall).
- Les porte-fusibles MINI FHM : compatibles 58 V d'après Littelfuse, boîtier marqué 32 V ;
  tenue à 42 V à faire confirmer. Délais de livraison longs constatés chez les
  distributeurs.
- Prix et stocks hors carte : estimations, aucun prix relevé ferme.
- Shunt du commerce : valeur réelle (souvent ±0,5 %), échauffement à 30 A, tenue des vis
  Kelvin aux vibrations.
- Fils Kelvin sans protection (L8) : à relire. Une option est de mettre une résistance de
  10 Ω fusible côté shunt, mais elle double la résistance du filtre de l'`INA228` (erreur
  de gain à évaluer avec la fiche technique).
- La résistance de précharge debout : tenue mécanique aux vibrations (la coller ou la
  brider), distance aux fils.
- Retour de masse : les masses des variateurs reviennent à la barrette GND, la logique par
  `J1` ; l'écart entre les deux (≈ 10–80 mV selon les fils) n'est pas mesuré.
- Routage autorouté (Freerouting + nettoyage) : lisible, pas soigné ; boucles d'entrée et
  nœuds SW des buck à reprendre à la main, comme sur `mainboard`.
- Aucun calcul thermique de la carte 1 oz ; aucune mesure.

## 10. Questions ouvertes pour William

1. **Connecteur batterie** : XT60 sur fil (plus de limite de 15 A) ou XT30 (limite et règle
   logicielle de `mainboard` §2 gardées) ?
2. **100 × 140 mm** acceptable, ou faut-il refaire les deux alimentations avec des selfs
   plus petites pour viser 100 × 100 mm ?
3. Le parrainage PCBWay couvre-t-il seulement la commande PCBWay ? Alors B déplace
   ≈ 35–115 € de pièces vers toi.
4. Mêmes points que `mainboard` : tension de bobine (JP1), pouvoir de coupure DC de l'arrêt
   d'urgence, niveau du BMS (R67), P1 et P3.
5. Où monter la distribution (barrettes, contacteur, shunt, fusibles) sur le châssis, à
   l'abri des chocs et des projections ?
