# Bancs

Chaque banc valide un maillon de la chaîne avant qu'il soit monté sur le robot.
Un rapport par banc, même structure : ce qui marche avec les chiffres, les
défauts trouvés et leur mécanisme, ce qui reste.

Installation et commandes de lancement : [`../DEMARRAGE.md`](../DEMARRAGE.md).
Mises en page Foxglove : [`../foxglove/`](../foxglove/).

| Banc | Chaîne | État | Chiffre clé |
|---|---|---|---|
| [B1 — IMU](imu.md) | BNO085 → SPI → ESP32 → série → ROS 2 → Foxglove | ✅ validé | `/imu/data` à 99,8 Hz, 0 erreur sur 10 000 rapports |
| [B2 — Lidar](lidar.md) | YDLIDAR X4 → USB → ROS 2 → Foxglove | ✅ validé | couverture 67 % pour un seuil de 60 % |
| [B3 — Moteurs](moteurs.md) | Foxglove → ROS 2 → série → ESP32 MOTION → ZS-X11H | 🟡 codé, premier essai matériel à faire | `MOTOR_CMD` à 50 Hz, arrêt sous 500 ms sans consigne |

```
B1  IMU      ████████████████████  validé
B2  lidar    ████████████████████  validé
B3  moteurs  ██████████░░░░░░░░░░  codé, testé sur hôte, aucune roue n'a tourné
```

Les bancs IMU et moteurs relient l'ESP32 au calculateur par une liaison série. **Aucune fonction de sécurité
n'est validée sur la série** : elle n'a ni arbitrage, ni acquittement, ni
confinement d'erreur. La bascule vers le CAN attend la carte
`safety_bus_distribution`.
