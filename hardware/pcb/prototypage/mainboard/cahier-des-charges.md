# Cahier des charges — `mainboard` (carte unique, v1.0-draft)

> **v1.0-draft — ne pas fabriquer avant P1, coil voltage, BMS level, and a review by an
> electronics engineer.**

Ce document fixe ce que la carte doit faire. Les choix techniques et leurs raisons sont
dans [`decisions.md`](decisions.md).

## 1. Rôle

Une seule carte remplace les trois cartes v2 (`safety_power`, `motor_interface` ×2 et
`safety_bus_distribution`) pour un premier montage bon marché, sponsorisé par PCBWay
(budget 60 €). On commande le **minimum de cartes**.

Elle porte :

- l'entrée batterie ;
- la distribution de puissance des moteurs ;
- les rails hôtel ;
- les trois ESP32-DevKitC V4 : SAFETY, MOTION_AVANT, MOTION_ARRIERE ;
- la chaîne de sécurité ;
- le connecteur de l'IMU ;
- le connecteur de données du BMS.

## 2. Priorités, dans l'ordre

1. Sécurité (points obligatoires du §5).
2. Le moins de fils volants possible : tout ce qui peut être une piste est une piste.
3. Le moins de CMS possible et le coût PCBWay le plus bas. PCBWay ne pose que les CMS ;
   William soude à la main tous les traversants (connecteurs, supports, modules,
   porte-fusibles, gros condensateurs, bornes).
4. La plus petite carte.

## 3. Décisions de William (ne pas rouvrir)

### 3.1 Contacteur et chemin de puissance

- **Pas de contacteur statique sur la carte.** William possède un disjoncteur et un
  contacteur mécanique externes.
- La batterie se branche sur la carte.
- BAT+ sort sur une borne forte « VERS CONTACTEUR », traverse le contacteur externe et
  revient sur une seconde borne forte « RETOUR CONTACTEUR » (= BUS+).
- BUS+ alimente les 4 variateurs ZS-X11H depuis la carte, par 4 sorties fusées à
  2 pôles (BUS+ / GND).
- Le négatif n'est jamais commuté : le négatif batterie est l'unique masse de la carte,
  en plans sur toute la surface. Le point de retour est au connecteur batterie.
- **Connecteur batterie : XT30 pour CI (type XT30PW)**, décision de William du
  23 novembre 2026. ⚠️ Un XT30 est donné pour 15 A en continu (30 A en pointe) alors
  que les 4 moteurs peuvent tirer ≈ 30 A : voir `decisions.md` §2.
- Le reste du chemin (cuivre, bornes, fusibles) est dimensionné pour **30 A continus**,
  de sorte que seul le connecteur limite. Cuivre calculé selon IPC-2152, échauffement
  indiqué. 1 oz ou 2 oz justifié par le coût ; 2 couches de préférence.

### 3.2 ESP32 et CAN

- Les 3 ESP32-DevKitC V4 s'enfichent sur la carte, sur 2 supports femelles 1×19 chacun,
  rangées à 25,40 mm (**P1 à confirmer**).
- CAN entre les 3 ESP32 par pistes : 3 × `TCAN1042HVDR` (VIO = 3V3 de chaque ESP32,
  VCC = 5 V), terminaison 120 Ω sur la carte, un petit connecteur (CANH, CANL, GND)
  vers l'adaptateur USB-CAN du PC (CANable Pro 1.1, terminaison commutable).

### 3.3 Commande des moteurs

Un ESP32 MOTION par paire de variateurs. Blocs repris de `motor_interface` v2 :

- passage Hall connecteur moteur → connecteur variateur, avec prélèvement :
  pull-up 2,2 kΩ, 2,2 kΩ + 10 nF, `BAT54S`, `SN74LVC3G17` → GPIO ;
- DIR et STOP par `AO3400A` en drain ouvert ;
- EL par `SN74LVC1G08` (GPIO ET /SAFE) pilotant un `AO3400A`, pull-down 100 kΩ sur les
  grilles ;
- VR 0–5 V, solution la plus simple qui soit correcte (DAC interne + `TLV9062` envisagé) ;
- ICD v1.3 `brake_chain` respectée : le pull-up 2,2 kΩ de EL vers 5V_BRAKE reste sur le
  faisceau côté variateur ; 5V_BRAKE est fourni sur le connecteur de commande du
  variateur ; 5V_BRAKE a un réservoir de 2200 µF alimenté par diode (D5).

### 3.4 IMU

BNO085 sur module (type GY-BNO08x d'AliExpress), connecteur 10 broches au pas de
2,54 mm, 1×10, ordre exact du module : VCC-3V3, GND, SCL/SCK/RX, SDA/MISO/TX,
ADDR/MOSI, CS, INT, RST, PS1, PS0. Câblé à l'ESP32 SAFETY exactement comme
`firmware/esp32_safety/main/board_config.h` : SCK GPIO18, MISO GPIO19, MOSI GPIO23,
CS GPIO22, INT GPIO25, RST GPIO33, PS0 GPIO26 (piloté, jamais câblé en dur). PS1 au
3V3 de la carte, VCC depuis la broche 3V3 de l'ESP32 SAFETY. Ces broches sont
éprouvées sur le banc : on n'y touche pas.

### 3.5 BMS

Connecteur de données pour le pack Xiaomi M365 Pro : JST, comme J2 de `safety_power`
(BMS_R, BMS_T, GND, NC). Masse = négatif batterie commun : l'isolation
ADuM1201/B0503S disparaît. Résistances série et écrêtage près du connecteur. Niveau
logique inconnu (PACK_ID / M3 ouverts) : conception 3,3 V avec une option tolérante
5 V, signalée.

## 4. Rails (tous en amont du contacteur, depuis BAT, toujours présents)

| Rail | Charges | Exigence |
|---|---|---|
| 5 V | 3 ESP32 (broches 5V), transceivers CAN, capteurs Hall, logique, 5V_BRAKE | ≈ 1,5–2 A ; module traversant ≥ 60 V vérifié, sinon `TPS54360B` de `safety_power` |
| 12 V PC (Youyeetoo X1) | calculateur | isolé ; `URB4812YMD-30WR3` ou équivalent vérifié ; module traversant ; bornier de sortie |
| 12 V AUX | ventilateurs | seulement s'il est presque gratuit |
| 3V3 | — | régulateur de chaque DevKitC ; pas de régulateur 3V3 sauf besoin |

## 5. Points de sécurité obligatoires

- **Hacheur de freinage (C-S2)** analogique, alimenté par le bus, sur BUS+ après le
  contacteur. Repris exactement de `safety_power` v2.1 : ON 43,0 V / OFF 42,3 V ; LED sur
  la sortie du pilote `CH_DRV` ; diviseur R23/R24 49,9 kΩ 0,1 %, R25 6,19 kΩ 0,1 %,
  R26 0 Ω, R27 1,69 MΩ. Résistance 22 Ω / 100 W hors carte, sur bornier. MOSFET : tout
  100 V D2PAK/TO-220 de R_DS(on) suffisant.
- **Précharge avant fermeture du contacteur externe** (sinon soudure des contacts,
  AMDEC n° 7) : précharge de `safety_power` (FET P `SUD50P10-43L` + `MMBT5551` + zener +
  diode série), pilotée par l'ESP32 SAFETY, entre BAT+ et BUS+. Résistance 10 Ω sur la
  carte (traversante) ou hors carte, au choix justifié. Règle logicielle : fermer le
  contacteur seulement quand VBUS ≥ VBAT − 1 V.
- **Commande de bobine du contacteur** : MOSFET N côté bas depuis l'ESP32 SAFETY, diode
  de roue libre ; la boucle NF de l'arrêt d'urgence est en série avec la bobine.
  **Tension de bobine inconnue** : sélecteur 12 V / BAT, jusqu'à 1 A, signalé.
- **/SAFE** : connecteur de boucle d'arrêt d'urgence, pull-up unique 1 kΩ, pull-down
  comme `safety_power` ; l'ESP32 SAFETY tient /SAFE par un MOSFET ; les 3 ESP32 lisent
  /SAFE ; /SAFE conditionne EL sur les deux paires par les portes ET. Verrou du watchdog
  conservé (`TPL5010` → `74LVC1G74` → /SAFE, D7). Watchdog propre aux MOTION ou
  surveillance par le battement CAN de SAFETY : à trancher et justifier.
- **Fusibles ≥ 58 V DC côté 42 V (C-S3)** : 4 branches en Littelfuse MINI 58V dans
  porte-fusibles Keystone 3568 (sauf moins cher à 58 V DC) ; petit fusible ou eFuse pour
  les rails hôtel.
- **Mesures pour l'ESP32 SAFETY** : VBAT (amont contacteur) et VBUS (aval) par diviseurs
  sur ADC1 (GPIO34–39) ; courant du bus par un `INA228` + shunt si le budget le permet.
- **TVS d'entrée `SMCJ48CA` bidirectionnelle**.

## 6. Abandonnés (à dire dans `decisions.md`)

Contacteur statique (`TPS48100`), 4 `INA228` de branche, isolation du BMS, `ACS758`,
carte `safety_bus_distribution` séparée, `ADS1115`, NTC moteur et straps de rôle
(chaque ESP32 a une place fixe), `TCA9555` si les GPIO de SAFETY suffisent.

## 7. GPIO

Table complète pour chacun des 3 ESP32 : jamais GPIO12 ; respect des broches de
strapping ; GPIO16/17 seulement sous condition (P3, variante PSRAM) ; entrées seules sur
34–39.

## 8. Méthode et livrables

Même méthode que les autres cartes : un `scripts/build.py` qui décrit le circuit une
fois et produit schéma et carte (UUID déterministes) ; cuivre de puissance par script,
signaux par Freerouting puis `patchroute` ; `build.sh`, `fab.sh`. Objectifs : ERC 0,
DRC 0 avec `--schematic-parity --severity-all`, 0 non connecté.

Sorties PCBWay dans `fab/` : Gerber + perçage (zip), BOM PCBWay (Designator, Quantity,
Manufacturer, MPN, Description, Package, Type SMD/THT), fichier de placement (CMS
seulement), schéma PDF, plan d'assemblage, rendus dessus et dessous. Estimation de coût
honnête comparée aux 60 €.
