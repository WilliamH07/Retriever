# `safety_power` v2.0-draft — décisions de conception

> ⚠️ **v2.0-draft — NE PAS FABRIQUER avant M1, M2, M10, M12, PACK_ID, P1–P3 et relecture
> par un électronicien.** Cette carte commute 42 V / 30 A sur un pack lithium de 474 Wh.
> Un schéma qui passe l'ERC et le DRC n'est pas un schéma juste : la section
> [« Relecture experte obligatoire »](#relecture-experte-obligatoire) liste ce qu'un
> professionnel doit regarder avant toute commande.

**Date** : 13 novembre 2026
**Statut** : schéma et carte générés par [`scripts/build.py`](scripts/build.py).
**ERC 0, DRC 0 (avec `--schematic-parity --severity-all`), 0 connexion manquante, parité 0.**
210 × 160 mm, 4 couches, 344 symboles, BOM JLCPCB 111 lignes / 298 placements.
**Non fabriquée, non relue.**
William a délégué les choix ; chacun est justifié ici pour pouvoir être contesté.

Sources : [`cahier-des-charges.md`](cahier-des-charges.md), [`../conception-v2.md`](../conception-v2.md)
§4 bis (D2–D9, tranchées le 13/11), `hardware/icd.yaml`,
[`12-contacteur-statique.md`](../../../docs/architecture/12-contacteur-statique.md),
[`11-corrections-v1.2.md`](../../../docs/architecture/11-corrections-v1.2.md), datasheets citées.
Stocks relevés le 13 novembre 2026 par l'API de recherche JLCPCB/LCSC : **à revérifier la
semaine de la commande**.

## Ce que fait la carte, en une phrase

Elle reçoit la batterie sur deux goujons M5, la commute sur le bus des variateurs par un
contacteur statique tête-bêche après précharge, écrête la régénération par un hacheur
analogique, distribue quatre branches moteur fusées et mesurées, produit les rails hôtel
(5 V, 3,3 V, 12 V auxiliaire, 12 V calculateur isolé) **en amont** du contacteur, et porte
l'ESP32 SAFETY, le pull-up unique de `/SAFE`, le watchdog verrouillé et la mesure de courant
matérielle.

---

## 1. Pièce critique : `TPS4810-Q1`

| Point | Constat |
|---|---|
| Référence commandable | **`TPS48100QDGXRQ1`** (la famille s'appelle `TPS4810-Q1`, la pièce `TPS48100-Q1`) |
| Disponibilité | ✅ **JLCPCB/LCSC `C43131316`, 903 pièces en stock** (13/11/2026, à revérifier). Pièce « extended ». Elle peut donc être **assemblée par JLCPCB** ; il n'y a pas besoin de la fournir |
| Datasheet lue | TI SLUSEW1C (rév. juin 2026), téléchargée et extraite (pdftotext) |
| Deux commandes de grille indépendantes | ✅ `G1PU`/`G1PD` (Q1, 1,62 A source / 2 A puits) et `G2` (Q2, 1,69 A / 2 A), commandées par **`INP1` et `INP2` séparés** (table 4-1). C'est ce qui rend le diagnostic de collage possible |
| Brochage | ✅ boîtier DGX : **20 positions, broche 16 dépeuplée** (19 broches). Le doute de l'étude `12` §AA.8-1 (« 19 broches mais la numérotation va à 20 ») est levé. 1 EN/UVLO, 2 INP2, 3 INP1, 4 NC, 5 FLT, 6 GND, 7 CS_SEL, 8 ISCP, 9 TMR, 10 SCP_TEST, 11 G2, 12 BST, 13 SRC, 14 G1PD, 15 G1PU, 17 CS−, 18 CS+, 19 NC, 20 VS |
| Seuil de court-circuit | ✅ éq. 5 : `R_ISCP = (I_SC × R_SNS − 19 mV) / 2 µA`. Table 5.5 : 10,5 kΩ → 40 mV, 28 kΩ → 75 mV (58,8–91,8 mV : **±22 %**) |
| Temporisation | ✅ éq. 7 (réarmement auto) `C_TMR = I_TMR × t_SC / 1,1 V`, I_TMR = 80 µA ; éq. 9 (verrouillage par 100 kΩ sur TMR) `C_TMR = t_SC / (R_TMR × ln(1 / (1 − 1,1 / (R_TMR × 80 µA))))` |
| Empreinte | générée d'après le « land pattern example » DGX0019A : 20 × 0,3 × 1,45 mm, pas 0,5, rangées à 4,4 mm (`kicad/lib/sp.pretty/TI_DGX0019A_VSSOP-19`) |

La valeur de 470 nF proposée par la v1 donnait t_SC ≈ 6,5 ms : beaucoup trop lent pour un
court-circuit franc sur un pack de 400 à 1400 A. Elle n'est pas reprise.

---

## 2. Décisions

| # | Question | Choix | Pourquoi |
|---|---|---|---|
| S1 | MOSFET du contacteur | **2 × `IPB017N10N5LFATMA1`** (C3289286, 1321 en stock) au lieu de `IPB017N10N5ATMA1` | La version standard est à **0 pièce** chez JLCPCB (C3289290). La version LF (LinearFET) a le même boîtier, le même R_DS(on) de 1,7 mΩ et une SOA linéaire meilleure : remplaçant direct, en mieux |
| S2 | Shunt du contacteur | **1 mΩ `WSK25121L000FEA`** 4 fils (C4248455), partagé par le `TPS48100` (CS+/CS−) et l'`INA228` 0x40 | Un vrai shunt 4 bornes donne des prises Kelvin physiques. Un seul shunt dans le chemin principal au lieu de deux : 1 mΩ de moins, 0,4 W de moins à 20 A |
| S3 | Seuil de court-circuit matériel | **I_SC ≈ 99 A** (R_ISCP = 40,2 kΩ → V_SCP = 99 mV ; dispersion TI ≈ 80–120 A) | Au-dessus des démarrages simultanés des 4 moteurs (≤ 4 × 20 A), en dessous du courant de court-circuit du pack. La surcharge « raisonnable mais trop longue » reste au budget logiciel et au comparateur ACS758 (S16) |
| S4 | Temporisation et comportement sur défaut | **t_SC ≈ 100 µs, verrouillage** : C_TMR = 6,8 nF ∥ R_TMR = 100 kΩ (éq. 9 : 100 k × 0,148 × 6,8 nF = 101 µs) | Pas de réarmement automatique sur un court-circuit : l'ESP32 réarme en basculant `INP1`, après diagnostic. 100 µs filtre les appels capacitifs des variateurs déjà préchargés |
| S5 | UVLO du contrôleur | **25,3 V montant / 23,4 V descendant** (1 MΩ / 51 kΩ, V_UVLOR 1,23 V) | Sous la coupure BMS (~30 V) : ne coupe jamais avant le BMS, mais coupe sur une batterie effondrée |
| S6 | Résistances de grille | `R_on` 10 Ω (G1PU), **`Rg_off` 150 Ω** (G1PD → Q1), 150 Ω sur G2 (Q2, une seule broche) | Milieu de la fenêtre 100–220 Ω de l'étude `12` §AA.4. **À régler à l'oscilloscope** (Q_gd réel en courbe seulement) |
| S7 | Protection grille | 100 kΩ grille-source + zener 15 V (`BZT52C15`) sur chaque FET | Le 100 kΩ garantit le blocage sans pilote ; la zener borne V_GS sous les 20 V du MOSFET en cas de défaut de la pompe de charge |
| S8 | Condensateur de bootstrap | **1 µF / 25 V** | Éq. 13 : C_BST ≥ Q_g(total) / 1 V. Deux IPB017 (Q_g ≤ 2 × 218 nC) → ≥ 436 nF. Conséquence : la pompe (345 µA) met ~30 ms à charger C_BST au démarrage |
| S9 | TVS de l'interrupteur | **`SMCJ48CA` bidirectionnelle** drain-à-drain (C151287), et une seconde en entrée batterie | L'étude `12` donnait `SMCJ48A` (unidirectionnelle). **Corrigé** : sur une batterie inversée, une unidirectionnelle drain-à-drain conduit en direct et charge les condensateurs des variateurs en inverse. La bidirectionnelle (même V_C 77,4 V) ne conduit dans aucun sens à 42 V |
| S10 | Roue libre | `SS510C` (100 V / 5 A, C19229) de `BUS_N` vers `BUS_P` | Transitoire négatif du faisceau côté charge (étude `12` §AA.4) |
| S11 | Anti-inversion de polarité | **pas de `LTC4359`** : contacteur bloquant (TPS48100 tenu à −65 V, FET tête-bêche), TVS bidirectionnelles, diode série `SS510C` sur la précharge, **FET P `SUD50P10-43L` en diode idéale** sur l'alimentation hôtel | Le chemin 30 A est déjà bloquant en inverse par construction ; un `LTC4359` n'y ajouterait rien. Les deux chemins non bloquants (précharge, hôtel) ont chacun leur protection. Le FET P hôtel dissipe 0,45 W à 2,7 A au lieu de 2 W pour une Schottky |
| S12 | Précharge | FET P **`SUD50P10-43L`** (100 V, 43 mΩ, C41408040) source au `BAT_P`, grille tirée 12 V plus bas par un **NPN `MMBT5551`** (160 V) piloté par le GPIO27, puis diode série `SS510C`, puis résistance hors carte (J13) | Topologie de l'étude `12` §AA.1.4. Un NPN plutôt qu'un petit N-MOSFET : le `DMG1012T` ne tient que 20 V et le `2N7002` n'est pas garanti à 3,3 V (C6). Le NPN commute à coup sûr avec 4,7 kΩ de base |
| S13 | Diagnostic de collage | nœud `MID` (source commune) : **100 kΩ vers `BUS_N`** + diviseur **150 kΩ / 10 kΩ** vers l'ADS1115 (42 V → 2,63 V) | ICD `stuck_fet_diagnostic`. La table « collé fermé » reste à dériver (étude `12` §AA.5.1) |
| S14 | Décharge active du bus (cahier #8) | **par le hacheur** : la sortie libre P17 de l'expander force le comparateur à travers une Schottky `B5819W` et 330 Ω | Pas de MOSFET ni de résistance de plus : la résistance de 22 Ω / 100 W décharge 10 mF en τ = 0,22 s. Le hacheur reste autonome : le forçage ne fait qu'ajouter une condition « ou ». **Le logiciel ne doit le commander que contacteur ouvert** (sinon 82 W permanents) |
| S15 | Hacheur | `TLV1701` (36 V max) alimenté par un **LDO 100 V `TPS7A4001`** à 12 V **depuis le bus lui-même** ; référence **`LM4040A25`** (0,1 %) ; pilote `UCC27517` ; MOSFET `IPB017N10N5LF` | C-S2 exige un hacheur analogique **alimenté par le bus** ; le cahier demande un rail régulé pour le `TLV1701`. Le `TPS7A4001` (7–100 V) fait les deux. Seuils calculés en §4 |
| S16 | Surintensité matérielle → `/SAFE` | comparateur fenêtre **`LM2903`** sur la sortie de l'ACS758 (J14) : **±35 A**, seuils ratiométriques au 5V_LOGIC, sorties vers le verrou du watchdog | ICD J14 `two_paths.rapide`. Le filtre 1 k / 10 nF n'est **que** sur la branche ADS1115, pas sur le comparateur. Capteur débranché → sortie à 0 V → déclenchement → pas d'armement : sûr |
| S17 | Verrou du watchdog (D7) | `TPL5010` (1,0 s, R_DELAY 5,23 kΩ) → `RSTn` ET `OC_N` (`74LVC1G08`) → **`CLR` d'un `SN74LVC1G74`** ; `Q̄` commande un `DMG1012T` qui tire `/SAFE` bas | Une impulsion de RSTn ou un dépassement de courant met la bascule à zéro ; elle tient `/SAFE` bas jusqu'à un front montant sur `SAFE_REARM` (GPIO33, pull-down 100 k). Mise sous tension : `OC_N` tenu bas ~10 ms par 10 kΩ / 1 µF → bascule à zéro |
| S18 | Maintien logiciel de `/SAFE` | `DMG1012T` sur `/SAFE`, grille `SAFE_HOLD` (GPIO32) **tirée haut** 10 kΩ | ESP32 absent, en reset ou en démarrage : grille haute → `/SAFE` bas. L'ESP32 doit activement tirer `SAFE_HOLD` bas pour autoriser |
| S19 | Pull-up et pull-down uniques | **1 kΩ vers 3V3_HOTEL → J11-1 → contact NF CH1 → J11-2 → cavalier JP1 (e-stop radio) → `/SAFE`** ; **10 kΩ vers GND_LOGIC** ; CH2 du champignon lu par l'expander | ICD `SAFE_N_spec` : niveau haut 3,00 V. La résistance est côté 3V3 : un fil du champignon à la masse ne tire que 3,3 mA |
| S20 | Rails 5 V et 12 V AUX | **`TPS54360B`** (60 V, 3,5 A, FET haut intégré, C524806) ×2, 400 kHz | D2 : transistor intégré. Une seule référence pour les deux rails. **Non synchrone** : diode `B560C` externe (calculs §5). Le `LM5164` de la v1 plafonne à 1 A, insuffisant pour 3 A |
| S21 | 12V_COMPUTE | **Mornsun `URB4812YMD-30WR3`** (18–75 V, 12 V / 2,5 A, 1500 V isolé, C22458769) | D2/D6. ⚠️ **8 pièces en stock** chez LCSC : prévoir Mouser/Digi-Key. Brochage relu sur la datasheet (§5.3). Format 1 × 1 pouce, pas 2 × 1 |
| S22 | 3V3_HOTEL | **`AP2112K-3.3`** (600 mA, C51118) depuis 5V_HOTEL | ~35 mA de charge, 0,06 W dissipés. Distinct du régulateur de la DevKitC, dont la broche 3V3 reste en l'air |
| S23 | eFuses (C10) | **`TPS259573`** sur 12V_AUX (OVLO 16,1 V, 2,0 A) ; **`TPS259531`** sur 5V_LOGIC (1,5 A), 5V_LED (0,95 A), 5V_BRAKE avant et arrière (0,49 A chacun) | TPS2595x : 2,7–18 V, seulement sur rails ≤ 12 V (C10). Le 573 (627 en stock) a la broche OVLO que l'ICD demande pour le 12 V ; la variante 531 écrête à 5,7 V. **Pas de `TPS2663x` sur 42 V** : aucune sortie 42 V de moins de 6 A n'existe sur la carte (les branches moteur sont fusées à 25 A) |
| S24 | 5V_BRAKE (D5) | 5V_HOTEL → **diode `SS34`** → **réservoir 2200 µF** → deux eFuses → J22 (avant), J23 (arrière), Micro-Fit 2 broches dont **la broche 2 est non connectée** | La diode empêche les autres charges de vider le réservoir. Pas de masse sur ce connecteur : le retour du pull-up de `EL` passe par `GND_MOT` = `BUS_N`, donc par le point étoile ; une masse de plus créerait une seconde liaison GND_LOGIC–BUS_N (D4) |
| S25 | Fusibles de branche | **Littelfuse MINI 58V 25 A (`0997025.WXN`) dans un porte-fusible CI Keystone `3568-20` (30 A)** au lieu de BF1 58V en MIDI 498 | Le MIDI 498 n'a pas d'empreinte connue et son entraxe n'est pas publié en clair ; le MINI 58V est coté 58 V DC (UL 248, détrompage contre les 32 V), et le porte-fusible a une empreinte KiCad. **À valider** : déclassement thermique du porte-fusible à 25 A continus |
| S26 | Bornes de puissance | **goujons/cosses à œil** : 2 × M5 (J1 batterie, entraxe 26 mm), M4 pour J3–J6, J12, J13. Trous métallisés avec couronne de vias | Aucune empreinte KiCad n'existe pour le Phoenix `PC 5/2-…-7,62` (la série PC 5 n'est pas dans la bibliothèque), et l'ICD prévoit déjà « insert M4 + cosse à œil » au-delà de 25 A. Une cosse sertie et vissée ne se desserre pas en vibration |
| S27 | Point étoile (D4) | **une liaison** `GND_LOGIC`–`BUS_N` : pont de cuivre 4 mm (`NT1`), à côté du goujon `BAT−`, sérigraphié `* GND STAR *` | Le courant de retour des rails hôtel (≤ 2,7 A) est le seul à le traverser. Plans : In1 et B.Cu = `BUS_N` sous la zone puissance, In1/F/B = `GND_LOGIC` sous la zone signal, séparés de 1,1 mm |
| S28 | Masses du domaine puissance | `TPS48100`, `INA228` ×5, hacheur : **masse = `BUS_N`** locale | Ces puces mesurent ou pilotent par rapport au négatif de puissance. Leurs signaux logiques (I²C, INP, FLT) traversent la frontière ; l'écart de masse est la chute dans le plan `BUS_N` (quelques dizaines de mV) |
| S29 | Mesure par branche | `WSK25122L000FEA` 2 mΩ 4 fils + `INA228` (0x41–0x44), **`VBUS` de chaque INA228 sur la sortie de sa branche** | Résout le cahier #13 : fusible fondu = V_branche ≈ 0 avec V_bus présent. ⚠️ Shunt 2 mΩ : **147 pièces** en stock |
| S30 | Isolation BMS (J2) | `ADuM1201` + convertisseur isolé **`B0503S-1WR3`** + 330 Ω de charge minimale ; JST GH 4 broches (verrouillé), masse BMS amenée par la broche 3 | Le connecteur d'origine n'a pas de masse : la référence du côté BMS est à câbler selon M3. Îlot `GND_BMS` séparé dans tous les plans |
| S31 | BNO085 | JST GH 8, 33 Ω série sur SCK/MOSI/CS/MISO, `IMU_WAKE` (PS0) tiré haut 10 kΩ et piloté par l'expander, `IMU_INT` sur GPIO36 | C15 : PS0/PS1 hauts avant le reset ; l'expander démarre en entrée, le pull-up tient PS0 haut |
| S32 | Ventilateurs | MOSFET drain ouvert commun (`DMG1012T`), grille tirée bas → **ventilateurs à 100 % si l'ESP32 est absent** ; tachy 4,7 kΩ série + 10 kΩ vers 3,3 V + `BAT54S` | ICD J18. Le tachy passe par l'expander : **présence et blocage seulement**, pas de mesure de vitesse (plus de GPIO) |
| S33 | WS2812B | `74AHCT1G125` ×2 (C7484) alimentés en 5V_HOTEL, 470 Ω série | Le `SN74AHCT125PWR` (4 voies) est à 0 en stock ; deux portes simples font le même travail |
| S34 | Sonde de température J21 | triple empreinte : 0 Ω vers l'ADS1115 **monté** (LM35/TMP36/module NTC), 4,7 kΩ (DS18B20) et 0 Ω vers GPIO16 **non montés** | ICD J21. GPIO16 est la seule broche libre, et seulement si P3 confirme un module sans PSRAM |
| S35 | Couches et cuivre | **4 couches, 2 oz externes**, 1 oz internes (D9). F.Cu : polygones positifs 42 V, puis signaux et `GND_LOGIC` ; In1 : plans `BUS_N` (zone puissance) / `GND_LOGIC` (zone signal) ; In2 : signaux sous la zone puissance, **plan `3V3_HOTEL`** sous la zone signal ; B.Cu : plan `BUS_N` (zone puissance), îlots de drain sous Q1/Q2, signaux et `GND_LOGIC` (zone signal) | Le cuivre de puissance est dessiné par le script (zones + vias de couture) et exporté vers Freerouting comme plans : l'autorouteur ne route que les signaux |
| S35b | Méthode de routage | Le script pose lui-même : le cuivre de puissance (zones unies par net), les vias de couture, **un via de sortie à côté de chaque pastille `BUS_N`, `GND_LOGIC` et `3V3_HOTEL`** vers son plan, un via dans chaque pastille exposée (eFuses, LDO), des liaisons sous boîtier pour la masse des `INA228`, et une **amorce de 0,25 mm** sur chaque broche fine d'un rail large. Freerouting route le reste, avec une marge de 20 µm ajoutée à toutes les isolations du fichier DSN. Enfin [`scripts/patchroute.py`](scripts/patchroute.py) retire les quelques segments que le DRC de KiCad refuse et termine les connexions restées ouvertes (recherche A* sur grille de 0,1 mm, F.Cu/B.Cu + vias) | Freerouting ne se raccorde pas seul aux plans internes et ne fait pas entrer une piste de 0,6 mm dans une broche de 0,3 mm. La marge absorbe l'écart d'arrondi entre Freerouting et le DRC de KiCad. Vias dans les pastilles exposées : à boucher (*tented/plugged*) à la commande |
| S36 | Isolements | 42 V puissance : **0,5 mm** ; signaux 42 V : 0,19 mm ; logique : 0,15 mm | Voir §6 |
| S37 | Format | **210 × 160 mm**, 6 trous M3 non métallisés avec garde de 4,5 mm sans cuivre | Les trous ne relient aucune masse au châssis (D4) |
| S38 | Repères | sur la couche de fabrication | Comme `safety_bus_distribution` |

---

## 3. Contacteur statique — valeurs

| Grandeur | Calcul | Valeur |
|---|---|---|
| Dissipation des FET à 20 A | 20² × 2,6 mΩ (chaud) × 2 | 2,1 W (1,05 W par FET) |
| Dissipation à 30 A / 2 s | 30² × 2,6 mΩ × 2 | 4,7 W |
| Shunt 1 mΩ à 20 A / 30 A | I² × R | 0,4 W / 0,9 W (WSK2512 : 1 W) |
| Plan de drain Q1 (`BAT_SH`) | F.Cu ≈ 19 × 26 mm + B.Cu ≈ 15 × 26 mm, cousus par vias 0,8/0,4 au pas de 2,2 mm | ≈ 8,8 cm² (étude : 10–12 cm²) ⚠️ |
| Plan de drain Q2 (`BUS_P`) | tout le bus, F.Cu, + îlot B.Cu 12 × 20 mm | > 30 cm² |
| Seuil SCP | (19 mV + 2 µA × 40,2 kΩ) / 1 mΩ | 99 A (≈ 80–120 A) |
| t_SC | éq. 9, R_TMR 100 kΩ, C_TMR 6,8 nF | ≈ 100 µs (I_TMR 67–114 µA : 70–170 µs) |
| UVLO | 1,23 V × (1 M + 51 k) / 51 k | 25,3 V ↑ / 23,4 V ↓ |
| C_BST | ≥ 2 × 218 nC / 1 V | 1 µF |

⚠️ Le plan de drain de Q1 est sous les 10–12 cm² recommandés par l'étude `12` : le goujon
batterie et le shunt occupent la place. Au budget de 20 A (1,05 W par FET) la marge reste
confortable ; à 25 A continu elle ne l'est plus. Point de relecture.

## 4. Hacheur — valeurs

Diviseur à réaction positive sur l'entrée + du `TLV1701` (sortie collecteur ouvert,
tirée à 12 V par 10 kΩ), référence 2,500 V sur l'entrée − :

- R_t = 2 × 49,9 kΩ = 99,8 kΩ (deux résistances : 20 V chacune, sous les 75 V d'une 0603)
- R_b = 6,04 kΩ + 221 Ω = 6,261 kΩ
- R_h = 1,69 MΩ
- **V_ON = 2,5 × (1 + R_t/R_b + R_t/R_h) = 2,5 × (1 + 15,940 + 0,0591) = 42,50 V**
- V_OH ≈ 12 V × 1,69 M / (1,69 M + 10 k) = 11,93 V
- **ΔV = V_OH × R_t / R_h = 0,70 V → V_OFF = 41,80 V**
- Filtre : 1 nF sur le nœud (≈ 6 µs)
- Erreur de seuil : LM4040A 0,1 %, résistances 1 % → ±0,4 V pire cas sur V_ON. **Trier ou
  mesurer** : la recette (étape 6) mesure le seuil réel.
- LDO `TPS7A4001` : 1,173 V × (1 + 93,1 k / 10 k) = 12,1 V ; charge ≈ 4 mA → 0,15 W à 42 V.

⚠️ **Question ouverte n° 1 — le seuil bas est sous la tension de pleine charge.** Pack plein
= 42,0 V > V_OFF = 41,8 V. Contacteur fermé, si une régénération porte le bus à 42,5 V sur
un pack plein, le hacheur s'allume et **ne s'éteint plus** tant que le pack n'est pas
descendu à 41,8 V : 82 W dans la résistance pendant plusieurs minutes. Les seuils
viennent du cahier (📐, « à recaler après M1 et M12 ») et sont appliqués tels quels.
Proposition : ON 43,0 V / OFF 42,3 V (R_b = 6,19 kΩ + 0 Ω, à recalculer), à trancher
avec M12.

## 5. Rails hôtel — valeurs

### 5.1 `TPS54360B` (TI SNVSB93), commun aux deux rails

| Paramètre | Équation datasheet | Valeur |
|---|---|---|
| f_sw | R_T = 101756 × f^−1,008 (éq. 8) | 400 kHz → **243 kΩ** |
| t_on min à 42 V, 5 V | D / f = 0,119 / 400 kHz | 298 ns > 135 ns ✅ |
| UVLO | R_UVLO1 = (V_start − V_stop) / 3,4 µA ; R_UVLO2 = 1,2 / ((V_start − 1,2)/R1 + 1,2 µA) | 24 V / 20 V → **1,18 MΩ / 59 kΩ** |
| Diode | V_R ≥ V_IN max, I ≥ I_L pic | **`B560C`** 60 V / 5 A |
| Bootstrap | | 100 nF |

### 5.2 Rails

| | 5V_HOTEL | 12V_AUX |
|---|---|---|
| I_out de conception | 3,5 A (charge prévue 3,2 A pire cas) | 2,5 A (eFuse à 2,0 A) |
| R_FB haut / bas (V_REF 0,8 V) | 53,6 k / 10,2 k → 5,00 V | 143 k / 10,2 k → 12,0 V |
| L_min (K_ind 0,3, V_IN 48 V) | (48 − 5)/(3,5 × 0,3) × 5/(48 × 400 k) = 10,7 µH | (48 − 12)/(2,5 × 0,3) × 12/(48 × 400 k) = 30 µH |
| L choisie | **15 µH** `SRP1265A-150M` | **33 µH** `MDA1365-330M` |
| Ondulation à 42 V | 0,73 A | 0,65 A |
| C_out | 3 × 47 µF 10 V X7R 1210 (≈ 60 µF effectifs à 5 V) | 3 × 22 µF 25 V 1210 (≈ 33 µF effectifs à 12 V) |
| f_p(mod) = I/(2π V C) | 1,86 kHz | 1,0 kHz |
| f_co = √(f_p × f_sw/2) | 19,3 kHz | 14,2 kHz |
| R_C (éq. 48, gm_ps 12 A/V, gm_ea 350 µA/V) | 10,8 k → **10,7 kΩ** | 10,5 k → **10,5 kΩ** |
| C_C = 1/(2π R_C f_p) | 8,0 nF → **8,2 nF** | 15,1 nF → **15 nF** |
| C_P = 1/(π R_C f_sw) | 74 pF → **82 pF** | 76 pF → **82 pF** |
| Perte diode (I × V_F × (1 − D)) | 3,2 A × 0,55 V × 0,88 ≈ 1,5 W | 2 A × 0,55 V × 0,7 ≈ 0,8 W |

La compensation suit la méthode simplifiée de la datasheet (§8.2.2.11), qui ignore la
rampe de compensation interne : la fréquence de coupure réelle sera plus basse. **À
vérifier par une mesure de réponse à un échelon de charge** (recette).

### 5.3 Module 12 V isolé

`URB4812YMD-30WR3` : brochage relu sur la datasheet Mornsun (vue de dessus, grille 2,54) :
1 Ctrl, 2 GND (entrée), 3 Vin, colonne gauche ; 6 0V, 5 Trim, 4 +Vo, colonne droite ;
entraxe 20,32 mm ; broches Ø 1,0 mm (trous 1,4 mm). Ctrl ouvert = marche ; un NPN commandé
par l'expander (`COMPUTE_OFF`) permet de couper le X1. Capacité de sortie : 110 µF (max
2000 µF). Trim non connecté.

### 5.4 eFuses (`TPS2595x`, SLVSE57C)

I_LIM ≈ 2100 / R_ILM (interpolé dans la table : 487 Ω → 4,17 A, 1,78 kΩ → 1,17 A,
4,42 kΩ → 0,49 A). UVLO 5 V : 1,2 V × 147/47 = 3,75 V. OVLO 12 V (variante 573,
EN/OVLO actif bas) : 1,2 V × 134/10 = 16,1 V. dV/dt : 10 nF. Sorties `FLT` réunies
(`EFUSE_FLT_N`, expander).

| Sortie | Pièce | R_ILM | I_LIM |
|---|---|---|---|
| 12V_AUX | TPS259573 | 1,05 kΩ | ≈ 2,0 A |
| 5V_LOGIC | TPS259531 | 1,4 kΩ | ≈ 1,5 A |
| 5V_LED | TPS259531 | 2,2 kΩ | ≈ 0,95 A |
| 5V_BRAKE AV / AR | TPS259531 ×2 | 4,42 kΩ | 0,49 A |

---

## 6. Isolements et largeurs de cuivre

| Classe | Réseaux | Piste | Isolement | Justification |
|---|---|---|---|---|
| HV_PWR | BAT_*, BUS_P, BR_*, PRE_*, CHOP_N | 1,5 mm (polygones en pratique) | **0,5 mm** | IPC-2221B B2 (externe, nu) demande 0,6 mm à 31–50 V. 0,5 mm est imposé par le shunt 4 fils WSK2512 (0,51 mm entre prise Kelvin et borne de courant). Vernis de tropicalisation de la zone puissance **recommandé** |
| HV_SIG | prises Kelvin, grilles, MID, SW des régulateurs… | 0,15 mm | 0,19 mm | Imposé par le pas de 0,5 mm du `TPS48100` et de l'`INA228` (TI les qualifie à 85–100 V dans ces boîtiers) |
| HV_RAIL | HOTEL_* (hors polygone) | 1,0 mm | 0,25 mm | Arrive sur des broches au pas de 1,27 mm |
| PWR_GND | BUS_N (hors plans) | 0,4 mm | 0,15 mm | 0 V ; les réseaux 42 V gardent leur 0,5 mm (règle de la plus grande des deux) |
| RAIL | 5 V, 12 V, BRK_RES | 0,6 mm | 0,2 mm | IPC-2152 : 0,6 mm sur 2 oz externe ≈ 3,2 A à ΔT 20 °C ; sur 1 oz interne ≈ 1,7 A. ⚠️ 5V_HOTEL porte jusqu'à 3,2 A : à élargir à la main sur ses tronçons internes |
| Default | logique | 0,15 mm | 0,15 mm | JLCPCB 4 couches : 0,09 mm mini ; 0,15 mm partout pour que l'autorouteur passe entre les broches au pas de 0,5 mm |

**Chemins de puissance** (IPC-2152, 2 oz externe) : 20 A continus demandent ≈ 7 mm à
ΔT 20 °C, 30 A ≈ 12 mm. Les polygones de F.Cu font : `BAT_P` ≥ 13 mm, `BAT_SH` ≥ 18 mm,
bande `BUS_P` 13 mm sur toute la longueur, branches ≥ 8 mm (25 A de fusible, 20 A de
pointe). Le retour `BUS_N` passe par **deux plans complets** (B.Cu 2 oz + In1 1 oz) sous
toute la zone puissance. Couture : vias 0,8/0,4 mm au pas de 2,2–2,6 mm. Les cosses ont
chacune une couronne de 8 trous métallisés de 0,5 mm qui amène le courant sur toutes les
couches.

---

## 7. Affectation des E/S de l'ESP32 SAFETY

DevKitC V4, 38 broches. 21 GPIO utilisables (C14) ; GPIO6–11 (flash), GPIO12 (MTDI), GPIO0,
GPIO1/3 (console) **non connectés**. Les entrées seules (34, 35, 36, 39) prennent les
entrées ; RX CAN, RX UART et MISO passent par la matrice GPIO.

| GPIO | Broche module | Réseau | Sens | Défaut matériel | Note |
|---|---|---|---|---|---|
| 5 | J3-10 | `CAN_TX` | S | pull-up 10 k | strapping : haut au boot |
| 34 | J2-5 | `CAN_RX` | E | — | entrée seule, `TCAN1042HV` push-pull |
| 21 | J3-6 | `I2C_SDA` | E/S | 2,2 k | INA228 ×5, ADS1115, TCA9555 |
| 22 | J3-3 | `I2C_SCL` | S | 2,2 k | 400 kHz |
| 18 | J3-9 | `SPI_SCK` | S | — | BNO085, 33 Ω série |
| 23 | J3-2 | `SPI_MOSI` | S | — | 33 Ω |
| 19 | J3-8 | `SPI_MISO` | E | — | 33 Ω |
| 15 | J3-16 | `SPI_CS` | S | pull-up 10 k | strapping MTDO : haut = log de boot conservé |
| 36 | J2-3 | `IMU_INT` | E | pull-up 10 k | entrée seule, H_INTN actif bas |
| 25 | J2-9 | `CTR_INP1` | S | pull-down 100 k | **sécurité** : Q1 |
| 26 | J2-10 | `CTR_INP2` | S | pull-down 100 k | **sécurité** : Q2 |
| 27 | J2-11 | `PRECH_EN` | S | pull-down 100 k | **sécurité** : précharge |
| 32 | J2-7 | `SAFE_HOLD` | S | **pull-up** 10 k | **sécurité** : haut = `/SAFE` tenu bas |
| 33 | J2-8 | `SAFE_REARM` | S | pull-down 100 k | **sécurité** : front montant = réarmement du verrou |
| 39 | J2-4 | `SAFE_N_IN` | E | 1 kΩ série | lecture de `/SAFE`, entrée seule |
| 14 | J2-12 | `WD_DONE` | S | pull-down 100 k | TPL5010 ; une impulsion parasite au boot ne fait qu'un DONE de plus |
| 35 | J2-6 | `BMS_RX` | E | — | entrée seule, via ADuM1201 |
| 17 | J3-11 | `BMS_TX` | S | — | ⚠️ P3 |
| 4 | J3-13 | `FAN_PWM` | S | pull-down 100 k | 25 kHz, MOSFET drain ouvert |
| 2 | J3-15 | `LED_DATA_F` | S | pull-down 100 k | strapping : doit rester bas, aucun pull-up |
| 13 | J2-15 | `LED_DATA_R` | S | pull-down 100 k | |
| 16 | J3-12 | `GPIO16_1W` | — | — | **réserve conditionnelle** (P3) : option DS18B20 (R159 non monté) |

**Réserves** : GPIO16 seulement si P3 confirme un `ESP32-D0WD-V3` sans PSRAM ; GPIO0
contraint. **Si P3 révèle une variante PSRAM**, GPIO16 et GPIO17 sont perdus : `BMS_TX`
passe sur GPIO13 et les deux bandeaux LED se partagent GPIO2 (même motif à l'avant et à
l'arrière). C'est le prix d'un budget à une broche près ; un expander SPI ou un second
`TCA9555` en v2.1 le lèverait.

### Expander `TCA9555` (0x20)

| Port | Réseau | Sens | Note |
|---|---|---|---|
| P00 | `WD_WAKE` | E | sortie WAKE du TPL5010 ; scrutée, le DONE part de GPIO14 |
| P01 | `TPS_FLT_N` | E | défaut du contrôleur (pull-up 10 k) |
| P02 | `SCP_TEST` | S | auto-test du comparateur SCP (pull-down 100 k) |
| P03 | `LATCH_Q` | E | état du verrou watchdog (1 = armé) |
| P04 | `OC_N` | E | surintensité ACS758 en cours |
| P05 | `CHOP_ACT` | E | hacheur conducteur (diviseur 100 k / 33 k) |
| P06 | `ESTOP_CH2_B` | E | second contact du champignon (divergence) |
| P07 | `IMU_WAKE` | S | PS0/WAKE du BNO085 (pull-up 10 k) |
| P10 | `FAN1_TACH` | E | présence / blocage |
| P11 | `FAN2_TACH` | E | présence / blocage |
| P12 | `EFUSE_FLT_N` | E | OU des cinq eFuses |
| P13 | `INA_ALERT_N` | E | OU des cinq INA228 |
| P14 | `LED_OK_K` | S | LED verte (cathode) |
| P15 | `LED_FLT_K` | S | LED rouge (cathode) |
| P16 | `COMPUTE_OFF` | S | coupe le module 12 V du X1 (pull-down 100 k sur la base) |
| P17 | `DISCH_REQ` | S | décharge active du bus par le hacheur (pull-down 100 k) |

Au démarrage le `TCA9555` est en entrée partout : aucune sortie n'est active avant que le
logiciel ne l'ait configuré.

### Plan d'adresses I²C

| Adresse | Composant | Straps |
|---|---|---|
| 0x20 | TCA9555 | A2 A1 A0 = GND |
| 0x40 | INA228 bus (shunt 1 mΩ) | A1 = GND, A0 = GND |
| 0x41 | INA228 branche AV G | A1 = GND, A0 = VS |
| 0x42 | INA228 branche AV D | A1 = GND, A0 = SDA |
| 0x43 | INA228 branche AR G | A1 = GND, A0 = SCL |
| 0x44 | INA228 branche AR D | A1 = VS, A0 = GND |
| 0x48 | ADS1115 | ADDR = GND |

Plage INA228 : `ADCRANGE = 1` (±40,96 mV) sur le bus → ±41 A ; `ADCRANGE = 0`
(±163,84 mV) sur les branches → ±82 A (le fusible est à 25 A). Canaux ADS1115 : A0 ACS758
(÷1,5), A1 DIAG (÷16), A2 V_bus (÷16), A3 température.

---

## 8. Budget de courant par rail

| Rail | Source (capacité) | Consommateurs | Typique | Pire cas réaliste |
|---|---|---|---|---|
| 5V_HOTEL | TPS54360B (3,5 A) | ESP32 0,35 A (0,5 A en rafale Wi-Fi) ; 3V3_HOTEL 0,04 A ; CAN 0,07 A ; B0503S 0,05 A ; 5V_LOGIC ≤ 1,5 A ; 5V_LED ≤ 0,95 A ; 5V_BRAKE 0,01 A | 2,1 A | **3,2 A** (eFuses à leur limite sauf frein) |
| 3V3_HOTEL | AP2112K (0,6 A) | INA228 ×5, ADS1115, TCA9555, TPL5010, logique, BNO085 15 mA, `/SAFE` 3,3 mA, LED 4 mA | 35 mA | 50 mA |
| 5V_LOGIC | eFuse 1,5 A | 2 × ESP32 MOTION (~0,25 A), ACS758 (14 mA), J9 | 0,6 A | 1,5 A |
| 5V_LED | eFuse 0,95 A | bandeaux WS2812B (60 mA/LED en blanc) | 0,3 A | 0,95 A → limiter la luminosité en logiciel |
| 5V_BRAKE AV/AR | eFuse 0,49 A chacun | 2 × 2,3 mA de pull-up `EL` par harnais | 5 mA | — |
| 12V_AUX | TPS54360B (2,5 A) + eFuse 2,0 A | 2 ventilateurs, J8 | 0,5 A | 2,0 A |
| 12V_COMPUTE | URB4812 (2,5 A) | Youyeetoo X1 (+ lidar par son USB) | 1,5–2 A | 2,5 A |
| HOTEL_IN | batterie, fusible 5 A temporisé | (5 V × 3,2 A)/0,88 + (12 V × 2 A)/0,9 + 30 W/0,87 | ≈ 1,5 A à 37 V | **2,7 A à 30 V** (79 W) |
| CH_12V | TPS7A4001 (50 mA) | TLV1701, LM4040, UCC27517, pull-up | 4 mA | 10 mA |

---

## 9. Points « À corriger » du cahier des charges

| # | Point | État |
|---|---|---|
| 1 | Rails non choisis | ✅ **résolu** : S20–S22, valeurs §5 |
| 2 | Pas d'affectation GPIO | ✅ **résolu** : §7 (22 GPIO, expander 16 E/S) |
| 3 | Stock du `TPS4810-Q1` | ✅ **résolu** : `TPS48100QDGXRQ1` C43131316, 903 pièces |
| 4 | Valeurs du `TPS4810-Q1` | ✅ **résolu** : S3–S8, §3 (C_TMR 6,8 nF au lieu de 470 nF) |
| 5 | Hacheur : comparateur, référence, alimentation | ✅ **résolu** : S15, §4 (⚠️ question ouverte n° 1 sur le seuil bas) |
| 6 | Point étoile, liaison `SHIELD` | ✅ étoile résolue (S27). `SHIELD` : traversant J15 ↔ J16, **relié à rien** sur cette carte (ICD : blindage relié côté X1) |
| 7 | Ligne `5V_BRAKE` dédiée | ✅ **résolu** : S24 |
| 8 | Décharge active du bus | ✅ **résolu** par le hacheur (S14) — à valider en recette |
| 9 | Calibre du MRBF | ⏳ hors carte, dépend de M1/M2 |
| 10 | J8 : bobine de contacteur | ✅ **résolu** : J8 = 12V_AUX seulement |
| 11 | J9 : calibre et protection | ✅ **résolu** : eFuse 1,5 A (5V_LOGIC partagé avec la dorsale) |
| 12 | Adresses I²C | ✅ **résolu** : §7 |
| 13 | Détection de fusible fondu | ✅ **résolu** : V_BUS de chaque INA228 sur sa branche (S29) |
| 14 | Marge INA228 85 V / TVS 77,4 V | ✅ reconfirmée : 7,6 V de marge à l'écrêtage nominal de la `SMCJ48CA`, qui n'est atteint qu'au courant de crête de la TVS |

---

## 10. Ce qui n'est pas vérifié

- **Aucune simulation**, aucun prototype. Les boucles des régulateurs, les seuils du hacheur,
  la commutation du contacteur et la tenue thermique sont calculés, pas mesurés.
- **Routage automatique** (Freerouting) des signaux : la boucle chaude des deux
  `TPS54360B` (condensateur d'entrée – circuit – diode) est placée serrée mais routée par
  l'autorouteur, pas à la main. À reprendre à la main avant fabrication.
- **Qualité du routage** : Freerouting a posé ~450 segments de signaux sur In1, la couche
  des plans de masse, qui est donc découpée en dentelle sous la zone signal ; et il a routé
  les deux `TPS54360B`. Le DRC est propre, mais un routage manuel de ces zones est
  nécessaire avant toute commande. Un via a été posé à la main après la passe de
  nettoyage (`EFUSE_FLT_N`, près de U14) ; un nouveau `./build.sh` redonne une carte
  équivalente, pas identique (Freerouting n'est pas déterministe).
- Les résistances ILM et condensateurs dV/dt des eFuses ont été permutés après routage
  (pour libérer la broche FLT) ; le script est à jour.
- Valeurs de stock relevées par l'API JLCPCB le 13/11/2026 ; plusieurs sont faibles :
  `URB4812YMD-30WR3` (8), `WSK25122L000FEA` (147), `LM4040A25` (696).
- Empreintes non vérifiées sur un composant réel : DevKitC (P1, P2), `URB4812`
  (datasheet seulement), inductances (`L_TaiTech_TMPC1265` utilisée pour un `SRP1265A` et un
  `MDA1365` : dimensions voisines, **pastilles à confirmer**), porte-fusible Keystone
  `3568-20` (empreinte KiCad du `3568`).
- Courant de saturation des inductances non relu (≥ 5,5 A souhaité, limite du TPS54360B).
- Brochage du `B0503S-1WR3` pris de mémoire de la série Mornsun B_S-1WR3 (1 GND, 2 Vin,
  3 0V, 4 +Vo) : **à vérifier sur la datasheet**.
- Diode entre l'USB et la broche 5V de la DevKitC V4 : non vérifiée. **Ne pas brancher
  l'USB de la DevKitC carte alimentée** tant que P2 ne l'a pas confirmé.
- Seuil réel du hacheur (±0,4 V pire cas) et tenue du `TLV1701` au démarrage du LDO.
- La table « collé fermé » du diagnostic (étude `12` §AA.5) n'est pas écrite.
- Le niveau logique du BMS (3,3 V présumé, M3).

## Relecture experte obligatoire

À faire relire par un électronicien de puissance **avant** toute commande :

1. **Commutation du contacteur** : Rg_off, di/dt, surtension réelle à l'ouverture sous 30 A
   avec le faisceau réel ; coordination TVS `SMCJ48CA` / roue libre / capacité des
   variateurs.
2. **Thermique** des deux `IPB017N10N5LF` (plan de drain de Q1 ≈ 8,8 cm²) et du shunt.
3. **Court-circuit franc** : t_SC 100 µs à 400–1400 A — l'énergie dans les FET pendant la
   détection est-elle dans leur SOA impulsionnelle ? (non calculé : courbes seulement).
4. **Isolements 42 V** à 0,5 mm (sous l'IPC B2) et 0,19 mm dans les boîtiers fins ;
   opportunité d'un vernis.
5. **Point étoile et passage des signaux** entre domaines `BUS_N` et `GND_LOGIC` (I²C, INP,
   FLT croisent la frontière loin de l'étoile).
6. **Routage** : refaire à la main la couche In1 (aucun signal sur les plans) et
   **mise en page des deux régulateurs à découpage** (boucle chaude, retour du plan,
   placement de la diode) et stabilité de la compensation.
7. **Hacheur** : comportement aux seuils, hystérésis, rapport cyclique en descente longue,
   et la question ouverte n° 1.
8. **Coordination des protections** : MRBF, fusibles MINI 58 V dans un porte-fusible CI à
   25 A, SCP du contrôleur, BMS.

## Questions ouvertes

1. Seuil bas du hacheur sous la tension de pleine charge (§4).
2. Plan de drain de Q1 sous la recommandation de l'étude `12` : accepter, ou agrandir la
   carte (déplacer le goujon `BAT+`) ?
3. Fusibles MINI 58V sur porte-fusible CI au lieu de BF1 en MIDI 498 : à confirmer.
4. Goujons M5/M4 et cosses au lieu du Phoenix PC 5 : à confirmer (et choix des inserts
   à sertir, PEM ou Würth REDCUBE).
5. Référence de masse du côté BMS (J2 broche 3) : dépend de M3.
6. GPIO16/17 (P3).

## Propositions pour l'ICD v1.3 (non appliquées, `icd.yaml` n'est pas modifié)

- `boards.safety_power.connectors.J1`, `J3_J6`, `J12`, `J13` : type « goujon M5 / M4,
  cosse à œil » au lieu de « Phoenix PC 5/2-STF1-7,62 » (S26).
- `J3_J6.protection` : « Littelfuse MINI 58V 25 A, porte-fusible Keystone 3568-20 »
  (S25) ; `current_sense` : « shunt 2 mΩ 4 fils + INA228, VBUS sur la branche ».
- `J2` : côté carte JST GH 4 broches, broche 3 = référence BMS isolée, broche 4 NC.
- `J8.function` : « ventilateurs et auxiliaires 12 V » (supprimer bobine et relais, I4) ;
  `protection` : `TPS259573`, OVLO 16,1 V, 2,0 A.
- `J9.protection` : `TPS259531`, 1,5 A, partagé avec la broche 1 de J15/J16.
- Nouveaux connecteurs **J22 / J23** `5V_BRAKE_AV` / `5V_BRAKE_AR` : Micro-Fit 2 broches,
  1 = 5V_BRAKE, 2 = NC ; supprimer `5V_BRAKE` de `motor_interface` J5/J6 broche 7 (D5).
- `solid_state_contactor.controller.part` : `TPS48100QDGXRQ1` ; `power_fets.part` :
  `IPB017N10N5LF` ; `turn_off.tvs.part` : **`SMCJ48CA` (bidirectionnelle)** ;
  `scp_threshold` : 99 A, t_SC 100 µs, verrouillage.
- `SAFE_N_spec.driven_low_by` : ajouter « verrou 74LVC1G74 (TPL5010 ET comparateur
  ACS758) » et « MOSFET `SAFE_HOLD` de l'ESP32 » (I8).
- `brake_chain.power_source.reservoir` : « 2200 µF sur safety_power, derrière une diode ».
- `J12.note` : « alimenté par le bus via un LDO 100 V » ; ajouter « décharge active du bus
  commandée par l'ESP32, contacteur ouvert uniquement ».
- Créer `gpio_allocation.safety_power` à partir du §7.
- `input_protection_cell.per_rail.42V` : retirer `TPS26630` et `SMCJ43A` pour cette carte
  (aucune sortie 42 V protégée par eFuse ; TVS `SMCJ48CA`).
