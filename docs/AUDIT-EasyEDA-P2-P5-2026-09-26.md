# Reprise EasyEDA — audit P2 à P5 du 26 septembre 2026

## Statut

**Conception en cours, non validée pour fabrication ni mise sous tension.** Les composants placés par Luna ne constituent pas des circuits fonctionnels. La connectivité réelle a été contrôlée par export EasyEDA Pro, puis comparée au plan local et aux fiches constructeur.

Projet ouvert : `Husky robot`, schéma `Power Interface`, EasyEDA Pro V3.2.149.88089769, mode Half Offline. Les modifications décrites ci-dessous ont été faites dans l’interface EasyEDA par Computer Use. Ce rapport ne remplace pas le schéma.

Références de conception prioritaires : [HANDOFF-safety_power.md](HANDOFF-safety_power.md) et [PLAN-P2-rails-power.md](PLAN-P2-rails-power.md). Les anciennes spécifications de `hardware/pcb/safety_power` décrivent une architecture différente ; elles ne doivent pas annuler les décisions plus récentes. Le fichier `PLAN-composants-par-feuille.md` préexistant est conservé sans modification.

## Preuves de connectivité

Les exports sont conservés dans [reviews/2026-09-26](reviews/2026-09-26/). Une netlist ne contient ici que les composants convertibles vers le PCB ; elle ne recense donc pas tous les brouillons visibles.

| Feuille | Composants dans la netlist initiale | Broches raccordées initialement | Netlist de référence du 26 septembre | État |
|---|---:|---:|---:|---|
| P1 | 128 | 288 / 322 | 288 / 322 | Connectivité préservée |
| P2 | 48 | 30 / 148 | 61 / 150 | P2-A repris ; P2-B incomplet |
| P3 | 15 | 0 / 30 | 22 / 22 | Distribution câblée ; protections et diagnostic incomplets |
| P4 | 14 | 0 / 73 | 29 / 65 | Bases et U6 corrigé câblés ; interfaces et sécurité incomplètes |
| P5 | 4 | 0 / 17 | 0 / 17 | Brouillon non câblé, dépend de M15 |

La netlist ultérieure `Netlist_Power_Interface_P2A_iso_2026-09-26.enet` contient 210 composants, dont la résistance réelle ajoutée `R_ESP_ISO`. Ses broches ont été vérifiées : `1 → ESP_5V_D`, `2 → ESP_5V`.

La comparaison des 128 composants de P1 entre les exports initial et P2-A a confirmé des `pinInfoMap` identiques. La comparaison avec l’export final contenant R_ESP_ISO confirme également leur identité : la connectivité de P1 est inchangée.

Le contrôle initial affichait 0 erreur fatale, 0 erreur, 29 avertissements et 60 informations. Le contrôle relancé à **13:10:57** affiche 0 erreur fatale, 0 erreur, **26 avertissements et 61 informations** dans l’interface ; le pied du fichier exporté compte 59 informations, hors messages de début/fin. U5.4 n’est plus signalé flottant dans cet export. Ces compteurs ne prouvent ni le fonctionnement, ni la sûreté : les feuilles encore flottantes et les composants provisoires restent à traiter.

Autre divergence avec le handoff : U3.2 de P1 est encore signalé flottant par le DRC courant, alors que le marqueur NC est décrit comme déjà posé dans la documentation. Cette exception est à vérifier sur P1 sans changer sa connectivité.

## Passe P3/P4 vérifiée à 13:38:43

Exports natifs : `P3-connected_2026-09-26.epro2`, `P4-foundation_2026-09-26.epro2`, `Netlist_Power_Interface_P3_P4_2026-09-26.enet` et `schDrcLog_P3_P4_2026-09-26.txt`. Les archives source passent le contrôle d’intégrité ZIP. La netlist contient **203 composants** : les quatre fusibles amovibles de P3 ont quitté le PCB, et trois résistances I²C dupliquées de P4 sont exclues du PCB et de la BOM. Les 128 composants P1 et les 49 composants P2 conservent tous leurs `pinInfoMap` de l’export P2-A final.

DRC courant : **0 erreur fatale, 0 erreur, 24 avertissements, 61 informations** dans l’interface. Les avertissements restants ne sont pas masqués par des NC sur des broches destinées à être raccordées. Les schémas restent non fonctionnels en l’état.

### P3 : distribution raccordée

- FH1–FH4 : broche 1 `BUS+`, broche 2 respectivement `MOTOR_1+` à `MOTOR_4+`.
- F1–F4 : mêmes réseaux que leur support, **BOM oui, PCB non**. Le fusible amovible est contenu dans son support ; aucune deuxième empreinte de fusible ne doit être produite sur le PCB.
- J3–J6 : broche 1 respectivement `MOTOR_1+` à `MOTOR_4+`, broche 2 `GND`.
- J7/J8 : broche 1 `+12V_AUX`, broche 2 `GND` ; J9 : broche 1 `+5V_PWR`, broche 2 `GND`.
- Annotation provisoire déplacée dans la zone libre sous les circuits, sans chevaucher le texte historique.

Le [fusible Littelfuse 0997](https://www.littelfuse.com/assetdocs/littelfuse-datasheet-997-mini58v?assetguid=f4bf5724-5a40-4a44-8f08-c52ae959a5ef) et le [support 178.6764.0001](https://www.littelfuse.com/assetdocs/mini-fl1-datasheet?assetguid=86e3ab08-0473-4acb-98d6-4cf3dbe2f0fa) sont annoncés 58 V. La coordination avec les transitoires, le courant de court-circuit réel et la détection de fusible fondu demeure à concevoir. Un moteur qui régénère peut maintenir le nœud aval d’un fusible ouvert : une simple lecture de tension n’établit pas sa continuité.

### P4 : bases raccordées

- PCA9555 U7 : broches 2/3/21 A1/A2/A0 à `GND` (adresse 7 bits **0x20**), 12 à `GND`, 22 `SCL`, 23 `SDA`, 24 `+3V3`. C8 : `+3V3`/`GND`.
- TPL5010 U8 : 1 `+3V3`, 2 `GND`. C13 : `+3V3`/`GND`. Temporisation et signaux de surveillance encore ouverts.
- SN74AHCT125 U9 : 14 `+5V_PWR`, 7 `GND`. C14 : `+5V_PWR`/`GND`. Les entrées/OE et sorties doivent encore être définies.
- R_SDA1, R_SCL1 et R_SDA2 : exclus de BOM/PCB pour éviter le cumul avec les deux tirages 2,2 kΩ de P1.
- À ce stade intermédiaire, U6 SN65HVD230 était non raccordé ; le remplacement et le câblage ultérieurs sont consignés dans la passe CAN ci-dessous.

Ces alimentations ont été vérifiées dans la netlist, pas seulement par proximité visuelle. Les fonctions CAN, watchdog matériel, ventilateurs, LED et `/SAFE` ne sont pas terminées.

## Passe CAN P4 vérifiée à 13:44:56

**U6 est désormais TCAN1042HGVDR / C124014**, remplacé dans le Device Manager natif EasyEDA en conservant U6 et son identifiant, avec le symbole et l’empreinte du nouveau composant. Le composant précédent était encore sans fils avant substitution. La recherche native affichait 168 pièces chez LCSC et JLCPCB au moment du choix ; ce stock n’est pas une réservation.

La [fiche TI TCAN1042HGV](https://www.ti.com/lit/ds/symlink/tcan1042hgv.pdf) donne une tenue aux défauts de bus ±70 V. Le suffixe V apporte l’alimentation logique VIO distincte. Connexions vérifiées : 1 `CAN_TX`, 2 `GND`, 3 `+5V_HOT`, 4 `CAN_RX`, 5 `+3V3`, 6 `CANL`, 7 `CANH`, 8 `GND`. STB à GND fixe le mode normal. C15 = 100 nF sur `+5V_HOT`, C16 = 100 nF sur `+3V3`, chacun vers GND. Ajouter la capacité de réserve 4,7 µF recommandée près de VCC ; réserver jusqu’à 80 mA au budget du rail HOT en fonctionnement dominant à forte charge. Ces alimentations permettent de conserver le CAN lorsque BUS+ est coupé, sous réserve du rail HOT fonctionnel.

R10 générique non utilisé est exclu de BOM/PCB. Le texte d’inventaire P4 a été remplacé par un état actuel. La netlist `Netlist_Power_Interface_P4_CAN_2026-09-26.enet` contient 202 composants ; P4 compte 10 composants PCB et 29/65 broches nommées. P1, P2 et P3 conservent strictement leurs connexions de la passe précédente. `P4-CAN-reviewed_2026-09-26.epro2` est la source P4 la plus récente, avec la note mise à jour ; son intégrité ZIP est vérifiée.

DRC `schDrcLog_P4_CAN_2026-09-26.txt` : **0 erreur fatale, 0 erreur, 28 avertissements et 61 informations** affichés (59 informations au pied du fichier). Les quatre avertissements supplémentaires concernent CANH, CANL, CAN_RX et CAN_TX : chaque réseau ne touche encore que U6, car le connecteur et les GPIO ne sont pas raccordés. Ils sont conservés comme travaux à finir, sans masquer le problème par des marqueurs NC.

Le CAN demeure incomplet : connecteur réel, protection contre les transitoires coordonnée avec le défaut batterie, terminaison selon topologie, capacité bulk, retour de masse et contrat GPIO final. La tenue ±70 V du transceiver ne suffit pas à valider les autres composants du faisceau ni à prouver une communication au-delà du domaine de mode commun recommandé.

### Correction du connecteur CAN provisoire — 28 septembre

La netlist post-placement du watchdog incluait encore `J13` (`gge225`) parmi les composants à convertir en PCB, alors que ce connecteur générique 3 broches n'a ni référence fabricant ni brochage de faisceau validé. Dans EasyEDA, `Convert to PCB` a été changé de **Yes** à **No** et la feuille P4 enregistrée. La source [P4-J13-excluded-2026-09-28.epro2](reviews/2026-09-26/P4-J13-excluded-2026-09-28.epro2) passe le contrôle d'intégrité ZIP et porte `Convert to PCB=no` pour `J13` ; `Add into BOM=no` est conservé. La [nouvelle netlist](reviews/2026-09-26/Netlist_Power_Interface_P4_J13_excluded_2026-09-28.enet) contient **203 composants contre 204**, avec `J13` comme seul identifiant supprimé. Aucun `pinInfoMap` ni autre propriété des 203 composants conservés n'a changé. Le symbole J13 reste visible pour préparer le futur choix d'un connecteur qualifié.

## Corrections appliquées et vérifiées sur P2

- `C26` est désormais exclu du PCB et de la BOM : c’est un brouillon, pas une pièce définie.
- Une sauvegarde de projet a été lancée sous le nom `Codex_audit_P2_P5_2026-09-26` ; l’opération s’est terminée. Vérifier sa présence dans le gestionnaire de sauvegardes avant une restauration future.
- `L1` était déjà remplacée par **Bourns SRP1038A-470M / C3220907**, 47 µH. La référence réelle a été contrôlée.
- `C3`, `C4`, `C5`, `C6` étaient déjà remplacés par **TDK C3225X7R2A225KT0L0U / C76685**, 2,2 µF / 100 V / X7R / 1210. La référence réelle a été contrôlée.
- Les connexions du LM5164, de son réseau Type 3, des condensateurs, du LDO et de D3 ont été ajoutées et vérifiées par netlist.
- `U4.6 PGOOD` possède déjà un marqueur NC, contrôlé visuellement et dans la source.
- `U5.4 NC` porte maintenant un marqueur NC natif, contrôlé visuellement.
- `R_ESP_ISO` **Uniroyal 0603WAF0000T5E / C21189**, 0 Ω / 0603, a été placée et raccordée entre `ESP_5V_D` et `ESP_5V`. La référence et les deux réseaux sont vérifiés dans l’export.

Une tentative d’édition de source avait remplacé P2 par une portion de texte ; la feuille a immédiatement été restaurée depuis l’historique de **12:37:55**, puis son contenu et ses connexions ont été revérifiés. Les tentatives ultérieures rejetées par « Invalid Data » ont été annulées. EasyEDA a aussi redémarré une fois ; les connexions sauvegardées de P2-A ont été retrouvées après réouverture. Le câblage final de R_ESP_ISO et le NC U5.4 ont été réalisés avec les outils natifs.

### Connexions P2-A confirmées

| Élément | Connexion |
|---|---|
| U4.1, U4.9 EP | GND |
| U4.2 VIN | BUS_RAW+ |
| U4.3 EN/UVLO | UVLO8 |
| U4.4 RON | RON8 |
| U4.5 FB | FB8 |
| U4.6 PGOOD | NC |
| U4.7 BST | BST8 |
| U4.8 SW | SW8 |
| C3–C6 | BUS_RAW+ ↔ GND |
| C7, 2,2 nF | BST8 ↔ SW8 |
| L1, 47 µH | SW8 ↔ +5V_HOT |
| R4, 220 kΩ | SW8 ↔ RIPPLE8 |
| C9, 3,3 nF | RIPPLE8 ↔ +5V_HOT |
| C10, 270 pF C0G | RIPPLE8 ↔ FB8 |
| R5, 41,2 kΩ | RON8 ↔ GND |
| R6, 100 kΩ | +5V_HOT ↔ FB8 |
| R7, 31,6 kΩ | FB8 ↔ GND |
| R8, 1 MΩ | BUS_RAW+ ↔ UVLO8 |
| R9, 68,1 kΩ | UVLO8 ↔ GND |
| C11, C12, 10 µF | +5V_HOT ↔ GND |
| U5.1 VIN, U5.3 EN | +5V_HOT |
| U5.2 | GND |
| U5.4 | NC |
| U5.5 | +3V3 |
| C1, 1 µF | +5V_HOT ↔ GND |
| C2, 1 µF | +3V3 ↔ GND |
| D3.2 A / D3.1 K | +5V_HOT / ESP_5V_D |
| R_ESP_ISO, 0 Ω | ESP_5V_D ↔ ESP_5V |

Le LM5164 n’a pas de broche VCC. Son réseau Type 3 et son bootstrap 2,2 nF correspondent au plan ; ne pas les remplacer par le réseau d’un LM5145. Voir la [fiche TI LM5164](https://www.ti.com/lit/ds/symlink/lm5164.pdf).

Le LDO AP2112K est cohérent pour le rail logique 3,3 V prévu à 100 mA ; la dissipation nominale serait alors ≈0,17 W. Ce calcul ne valide pas un fonctionnement à 600 mA. Voir la [fiche Diodes AP2112](https://www.diodes.com/datasheet/download/AP2112.pdf).

### P2-A reste incomplet

**H2.1**, identifié `5V` dans la netlist, est encore libre sur P1. **H2.19**, identifié `3V3`, est actuellement connecté à `+3V3` sur P1, contrairement au plan d’isolement du régulateur du DevKitC. La correction ciblée a été soumise au propriétaire car P1 est explicitement gelée dans le handoff ; aucune coupure de cette liaison n’a été faite pendant cet audit.

La correction à réaliser est concrète : raccorder H2.1 à `ESP_5V`, isoler H2.19 du rail `+3V3` et poser son NC. Vérifier la variante exacte du module, l’orientation des deux barrettes et le comportement avec USB. Les possibilités d’alimentation sont décrites dans le [guide officiel ESP32-DevKitC](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html).

Il reste aussi à remettre P2-A en page, enlever les étiquettes orphelines identifiées, ajouter les points de test, vérifier la capacité effective de C11/C12 sous polarisation et établir le budget réel de courant de +3V3. Les essais de charge, démarrage, UVLO et branchement USB restent nécessaires.

## P2-B — convertisseurs 12 V / 9 A et 5 V / 5 A

`U11` et `U12` sont des LM5145RGYR / C485912 réels mais toutes leurs broches sont flottantes. Les composants génériques qui les entourent ne représentent pas un dimensionnement terminé.

**Nettoyage vérifié le 28 septembre :** dans EasyEDA, `C17`–`C21`, `C27`, `Q11`, `Q12` et `L11` ont été placés hors BOM et hors conversion PCB. Ces neuf symboles sont des réservations P2 sans référence de fabrication validée. La netlist antérieure montre C17/C20/C21/C27 et Q11 entièrement flottants ; C18/C19, Q12 et L11 ne touchent que des réseaux internes orphelins. `L11` affiche « INDUCTOR_3T » comme champ de référence, qui ne constitue pas une référence fabricant. L'[archive native P2](reviews/2026-09-26/P2-brouillons-exclus-2026-09-28.epro2) passe le contrôle d'intégrité ZIP et porte `Add into BOM=no` ainsi que `Convert to PCB=no` pour chacun des neuf composants. La [netlist après nettoyage](reviews/2026-09-26/Netlist_Power_Interface_P2_placeholders_excluded_2026-09-28.enet) contient **192 composants contre 201** avant cette passe : les neuf identifiants visés sont les seuls disparus. Les propriétés et `pinInfoMap` des 192 composants conservés sont identiques ; les autres sections de la netlist sont inchangées. Les symboles restent visibles sur P2 pour poursuivre le dimensionnement.

**Passe de calcul du 26 septembre, après suspension du Computer Use par verrouillage du Mac :** la [revue P2-B](reviews/2026-09-26/P2B-dimensionnement-preliminaire.md) corrige une erreur importante du handoff : **RT = 33,2 kΩ pour 300 kHz, et non 133 kΩ**. Elle documente l'UVLO 35,68 V ON / 25,68 V OFF, ses tolérances, le conflit entre démarrage à 85 % et précharge exigée à 95 %, ainsi que les courants RMS/crêtes. Un candidat d'inductance réel a été identifié, SRP2313AA-100M / C2045635 ; le candidat MOSFET BSC070N10LS5 / C534362 nécessite encore la vérification de Qg à la tension de commande. Ni placement ni câblage P2-B n'ont été effectués pendant cette passe. Les calculs reproductibles sont enregistrés dans `P2B-preliminary-calculations.json`.

**Correction de composants du 28 septembre :** dans EasyEDA, `R_RT10` et `R_RT11` ont été remplacées par la référence UNI-ROYAL `0603WAF3322T5E` / `C23003`, 33,2 kΩ ±1 %, R0603. Les deux propriétés ont été vérifiées et la sauvegarde confirmée. Le contrôle de bibliothèque indiquait 9 005 pièces JLCPCB à cet instant. Les étiquettes RT amorcées ensuite ne disposent pas encore d'une netlist post-modification ; aucune connexion U11/U12 n'est revendiquée. Voir la [mise à jour de la revue P2-B](reviews/2026-09-26/P2B-dimensionnement-preliminaire.md) avant toute interprétation de l'état électrique.

La [fiche TI LM5145](https://www.ti.com/lit/ds/symlink/lm5145.pdf) impose de résoudre les points suivants avant câblage définitif :

1. Choisir les quatre MOSFET 100 V et valider pertes de conduction, commutation, charge de grille et thermique. La cible du handoff est RDS(on) ≤10 mΩ et Qg ≤30 nC. Le SiR870ADP présent sur P5 ne satisfait pas cette cible de Qg : la [fiche Vishay](https://www.vishay.com/docs/63657/sir870adp.pdf) donne jusqu’à 62 nC à 7,5 V. Il ne constitue donc pas un remplacement automatiquement validé pour P2-B.
2. Choisir les inductances 10 µH avec DCR ≤5 mΩ et marge de saturation pour 9 A / 5 A, en tenant compte de l’ondulation et des tolérances.
3. Définir exactement C_IN/C_OUT : capacité effective, ESR, courant d’ondulation et tenue en tension. Une valeur nominale dans un brouillon ne suffit pas.
4. Calculer une compensation Type III avec le réseau complet requis ; la liste ancienne R_C/C_C1/C_C2 est incomplète pour une réalisation Type III. Ne pas inventer ses valeurs.
5. Définir le soft-start, la limitation de courant par RDS(on) avec sa variation en température, le bootstrap, VCC et les chemins de masse.
6. Recalculer l’hystérésis UVLO. Avec une résistance haute de 1 MΩ et le courant interne d’hystérésis de 10 µA, l’écart induit peut être de l’ordre de 10 V ; le seul seuil de démarrage ≈35,7 V ne suffit pas à valider le comportement.
7. Le double EP a été clarifié par inspection de l'export natif : broche périphérique 15 et pad central 21 sont cohérents avec la fiche TI. Les deux devront être reliés au GND avec AGND/PGND. Dimensions, montage et routage restent à vérifier avant conversion PCB.

## P3 — distribution et fusibles

Les quatre fusibles **0997015.WXN / C207027**, les quatre supports **178.6764.0001 / C142933** et J3–J9 **XY636-6.35-2P / C557968** sont désormais raccordés comme décrit dans la passe P3/P4 ci-dessus. La détection de fusible fondu n’est pas réalisée.

La [fiche Littelfuse MINI 58 V](https://www.littelfuse.com/assetdocs/littelfuse-datasheet-997-mini58v?assetguid=f4bf5724-5a40-4a44-8f08-c52ae959a5ef) confirme la famille 58 V et le calibre 15 A. La [fiche du support MINI FL1](https://www.littelfuse.com/assetdocs/mini-fl1-datasheet?assetguid=86e3ab08-0473-4acb-98d6-4cf3dbe2f0fa) récente donne 58 V, 22 A continus et 30 A maximum pour 178.6764.0001. Ne pas reprendre sans contrôle les anciennes descriptions commerciales à 32 V.

**Contrôle documentaire complémentaire du 28 septembre :** une [ancienne fiche Littelfuse datée de 2016](https://origin-savvis.littelfuse.com/~/media/commercial-vehicle/datasheets/automotive-fuse-holders/mini/littelfuse-fuseholder-mini-fl1-pcb-mount.pdf) donnait **125 V DC** pour le même repère `178.6764.0001`, alors que la fiche fabricant révisée en 2025 donne **58 V DC**. Cette divergence de révision interdit de retenir 125 V pour qualifier l'assemblage actuel sans confirmation explicite du fabricant. De toute façon, le fusible `0997015.WXN` lui-même reste limité à **58 V DC**, avec un pouvoir de coupure annoncé de **1 000 A à 58 V DC** par sa fiche fabricant ; la tenue de l'ensemble ne peut dépasser celle de son élément le moins bien coté.

La tenue de 58 V reste à coordonner avec les surtensions réelles et la protection du bus : le D1 SMCJ48CA de P1 peut écrêter beaucoup plus haut, jusqu’à 77,4 V selon ses conditions spécifiées. Ce constat n’impose pas de modifier P1 ; il impose de fixer l’enveloppe de tension avant de valider les fusibles, borniers et cartes moteur. Vérifier également le courant de court-circuit disponible et le pouvoir de coupure. Une sélectivité ne se déduit pas du seul rapport entre les calibres.

Pour `J3`–`J9`, la [fiche dessinée par XINLAIYA pour XY636-6.35](https://robu-prod-media.s3.ap-south-1.amazonaws.com/uploads/2024/10/R155999.pdf) indique **30 A, 300 V, 26–10 AWG / 4 mm², pas 6,35 mm et serrage 0,5 N·m** ; la [fiche catalogue du code C557968](https://item.szlcsc.com/581054.html) associe ces caractéristiques à la variante 2 pôles `XY636-6.35-2P`. La tension nominale du bornier ne semble donc pas être la limite à 58 V identifiée ci-dessus. Il reste à vérifier son empreinte, l'espacement réel, l'échauffement des contacts et du cuivre, la section du faisceau et le maintien mécanique sur la carte avant validation des sorties de roue.

**F1–F4 sont désormais exclus du PCB, tandis que FH1–FH4 conservent leur empreinte.** Le fusible amovible et son support doivent être représentés comme un seul assemblage physique : valider l’affectation des contacts au support, conserver le fusible dans la BOM, et éviter de générer deux empreintes distinctes par branche. Ne pas créer un contournement électrique du fusible ni placer le support comme un second élément indépendant en série.

Le schéma doit matérialiser pour chaque roue : `BUS+ → fusible → sortie roue`, retour GND et détection de défaut appropriée. J7 est la branche 12 V / 3 A du Youyeetoo X1, J8 la sortie 12 V / 5 A, J9 la sortie 5 V / 3 A. Ne pas ajouter un fusible de tête 40 A en reprenant l’ancienne spécification.

## P4 — commande et périphériques

Les quatre circuits intégrés sont réels. U7/U8/U9 disposent maintenant de leurs alimentations ; leur logique reste incomplète :

| Repère | Référence | Conclusion de revue |
|---|---|---|
| U6 | TCAN1042HGVDR / C124014 | Remplacement et câblage vérifiés ; connecteur, protections et terminaison encore à terminer |
| U7 | PCA9555DBR / C45293 | I²C 3,3 V câblé, adresse 0x20 ; INT et affectation des E/S à définir |
| U8 | TPL5010DDCR / C473912 | Référence réelle ; délai, DONE, WAKE et chemin matériel /SAFE à concevoir |
| U9 | SN74AHCT125DR / C155176 | Cohérent pour convertir un signal logique 3,3 V vers WS2812B alimenté en 5 V |

Le [SN65HVD230](https://www.ti.com/lit/ds/symlink/sn65hvd230.pdf) n’est pas un transceiver résistant à un court-circuit CAN vers la batterie 42 V. Le remplacement retenu et appliqué est TCAN1042HGVDR, détaillé dans la passe CAN ci-dessus. La piste TCAN3413 ±58 V n’a pas été utilisée.

Pour le [PCA9555](https://www.ti.com/lit/ds/symlink/pca9555.pdf), définir A0/A1/A2 par câblage, typiquement 0x20 si les trois sont à GND, et vérifier les autres adresses. P1 possède déjà les résistances `R_SDA` et `R_SCL` de 2,2 kΩ vers +3V3. Les brouillons `R_SDA1`, `R_SCL1`, `R_SDA2` de P4 ne doivent pas être mis en parallèle par défaut. Les commandes critiques et rapides doivent rester sur des GPIO directs.

Pour le [TPL5010](https://www.ti.com/lit/ds/symlink/tpl5010.pdf), la sortie RESET est open-drain et nécessite sa polarisation ; le délai doit être choisi dans la table constructeur. Définir précisément la séquence DONE/WAKE et la manière dont le défaut inhibe matériellement la puissance. Un simple lien vers le reset logiciel ESP32 ne démontre pas la fonction /SAFE. L’avertissement DRC d’attributs de U8 concerne notamment le nom affiché abrégé TPL5010 ; vérifier les propriétés contre le composant fournisseur.

**Revue complémentaire et avancement du 28 septembre :** [watchdog et brochage préliminaires](reviews/2026-09-26/P4-watchdog-et-brochage-preliminaire.md). Les résistances réelles de 7,15 kΩ et 19,1 kΩ ont été placées et sauvegardées sur P4 ; l'[export natif](reviews/2026-09-26/P4-watchdog-resistors-positioned-2026-09-28.epro2) et la [nouvelle netlist](reviews/2026-09-26/Netlist_Power_Interface_P4_resistors_2026-09-28.enet) ont été contrôlés. La netlist comporte 204 composants contre 202 au 26 septembre, uniquement ces deux résistances en plus ; les connexions des 202 composants précédents sont inchangées. U8.3 reste flottant, R_WD2 est flottante et chaque borne de R_WD1 a un réseau orphelin distinct provenant de fils de longueur nulle. Les chiffres du tableau ci-dessus restent ceux de la netlist de référence. La table constructeur prévoit ces deux valeurs **en parallèle** pour 1 s : ce câblage reste à réaliser. RSTn n’est garanti bas qu’à 1 mA alors que le pull-up `/SAFE` de 1 kΩ demanderait environ 3 mA : un raccordement direct n’est pas justifié. Une entrée Schmitt et deux drains ouverts séparés sont proposés, mais non placés ; le maintien inhibé après reset et lors de la perte +3V3 reste à concevoir. L’inventaire H1/H2 est extrait de la netlist contrôlée ; aucune affectation firmware de banc n’a été recopiée.

**Export P4 ultérieur, après pose d'étiquettes réseau :** la [netlist](reviews/2026-09-26/Netlist_Power_Interface_P4_watchdog_delay_2026-09-28.enet) contient U8.3 et R_WD1.1 sur `WD_DELAY_1S`, R_WD1.2 sur `GND`, sans changement de composant ni d'autres `pinInfoMap`. R_WD2.1/.2 restent **flottantes**, bien que deux étiquettes leur soient visuellement accolées dans EasyEDA ; le [DRC](reviews/2026-09-26/DRC_Power_Interface_P4_watchdog_delay_2026-09-28.txt) confirme ce point (0 erreur fatale, 0 erreur, 28 avertissements, 61 informations). La résistance équivalente de 5,202 kΩ et la temporisation nominale de 1 s ne sont **pas encore câblées**. L'empreinte de U8 a été comparée géométriquement au land pattern TI ; le détail est dans la revue P4.

La [source native de cet export partiel](reviews/2026-09-26/P4-watchdog-delay-partial-2026-09-28.epro2) ne contient effectivement aucun fil de R_WD2. Après réouverture de P4, une nouvelle saisie broche par broche a été enregistrée dans EasyEDA. **Contrôle ultérieur concluant :** la [netlist finale de cette passe](reviews/2026-09-26/Netlist_Power_Interface_P4_RWD2_2026-09-28.enet) relie U8.3, R_WD1.1 et R_WD2.1 à `WD_DELAY_1S`, ainsi que R_WD1.2 et R_WD2.2 à `GND`. Par rapport à l'export partiel, seul le `pinInfoMap` de R_WD2 change parmi les 192 composants. La [source native actualisée](reviews/2026-09-26/P4-watchdog-delay-reviewed-2026-09-28.epro2) passe le contrôle d'intégrité ZIP, contient les deux fils de R_WD2 et une note de statut cohérente ; le [DRC](reviews/2026-09-26/DRC_Power_Interface_P4_RWD2_final_2026-09-28.txt) n'y relève plus de broche flottante et affiche 0 erreur fatale, 0 erreur, 24 avertissements, 65 informations. Les deux résistances en parallèle correspondent à **5,202 kΩ**, soit le délai nominal de **1 s** selon TI. Ce constat remplace le statut « non câblé » des exports intermédiaires ; DONE, WAKE, RSTn et le chemin matériel de sécurité restent incomplets et aucun essai au banc n'a été réalisé.

**Rappel de reset P4 ajouté et contrôlé ensuite :** R_WD_RST est une résistance 100 kΩ ±1 % UNI-ROYAL `0603WAF1003T5E`, R0603, LCSC `C25803`. La [netlist actualisée](reviews/2026-09-26/Netlist_Power_Interface_P4_RST_pullup_2026-09-28.enet) confirme U8.6 et R_WD_RST.1 sur `WD_RST_N`, R_WD_RST.2 sur `+3V3`. Elle ajoute exactement un composant aux 192 précédents et ne modifie que le `pinInfoMap` de U8 parmi les composants déjà présents. La [source native actuelle](reviews/2026-09-26/P4-watchdog-RST-pullup-reviewed-2026-09-28.epro2) passe le contrôle ZIP et porte une note visible actualisée. Le [DRC actualisé](reviews/2026-09-26/DRC_Power_Interface_P4_RST_pullup_2026-09-28.txt) indique 0 erreur fatale, 0 erreur, 27 avertissements et 60 informations dans son fichier exporté ; U8.6 et R_WD_RST n'y sont plus signalés flottants. Le nombre de groupes de broches flottantes n'est pas directement comparable au précédent rapport. La sortie RSTn est maintenant polarisée localement, mais DONE, WAKE et les circuits de reset ESP32 et de sécurité restent à réaliser ; aucun essai matériel n'a été effectué.

La vérification native des candidats pour l'interface suivante distingue le SN74LVC1G14DBVR **TI / C7835** de la première réponse de recherche **UMW / C434069** ; son symbole affiche 1 NC, 2 A, 3 GND, 4 Y, 5 VCC. Pour le MOSFET, `DMG1012T-7` **DIODES / C20512** est distinct des variantes de fabricants tiers, notamment `C42412320` d'ElecSuper. Ces références sont consignées dans la [revue P4](reviews/2026-09-26/P4-watchdog-et-brochage-preliminaire.md) ; elles ne sont pas encore placées sur P4, car le maintien de l'état sûr après défaut et le réarmement restent à concevoir.

Le [SN74AHCT125](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf) doit être alimenté en 5 V. Fixer les entrées des portes inutilisées, gérer les OE au démarrage et éviter toute alimentation parasite du bandeau éteint.

Les connecteurs de ventilateurs et les MOSFET associés restent provisoires. **Obtenir les modèles de ventilateurs et leur nombre de fils** avant de décider entre commutation de puissance et commande PWM dédiée. Les connecteurs génériques actuels ne définissent pas un brochage exploitable.

Le fichier `firmware/esp32_safety/main/board_config.h` annonce des affectations **BENCH** : ce n’est pas un contrat de brochage PCB. Établir un tableau complet H1/H2 ↔ signaux, incluant restrictions ESP32, broches de démarrage, broches réservées à la mémoire et état sûr au reset, avant les connexions finales.

## P5 — freinage analogique

`U10` TLV1701QDBVRQ1 / C702102 et `Q6` SiR870ADP / C506607 sont réels mais non raccordés. Les autres éléments sont majoritairement des brouillons. Un élément appelé `F_P5` utilise encore un symbole de résistance ; les repères `19` et `20` sont invalides ou ambigus. Ils ne représentent pas un fusible et une résistance de freinage finalisés.

**Vérification de brochage complémentaire :** la netlist native du 28 septembre donne pour U10 `1 IN+`, `2 V−`, `3 IN−`, `4 OUT`, `5 V+`, conformément à la [table de brochage TI du TLV1701-Q1](https://www.ti.com/lit/ds/symlink/tlv1701-q1.pdf). Pour Q6, elle donne `1–3 S`, `4 G`, `5–8 D`, conformément au [boîtier PowerPAK SO-8 de Vishay](https://www.vishay.com/docs/63657/sir870adp.pdf). Le brochage logique de ces symboles est donc cohérent ; aucune broche n'est raccordée. U10 et Q6 restent tous deux marqués `Add into BOM=yes` et `Convert to PCB=yes` dans la netlist, alors que la décision M15 conditionne encore l'existence même du hacheur. Cette observation ne qualifie ni leurs empreintes physiques ni leur aptitude thermique ou électrique pour P5.

Le [TLV1701-Q1](https://www.ti.com/lit/ds/symlink/tlv1701-q1.pdf) fonctionne jusqu’à 36 V et possède une limite absolue d’alimentation de 40 V. **Ne pas alimenter V+ directement avec un bus à 42 V ou davantage.** Prévoir, si le hacheur est nécessaire, une alimentation locale protégée issue du bus, un diviseur de mesure, une référence, l’hystérésis, une commande de grille adaptée et un état OFF défini.

La sortie du comparateur est open-collector ; elle n’est pas un driver de MOSFET complet. La résistance de freinage, l’énergie à absorber, le courant, le fusible, la SOA de Q6 et l’évacuation thermique restent à dimensionner. La résistance ne peut pas être choisie sur la seule tension nominale du pack.

**M15 détermine si P5 est nécessaire.** Le seuil ancien de 42,5 V ne constitue pas une validation. M14, M12 et l’enveloppe de tension des cartes moteur doivent aussi être intégrés. Aucun nouveau câblage de puissance de P5 n’a été inventé pendant cette revue.

### Correction des réservations P5 — 28 septembre

`R18` (`gge251`, diviseur de mesure BUS à valeur TBD) était déjà hors BOM mais encore convertible vers le PCB. `R25` (`gge244`, résistance générique 10 kΩ non câblée, sans référence fabricant) était incluse dans les deux. Leurs propriétés sont maintenant **Add into BOM=No** et **Convert to PCB=No** dans EasyEDA. Les symboles restent visibles pour poursuivre la conception. L’[export natif P5](reviews/2026-09-26/P5-resistances-exclues-2026-09-28.epro2) passe le contrôle d’intégrité ZIP et contient ces quatre attributs à `no`. La [netlist après P5](reviews/2026-09-26/Netlist_Power_Interface_P5_resistors_excluded_2026-09-28.enet) contient **201 composants contre 203** après la correction J13 : seuls `R18` et `R25` ont disparu, sans changement des propriétés ni des réseaux de broches des 201 composants conservés. Ce nettoyage ne valide pas le hacheur P5.

**Contrôle DRC du 28 septembre :** le [rapport exporté depuis EasyEDA](reviews/2026-09-26/DRC_Power_Interface_2026-09-28.txt) porte sur tout le schéma Power Interface et affiche **0 erreur fatale, 0 erreur, 30 avertissements et 61 informations**. Il confirme notamment U8.3–U8.6 et R_WD2.1/.2 flottants ; les réseaux `$4N46`/`$4N47` de R_WD1 n'atteignent chacun qu'une seule broche. Il signale aussi une discordance entre les attributs de U8 et sa référence fournisseur, à vérifier avant validation BOM. Les essais de fil et d'étiquette dans l'interface ont été annulés : P4 reste à 11 composants et 32 objets Wire/Bus, sans nouveau raccordement confirmé. L'absence d'erreurs de catégorie « Error » ne vaut pas validation fonctionnelle.

## Suite de travail

1. Obtenir la décision sur la correction ciblée de P1 pour l’alimentation ESP32, puis finir P2-A et exporter son PDF/BOM/netlist.
2. Poursuivre le tri des brouillons hors cadre et des pièces génériques encore incluses au PCB/BOM ; conserver une trace des éléments retirés. Sur P2, C17–C21, C27, Q11/Q12 et L11 sont désormais exclus, comme les résistances I²C dupliquées, R10 et J13 provisoires de P4, puis R18/R25 de P5. Ne pas convertir les autres réservations comme si elles étaient sélectionnées.
3. Dimensionner P2-B à partir de références réelles et valider les boucles, protections et thermiques.
4. Fixer l’enveloppe de bus, le courant de défaut et la détection des fusibles pour valider P3 déjà raccordée.
5. Établir le contrat de brochage ESP32, préciser les ventilateurs, choisir la protection CAN et concevoir le chemin /SAFE pour P4.
6. Recevoir les résultats M14/M15 ; concevoir P5 seulement si le résultat le justifie.
7. Vérifier symboles/empreintes, passer ERC/DRC avec justification explicite des exceptions, puis procéder à la revue de routage et aux essais prévus dans le dossier de mesures.

L’absence de réponse aux questions techniques ne vaut ni résultat de mesure ni autorisation de modifier le bloc gelé de P1.
