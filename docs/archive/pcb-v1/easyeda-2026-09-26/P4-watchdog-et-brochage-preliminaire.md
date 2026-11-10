# P4 — revue du watchdog et inventaire ESP32

**État au 28 septembre 2026 : réseau de temporisation nominale de 1 s et rappel RSTn de 100 kΩ câblés et vérifiés dans la netlist, mais watchdog fonctionnel et essais au banc encore incomplets.** La [source native actuelle](P4-watchdog-RST-pullup-reviewed-2026-09-28.epro2), la [netlist](Netlist_Power_Interface_P4_RST_pullup_2026-09-28.enet) et le [DRC](DRC_Power_Interface_P4_RST_pullup_2026-09-28.txt) documentent cet état. Les propositions ci-dessous ne sont pas une BOM approuvée.

Au cours de cette passe, le connecteur CAN provisoire `J13` a été exclu de la conversion PCB dans EasyEDA. La source intermédiaire est `P4-J13-excluded-2026-09-28.epro2` et sa netlist `Netlist_Power_Interface_P4_J13_excluded_2026-09-28.enet` ; le raccordement du watchdog a été effectué ensuite.

### Avancement natif vérifié le 28 septembre

Deux composants fournisseurs 0603 ont été ajoutés puis placés sous U8 dans EasyEDA. La feuille a été enregistrée ; elle a été rouverte après redémarrage de l'application et les composants étaient toujours visibles. L'archive native de la feuille passe le contrôle d'intégrité ZIP et contient les enregistrements suivants :

| Repère | Valeur | Référence fabricant / fournisseur | Position du symbole |
|---|---:|---|---|
| R_WD1 | 7,15 kΩ, ±1 % | UNI-ROYAL 0603WAF7151T5E / LCSC C25980 | (330, −420) |
| R_WD2 | 19,1 kΩ, ±1 % | UNI-ROYAL 0603WAF1912T5E / LCSC C22897 | (330, −380) |

La [table 3 du TPL5010](https://www.ti.com/lit/ds/symlink/tpl5010.pdf) donne précisément cette paire **en parallèle** pour une temporisation nominale de 1 s (équivalent 5,202 kΩ). Les stocks constatés dans la bibliothèque EasyEDA au moment de la sélection étaient respectivement 8 600 / 8 678 et 43 200 / 65 446 (LCSC / JLCPCB) ; ils peuvent changer. La netlist actualisée contient 204 composants PCB contre 202 avant placement, soit uniquement R_WD1 et R_WD2 en plus. Les `pinInfoMap` des 202 composants antérieurs sont identiques. U8.3 DELAY/M_RST reste sans réseau ; R_WD2.1 et R_WD2.2 aussi. R_WD1.1 et R_WD1.2 portent chacun un **réseau orphelin distinct** (`$4N47` et `$4N46`) issu de fils de longueur nulle dans la source native ; ils ne rejoignent ni U8 ni GND. **Ne pas déduire une temporisation de 1 s du seul placement ou de ces deux réseaux.**

**Attribut fournisseur de U8 :** dans l'archive native du 28 septembre, le device TPL5010DDCR / C473912 de la bibliothèque porte `Value = -`, alors que l'instance U8 surcharge ce champ avec `Value = TPL5010`. Le symbole, l'empreinte et la référence fournisseur restent ceux du device. Le DRC actuel signale toujours une différence d'attributs avec la pièce fournisseur. L'onglet de normalisation EasyEDA classe U8 comme « Undetermined » et recommande **la même** référence TPL5010DDCR / C473912 et **la même** empreinte, avec le commentaire `-` à la place de `TPL5010` ; la surcharge de libellé explique donc l'écart visible, sans démontrer une erreur de pièce ou de brochage. Ne pas remplacer le device ni effacer le libellé utile sans vérifier l'effet sur le schéma et la BOM. Les 28 points de test sans référence d'achat sont, eux, classés dans « Allocation number » ; ce classement ne qualifie pas leurs empreintes.

**Empreinte de U8 :** les six pads de l'empreinte embarquée sont numérotés 1 à 6. Leurs dimensions internes, converties depuis les unités de l'archive, donnent **1,10 × 0,60 mm**, un pas de **0,95 mm** sur chaque rangée et **2,70 mm** entre axes des rangées. Ces valeurs correspondent à l'[exemple de land pattern TI pour le boîtier DDC0006A](https://www.ti.com/lit/ds/symlink/tpl5010.pdf), pages 23–24 ; la référence TPL5010DDCR est bien donnée en SOT-23-THIN DDC à six broches. Ce contrôle géométrique ne remplace pas une revue de l'orientation, des masques, de la pâte et du routage du PCB.

**Raccordement tenté ensuite dans EasyEDA :** l'export [netlist après saisie des étiquettes](Netlist_Power_Interface_P4_watchdog_delay_2026-09-28.enet) conserve les **192 composants** de l'export P2 final. Seuls les `pinInfoMap` de U8 et R_WD1 ont changé : U8.3 et R_WD1.1 portent `WD_DELAY_1S`, R_WD1.2 porte `GND`. Malgré deux étiquettes visibles `WD_DELAY_1S` et `GND` sur R_WD2 et leur présence dans son formulaire « Fan Out Netlabel », **R_WD2.1 et R_WD2.2 restent sans réseau dans la netlist**. Le [DRC réexporté](DRC_Power_Interface_P4_watchdog_delay_2026-09-28.txt) confirme leur flottement ; il donne 0 erreur fatale, 0 erreur, 28 avertissements et 61 informations. Les anciens réseaux orphelins `$4N46`/`$4N47` ont disparu. La temporisation de 1 s **n'est donc toujours pas matériellement représentée**. Il faut résoudre l'écart entre affichage et connectivité native avant de poursuivre U8.

La [copie native de cet état partiel](P4-watchdog-delay-partial-2026-09-28.epro2) tranche l'ambiguïté : elle contient les fils de U8.3 et de R_WD1, mais **aucun enregistrement `WIRE` aux bornes de R_WD2**. Après fermeture puis réouverture de P4, les étiquettes visuelles de R_WD2 avaient disparu. Une seconde saisie, broche par broche et validée avec Entrée, a produit des modifications enregistrées.

**Contrôle final de cette passe :** la [nouvelle netlist](Netlist_Power_Interface_P4_RWD2_2026-09-28.enet) attribue `WD_DELAY_1S` à U8.3, R_WD1.1 et R_WD2.1, puis `GND` à R_WD1.2 et R_WD2.2. Elle contient toujours 192 composants ; le seul changement de `pinInfoMap` depuis l'export partiel concerne R_WD2. La [source native actuelle](P4-watchdog-delay-reviewed-2026-09-28.epro2) passe le contrôle d'intégrité ZIP, contient deux fils partant des bornes R_WD2 `(310, −380)` et `(350, −380)` avec les mêmes étiquettes, et porte la note de statut actualisée. Le [DRC réexporté](DRC_Power_Interface_P4_RWD2_final_2026-09-28.txt) ne signale plus R_WD2 ni `WD_DELAY_1S` ; il affiche 0 erreur fatale, 0 erreur, 24 avertissements et 65 informations. La résistance équivalente nominale est **5,202 kΩ**, valeur que la table TI associe à **1 s**. Ce contrôle établit la connectivité schématique du délai, sans prouver la tolérance temporelle réelle ni le fonctionnement du watchdog.

**Rappel RSTn ajouté ensuite :** R_WD_RST est une UNI-ROYAL `0603WAF1003T5E`, 100 kΩ ±1 %, empreinte R0603, fournisseur LCSC `C25803` (Basic Part), retenue après vérification dans la bibliothèque EasyEDA. La [netlist actualisée](Netlist_Power_Interface_P4_RST_pullup_2026-09-28.enet) place U8.6 et R_WD_RST.1 sur `WD_RST_N`, puis R_WD_RST.2 sur `+3V3`. Elle contient 193 composants : par rapport à la précédente, seule R_WD_RST a été ajoutée et seul le `pinInfoMap` de U8 a changé. La [nouvelle archive native](P4-watchdog-RST-pullup-reviewed-2026-09-28.epro2) passe le contrôle ZIP, contient la résistance et les étiquettes, et met à jour la note visible de P4. Le [DRC de cette étape](DRC_Power_Interface_P4_RST_pullup_2026-09-28.txt) ne cite ni U8.6 ni R_WD_RST comme broche flottante et donne 0 erreur fatale, 0 erreur, 27 avertissements, 60 informations dans le fichier exporté. Les avertissements restants concernent notamment les broches ouvertes et réseaux à une seule broche des sous-circuits inachevés, ainsi que le libellé fournisseur de U8. Le nombre d'avertissements ne mesure pas seul la progression : les groupes de broches flottantes varient entre deux exécutions du DRC. DONE, WAKE et le chemin matériel jusqu'à `SAFE_N` et `ESP_EN` restent à concevoir et câbler.

## 1. Exigence et anomalie électrique

L’architecture `docs/architecture/04-securite-watchdogs-capteurs.md`, §M.1 et cas de panne 5, impose **1 s**, avec reset ESP32 et activation matérielle de `/SAFE`. Le handoff impose que le watchdog reste hors du PCA9555.

L’ancienne spécification électrique `hardware/pcb/safety_power/icd.yaml`, `SAFE_N_spec`, prévoit un pull-up central de **1 kΩ**, un contact NF d’arrêt d’urgence en série et un pull-down central de **10 kΩ**. Cette spécification doit encore être matérialisée sur P4. Ne pas reprendre ses anciens noms de rails sans les rapprocher du handoff courant.

Pour U8, TI spécifie RSTn à **0,3 V maximum sous 1 mA**. La table 3 donne **7,15 kΩ // 19,1 kΩ** pour 1 s. RSTn est bas au démarrage et produit une impulsion de **320 ms typique** lors d’un défaut. DONE exige un front montant, une largeur minimale de **100 ns** et une arrivée au moins **20 ms** avant l’échéance ; seul le premier front de l’intervalle compte. WAKE dure **20 ms typique** et n’est pas émis au début du premier cycle. La résistance de délai est lue au démarrage. Un pull-up RSTn de **100 kΩ** est recommandé. Source : [TI TPL5010, §7.5, §8.3–8.5 et table 3](https://www.ti.com/lit/ds/symlink/tpl5010.pdf).

Avec le pull-up `/SAFE` de 1 kΩ, maintenir 0,3 V demanderait `(3,3 − 0,3) / 1000 − 0,3 / 10000 = 2,97 mA`, hors charges additionnelles. **Le raccordement direct RSTn → `/SAFE` n’a donc pas de niveau bas garanti par cette spécification.** Le courant absolu maximal d’une broche n’est pas une garantie de fonctionnement à ce courant.

Le rafraîchissement doit attester l’exécution de la boucle de sécurité. Un générateur périodique autonome pourrait continuer à produire DONE pendant un blocage de cette boucle. La période de 1 s ne démontre pas un arrêt en 50 ou 500 ms.

## 2. Interface proposée pour la reprise de saisie

Topologie candidate : **RSTn → inverseur à entrée Schmitt → deux MOSFET N distincts**, drain ouvert vers `SAFE_N` et `ESP_EN`. Les deux lignes ne sont pas reliées entre elles. Le nom `SAFE_N` est proposé pour correspondre à l’ICD ; aucun réseau `/SAFE` fonctionnel n’existe encore dans l’export courant.

| Élément proposé | Raccordement à préparer |
|---|---|
| U8.3 DELAY/M_RST | 7,15 kΩ et 19,1 kΩ, 1 %, en parallèle vers GND : câblé et vérifié dans la netlist ; pas de condensateur ajouté arbitrairement |
| U8.4 DONE | `WD_DONE`, GPIO direct ; pull-down externe 100 kΩ proposé pour définir le reset |
| U8.5 WAKE | `WD_WAKE`, entrée GPIO directe |
| U8.6 RSTn | `WD_RST_N`, pull-up 100 kΩ vers +3V3 : câblé et vérifié dans la netlist |
| Nouveau SN74LVC1G14DBVR | 1 NC, 2 `WD_RST_N`, 3 GND, 4 `WD_FAULT`, 5 +3V3 ; 100 nF local |
| Deux nouveaux DMG1012T-7 | 1 G par résistance 100 Ω depuis `WD_FAULT`, 2 S vers GND, 3 D respectivement vers `SAFE_N` et `ESP_EN` |
| Chaque grille MOSFET | Pull-down externe 100 kΩ vers GND |
| `ESP_EN` | À raccorder à H2.18, aujourd’hui flottant ; relever le circuit EN réel du DevKit avant ajout de sa polarisation ou modification de son condensateur |

Le [SN74LVC1G14](https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf) accepte les fronts lents par son entrée Schmitt. Son boîtier DBV possède le brochage indiqué ci-dessus. À faible charge, son niveau haut est garanti à `VCC − 0,1 V` sous 100 µA. Deux pull-downs de 100 kΩ demandent environ 66 µA à 3,3 V, hors fuites ; la charge capacitive des grilles reste à vérifier pour les transitoires.

**Vérification de bibliothèque EasyEDA du 28 septembre :** la recherche `SN74LVC1G14DBVR` renvoie six références distinctes. La ligne du **fabricant TI** porte LCSC `C7835`, classe Extended Part et empreinte `SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR` ; le symbole prévisualisé affiche 1 NC, 2 A, 3 GND, 4 Y, 5 VCC, en accord avec la fiche TI. La première ligne de résultat, `C434069`, est fabriquée par UMW et ne doit pas être prise pour la pièce TI sur le seul nom de recherche. `C7835` est un candidat identifié, non encore placé ni qualifié pour la BOM finale ; revoir le land pattern et les données d'achat avant conversion PCB.

Le [DMG1012T-7](https://www.diodes.com/datasheet/download/DMG1012T.pdf) est un **SOT-523**, G1/S2/D3, avec RDS(on) maximal de 0,5 Ω à VGS = 2,5 V, dans les conditions de test constructeur. C20512 est déjà identifié pour cette référence sur P1 ; les nouveaux devices, leurs empreintes et leur stock doivent être contrôlés dans EasyEDA avant inclusion dans une BOM. La variante générique ou alternative de P2 ne vaut pas qualification du composant Diodes.

Dans la bibliothèque EasyEDA, la recherche `DMG1012T-7` renvoie cinq pièces de fabricants différents. La ligne **DIODES / C20512** porte une empreinte `SOT-523-3_L1.6-W0.8-P1.00-LS1.6-BR` et la classe Extended Part ; la variante `DMG1012T-7(ES) / C42412320` est d'ElecSuper avec une empreinte et des caractéristiques catalogue différentes. Sélectionner explicitement `C20512` si cette architecture est retenue, puis vérifier ses trois pads et son implantation physique avant la BOM. Aucun de ces MOSFET n'a été ajouté à P4 pendant cette vérification.

À titre d’estimation à température de test, 3,3 mA dans 0,5 Ω donnent environ 1,65 mV. Cette estimation montre l’intérêt d’une sortie tamponnée ; elle ne borne pas les parasites du faisceau, la température ou une panne de composant.

**Ne pas remplacer cette interface par un SN74LVC2G07 directement derrière le pull-up de 100 kΩ sans nouvelle justification.** Ce buffer impose une pente d’entrée maximale de 10 ns/V à 3,3 V ; la montée RC de RSTn peut la dépasser. Le SN74AUP2G07 admet 200 ns/V, mais ne dispense pas d’un calcul de capacité et de courant. Sources : [TI LVC2G07, conditions recommandées](https://www.ti.com/lit/ds/symlink/sn74lvc2g07.pdf), [TI AUP2G07, conditions recommandées](https://www.ti.com/lit/ds/symlink/sn74aup2g07.pdf).

Les résistances de grille et de rappel sont des valeurs proposées pour cette interface, pas des prescriptions TI. Les repères définitifs et références fournisseur restent à attribuer contre toutes les feuilles, y compris les composants exclus de BOM/PCB.

## 3. Ce que cette interface démontre — et ce qui reste ouvert

| Situation | Effet attendu de l’interface proposée | Condition restante |
|---|---|---|
| RSTn bas, +3V3 présent | `WD_FAULT` haut, deux MOSFET conducteurs : SAFE_N et ESP_EN bas | Vérifier niveaux et délais à l’oscilloscope |
| RSTn relâché | MOSFET bloqués ; chaque ligne retrouve sa propre polarisation | Ne constitue pas un acquittement ni un armement |
| Arrêt d’urgence ou fil NF coupé | Pull-up SAFE_N déconnecté, pull-down ramène SAFE_N bas | Circuit NF, protection et faisceau encore à saisir |
| ESP32 absent ou en reset | INP/INP_G doivent rester bas ; la décharge redevient active par défaut | Vérifier état réel des broches et de P1 ; pas de commande de sécurité sur expander |
| +3V3 absent, ESP32 encore alimenté par son DevKit | Watchdog et inverseur hors fonctionnement garanti | SAFE_N doit retomber par sa polarisation passive ; l’inhibition du contacteur ne doit pas dépendre d’un logiciel qui lit cette perte |

**Ne pas autoriser la remontée automatique de SAFE_N à la fin du reset comme preuve d’un réarmement sûr.** Prévoir un maintien inhibé jusqu’à auto-test et acquittement, avec état passif inhibé au reset. L’interface à deux drains seule ne réalise pas ce maintien. Le circuit d’armement et son action sur INP/INP_G restent à concevoir ; ne pas ajouter un latch ou une temporisation au hasard.

Le handoff annonce INP/INP_G bas au reset : le contacteur s’ouvre alors dès le reset ESP32. Cela doit être rapproché de la séquence de freinage et des essais M14/M15 ; on ne peut pas en déduire que le bus reste alimenté une seconde pour freiner. Aucun résultat d’essai ne permet encore de valider cette chaîne.

## 4. Inventaire des connexions et budget de GPIO

Le fichier compagnon `P4-ESP32-header-inventory.csv` est extrait de la **netlist native courante**, sans assignation inventée. H1.8/H1.9 portent déjà GPIO16/GPIO17 pour le BMS gelé. H2.1 (5 V) et H2.18 (EN) sont flottants ; H2.19 (3V3) est relié à +3V3. Le raccordement des GPIO P4 et la correction d’alimentation nécessitent une exception ciblée au gel de P1, où se trouvent les headers. Aucun changement P1 n’a été appliqué.

Les [restrictions Espressif](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html) identifient les broches de strapping, réservent normalement GPIO6–11 à la mémoire et limitent GPIO34–39 aux entrées sans rappels internes. GPIO16/17 peuvent être utilisés par la PSRAM selon le module : le module réel doit être compatible avec le BMS déjà validé. Les interruptions sur GPIO36/39 demandent de tenir compte des restrictions ADC et modes de sommeil radio.

Dans les headers exportés, en réservant GPIO0/2 au boot, GPIO1/3 à l’USB, GPIO6–11 à la mémoire, GPIO12 au strap sensible et GPIO16/17 au BMS, il reste **19 GPIO : 15 capables de sortie et 4 d’entrée seule**. GPIO0/2 apporteraient deux possibilités supplémentaires sous contraintes de démarrage ; ils ne sont pas une réserve libre. Ce décompte n’est pas un brochage final.

| Fonctions P4/P1 à relier directement | Nombre de GPIO proposé pour le budget |
|---|---:|
| SDA/SCL, CAN_TX/CAN_RX | 4 |
| INP, INP_G, DISCH_INH | 3 |
| FLT_I, FLT_T | 2 |
| Lecture et commande drain ouvert de SAFE_N sur une broche commune | 1 |
| Deux PWM de ventilateurs indépendants | 2 |
| WD_DONE, WD_WAKE | 2 |
| Données WS2812B | 1 |
| **Sous-total, hors BMS déjà réservé** | **15** |

Un circuit d’armement peut demander une broche supplémentaire ou changer l’usage de la broche SAFE_N. Un INT du PCA9555 demande aussi une entrée s’il est utilisé. STAT_G, STAT_R, EN_12V, EN_5V, INA_ALERT et les tachymètres sont les seules fonctions autorisées sur l’expander par le handoff §8.7 ; cela ne valide pas encore la mesure de vitesse par lecture I²C.

L’architecture générale mentionne le BNO085, mais sa destination et son interface ne sont pas fixées par le brief P4. **Ne pas ajouter automatiquement ses sept lignes SPI/INT/RESET/PS0 au brochage.** Si elles doivent toutes être directes, le budget passerait à 22 GPIO hors BMS et dépasserait les 19 disponibles sous les réserves ci-dessus. Des straps fixes ou un autre périmètre peuvent changer ce calcul ; la décision doit précéder les connexions finales. Le fichier firmware `board_config.h` de banc n’est pas utilisé comme contrat PCB.

## 5. Suite de la saisie dans EasyEDA

1. Conserver le réseau de délai et le rappel RSTn désormais vérifiés ; confirmer la temporisation effective au banc, avec les tolérances des résistances et du TPL5010.
2. Contrôler le device SN74LVC1G14DBVR, les DMG1012T-7, leurs empreintes et le stock ; attribuer des repères uniques.
3. Saisir l’interface RSTn indépendante des GPIO ; conserver le circuit d’armement explicitement incomplet jusqu’à conception cohérente.
4. Arrêter le contrat H1/H2 et la portée exacte des exceptions P1 avant raccordement du reset et des signaux inter-feuilles.
5. Exporter source native, netlist et DRC ; vérifier broche par broche et comparer les feuilles non modifiées.
6. Mesurer reset, absence de DONE, DONE figé, démarrage, perte +3V3, arrêt d’urgence et retour après défaut. Une netlist connectée ou un DRC sans erreur ne remplacent pas ces essais.
