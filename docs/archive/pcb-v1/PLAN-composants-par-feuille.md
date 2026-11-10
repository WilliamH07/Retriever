# Inventaire et organisation logique — carte `safety_power`

Date : 2026-09-23  
Portée : inventaire des composants présents ou requis, et proposition de zones de travail pour faciliter le câblage.  
Source principale : `HANDOFF-safety_power.md` et `PLAN-P2-rails-power.md`, complétés par l’inspection de l’arborescence EasyEDA.

### Passe Computer Use — 25 septembre 2026, P4/P5 — réservations complémentaires

- **P4 :** les placeholders historiques `R21` (`$4I27`) et `R22` (`$4I28`), auparavant étiquetés pour une terminaison CAN, sont maintenant réaffectés aux résistances série de grille `R_G_FAN1` et `R_G_FAN2`; valeur, puissance et MOSFET associés restent à choisir selon les ventilateurs. BOM et PCB restent désactivés; sauvegarde globale EasyEDA confirmée. `R_CAN_TERM` (`$4I33`) est le seul emplacement explicite réservé à la résistance 120 Ω optionnelle, limitée à un nœud d’extrémité; un cavalier/interrupteur de sélection reste à ajouter après validation de la topologie. Le composant a été déplacé depuis l’extérieur du cadre vers la zone fonctionnelle CAN (coordonnées de placement affichées x=2,1 po, y=3,45 po); à confirmer au zoom schéma lors de la revue finale.
- `C17` (`$4I35`) est maintenant ajouté sur P4 près du bloc U8 comme `CAP_0603`, annotation `TBD — C_U8_LOCAL (100 nF cible)`, description de réserve et BOM/PCB désactivés. C’est un emplacement de découplage à confirmer selon la fiche fabricant, pas un choix de composant/empreinte validé; aucun fil n’a été ajouté. Sauvegarde EasyEDA confirmée.
- `D4` (`$4I34`) a été ajouté depuis la recherche « TVS » pour réserver une protection ESD/transitoire à côté du bloc CAN. La pièce renvoyée par la bibliothèque est le placeholder catalogue générique `TVS` / C9900021122 avec empreinte SOD-523; `Add into BOM = No` et `Convert to PCB = No` ont été sélectionnés. Cette référence et cette empreinte ne sont pas validées pour le CAN ni pour un défaut vers le bus 42 V; choisir une protection coordonnée au transceiver finalement retenu et à la topologie, puis placer D4 au connecteur avant câblage.
- **P5 :** ajout de `R20` (`$5I28`), `Res_0603`, annotation `TBD — R_BRAKE — dimensionner après M15`, pour réserver la fonction de résistance de dissipation. BOM et conversion PCB désactivés; sauvegarde confirmée. Le 0603 est un simple symbole de travail, impropre à représenter/choisir la résistance de puissance. Aucun câblage ni dimensionnement n’a été fait; le besoin même du hacheur et son énergie restent conditionnés par les essais M15.

### Passe Computer Use — 25 septembre 2026, P2/P4 — compléments

- **P2 :** ajoutés `C_IN10_1` (`$2I69`), `C_IN10_2` (`$2I70`), `C_IN10_3` (`$2I71`) et `C_IN10_4` (`$2I72`) près de `U11`, dans le groupe du convertisseur 12 V. Valeur/commentaire: `TBD — 10 µF / 100 V — package/DC-bias à valider`. Ils emploient le symbole `CAP_0603/C0603` uniquement comme placeholder; cette empreinte est inadaptée et leur Description impose la sélection d’un vrai boîtier avec tension et capacité effective vérifiées. Aucun fil ajouté. EasyEDA confirme `Add into BOM = No`, `Convert to PCB = No` pour C_IN10_2, C_IN10_3 et C_IN10_4, ainsi que « Saved successfully! » pour C_IN10_3 et C_IN10_4; mêmes réglages documentés pour C_IN10_1. `C_BULK10` (`$2I73`) a été ajouté près du groupe d’entrée 12 V, valeur TBD 100 µF/≥63 V, avec avertissement sur boîtier, ripple/ESR et empreinte inadaptée; BOM/PCB No et sauvegarde « Saved successfully! » confirmés. Un `C23` (`$2I75`) supplémentaire apparaît ensuite près du bord inférieur de P2-B; la vue EasyEDA le montre avec la valeur par défaut `100nF`, empreinte `C0603` et options BOM/PCB `Yes/Yes`. La hiérarchie contient déjà un autre `C23` (`$2I62`) sur P2 : il s’agit donc d’un doublon de repère, et non d’un composant prêt. Son état sauvegardé n’est pas établi; **ne pas exporter la BOM ni le compter** avant correction du repère, de la valeur, de l’empreinte et des options. À poursuivre: corriger ou retirer ce brouillon, compléter les condensateurs bulk/sortie et réseaux de compensation manquants, puis traiter le chevauchement visible de U11/U12 et les autres objets hors cadre.
- **P4 :** ajouté `C17` (`$4I35`) près de `U8` pour réserver son découplage local; `TBD — C_U8_LOCAL (100 nF cible)`, valeur/empreinte à confirmer, non câblé, `Add into BOM = No`, `Convert to PCB = No`; sauvegarde EasyEDA confirmée.

### Passe Computer Use — 25 septembre 2026, P5 — résistance de référence/biais

- Ajouté sur P5 un symbole générique de résistance `Res_0603/R0603`, repère EasyEDA `R16`, valeur/commentaire `TBD — R_REF_P5` pour réserver la référence/biais. `Add into BOM = No` et `Convert to PCB = No` sont confirmés dans les propriétés EasyEDA; sauvegarde confirmée par « Saved successfully! ».
- Cette fonction est distincte de `R14/R15`, déjà réservées au diviseur de mesure BUS+ dans l’inventaire antérieur. Le placeholder n’est pas relié, ne fixe aucune valeur et n’est pas un choix d’empreinte de production. Les fonctions de référence, hystérésis, rappel/pilote, alimentation/découplage et protection restent à dimensionner/compléter; le dimensionnement demeure soumis à M15 et à la fiche du comparateur.

### Passe Computer Use — 25 septembre 2026, inductances réservées pour P2-B

- `L10` (`$2I66`) et `L11` (`$2I67`) sont présents sur P2 comme symboles d’inductance génériques nommés `TBD POWER INDUCTOR`, exclus de BOM et de conversion PCB. Ils réservent les fonctions d’inductance des deux convertisseurs P2-B; ni leur inductance nominale ni leur courant admissible ne sont représentés comme validés.
- La bibliothèque EasyEDA leur associe encore un petit symbole/footprint traversant générique inadapté à la sélection d’une inductance de puissance. Le commentaire de L10 comporte actuellement une faute (`TTBD POWER INDUCTOR`). Aucun câblage n’a été ajouté.
- Pendant cette passe, le cadrage « Fit All » a révélé que des objets de P2 sont dispersés hors du cadre A4. Un déplacement de L10 a été tenté; sa position finale n’a pas pu être vérifiée après verrouillage de l’ordinateur. Revoir L10/L11 et les autres objets hors-cadre avant de considérer le regroupement visuel réalisé.

### Passe Computer Use — 25 septembre 2026, reprise de P5 (J19 et R_GS_P5)

- `J19` (`$5I25`) a été placé dans le cadre de P5 comme symbole générique 2 broches `HDR-F_2.54_1x2P`, réservé provisoirement à l’entrée `BUS+ / GND` du hacheur. Le nom rappelle que modèle et brochage restent à choisir après M15; `Add into BOM = No` et `Convert to PCB = No` sont vérifiés. Le modèle 2 broches n’est pas une sélection de connecteur validée et aucun fil n’a été ajouté.
- `R_GS_P5` (`$5I26`) a été ajouté près de J19 en tant que `Res_0603/R0603`, valeur `TBD`, avec description « résistance grille-source de Q6; valeur/puissance/besoin à confirmer après M15 ». `Add into BOM = No` et `Convert to PCB = No` sont vérifiés. C’est un placeholder graphique, pas une sélection de composant ou d’empreinte pour le hacheur.
- Sauvegarde globale EasyEDA confirmée (« Saved successfully! »). P5 compte 238 objets dans l’arborescence du schéma; aucune connexion nouvelle n’a été faite. L’annotation détaillée, `R23` et `R24` restent à replacer/valider visuellement dans le cadre; P5 n’est pas terminée et le verrou M15 reste applicable.

### Passe Computer Use — 25 septembre 2026, reprise de P4

- `J18` (`$4I30`) est maintenant présent sur P4 à côté de la zone connecteurs, avec le symbole générique 3 broches `HDR-F_2.54_1x3P` et empreinte catalogue traversante `HDR-TH_3P-P2.54-V-F`. Sa description le réserve à l’interface du bandeau WS2812B; le connecteur réel, le brochage et l’ordre alimentation/données/masse restent à définir. `Add into BOM = No` et `Convert to PCB = No`; la sauvegarde EasyEDA a confirmé « Saved successfully! ».
- L’arborescence confirme déjà `J15`, `J16` et `J17` sur P4. La description actuelle de `J17` indique également « TBD — interface WS2812B », alors que la matrice plus bas le réserve aux ventilateurs. Ne pas attribuer/connecter J17 avant correction de cette incohérence; `J18` est pour l’instant un emplacement supplémentaire, pas une décision de brochage.
- Aucun fil ni net n’a été ajouté pendant cette passe. P4 reste incomplet et non validé électriquement.

### Passe Computer Use — 25 septembre 2026, complément P5

- `R23` (`$5I22`) est le placeholder `R_PU_P5` pour le rappel de la sortie collecteur-ouvert de U10; valeur `TBD`, description de calcul enregistrée, `Add into BOM = No` et `Convert to PCB = No`.
- `R24` (`$5I23`) est un placeholder `R_G_P5` pour la résistance série de grille de Q6; valeur `TBD`, description précisant que puissance et valeur restent à vérifier après M15, `Add into BOM = No` et `Convert to PCB = No`.
- Les deux symboles utilisent la bibliothèque générique `Res_0603/R0603` uniquement pour réserver les fonctions sur P5; cette empreinte n’est pas validée. Ils ne sont pas câblés et ne sont pas des composants de fabrication. La position de R24 reste à contrôler au zoom feuille avant de considérer le groupement visuel satisfaisant.

### Passe Computer Use — 25 septembre 2026, connecteur CAN P4

- `J13` (`$4I29`) a été ajouté dans la zone libre de P4 comme connecteur générique 3 broches `HDR-F_2.54_1x3P` avec empreinte traversante catalogue `HDR-TH_3P-P2.54-V-F`. Sa description le réserve à `CANH`, `CANL` et `GND`; le modèle réel, le brochage et la compatibilité faisceau restent à valider. `Add into BOM = No` et `Convert to PCB = No`; EasyEDA a confirmé la sauvegarde. Aucun fil n’a été posé.

### Passe Computer Use — 25 septembre 2026, reprise de P5

- L’arborescence EasyEDA a permis de rouvrir `P5` après retour à l’écran d’accueil.
- `R14` (`$5I16`) et `R15` (`$5I17`) sont deux symboles `Res_0603` ajoutés dans une petite zone à droite de `U10`. Leurs commentaires sont respectivement `TBD — R_SENSE_P5_A` et `TBD — R_SENSE_P5_B`. Pour chacun, `Add into BOM = No` et `Convert to PCB = No` ont été vérifiés; la sauvegarde EasyEDA a confirmé « Saved successfully! » après `R15`.
- `R16` (`$5I18`) a ensuite été posé à droite de `R15`, commentaire `TBD — R_REF_P5`. L’état courant EasyEDA confirme `Add into BOM = No` et `Convert to PCB = No`; la feuille est actuellement en P5. À poursuivre : ajouter les autres symboles fonctionnels sans câblage, puis sauvegarder et vérifier chaque page.
- Ces résistances 0603 ne sont que des placeholders d’interface et ne doivent pas servir de sélection de puissance ou entrer dans une fabrication. `R10`–`R13` historiques restent en grappe, avec chevauchement et plusieurs désignateurs dupliqués (`R11`, `R12`); ils doivent être réorganisés/renumérotés avant de considérer P5 propre.
- Aucun fil ni net n’a été créé. U10 et Q6 restent provisoires; le dimensionnement du hacheur reste bloqué par M15 et les limites de la fiche TI.

### Passe Computer Use — 25 septembre 2026, ajout confirmé P5/P4

- **P5 :** `C22` (`$5I19`) a été posé près de `U10` comme symbole `CAP_0603`, puis son commentaire a été remplacé par `TBD — C_U10_LOCAL`. `Add into BOM = No` et `Convert to PCB = No`; EasyEDA a confirmé « Saved successfully! ». Ce n’est pas une valeur de découplage approuvée.
- **P4 :** `J15` (`$4I24`), `J16` (`$4I25`) et `J17` (`$4I26`) sont des connecteurs système génériques `HDR-F_2.54_1x3P`, posés dans une zone libre. J15 est réservé provisoirement à l’arrêt sûr, J16 au ventilateur, J17 à l’interface WS2812B. Pour chacun, `Add into BOM = No`, `Convert to PCB = No`; EasyEDA a confirmé l’enregistrement. Brochage, empreinte réelle et affectations sont à définir. Aucun fil/net n’a été ajouté.
- **Portée :** ces ajouts complètent des emplacements de composants, pas les quatre schémas prêts à fabriquer. Ils restent des placeholders; P2 reste incomplet, P4 manque encore CAN/protections/commande fan et LED, et P5 attend le bilan M15. P1 n’a pas été modifiée; P3 reste la feuille déjà équipée.

### Passe Computer Use — 25 septembre 2026, reprise P2-B

- **Reprise du 25 septembre — placeholders P2 vérifiés :** `C24` (`$2I63`) et `C25` (`$2I64`) sont présents dans une zone libre à droite du groupe P2-B. Ce sont des symboles `CAP_0603`, sans câblage; les valeurs sont `TBD`, `Add into BOM = No` et `Convert to PCB = No`. C24 est réservé provisoirement à `C_IN10_2` (condensateur d’entrée 10 µF/100 V à sélectionner), C25 à `C_C10_1` (compensation LM5145 à calculer). L’empreinte 0603 de la bibliothèque n’est pas approuvée pour C_IN10_2 et reste purement graphique. EasyEDA a confirmé l’enregistrement de C25. Il manque encore les autres condensateurs d’entrée/sortie et de compensation, ainsi que les inductances de puissance; la feuille ne devient pas de ce fait complète ni fabricable.
- `R19` (`$2I65`) a été posé près de C25 comme position de réserve pour la résistance de grille P2-B (`R_GD10`). Valeur `TBD`, commentaire indiquant le dimensionnement ultérieur, `Add into BOM = No` et `Convert to PCB = No`. Le symbole/empreinte 0603 est seulement graphique et ne remplace pas une sélection de résistance adaptée. Aucun câblage.

- `C22` (`$2I55`) a été posé sur P2-B comme `CAP_0603`, annotation `TBD — C_P2B_LOCAL`; il est exclu de BOM et PCB. EasyEDA a confirmé « Saved successfully! ».
- Deux symboles N-MOS génériques sont maintenant posés sur P2-B : `Q9` (`$2I56`) et `Q10` (`$2I57`). Q9 porte la description `TBD — MOSFET de puissance P2B, boîtier à choisir`; Q10 a la même intention. BOM et PCB sont désactivés et EasyEDA a confirmé la sauvegarde. Les footprints système visibles (SOT-23) ne conviennent pas comme sélection de puissance : ces symboles ne font que réserver les emplacements, sans MPN/boîtier validé, valeur ni câblage.
- Un troisième symbole générique `Q13` (`$2I60`) a été ajouté à P2-B, décrit comme MOSFET de puissance TBD, exclu BOM/PCB et sauvegardé. Il porte toujours un footprint bibliothèque SOT-23 non valable pour le rôle puissance; il s'agit uniquement d'un placeholder. L'affectation des repères de toute la feuille est à revoir globalement (Q7/Q8 déjà présents, Q9/Q10 et Q13 ne constituent pas une nomenclature cohérente).
- Un quatrième symbole générique `Q14` (`$2I61`) a ensuite été posé dans P2-B et sauvegardé. Sa description indique que boîtier/MPN restent à valider; BOM et PCB sont désactivés. Il utilise également un footprint de bibliothèque SOT-23 impropre à une sélection de MOSFET de puissance et ne sert que de repère schématique.
- Les composants ajoutés précédemment sont répartis dans la zone de P2-B mais leur placement visuel n'a pas encore été revu à fort zoom. Le nombre de symboles réservés atteint désormais quatre (`Q9`, `Q10`, `Q13`, `Q14`), mais la cohérence globale des repères reste à revoir compte tenu des `Q7/Q8` et autres duplicatas hérités. Les deux inductances de puissance et les capacités/réseaux de compensation manquent toujours; aucun placeholder ne doit être utilisé pour fabriquer.

### Passe Computer Use — 25 septembre 2026, complément P5

- `R17` (`$5I20`) et `R18` (`$5I21`) sont deux symboles système `Res_0603`, posés ensemble dans la zone libre de P5 pour représenter provisoirement le diviseur de mesure BUS. Leurs valeurs sont `TBD` (aucune résistance 10 kΩ par défaut n'est validée); leur intention est résistance haute et basse du diviseur. Les deux sont exclus de BOM et de la conversion PCB; `R18` porte une description TBD. EasyEDA a confirmé « Saved successfully! » après R18.
- La description de `R17` a été corrigée et vérifiée dans les propriétés : `TBD — R_BUS_DIV_P5_HIGH; valeur à calculer avant MPN`. R18 est `TBD — R_BUS_DIV_P5_LOW; valeur à calculer avant MPN`. Les deux sont sauvegardés avec BOM/PCB sur No. Ils ne sont pas câblés. Les symboles/empreintes 0603 restent provisoires; ils ne définissent ni la tension maximale d'entrée admissible de U10 ni le courant de mesure. Pas de sélection de BOM/fabrication.

### Passe Computer Use — 25 septembre 2026, complément P4

- `R21` (`$4I27`) a été posé dans la zone libre de P4 pour réserver une position au réseau de terminaison CAN. Le composant est `Res_0603`, valeur `TBD`, description `TBD — R_CAN_TERM_P4; valeur/configuration à valider selon topologie CAN`, `Add into BOM = No` et `Convert to PCB = No`. EasyEDA a confirmé « Saved successfully! ».
- R21 n'est pas câblé et ne décide pas si/combien de terminaisons sont nécessaires : cela dépend du placement sur le bus, de l'impédance du câble et de la topologie. C'est un placeholder uniquement, pas une recommandation automatique de 120 Ω.

## État observé dans EasyEDA

### Passe de placement du 25 septembre 2026 (reprise autonome)

- **P2-B — ajouts visibles dans EasyEDA :** `R_F1_10` et `R_F1_11` (10 kΩ, 0603, C25804); `R_F2_10` (715 Ω, 0603, UNI-ROYAL 0603WAF7150T5E, C23238); `R_F2_11` (1,91 kΩ, 0603, UNI-ROYAL 0603WAF1911T5E, C22853); deux FETs `DMG1012T-7(ES)` (C42412320, SOT-523), provisoirement repérés Q7/Q8 sur cette feuille. Les quatre résistances et les deux FETs restent sans connexion. Les repères FET doivent être comparés à l’ensemble des feuilles avant nomenclature, car les références de composants sont réutilisées entre pages. L’ESD de la variante `DMG1012T-7(ES)` et son adéquation au circuit d’inhibition doivent être revus sur fiche constructeur avant BOM.
- **P4 — pull-ups I²C vérifiés :** la passe du 25 septembre a ajouté `R_SDA` (ID `$4I19`, 2,2 kΩ, UNI-ROYAL 0603WAF2201T5E, LCSC C4190) sous `R_SCL`, dans la zone logique près de U7. EasyEDA a confirmé « Saved successfully! » et le total du schéma est passé de 195 à 196 objets. Les deux résistances ne sont pas câblées. La recherche du connecteur CAN n’a pas permis de poser un symbole 3 broches sans confirmer un modèle/empreinte; aucun connecteur provisoire n’a été choisi.
- **Alerte de disposition P2 :** la vue actuelle montre les nouveaux composants trop près du cadre inférieur et plusieurs étiquettes se chevauchent. Ce placement prouve seulement leur présence dans le schéma; il ne constitue pas une disposition logique relue. Réorganiser le groupe P2-B en zone dégagée, sans toucher aux fils/nets, puis vérifier chaque repère et sauvegarder.
- **P3–P5 :** inspection visuelle de P3 confirme la présence des fusibles, porte-fusibles et connecteurs déjà décrits plus bas. P4 contient U6–U9, C8/C13–C16 et le groupe de commande documenté; les zones libres doivent encore recevoir/identifier les connecteurs et protections manquants. P5 contient U10 et Q6 uniquement parmi les composants fonctionnels visibles. Aucun composant supplémentaire n’a été ajouté sur P3, P4 ou P5 dans cette passe.
- **P5 bloqué par M15 :** ne pas choisir de résistance de freinage, seuil, puissance ou thermique tant que l’acceptation de régénération par le BMS et les mesures de tension/énergie ne sont pas faites. Les placeholders à ajouter devront être clairement `TBD` et sans MPN/empreinte si le symbole générique correspondant est disponible.
- **Passe P5 du 25 septembre :** une annotation texte listant les zones puissance/mesure/commande et les repères TBD a été saisie et sauvegardée dans EasyEDA (confirmation AX « Saved successfully! »). Elle n’apparaît pas dans la vue complète à 79 % après insertion; sa position/rendu visuel reste à vérifier. Elle ne compte pas comme placement des composants génériques eux-mêmes.
- **État global :** sauvegardes EasyEDA confirmées après chaque ajout P2. Le design n’est pas complet : les MOSFETs synchrones, inductances, banques de capacités, compensations et composants d’interface manquants doivent encore être posés/identifiés; aucune connexion électrique ne doit être tracée dans cette passe.

### Passe Computer Use — 25 septembre 2026 (ajouts complémentaires)

- **P2 :** quatre symboles `CAP_0603` (C17, C18, C20, C21) ont été ajoutés dans la zone de P2-B. Il s’agit de symboles génériques; la bibliothèque a prérempli certains commentaires `100nF`, qui ne sont pas validés comme valeurs de conception. C21 est marqué `TBD`; les autres commentaires doivent être remplacés par `TBD` ou des valeurs issues des datasheets avant génération BOM. Les nouveaux condensateurs ne sont pas raccordés. La disposition P2-B reste à ranger, et Q8 est encore hors du cadre inférieur.
- **P4 :** un connecteur générique 2 broches `H4` (`HDR-F_2.54_1x2P`, symbole système) a été posé dans le cadre, comme placeholder d’interface. Ce n’est ni le connecteur CAN 3 broches ni une sélection de connecteur de sécurité validée; il n’est pas câblé. Le modèle comporte une empreinte catalogue générique : ne pas fabriquer à partir de cet état.
- **P5 :** deux résistances génériques `R10` et `R11` (Res_0603/R0603) ont été posées dans la zone fonctionnelle. Leurs propriétés sont signalées `TBD`, et `Add into BOM = No`, `Convert to PCB = No`. Attention : l’étiquette visible de R11 affiche encore `10K` dans la vue, malgré la propriété changée en TBD; corriger/rafraîchir avant toute revue. Elles illustrent les réseaux de freinage/mesure et ne sont pas des pièces de production. U10 et Q6 restent les seuls composants actifs identifiés et provisoires.
- **Sauvegarde :** EasyEDA a confirmé la sauvegarde de P2, P4 et P5. Aucun fil/net n’a été ajouté.
- **État honnête :** les quatre feuilles ne sont pas complètes. P2-B manque notamment les quatre MOSFETs de conversion, les deux inductances de puissance et les réseaux de puissance/compensation validés. P4 manque au moins le CAN complet (transceiver compatible défaut bus, protection, terminaison et connecteur adapté), les interfaces arrêt sûr/fan/LED. P5 manque les protections/passifs/connecteurs requis, dont les valeurs ne peuvent être gelées avant mesure M15 et calcul énergétique/thermique. P3 est peuplée avec les composants documentés mais reste sans validation électrique/netlist.

### Passe Computer Use — 25 septembre 2026 (reprise immédiate)

- **P4 — J13 CAN :** ajout du symbole système `HDR-F_2.54_1x3P` dans la zone connecteurs, repère `J13`. Il représente seulement les trois positions CANH/CANL/GND attendues; brochage, connecteur réel et protection restent à définir. `Add into BOM = No` est confirmé; `Convert to PCB` reste `Yes` et doit être désactivé avant toute génération PCB. La feuille porte un astérisque de modification après cette passe : la sauvegarde de ce dernier état reste à confirmer (ne pas s'appuyer uniquement sur la sauvegarde antérieure).
- **P5 — passifs de commande/mesure :** correction du champ Value de `R12` vers `TBD — R_HYST_P5`; son inclusion BOM a été passée à `No`, et son inclusion PCB est à vérifier. Un symbole de résistance supplémentaire `R13` a été copié dans la grappe de passifs, mais sa valeur par défaut `10K` est visible dans les propriétés après duplication; **il ne doit pas être interprété comme une valeur choisie**. Les repères et annotations de cette grappe se chevauchent; réviser/supprimer les duplicatas éventuels et renommer chaque instance de façon unique avant de considérer P5 organisé.
- **Sauvegarde et portée :** P5 avait affiché « Saved successfully! » après la passe des passifs; les modifications ultérieures décrites ici ne sont pas toutes confirmées enregistrées. Aucun fil n'a été ajouté. Cette passe ne complète pas les quatre feuilles.

| Feuille | État constaté | Suite |
|---|---|---|
| P1 | Feuille de sécurité déjà validée selon le handoff | Conserver sa disposition et ses connexions ; ne pas modifier |
| P2 | Bloc 8/9/12 commencé, éléments dispersés; U11/U12 LM5145RGYR provisoires et non câblés en P2-B. R_RT10/R_RT11, réseaux UVLO, C_VCC/C_BST et quatre résistances R_F présents. Deux DMG1012T-7(ES) provisoires Q7/Q8. Placeholders génériques de conversion Q9/Q10/Q13/Q14, plus C22 local TBD, ajoutés sans câblage; BOM/PCB désactivés pour Q14 (et préalablement Q9/Q10/Q13). Tous restent à revoir pour repères et footprints, et le placement n'a pas été relu à fort zoom. | Ajouter les deux inductances et les capacités/réseaux manquants; réorganiser P2-B, vérifier BOM/PCB de tous les placeholders, valider les repères globaux et corriger EP de U4 avant validation |
| P3 | Note fonctionnelle, F1–F4 (Littelfuse 0997015.WXN), FH1–FH4 (Littelfuse 178.6764.0001, LCSC C142933) et J3–J9 (XY636-6.35-2P, LCSC C557968) présents dans le cadre A4. J3–J9 sont regroupés en zone de sorties; aucune connexion électrique n’est validée. Le FH5 surnuméraire créé pendant une tentative de pose incorrecte a été supprimé. | Conserver seulement FH1–FH4; garder J3–J9 comme bornes provisoires jusqu’à validation du courant, du harnais et de l’empreinte; vérifier les données EasyEDA contradictoires avec la fiche Littelfuse, puis traiter la détection et le câblage |
| P4 | U6–U9, C8/C13–C16, R_SCL/R_SDA, J13–J17 et placeholder R21 de terminaison CAN présents. J15/J16/J17 et R21 sont provisoires, sans câblage et exclus de BOM/PCB. | Sélectionner transceiver CAN survivant au défaut bus et protections; décider la terminaison d'après le harnais/topologie; compléter commande fan et buffer/protection WS2812B; valider connecteurs, datasheets et empreintes |
| P5 | Note d’inventaire, U10 (TLV1701-Q1), Q6 (SiR870ADP candidat), R10–R16 historiques/provisoires, C22 local TBD et nouveaux placeholders R17/R18 (diviseur BUS, valeur TBD, BOM/PCB désactivés) présents. Aucun câblage n’a été ajouté. Le placement de R17/R18 dans la page est confirmé; disposition de toute la feuille et annotation de R17 à vérifier. | Ranger/renuméroter les duplicatas R11/R12 et chevauchements; ajouter connectique/protections et passifs de commande manquants; garder le hacheur en TBD jusqu’aux mesures M15 et au bilan énergétique/thermique |

Les feuilles P3–P5 ne possèdent pas encore de nomenclature vérifiée au niveau des références. Les fonctions et caractéristiques ci-dessous sont des besoins de conception, pas une autorisation à sélectionner des références arbitraires.

## Audit de cohérence avant la prochaine saisie EasyEDA

Une revue de cohérence des documents et de la nomenclature montre plusieurs collisions à traiter avant de compléter le schéma :

| Sujet | Constat vérifié | Traitement requis |
|---|---|---|
| Références P2-B / P4 | Le handoff réserve `U6` et `U7` aux deux LM5145 de P2-B, tandis que P4 emploie déjà `U6` SN65HVD230 et `U7` PCA9555. Les LM5145 ont été saisis dans EasyEDA sous `U11`/`U12`, références uniques; le bloc n’est pas complet. | Conserver provisoirement `U11`/`U12`; confirmer globalement les références et ne pas câbler les contrôleurs avant sélection des composants de puissance et calculs de compensation. |
| Références de commande P2-B | Le handoff duplique `Q7`, `R_RT`, `R_UV5/6`, `C_VCC` et `C_BST` pour chacun des deux convertisseurs, et décrit quatre MOSFET sous `Q8/Q9 ×4`. | Attribuer un repère unique à chaque occurrence (proposition MOSFET : `Q8`–`Q11`, inhibitions `Q12`/`Q13`); ne pas copier les repères répétés tels quels. Les résistances et condensateurs doivent également recevoir des références uniques lors de l’annotation. |
| P3 porte-fusibles | `FH1`–`FH4` ont été ajoutés comme symboles Littelfuse `178.6764.0001` (LCSC C142933) et sauvegardés. La bibliothèque EasyEDA annonce 125 V/30 A et 5 808 pièces, alors que la fiche constructeur 2025 indique 58 VDC/22 A continu/30 A maximum; les métadonnées de la bibliothèque ne concordent donc pas et son stock n’est pas une validation d’achat. | Avant BOM finale, contrôler l’empreinte et la fiche constructeur, confirmer un stock réel, le fusible exact, la courbe temps-courant, le courant de défaut et la tension transitoire BUS+. Les quatre symboles ne sont pas câblés ni routés. Source fabricant : [MINI FL1 58 V PCB Fuse Holder](https://www.littelfuse.com/assetdocs/mini-fl1-datasheet?assetguid=86e3ab08-0473-4acb-98d6-4cf3dbe2f0fa). |
| P4 transceiver CAN | Le handoff demande `SN65HVD230`, mais la fiche TI fixe les terminaux CANH/CANL à −4…+16 V absolus; le bus-fault 42 V possible documenté par le projet dépasse cette limite. TI classe le composant pour un bus-fault de −4…+16 V. | Ne pas raccorder le câble CAN au SN65HVD230 tant que la protection de défaut n’est pas démontrée ou que le propriétaire n’a pas choisi un transceiver protégé. La fiche produit TI indique ±70 V pour `TCAN1042HV`, mais cette substitution change VCC, VIO, brochage périphérique et passifs et doit être revue avant remplacement. Sources constructeur : [SN65HVD230 datasheet](https://www.ti.com/lit/ds/symlink/sn65hvd230.pdf), [TCAN1042HV product data](https://www.ti.com/product/TCAN1042HV). |
| P5 freinage | `M15` détermine si la dissipation de freinage est nécessaire; la résistance et la puissance dépendent de l’énergie régénérée et de la tension mesurée. | Maintenir U10/Q6 explicitement provisoires; ne pas dimensionner/figer le banc de freinage avant M15, puis vérifier SOA impulsionnelle, thermique, seuil et hystérésis. |
| Directive de distribution antérieure | `docs`/spécification de distribution alternative contient un fusible principal 40 A et d’autres charges; le handoff `safety_power` du 14 septembre l’exclut explicitement et remplace les consignes antérieures. | Pour ce projet EasyEDA, ne pas importer le fusible principal ni les charges hors périmètre dans le handoff; conserver la demande de quatre fusibles moteurs et noter les divergences pour revue de configuration. |

La feuille 2 possède également deux sources internes de valeurs pour l’inductance du bloc 8 (ancienne `33 µH`, décision ultérieure `SRP1038A-470M`, `47 µH`). Le plan `PLAN-P2-rails-power.md` retient 47 µH et indique qu’elle doit remplacer l’empreinte actuelle avant câblage; c’est cette décision tardive qui prévaut, sous réserve de vérification physique dans EasyEDA.

**État de l’organisation physique :** P2 contient déjà des symboles et des fils : il faut les réorganiser en conservant les connexions et vérifier chaque nœud après déplacement. P3 contient F1–F4, FH1–FH4 et J3–J9 dans le cadre A4; les sept connecteurs XY636-6.35-2P (C557968) sont regroupés en zone de sorties, FH5 créé par erreur a été supprimé et l’enregistrement est confirmé. Les bornes restent non câblées et provisoires (harnais, courant de branche et empreinte à valider). La fiche fabricant des porte-fusibles donne 58 VDC/22 A continu, tandis que la fiche EasyEDA affiche des valeurs génériques divergentes (125 V/30 A). P4 a U6–U9 et cinq 100 nF (C8, C13–C16); C8/C13/C14/C16 ont été placés dans le cadre A4 près des zones des CI et sauvegardés, sans ajouter de connexions. C15 reste à confirmer visuellement; tous les condensateurs doivent être mis au plus près des pins VCC/GND uniquement après vérification des nets. Des fils verts traversent toutefois les zones U7–U9 et leur origine/nomenclature reste à vérifier avant toute revue électrique. P5 a U10 et Q6 dans le cadre A4; le 23 septembre, Q6 a été rapproché sous U10, sans connexion, et reste un candidat. La pose d’un symbole ne valide ni son circuit, ni son câblage, ni son empreinte pour fabrication.

**Anomalie P2 vue à fort zoom pendant cette revue :** le pad exposé `U4.EP` se termine visuellement par un point gris au lieu d’une connexion GND vérifiée; deux libellés `GND` paraissent flotter sous U4. Ne pas considérer EP comme à la masse ni enregistrer ce sous-ensemble comme terminé avant nettoyage puis vérification de continuité/net dans EasyEDA. La vue d’ensemble montre également que les blocs de P2 n’ont pas encore été regroupés en zones lisibles. Aucune modification de câblage n’a été faite pendant la préparation de cet inventaire.

## P1 — Entrée batterie, contacteur et sécurité (gelée)

### Zone 1 — entrée, mesure de courant et protections

- `CN1` : XT30PW-M30, entrée batterie.
- `R4a`, `R4b` : 2 × 1 mΩ en parallèle, shunt 0,5 mΩ.
- `C_IN1..4` : 4 × 10 µF, 100 V, X7S, 1210.
- `D1` : SMCJ48CA, TVS bidirectionnelle (référence à confirmer selon handoff).
- `D2` : SS310, SMA (référence à confirmer selon handoff).
- `U2` : INA228AIDGSR, mesure courant/tension.
- `R_F1`, `R_F2` : 10 Ω ; `C_F` : 1 µF.
- `TP6`, `TP7` : points de mesure du shunt (à garder proches l’un de l’autre).

### Zone 2 — contrôleur de puissance, contacteur et précharge

- `U1` : TPS48111LQDGXRQ1.
- `Q1`, `Q2` : IPB017N10N5, MOSFETs dos à dos du contacteur.
- `Q3` : IPB017N10N5, MOSFET de précharge.
- `R_PRECH` : 10 Ω, 10 W, ciment axial, sur un bord thermique de carte.
- `R_VS`, `R_G1`, `R_G2` : 0 Ω ; `R_SET` : 100 Ω ; `R_G3` : 220 Ω.
- `R_ISCP` : 1,5 kΩ ; `R_IWRN` : 59 kΩ ; `R_TMR`, `R_G4`, `R_G5` : 100 kΩ.
- `C_TMR` : 470 nF ; `C_VS1`, `C_VS2`, `C_VS3`, `C_EN` : 100 nF, 1 µF, 100 nF, 100 nF respectivement ; `C_BST` : 1 µF.
- `D_Z4` : BZT52C12 ; `Q5` : DMG1012T-7.
- `TP3`, `TP10`, `TP11`, `TP12` : grappe de mesures par rapport à `SRC`.

### Zone 3 — décharge du bus

- `Q4` : IPB017N10N5, MOSFET de décharge.
- `R_DIS1..6` : 6 × 2 kΩ, 2512, 1 W, en parallèle (équivalent 333 Ω).
- `R_GS3` : 1 MΩ ; `R_D?1a/b`, `R_D?2`, `R_D?3` associés au pilotage/diagnostic, selon désignateurs finaux du schéma.
- `D_DS`, `D_DB`, `D_DA` : BAT54S (suffixe S obligatoire).
- `R_UV1`, `R_UV2` : 470 kΩ / 24,9 kΩ.
- `TP4`, `TP5` : mesure BUS+/GND ; `TP5` masse centrale.

### Zone 4 — diagnostic, interface ESP32 et signalisation

- `U3` : ADS1115IDGSR.
- `CN2` : XY-HY2.0-3PWZ, liaison BMS (bloc gelé, validé au banc).
- `H1`, `H2` : deux rangées de 19 broches, module ESP32 DevKitC.
- `R_D?1a/b` ×6 : 6 × 47 kΩ ; `R_D?2` ×3 : 3 × 6,8 kΩ ; `R_D?3` ×3 : 3 × 1 kΩ.
- `R_FLT1`, `R_FLT2`, `R_ALERT`, `R3` : 4 × 10 kΩ ; `R_SDA`, `R_SCL` : 2 × 2,2 kΩ.
- `R_S1..S5`, `R_L1`, `R_L5..L8` : 1 kΩ ; `R_L2` : 2,2 kΩ ; `R_L3` : 6,8 kΩ ; `R_L4a`, `R_L4b` : 2 × 20 kΩ en série.
- `C_ISCP` : 1 nF ; `C_VDD3`, `C_D?` : 100 nF selon les désignateurs de diagnostic finaux.
- LEDs : 4 vertes KT-0603G, 2 rouges KT-0603R, 2 jaunes KT-0603Y.
- `TP1..TP28` : 28 points de test (affecter leur sous-groupe à la zone mesurée ; voir handoff pour les contraintes d’accès).

Références et valeurs exactes restent celles de la section 5 du handoff. Les désignateurs `R_D?` et `C_D?` sont maintenus comme groupes tant que la correspondance de chaque diviseur n’est pas vérifiée dans EasyEDA. D1, D2 et C_TMR ont une référence d’achat à confirmer.

## P2 — Conversion et rails logiques

### Zone A — entrée BUS_RAW+, démarrage et LM5164

- `U4` : LM5164DDAR.
- `C3..C6` : 4 × TDK C3225X7R2A225KT0L0U, 2,2 µF, 100 V.
- `R8` / `R9` : 1 MΩ / 68,1 kΩ, pont UVLO (`UVLO8`).
- `R5` : 41,2 kΩ, programmation RON (`RON8`).

### Zone B — nœud de commutation et filtre Type 3

- `L1` : Bourns SRP1038A-470M, 47 µH (référence retenue dans le plan ; remplacer toute ancienne 33 µH).
- `C7` : 2,2 nF, 50 V, BST–SW.
- `R4` : 220 kΩ ; `C9` : 3,3 nF ; `C10` : 270 pF C0G/NP0.
- Nœuds à garder compacts : `SW8`, `RIPPLE8`, `FB8`.

### Zone C — sortie +5V_HOT et retour de régulation

- `C11`, `C12` : 2 × 10 µF, 25 V, X7R (C12 actuellement identifié dans EasyEDA comme Samsung CL21B106KAYQNNE).
- `R6`, `R7` : 100 kΩ / 31,6 kΩ, diviseur de feedback vers `FB8`.
- `U5` : AP2112K-3.3TRG1.
- `C1`, `C2` : 2 × 1 µF, 50 V X5R, entrée/sortie U5.
- Sorties : `+5V_HOT` puis `+3V3`.

### Zone D — passage isolé vers l’entrée 5 V du module

- `D3` : SS34, anode `+5V_HOT`, cathode vers `ESP_5V_D`.
- `R_ESP_ISO` : 0 Ω retirable, entre `ESP_5V_D` et `ESP_5V`.
- Connexion vers la broche 5 V du DevKitC uniquement après vérification de `H2.1`.
- No Connect requis : `U4.6 PGOOD`, `U5.4 NC`, broche 3V3 du module ESP32.

### Zone E — réserves P2-B, à conserver séparées de P2-A

Ces blocs sont prévus au même feuillet mais ne sont pas prêts à réaliser. Les contrôleurs provisoires ont été ajoutés dans EasyEDA le 23 septembre, sans connexion électrique; les autres composants ne sont pas encore posés :

- `U11` : TI LM5145RGYR, LCSC C485912, provisoirement réservé au bloc 10 (42 V → 12 V / 9 A).
- `U12` : TI LM5145RGYR, LCSC C485912, provisoirement réservé au bloc 11 (42 V → 5 V / 5 A).
- Les deux symboles U11/U12 ont été copiés depuis le même composant fabricant, regroupés côte à côte dans une zone P2-B dégagée du cadre A4. Une annotation visible les identifie comme provisoires et non câblés; elle signale les MOSFET, inductances, condensateurs, compensation et validation thermique encore requis. P2 a été enregistrée (« Saved successfully! »).
- R_RT10 et R_RT11 ont été ajoutées dans la partie inférieure droite de la feuille avec la référence fabricant `0603WAF1333T5E`, valeur 133 kΩ, empreinte R0603 et LCSC C22870. Leur placement correspond à la valeur 133 kΩ du plan P2-B; elles restent non câblées et ne constituent pas la validation des convertisseurs. La dernière sauvegarde EasyEDA a confirmé « Saved successfully! ».
- Le 25 septembre, EasyEDA a reçu puis, après relance de l’application, confirmé dans l’arborescence P2 `R_UV5_11` (1 MΩ, C22935), `R_UV6_11` (34,8 kΩ, C23141), `C_VCC11` (1 µF, 50 V, Samsung C15849), `C_BST10`/`C_BST11` (100 nF, 50 V, Yageo C14663). Ces composants restent séparés et non câblés; aucun statut de BOM approuvée n’est implicite. Une insertion de `DMG1012T-7` a été tentée mais n’est pas présente après réouverture et ne doit pas être comptée.
- Après la passe du 25 septembre, les quatre résistances `R_F1/R_F2` sont présentes; deux FETs d’inhibition provisoires C42412320 sont ajoutés (repères Q7/Q8 à confirmer). Les quatre MOSFETs synchrones, L10/L11, capacités d’entrée/sortie et symboles de compensation `TBD` restent à poser. Les composants de puissance, leurs empreintes, leur déclassement DC-bias et la compensation restent à sélectionner/calculer.

- **Bloc 10, 42 V → 12 V / 9 A** : `U6` LM5145RGYR; quatre MOSFETs au total pour les deux convertisseurs (`Q8/Q9` côté haut/bas; désignateurs uniques à fixer); `L10` 10 µH, Isat ≥ 11 A, DCR ≤ 5 mΩ; `Q7` d’inhibition DMG1012T-7; `R_RT` 133 kΩ; `R_UV5` 1 MΩ et `R_UV6` 34,8 kΩ; `C_VCC` 1 µF et `C_BST` 100 nF; entrée 4 × 10 µF / 100 V + 100 µF; sortie 4 × 22 µF / 25 V; `R_F1/R_F2` 10 kΩ / 715 Ω. `R_C`, `C_C1`, `C_C2` de compensation à calculer avec WEBENCH et les composants de sortie exacts.
- **Bloc 11, 42 V → 5 V / 5 A** : `U7` LM5145RGYR; les deux autres MOSFETs parmi les quatre requis (références et désignateurs uniques à fixer); `L11` 10 µH, Isat ≥ 6 A, DCR ≤ 5 mΩ; `Q7` d’inhibition DMG1012T-7 (désignateur unique à attribuer); `R_RT` 133 kΩ; `R_UV5` 1 MΩ et `R_UV6` 34,8 kΩ; `C_VCC` 1 µF et `C_BST` 100 nF; entrée 2 × 10 µF / 100 V + 100 µF; sortie 4 × 22 µF / 16 V; `R_F1/R_F2` 10 kΩ / 1,91 kΩ. Compensation `R_C`, `C_C1`, `C_C2` à calculer.
- **Quantités partagées par bloc** : 1 contrôleur, 2 MOSFETs synchrones, 1 inductance, 1 transistor d’inhibition, 1 réseau UVLO (2 résistances), 1 résistance RT, 1 paire de condensateurs de bootstrap/VCC, capacités d’entrée et sortie selon ci-dessus, réseau de compensation non chiffré. Total connu pour P2-B : 2 contrôleurs, 4 MOSFETs, 2 inductances, 2 transistors d’inhibition.
- **À ne pas saisir avant validation** : sélection MOSFET (100 V, ≤10 mΩ, Qg ≤30 nC; ne pas reprendre IPB017N10N5), sélection inductance/condensateurs avec modèles réels, compensation, tenue thermique et brochage des empreintes. Les références de passifs ci-dessus sont des valeurs/caractéristiques tirées du handoff, mais ne remplacent pas ces validations.
- **Désignateurs globaux** : le handoff réutilise des noms abrégés tels que `Q7`, `R_F1/R_F2`, `R_RT`, `R_UV5/R_UV6`, `C_VCC/C_BST` par convertisseur, alors que certains sont déjà employés ailleurs dans le schéma. Proposition de repères uniques pour la pose restante : `Q8`–`Q11` pour les quatre MOSFET synchrones (composant exact à sélectionner), `Q12/Q13` pour les deux inhibitions DMG1012T-7, `L10/L11`, `R_UV5_10/R_UV6_10` et `R_UV5_11/R_UV6_11`, `C_VCC10/C_BST10` et `C_VCC11/C_BST11`, `C_IN10_1..4`, `C_BULK10`, `C_OUT10_1..4`, `C_IN11_1..2`, `C_BULK11`, `C_OUT11_1..4`, et `R_F1_10/R_F2_10`, `R_F1_11/R_F2_11`. Pour la compensation différée, réserver `R_C10/C_C10_1/C_C10_2` et `R_C11/C_C11_1/C_C11_2`, avec valeur marquée `TBD—calculer`, sans empreinte/BOM définitive. Les repères proposés doivent être vérifiés contre la totalité de la hiérarchie du projet avant annotation finale.

**Matrice de pose P2-B (composants requis, regroupés par convertisseur)**

| Zone / repères proposés | Quantité | Valeur ou identité autorisée par le handoff | État à afficher dans EasyEDA |
|---|---:|---|---|
| 12 V : `U11`, `Q8/Q9`, `L10`, `Q12` | 5 | LM5145RGYR C485912; deux MOSFETs 100 V / ≤10 mΩ / Qg ≤30 nC encore à sélectionner; L10 10 µH / Isat ≥11 A / DCR ≤5 mΩ; DMG1012T-7 C20512 | Contrôleur déjà posé; symboles restants à placer. MOSFET et L10 en `TBD—sélectionner`, aucun device/footprint non validé |
| 12 V : `R_RT10`, `R_UV5_10`, `R_UV6_10`, `R_F1_10`, `R_F2_10` | 5 | 133 kΩ, 1 MΩ, 34,8 kΩ, 10 kΩ et 715 Ω; `R_RT10` C22870 est déjà posé | Toutes présentes; les résistances de retour sont proches du bord inférieur et doivent être regroupées/repositionnées. Pas de liaison au LM5145 avant revue de broches |
| 12 V : `C_VCC10`, `C_BST10`, `C_IN10_1..4`, `C_BULK10`, `C_OUT10_1..4` | 11 | 1 µF/50 V X5R C15849; 100 nF/50 V X7R C14663; 4 × 10 µF/100 V; 100 µF; 4 × 22 µF/25 V | Les deux petits condensateurs ont une référence de composant; C_IN/C_BULK/C_OUT restent à sélectionner avec empreinte et déclassement DC-bias compatibles |
| 5 V : `U12`, `Q10/Q11`, `L11`, `Q13` | 5 | LM5145RGYR C485912; deux MOSFETs mêmes critères électriques; L11 10 µH / Isat ≥6 A / DCR ≤5 mΩ; DMG1012T-7 C20512 | Contrôleur déjà posé; MOSFET et L11 à sélectionner; ne pas recopier de référence non vérifiée |
| 5 V : `R_RT11`, `R_UV5_11`, `R_UV6_11`, `R_F1_11`, `R_F2_11` | 5 | 133 kΩ, 1 MΩ, 34,8 kΩ, 10 kΩ et 1,91 kΩ | Toutes présentes; R_F1_11/R_F2_11 à regrouper et dégager du cadre. Aucun câblage avant revue |
| 5 V : `C_VCC11`, `C_BST11`, `C_IN11_1..2`, `C_BULK11`, `C_OUT11_1..4` | 9 | 1 µF/50 V X5R C15849; 100 nF/50 V X7R C14663; 2 × 10 µF/100 V; 100 µF; 4 × 22 µF/16 V | Même réserve de validation DC-bias, empreinte et disponibilité pour les condensateurs de puissance |
| Compensations `R_C10/C_C10_1/C_C10_2`, `R_C11/C_C11_1/C_C11_2` | 6 | Valeurs dépendantes du contrôleur, de L, du condensateur de sortie réel et de sa capacité effective | Placer comme symboles annotés `TBD—calcul WEBENCH`; ne pas inventer de valeurs ni déclarer les blocs réglés |

Cette matrice fixe le minimum des **46 instances** P2-B (incluant U11/U12 et R_RT10/R_RT11 déjà saisis) sans prétendre que les composants de puissance ou leurs empreintes sont validés. Les symboles génériques `TBD` servent à rendre la feuille complète fonctionnellement; ils ne devront pas apparaître dans une BOM de fabrication comme composants approuvés.

Garder chaque convertisseur en un bloc séparé : contrôleur au centre, MOSFETs et condensateurs d’entrée du côté `BUS+`, boucle de commutation et inductance proches, sortie/condensateurs puis retour FB regroupés; UVLO/inhibition à l’écart du nœud SW. Ne pas les intercaler avec les blocs 8/9/12.

### Revue d’état visible et fiches techniques — P2

À la revue visuelle EasyEDA du 2026-09-23, les passifs du bloc 8 sont éparpillés dans la feuille et plusieurs broches semblent encore sans fil/étiquette visible; leur connectivité doit être contrôlée par nets dans l’éditeur avant validation. Valeurs lisibles : `C9 = 3,3 nF`, `C10 = 270 pF`, `C7 = 2,2 nF`, `R7 = 31,6 kΩ`, `R9 = 68,1 kΩ`, `C11/C12 = 10 µF`, `C1/C2 = 1 µF`, ainsi que plusieurs `2,2 µF`. `L1` affiche 47 µH. Le handoff a une nomenclature plus ancienne (33 µH) mais précise plus loin (§6.2) que le propriétaire a choisi le remplacement Bourns `SRP1038A-470M`, 47 µH; conserver cette décision récente et harmoniser les repères `L1/L8` avant clôture.

La fiche TI actuelle du LM5164 (Rev. D) donne 6–100 V d’entrée et 1 A max, avec MOSFETs, biais VCC et diode de bootstrap intégrés : ne pas ajouter de condensateur VCC externe. Cela convient au bloc hôtel 42→5 V / 1 A sur le papier, mais ne certifie ni le réseau Type 3, ni les composants visibles, ni leur câblage. La fiche Diodes Inc. AP2112 indique 2,5–6 V d’entrée et 600 mA min.; l’alimenter depuis `+5V_HOT` est cohérent, mais calculer la dissipation avec le courant réel. Sources primaires : [LM5164 Rev. D (TI)](https://www.ti.com/lit/ds/symlink/lm5164.pdf), [AP2112 (Diodes Inc.)](https://www.diodes.com/datasheet/download/AP2112.pdf).

**Suite obligatoire P2 :** regrouper physiquement le bloc 8 en conservant les nets, valider les connexions de U4 broche par broche (notamment `EP` à GND, `PGOOD` non connectée), vérifier le nombre/placement des `C_IN8`, puis faire ERC et revue net-par-net. Pour P2-B, saisir uniquement les symboles génériques/valeurs nécessaires après validation des références MOSFET, inductances et condensateurs réels; dimensionner la compensation dans WEBENCH. Ne pas déclarer la feuille prête au routage avant que ces contrôles passent.

## P3 — Distribution et fusibles (4 symboles saisis, non raccordés; F1 hors-cadre)

### Zone A — arrivée `BUS+` et séparation des branches motrices

- Une entrée de rail `BUS+` et retour `GND` depuis le bloc contacteur.
- 4 protections de branche, une par variateur, **15 A chacune** (4 porte-fusibles + 4 fusibles; technologie/référence homologuée pour la tension DC réelle à sélectionner; ne pas prendre un modèle limité à 32 V sans vérification).
- Détection individuelle de fusible fondu : un circuit par branche, avec composants et seuils encore à concevoir. Ce sous-bloc doit être dupliqué quatre fois après choix de l’architecture de détection.
- `J3`, `J4`, `J5`, `J6` : sorties vers les quatre ZS-X11H.

Grouper chaque chaîne `BUS+ → fusible → détection → connecteur` horizontalement et la répéter quatre fois, dans l’ordre `J3` à `J6`. Les quatre retours `GND` suivent le même ordre. Aucun fusible principal en tête.

### Zone B — distribution compute 12 V

- Entrée rail `+12V_AUX`, retour `GND`; protection de cette branche requise, valeur, technologie et emplacement à arbitrer avec l’inventaire de fusibles externe.
- `J7` : sortie vers Youyeetoo X1, 12 V / 3 A.

### Zone C — sorties auxiliaires

- Pour la branche auxiliaire `+12V_AUX` : protection à définir, `J8` bornier +12 V, jusqu’à 5 A.
- Pour la branche auxiliaire `+5V_PWR` : protection à définir, `J9` bornier +5 V, jusqu’à 3 A.
- Réseaux `+12V_AUX`, `+5V_PWR` et `GND`; connecteurs/polarité et protections à confirmer selon les modèles réellement utilisés.

Ne pas ajouter de fusible principal 40 A sur cette feuille : le handoff demande quatre protections de branche sans fusible de tête.

### État EasyEDA — passe du 2026-09-23

P3 a été rouverte; la note fonctionnelle A–C reste en haut à gauche. Quatre symboles `F1`–`F4` ont ensuite été posés depuis le résultat EasyEDA/LCSC `0997015.WXN` (`C207027`, Littelfuse; interface affiche 15 A, 58 VDC et 1 kA à 58 V). À la vue d’ensemble F1 paraissait sous la note; la sélection de F1 dans l’arborescence centre toutefois la caméra sur le symbole à droite du cadre A4, et son placement hors cadre est confirmé. Aucun déplacement n’a été validé pendant la reprise actuelle. Les fusibles ne sont pas raccordés à `BUS+` ni aux sorties, et aucun porte-fusible PCB n’a été posé. La compatibilité candidate avec `178.6764.0001` n’est toujours pas verrouillée compte tenu des versions contradictoires des fiches. Cette insertion est une étape de schéma, pas une validation électrique ou de fabrication.

Ne pas annoncer P3 comme terminé : il faut sélectionner/connecter les composants après validation du rating DC et du type de porte-fusible, des connecteurs réels, des protections des branches auxiliaires et de la méthode de détection. La recherche LCSC « 15A fuse 58VDC » n’a pas permis d’identifier un modèle approprié dans les résultats consultés; les références de porte-fusible visibles étaient sans stock, les fusibles proposés sur la première page n’avaient pas la tenue DC requise démontrée.

### Recherche complémentaire de protections — 2026-09-23 (candidats, non figés)

Une recherche des fiches fabricant/LCSC a trouvé un couple Mini-blade potentiellement utilisable pour les quatre branches : Littelfuse `0997015.WXN` (15 A, 58 VDC, pouvoir de coupure 1 kA à 58 V; LCSC C207027; la page consultée indiquait 462 en stock) et porte-fusible PCB MINI FL1 `178.6764.0001` (LCSC C142933). Le fabricant publie pour le FL1 une révision 2025 à 58 VDC et 22 A continu / 30 A max; toutefois, LCSC/EasyEDA expose encore des fiches et champs contradictoires (ancienne fiche 32 V, métadonnées 125 V, état « non recommandé pour nouveaux designs », stocks affichés variables). **Ne pas figer ni placer ce couple tant que la révision applicable au numéro exact et son rating 58 V n’ont pas été confirmés dans la bibliothèque EasyEDA et le lot réellement disponible.** Sources : [fiche Littelfuse MINI 58 V](https://www.littelfuse.com/assetdocs/littelfuse-datasheet-997-mini58v?assetguid=838cc4ad-f429-4185-a8e8-ccc70cd2b713), [fiche Littelfuse FL1 58 V (rév. 2025)](https://www.littelfuse.com/assetdocs/mini-fl1-datasheet?assetguid=86e3ab08-0473-4acb-98d6-4cf3dbe2f0fa), [LCSC C207027](https://www.lcsc.com/ko/product-detail/Automotive-Fuses_Littelfuse_C207027.html), [LCSC C142933](https://www.lcsc.com/product-detail/C142933.html).

Un second porte-fusible PCB ATO/FKS Littelfuse `178.6165.0002` (C207061) est listé par LCSC, avec fiche constructeur 80 V et courant du porte-fusible annoncé à 40 A; mais le fusible ATO 58 V/15 A `142.6185.5156` correspondant apparaît sans stock/discontinué chez le distributeur consulté. Il ne constitue donc pas aujourd’hui un couple d’achat démontré. Sources : [fiche 80 V du porte-fusible](https://www.littelfuse.com/~/media/commercial-vehicle/datasheets/automotive-fuse-holders/ato/littelfuse-fuse-holder-ato-flr-pcb-datasheet.pdf), [état distributeur du fusible 142.6185.5156](https://www.digikey.com/en/products/detail/littelfuse-inc/142-6185-5156/2515782), [LCSC C207061](https://www.lcsc.com/zh-TW/product-detail/Fuseholders_Littelfuse-178-6165-0002_C207061.html).

**Actualisation de source/stock — 2026-09-23 :** la fiche fabricant 2025 confirme bien le `178.6764.0001` à 58 VDC, 22 A continus et 30 A maximum; la fiche Littelfuse `MINI 58 V` couvre `0997xxx.WXN`, avec pouvoir de coupure 1 kA à 58 V, et le distributeur donne `0997015.WXN` = 15 A. Le distributeur LCSC affiche aujourd’hui du stock pour les deux références (`C142933` et `C207027`; vue directe consultée : 6 324 et 484 respectivement), mais certains caches LCSC affichent seulement 384 porte-fusibles et le marquent **Not recommended for new designs**. Donc les ratings nominaux forment un couple possible au niveau des fiches, mais cette branche reste non gelée : rating de 58 V à comparer aux transitoires, déclassement thermique à 15 A, capacité de coupure au courant de défaut mesuré et statut NRND/lot disponible à revalider à l’achat. Sources : [fiche fabricant FL1 58 V](https://www.littelfuse.com/assetdocs/mini-fl1-datasheet?assetguid=86e3ab08-0473-4acb-98d6-4cf3dbe2f0fa), [fiche fabricant MINI fuse 58 V](https://www.littelfuse.com/assetdocs/littelfuse-datasheet-997-mini58v?assetguid=838cc4ad-f429-4185-a8e8-ccc70cd2b713), [LCSC C142933](https://www.lcsc.com/product-detail/C142933.html), [LCSC C207027](https://www.lcsc.com/product-detail/Automotive-Fuses_Littelfuse-0997015-WXN_C207027.html).

Même si le couple 58 V était confirmé, sa tension assignée n’est acceptable que si la tension maximale mesurée/calculée sur `BUS+` reste sous 58 V, marge transitoire comprise; le pouvoir de coupure 1 kA doit être comparé au courant de défaut réel limité par pack/BMS et au profil du moteur. Le courant continu admissible des branches doit également être comparé aux courbes temps-courant, température et déclassement, pas seulement au marquage 15 A. L’incertitude sur la régénération (M14/M15) reste donc un verrou électrique, indépendamment du stock.

## P4 — Contrôle, CAN et périphériques (CI posés; circuit incomplet)

### Zone A — interface logique de l’ESP32

- Raccords vers le module ESP32 et signaux inter-feuilles nécessaires; ne pas dupliquer le module déjà représenté par `H1/H2` en P1.
- Bus I²C partagé vers `PCA9555`, pull-ups `R_SDA` et `R_SCL` séparés (2,2 kΩ chacun, depuis `+3V3`, suivant P1) et condensateurs de découplage des circuits locaux, quantités à vérifier aux fiches techniques.

### Zone B — bus CAN

- 1 transceiver `SN65HVD230` (confirmer le modèle exact, la tension logique et son brochage contre sa fiche technique avant symbole/empreinte).
- 1 `J13` : connecteur CAN (`CANH`, `CANL`, `GND`; alimentation seulement si elle est requise par le faisceau retenu).
- Protection ESD sur les lignes CAN, terminaison commutable 120 Ω et son cavalier/interrupteur; quantités/références à figer selon la topologie et la position du nœud.

### Zone C — watchdog, expander et arrêt sûr

- 1 watchdog `TPL5010` et les composants de temporisation, `DONE/WAKE`, reset/pull-up définis par la fiche technique et la revue de la séquence de sûreté.
- 1 expander I²C `PCA9555` et ses résistances/découplages de bus; seuls les signaux non critiques retenus au handoff y passent.
- 1 interface pour le champignon d’arrêt d’urgence à contact NF; le bouton physique et son faisceau sont des éléments externes à la carte. L’interface électrique exacte reste à arrêter.
- 1 connecteur `J15` pour `/SAFE`, avec sorties sûres, résistances de rappel et protection de ligne à dimensionner. Le watchdog et l’arrêt d’urgence restent câblés matériellement hors de l’expander.
- Réseaux de reset, découplages et protections associées, à inventorier une fois le circuit détaillé.

### Zone D — ventilateurs et bandeau lumineux

- 2 ventilateurs PWM 12 V : 2 connecteurs, 2 commandes de puissance, 2 entrées tachymètre avec adaptation/protection; composants de commutation et valeurs à choisir selon les modèles de ventilateur. Les tachymètres ne se raccordent pas directement à un GPIO sans vérification de leur niveau électrique.
- 1 connecteur de bandeau de 20 × WS2812B, rail `+5V_PWR` et GND; 1 résistance série de données et 1 tampon 5 V compatible niveau logique 3,3 V (74AHCT125 envisagé, référence et brochage à valider), condensateurs de réserve selon le courant et la longueur de câble.

### Zone E — extensions

- Points de test pour rails/signaux et connecteurs de programmation/reset à définir selon les besoins de mise au point; les placer aux bords, hors de la zone CAN et de l’antenne ESP32.
- Les fonctions plus larges listées dans l’architecture (GPS, BNO085, capteurs) ne sont pas automatiquement ajoutées à `safety_power`; vérifier leur carte de destination.

### État EasyEDA — composants et annotations présents sur P4

| Repère | Composant choisi | Identité fournisseur | Zone | État |
|---|---|---|---|---|
| `U6` | TI SN65HVD230DR, SOIC-8 | LCSC C12084 | CAN | Présent dans le cadre A4; ne pas relier au connecteur avant d’avoir résolu le défaut bus 42 V par protection/choix de transceiver |
| `U7` | TI PCA9555DBR, SSOP-24 | LCSC C45293 | E/S I²C | Présent dans le cadre A4; C16 le chevauche actuellement |
| `U8` | TI TPL5010DDCR, SOT-23-Thin-6 | LCSC C473912 | Watchdog | Présent dans le cadre A4; la valeur d’affichage est TPL5010 |
| `U9` | TI SN74AHCT125DR, SOIC-14 | LCSC C155176 | Buffer de bandeau LED | Présent dans le cadre A4; connexions/fils verts proches à contrôler |

Dans la nomenclature P4, `U6` à `U9` occupent déjà ces repères; le handoff qui réserve U6/U7 aux blocs LM5145 de P2-B devra donc être renuméroté avant leur éventuelle saisie. `U6` à `U9` étaient présents dans EasyEDA et leur placement dans A4 reste à revoir par rapport à la topologie; la note visible distingue CAN, extension E/S, watchdog et adaptation logique. Des fils verts visibles restent à revoir net par net; aucune nouvelle connexion n’a été volontairement dessinée. Les symboles `C15` et `C16` ont depuis été ajoutés; C16 a été déplacé pour libérer le chevauchement sur U7 mais doit encore être placé au plus près de son alimentation une fois le net confirmé.

**Revue datasheet / composants manquants :** le TI SN65HVD230 recommande des condensateurs de bypass et bulk au plus près de VCC, et une protection transitoire externe près du connecteur CAN; la datasheet ne prescrit pas ici une valeur unique. La datasheet PCA9555 recommande les condensateurs bypass/découplage au plus près de VCC, sans fixer de valeur dans le passage de layout consulté. Le TI TPL5010 recommande explicitement un condensateur MLCC X7R de 0,1 µF entre VDD et GND. Il faut donc réserver **au moins un 100 nF local par U6–U9** (4 pièces au total, dont U8 a une recommandation TI explicite), en plus de la réserve de bus CAN. Le projet possède déjà le composant `C14663`, 100 nF C0603 Yageo `CC0603KRX7R9BB104`; EasyEDA affiche une fiche LCSC disponible. C8/C13/C14/C16 sont désormais groupés par zones présumées U7/U8/U9/CAN, sans câblage; C15 doit être identifié et rapproché du circuit restant. Cette proximité ne constitue pas une connexion : vérifier les nets et relier chaque composant uniquement après identification de VCC/GND.

**Matrice de pose P4, hors CI et condensateurs déjà présents**

| Zone | Instances à placer/regrouper | Identité ou valeur établie | À marquer comme indéterminé |
|---|---|---|---|
| CAN / connecteur | `J13`, connecteur CANH/CANL/GND; transceiver `U6` existe déjà | SN65HVD230 actuellement installé, mais incompatible avec un défaut 42 V documenté (broches CAN −4…+16 V absolus) | Référence du transceiver à arbitrer (TCAN1042HV est une option à refaire/revalider); TVS/ESD, terminaison commutable 120 Ω, cavalier/interrupteur, nombre exact de connecteurs |
| Expander / I²C | `R_SDA`, `R_SCL` auprès de `U7`; U7 existe déjà | 2,2 kΩ chacune; PCA9555 | Adresse, nets, placement et connexions après vérification avec le bus I²C de P1; composants de reset/pull-up seulement après définition |
| Watchdog / arrêt sûr | `U8` existe déjà; `J15` pour `/SAFE`; entrée externe NF d’arrêt d’urgence; composants DONE/WAKE/reset et polarisation | 100 nF local C14663 par CI à découpler; pas de raccordement du bouton à l’expander pour la fonction d’arrêt | Temporisation, filtre, pull-up/pull-down, protections et configuration de contact à dimensionner; sécurité matérielle à revoir |
| Deux sorties ventilateur | `J16/J17` (repères provisoires), 2 commutateurs de puissance, 2 réseaux tachymètres/protections | Besoin : deux ventilateurs PWM 12 V et deux retours tachymètre | Modèles de ventilateur, brochage PWM/tachy, MOSFETs, résistances de grille/pull-up, TVS et connecteurs exacts à sélectionner |
| Bandeau WS2812B | `J18` (provisoire), buffer `U9` déjà présent, résistance série données | Besoin : 20 pixels, logique d’entrée MCU 3,3 V vers données 5 V; U9 SN74AHCT125 présent | Connecteur et ordre des broches à confirmer; valeur/puissance de résistance série; capacité bulk selon longueur/courant; valider pinout/alimentation et capacités avec fiche exacte du bandeau |

Le routage bus CAN, le câblage de l’arrêt sûr et les connexions de puissance des ventilateurs restent interdits tant que les lignes « indéterminé » ne sont pas levées. Les désignateurs J16–J18 sont une proposition seulement, à vérifier contre les feuilles hiérarchiques avant attribution dans EasyEDA. Les cinq symboles 100 nF déjà observés (C8, C13–C16) dépassent le minimum de quatre découplages locaux; réaffecter/rapprocher après inspection de leurs nets, plutôt que d’en poser d’autres aveuglément.

### Écart de sources — U6 CAN, à résoudre avant câblage/validation

Le handoff le plus récent demande un transceiver `SN65HVD230`, qui est déjà placé comme U6 dans EasyEDA. En revanche, `docs/architecture/09-validation-composants.md` rejette explicitement ce composant : sa limite absolue sur CANH/CANL est −4 à +16 V alors qu’un défaut de faisceau pourrait exposer le bus CAN aux rails 42 V; ce document retient `TCAN1042HVDR`, annoncé ±70 V et avec VIO. Ce n’est pas une simple variante de BOM : il faut aussi modifier alimentation, pins et passifs (TCAN1042HV: VCC 5 V, VIO 3,3 V, bypass 4,7 µF + 100 nF côté VCC, 100 nF sur VIO, état de STB déterminé explicitement). L’inventaire EasyEDA actuellement note encore le SN65HVD230; **ne pas câbler ni déclarer la zone CAN sûre avant d’avoir arbitré cette contradiction et vérifié la référence/empreinte retenue sur sa fiche constructeur.** Sources primaires : [SN65HVD230 (TI)](https://www.ti.com/lit/ds/symlink/sn65hvd230.pdf), [TCAN1042HV (TI)](https://www.ti.com/lit/ds/symlink/tcan1042hv.pdf). La politique du projet est de suivre le handoff récent, mais elle ne supprime pas le risque électrique démontré par la fiche technique.

Une note d’inventaire/zones est maintenant visible dans la zone libre de P4 et enregistrée. Elle distingue CAN (`U6`), extension E/S (`U7`), watchdog (`U8`) et adaptation logique (`U9`); elle rappelle les pièces encore à sélectionner. Elle ne remplace ni les symboles des composants manquants, ni les connexions, ni le contrôle électrique. Une cinquième instance 100 nF, `C16`, est visible sur la page mais chevauche actuellement les broches de U7; elle doit être déplacée avant le câblage.

**Historique de la passe antérieure :** le dialogue était en `Half Offline` et les premières recherches n’avaient pas trouvé de résultat exploitable; la duplication de `C_DA` depuis P1 n’avait pas abouti. Cette limitation a été contournée lors de la reprise en sélectionnant la référence LCSC C14663 depuis la bibliothèque EasyEDA, sans toucher P1. `C8` et `C13`–`C16` sont maintenant listés sur P4 et sauvegardés; aucun n’est raccordé. C16 a été déplacé hors du chevauchement avec U7; C8 reste loin du circuit et le placement près des broches doit être fait après vérification des nets.

À faire : confirmer ces nets, placer les quatre `100 nF` près de VCC/GND des U6–U9 et connecter; terminer la logique matérielle du watchdog et du `/SAFE`, choisir les protections et terminaison CAN, fixer les connecteurs réels et documenter les broches; guider chaque connexion par les fiches techniques. Sources primaires : [datasheet SN65HVD230 (TI)](https://www.ti.com/lit/ds/symlink/sn65hvd230.pdf), [datasheet PCA9555 (TI)](https://www.ti.com/lit/ds/symlink/pca9555.pdf), [datasheet TPL5010 (TI)](https://www.ti.com/lit/ds/symlink/tpl5010.pdf), [datasheet SN74AHCT125 (TI)](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf).

## P5 — Hacheur de freinage (squelette de composants saisi; détails bloqués par M15)

### Rôle du hacheur et décision M15

Quand le robot ralentit ou qu’une roue est entraînée par le sol, le moteur peut fonctionner en génératrice et renvoyer de l’énergie vers `BUS+`. Si la batterie/BMS ne peut pas absorber ce courant, la tension du bus peut monter au-delà de sa limite. Le hacheur surveille cette tension puis commute `Q6` pour raccorder brièvement une résistance de dissipation au bus : l’énergie électrique excédentaire y est transformée en chaleur, ce qui limite la surtension. Il s’agit d’un dispositif de dissipation/protection, pas d’un chargeur, d’un récupérateur d’énergie, ni du mécanisme qui garantit à lui seul l’arrêt mécanique du robot.

Le hacheur ne doit être conservé que si le test M15 établit que le BMS n’absorbe pas suffisamment la régénération ou que `BUS+` dépasse une limite admissible. Si le BMS accepte le courant et maintient la tension dans les limites de tous les composants, ce bloc peut être inutile; le garder sans nécessité ajoute un chemin de puissance qui peut chauffer en défaut. Aucun seuil « 42,5 V » ni aucune résistance ne sont donc figés par le simple fait que ces composants figurent dans le schéma.

**Alerte de compatibilité importante :** le handoff dit que le circuit doit être autoalimenté depuis `BUS+`, mais le `TLV1701-Q1` actuellement prévu (`U10`) n’est spécifié que pour 2,2–36 V d’alimentation et sa limite absolue d’alimentation est 40 V. Un bus à 42–42,5 V ne peut donc pas alimenter directement U10; son alimentation doit être abaissée/protégée et la mesure du bus divisée/protégée avant raccordement. L’indication « seuil 42,5 V » ne valide pas le circuit autour de ce comparateur. Source constructeur : [fiche technique TI TLV170x-Q1](https://www.ti.com/lit/ds/symlink/tlv1701-q1.pdf).

Pour le dimensionner après M15, il faudra relever la tension maximale et la durée des épisodes de régénération, estimer/mesurer l’énergie à absorber, puis vérifier la résistance (valeur minimale, courant et énergie impulsionnels, puissance moyenne/refroidissement), `Q6` (SOA en impulsion, avalanche éventuelle, commande de grille et thermique), la protection et l’hystérésis. Le seuil doit être coordonné avec la tension maximale du pack/BMS et les limites du bus, pas choisi indépendamment.

### Zone unique, à découper en sous-zones puissance / commande analogique

- Connecteur/pads d’entrée `BUS+` et retour de puissance `GND`.
- 1 comparateur analogique et référence de tension; seuil nominal provisoire 42,5 V avec hystérésis à concevoir puis recaler selon système et mesures.
- 1 `Q6` MOSFET de freinage, tenue minimale 100 V; courant, RDS(on), SOA, charge de grille et dissipation à calculer.
- 1 résistance de dissipation (éventuellement banc parallèle seulement après calcul), valeur et capacité impulsionnelle/thermique déterminées par M15 et bilan énergétique.
- Réseau de commande analogique, polarisation de grille, hystérésis, protections et composants de stabilité à dimensionner sur les fiches techniques.
- Points de test sur BUS+, seuil comparateur, grille Q6, résistance/courant et GND.

**Blocage :** aucune valeur de résistance de freinage ne doit être choisie avant M15 (tension BUS+ induite en roue libre/poussée), le calcul de l’énergie régénérative et la vérification thermique. Ce bloc doit fonctionner sans l’ESP32.

### Composants et revue datasheet — provisoires, à confirmer après M15

- `U10` : TI `TLV1701QDBVRQ1`, LCSC C702102, SOT-23-5. Il a été repositionné dans le cadre A4 de P5 et la feuille sauvegardée le 23 septembre; il demeure non raccordé et doit être rapproché de son réseau de commande analogique lorsque les passifs seront dimensionnés. La fiche constructeur autorise 2,2–36 V d’alimentation, entrée rail-à-rail et sortie collecteur ouvert; une mesure BUS+ 42,5 V ne doit donc **pas** être reliée directement à son alimentation ni hors plage à ses entrées. Prévoir une alimentation ≤36 V et diviser BUS+ en dessous de la plage d’entrée, avec résistances encore à calculer. La sortie à collecteur ouvert exige une résistance de rappel et une commande de grille à valider. La fiche mentionne un délai typique de 560 ns. Source primaire : [TI TLV170x-Q1](https://www.ti.com/lit/ds/symlink/tlv1701-q1.pdf).
- `Q6` : Vishay `SiR870ADP-T1-GE3`, LCSC C506607, symbole posé mais non relié. Candidat seulement : la fiche garantit 100 V et RDS(on) max de 6,6 mΩ à VGS=10 V; la charge totale de grille maximale est 80 nC dans les conditions datasheet (VDS=50 V, VGS=10 V, ID=20 A). Il ne satisfait donc pas le critère de conception P2-B `Qg ≤30 nC`, qui ne doit pas être copié aveuglément au hacheur P5; son adéquation P5 dépend du courant, de l’énergie, de la SOA impulsionnelle, du refroidissement et du pilote de grille. Bibliothèque EasyEDA au 2026-09-23 : elle affiche 3000 en stock pour C506607, en contradiction avec la vérification antérieure « sans stock »; disponibilité à revérifier avant nomenclature/achat. Source primaire : [Vishay SiR870ADP](https://www.vishay.com/docs/63657/sir870adp.pdf).

La note M15 reste le verrou du **dimensionnement**, pas une autorisation à déclarer ces deux candidats définitifs. Aucun réseau de seuil/hystérésis, résistance de dissipation, rappel/pilote de grille, protection, connecteur ou point de test n’a encore été posé/câblé. Ne pas relier directement le bus 42 V à U10; calculer la division et l’hystérésis sur seuil réel après M15. Déterminer la résistance de freinage uniquement après le calcul d’énergie et la vérification impulsionnelle/thermique. Garder la voie de puissance (`BUS+` → Q6 → résistance → GND) dans sa zone thermique et U10/réseau de commande dans une zone distincte mais proche de la grille, avec un retour de mesure propre.

**Matrice de pose P5 (unité de freinage autonome, composants de puissance interdits avant M15)**

- Zone puissance : connecteur d’entrée `J19` (repère à vérifier) ou deux pads de BUS+/GND, MOSFET Q6 déjà candidat; symbole `R_BRAKE` ou banque (valeur et empreinte `TBD—M15 + énergie + thermique`). Ajouter les points de test BUS+, drain/grille, courant et GND uniquement après vérification des distances/accès.
- Zone mesure analogique : U10 déjà candidat; réserver deux résistances de diviseur BUS+, résistance de référence/biais et réseau d’hystérésis avec noms `R_SENSE_P5_A/B`, `R_HYST_P5`, `R_REF_P5`, valeurs `TBD—calculer`, sans connexion au bus jusqu’à validation de la plage commune et de l’alimentation U10 (2,2–36 V).
- Zone commande : résistance de pull-up obligatoire pour la sortie collecteur-ouvert du TLV1701-Q1, étage/polarisation de grille, résistance série et pull-down; désignateurs `R_PU_P5`, `QDRV_P5`, `R_G_P5`, `R_GS_P5` provisoires, composants exacts et valeurs `TBD—datasheet/SOA`.
- Zone alimentation et protection : découplage local U10, protection contre transitoires au connecteur, et éventuellement dispositif d’alimentation/régulation du comparateur; référence/valeur à choisir pour garder alimentation et entrées sous les limites TI en tout scénario. La seule tension BUS+ ne peut alimenter directement U10 ni son entrée de mesure.

Tous les « TBD » de P5 peuvent être représentés et regroupés comme composants génériques/notes de conception dans le schéma afin de rendre visibles les fonctions manquantes, mais ni Q6, ni le freinage, ni le seuil 42,5 V ne deviennent ainsi approuvés. L’essai M15 sur l’acceptation de charge par le BMS, l’énergie régénérée et l’enveloppe thermique restent des critères préalables à la sélection réelle.

## Règles de mise en page

1. Placer d’abord les composants d’un même nœud ou sous-bloc dans la même zone ; garder les signaux de puissance et de commande visuellement distincts.
2. Conserver U4 et son réseau SW/BST/filtre Type 3 compacts ; garder la boucle de commutation courte.
3. Garder les condensateurs de découplage près des broches d’alimentation concernées.
4. Placer chaque connecteur de sortie près de sa protection correspondante ; répéter les branches dans le même ordre J3→J6.
5. Ne jamais compter une proximité graphique comme une connexion électrique ; vérifier nets, ancres, jonctions et ERC séparément.
6. Les pages P3–P5 restent des plans fonctionnels tant que les composants spécifiques, calculs et fiches techniques ne sont pas validés.
