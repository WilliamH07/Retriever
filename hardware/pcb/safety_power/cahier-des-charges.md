# `safety_power` — cahier des charges v2

**Statut** : la plus lourde des trois, fabriquée en dernier. Bloquée par M1, M2,
M10, M12, PACK_ID et P1–P3.
**Exemplaires** : 1 en service, lot de 5.
**Références** : [`11-corrections-v1.2.md`](../../../docs/architecture/11-corrections-v1.2.md),
[`12-contacteur-statique.md`](../../../docs/architecture/12-contacteur-statique.md),
[`09-validation-composants.md`](../../../docs/architecture/09-validation-composants.md).
**Brochage** : `boards.safety_power`, `shared_pinouts`, `brake_chain` dans
[`hardware/icd.yaml`](../../icd.yaml).
**Cadre commun** : [`../conception-v2.md`](../conception-v2.md).

## 1. Rôle

La carte qui décide si le robot a le droit de bouger. Elle :

- reçoit la batterie, aval du coupe-batterie et du fusible MRBF ;
- la commute sur le bus par un **contacteur statique**, après **précharge** ;
- absorbe l'énergie de freinage par un **hacheur** ;
- mesure tension, courant et énergie ;
- produit les rails 12 V et 5 V, dont ceux qui **survivent** à l'ouverture du contacteur ;
- porte l'**ESP32 SAFETY**, qui accorde ou refuse l'armement, et le pull-up unique de `/SAFE` ;
- héberge l'IMU déportée, les ventilateurs, les LED, la sonde de température.

## 2. Blocs et composants

| Bloc | Composant | Valeurs | Statut |
|---|---|---|---|
| Entrée batterie | Phoenix PC 5/2-STF1-7,62 | 32 A, 25,6 A déclassé | ✅ ; ⚠️ sous la capacité cellule 26–40 A |
| Anti-inversion | `LTC4359` + FET | | ✅ ; absent de l'ICD |
| Contacteur statique | `TPS4810-Q1` + 2 × `IPB017N10N5` tête-bêche, source commune | 20 A continu, 30 A ≤ 2 s | ✅ pièces ; ⚠️ **stock LCSC jamais vérifié** |
| | shunt de protection | 1 mΩ, 4 fils | ✅ |
| | résistance de grille à l'ouverture | 100–220 Ω | 📐 à régler à l'oscilloscope |
| | TVS drain-à-drain | `SMCJ48A`, écrêtage 77,4 V | ✅ |
| | roue libre côté charge | Schottky 100 V | ✅ |
| | diagnostic de collage | nœud `DIAG`, 100 kΩ, lu par ADS1115 | ✅ ; cas « collé fermé » non tabulé par TI |
| Précharge | FET P 100 V, ~100 mΩ, piloté par l'ESP32 | | 📐 |
| | résistance hors carte | `RH02510R00FE02`, 10 Ω / 25 W, τ 0,1 s, timeout 1,5 s | 📐 dépend de M10 |
| Hacheur de freinage | comparateur analogique + MOSFET N 100 V ≥ 30 A | ON 42,5 V / OFF 41,8 V | 📐 seuils ; comparateur et alimentation **non choisis** |
| | résistance hors carte | `TT WH100-22RJI`, 22 Ω / 100 W | ✅ |
| Fusibles de branche | 4 × `BF1 58V` 25 A, porte-fusible MIDI 498 | | ✅ |
| Mesure | `INA228` bus + `INA228` par branche, shunt 2 mΩ | | ✅ ; ⚠️ 85 V abs. contre 77,4 V d'écrêtage |
| Surintensité matérielle | `ACS758` + comparateur → `/SAFE` | 35 A | ✅ |
| Branches protégées | `TPS26630` (42 V, 6 A), `TPS26620` (42 V, < 880 mA), `TPS259573` (12 V / 5 V) | variantes à seuil **ajustable** | ✅ |
| Rails | 12 V calculateur, 12 V auxiliaire, 5 V logique, 5 V / 3,3 V hôtel | | 🔴 **aucune pièce choisie** (D2) |
| MCU | ESP32-DevKitC V4 sur supports Mill-Max 310 | | 📐 P1 |
| CAN | `TCAN1042HVDR` | | ✅ |
| Watchdog | `TPL5010` | | ✅ ; verrou sur `/SAFE` à ajouter (D7) |
| `/SAFE` | pull-up 1 kΩ vers `3V3_HOTEL` en série avec le NF du champignon ; pull-down 10 kΩ | | ✅ |
| BMS | isolateur `ADuM1201` ou opto, UART | | 📐 ; GPIO16/17 selon P3 |
| Périphériques | BNO085 déporté sur mât, 2 ventilateurs PWM, WS2812B AV/AR via `SN74AHCT125`, sonde 3 broches (double empreinte) | | ✅ |

## 3. Connecteurs

21 positions dans l'ICD (J10 supprimé) : 7 Phoenix 7,62 mm (puissance), 9 Micro-Fit
3.0 (signaux, alimentations), JST PAP, XH, GH et deux en-têtes ventilateur. Détail
dans `boards.safety_power.connectors`.

## 4. À corriger ou compléter avant schéma

### 🔴 Bloquants de conception

1. **Rails non choisis.** Quatre convertisseurs sans référence. → D2 :
   modules DC/DC entrée ≥ 60 V. Décider pour chacun s'il est **amont** (survit au
   contacteur : `5V_HOTEL`, `3V3_HOTEL`, `5V_BRAKE`) ou **aval**.
2. **Pas d'affectation GPIO.** Environ 33 signaux pour 21 broches utilisables.
   → D3 : liste exhaustive des signaux, classés sécurité (GPIO directs) et lents
   (expander I²C).
3. **Stock du `TPS4810-Q1`** à vérifier chez LCSC avant tout dessin. S'il est absent,
   l'étude `12` est à reprendre : aucun autre contrôleur au-dessus de 40 V n'a deux
   sorties de grille indépendantes.
4. **Valeurs du `TPS4810-Q1`** : seuil de court-circuit, `R_ISCP`, `C_TMR`
   (470 nF proposé par la v1), seule la formule est donnée.
5. **Hacheur** : choisir comparateur, référence et alimentation locale. Le
   `TLV1701` est limité à 36 V : il faut l'alimenter depuis un rail régulé.

### 🟠 À compléter

6. **Point d'étoile de masse** `★ GND STAR` (D4) et liaison de `SHIELD`.
7. **Ligne `5V_BRAKE` dédiée** vers le faisceau des variateurs (D5).
8. **Décharge active du bus** : deux propositions concurrentes (MOSFET + 47 Ω / 50 W,
   ou 6 × 2512 auto-alimentées). Elle conditionne le test de collage.
9. **Calibre du MRBF** : 60 ou 80 A après M1 ; MRBF ou fusible classe T après M2.
10. **J8** : supprimer l'alimentation de « bobine de contacteur » (I4).
11. **J9** : calibre et protection absents.
12. **Adresses I²C** de tous les composants du bus (INA228 ×5, ADS1115, expander).
13. **Détection de fusible fondu** sur les branches moteur.
14. **Marge INA228** : 85 V absolus contre 77,4 V d'écrêtage TVS, à reconfirmer.

### Règle de placement

Zone puissance et zone signal strictement séparées, plan de masse de séparation,
un seul point de liaison sérigraphié. Cuivre 2 oz externe, 10–12 cm² par FET du
contacteur.

## 5. Mesures bloquantes

| Mesure | Ce qu'elle change |
|---|---|
| **PACK_ID** étiquettes pack et BMS | budget courant, protocole BMS |
| **M1** seuil de coupure du BMS | calibre MRBF, suffisance de J1 |
| **M2** résistance interne | courant de court-circuit, MRBF ou classe T |
| **M10** capacité du bus | résistance et durée de précharge, énergie du test de collage |
| **M12** tension des condensateurs ZS-X11H | si 50 V, marge du hacheur |
| **P1–P3** module ESP32 | empreinte, GPIO16/17 |
| M13–M15 (proposées en v1) | repos du bus, tension renvoyée par une roue tournée à la main, acceptation de la charge par le BMS |

⚠️ **M1** : fusible 40 A en série, pack ≤ 50 % de charge, à l'extérieur, sable
sec ou extincteur classe D à portée.

## 6. Ce que la v1 laisse de réutilisable

Dans [`docs/archive/pcb-v1/`](../../../docs/archive/pcb-v1/) :

- bloc `LM5164` complet, compensation de type 3, inductance 47 µH ;
- `RT` = 33,2 kΩ pour 300 kHz sur `LM5145` (la v1 avait 133 kΩ, faux) ;
- candidats `SRP2313AA-100M` et `BSC070N10LS5`, bilans de pertes ;
- `C_TMR` 470 nF, diviseurs de tension scindés, routage Kelvin des shunts ;
- constat de terrain : une roue tournée à la main rétro-alimente le bus.

## 7. Recette de mise en route (à détailler)

Alimentation de labo limitée en courant, **jamais la batterie** en premier essai.

1. 30 V / 0,5 A labo sur l'entrée batterie, contacteur ouvert : rails hôtel
   présents, ESP32 démarré, `/SAFE` haut champignon relâché, bus à 0 V.
2. Champignon enfoncé : `/SAFE` bas.
3. Limite portée à 1 A, capacité de test sur le bus : précharge en moins de
   1,5 s, puis fermeture du contacteur.
4. Test `SCP_TEST` du `TPS4810-Q1` : ouverture sur défaut simulé.
5. Diagnostic de collage : Q1 et Q2 commandés séparément, nœud `DIAG` lu.
6. Hacheur : rampe du labo à 43 V, conduction à 42,5 V, arrêt à 41,8 V.
