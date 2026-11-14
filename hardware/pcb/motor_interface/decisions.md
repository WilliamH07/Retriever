# `motor_interface` v2.0-draft — décisions de conception

**Date** : 13 novembre 2026
**Statut** : **v2.0-draft — ne pas fabriquer avant M7, HALL_OC, P1, P2, P3.**
Schéma et routage générés par [`scripts/build.py`](scripts/build.py), ERC et DRC propres
(voir [`README.md`](README.md)). William a délégué les choix ; chacun est justifié ici
pour pouvoir être contesté.

Sources : [`cahier-des-charges.md`](cahier-des-charges.md),
[`10-spec-motor-interface.md`](../../../docs/architecture/10-spec-motor-interface.md),
[`11-corrections-v1.2.md`](../../../docs/architecture/11-corrections-v1.2.md) (C2, C5, C6,
C7, C14, C16), [`09-validation-composants.md`](../../../docs/architecture/09-validation-composants.md),
`hardware/icd.yaml`, décisions D2–D9 de [`../conception-v2.md`](../conception-v2.md) §4 bis,
datasheets citées. Disponibilité LCSC relevée le 13 novembre 2026 par recherche ;
**à revérifier la semaine de la commande**.

## Ce que fait la carte, en une phrase

Elle porte un ESP32-DevKitC V4 (nœud MOTION) sur supports, laisse passer sans les toucher
les fils Hall de deux moteurs vers leurs variateurs ZS-X11H, en prélève une copie tamponnée
pour l'ESP32, commande chaque variateur (`VR`, `DIR`, `STOP`, `EL`), lit leurs NTC, et porte le
nœud CAN et l'entrée `/SAFE`.

## Décisions

### Alimentation et masses

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| M1 | Double source 5 V (J7 et dorsale) | **Dorsale seule** (broche 1 de J8/J9). **J7 supprimé**, pas même en option | Une seule source, pas de règle de priorité à écrire. La branche de `safety_bus_distribution` fournit déjà un 5 V limité à ≈ 0,95 A par eFuse ; la carte consomme < 0,35 A. Une deuxième entrée n'apporterait qu'un moyen de se tromper |
| M2 | Protection d'entrée | **P-MOSFET `AO3401A`** (anti-inversion) **+ TVS `SMAJ6.0A` + 10 µF + 100 nF + LED verte** | Même cellule que `safety_bus_distribution`. La TVS est après le MOSFET pour ne pas conduire en inverse. Pas d'OVLO : l'eFuse amont écrête à 5,7 V |
| M3 | Anti-retour USB | **`LM66100`** (C2869734) du 5 V carte vers la broche 5V du module | Le schéma Espressif de la DevKitC V4 montre une Schottky `BAT760` entre VBUS USB et la broche 5V : l'hôte USB est déjà protégé. Il manquait l'autre sens : sans `LM66100`, l'USB branché robot éteint alimenterait le transceiver CAN, l'ampli et la dorsale à travers la carte. `CE` à la masse = toujours actif |
| M4 | Origine du 3,3 V | **Régulateur de la DevKitC** (classe AMS1117, 1 A), pas de LDO sur la carte | La logique de la carte consomme < 20 mA (LED comprises). Un second régulateur aurait été mis en parallèle avec celui du module sur la broche 3V3 : interdit. Et c'est fail-safe : module retiré → plus de 3,3 V → porte ET sans alimentation → frein serré |
| M5 | Rails des circuits annexes | `TCAN1042` VCC et `TLV9062` sur le **5 V carte** (après anti-inversion, avant `LM66100`) ; tampons, porte ET, `MCP4728`, `ADS1115`, `TPL5010`, `VIO` sur le **3,3 V du module** | Le 5 V reste présent pour le bus quand le module est retiré ; tout ce qui dialogue avec l'ESP32 suit son 3,3 V |
| M6 | Masses (D4) | **Trois réseaux distincts** : `GND` (logique), `GND_MOT_A`, `GND_MOT_B`. **Aucune liaison sur la carte.** Plans séparés sur les quatre couches (bandes du haut et du bas) | D4 : `GND_MOT` est le `BUS_N` des variateurs et ne rejoint `GND_LOGIC` qu'au point étoile de `safety_power`. Séparer A et B évite en plus que le courant de traction d'un variateur revienne par le faisceau Hall de l'autre à travers la carte |
| M7 | Comment les signaux traversent les domaines | Le filtre RC et le clamp de chaque voie Hall sont **référencés à `GND_MOT_x`** (domaine de la source) ; le tampon lit le nœud filtré en haute impédance. Les MOSFET `DIR`/`STOP`/`EL` ont leur **source sur `GND`** logique | Côté Hall, le courant de front reste dans le domaine moteur. Côté commande, la tension grille-source est exactement le niveau logique : un rebond de `GND_MOT` ne peut pas rendre passant le MOSFET de frein. Pour `EL`, la boucle de courant (5V_BRAKE de `safety_power` → 2,2 k faisceau → MOSFET → `GND`) reste entièrement dans le domaine logique |
| M8 | Risque résiduel des masses | **Assumé et mesurable** : points de test `GMA`, `GMB` et `GND` | Le décalage `GND_MOT` – `GND` vaut la chute dans le câble `BUS_N` variateur → étoile : ≈ 0,05–0,2 V en continu à pleine charge, plus les pointes de commutation. Marge du tampon : niveau bas Hall ≈ 0,2 V contre `VT−` min 0,84 V → ≈ 0,4 V de marge. Sur la NTC : ≈ 5 °C d'erreur à 80 °C pour 0,1 V. **À mesurer à l'oscilloscope (M7)** |
| M9 | Banc sans `safety_power` | **R148 / R178, 0 Ω `GND_MOT_x`–`GND`, NON MONTÉES**, sérigraphiées `BANC SEUL` | Sur établi (M7, alimentation de labo) il n'y a pas d'étoile : sans liaison, le tampon lit des lignes flottantes. On soude le 0 Ω sur la carte de banc, on le retire avant le robot |

### Prélèvement Hall

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| M10 | Passage J1→J3, J2→J4 | **Pistes droites 0,8 mm sur F.Cu, broche k vers broche k, sans via, sans composant**, posées et verrouillées par le script avant l'autoroutage | Exigence dure de l'ICD. Connecteurs orientés broches vers le bas pour que les cinq conducteurs soient parallèles. Continuité vérifiable hors module (recette 1) |
| M11 | Pull-up 2,2 kΩ vers `+5V_MOT_x` | **Monté par défaut, une résistance par voie, retirable** (option de peuplement liée à HALL_OC) | Spec Z.3.2 : variateur débranché → lignes définies, constantes de temps bornées (22 µs descendant, 40 µs montant). Si HALL_OC montre des sorties push-pull, ne pas monter R101/R105/R109 et R151/R155/R159 |
| M12 | PPTC sur le piquage `+5V_MOT` (ICD v1.2) | **Supprimée** | (1) `+5V_MOT_A` et `+5V_MOT_B` sont deux réseaux séparés : un défaut sur l'un ne peut plus remonter vers l'autre variateur, ce que la PPTC devait empêcher. (2) La `MF-MSMF014` citée tient 140 mA (I10) et ne déclencherait jamais avant la limite du 78L05. (3) Tout ce qui touche `+5V_MOT` sur la carte passe par ≥ 2,2 kΩ ou par la cathode d'un clamp. **Aucun condensateur sur `+5V_MOT`** |
| M13 | Filtre et protection | **2,2 kΩ série + 10 nF / 100 V** (C43253) **+ `BAT54S`** (C47546) vers `+5V_MOT_x` / `GND_MOT_x` | Inchangé (C7). Le 10 nF est **en aval** de la 2,2 kΩ : un condensateur en court-circuit ne tue pas la ligne. Phase 37 V sur une ligne : 17 mA injectés, sous les 50 mA de `IIK`. τ 22 µs, coupure 7,2 kHz (corrigé en `conception-v2.md` §7) |
| M14 | Tampon | **2 × `SN74LVC3G17DCUR`** (C68245) à 3,3 V, un par moteur | `Ioff` garanti : passthrough intact module retiré ou hors tension. Non inverseur. **Interdits de substitution** : `74HC14`, `74HCT14`, `SN74LVC14A` (écrit au schéma) |
| M15 | LED d'activité Hall (spec Z.6) | **Supprimées** | Elles demandaient deux tampons de plus, six LED et un circuit d'inhibition. La recette « roue tournée à la main » se fait aux points de test `HxA/HxB/HxC` ou par la console série ; le firmware publie l'état Hall |

### Commande des variateurs

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| M16 | `MCP4728` : le bus I²C 3,3 V suffit-il à VDD = 5 V ? | **Non.** Datasheet DS22187E : `VIH` (SDA, SCL) = **0,7 × VDD**, soit 3,5 V à 5 V. → **`MCP4728` alimenté en 3,3 V**, référence **interne 2,048 V**, gain ×1 | Pas de translateur à ajouter. La référence interne rend la consigne indépendante de la précision du 3,3 V du module |
| M17 | Mise à l'échelle 0–5 V | **`TLV9062`** (C398355) en non-inverseur, **gain 2,5** (15 k / 10 k), alimenté en 5 V | 2,048 × 2,5 = 5,12 V, écrêté à ≈ 4,98 V par l'ampli : codes 0 à ≈ 3980 linéaires, ce qui suffit à la boucle PI. 15 k et 10 k sont des pièces basic |
| M18 | `VR` module retiré | **100 kΩ à la masse sur l'entrée + de l'ampli** ; 100 Ω série en sortie ; **10 kΩ à la masse au connecteur** | DAC non alimenté → entrée tenue à 0 → `VR` = 0. Le 10 kΩ définit `VR` si l'ampli est éteint ; il ne protège **pas** d'une rupture de fil côté variateur (voir ICD v1.3). EEPROM du `MCP4728` à programmer à 0 en production (inchangé) |
| M19 | Interrupteurs `DIR`, `STOP`, `EL` | **`AO3400A`** (C20917, **basic**, SOT-23) au lieu du `DMG1012T` (SOT-523) | `RDS(on)` garanti **48 mΩ à VGS = 2,5 V** (le `DMG1012T` : 0,5 Ω ; le `BSS138` : rien sous 4,5 V). `VGS(th)` max 1,45 V : 1,85 V de marge à 3,3 V. SOT-23 retouchable au fer, pièce basic donc sans surcoût d'assemblage. 30 V de `VDS` |
| M20 | Étage agnostique en polarité | **Sur `DIR` et `STOP` seulement** : `R_PU` 4,7 k vers `+5V_MOT_x`, `R_PD` 10 k vers `GND_MOT_x`, `R_DIRECT` 1 k GPIO → sortie, **tous non montés** | Le firmware inverse la polarité logique sans matériel. Les options couvrent les deux vrais cas : entrée sans pull-up interne (monter `R_PU`), ou entrée qui exige un niveau actif haut non inversé (retirer le MOSFET, monter `R_DIRECT` + `R_PD`). Pas d'inverseur SOT-23 (JP3 de la spec) : il ne servait qu'à l'état pendant le reset, sans enjeu puisque `VR` = 0 et frein serré à ce moment |
| M21 | `EL` | **Porte ET `SN74LVC1G08`** (C7666) **par roue** : `GPIO26` · `/SAFE` → grille de l'`AO3400A` qui tire `EL` bas. **Aucune option de peuplement sur `EL`. Pas de `5V_BRAKE` sur la carte** (D5) | Deux portes : une porte défaillante ne relâche qu'une roue. Le pull-up 2,2 k vers `5V_BRAKE` est sur le faisceau (D5) : carte débranchée → `EL` reste haut → frein serré |
| M22 | Pull-downs de grille | **100 kΩ sur chaque grille** (`DIR`, `STOP`, sortie de chaque porte ET) **et sur `GPIO26`** (R7) | Module retiré, ESP32 en reset (D7) ou porte non alimentée (`Ioff`, sortie flottante) : tous les MOSFET bloqués, frein serré |
| M23 | J5/J6 broche 7 | **NC** (D5) | Était `5V_BRAKE`. Ne pas la réaffecter : un ancien faisceau y amènerait encore du 5 V |
| M24 | Voyants « frein serré » | **Un troisième `SN74LVC3G17`** lit `EL_A`, `EL_B` (10 k série, entrée tolérante 5 V) et `/SAFE` ; LED rouges | Une LED directement sur `EL` chargerait le pull-up 2,2 k et fausserait le niveau. Un 1 MΩ vers 3,3 V sur l'entrée : faisceau débranché, le voyant affiche « serré », ce que fait réellement le variateur. Ce n'est pas une option sur `EL` : 1 µA dans le sens du frein |

### Mesures et identité

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| M25 | `ADS1115` | **Adresse 0x48** (ADDR à GND), alimenté en **3,3 V** ; AIN0 = NTC A, AIN1 = NTC B, AIN2 = rôle, AIN3 = révision | Pas de conflit avec le `MCP4728` (0x60 usine). ALERT/RDY non utilisé (aucun GPIO libre hors 16/17 conditionnels) |
| M26 | NTC 10 k, B = 3950 (hypothèse) | **3,3 kΩ vers 3,3 V**, NTC vers `GND_MOT_x` (broche 5/8 de J5/J6), **1 kΩ + 100 nF** avant l'ADC | 3,3 k centre la pente vers 60 °C : 2,48 V à 25 °C, 1,42 V à 60 °C, 0,92 V à 80 °C (≈ 21 mV/K), 0,58 V à 100 °C. Le 1 k limite le courant si un fil 5 V touche la ligne |
| M27 | Rôle AVANT / ARRIÈRE | Diviseur sur AIN2 avec **ponts de soudure** : SJ1 ouvert → 0 V = **AVANT** ; SJ1 fermé → 1,10 V (1/3) = **ARRIÈRE** ; SJ2 fermé → 3,3 V = **BANC** | Un cavalier peut tomber en vibration, un pont de soudure non. Encodage de l'ICD (0, 1/3, 2/3 réservé, Vref). Seuils firmware à 1/6, 1/2, 5/6 de 3,3 V |
| M28 | Révision matérielle | Diviseur fixe sur AIN3 : **10 k / 10 k → rapport 1/2 = v2.0** | Table : rapport n/8 du 3,3 V, n = 4 pour v2.0, les révisions suivantes changent la résistance basse. Publiée dans le heartbeat |

### Watchdog, CAN, `/SAFE`

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| M29 | `TPL5010` (D7) | **`RSTn` sur `EN`** de l'ESP32 ; `DELAY` = **6,8 kΩ → ≈ 2 s** (table 3 SNAS651A : 6,788 kΩ → 2 s) ; pull-up 100 k sur `EN` ; pull-down 100 k sur `DONE` | 2 s laisse le temps au démarrage (premier `DONE` avant la fin du premier intervalle) ; un ESP32 figé est redémarré en ≤ 4 s, et pendant ses 320 ms de reset `GPIO26` flotte → frein serré. Le chemin rapide reste le heartbeat CAN surveillé par SAFETY. La DevKitC a déjà 10 k + 0,1 µF sur `EN` ; le 100 k recommandé par TI ne change rien à ce RC |
| M30 | CAN | **`TCAN1042HVDR`** (C127869), `STB` à la masse, `VIO` 3,3 V, `NUP2105L` + self `ACT45B-510` ; **pas de terminaison** ; pull-up 10 k sur `GPIO5` (strapping) | Inchangé (C5). Symbole KiCad du `TJA1042T/3`, brochage identique (TXD, GND, VCC, RXD, VIO, CANL, CANH, STB) |
| M31 | Dorsale | **J8 et J9 en parallèle**, broche à broche ; `SHIELD` traversant, relié à rien sur la carte | Le bus traverse sans stub. Blindage relié d'un seul côté, côté X1 (ICD) |
| M32 | Entrée `/SAFE` | **47 kΩ série** puis **1 MΩ à la masse** et 100 pF sur le nœud local `SAFE_N_IN` | Nœud éteint : ≤ 53 µA rétro-injectés, chute < 0,05 V sur la ligne. Niveau haut local 3,00 × 1 M / 1,047 M = 2,87 V, au-dessus du `VIH` ESP32 (2,48 V) et du `VIH` de la porte ET (2,0 V). Carte débranchée : nœud tiré bas → frein serré. Filtre 4,7 µs, très en dessous des 10 ms exigés |

### Module, fabrication, sérigraphie

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| M33 | Brochage DevKitC V4 | **J2** (rangée haute) : 3V3, EN, IO36, IO39, IO34, IO35, IO32, IO33, IO25, IO26, IO27, IO14, IO12, GND, IO13, IO9, IO10, IO11, 5V. **J3** (rangée basse) : GND, IO23, IO22, IO1, IO3, IO21, GND/NC, IO19, IO18, IO5, IO17, IO16, IO4, IO0, IO2, IO15, IO8, IO7, IO6 | Lu sur le schéma Espressif `ESP32_DevKitc_V4` (6/12/2017) et le guide utilisateur. Broche 1 côté antenne. **J3-7** est `GND` dans le guide mais sans étiquette dans le schéma : laissée en l'air (inoffensif dans les deux cas). **P1 et P2 doivent le confirmer** |
| M34 | Affectation GPIO | **Celle de `gpio_allocation.motor_interface`**, sans changement. IO6–IO11, IO12, IO0, IO2, IO1, IO3, IO16, IO17 non connectées | Sérigraphie `NC - FLASH` sur les deux rangées |
| M35 | Supports | **Mill-Max `310-43-119-41-001000`** (Mouser), soudés à la main | Broches carrées 0,64 mm de la DevKitC : pas de série 315. Aucune équivalence vérifiée chez LCSC |
| M36 | Antenne | **Encoche de 9,5 × 18,8 mm** dans le bord droit, sous l'antenne du WROOM | Espressif : pas de carte sous l'antenne. Wi-Fi inutilisé, mais l'encoche ne coûte rien et garde la porte ouverte |
| M37 | Couches | **4 couches** (D9). L1 signaux, L2 masse, L3 3,3 V / 5 V, L4 signaux ; chaque couche découpée en domaines (`GND_MOT_A` en haut, `GND_MOT_B` en bas) | Plans posés **après** l'autoroutage (leçon de la première carte) ; L2 et L3 déclarées « power » pour que Freerouting n'y route pas |
| M38 | Format | **100 × 100 mm**, 4 trous M3, coins chanfreinés | Moteur A en haut, B en miroir en bas, module au centre-droit, dorsale à gauche. Reste dans le tarif JLCPCB 4 couches ≤ 100 × 100 |
| M39 | Connecteurs | Micro-Fit 3.0 verticaux : **43650-0615** (C505231) pour J1–J4, J8, J9 ; **43650-0815** pour J5/J6, **hors LCSC** (Mouser 538-43650-0815) | LCSC ne stocke pas le 8 positions vertical. Traversants soudés à la main de toute façon |
| M40 | Règles | piste 0,25 mm (signal), 0,4 mm (alimentations et masses), 0,3 mm (lignes Hall hors passage), 0,8 mm (passage Hall) ; isolation 0,15 mm ; via 0,7 / 0,3 mm | Dans les capacités JLCPCB 4 couches avec marge. 0,15 mm imposé par les boîtiers à pas de 0,5 mm |
| M41 | Points de test | Pastilles nues 1,5 mm, **nommées** en sérigraphie : `5V`, `3V3`, `GND`, `CANH`, `CANL`, `/SAFE`, `HAA HAB HAC HBA HBB HBC`, `5VMA 5VMB`, `GMA GMB`, `ELA ELB`, `VRA VRB` | Spec Z.6 : nommés, jamais numérotés |
| M42 | Repères | Sur la couche de fabrication | Comme la première carte : sur une carte dense ils tombent sur les pastilles |

## Table des modes de défaillance (vérifiée sur le schéma)

| Événement | Mécanisme sur cette carte | Résultat |
|---|---|---|
| Carte débranchée (J5/J6) | Pull-up 2,2 k sur le faisceau, alimenté par `5V_BRAKE` de `safety_power` | `EL` haut → **frein serré** |
| Module retiré | Plus de 3,3 V : portes ET sans alimentation, sortie flottante ; R141/R171 tirent les grilles ; R7 tire `GPIO26` | MOSFET bloqués → **frein serré** ; `VR` = 0 (R15/R18) |
| ESP32 en reset (`TPL5010`, D7) | `GPIO26` haute impédance, R7 100 k | **frein serré** |
| `/SAFE` bas ou câble coupé | Entrée B des portes ET basse (R6 1 MΩ définit le nœud si la dorsale est débranchée) | **frein serré** |
| Perte du 5 V dorsale | Module non alimenté → 3,3 V perdu | **frein serré** |
| ESP32 retiré, variateur en marche | Tampons Hall hors tension, `Ioff` | Passthrough Hall intact (exigence dure) |
| Phase 37 V sur une ligne Hall | 2,2 k série → 17 mA dans le clamp | Tampon protégé ; ligne Hall du variateur compromise (défaut externe) |

## Ce qui n'est pas vérifié

- **P1, P2** : entraxe 25,40 mm et ordre des broches du module réel. Tout le placement en
  dépend. **J3-7** (GND ou NC) à lever au multimètre.
- **M7, HALL_OC** : niveau, impédance et type des sorties Hall. Les pull-ups montés par
  défaut supposent un collecteur ouvert.
- **Décalage de masse** `GND_MOT` – `GND` en marche : seulement estimé (M8).
- **NTC** : présence, valeur et coefficient B réels sur les ZS-X11H ; B = 3950 supposé. La
  NTC est supposée flottante à deux fils, retour sur `GND_MOT`.
- **Polarités `DIR`, `STOP`, `EL`** (M4) : hypothèses de la spec, options de peuplement prévues.
- **Disponibilité et prix** : stocks relevés par recherche web, classes basic/extended
  vérifiées pour quelques pièces seulement ; `SN74LVC1G08DBVR`, `ADS1115`, `BAT54S` sont
  « extended ». **`43650-0815` et les supports Mill-Max ne sont pas chez LCSC.**
- **Rotations du fichier de placement** : non comparées à la bibliothèque JLCPCB ; vérifier
  l'aperçu de placement à la commande (SOT-23-5, SC-70-6, VSSOP-8, TSSOP-10).
- **Firmware** : intervalle du watchdog (2 s), seuils de rôle, code de la révision, EEPROM du
  `MCP4728` à 0 — à écrire dans `board_config.h` et la procédure de recette.
- **Aucune simulation** : filtre Hall, gain de l'ampli et diviseurs calculés à la main.
- **Rendu et routage automatiques** : relecture humaine dans KiCad nécessaire, notamment
  les retours de masse sous le module et la traversée des coupures de plan par les pistes
  de commande.

## Changements proposés pour l'ICD v1.3 (non appliqués : fichier hors périmètre de cette carte)

1. `boards.motor_interface.connectors.J7` : supprimer ; alimentation par la broche 1 de la dorsale uniquement.
2. `J5_J6.pins.7` : `NC` (D5) ; retirer `V5_BRAKE`. Remplacer `safety_warning` (relais NF) par la chaîne MOSFET + porte ET.
3. `J1_J2.passthrough_purity` : retirer la PPTC 30 mA du piquage ; `+5V_MOT` et `GND_MOT` deviennent `*_A` / `*_B`, séparés sur la carte.
4. Nouvelle entrée `grounds` : `GND`, `GND_MOT_A`, `GND_MOT_B` non reliés sur `motor_interface` ; 0 Ω de banc non monté.
5. `role_selection` (carte) : « ponts de soudure SJ1/SJ2 sur le diviseur ADS1115 AIN2 » au lieu de « straps ROLE0/ROLE1 ».
6. `brake_chain.power_source.reservoir` : 2200 µF sur `safety_power` (D5) ; `SAFE_N_spec.level_shift` et `consumed_by` : remplacer « relais NF » par « porte ET + MOSFET ».
7. `gpio_allocation.motor_interface` : notes `DMG1012T` → `AO3400A` ; `mcp4728_fullscale` → `MCP4728` en 3,3 V, référence interne 2,048 V, ampli ×2,5.
8. Ajouter le plan de l'`ADS1115` : 0x48, AIN0 NTC A, AIN1 NTC B, AIN2 rôle, AIN3 révision (½ = v2.0).
9. `J5_J6.pins.1` (`VR`) : le 10 kΩ à la masse doit aussi être **sur le faisceau, côté variateur** pour couvrir la rupture de fil ; celui de la carte ne couvre que l'ampli éteint.
10. `TPL5010` : `DELAY` 6,8 kΩ → 2 s, `RSTn` sur `EN`.
11. `SAFE_N_spec.per_board` : préciser la résistance série (47 kΩ) devant le 1 MΩ.
12. Module : noter l'ambiguïté de J3-7 (GND dans le guide, sans étiquette dans le schéma Espressif) à lever par P2.
