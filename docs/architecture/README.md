# Dossier d'architecture

Le dossier a été écrit avant la première découpe. Il couvre l'énergie, les
communications, ROS 2, la sécurité, le réseau, la nomenclature, l'AMDEC et la
console opérateur. Chaque affirmation porte un marqueur de confiance.

<p align="center">
  <img src="../images/diagrams/architecture.svg" width="100%" alt="Architecture du système">
</p>

## Comment le lire

Le socle `00`–`07` date d'août 2026 (v1.1). La revue des PCB et la validation
des composants par datasheet ont ensuite corrigé plusieurs points, dont trois
critiques pour la sécurité. Ces corrections sont dans `11`, qui **prime** sur
`00`–`07` partout où ils divergent. Chaque document du socle le rappelle en
tête.

Ordre conseillé : `00` pour la vue d'ensemble, `11` pour savoir ce qui a changé,
puis la section qui vous intéresse.

## Documents

| # | Document | Contenu | Statut |
|---|---|---|---|
| 00 | [Index, hypothèses, questions](00-index-A-B.md) | Vue d'ensemble, schéma général, hypothèses, mesures à faire | v1.1, voir `11` |
| 01 | [Inventaire électrique](01-inventaire-electrique.md) | Composants, criticité, architecture de puissance, busbars | v1.1, voir `11` |
| 02 | [Communications, ESP32, moteurs](02-comms-esp32-moteurs.md) | Bus CAN, rôles des ESP32, variateurs, chaîne d'arrêt | v1.1, voir `11` |
| 03 | [ROS 2, états, démarrage](03-ros2-etats-boot.md) | Graphe de nœuds, machine d'états, séquence de boot | v1.1 |
| 04 | [Sécurité, chiens de garde, capteurs](04-securite-watchdogs-capteurs.md) | Les six niveaux d'arrêt, watchdogs, capteurs | v1.1, voir `11` |
| 05 | [Réseau, code, tests, physique](05-reseau-code-tests-physique.md) | Accès distant, organisation du code, stratégie de test | v1.1 |
| 06 | [BOM, AMDEC, plan](06-bom-fmea-schema-plan.md) | Nomenclature chiffrée, AMDEC, plan de construction | v1.1, voir `11` |
| 07 | [Interface opérateur](07-interface-operateur.md) | Pupitre Nintendo Switch, sans ROS côté console | v1.1 |
| 08 | [Revue de conception PCB](08-revue-conception-pcb.md) | Audit des trois cartes avant schéma | partiellement invalidé par `09` et `11` |
| 09 | [Validation des composants](09-validation-composants.md) | Chaque composant vérifié sur datasheet | **référence** |
| 10 | [Spécification `motor_interface`](10-spec-motor-interface.md) | Carte 2 moteurs, identique avant et arrière | **référence** |
| 11 | [Corrections v1.2](11-corrections-v1.2.md) | Errata du socle, décisions du 24 août, état des mesures | **prime sur 00–07** |
| 12 | [Contacteur statique](12-contacteur-statique.md) | `TPS4810-Q1` et MOSFET tête-bêche, précharge conservée | **référence** |
| 13 | [Liaison logicielle](13-architecture-logicielle-liaison.md) | Couche de liaison, firmware, chaîne ROS 2, banc IMU | **référence** |

Tables du protocole, générées depuis `firmware/protocol/protocol.yaml` :
[`generated/protocol-tables.md`](generated/protocol-tables.md).

## Marqueurs

| Marqueur | Sens |
|---|---|
| ✅ | **Vérifié** : datasheet constructeur ou norme |
| 🟡 | **Consensus** : rétro-ingénierie communautaire recoupée |
| 🔴 | **À mesurer** : inconnu ou contradictoire, interdiction de câbler avant mesure |
| ⚠️ | **Risque** : dangereux si mal traité |
| 📐 | **Hypothèse** : valeur choisie faute de donnée, à confirmer |

## Ce qui reste à faire

Les PCB vont être repris à neuf. La conception repartira de
[`hardware/icd.yaml`](../../hardware/icd.yaml), de `09` et de `11`. Le travail
EasyEDA de septembre est conservé dans [`../archive/pcb-v1/`](../archive/pcb-v1/).
