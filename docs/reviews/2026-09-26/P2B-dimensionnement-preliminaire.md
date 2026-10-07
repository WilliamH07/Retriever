# P2-B — revue préalable des deux convertisseurs

26 septembre 2026. **Calculs préliminaires, non validés pour fabrication.** Aucun câblage P2-B n'a été appliqué pendant cette passe : le Mac est verrouillé. U11/U12 restent dans l'état de la netlist `Netlist_Power_Interface_P4_CAN_2026-09-26.enet`.

Le périmètre est `BUS+ → +12V_AUX / 9 A` et `BUS+ → +5V_PWR / 5 A`. P1 reste gelée. Les résultats numériques sont conservés dans `P2B-preliminary-calculations.json`, avec les hypothèses et les unités.

## Correction indispensable : fréquence

La résistance **133 kΩ** du handoff §6 ne programme pas 300 kHz sur un LM5145. La relation est `R_RT[kΩ] = 10⁴ / f_SW[kHz]`. La table 8-1 donne **33,2 kΩ pour 300 kHz**. Le calcul donne 301,2 kHz. Référence de saisie proposée : **0603WAF3322T5E / C23003**, ±1 %, à vérifier dans la bibliothèque native.

L'ancienne formule `4 × 10⁴ / R` comporte un facteur quatre incorrect. Une extrapolation avec 133 kΩ donne seulement 75,2 kHz, sous la plage spécifiée ; elle ne garantit pas que le circuit fonctionne à cette fréquence. Elle illustre cependant pourquoi le dimensionnement ne peut pas conserver cette valeur : avec 10 µH, l'ondulation théorique serait 11,4 A sur le 12 V et 5,86 A sur le 5 V, au lieu de 2,86 A et 1,47 A à 300 kHz. Les crêtes correspondantes seraient 14,7 A et 7,93 A à pleine charge.

Source : [TI LM5145 Rev. B, §8.3.6.1 et table 8-1](https://www.ti.com/lit/ds/symlink/lm5145.pdf).

## UVLO et séquence de précharge

Calcul pour les résistances proposées **1 MΩ / 34,8 kΩ** :

| Résultat | Typique | Coins calculés |
|---|---:|---:|
| Démarrage | 35,683 V | 33,950–37,471 V |
| Arrêt | 25,683 V | 23,060–28,381 V |
| Hystérésis typique | 10 V | — |

Les coins combinent résistances ±1 %, référence EN 1,164–1,236 V et courant d'hystérésis 9–11 µA. Ils excluent courants de fuite et dérive des résistances. Les équations employées sont `Von = VEN × (1 + Rhaut/Rbas)` et `Voff = Von − Ihys × Rhaut`.

**Le seuil de 35,7 V ne suffit pas à empêcher la charge pendant la précharge.** À batterie 42 V, il représente 85 %, alors que le handoff exige 95 % avant fermeture du contacteur. Avec la résistance de précharge 10 Ω et un modèle idéal sans chute de diode, la puissance disponible au bus n'est que 22,49 W à 85 %, puis 8,38 W à 95 %. Les deux rails demanderaient jusqu'à 133 W en sortie. Leur activation avant fermeture peut donc empêcher la montée du bus. Ce calcul est un contre-exemple de fonctionnement à pleine charge, pas une mesure du démarrage réel.

La séquence à concevoir doit maintenir les convertisseurs inhibés pendant la précharge, puis les autoriser après confirmation de fermeture et de tension du bus. Elle doit également prévoir le reset ESP/PCA, le défaut de commande et le bus régénéré avec alimentation logique absente. Une résistance haute de 100 kΩ réduirait l'hystérésis à environ 1 V, mais ne résoudrait ni cette séquence ni le démarrage sur batterie partiellement déchargée. Aucun remplacement de diviseur n'est figé ici.

Un démarrage à 35,7 V bloque aussi un redémarrage à froid lorsque le pack est sous ce seuil, même si le convertisseur précédemment démarré peut continuer jusqu'au seuil d'arrêt. Choisir la plage de batterie utilisable avec M1, puis dimensionner l'UVLO pour cette plage.

Le DMG1012T envisagé en tirage vers GND de EN/UVLO **inhibe lorsque sa grille est haute**. Les noms `EN_12V` et `EN_5V` doivent donc préciser cette inversion dans le contrat de commande. Un pull-up de grille vers +3V3 pourrait assurer l'inhibition au reset du PCA, mais ne suffit pas lorsque +3V3 est absent et BUS+ est présent. Ne pas supposer que les sorties du PCA ont une valeur active garantie à la mise sous tension.

## Courants et inductances

Modèle de buck idéal en conduction continue : `D = Vout/Vin`, `ΔI = Vout × (1−D)/(L × f)`, `Icrête = Iout + ΔI/2` et `Irms = √(Iout² + ΔI²/12)`.

| Cas | 12 V / 9 A | 5 V / 5 A |
|---|---:|---:|
| Ondulation, 42 V / 10 µH / 300 kHz | 2,857 A | 1,468 A |
| Crête dans ce cas | 10,429 A | 5,734 A |
| Crête, 42 V / 8 µH / 270 kHz | 10,984 A | 6,020 A |
| Crête, 75 V / 8 µH / 270 kHz | 11,333 A | 6,080 A |
| Courant RMS d'entrée, nominal, sans correction d'ondulation | 4,066 A | 1,619 A |
| Courant RMS des capacités de sortie, nominal | 0,825 A | 0,424 A |

270 kHz est un point de balayage de conception ; il ne représente pas une tolérance garantie de TI à 300 kHz. 8 µH représente −20 % de tolérance initiale et **n'inclut pas** la baisse supplémentaire sous courant/température. 75 V est une borne de comparaison du contrôleur, pas l'enveloppe validée du bus du robot.

La marge de saturation de 11 A / 6 A du handoff est insuffisante comme seul critère : il faut couvrir les surcharges jusqu'au courant de crête maximal effectivement limité, ainsi que la baisse d'inductance.

**Candidat réel : Bourns SRP2313AA-100M / C2045635**, 10 µH ±20 %, DCR maximale 4,15 mΩ, boîtier 23,5 × 22 mm, hauteur maximale 13 mm. La [fiche constructeur actuelle](https://www.bourns.com/docs/product-datasheets/srp2313aa.pdf) indique Irms typique 33 A et Isat typique 28 A pour une baisse de L de 30 %. L'ancienne fiche associée au catalogue LCSC indique 30 A / 20 A : conserver cette différence de révision dans la revue d'achat. Ces valeurs typiques ne sont pas des minima garantis.

À 42 V et 300 kHz, la perte cuivre calculée avec DCR maximale vaut 0,339 W sur le 12 V et 0,104 W sur le 5 V à 25 °C ; l'estimation à 100 °C devient 0,439 W et 0,135 W. Elle ne comprend pas les pertes de noyau ni les pertes AC. Le candidat satisfait la cible de DCR et dispose d'une marge de courant utile, mais sa taille, les courbes L(I,T), les pertes à 300 kHz, l'empreinte et le courant limite restent à valider avant sélection finale. Pas de placement effectué.

## MOSFET : candidat et limites de preuve

**BSC070N10LS5 / C534362** est un candidat de simulation : 100 V, PG-TDSON-8 avec pad thermique, RDS(on) maximale 8,5 mΩ à 4,5 V et 7 mΩ à 10 V. Le fabricant le marque actif. Sa [fiche Infineon Rev. 2.2](https://www.infineon.com/assets/row/public/documents/24/49/infineon-bsc070n10ls5-datasheet-en.pdf) donne Qg maximale **20 nC à 4,5 V**, mais seulement Qg(sync) **typique 26 nC à 10 V**. Ces conditions ne permettent pas d'affirmer une Qg maximale ≤30 nC à la commande 7,5 V. Il n'est donc pas déclaré entièrement conforme à la cible du handoff.

Sur le modèle nominal, deux MOSFET de 8,5 mΩ donnent ensemble environ 0,694 W de conduction sur le 12 V et 0,214 W sur le 5 V, avant majoration en température. Ajouter commutation, Qoss, récupération de diode, temps mort et commande de grille pour un bilan complet. Les puissances annoncées avec boîtier maintenu à 25 °C ne sont pas une capacité de dissipation de la carte.

Exemple de budget de polarisation interne, avec 25 nC par MOSFET à 300 kHz : courant de grille moyen 15 mA par contrôleur ; à VIN 42 V et VCC 7,5 V, perte LDO liée aux grilles ≈0,518 W. En ajoutant 1,8 mA de courant de contrôle pris sur VIN, l'ordre de grandeur devient 0,593 W par contrôleur. Ce résultat doit être refait avec les modèles choisis. Le refroidissement des deux contrôleurs est à traiter ; une polarisation externe issue du 12 V modifierait la tension de grille et la séquence entre rails.

Références écartées comme remplacements conformes directs : SiR870ADP (Qg trop grande), CSD19534Q5A (RDS(on) trop élevée), AON6294 (RDS(on) à 6 V jusqu'à 14 mΩ et Qg jusqu'à 40 nC à 10 V), AON6276 (80 V). Ne pas confondre une courbe typique et une limite garantie.

## Boucle, protections et câblage à préparer

Les diviseurs 10 kΩ / 715 Ω et 10 kΩ / 1,91 kΩ donnent respectivement 11,989 V et 4,988 V. En combinant ±1 % résistances, référence 0,792–0,808 V et biais FB ±0,1 µA : plages calculées 11,649–12,338 V et 4,855–5,125 V, hors dérive des résistances et ondulation.

La capacité nominale de 4 × 22 µF ne définit pas la capacité effective ni l'ESR de chaque rail. Fixer les références, les modèles sous polarisation et les transitoires de charge, puis effectuer WEBENCH comme demandé au handoff §10.3. Le réseau Type III complet exige `RC1`, `CC1`, `CC2`, `RC2`, `CC3` ; aucune valeur de compensation n'est validée ici.

La limitation par RDS(on) agit sur la **vallée** du courant : `Ivallée ≈ IILIM × RILIM / RDS(on)` et `Icrête ≈ Ivallée + ΔI`. Couvrir dispersion du MOSFET, courant ILIM, offset du comparateur et températures respectives du MOSFET et du contrôleur. La fiche ne garantit pas une RDS(on) minimale : prendre sa valeur maximale pour calculer RILIM ne borne pas la crête maximale en surcharge. Le réseau inclut aussi CILIM et sa constante de temps ; il est absent des anciens brouillons.

Le choix de synchronisation est fonctionnel : SYNCIN à GND permet l'émulation de diode, tandis qu'une horloge ou un état haut impose le PWM forcé avec courant inverse possible à faible charge. L'entrelacement des deux rails ne doit donc pas être ajouté uniquement pour réduire l'ondulation d'entrée sans revoir les retours d'énergie.

## Contrôle documentaire symbole/empreinte

L'export natif P2 contient 21 pads dans l'empreinte `c7671b3a46aa9a1e` : 1–20 périphériques et **21 central**. Le symbole possède EP15 et EP21. La fiche TI confirme que la broche 15 est reliée intérieurement au pad exposé, lequel est isolé des circuits internes. Le double EP du symbole est donc cohérent avec la représentation de cette empreinte ; ce n'est pas un doublon à supprimer.

Pour les deux contrôleurs, la saisie devra relier **6 AGND, 12 PGND, 15 EP et 21 pad exposé au GND**, avec des chemins de retour appropriés au routage. Les broches 9 et 16 sont NC. Cette inspection résout l'ambiguïté de numérotation ; elle ne valide pas les dimensions de l'empreinte, la pâte thermique ou le PCB.

## État pour la reprise Computer Use

Prochaines actions : contrôler C23003 et C2045635 dans la bibliothèque native ; sélectionner les modèles de condensateurs et MOSFET ; établir la commande d'inhibition et l'enveloppe d'entrée ; dimensionner ILIM et les deux compensations ; seulement alors câbler U11/U12 et exporter netlist/BOM/DRC. Les mesures M1, M14 et les transitoires de charges doivent être intégrés à la validation. Aucun calcul de ce document ne constitue un essai au banc.

## Mise à jour native du 28 septembre 2026

La bibliothèque EasyEDA a été consultée pour `C23003` : la ligne exacte est `0603WAF3322T5E`, UNI-ROYAL, **33,2 kΩ ±1 %**, empreinte R0603, classe JLCPCB « Extended Part ». Le stock JLCPCB affiché lors du contrôle était de 9 005 pièces ; il devra être revérifié avant commande. Le gestionnaire de remplacement a changé **R_RT10 et R_RT11 ensemble**, de la pièce 133 kΩ `C22870` vers `C23003`, sans changer leurs repères ni leur empreinte. Les propriétés des deux composants ont été relues dans EasyEDA et la sauvegarde globale a affiché « Saved successfully! ».

Une saisie d'étiquettes `RT_12V`, `RT_5V` et `GND` a ensuite été lancée sur les deux résistances. La feuille P2 affichait encore l'indicateur de modifications non enregistrées au moment où l'interface a cessé d'accepter les entrées. La connexion effective des broches de R_RT10/R_RT11, et surtout des broches RT de U11/U12, **n'est pas validée par une netlist exportée**. Ne pas compter cette étape comme un câblage terminé. Au retour de l'interface, contrôler les quatre broches des résistances et U11.2/U12.2 dans une nouvelle netlist, enregistrer la source native, puis refaire le DRC. Les autres broches des deux convertisseurs restent à traiter selon le dimensionnement et la séquence de sécurité décrits ci-dessus.
