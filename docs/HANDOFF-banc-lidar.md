# HANDOFF — banc lidar, le YDLIDAR X4

**État au 20 septembre 2026.** Branche `feat/link-layer-and-imu-bench`. Pendant
de [`HANDOFF-banc-imu.md`](HANDOFF-banc-imu.md), même structure : ce qui marche
avec les chiffres, ce qui a été cassé et par quel mécanisme, ce qui reste.

---

## 1. Ce qui fonctionne, mesuré

Chaîne complète **X4 → CP2102 → `/dev/ydlidar` → `ydlidar_ros2_driver` →
`/scan` → foxglove_bridge → Foxglove Studio**, en une commande :

```bash
ros2 launch retriever_bringup bench_lidar.launch.py
```

| Mesure | Valeur | Où la relire |
|---|---|---|
| Points par tour | 663 à 667 | `ros2 topic echo /scan --once --field ranges` |
| Vitesse de rotation | ~7,5 Hz, libre, non asservie | déduite : 5 kHz / 667 |
| Couverture (échos ≥ `range_min`) | **67 %** — seuil §03 : > 60 % | DEMARRAGE.md §4 ter, point 3 |
| Portée relevée | 0,31 à 5,19 m dans la pièce du banc | idem |
| Orientation | ✅ validée : objet à 1 m droit devant apparaît devant | `reversion: false`, `inverted: false` |
| Modèle, firmware | X4, 1.10, code modèle 6, série 2021090300040777 | journal du pilote en double canal |

---

## 2. Les défauts trouvés, et leur mécanisme

Une après-midi pour un capteur qui répondait dès la première seconde. Toute la
difficulté tenait à des **paramètres**, et à la méthode pour les trouver.

### 2.1 La méthode qui a fini par marcher

Cinq hypothèses successives — alimentation, DTR, résolution fixe, fréquence,
intensité — chacune plausible, chacune fausse ou confondue avec une autre. Ce
qui a débloqué : **`tri_test`**, le programme d'exemple du SDK, qui recevait des
scans. À partir de là, la règle a été de reproduire sa configuration **à
l'identique** dans le pilote ROS, puis de s'en écarter un paramètre à la fois.

⚠️ La règle « un paramètre à la fois » a été enfreinte deux fois dans la
journée, et les deux fois ont coûté : un résultat attribué au mauvais réglage,
consigné comme un fait, puis rétracté. Voir 2.3.

### 2.2 `isSingleChannel: true` — contraire à la documentation (`f8720dc`)

La table par modèle du constructeur donne le X4 en double canal. Cet exemplaire
répond au dialogue de configuration comme un double canal — il livre ses
informations produit — mais **ne délivre ses scans qu'en mono-canal** :

| | `false` (documentation) | `true` (mesure) |
|---|---|---|
| Informations produit | ✅ lues | ❌ « Fail to get baseplate device information » |
| Scans | ❌ `Operation timed out` à l'infini | ✅ 660+ points par tour, en continu |

Conséquence permanente : le journal affiche « Fail to get baseplate device
information » à chaque démarrage. **Ce n'est pas une panne.**

### 2.3 `support_motor_dtr: true` — et une rétractation

Un premier commit affirmait `false` comme établi : le moteur ne démarrait pas
avec `true`. Mais `isSingleChannel` était encore à `false` à ce moment-là ; les
deux avaient changé ensemble et le résultat a été attribué au mauvais. `tri_test`
tourne avec `true`, le moteur va bien. Le fichier de configuration porte la
rétractation en commentaire, pour que personne ne remette `false` en se fiant à
l'historique.

### 2.4 `intensity_bit: 10` — « cherche », pas une largeur

Le pilote ROS met 0 par défaut. Or 10 signifie « je ne sais pas, sonde » : c'est
ce qui déclenche la séquence `16 → 8 → 0` visible au démarrage, **avec ses
erreurs de somme de contrôle, qui sont normales** — le SDK essaie les largeurs
une à une et resynchronise le flux à chaque essai. À 0, il ne cherche pas, ne
resynchronise jamais, et attend des trames qui n'arrivent pas. C'était la
différence décisive entre `tri_test` et le pilote ROS aux paramètres minimaux.

### 2.5 `sample_rate: 5` — le pilote ROS met 9

Valeur par défaut d'un autre modèle. Avec 9, le nombre de points par tour
attendu est faux d'un tiers.

### 2.6 `invalid_range_is_inf` est sans effet (`f93e2bf`)

Réglé à `true`, les mesures sans écho sortent quand même à **`0.0`** — 221 zéros
sur 667 points, aucun `+inf`. Le réglage promet REP-117 et ne le tient pas.
Deux conséquences :

- **tout consommateur de `/scan` doit filtrer sous `range_min` lui-même.**
  `slam_toolbox` et Nav2 le font ; un nœud maison qui l'oublierait verrait 221
  obstacles collés au capteur ;
- le taux de couverture se compte **sous `range_min`**, pas par `isfinite()`,
  qui donne 100 % et ne mesure rien.

---

## 3. Ce qui reste

### 3.1 Alimentation `USB_PWR` — avant tout usage prolongé

Le banc tourne sur l'USB du PC. Le manuel avertit qu'un port USB ne fournit
souvent pas la pointe de **1 A au démarrage du moteur**, et le §01 retient une
alimentation 5 V dédiée. Symptôme à reconnaître si ça se produit : moteur qui
démarre puis cale, scans tronqués. Pas de power bank — ondulation.

### 3.2 Diagnostics sur `/scan`

Le §04 prévoit un `DiagnosedPublisher` et un `source_timeout` de 2 s côté
collision monitor. Le pilote tiers ne fournit rien de tel : à écrire côté projet,
sur le modèle de ce que fait `retriever_link` pour l'IMU (cadence attendue,
âge du dernier message, taux de couverture — ce dernier avec le bon critère,
voir 2.6).

### 3.3 Position du lidar dans l'URDF

Le banc publie `base_link → laser` par un `static_transform_publisher`, avec
des arguments `x y z yaw` pour pouvoir mesurer avant d'avoir l'URDF. C'est une
**aide de banc**. Sur le robot, `retriever_description` décrit le montage, et
lui seul : deux sources sur la même arête de l'arbre TF est la faute du §I.3.

### 3.4 `ignore_array` — une fois monté

Les secteurs où le lidar voit le châssis, en degrés. Vide au banc.

### 3.5 Le remplacement, phase 4

Rappel du §00 : le X4 est un capteur d'intérieur — 0/550/2000 lux spécifiés,
0–40 °C, aucun indice IP. Le tiers d'échos perdus au banc, sur une pièce
intérieure, donne la mesure : en extérieur il ne servira qu'à la détection
d'obstacles locale par temps couvert, jamais à la localisation. Hokuyo UST-10LX
ou RPLIDAR série S/T prévus.

---

## 4. Où se trouve quoi

| | |
|---|---|
| Installation, lancement, vérification, dépannage | `docs/DEMARRAGE.md` §4 ter |
| Paramètres, chaque valeur avec sa provenance | `ros2_ws/src/retriever_bringup/config/lidar_bench.yaml` |
| Fichier de lancement | `ros2_ws/src/retriever_bringup/launch/bench_lidar.launch.py` |
| Version épinglée du pilote | `ros2_ws/retriever.repos` — branche `humble` |
| Mise en page Foxglove | `docs/foxglove/bench_lidar.json` |
| Le témoin qui marche, quand plus rien ne marche | `~/YDLidar-SDK/build/tri_test` |

---

*Copyright (c) 2026 William Hanczyk — Apache License 2.0*
