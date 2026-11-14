# Outils de conception PCB

**Objectif** : que la conception soit pilotable entièrement en ligne de commande et
par fichiers texte, pour que Claude puisse dessiner, vérifier et exporter les cartes,
et que William relise dans l'interface graphique.

## Pourquoi KiCad, et pas EasyEDA Pro

| | EasyEDA Pro (v1) | **KiCad 10** |
|---|---|---|
| Format des fichiers | archive binaire `.epro2` | **texte** (S-expressions), diff lisible dans git |
| Pilotage sans interface | aucun : la v1 était saisie par capture d'écran | **`kicad-cli`** : ERC, DRC, Gerber, BOM, PDF, rendu 3D |
| Scripts | non | **Python** (`pcbnew`, API IPC) |
| Vérification en CI | impossible | ERC et DRC à chaque commit |
| Bibliothèque LCSC | intégrée | importée par `easyeda2kicad` |
| Commande JLCPCB | intégrée | plugin Fabrication Toolkit, ou export scripté |
| Licence | propriétaire, en ligne | GPL, hors ligne |

EasyEDA reste installé ; il peut servir à consulter les composants LCSC.

## La chaîne

```
  icd.yaml ──► script Python ──► schéma KiCad (.kicad_sch)
                                       │  kicad-cli sch erc        ← règles électriques
                                       │  kicad-cli sch export pdf ← relecture par William
                                       ▼
                                 carte KiCad (.kicad_pcb)
                                       │  placement scripté (pcbnew)
                                       │  routage : Freerouting, puis reprise manuelle
                                       │  kicad-cli pcb drc         ← règles JLCPCB
                                       │  kicad-cli pcb render      ← vue 3D pour relecture
                                       ▼
                                 Gerber · perçage · BOM · placement   → JLCPCB
```

## À installer

| Outil | Rôle | Installation | Taille |
|---|---|---|---|
| **KiCad 10.0** | CAO, `kicad-cli`, module Python `pcbnew`, ngspice | `brew install --cask kicad` | ~6 Go avec bibliothèques |
| **Java ≥ 25** | requis par Freerouting 2.5 (classes compilées en Java 25) | `brew install openjdk` | ~350 Mo |
| **Freerouting 2.5** | autorouteur (DSN → SES) | `.jar` depuis les releases GitHub `freerouting/freerouting` | ~65 Mo |
| **easyeda2kicad** | importe symbole, empreinte et 3D à partir d'une référence LCSC | `pip`, dans l'environnement ci-dessous | léger |
| **kicad-skip** | lit et modifie les schémas `.kicad_sch` en Python | idem | léger |
| **KiBot** | génère toutes les sorties de fabrication depuis un fichier YAML | idem | léger |
| **KiKit** | panélisation, presets JLCPCB | idem | léger |

KiCad s'installe par Homebrew mais demande le mot de passe administrateur
(`sudo`, pour `/Library/Application Support/kicad`) : la commande se lance dans un
terminal où William peut le taper.

## Emplacements sur la machine de William

| Quoi | Où |
|---|---|
| KiCad, `kicad-cli` | `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` |
| Java | `/opt/homebrew/opt/openjdk/bin/java` (keg-only, hors `PATH`) |
| Freerouting | `~/.local/share/freerouting/freerouting-2.5.0.jar` |
| Outils Python | environnement virtuel `~/.local/share/retriever-pcb-venv` |

Les outils Python vivent dans un environnement virtuel dédié, **construit sur le
Python fourni avec KiCad** (3.9) et non sur celui du système : KiKit et KiBot
importent le module `pcbnew`, compilé pour ce Python-là.

```bash
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 -m venv --system-site-packages ~/.local/share/retriever-pcb-venv
```

```bash
~/.local/share/retriever-pcb-venv/bin/pip install easyeda2kicad kicad-skip kikit kibot skidl
```

Optionnel :

| Outil | Rôle |
|---|---|
| **SKiDL** (installé dans l'environnement) | décrire un circuit en Python et en tirer une netlist, utile pour vérifier une carte contre l'ICD |
| **Interactive HTML BOM** (plugin KiCad) | aide au placement des composants soudés à la main |
| **ngspice** (inclus dans KiCad) | simuler le filtre Hall, le comparateur du hacheur, la précharge |

Espace disque : environ 7 Go au total. 28 Go sont libres sur la machine au
10 novembre 2026.

## Ce que fait Claude, ce que fait William

| Étape | Claude | William |
|---|---|---|
| Composants | vérifie stock et prix LCSC, importe les bibliothèques | valide les choix |
| Schéma | écrit les feuilles depuis l'ICD, lance l'ERC | **relit le PDF** |
| Placement | place par script selon les zones (puissance, signal, connecteurs en bordure) | ajuste dans KiCad si besoin |
| Routage | autoroute les signaux, route à la main les pistes de puissance par script, lance le DRC | **relit le rendu 3D** et les plans de cuivre |
| Fabrication | génère Gerber, BOM, placement depuis un commit étiqueté | **passe la commande** et paie |

Claude ne passe aucune commande et n'entre aucun moyen de paiement.

## Limites, dites honnêtement

- **Le schéma généré par script est juste mais pas beau.** La lisibilité demande
  une reprise de la mise en page dans l'interface. Prévoir une passe par feuille.
- **Le routage automatique ne convient pas à la puissance.** Les pistes du
  contacteur, du hacheur et des shunts Kelvin de `safety_power` seront tracées
  avec des règles explicites (largeur, cuivre, coutures de vias), pas par
  Freerouting.
- **Le contrôle visuel passe par des rendus** (`kicad-cli` en SVG ou PNG) ; il ne
  remplace pas la relecture de William dans KiCad.

## Le générateur

Les cartes ne sont pas dessinées à la souris. Un script Python par carte
(`<carte>/scripts/build.py`) décrit le circuit **une seule fois** : composants,
références LCSC, broche par broche, et position sur la carte. Deux modules
communs en tirent les deux fichiers KiCad :

| Module | Rôle |
|---|---|
| [`scripts/kicadgen.py`](scripts/kicadgen.py) | écrit le schéma `.kicad_sch` (symboles des bibliothèques KiCad, une étiquette de réseau par broche) |
| [`scripts/kicadpcb.py`](scripts/kicadpcb.py) | construit la carte : empreintes liées aux symboles par UUID, règles, plans de cuivre, aller-retour Freerouting |
| [`scripts/fab.py`](scripts/fab.py) | BOM et fichier de placement au format JLCPCB |

Parce que schéma et carte sortent de la même description, le contrôle
« parité schéma » du DRC doit toujours donner 0. Les UUID sont déterministes :
régénérer ne casse pas le lien entre les deux.

Ordre de construction (`build.sh`) : schéma → placement → remplissage des plans
par `kicad-cli` → routage Freerouting → plans de cuivre → remplissage → ERC et
DRC. Les plans de cuivre sont posés **après** le routage : posés avant,
Freerouting compte sur eux pour la masse et le 5 V, puis les pistes les
découpent en îlots.

## Organisation des fichiers par carte

```
hardware/pcb/<carte>/
  cahier-des-charges.md
  README.md
  kicad/
    <carte>.kicad_pro
    <carte>.kicad_sch        + feuilles hiérarchiques
    <carte>.kicad_pcb
    lib/                     symboles, empreintes, modèles 3D importés de LCSC
  scripts/                   génération depuis l'ICD, placement
  fab/                       sorties de fabrication, générées, jamais éditées
```

## Vérification après installation

```bash
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli version
```

```bash
/opt/homebrew/opt/openjdk/bin/java -jar ~/.local/share/freerouting/freerouting-2.5.0.jar --help
```

```bash
~/.local/share/retriever-pcb-venv/bin/python -c "import pcbnew; print(pcbnew.Version())"
```

## Chaîne validée le 10 novembre 2026

Sur une carte de démonstration KiCad :

| Étape | Commande | Résultat |
|---|---|---|
| Règles électriques | `kicad-cli sch erc` | rapport produit |
| Règles de fabrication | `kicad-cli pcb drc` | rapport produit |
| Gerber | `kicad-cli pcb export gerbers` | 21 couches |
| Schéma PDF | `kicad-cli sch export pdf` | ✅ |
| Rendu 3D | `kicad-cli pcb render` | PNG ✅ |
| Routage automatique | `pcbnew.ExportSpecctraDSN` → Freerouting sans interface → `pcbnew.ImportSpecctraSES` | 14 réseaux routés en 0,6 s, 0 non connecté |
| Import LCSC | `easyeda2kicad --full --lcsc_id=C88056` | symbole, empreinte, modèles STEP et WRL de l'`ACT45B` |

Pièges rencontrés :
- `kicad-cli` refuse un motif qui désigne plusieurs fichiers : nommer le fichier.
- `easyeda2kicad` exige que le dossier parent de `--output` existe.
- macOS n'a pas `timeout` : ne pas s'en servir dans les scripts.
