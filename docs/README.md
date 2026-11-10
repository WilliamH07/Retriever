# Documentation

Une page pour savoir quel document ouvrir, et s'il est à jour.

## Par besoin

| Je veux… | Ouvrir |
|---|---|
| Installer, flasher un ESP32, voir l'IMU dans Foxglove | [`DEMARRAGE.md`](DEMARRAGE.md) |
| Savoir ce qui tourne aujourd'hui, avec les chiffres | [`bancs/`](bancs/) |
| Comprendre l'architecture du robot | [`architecture/`](architecture/) |
| Connaître le brochage d'un connecteur | [`../hardware/icd.yaml`](../hardware/icd.yaml) |
| Savoir quelles mesures bloquent la conception | [`measurements/`](measurements/) |
| Ouvrir une mise en page Foxglove de banc | [`foxglove/`](foxglove/) |
| Retrouver une image, un rendu, un schéma | [`images/`](images/) |
| Présenter le projet à un sponsor | [`sponsorship/`](sponsorship/) |
| Relire un travail abandonné ou remplacé | [`archive/`](archive/) |

## Arborescence

```
docs/
  README.md            cette page
  DEMARRAGE.md         du dépôt vierge au flux /imu/data
  architecture/        dossier de conception, 00 à 13, avec son index
  bancs/               un rapport par banc : IMU, lidar, moteurs
  measurements/        mesures qui conditionnent le matériel
  foxglove/            mises en page Foxglove Studio, une par banc
  images/              rendus CAO, photos de montage, schémas SVG
  sponsorship/         dossier de sponsoring (Typst + PDF)
  archive/             travaux remplacés, conservés pour l'historique
```

## Règles

- **Une information, un endroit.** Le brochage vit dans `hardware/icd.yaml`, le
  protocole dans `firmware/protocol/protocol.yaml`. Les documents y renvoient
  au lieu de recopier.
- **Ce qui est périmé va dans `archive/`**, avec une ligne qui dit par quoi il
  est remplacé. Rien n'est supprimé.
- **Les liens sont vérifiés en CI** par `tools/check_links.py`.
- Les documents de conception sont en français. Le README racine et les README
  du matériel sont en anglais, pour les visiteurs.
