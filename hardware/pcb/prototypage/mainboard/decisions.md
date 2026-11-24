# Décisions de conception — `mainboard` v1.0-draft

> **v1.0-draft — ne pas fabriquer avant P1, coil voltage, BMS level, and a review by an
> electronics engineer.**

Carte unique qui remplace `safety_power`, `motor_interface` ×2 et
`safety_bus_distribution` pour un premier montage bon marché. William a délégué tous les
choix techniques ; ceux qu'il a tranchés lui-même sont dans
[`cahier-des-charges.md`](cahier-des-charges.md) §3 et ne sont pas rediscutés ici.

Tout ce qui suit est **calculé ou simulé, rien n'est mesuré**. ERC 0 et DRC 0 disent que
le schéma est cohérent et que la carte respecte les règles de fabrication ; ils ne disent
pas que le circuit marche.

## Sommaire

1. [La carte en une phrase](#1-la-carte-en-une-phrase)
2. [Connecteur batterie XT30 : la limite à connaître](#2-connecteur-batterie-xt30--la-limite-à-connaître)
3. [Décisions](#3-décisions)
4. [Cuivre de puissance (IPC-2152)](#4-cuivre-de-puissance-ipc-2152)
5. [Hacheur](#5-hacheur)
6. [Précharge et contacteur](#6-précharge-et-contacteur)
7. [Tables des GPIO](#7-tables-des-gpio)
8. [Budget des rails](#8-budget-des-rails)
9. [Ce qui a été abandonné](#9-ce-qui-a-été-abandonné)
10. [Fabrication PCBWay et coût estimé](#10-fabrication-pcbway-et-coût-estimé)
11. [Ce qui n'est pas vérifié](#11-ce-qui-nest-pas-vérifié)
12. [Questions ouvertes pour William](#12-questions-ouvertes-pour-william)
13. [Propositions de modification de l'ICD](#13-propositions-de-modification-de-licd)

---

## 1. La carte en une phrase

La batterie arrive sur un XT30, repart vers le contacteur mécanique externe par une borne
M5 et revient par une seconde borne M5 ; le bus (BUS+) traverse un shunt de 1 mΩ puis
alimente le hacheur et quatre sorties fusées vers les ZS-X11H ; en amont du contacteur,
un fusible de 5 A alimente les rails hôtel (5 V, 12 V AUX, 12 V PC isolé) ; trois
ESP32-DevKitC V4 enfichés commandent la précharge, la bobine du contacteur, `/SAFE` et
les quatre variateurs, et se parlent en CAN par des pistes.

**Format : 180 × 150 mm, 2 couches, cuivre 2 oz, 1,6 mm.** 4 trous M3 non métallisés.
Bande de puissance en haut (y < 40,5 mm), alimentations hôtel au milieu, connecteurs moteurs
au-dessus des trois DevKitC alignés en bas, connecteurs SAFETY (IMU, arrêt d'urgence, bobine,
CAN, BMS) sur le bord gauche. 273 CMS, 39 traversants, 881 vias, ERC 0, DRC 0 (toutes
sévérités, parité schéma comprise), 0 non connecté.

## 2. Connecteur batterie XT30 : la limite à connaître

**Décision de William (23 novembre 2026) : XT30 pour CI, `XT30PW-M` (Amass), LCSC
C431092.** Elle n'est pas rediscutée ; voici ce qu'elle implique.

- **Courant admissible.** Les fiches distributeurs de l'Amass XT30 donnent **15 A en
  continu et 30 A en pointe** (fil de 18 AWG). Le catalogue Amass groupe aussi le
  `XT30PW-M` avec une valeur « 20 A max, échauffement < 85 °C ». ⚠️ Je n'ai **pas pu lire
  la valeur sur la fiche PDF Amass elle-même** : on retient l'hypothèse prudente, 15 A
  continus.
- **Ce que tirent les moteurs.** 4 × 250 W à 37 V font ≈ 27 A ; avec les pointes de
  démarrage, ≈ 30 A. **Le courant total des moteurs doit rester sous 15 A en continu**,
  sinon le connecteur chauffe (résistance de contact, plastique qui ramollit, à terme
  contact qui se dégrade et chauffe encore plus).
- **Limite logicielle proposée.** L'`INA228` de la carte mesure le courant du bus sur le
  shunt RS1 (côté batterie du bus, donc le courant du XT30 moins les ≤ 2 A des rails
  hôtel). Le firmware SAFETY applique :
  - **limite continue : 13 A** en moyenne glissante sur 10 s (15 A du XT30 moins 2 A de
    rails hôtel) ;
  - **pointe tolérée : 25 A pendant 2 s au plus** ;
  - au-delà : SAFETY demande aux MOTION, par CAN, de réduire la consigne VR ; si le
    dépassement dure, SAFETY tire `/SAFE` bas (freins serrés).
  L'`INA228` a une sortie d'alerte matérielle (non câblée ici, faute de GPIO) et un
  accumulateur de charge : la limite reste logicielle.
- **Pas de chemin de mise à niveau par empreinte.** Le XT60 (`XT60PW-M`) a une autre
  empreinte (entraxe 7,2 mm contre 5 mm, broches plus grosses) : on ne peut pas souder un
  XT60 à la place du XT30 sur cette carte. Passer au XT60 demande une révision de la
  carte. Le reste du chemin de puissance (cuivre, bornes M5/M4, fusibles) est déjà
  dimensionné pour 30 A : seul le connecteur changerait.
- **Câble.** Côté batterie, une fiche XT30 femelle (`XT30U-F`) sur fil 14 AWG au moins
  (le 18 AWG des fiches techniques est le minimum du connecteur, pas du courant).
- Polarité : sur l'empreinte KiCad `AMASS_XT30PW-M`, la pastille 2 est « + » et la
  pastille 1 « − » (sérigraphie du fabricant reprise par KiCad). À vérifier sur la pièce
  avant de souder.

## 3. Décisions

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| M1 | Couches et cuivre | **2 couches, 2 oz (70 µm) des deux côtés, 1,6 mm** | Le chemin de 30 A en 1 oz demanderait des bandes de 21,5 mm (§4) et une carte plus grande ; en 2 oz, 13 mm suffisent. 4 couches coûteraient plus que le surcoût du 2 oz. Le 2 oz impose 0,15 mm minimum entre pistes chez PCBWay : on garde 0,2 mm partout sauf entre les pattes des boîtiers fins |
| M2 | Répartition des couches | F.Cu : polygones 42 V (BAT_P, BUS_P, BUS, branches, CHOP_N) puis signaux ; B.Cu : **plan GND plein sous toute la bande de puissance** (aucune piste n'y est autorisée), puis signaux ; GND coulé sur les deux faces partout ailleurs, après le routage | Le retour de 30 A passe par le plan B.Cu, large de toute la carte ; le point de retour est la pastille « − » du XT30 |
| M3 | Point étoile | La pastille « − » du XT30 est le seul point où le négatif entre ; il n'y a qu'une masse (GND) sur la carte | Décision de William : un seul négatif, jamais commuté |
| M4 | Bornes de puissance | **Goujon et cosse à œil** : M5 pour le contacteur (paire au pas de 26 mm), M4 pour les 4 sorties variateurs et le hacheur (paires au pas de 13 mm). Trous métallisés avec couronne de 8 vias | Même choix que `safety_power` (S26) : aucune empreinte KiCad de bornier 30 A, et une cosse sertie vissée tient aux vibrations. Coût : une vis et un écrou par pôle |
| M5 | Fusibles des branches | **Littelfuse `0997025.WXN` (MINI 58V, 25 A) dans Keystone `3568`** | Repris de `safety_power` (S25). Coté 58 V DC (C-S3). Je n'ai rien trouvé de moins cher et coté 58 V DC avec une empreinte KiCad sûre. À 15 A au total, un fusible de 25 A ne protège que contre le court-circuit franc, ce qui est son rôle |
| M6 | Fusible hôtel | **Littelfuse `0452005.MRL` (NANO2, 5 A, 125 V AC/DC), CMS** | Coté au-dessus de 58 V DC ; ≤ 1,9 A de charge hôtel à 30 V (§8) |
| M7 | Anti-inversion hôtel | FET P `SUD50P10-43L` en diode idéale + zener 12 V + 100 kΩ (comme `safety_power` S11) | Le XT30 est détrompé, mais c'est William qui soudera la fiche sur le pack : une inversion détruirait les deux `TPS54360B`. 3 pièces, 0,1 W perdu |
| M8 | TVS d'entrée | **`SMCJ48CA` bidirectionnelle** entre BAT_P et GND, + 2 × 2,2 µF 100 V | `safety_power` S-TVS / S9 : une unidirectionnelle conduirait sur une batterie inversée |
| M9 | Mesure du courant | **1 × `INA228` + shunt `WSK25121L000FEA` 1 mΩ 4 fils** sur BUS, côté batterie | Peu cher (≈ 3 pièces de plus) et indispensable pour la limite du XT30 (§2). Prises Kelvin et filtre 10 Ω tracés par le script ; la broche VBUS de l'INA228 est reliée à IN− (prise Kelvin côté bus, après les 10 Ω : erreur < 0,01 % vu l'impédance d'entrée VBUS) — mesure précise de VBUS en plus du diviseur. Une zone interdite aux pistes protège le cuivre de 30 A entre la borne RETOUR et le shunt |
| M10 | Mesures ADC | VBAT : 243 kΩ / 10 kΩ sur GPIO39, **pris après le fusible hôtel (HOTEL_F)** : même tension que BAT+ à 30 mV près, toujours en amont du contacteur, et accessible depuis la zone logique (si le fusible hôtel fond, les ESP32 sont éteints de toute façon) ; VBUS : 243 kΩ / 10 kΩ sur GPIO34 ; 100 nF chacun | 42 V → 1,66 V, 60 V → 2,37 V : sous le plein échelle de l'ADC (≈ 3,1 V à 11 dB) même en surtension, sans écrêteur. Les deux diviseurs ont la même dérive : la comparaison VBUS ≥ VBAT − 1 V reste juste à ±0,6 V ; l'INA228 donne VBUS à mieux que 0,1 % |
| M11 | 5 V | **`TPS54360B`** (valeurs de `safety_power` §5.1–5.2, 15 µH `SRP1265A-150M`, 3 × 47 µF) | Je n'ai pas trouvé de module traversant ≥ 60 V d'entrée et ≥ 1,5 A non isolé dont je puisse vérifier le brochage ; les modules isolés 10–30 W coûtent 10 à 25 €. Le `TPS54360B` coûte quelques euros de pièces et ses valeurs sont déjà calculées. Le rail est surdimensionné (3,5 A pour ≈ 1 A) : c'est la conception existante, sans risque nouveau |
| M12 | 12 V AUX | **Gardé**, second `TPS54360B` (valeurs `safety_power`, 33 µH) | Presque gratuit en coût (≈ 3 € de pièces), et nécessaire : si la bobine du contacteur est en 12 V, il faut un 12 V non isolé capable d'1 A. Il alimente aussi le ventilateur (J8, toujours allumé) |
| M13 | 12 V PC | **Mornsun `URB4812YMD-30WR3`** gardé (18–75 V, 12 V / 2,5 A, isolé 1500 V) | Brochage déjà relu (`safety_power` §5.3). ⚠️ Stock LCSC faible (8 pièces au 14/11) : acheter chez Mouser/Digi-Key. Broche Ctrl laissée en l'air = marche (plus de GPIO pour la couper). Sortie sur bornier Phoenix MKDS 5,08 mm (2,5 A ; le XH à 3 A aurait été trop juste) |
| M14 | 3V3 | Régulateur de chaque DevKitC (aucun régulateur ajouté) | Charges ajoutées ≤ 30 mA par module (IMU, INA228, VIO du TCAN, logique, pull-up `/SAFE`) |
| M15 | 5 V vers les DevKitC | **`B5819W` en série** entre le rail 5 V et la broche 5V de chaque module | Un câble USB branché sur un seul module ne doit pas alimenter toute la carte (les autres modules, les transceivers, la sortie du buck). Chute 0,3 V : 4,7 V à l'entrée du régulateur de la DevKitC, suffisant |
| M16 | CAN | 3 × `TCAN1042HVDR`, STB à la masse, VIO = 3V3 du module, VCC = 5 V ; **120 Ω près du transceiver ARRIÈRE** (bout de bus) ; XH 3 broches + `NUP2105L` vers le CANable | Le CANable Pro termine l'autre bout (sa terminaison commutable doit être **activée**). Pas de self de mode commun : bus de quelques centimètres sur la carte |
| M17 | VR | **DAC interne de l'ESP32 (GPIO25/26) + `TLV9062` en gain 1,68** (6,8 kΩ / 10 kΩ), 100 Ω série, 10 kΩ à la masse | Supprime le `MCP4728` et le bus I²C des MOTION. Résolution : 8 bits, 5 V / 256 ≈ **20 mV par pas (0,4 % de la pleine échelle)** ; la boucle de vitesse n'a pas besoin de mieux (le ZS-X11H a lui-même une zone morte d'environ 1 V). Le DAC de l'ESP32 sort ≈ 0,1 à 3,2 V : VR ≈ 0,15 à 5 V (écrêté par le TLV9062 à ≈ 4,98 V). DAC éteint ou ESP32 en reset : 100 kΩ tient l'entrée à 0, VR = 0 |
| M18 | Prélèvement Hall | Repris de `motor_interface` v2 sans changement (2,2 kΩ vers le 5 V du variateur, 2,2 kΩ + 10 nF, `BAT54S`, `SN74LVC3G17`) | Simulé en v2 (`simulations.md` §3). Le 5 V des capteurs Hall vient toujours du variateur par le connecteur de passage : la carte ne l'alimente pas (pas de conflit entre deux 5 V) |
| M19 | `SN74LVC3G17` et `74LVC1G74` | Boîtier **DCT (SSOP-8, pas de 0,65 mm)** au lieu de DCU (0,5 mm) | Le 2 oz supporte mal le pas de 0,5 mm ; même brochage TI |
| M20 | DIR, STOP, EL | Repris de `motor_interface` (AO3400A, 100 kΩ sur les grilles, `SN74LVC1G08`) ; **options de polarité DIR/STOP (non montées en v2) supprimées** | Pièces non montées = empreintes qui prennent de la place ; à rajouter seulement si M7/HALL_OC le demande |
| M21 | Voyants de frein et lecture de EL | **Supprimés** (troisième `SN74LVC3G17`, 10 kΩ / 1 MΩ, LED) | Moins de CMS ; l'état du frein reste lisible au variateur |
| M22 | Watchdog des MOTION | **Pas de `TPL5010` sur les MOTION** : chien de garde interne de l'ESP32 (RTC WDT, task WDT) + surveillance du battement CAN par SAFETY | Si un MOTION se bloque, SAFETY ne reçoit plus son battement et tire `/SAFE` bas : les portes ET coupent EL, les freins serrent. S'il redémarre, ses GPIO flottent, les pull-down 100 kΩ bloquent les MOSFET, le frein serre. Le watchdog matériel reste sur SAFETY, qui est le seul à pouvoir ouvrir `/SAFE` et la bobine |
| M23 | Verrou watchdog SAFETY (D7) | `TPL5010` (1,0 s, 5,23 kΩ) ; sa sortie RSTn (drain ouvert) **et** un RC de mise sous tension (10 kΩ / 1 µF, ≈ 10 ms) remettent à zéro le `74LVC1G74` ; `Q̄` commande Q9 qui tire `/SAFE` bas ; réarmement par un front sur `SAFE_REARM` (GPIO21) | Comme `safety_power` S17, sans la porte ET (la voie surintensité ACS758 n'existe plus) : RSTn et le RC se partagent le même nœud. 100 Ω entre RSTn et le condensateur limitent le courant de décharge. Le pull-up 100 kΩ de `Q̄` (R142 de v2) est supprimé : `Q̄` est une sortie push-pull, définie dès que le 3V3 dépasse ≈ 1,65 V, et en dessous `/SAFE` n'a de toute façon pas de pull-up alimenté (place manquante au routage) |
| M24 | Bobine du contacteur | `SN74AHCT1G08` alimenté en 5 V : **COIL_EN (GPIO32) ET LATCH_Q** → `IRL540N` côté bas (5 V de grille), diode `S1M` aux bornes de la bobine ; **contact NF CH2 de l'arrêt d'urgence en série** (J11) ; sélecteur **12 V AUX / BAT par cavalier** (JP1) | Le cavalier, au contraire d'un pont de soudure à 3 plots, ne peut pas relier 12 V et BAT ensemble. **Livré sans cavalier** : le contacteur ne peut pas se fermer tant que la tension de bobine n'est pas connue. LATCH_Q dans la porte : si le watchdog de SAFETY déclenche, la bobine retombe aussi, pas seulement les freins. La diode seule ralentit la retombée (quelques dizaines de ms) : voir questions ouvertes |
| M25 | MOSFET traversants | **`IRL540NPBF`** (TO-220, 100 V, 44 mΩ à 10 V, 53 mΩ à 5 V) pour le hacheur (Q5) **et** la bobine (Q10) | Une seule référence ; soudée à la main ; 0,2 W au plus dans le hacheur (1,9 A), pas de radiateur. V_GS max ±16 V : la grille du hacheur reçoit 12,1 V |
| M26 | Hacheur | **Bloc de `safety_power` v2.1 inchangé**, références comprises (R19–R33, C9–C14, U3–U5, D8–D10, Q5, J12) | Exigence C-S2. Seul le MOSFET change (`IRL540N` au lieu de l'`IPB017N10N5LF`) et le `TPS7A4001` passe sur une empreinte à pattes de 0,42 mm (motif TI DGN ≤ 0,45 mm) pour tenir 0,2 mm entre pastilles. `CHOP_ACT` va sur un point de test, pas sur un GPIO (plus de broche libre) : le firmware déduit l'activité du hacheur de VBUS > 43 V |
| M27 | Décharge active du bus (`DISCH_REQ`) | **Supprimée** | Plus de GPIO libre sur SAFETY. Le bus se décharge par les variateurs ; à rajouter si un essai montre que c'est trop lent |
| M28 | `/SAFE` | 1 kΩ depuis le 3V3 de SAFETY → J10 (contact NF CH1 de l'arrêt d'urgence) → `/SAFE` ; 10 kΩ vers GND ; `ESD5Z3.3` ; Q8 (`SAFE_HOLD`, GPIO13, grille tirée haut 10 kΩ : ESP32 absent ou en démarrage = `/SAFE` bas) ; Q9 (verrou) ; lecture par SAFETY à travers 1 kΩ, par chaque MOTION à travers 47 kΩ ; portes ET des MOTION directement sur `/SAFE` (entrées `Ioff`) | Repris de `safety_power` S18/S19 et `motor_interface`. Module SAFETY retiré : pas de 3V3 pour le pull-up → `/SAFE` bas. Le cavalier « e-stop radio » de v2 est supprimé : un contact radio se câble en série dans la boucle |
| M29 | IMU | Support femelle 1×10 au pas de 2,54 mm, le module BNO085 s'enfiche directement ; **pas de résistances série** | Pistes de quelques centimètres à 1 MHz : les 33 Ω de v2 (câble de 8 voies) ne servent plus. PS1 au 3V3, VCC sur le 3V3 de SAFETY, broches exactement comme `board_config.h` |
| M30 | BMS | JST GH 4 broches (comme J2 de v2) ; RX : 1 kΩ série + `BAT54S` vers GND/3V3 + 10 kΩ de rappel au 3V3 ; TX : 100 Ω série + `BAT54S` ; **option 5 V : R67 (22 kΩ vers GND, non montée)** | Avec 1 kΩ et l'écrêteur, une sortie BMS en 5 V n'injecte que 1,4 mA dans le 3V3 : tolérée. R67 forme avec R65 un diviseur (5 V → 4,4 V avant écrêtage) pour réduire encore ce courant si M3 montre un BMS 5 V. Un TX à 3,3 V est lu « haut » par une entrée TTL 5 V (2,0 V), pas par une entrée CMOS 5 V (3,5 V) : à vérifier avec PACK_ID |
| M31 | Connecteurs signaux | **JST XH** (2,5 mm) pour Hall, commandes, arrêt d'urgence, bobine, CAN, ventilateur | Quelques centimes pièce contre 1 à 3 € pour un Micro-Fit ; 3 A par contact suffisent partout (bobine ≤ 1 A) |
| M32 | Connecteur de commande variateur | **XH 6 broches : 1 VR, 2 DIR, 3 EL, 4 STOP, 5 GND, 6 5V_BRAKE** | Nouveau brochage (pas de NTC). Un ancien faisceau Micro-Fit 8 voies ne peut pas s'y brancher : pas de risque de 5 V sur une ancienne broche (ICD `NE PAS RÉAFFECTER`) |
| M33 | 5V_BRAKE | 5 V → **`SS34`** → **réservoir 2200 µF** (+10 µF) → **220 Ω 1206 par sortie** → broche 6 de chaque connecteur de commande | D5. Les quatre pull-up 2,2 kΩ du faisceau tirent 4 × 2,3 mA ; 220 Ω font chuter 0,5 V (EL haut ≈ 4,5 V) et limitent un court-circuit de faisceau à 23 mA (0,11 W) sans vider le réservoir ni faire tomber le 5 V. Remplace les eFuses de v2 |
| M34 | Place des modules | Les trois DevKitC alignés en bas, **antenne au bord inférieur, en porte-à-faux de 3 mm** ; aucune piste ni cuivre sous la partie de l'antenne qui reste au-dessus de la carte | Recommandation Espressif ; ni plan de masse ni piste sous l'antenne |
| M35 | CMS sous les modules | Empreinte DevKitC dont la zone d'occupation se limite aux deux rangées de supports : les CMS de chaque nœud sont placés **entre les rangées, sous le module** | Supports de 8,5 mm : place libre sous le module. Gain : la carte serait 30 mm plus longue sinon. Les pièces sous le module restent accessibles en retirant le module |
| M36 | Méthode | Comme `safety_power` : cuivre de puissance par zones posées par le script ; prises Kelvin, filtre de l'INA228, liaisons de R3, R19 et du diviseur VBAT tracés à la main par le script (pistes verrouillées) ; signaux par Freerouting (40 passes, marge de 20 µm sur les isolements du DSN) ; nettoyage par [`scripts/patchroute_mb.py`](scripts/patchroute_mb.py) (copie de `safety_power/scripts/patchroute.py` limitée à F.Cu/B.Cu, B.Cu interdit sous la bande de puissance, boîte de recherche élargie en dernier essai) ; GND coulé sur les deux faces ; vias de couture GND au pas de 4 mm là où les deux faces sont en GND | Mêmes outils, aucune modification des cartes existantes. Le routage n'est **pas déterministe** et prend plusieurs heures sur cette carte : un nouveau `./build.sh` donne une carte équivalente, pas identique, et peut laisser une ou deux connexions à finir. **La carte livrée (23/11/2026) a demandé une dizaine de reprises locales** après le routage : vias remis là où le nettoyage les avait retirés, fin des liaisons I²C de l'INA228 et de `CH_VIN`/`CH_DRV`/`CH_G`, `R29`/`R30` déplacées près de la grille de Q5 (`MOVED_AFTER_PACK`), vias GND ajoutés dans les îlots de plan (`islands`). Ces reprises sont dans le fichier `.kicad_pcb`, pas toutes dans `build.py` |

## 4. Cuivre de puissance (IPC-2152)

**Méthode.** IPC-2152 (fig. 5-1, conducteur de référence) ramené au cas d'une piste externe
au-dessus d'un plan, approché ici par la formule externe d'IPC-2221B,
`I = 0,048 × ΔT^0,44 × A^0,725` (A en mil²). Pour une piste externe de 1,6 mm d'épaisseur
de carte, IPC-2152 donne en général des largeurs égales ou plus faibles (la présence du plan
B.Cu à 1,5 mm abaisse encore l'échauffement) : les chiffres ci-dessous sont **du côté
prudent**. ⚠️ Approximation : à refaire avec un calculateur IPC-2152 complet (Saturn PCB
Toolkit, mode IPC-2152 avec plan) lors de la relecture.

Largeur pour ΔT = 20 °C :

| Courant | 1 oz | 2 oz |
|---|---|---|
| 15 A (limite XT30) | 8,3 mm | 4,1 mm |
| 30 A (exigence) | **21,5 mm** | **10,7 mm** |

**Choix : 2 oz.** En 1 oz, les bandes de 21,5 mm pour BAT, BUS_P et BUS allongeraient la
carte d'environ 10 mm en hauteur et élargiraient chaque branche ; le surcoût du 2 oz
(voir §10) est inférieur au surcoût de surface, et le 2 oz garde la marge si un XT60
remplace un jour le XT30 (sur une carte révisée).

Échauffement calculé des polygones dessinés (2 oz, formule ci-dessus, régime établi) :

| Tronçon | Largeur mini | Courant | ΔT |
|---|---|---|---|
| BAT_P (XT30 → borne VERS CONTACTEUR) | 21,5 mm (moins la pastille « − » du XT30 : ≥ 18 mm) | 30 A | ≈ 7–9 °C |
| BUS_P (borne RETOUR → shunt) | 18 mm, puis 5,5 mm sur 4 mm de long avant la pastille du shunt | 30 A | ≈ 8 °C ; **≈ 60 °C local** sur le col de 5,5 mm (court, relié à de grandes surfaces ; le shunt 2512 lui-même est plus étroit). À relire |
| Barre BUS (shunt → fusibles, hacheur) | 16,5 mm | 30 A | ≈ 10 °C |
| Branche (fusible → borne M4) | 8,4 mm | 7,5 A typique / 25 A fusible | ≈ 1,5 °C / ≈ 21 °C |
| Retour GND (plan B.Cu) | toute la largeur de la carte (≥ 150 mm) | 30 A | < 1 °C |

Au courant que le XT30 autorise (15 A), tous ces tronçons restent sous 3 °C, le col de
BUS_P sous 15 °C.

Le courant passe de F.Cu à la borne par la pastille de la borne et sa couronne de 8 trous
métallisés de 0,5 mm ; le retour GND entre dans le plan B.Cu par les bornes « GND » des
sorties (traversantes) et ressort par la pastille « − » du XT30.

**Isolements.** HV_PWR (polygones 42 V) : 0,5 mm, comme `safety_power` (IPC-2221B B2
demande 0,6 mm sans revêtement ; vernis de tropicalisation recommandé sur la bande de
puissance). Petits signaux 42 V (HV_SIG) : 0,2 mm (IPC-2221B B4, conducteur externe
revêtu, 31–50 V : 0,13 mm). Logique : 0,2 mm.

## 5. Hacheur

Bloc de `safety_power` v2.1 inchangé (valeurs, références, LED sur `CH_DRV`). Simulation
rejouée le 23/11/2026 sur la copie [`sim/hacheur_v21.cir`](sim/hacheur_v21.cir) :

| | Résultat |
|---|---|
| Seuil ON | **42,95 V** |
| Seuil OFF | **42,29 V** |
| Sortie haute du comparateur | 11,21 V |
| `CHOP_ACT` (point de test) | 2,78 V |

Identique à `simulations.md` §1. Pire cas (0,1 %) : OFF 42,12 à 42,46 V, au-dessus du pack
plein (42,0 V). La résistance de 22 Ω / 100 W reste hors carte, sur la paire M4 J12
(BUS+ / CHOP_N), avec la roue libre `SS510C` (D8) sur la carte.

## 6. Précharge et contacteur

### 6.1 Précharge

Topologie de `safety_power` (S12) : `SUD50P10-43L` source sur BAT_P, grille tirée 12 V plus
bas par `MMBT5551` (GPIO27, 4,7 kΩ / 100 kΩ), zener `BZT52C12`, diode série `SS510C` vers
BUS.

**Résistance de 10 Ω sur la carte**, traversante : Yageo `SQP500JB-10R` (5 W, céramique).
Moins de fils, et l'énergie est faible. Simulation ([`sim/precharge.cir`](sim/precharge.cir),
bus de 10 mF supposé) :

| | Résultat |
|---|---|
| Bus à 95 % | 0,33 s |
| Courant crête | 4,13 A |
| Énergie dans la résistance | **8,6 J** par précharge (crête 171 W) |
| Bus en court-circuit, précharge laissée 0,59 s ([`sim/precharge_court.cir`](sim/precharge_court.cir)) | **101 J** dans la résistance, 0,43 J dans Q3 |

Une résistance céramique de 5 W supporte d'ordinaire 10 fois sa puissance pendant 5 s
(250 J) : 8,6 J est sans souci, un court-circuit franc du bus tient si le firmware coupe à
temps. ⚠️ Valeur de surcharge courte **à vérifier sur la fiche Yageo SQP**.

**Règles logicielles (obligatoires) :**

1. Précharger avec `/SAFE` bas (freins serrés).
2. Fermer le contacteur seulement quand **VBUS ≥ VBAT − 1 V** (`simulations.md` §2 : au-delà
   de 3 à 4 V d'écart, le pic de fermeture soude les contacts).
3. **Abandonner la précharge si VBUS < 50 % de VBAT après 0,5 s, ou si VBUS ≥ VBAT − 1 V
   n'est pas atteint en 1,5 s** (bus en court-circuit ou variateur défaillant) : la
   résistance reçoit alors au plus ≈ 90 J.
4. Couper `PRECH_EN` une fois le contacteur fermé.
5. Contacteur collé : contacteur commandé ouvert mais VBUS qui suit VBAT (sans précharge)
   → défaut, ne pas réarmer.

### 6.2 Bobine du contacteur

`COIL_EN` (GPIO32) ET `LATCH_Q` → `SN74AHCT1G08` (5 V) → 100 Ω → grille de l'`IRL540N` (Q10).
La bobine se branche sur J13 (COIL_P, COIL_N), la diode `S1M` (D21) est aux bornes de la
bobine sur la carte. Le contact NF CH2 de l'arrêt d'urgence (J11) est entre la sortie du
sélecteur (COIL_SUP) et COIL_P : appuyer sur le champignon coupe la bobine sans logiciel.
JP1 : cavalier 1-2 = 12 V AUX, 2-3 = BAT (après le fusible hôtel de 5 A). Courant de bobine
jusqu'à 1 A dans les deux cas (Q10 : 53 mΩ, 0,05 W).

⚠️ Le contact CH2 coupe le courant de bobine sous 12 à 42 V DC : le pouvoir de coupure DC
du champignon est à vérifier.

## 7. Tables des GPIO

Règles : jamais GPIO12 ; GPIO6–11 (flash) jamais ; GPIO0, 2, 5, 15 (strapping) seulement
pour des signaux dont l'état au démarrage est le bon ; 34–39 en entrée seulement ;
GPIO16/17 non utilisés (P3, variante PSRAM) ; GPIO1/3 = UART0 du pont USB, laissés libres.

### 7.1 SAFETY (U10)

| GPIO | Broche DevKitC | Signal | Sens | Remarque |
|---|---|---|---|---|
| 36 | J2-3 | `SAFE_N_IN_S` | entrée | /SAFE à travers 1 kΩ |
| 39 | J2-4 | `VBAT_ADC` | ADC1_CH3 | 243 k / 10 k |
| 34 | J2-5 | `VBUS_ADC` | ADC1_CH6 | 243 k / 10 k |
| 35 | J2-6 | `BMS_RX` | entrée (UART2 RX) | 1 kΩ + BAT54S + 10 kΩ au 3V3 |
| 32 | J2-7 | `COIL_EN` | sortie | 100 kΩ vers GND |
| 33 | J2-8 | `IMU_RST` | sortie | `board_config.h` |
| 25 | J2-9 | `IMU_INT` | entrée | `board_config.h` (pull-up interne) |
| 26 | J2-10 | `IMU_PS0` | sortie | `board_config.h`, jamais en dur |
| 27 | J2-11 | `PRECH_EN` | sortie | base 4,7 kΩ / 100 kΩ : flottant = précharge coupée |
| 14 | J2-12 | `BMS_TX` | sortie (UART2 TX) | émet un PWM au démarrage : trame invalide pour le BMS, sans effet |
| 12 | J2-13 | — | — | **jamais** |
| 13 | J2-15 | `SAFE_HOLD` | sortie | 10 kΩ au 3V3 : démarrage/absence = /SAFE bas |
| 23 | J3-2 | `IMU_MOSI` | sortie | `board_config.h` |
| 22 | J3-3 | `IMU_CS` | sortie | `board_config.h` |
| 1, 3 | J3-4, J3-5 | UART0 | — | pont USB, non câblé sur la carte |
| 21 | J3-6 | `SAFE_REARM` | sortie | CLK du 74LVC1G74, 100 kΩ vers GND |
| 19 | J3-8 | `IMU_MISO` | entrée | `board_config.h` |
| 18 | J3-9 | `IMU_SCK` | sortie | `board_config.h` |
| 5 | J3-10 | `CAN_TX` | sortie | strapping : 10 kΩ au 3V3 (haut au démarrage) |
| 17, 16 | J3-11, J3-12 | — | — | réservées (P3) |
| 4 | J3-13 | `CAN_RX` | entrée | |
| 0 | J3-14 | `I2C_SCL` | E/S | strapping : 2,2 kΩ au 3V3 = haut au démarrage (démarrage normal) ; le circuit auto-reset de la DevKitC le tire bas pour flasher, sans dommage pour l'I²C |
| 2 | J3-15 | `WD_DONE` | sortie | strapping : 100 kΩ vers GND (bas = autorisé) |
| 15 | J3-16 | `I2C_SDA` | E/S | strapping MTDO : 2,2 kΩ au 3V3 = haut (valeur par défaut) |

**Aucune broche libre.** Le `TCA9555` n'est pas nécessaire, au prix de trois sacrifices :
pas de lecture de `CHOP_ACT` (point de test), pas de décharge active, pas de coupure du
12 V PC. I²C : un seul esclave, l'`INA228` à 0x40.

### 7.2 MOTION_AVANT (U20) et MOTION_ARRIERE (U30) — table identique

Variateur 1 = gauche (AV_G sur AVANT, AR_G sur ARRIÈRE) ; variateur 2 = droite.

| GPIO | Broche DevKitC | Signal | Sens | Remarque |
|---|---|---|---|---|
| 36 | J2-3 | `HALL1_A` | entrée | sortie push-pull du SN74LVC3G17 (pas de pull-up nécessaire) |
| 39 | J2-4 | `HALL1_B` | entrée | |
| 34 | J2-5 | `HALL1_C` | entrée | |
| 35 | J2-6 | `HALL2_A` | entrée | |
| 32 | J2-7 | `HALL2_B` | entrée | |
| 33 | J2-8 | `HALL2_C` | entrée | |
| 25 | J2-9 | `DAC1` → VR variateur 1 | DAC | |
| 26 | J2-10 | `DAC2` → VR variateur 2 | DAC | |
| 27 | J2-11 | `DIR1` | sortie | 100 kΩ vers GND |
| 14 | J2-12 | `DIR2` | sortie | 100 kΩ ; PWM au démarrage : frein serré à ce moment-là (BRAKE_REL bas), sans effet |
| 12 | J2-13 | — | — | **jamais** |
| 13 | J2-15 | `STOP1` | sortie | 100 kΩ |
| 23 | J3-2 | `STOP2` | sortie | 100 kΩ |
| 22 | J3-3 | `BRAKE_REL` | sortie | 100 kΩ vers GND : reset = frein serré |
| 21 | J3-6 | — | libre | |
| 19 | J3-8 | `SAFE_N_IN` | entrée | /SAFE à travers 47 kΩ |
| 18 | J3-9 | — | libre | |
| 5 | J3-10 | `CAN_TX` | sortie | strapping : 10 kΩ au 3V3 |
| 4 | J3-13 | `CAN_RX` | entrée | |
| 0, 2, 15 | J3-14…16 | — | libres | strapping, laissées en l'air |
| 16, 17 | J3-11, J3-12 | — | réservées | P3 |

Deux broches libres par MOTION (18, 21).

## 8. Budget des rails

| Rail | Charges | Courant | Source et marge |
|---|---|---|---|
| 5 V | 3 ESP32 (Wi-Fi coupé ≈ 80 mA, pointe ≈ 240 mA chacun), 3 TCAN1042 (≤ 70 mA dominant), 2 TLV9062, AHCT, LED, 5V_BRAKE (4 × 2,3 mA + recharge du réservoir) | ≈ 0,5 A typique, **≈ 1,0 A pointe** | `TPS54360B` conçu pour 3,5 A |
| 3V3 de chaque DevKitC | ESP32 + ≤ 30 mA ajoutés (SAFETY : IMU ≈ 15 mA, INA228, VIO, pull-up `/SAFE` 3,3 mA, logique) | ≤ 0,3 A | régulateur de la DevKitC (≈ 0,8–1 A) |
| 12 V AUX | bobine (≤ 1 A si 12 V), ventilateur (≈ 0,2 A) | ≤ 1,3 A | `TPS54360B` conçu pour 2,5 A |
| 12 V PC | Youyeetoo X1 | ≤ 2,5 A | `URB4812YMD-30WR3` 30 W |
| Capteurs Hall | — | 0 sur la carte | alimentés par le 5 V de chaque variateur (passage) |
| HOTEL_IN (42 V) | 5 V (≈ 6 W), 12 V AUX (≈ 18 W), 12 V PC (≈ 34 W), rendements 85–88 % | **≈ 1,4 A à 42 V, ≈ 1,9 A à 30 V** | fusible 5 A temporisé |

## 9. Ce qui a été abandonné

| Élément de v2 | Pourquoi |
|---|---|
| Contacteur statique (`TPS48100`, 2 × `IPB017N10N5LF`) | Décision de William : contacteur mécanique externe |
| 4 `INA228` de branche + shunts 2 mΩ | Coût ; le fusible fondu se voit au comportement du moteur. Un seul `INA228` sur le bus |
| Isolation du BMS (`ADuM1201`, `B0503S`) | Masse commune décidée |
| `ACS758` et comparateur `LM2903` | La surintensité matérielle reste aux fusibles ; le courant est lu par l'INA228 |
| Carte `safety_bus_distribution` | CAN et `/SAFE` sont des pistes sur la carte unique |
| `ADS1115` | VBAT/VBUS sur l'ADC de l'ESP32 ; plus de NTC ni de straps à lire |
| NTC des variateurs, straps de rôle, révision matérielle | Chaque ESP32 a une place fixe |
| `TCA9555` | Les GPIO de SAFETY suffisent (§7.1) |
| `MCP4728` | DAC interne de l'ESP32 (M17) |
| eFuses `TPS2595x` | 220 Ω par sortie 5V_BRAKE (M33) ; plus de dorsale 5 V à protéger |
| `TPL5010` des MOTION | M22 |
| Selfs de mode commun CAN, `LM66100` | Bus sur la carte ; diode `B5819W` (M15) |
| WS2812B, sonde de température J21, tachymètres des ventilateurs, coupure du 12 V PC | Plus de GPIO ; ventilateur toujours alimenté |
| Micro-Fit 3.0 | JST XH (M31) |

## 10. Fabrication PCBWay et coût estimé

### 10.1 Ce que PCBWay reçoit (`fab/`, produit par `fab.sh`)

| Fichier | Contenu |
|---|---|
| `mainboard_gerbers.zip` | Gerber 2 couches (F/B cuivre, masque, sérigraphie, pâte, contour) + perçage Excellon |
| `bom_pcbway.csv` | Designator, Quantity, Manufacturer, MPN, Description, Package, **Type (SMD/THT)**, **Placed by (PCBWay / hand)**, LCSC (référence) |
| `centroid_pcbway.csv` | position des **CMS seulement** (mm, face dessus) |
| `schematic.pdf`, `assembly_top.pdf` | schéma, plan d'assemblage (repères sur la couche Fab) |
| `render_top.png`, `render_bottom.png` | rendus 3D |

Paramètres de commande : 2 couches, FR-4 TG150, 1,6 mm, **cuivre 2 oz extérieur**, vernis
vert, sérigraphie blanche, HASL sans plomb, 180 × 150 mm ; quantité **5** (le minimum PCBWay),
**assemblage CMS d'une seule carte** (ou deux) ; les autres restent nues.

**PCBWay pose : 273 CMS (719 pastilles). William soude : 39 pièces
traversantes** (XT30, bornes à vis M5/M4 = trous seulement, 4 porte-fusibles, 2 × IRL540N,
résistance de précharge, module 12 V, condensateur 2200 µF, 6 supports 1×19, support IMU,
17 connecteurs XH, bornier 12 V PC, cavalier de bobine). 114 (dont 1 ligne DNP, R67) lignes de BOM.

### 10.2 Coût estimé — **estimations, pas un devis**

Je n'ai pas de devis PCBWay ni leurs grilles de prix à jour : les chiffres ci-dessous sont
des ordres de grandeur tirés des prix habituels des fabricants chinois (et des tarifs
publiés de JLCPCB pour l'assemblage : 25 $ de mise en route, ≈ 8 $ de pochoir, ≈ 0,0016 $
par joint). **Faire un devis en ligne avec les fichiers de `fab/` avant toute décision.**

| Poste | Estimation |
|---|---|
| PCB 5 ex., 180 × 150 mm, 2 couches, **2 oz** | 40 à 80 € (le 2 oz double à peu près le prix du nu) |
| Assemblage CMS d'1 carte (mise en route, pochoir, ≈ 720 joints) | 35 à 90 € |
| Pièces CMS pour 1 carte (dont 2 × TPS54360B, INA228, TPS7A4001, 3 × TCAN1042, 0,1 %…) | 35 à 55 € (minimums d'achat et pertes compris) |
| Port DHL vers la France | 20 à 35 € |
| **Sous-total PCBWay** | **≈ 130 à 260 €** |
| Pièces traversantes achetées par William (module URB 30 W ≈ 25–35 €, fusibles et porte-fusibles ≈ 12 €, supports, connecteurs, IRL540N, etc.) | ≈ 50 à 70 € |
| 3 ESP32-DevKitC V4 (si non possédés) | ≈ 30 € |

**Verdict : le budget de 60 € ne couvre pas la carte assemblée.** Même en ne comptant que
la commande PCBWay, on est **2 à 4 fois au-dessus** (≈ 70 à 200 € de trop). Si le
parrainage de PCBWay couvre la fabrication et l'assemblage, les 60 € peuvent suffire pour
une partie des pièces traversantes.

**Ce qu'on peut couper, du plus rentable au moins rentable :**

1. **Ne faire assembler qu'une carte** sur les 5 (déjà prévu).
2. **Cuivre 1 oz** au lieu de 2 oz : −15 à −40 € estimés. Avec le XT30 limité à 15 A, les
   bandes de 13 mm et plus restent sous 10 °C à 15 A en 1 oz (§4) ; on perd la tenue de
   30 A continus que demande le cahier. À décider avec la question n° 1.
3. **Sortir le module 12 V PC de la commande** (le X1 sur une alimentation 12 V séparée,
   achetée plus tard) : −25 à −35 € de pièces traversantes ; l'empreinte reste sur la carte.
4. **Supports génériques** au lieu de Mill-Max (≈ 0,5 € au lieu de 3–5 € pièce) : −15 à
   −25 €. Vérifier qu'ils acceptent les broches carrées de 0,64 mm de la DevKitC.
5. Réduire la carte : la surface est fixée par les trois modules et la bande de puissance ;
   gagner 10 % de surface ne change le prix du nu que de quelques euros.
6. Assemblage « économique » (si PCBWay le propose) plutôt que standard.

Ce qu'il **ne faut pas** couper : le hacheur, la précharge, les fusibles 58 V, la TVS,
l'INA228 (limite du XT30) et le verrou du watchdog.


## 11. Ce qui n'est pas vérifié

- **P1** : entraxe des rangées de la DevKitC (25,40 mm supposé). Une erreur rend les trois
  emplacements inutilisables.
- Les valeurs du XT30 (15 A / 30 A) viennent des distributeurs, pas de la fiche Amass.
- Polarité de l'empreinte XT30 (pastille 2 = « + ») : sérigraphie KiCad, à comparer à la
  pièce.
- Surcharge courte du `SQP500JB-10R` (250 J supposés) ; tenue de la céramique aux
  précharges répétées.
- Pouvoir de coupure DC du contact NF de l'arrêt d'urgence sur la bobine.
- Calcul IPC-2152 approché (§4) ; aucune mesure thermique.
- Compensation des deux `TPS54360B` (méthode simplifiée de la datasheet, comme v2) et
  routage des régulateurs par l'autorouteur : **à reprendre à la main** (boucle d'entrée,
  nœud SW).
- Stock et prix PCBWay de chaque pièce : les LCSC indiqués sont des références, PCBWay
  achète sur MPN. `SN74LVC3G17DCTR`, `SN74LVC1G74DCTR`, `SN74AHCT1G08DBVR` : pas de
  référence LCSC vérifiée.
- Empreinte du module `URB4812YMD-30WR3` (reprise de v2, relue sur la datasheet mais pas
  sur pièce) et stock.
- Hall : niveau et bruit réels (M7, HALL_OC) non mesurés ; le passage du 5 V du variateur
  est repris de v2.
- Le DAC de l'ESP32 : linéarité et décalage réels à mesurer ; le firmware devra
  calibrer.
- Routage autorouté : lisible mais pas soigné ; relecture des pistes 42 V et du
  placement sous les modules.

## 12. Questions ouvertes pour William

1. **XT30 : 15 A continus.** Accepter de limiter les moteurs à ≈ 13 A au total par le
   firmware (§2) ? Sinon, la seule voie est une révision de carte avec un XT60.
2. **Tension de bobine du contacteur** (12 V, 24 V, 36/48 V ?) et son courant. Selon la
   réponse : cavalier JP1 sur 12 V ou sur BAT. Une bobine 24 V n'est pas prévue.
3. **Pouvoir de coupure** du contact NF de l'arrêt d'urgence en courant continu, et
   présence de deux contacts NF (CH1 pour `/SAFE`, CH2 pour la bobine).
4. **Niveau logique du BMS** (PACK_ID / M3) : 3,3 V ou 5 V ? Pour le 5 V, souder R67.
5. **P1** : mesurer l'entraxe des rangées de la DevKitC, et **P3** (PSRAM).
6. Le CANable Pro : activer sa terminaison (la carte n'en porte qu'une).
7. Faut-il accélérer la retombée du contacteur (diode + zener au lieu de la diode seule) ?
8. Accepter les coupes proposées au §10 si le devis dépasse le budget.

## 13. Propositions de modification de l'ICD

Je ne modifie pas `hardware/icd.yaml`. Propositions pour une v1.4 :

- Nouvelle carte `mainboard` remplaçant `safety_power`, `motor_interface` et
  `safety_bus_distribution` pour le premier montage.
- Entrée batterie : **XT30PW-M** (au lieu des goujons M5), limite 15 A continus documentée.
- Contacteur : **mécanique externe**, bornes M5 « VERS CONTACTEUR » / « RETOUR
  CONTACTEUR » ; commande de bobine côté bas, sélecteur 12 V / BAT ; NF de l'arrêt
  d'urgence en série avec la bobine.
- Masse : **une seule masse** (négatif batterie). `GND_MOT_x`, `GND_LOGIC`, `BUS_N`,
  `GND_BMS` deviennent `GND` ; le point étoile D4 est remplacé par la pastille « − » du
  XT30. `GND_COMPUTE` reste isolé (12 V PC).
- Connecteur de commande variateur : **JST XH 6 broches, 1 VR, 2 DIR, 3 EL, 4 STOP, 5 GND,
  6 5V_BRAKE** ; plus de NTC.
- Connecteurs Hall : JST XH 5 broches, 1 5V (du variateur), 2 GND, 3 HA, 4 HB, 5 HC.
- `5V_BRAKE` : 220 Ω par sortie au lieu des eFuses ; réservoir 2200 µF conservé.
- VR : DAC interne de l'ESP32 + TLV9062 gain 1,68 ; le `MCP4728` disparaît.
- `gpio_allocation` : tables du §7 pour SAFETY, MOTION_AVANT, MOTION_ARRIERE.
- IMU : connecteur 1×10 au pas de 2,54 mm (ordre du module GY-BNO08x) au lieu du JST GH 8.
- BMS : JST GH 4 non isolé, masse commune, option 5 V (R67).
- Limite de courant logicielle du bus (13 A continus, 25 A / 2 s) à la charge de SAFETY.
- Watchdog : matériel sur SAFETY seulement ; MOTION surveillés par le battement CAN.
