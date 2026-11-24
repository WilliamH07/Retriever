# Brouillon — message à PCBWay

À envoyer par William depuis son compte PCBWay (messagerie du programme de sponsoring
ou e-mail du contact sponsoring). Rien n'a été envoyé. Joindre les fichiers de `fab/`.

---

**Subject:** Retriever robot — sponsored order, mainboard PCB + SMD assembly (60 € sponsorship)

Hello PCBWay team,

Thank you again for sponsoring the Retriever project (60 €). Retriever is an open-source
four-wheel mobile robot (ESP32 nodes, CAN bus, 10S lithium pack). The design files are public
on GitHub.

I would like to order our main board and would appreciate a quote before I place the order.

**Board**

- Size 180 × 150 mm, 2 layers, 1.6 mm FR-4.
- 2 oz outer copper (power path for the motors). If 1 oz is much cheaper, please quote both.
- HASL lead-free or ENIG, green solder mask, white silkscreen.
- Quantity: 5 bare boards, **only 1 assembled**.

**Assembly (1 board, top side only)**

- 273 SMD placements, 79 unique SMD part numbers. Smallest passives 0603, one SOD-523, finest pitch
  0.5 mm (VSSOP-8, TSSOP-10, SN74LVC DCT packages). No BGA, no QFN.
- The 39 through-hole parts (connectors, sockets, fuse holders, terminals) are **not** to be
  assembled: I will solder them myself.
- Parts sourced by PCBWay, please. If some parts are unavailable, please suggest equivalents
  before buying.

**Files attached**

- `mainboard_gerbers.zip` — Gerber RS-274X and Excellon drill files.
- `bom_pcbway.csv` — BOM with manufacturer, MPN, package, and a "Placed by" column (SMD = PCBWay,
  THT = me).
- `centroid_pcbway.csv` — pick-and-place file, SMD parts only, top side.
- `assembly_top.pdf` and `schematic.pdf` — for reference.

**Questions**

1. What is the total for this order (PCB + assembly + parts + shipping to France), and how much
   would remain to pay after the 60 € sponsorship?
2. Which options would bring the order closest to 60 € (1 oz copper, fewer boards, other)?
3. Is there anything in the files that would block production?

In return I will credit PCBWay in the project README and document the board build with photos.

Best regards,
William
