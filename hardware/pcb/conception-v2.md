# Conception PCB v2 — dossier transverse

**Version** : 0.1 — 10 novembre 2026
**Statut** : cadrage. Aucun schéma n'est commencé.
**Portée** : les trois cartes du robot, ce qui les relie, et la manière de les concevoir.

Ce document est le point d'entrée de la reprise des PCB. Il ne recopie pas les
spécifications : il dit ce qu'il faut faire, dans quel ordre, et ce qui doit être
tranché avant. Le détail par carte est dans chaque dossier :

| Carte | Cahier des charges | Exemplaires | Bloquée par |
|---|---|---|---|
| `safety_bus_distribution` | [`safety_bus_distribution/cahier-des-charges.md`](safety_bus_distribution/cahier-des-charges.md) | 1 en service, lot de 5 | rien |
| `motor_interface` | [`motor_interface/cahier-des-charges.md`](motor_interface/cahier-des-charges.md) | 2 en service, lot de 5 | M7, HALL_OC, P1–P3 |
| `safety_power` | [`safety_power/cahier-des-charges.md`](safety_power/cahier-des-charges.md) | 1 en service, lot de 5 | M1, M2, M10, M12, PACK_ID, P1–P3 |

Outils et méthode de travail : [`outils.md`](outils.md).

---

## 1. Pourquoi une v2

La première passe (août–septembre 2026) est archivée dans
[`docs/archive/pcb-v1/`](../../docs/archive/pcb-v1/). Elle a échoué pour quatre
raisons, toutes évitables :

1. **Elle partait d'hypothèses périmées** : pack 7,8 Ah, `SN65HVD230`, contrôleur
   `TPS48111`. Les corrections v1.2 n'avaient pas été reportées dans la consigne.
2. **Elle concevait des convertisseurs à découpage de zéro** sans les finir :
   `LM5145` aux broches en l'air, `RT` faux d'un facteur quatre, compensation non
   calculée.
3. **Le budget GPIO était à zéro** dès le départ.
4. **L'outil n'était pas pilotable** : EasyEDA Pro, format binaire, saisie par
   capture d'écran, instable.

La v2 corrige chacun de ces points : une ICD réconciliée d'abord, des modules
pour l'énergie, un budget d'E/S posé avant le schéma, et un outil dont les
fichiers sont du texte.

## 2. Principes

1. **L'ICD fait foi.** [`hardware/icd.yaml`](../icd.yaml) définit chaque
   connecteur, chaque broche, chaque couleur de fil. Un schéma qui la contredit
   est faux. Elle passe en **v1.3** avant le premier schéma (§6).
2. **Chaque carte se teste seule**, sur établi, sans le robot. Points de test
   sérigraphiés, recette écrite avant le routage.
3. **Fail-safe par construction.** Une carte débranchée, un fil coupé, un MCU
   retiré de son support : chaque cas mène au frein serré et au contacteur
   ouvert. Le tableau des modes de défaillance de chaque carte est vérifié sur le
   schéma, ligne par ligne.
4. **Composants disponibles avant d'être dessinés.** Chaque référence est
   vérifiée en stock chez l'assembleur (LCSC/JLCPCB) avant d'entrer dans le
   schéma. Préférer les pièces « basic » quand une pièce « extended » n'apporte
   rien.
5. **Pas de convertisseur à découpage conçu sur carte** si un module certifié
   fait le travail (décision D2).
6. **Les fichiers sont du texte, versionnés, vérifiés en CI** : ERC et DRC à
   chaque commit, sorties de fabrication générées par script.

## 3. Ordre de fabrication

Inchangé depuis [`11-corrections-v1.2.md`](../../docs/architecture/11-corrections-v1.2.md)
partie 6, complété des mesures P1–P3 qui conditionnent l'empreinte du module
ESP32 sur deux cartes.

```
 0  ICD v1.3 + décisions D1–D9                     ← maintenant
 1  P1, P2, P3 sur un ESP32 DevKitC réel           pied à coulisse, multimètre, 15 min
 2  safety_bus_distribution  → lot de 5            rien ne bloque
 3  M4, M5, M7, HALL_OC, HALL_COL                  un moteur + un ZS-X11H, alim labo 24 V / 3 A
 4  maquette du tap Hall, un canal                 plaque à trous
 5  motor_interface  → lot de 5
 6  PACK_ID, M1, M2, M10, M12                      ⚠️ protocole M1 : voir docs/measurements
 7  safety_power  → lot de 5
```

Règles de lot : commander deux fois la BOM ; vérifier le stock avant de figer.

## 4. Décisions transverses

À trancher avant tout schéma. Chaque ligne donne ma recommandation ; la colonne
statut passe à « tranché » avec la date quand William a choisi.

| # | Question | Options | Recommandation | Statut |
|---|---|---|---|---|
| **D1** | Outil de CAO | KiCad · EasyEDA Pro | **KiCad 10** : format texte, `kicad-cli` pour ERC/DRC/exports, scriptable en Python. Voir [`outils.md`](outils.md) | à trancher |
| **D2** | Rails de `safety_power` (12 V calculateur, 12 V auxiliaire, 5 V) | convertisseurs conçus sur carte · modules DC/DC | **Modules** entrée ≥ 60 V, montés sur la carte. C'est là que la v1 a échoué ; le gain d'un convertisseur maison est nul à 1 exemplaire | à trancher |
| **D3** | Manque de GPIO sur l'ESP32 SAFETY (~33 signaux pour 21 broches) | expander I²C · second MCU · ESP32-S3 | **Expander I²C** (type `TCA9555`) pour les signaux lents (LED, présences, straps) ; les signaux de sécurité restent sur GPIO directs | à trancher |
| **D4** | Masses | non défini aujourd'hui | **Un seul point de liaison** `GND_LOGIC`–`BUS_N`, sur `safety_power`, sérigraphié `★ GND STAR`. Aucune autre liaison, nulle part | à trancher |
| **D5** | Alimentation du pull-up de frein `5V_BRAKE` | par `motor_interface` (actuel) · ligne dédiée | **Ligne dédiée** de `safety_power` au faisceau des variateurs, sans passer par `motor_interface` (§5.2) | à trancher |
| **D6** | Isolation du calculateur X1 | adaptateur USB-CAN isolé · renoncer à l'isolation | **Adaptateur isolé** ; sinon l'isolation de `GND_COMPUTE` est fictive (le lidar et l'adaptateur la court-circuitent) | à trancher |
| **D7** | Watchdog `TPL5010` sur `/SAFE` | direct · avec verrou | **Verrou matériel** : `RSTn` est une impulsion, pas un état | à trancher |
| **D8** | Module MCU | DevKitC sur supports · WROOM soudé | **DevKitC sur supports Mill-Max** (remplaçable sans fer). Empreinte validée par P1 | proposé en v1.2 |
| **D9** | Fabrication | JLCPCB assemblé · nu + soudure main | **JLCPCB, 4 couches, assemblage des CMS**, traversants soudés à la main | à trancher |

## 5. Interfaces communes

### 5.1 Dorsale CAN + `/SAFE`

Micro-Fit 3.0, 6 positions, deux en parallèle par nœud. Brochage dans
`shared_pinouts` de l'ICD.

| Broche | Réseau | Note |
|---|---|---|
| 1 | `5V_LOGIC` | origine à trancher : amont ou aval du contacteur (§6, I3) |
| 2 | `CANH` | |
| 3 | `CANL` | |
| 4 | `/SAFE` | actif bas, drain ouvert, référencé 3,3 V |
| 5 | `GND_LOGIC` | |
| 6 | `SHIELD` | relié d'un seul côté ; quel côté et quelle masse : à trancher avec D4 |

- **CAN** : 500 kbit/s, `TCAN1042HVDR` sur chaque nœud, `STB` à la masse,
  terminaisons fendues sur `safety_bus_distribution` uniquement. Stub ≤ 30 cm,
  aller et retour compris.
- **`/SAFE`** : **un** pull-up 1 kΩ vers `3V3_HOTEL`, en série avec le contact NF
  du champignon, sur `safety_power`. **Un** pull-down 10 kΩ, sur `safety_power`.
  1 MΩ sur chaque autre carte, pour définir son état débranchée. Tirée à la
  masse par : champignon, ESP32 SAFETY, `TPL5010` (via verrou, D7), comparateur
  de surintensité, e-stop radio.
- **Nœud éteint sur `/SAFE` actif** : prévoir une résistance série sur chaque
  entrée, pour qu'un ESP32 non alimenté ne soit pas rétro-alimenté par ses
  diodes de protection.

### 5.2 Chaîne de freinage — ⚠️ défaut à corriger

`/SAFE` **ne freine pas** : `STOP` met les ZS-X11H en roue libre. Le freinage
vient de `EL`, actif haut, tiré vers `5V_BRAKE` par une résistance de 2,2 kΩ
**sur le faisceau, côté variateur**. `motor_interface` le relâche par un
`DMG1012T` commandé par `GPIO26 ET /SAFE`.

**Défaut trouvé en analyse** : `5V_BRAKE` arrive au faisceau par la broche 7 de
J5/J6, c'est-à-dire **par `motor_interface`**. Carte débranchée, le pull-up n'est
plus alimenté, `EL` retombe et **le frein se relâche**. L'ICD affirme l'inverse
(`failure_modes`). Et aucun connecteur n'apporte `5V_BRAKE` à `motor_interface`.

→ Décision D5. La correction doit être vérifiée contre ces quatre cas :
`motor_interface` débranchée, ESP32 retiré, câble `/SAFE` coupé, contacteur
ouvert.

### 5.3 Rails

| Rail | Origine | Survit à l'ouverture du contacteur | Usage |
|---|---|---|---|
| `BUS` 30–42 V | aval contacteur | non | variateurs, hacheur |
| `5V_HOTEL` / `3V3_HOTEL` | amont contacteur | **oui** | ESP32 SAFETY, pull-up `/SAFE`, `5V_BRAKE` |
| `12V_COMPUTE` | à trancher (D2, D6) | à trancher | X1 |
| `12V_AUX` | à trancher (D2) | à trancher | ventilateurs, lidar |
| `5V_LOGIC` | à trancher (§6, I3) | à trancher | dorsale, nœuds MOTION |

Tout composant relié au bus est coté **60 V minimum** ; fusibles et
porte-fusibles **58 V DC** (C-S3).

## 6. ICD v1.3 — ce qu'il faut corriger avant le premier schéma

| # | Incohérence | Correction |
|---|---|---|
| I1 | Le relais NF de frein est encore décrit à six endroits | Garder uniquement MOSFET + porte ET + pull-up faisceau |
| I2 | `5V_BRAKE` passe par `motor_interface` | Appliquer D5 ; corriger `failure_modes` |
| I3 | `5V_LOGIC` amont du contacteur (`01`) ou aval (`08`) | Trancher. Recommandation : amont, pour garder le diagnostic CAN contacteur ouvert |
| I4 | J8 de `safety_power` alimente une « bobine de contacteur » qui n'existe plus | Supprimer |
| I5 | Rôle de `motor_interface` : straps GPIO ou ADS1115 | ADS1115 partout |
| I6 | Pas de `gpio_allocation.safety_power` | La créer, avec D3 |
| I7 | Masses et `SHIELD` non définis | Appliquer D4 |
| I8 | Comparateur ACS758 → `/SAFE` absent de `driven_low_by` | L'ajouter |
| I9 | `PPTC 1812L050/30` ou eFuse `TPS259573` par branche, non tranché | Trancher par carte |
| I10 | Valeur de `MF-MSMF014` annoncée 30 mA | Vérifier sur datasheet |

Les documents du dossier (`02`, `06`, `08`) gardent d'anciennes valeurs
(`SN65HVD230`, 2N7002, stub 15 cm, pull-up 4,7 kΩ vers 5 V). L'ICD v1.3 et le
document `11` font foi ; ces passages seront annotés, pas réécrits.

## 7. Erreurs de calcul relevées dans le dossier

- **Filtre Hall** : 2,2 kΩ × 10 nF donne τ = 22 µs et une coupure à 7,2 kHz,
  pas « 7 µs / 22 kHz » (`11`, `09`). Atténuation réelle à 16 kHz : environ
  −8 dB sur le front descendant, −12 dB sur le montant ; pas « 12 à 15 dB ».
  Le filtre reste suffisant pour le comptage ; à confirmer à l'oscilloscope (M7).
- **Interruptions Hall** : 1740/s par carte (deux moteurs, trois lignes), pas 870/s.

## 8. Critères de sortie, communs aux trois cartes

Une carte part en fabrication quand :

- [ ] l'ICD v1.3 est respectée, broche par broche ;
- [ ] ERC sans erreur, DRC sans erreur aux règles JLCPCB 4 couches ;
- [ ] chaque composant a une référence LCSC en stock, vérifiée la semaine de la commande ;
- [ ] le tableau des modes de défaillance est vérifié sur le schéma ;
- [ ] la recette de mise en route est écrite et chaque mesure a son point de test ;
- [ ] le PDF du schéma et le rendu 3D sont relus par William ;
- [ ] Gerber, perçage, BOM et placement sont générés par script depuis le commit étiqueté.
