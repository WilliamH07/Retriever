# État des lieux des cartes — 14 novembre 2026

Les trois cartes v2 sont dessinées. Chacune est générée par script (KiCad 10),
vérifiée par `kicad-cli` et livrée avec ses fichiers JLCPCB dans `fab/`. **Aucune
n'a été fabriquée, mesurée ou relue par un électronicien.**

## Vue d'ensemble

| | `safety_bus_distribution` | `motor_interface` | `safety_power` |
|---|---|---|---|
| Statut | **v2.0, prête à commander** | v2.0-draft | v2.0-draft |
| Rôle | tronc CAN + `/SAFE`, 5 V protégé par nœud, sans MCU | ESP32 MOTION ↔ 2 × ZS-X11H, Hall, VR/DIR/EL/STOP | batterie, contacteur statique, précharge, hacheur, INA228, rails, ESP32 SAFETY |
| Format | 110 × 72 mm, 2 couches | 100 × 100 mm, 4 couches | 210 × 160 mm, 4 couches, 2 oz externe |
| BOM JLCPCB | 21 lignes, 122 posés | 36 lignes, 123 posés | 111 lignes, 298 posés |
| ERC | 0 | 0 | 0 |
| DRC (toutes sévérités) | 0 | 0 | 0 |
| Non connectés | 0 | 0 | 0 |
| Parité schéma/carte | 0 | 0 | 0 |
| Routage | Freerouting, reproductible | Freerouting, reproductible | cuivre de puissance par script, signaux par Freerouting + `patchroute.py`, non déterministe |
| Bloquée par | rien | M7, HALL_OC, P1, P2, P3 | M1, M2, M10, M12, PACK_ID, P1–P3, **relecture experte** |
| Décisions | [B1–B20](safety_bus_distribution/decisions.md) | [42 décisions](motor_interface/decisions.md) | [decisions.md](safety_power/decisions.md) |

Les vérifications ERC et DRC ci-dessus ont été relancées le 14/11 sur les fichiers
du dépôt, indépendamment des scripts qui les ont produits.

## Ce que veulent dire les chiffres

ERC 0 et DRC 0 disent que le schéma est cohérent et que la carte respecte les
règles de fabrication de JLCPCB. Ils ne disent **pas** que le circuit fonctionne,
que les valeurs sont justes ni que la carte supporte le courant ou la chaleur.
Seuls la relecture et les essais le disent.

## Mesures qui bloquent

| Code | Quoi | Carte |
|---|---|---|
| M1, M2 | courant de pointe et d'appel réels des moteurs | `safety_power` |
| M7 | niveaux et forme des signaux Hall sur un vrai moteur | `motor_interface` |
| M10, M12 | tension de régénération, comportement du BMS | `safety_power` |
| HALL_OC | sorties Hall à collecteur ouvert ou push-pull | `motor_interface` |
| PACK_ID | étiquette du pack et du BMS | `safety_power` |
| P1 | entraxe réel des rangées de la DevKitC V4 (25,40 mm supposé) | `motor_interface`, `safety_power` |
| P2, P3 | brochage du module, présence de PSRAM (GPIO16/17) | `motor_interface`, `safety_power` |

## Ordre recommandé

1. **Commander `safety_bus_distribution`.** Elle débloque le banc CAN et ne dépend
   d'aucune mesure. Vérifier l'aperçu de placement sur la page JLCPCB avant de payer.
2. Mesurer M7, HALL_OC et P1–P3 sur un moteur et un ZS-X11H, alimentation de labo
   limitée en courant.
3. Mettre `motor_interface` à jour avec ces mesures, puis la commander.
4. Mesurer M1, M2, M10, M12 et relever PACK_ID sur le pack.
5. Faire relire `safety_power` par un électronicien, reprendre les points listés,
   puis seulement la commander.

## `safety_power` : à reprendre avant fabrication

C'est la carte qui commute 42 V / 30 A sur un pack lithium de 474 Wh. Elle est
dessinée jusqu'au bout pour être relue, pas pour être commandée en l'état.

- **Routage brouillon** : environ 450 segments de signaux sur la couche interne
  In1, qui découpent le plan de masse ; les deux régulateurs à découpage
  `TPS54360B` sont routés par l'autorouteur et doivent être refaits à la main.
- **Plan de drain du contacteur** : 8,8 cm², sous les 10–12 cm² demandés.
- **Isolement 42 V** : 0,5 mm entre pistes (IPC B2 demande 0,6 mm).
- **Hacheur** : seuil bas à 41,8 V, sous la tension pack pleine (42,0 V). Il
  resterait allumé à pack plein. Proposition : 43,0 V / 42,3 V.
- **Stocks faibles** : `URB4812YMD-30WR3` (8 pièces), shunt WSK 2 mΩ (147).
- **Non relus sur pièce** : empreintes des inductances et du porte-fusible,
  brochage du `B0503S`.
- **À faire relire** : commutation et surtension des MOSFET, SOA sur court-circuit
  pendant 100 µs, thermique, point étoile, signaux entre domaines de masse,
  coordination des fusibles.

## `motor_interface` : questions tranchées par défaut

| Question | Choix retenu |
|---|---|
| MOSFET de commande | `AO3400A` au lieu du `DMG1012T` (stock) |
| LED d'activité Hall | non |
| NTC moteur | 2 fils, retour sur `GND_MOT` |
| 10 kΩ sur VR côté faisceau | non, à revoir après M7 |

## Écarts à l'ICD à reporter dans `icd.yaml` v1.3

Les deux agents de conception ont listé leurs propositions à la fin de leur
`decisions.md`. Les principales :

- `5V_BRAKE` fourni par `safety_power` sur J22/J23 ; la broche 7 de J5/J6 de
  `motor_interface` devient NC.
- Bornes de puissance en goujon + cosse à œil au lieu du Phoenix PC 5.
- Fusibles MINI 58 V 25 A sur Keystone 3568-20 au lieu du MIDI 498.
- Contacteur : `TPS48100QDGXRQ1`, `IPB017N10N5LF`, `SMCJ48CA` bidirectionnelle.
- BMS sur JST GH 4 broches isolé (`ADuM1201` + `B0503S`).
- Nouvelle table `gpio_allocation.safety_power`.

`icd.yaml` n'est pas encore modifié : c'est le prochain travail.
