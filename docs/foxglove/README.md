# Mises en page Foxglove

Versionnées ici pour une raison simple : une mise en page Foxglove vit dans le
stockage local de l'application, elle n'est ni partagée entre machines ni
sauvegardée, et **sa suppression est définitive** — il n'y a pas d'annulation.
Reconstruire six panneaux à la main après chaque mise à jour, changement de
poste ou fausse manœuvre est exactement le genre de travail qu'un fichier
versionné supprime.

## `bench_imu.json` — banc B1

Les six panneaux de la recette de banc :

| Panneau | Contenu |
|---|---|
| 3D | repère fixe `imu_world`, le marqueur suit `imu_link` |
| Plot | `/imu/data.angular_velocity` sur les trois axes |
| Plot | `/imu/data.linear_acceleration` sur les trois axes, **gravité comprise** |
| Diagnostics | les trois vérifications du pont : capteur, liaison, nœud |
| Raw Messages | `/retriever/imu_status` — qualités et état d'étalonnage |
| Raw Messages | `/retriever/link_status` — hash du protocole, erreurs, aller-retour |

### Importer

Dans Foxglove Studio, menu des mises en page (l'icône à deux rectangles, en
haut à droite) → **Import from file…** → choisir ce fichier.

Se connecter ensuite à `ws://<adresse-du-calculateur>:8765`.

⚠️ Le panneau 3D n'affiche quelque chose que si `bench.publish_tf` est actif
dans `ros2_ws/src/retriever_bringup/config/link_bench.yaml`. C'est une aide de
banc : sur le robot, c'est l'EKF qui publie cette transformation, et laisser les
deux actifs donnerait deux sources sur la même arête de l'arbre TF.

## `bench_lidar.json` — banc lidar

| Panneau | Contenu |
|---|---|
| 3D | `/scan` coloré par la distance, repère fixe `base_link`, grille de 20 m |
| Plot | trois rayons du scan, pour voir la stabilité des mesures dans le temps |
| Raw Messages | `/scan` — `angle_min`, `angle_increment`, `range_min/max`, la taille du tableau |
| Diagnostics | `/diagnostics` |

Vue **orthographique vue de dessus** : c'est la seule qui permette de juger
qu'une pièce ressemble à une pièce. En perspective, un scan 2D est illisible.

⚠️ Deux ponts Foxglove ne peuvent pas écouter le même port. Si le banc IMU
tourne déjà, lancer le lidar avec `foxglove:=false`.

### Ce qu'on regarde, et dans quel ordre

1. **Diagnostics** — les trois lignes au vert. C'est le seul panneau qui dit
   « tout va bien » sans qu'on ait à interpréter des chiffres.
2. **3D** — on bouge le capteur, le repère suit. Vérifie la chaîne entière
   d'un coup d'œil, y compris les conventions de repère.
3. **Plots** — au repos, `linear_acceleration` doit avoir une norme de
   9,81 m/s². Un écart constant dans toutes les orientations est une erreur
   d'échelle ; un écart qui varie avec l'orientation est un biais, et c'est ce
   que corrige l'étalonnage (`tools/imu_cal.py`, voir `docs/DEMARRAGE.md` §4 bis).
4. **`/retriever/link_status`** — `protocol_match` vrai, `unknown_frames` à 0.

*Copyright (c) 2026 William Hanczyk — Apache License 2.0*

## `bench_motors.json` — banc B2, les variateurs

| Panneau | Contenu |
|---|---|
| Publish ×2 | `/retriever/motor_enable` — **ARMER** (masque 7 = m0..m2, 15 = les quatre) et **DESARMER** (0) |
| Publish | `/retriever/motor_command` — la consigne, `duty: [m0, m1, m2, m3]` dans [-1, 1] |
| Publish ×2 | **STOP** (zéros) et **ARRÊT D'URGENCE** (`/retriever/estop`, à ré-armer ensuite) |
| Plot | `/retriever/motor_state.applied[0..3]` — ce que le nœud applique vraiment, après pente et chien de garde |
| Plot | `/retriever/motor_state.cmd_age_ms` — doit rester sous 30 ms tant que le pont tourne |
| Diagnostics | Moteurs / Liaison / Nœud MOTION_FRONT |
| Raw Messages | `/retriever/motor_state` et `/retriever/motion/node_status` |

Séquence : **ARMER** → éditer `duty` dans le panneau consigne → **ENVOYER** →
la roue tourne 10 s (`motors.command_timeout_s`) puis s'arrête seule, ou avant
avec **STOP**. Modifier `duty` ne publie rien tant qu'on n'a pas cliqué.

⚠️ Le panneau Publish n'émet qu'au clic. C'est le pont qui répète la dernière
consigne à 50 Hz vers l'ESP32 ; c'est lui aussi qui l'annule après
`command_timeout_s`. Le chien de garde du firmware (500 ms sans trame) reste
la vraie protection si le PC ou le câble lâche.
