# MOTION — banc avant, arrière ou quatre roues

Un même projet ESP-IDF v5.5 produit les programmes des deux ESP32 classiques
DevKitC/WROOM et celui du banc à un seul ESP32. Les variateurs ZS-X11H assurent
la commutation BLDC ; l'ESP32 leur fournit VR, DIR et STOP. Le firmware ne
commute pas directement les phases du moteur.

Les cartes `motor_interface` étant encore en conception, ces profils pilotent
**le montage de banc PWM + RC**. Ils ne pilotent pas encore le MCP4728, les
Hall, l'ADS1115, `/SAFE`, le frein EL ou le watchdog externe de la carte finale.

## Profils et câblage

| Profil | Identité | Roues globales | Sorties locales | Masque pour armer |
|---|---|---|---|---|
| `front` | MOTION_FRONT, 2 | m0 avant gauche, m1 avant droite | 0, 1 | 3 |
| `rear` | MOTION_REAR, 3 | m2 arrière gauche, m3 arrière droite | 0, 1 | 12 |
| `bench4`, 3 moteurs | MOTION_FRONT, 2 | m0, m1, m2 | 0, 1, 2 | 7 |
| `bench4`, 4 moteurs | MOTION_FRONT, 2 | m0, m1, m2, m3 | 0, 1, 2, 3 | 15 |

Le banc utilise l'identité FRONT : ne pas connecter simultanément un banc4 et
un FRONT sur le même CAN. Les cartes avant et arrière utilisent les **mêmes
broches locales**, mais sélectionnent des indices de roues différents.

| Sortie locale | PWM → VR | DIR | STOP |
|---|---|---|---|
| 0 | GPIO25 | GPIO26 | GPIO27 |
| 1 | GPIO32 | GPIO33 | GPIO14 |
| 2, banc seulement | GPIO18 | GPIO19 | GPIO21 |
| 3, banc seulement | GPIO22 | GPIO23 | GPIO13 |

UART USB : GPIO1/3, 921600 bauds. CAN : TX GPIO5, RX GPIO4, 500 kbit/s,
transceiver externe obligatoire. Deux terminaisons de 120 Ω aux extrémités.
GPIO5 est une broche de strapping : vérifier son état haut au démarrage.

**Interface DIR/STOP obligatoire.** Le drain ouvert interne ne rend pas les
GPIO tolérants au 5 V. Le rappel du variateur ne doit jamais arriver directement
sur l'ESP32. Voir les limites électriques de la
[datasheet Espressif](https://documentation.espressif.com/esp32_datasheet_en.html).

Deux configurations logicielles sont prévues ; choisir celle qui correspond au
montage effectivement réalisé et mesurer les niveaux avant connexion :

- Par défaut, interface externe **non inversante**, côté ESP limité à 3,3 V,
  GPIO en drain ouvert. STOP logique 0 doit donner STOP variateur bas.
- `--inverted` : un NMOS externe par ligne, source à GND, drain à DIR ou STOP,
  grille au GPIO. Le GPIO est en push-pull 3,3 V ; niveau GPIO haut donne
  niveau variateur bas. Tirer la grille du NMOS STOP à 3,3 V par 10 kΩ pour
  maintenir STOP bas pendant le reset tant que ce rail est alimenté.

Le RC de banc est GPIO PWM → 1 kΩ → VR, avec 2,2 µF vers GND sur VR et un
rappel 10 kΩ vers GND **côté variateur**. Pleine échelle électrique environ
3 V, à vérifier sous charge ; elle ne représente pas une vitesse étalonnée.
Les masses de l'ESP et des interfaces sont communes. EL n'est pas piloté.
Le comportement en absence d'alimentation logique reste à vérifier matériellement.

## Compiler et téléverser

Sur le Mac, ESP-IDF v5.5 est installé dans `~/esp/esp-idf-v5.5`. Le raccourci
`get_idf`, disponible dans un nouveau terminal, active son environnement.
Installation selon la [notice officielle Espressif](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32/get-started/linux-macos-setup.html).
Le script Mac l'active automatiquement ; depuis la racine du dépôt :

```bash
./tools/flash_motion_mac.sh bench4 --count 4
./tools/flash_motion_mac.sh bench4 --count 4 --flash --port <port-USB>
```

La première commande compile seulement ; la seconde téléverse. `--count`
configure les premiers emplacements ; il ne détecte pas les roues présentes.
Les profils `front`,
`rear`, `--inverted` et `--transport can` fonctionnent aussi avec ce raccourci.

Depuis la racine du dépôt, après chargement de l'environnement ESP-IDF :

```bash
. <installation-esp-idf-v5.5>/export.sh
python3 tools/flash_motion.py front
python3 tools/flash_motion.py rear
python3 tools/flash_motion.py bench4 --count 3
```

Chaque profil, transport, nombre de sorties et type d'interface a son propre
répertoire sous `firmware/esp32_motion/build/`. Le programme régénère son
`sdkconfig` depuis les valeurs versionnées à chaque exécution : pas de rôle
avant conservé par erreur dans une compilation arrière, ni d'ancien défaut
masquant une modification du watchdog. Pour modifier un réglage permanent,
modifier les defaults versionnés ; les changements manuels de ce `sdkconfig`
généré sont écrasés.

Identifier physiquement les deux ports avant de flasher, puis :

```bash
python3 tools/flash_motion.py front --flash --port <port-ESP-avant>
python3 tools/flash_motion.py rear --flash --port <port-ESP-arriere>
```

Ajouter `--inverted` pour les NMOS externes inversants. Ajouter `--transport can`
quand les transceivers sont câblés. Pour une seule roue sur un essieu, utiliser
`--count 1` : elle occupe le **premier** emplacement local (m0 ou m2). Pour
une roue droite seule, déplacer provisoirement son câblage sur cet emplacement
et consigner l'écart dans le relevé du banc.

Avec l'avant droit déconnecté, conserver `--count 4` et les indices fixes.
Les roues présentes sont m0, m2, m3 : masque 13 (1 + 4 + 8). Pour les premiers
essais, autoriser séparément 1, 4 et 8 ; garder m1 à zéro. `--count 3` serait
adapté à un câblage regroupé sur les sorties 0, 1, 2, qui est un autre montage.
Après remontage de la quatrième roue : masque 15.

**Protocole 0.2.0.** Reconstruire le workspace ROS et reflasher le nœud IMU
quand il est utilisé avec ce workspace : le hash est commun à tout le dépôt.
Les captures anciennes restent décodables, mais l'ancien outil de commande
ne valide pas MOTOR_SESSION et ne peut plus armer ce firmware.

## Self-test et diagnostics

Le firmware initialise toutes les sorties à l'arrêt et interdit les moteurs.
Avant cette initialisation, pendant le reset, leur état dépend des rappels et
de l'interface électrique du banc.

| Bit | Contrôle réellement effectué |
|---|---|
| CONFIG, 0x01 | Indices, GPIO valides et distincts, réservations flash/console/CAN, limites finies |
| GPIO, 0x02 | Configuration DIR/STOP, écriture puis lecture des niveaux GPIO de repos |
| PWM, 0x04 | Initialisation LEDC, fréquence 20 kHz et lecture de chaque duty à zéro |
| TASK, 0x08 | Création de la tâche 200 Hz et inscription au task watchdog ESP-IDF |
| LINK, 0x10 | Initialisation du transport, files et tâches de liaison |

Attendu : `passed=31` (0x1F), `failed=0`, `output_errors=0`. Un défaut de
périphérique inhibe l'armement jusqu'au redémarrage. Le watchdog de tâche est
réglé à 2 s avec panic/reset ; il ne remplace pas le watchdog matériel externe.

Ces contrôles vérifient les périphériques et le logiciel. Ils ne prouvent pas
la tension VR au connecteur, la présence du variateur, le mouvement, le sens
mécanique ou le freinage. `configured_mask` décrit la configuration compilée,
**pas une détection automatique de la roue manquante**. Les contrôles physiques
restent dans la recette ci-dessous.

Les états, diagnostics et heartbeats sont publiés à 10 Hz :

| | Avant ou banc4 | Arrière |
|---|---|---|
| Consignes appliquées | MOTOR_STATE, 0x1A0 | MOTOR_STATE_REAR, 0x1A1 |
| Self-test / compteurs | MOTOR_DIAG_FRONT, 0x1A2 | MOTOR_DIAG_REAR, 0x1A3 |
| État / uptime / hash | HEARTBEAT_MOTION_FRONT, 0x702 | HEARTBEAT_MOTION_REAR, 0x703 |

Les quatre valeurs sont toujours ordonnées m0, m1, m2, m3. Les positions non
locales restent nulles. L'état renvoie une consigne électrique après limites,
pente et autorisations ; **il ne renvoie aucune vitesse mesurée**. Les erreurs
de sortie rendent cette consigne non fiable : lire `OUTPUT_FAULT` et le compteur.

READY signifie logiciel initialisé, sorties interdites. ACTIVE signifie
armement accepté, y compris à consigne zéro. DEGRADED signale un arrêt logiciel
ou une perte de commandes après armement. FAULT signale un self-test ou une
sortie en échec. `PROTOCOL_BLOCKED` précise qu'aucune session concordante n'a
encore été reçue, même si les périphériques sont prêts.

Sur CAN, les journaux restent sur la console locale : le LOG commun du banc
série n'est pas utilisé par deux émetteurs concurrents. Les diagnostics gardent
leurs identifiants distincts. LINK_PONG est une réponse à une cible explicite.

## Armement et comportement en défaut

L'ordinateur valide le hash reçu puis envoie MOTOR_SESSION avec l'identité
cible et le même hash. Le firmware vérifie aussi ce hash. Ensuite :

1. Envoyer une MOTOR_CMD à zéro, répétée à 50 Hz.
2. Attendre une télémétrie fraîche avec sorties nulles et self-test réussi.
3. Envoyer MOTOR_ENABLE avec magic 0xEB et le masque voulu.
4. Attendre le masque confirmé, puis envoyer les consignes à 50 Hz.

Le firmware rejette les DLC incorrects, les gardes incorrectes, les masques
hors b0..b3 et les consignes hors [-1,1]. Une commande invalide ne rafraîchit
pas le watchdog. Les roues de l'autre essieu sont filtrées.

Défauts et réglages du banc :

- Plus de 500 ms sans commande valide : consignes nulles, STOP bas et
  **désarmement mémorisé**. Le retour de liaison ne réarme jamais.
- Arrêt logiciel : consignes nulles et désarmement, réarmement explicite à zéro.
- Défaut de sortie : tentative de STOP/PWM zéro sur toutes les sorties,
  défaut mémorisé, redémarrage requis.
- Bus-off observé : arrêt logiciel mémorisé, même après reprise automatique du CAN.
- Limite de duty par défaut : 0,25. Une demande supérieure est limitée et
  `LIMITED` est publié. Ce n'est ni 25 % d'une vitesse mesurée ni une limite de courant.
- Accélération : 2 unités/s. Réduction et coupure sans rampe logicielle ; le RC
  et la mécanique ont leur propre délai.
- Inversion : passage à zéro, DIR conservé et pause de 250 ms avant inversion.
  **Cette pause ne démontre pas que la roue est arrêtée.** Sans Hall, attendre
  l'immobilisation mécanique avant de demander l'autre sens.

Le traitement logiciel se fait au prochain cycle de 5 ms sous ordonnancement
normal. STOP donne la roue libre, pas un freinage garanti. Les essais se font
roues levées, avec une coupure de puissance accessible. La chaîne matérielle
`/SAFE` / EL / contacteur reste à réaliser et à valider sur les cartes.

## Vérifier sans ROS

Dépendances : `pyyaml`, `pyserial` ; pour SocketCAN sous Linux, `python-can`.

```bash
python3 tools/motor_bench.py --device <port-avant> --self-test --report <resultat-avant.json>
python3 tools/motor_bench.py --device <port-arriere> --node rear --self-test --report <resultat-arriere.json>
```

`--self-test` observe sans envoyer de commande ou d'armement et retourne un
code non nul si la télémétrie est absente, périmée, incohérente, en erreur ou
si les sorties sont actives. Par défaut, l'outil **ne demande plus de reset**
à l'ouverture USB (`--no-reset` reste accepté). `--reset` demande explicitement
un redémarrage : l'utiliser uniquement puissance moteur coupée. Le circuit
USB-série et son pilote peuvent encore produire des transitions à l'ouverture ;
les rappels matériels restent nécessaires pendant un reset ou une coupure USB.

L'acquisition de la télémétrie est limitée à trois secondes, puis l'outil
observe pendant la durée `--seconds`. Les octets du bootloader, émis à une
autre vitesse sur UART0, restent visibles dans `decoder_acquisition`.
`decoder_observation` compte la période synchronisée : toute erreur de CRC,
format ou débordement pendant cette période fait échouer le test. Le verdict
global est `exit_code: 0`, pas seulement `healthy: true`.

`healthy` décrit la fraîcheur de la télémétrie et le self-test. Il ne signifie
pas que l'armement est autorisé. `session_ready` exige en plus la confirmation
de MOTOR_SESSION et d'une commande fraîche dans les deux retours STATE et
DIAG. Avant l'armement, le script répète uniquement SESSION et les commandes
zéro jusqu'à cette confirmation. Les premiers paquets perdus pendant le boot
ne doivent pas conduire à une tentative d'armement prématurée. Le firmware
attend aussi l'installation du traitement des commandes avant sa première
publication d'état.

Sur le Mac, avant ROS, depuis la racine du dépôt :

```bash
source ~/esp/esp-idf-v5.5/export.sh
python3 tools/motor_bench.py --device /dev/cu.usbserial-0001 --self-test --seconds 10 --report firmware/esp32_motion/build/mac-self-test.json
python3 tools/motor_bench.py --device /dev/cu.usbserial-0001 --enable 0 --duty 0 0 0 0 --seconds 3 --report firmware/esp32_motion/build/mac-zero-test.json
```

Remplacer le port si nécessaire. La seconde commande vérifie les commandes
zéro et le retour de désarmement sans autoriser une roue. Attendre
`exit_code: 0` et `shutdown_confirmed: true`. Ensuite seulement, roues levées
et interface électrique vérifiée, essayer une roue à la fois :

```bash
python3 tools/motor_bench.py --device /dev/cu.usbserial-0001 --enable 1 --duty .1 0 0 0 --seconds 3
python3 tools/motor_bench.py --device /dev/cu.usbserial-0001 --enable 4 --duty 0 0 .1 0 --seconds 3
python3 tools/motor_bench.py --device /dev/cu.usbserial-0001 --enable 8 --duty 0 0 0 .1 --seconds 3
```

Ces trois essais laissent l'avant droit (m1) interdit. Vérifier le mouvement
physique, le sens et l'arrêt ; les retours actuels ne mesurent pas la rotation.

### Diagnostic de sélection des sorties

Les quatre canaux LEDC sont indépendants et partagent uniquement le timer
de fréquence. Une seule tâche effectue les écritures. À chaque cycle de 5 ms,
le firmware relit les rapports cycliques LEDC du cycle précédent et les pads
STOP. Un écart avec les écritures attendues déclenche un défaut mémorisé et
l'arrêt de toutes les sorties. Les sorties inactives sont réécrites à zéro
avant la mise à jour des sorties actives.

`applied_m0..m3` est maintenant calculé depuis les registres PWM relus, avec
le signe de la commande écrite. Ce retour peut avoir un cycle de retard et
ne vérifie ni la tension VR après l'interface, ni la rotation. Le masque
`stop_gpio_high` est celui des niveaux physiques côté ESP, avant l'interface ;
sa polarité dépend donc de `--inverted`.

Après téléversement de cette version, exemple de relevé pour m3 seul :

```bash
python3 tools/motor_bench.py --device /dev/cu.usbserial-0001 --enable 8 --duty 0 0 0 .1 --seconds 3 --logs --report firmware/esp32_motion/build/m3-diagnostic.json
```

Le journal doit contenir `readback pwm=[0,0,0,102]` au plateau (PWM sur 1023).
Pour l'interface non inversante, `stop_gpio_high=0x08` est attendu ; pour les
NMOS inversants, `0x07`. Les GPIO STOP d'une interface non inversante doivent
avoir un rappel externe côté 3,3 V pour pouvoir être relus au niveau haut.
Un arrêt pour `readback ... stop=0/1` peut révéler ce rappel absent.
Le script interrompt aussi l'essai si les retours signalent une roue non
commandée active ou un sens contraire. Le rapport conserve les pics observés
dans `peak_applied` et les derniers journaux dans `esp_logs`, même après l'arrêt.

Ces contrôles améliorent le diagnostic ; ils ne prouvent pas la cause des
mouvements inattendus observés sur le banc. Le test hôte `test_motor_outputs`
exécute le code de sortie réel avec GPIO/LEDC simulés, y compris des erreurs
de lecture et d'écriture. La validation électrique et mécanique reste à faire.

Mouvement bref d'une seule roue, 0,10 de consigne, trois secondes :

```bash
python3 tools/motor_bench.py --device <port-avant> --enable 1 --duty .1 0 0 0
python3 tools/motor_bench.py --device <port-arriere> --node rear --enable 4 --duty 0 0 .1 0
python3 tools/motor_bench.py --device <port-banc4> --enable 1 --duty .1 0 0 0
```

L'outil attend la validation et l'acquittement de l'armement avant de demander
le mouvement. À la sortie, il tente trois désarmements et commandes zéro. Le champ
`shutdown_confirmed` indique si une télémétrie fraîche a confirmé le
désarmement à zéro. Si le câble est coupé, le timeout firmware prend le relais ; l'outil ne prétend
pas avoir confirmé un arrêt sur une liaison perdue.

CAN après configuration de `can0` à 500 kbit/s :

```bash
python3 tools/motor_bench.py --transport can --interface can0 --node rear --self-test
```

**Un seul producteur de commandes sur le bus.** MOTOR_CMD et MOTOR_ENABLE
portent les quatre roues et sont diffusés : ne pas lancer deux outils de
commande sur le même CAN. Le script est un outil de recette d'un nœud à la
fois ; il ne constitue pas encore un superviseur ROS unique des deux essieux.

## ROS et Foxglove

### Préparer l'ordinateur de contrôle

L'archive locale `firmware/esp32_motion/build/transfer/retriever-motor-bench-source.tar.gz`
contient les sources actuelles, y compris les modifications non commitées,
sans ESP-IDF ni fichiers de compilation. La copier sur le calculateur Ubuntu
équipé de ROS 2 Jazzy, puis l'extraire dans un dossier dédié :

```bash
mkdir -p ~/retriever-motor-bench
tar -xzf <chemin-archive> -C ~/retriever-motor-bench
cd ~/retriever-motor-bench/ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -y
colcon build --symlink-install --packages-up-to retriever_bringup
cd ..
```

`rosdep` doit être initialisé sur le calculateur. Pour ouvrir la liaison avec
un ESP qui pilote les quatre roues, utiliser son port USB persistant :

```bash
./tools/run_motor_bench_ros.sh bench4 /dev/serial/by-id/<identifiant-ESP>
```

Pour deux ESP sur deux ports USB :

```bash
./tools/run_motor_bench_ros.sh axles <port-avant> <port-arriere>
```

Les profils `front` et `rear` lancent un seul essieu. Ce raccourci charge ROS
et le workspace, puis ouvre la liaison et les diagnostics sans armer les
moteurs. Ajouter `foxglove:=false` pour lancer sans affichage Foxglove.
Les essais de mouvement et leur relevé viennent après la recette électrique.

### Commandes et retours

Le pont accepte `link.peer: motion_front` et `link.peer: motion_rear`. Il envoie
MOTOR_SESSION, décode les retours de son essieu et publie
`retriever/motor_state` (avec `node_id`) et `retriever/motor_diagnostics`.
Le panneau Diagnostics reprend le self-test, l'âge et les compteurs.

```bash
ros2 launch retriever_bringup bench_motors.launch.py device:=<port-avant>
ros2 launch retriever_bringup bench_motors.launch.py device:=<port-arriere> peer:=motion_rear
```

Ces commandes alternatives testent **un essieu à la fois**. Pour deux ESP en
USB simultanés, la launch `bench_axles.launch.py` sépare leurs retours tout en
leur fournissant une commande commune. Le banc4 garde le layout Foxglove
existant. Exemple pour les deux ports :

```bash
ros2 launch retriever_bringup bench_axles.launch.py front_device:=<port-avant> rear_device:=<port-arriere>
```

Les commandes restent `/retriever/motor_command`, `/retriever/motor_enable` et
`/retriever/estop`. Les retours sont `/retriever/front/motor_state` et
`/retriever/rear/motor_state`, avec les diagnostics dans les mêmes préfixes.
Publier la commande à 50 Hz : cette launch coupe la consigne ROS après 0,5 s
sans message. Pour armer les deux essieux, publier des zéros, puis masque 15.

Le pilotage CAN simultané des deux essieux par un superviseur unique
et le contrôle fermé avec Hall restent une étape suivante.

## Recette physique à relever

Consigner le port, le profil, le hash, le câblage, le sens mécanique, les niveaux
mesurés et le résultat pour chaque essai. Aucun de ces résultats n'est acquis
par la seule compilation.

1. Sans puissance moteur : GPIO côté ESP ≤3,3 V, STOP côté variateur bas au
   démarrage/reset, VR zéro. Vérifier la polarité de l'interface DIR/STOP.
2. Self-test sur chaque ESP : bits 0x1F, aucun échec, hash concordant ; masque
   3 pour l'avant, 12 pour l'arrière, ou 7 pour le banc à trois roues.
3. Roues levées, tester une roue à la fois à 0,10 : bon moteur, bon sens,
   tension VR cohérente. Le sens peut dépendre du câblage moteur ; consigner
   les inversions nécessaires avant utilisation d'une commande de déplacement.
4. Arrêt explicite : mesurer STOP bas et VR qui revient à zéro. Vérifier les
   autres roues et mesurer le délai électrique, puis la décélération réelle.
5. Couper le flux de commandes ou débrancher l'USB : après 500 ms plus un
   cycle de contrôle, STOP bas. Reconnecter **sans reset**, envoyer une nouvelle
   consigne et vérifier l'absence de redémarrage. Zéro puis réarmement requis.
6. Tester reset, absence de variateur et quatrième roue non câblée : le
   self-test logiciel ne doit pas être interprété comme une présence physique.
7. Après câblage CAN : identifier les deux nœuds, vérifier les retours distincts,
   puis perte de bus / reprise sans réarmement. Ne pas simuler un défaut en
   court-circuitant un GPIO ni en appliquant 5 V à l'ESP.
8. Endurance dix minutes : états/diagnostics/heartbeats à environ 10 Hz,
   compteurs de rejet, liaison et sortie stables ; conserver le relevé JSON
   ou l'enregistrement ROS. La vitesse réelle demande un retour Hall.

## Vérifications automatisées

```bash
make -C firmware/test
python3 tools/check_protocol_sync.py
python3 -m unittest discover -s tools/tests
```

Le même moteur de règles C est compilé dans le firmware et dans les tests
hôte. Les tests couvrent armement à zéro, validation du hash, mapping des
essieux, perte de consigne entre deux cycles, absence de reprise automatique,
limite, rampe, inversion, arrêt et données invalides. La CI compile les profils
avant, arrière et banc sur les transports série et CAN.
