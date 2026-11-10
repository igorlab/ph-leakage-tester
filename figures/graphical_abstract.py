"""Graphical abstract for HardwareX: problem, tester, application.

    python3 graphical_abstract.py

Writes graphical_abstract.pdf (vector, fonts embedded) and graphical_abstract.tif
(600 dpi) next to this script. Size 13 × 6 cm, landscape, as the Guide for authors asks
(at least 1328 px wide, readable at 13 cm). Numbers as in the paper: failed amplifier
about 12 nA (Section 1, Figure 1; protocol H, preliminary), redesigned amplifier 0.5–4.6 pA in magnitude (toggle runs on two days, Section 7.4).
The middle panel draws the tester as its measurement principle (Figure 3) instead of a photograph.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GREEN, BLUE, DARK, GREY, RED = "#2b8a3e", "#2f6db5", "#333333", "#888888", "#c0392b"
CM = 1 / 2.54
NERNST = 59.16                         # mV per pH at 25 degC

plt.rcParams.update({"font.family": "Arial", "font.size": 7.5, "pdf.fonttype": 42, "savefig.bbox": None,
                     "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic",
                     "axes.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False})
fig = plt.figure(figsize=(13 * CM, 6 * CM))
HEAD_Y = 0.93


def head(x, s):
    fig.text(x, HEAD_Y, s, ha="center", fontsize=8.5, weight="bold")


def arrow(x0, x1, y=0.55):
    fig.add_artist(FancyArrowPatch((x0, y), (x1, y), transform=fig.transFigure,
                                   arrowstyle="-|>", mutation_scale=10, color=GREY, lw=1.2))


# (1) problem: the input current flows through the electrode resistance
head(0.16, "Problem")
a = fig.add_axes([0.015, 0.0, 0.29, 0.88])
a.set_xlim(-0.6, 9.4); a.set_ylim(3, 13.6); a.set_aspect("equal"); a.axis("off")
# combined glass electrode: outer tube with reference electrolyte, inner tube with internal
# buffer, internal and reference wires, cap, cable, filling port, diaphragm, membrane bulb
EL_REF, EL_BUF, EL_CAP = "#e6ebf0", "#cfe2f5", "#6b6b6b"   # own neutral palette
BX, BY, BR = 1.0, 5.65, 0.45           # membrane bulb
NX = 0.18                              # half width of the inner tube, which opens into the bulb
NY = BY + (BR ** 2 - NX ** 2) ** 0.5   # where the inner tube meets the bulb
# fills without edges, so that the outer tube tapers into the bulb with no seams
a.add_patch(Polygon([[0.5, 10.6], [0.5, 6.4], [BX - NX, NY], [BX + NX, NY], [1.5, 6.4], [1.5, 10.6]],
                    closed=True, fc=EL_REF, ec="none"))
a.add_patch(Rectangle((0.5, 9.6), 1.0, 1.0, fc="white", ec="none"))
a.add_patch(Circle((BX, BY), BR, fc=EL_BUF, ec="none"))
a.add_patch(Rectangle((BX - NX, NY - 0.05), 2 * NX, 9.0 - NY + 0.05, fc=EL_BUF, ec="none"))
a.add_patch(Rectangle((BX - NX, 9.0), 2 * NX, 1.6, fc="white", ec="none"))
# outlines: outer wall tapering to the bulb, inner tube walls down to the bulb, bulb without its top
a.plot([0.5, 0.5, BX - NX], [10.6, 6.4, NY], color=DARK, lw=0.8)
a.plot([1.5, 1.5, BX + NX], [10.6, 6.4, NY], color=DARK, lw=0.8)
a.plot([BX - NX, BX - NX], [10.6, NY], color=DARK, lw=0.6)
a.plot([BX + NX, BX + NX], [10.6, NY], color=DARK, lw=0.6)
gap = np.degrees(np.arccos(NX / BR))
a.add_patch(Arc((BX, BY), 2 * BR, 2 * BR, theta1=180 - gap, theta2=360 + gap, color=DARK, lw=0.8))
a.plot([1.0, 1.0], [10.6, 5.75], color="black", lw=0.9)              # internal electrode
a.plot([1.0, 1.0], [5.95, 5.45], color="black", lw=2.2, solid_capstyle="round")
a.plot([0.66, 0.66], [10.6, 7.0], color=GREY, lw=0.9)               # reference electrode
a.plot([1.32, 1.5], [6.95, 6.95], color="black", lw=1.4)             # diaphragm
a.add_patch(Rectangle((1.5, 9.95), 0.2, 0.25, fc="white", ec=DARK, lw=0.6))   # filling port
a.add_patch(Rectangle((0.38, 10.6), 1.24, 0.6, fc=EL_CAP, ec=DARK, lw=0.8))   # cap
a.plot([1.0, 1.0], [11.2, 12.0], color="black", lw=1.6)              # cable
a.text(1.0, 5.0, "glass\nelectrode", ha="center", va="top", fontsize=6.5)
# its resistance, the amplifier and the current it draws
y = 12.0
a.plot([1.0, 2.0], [y, y], color=DARK, lw=1)
x = np.linspace(2.0, 4.2, 11)
a.plot(x, y + 0.3 * np.array([0, 1, -1, 1, -1, 1, -1, 1, -1, 1, 0]), color=DARK, lw=1)
a.text(3.1, y + 0.6, "$R_{el}$", ha="center", fontsize=7.5)
a.text(3.8, y - 0.65, "100 MΩ–1 GΩ", ha="center", va="top", fontsize=6.5)
a.plot([4.2, 6.0], [y, y], color=DARK, lw=1)
a.add_patch(Polygon([[6.0, y - 1.0], [6.0, y + 1.0], [8.0, y]], closed=True, fc="white", ec=DARK, lw=1))
a.plot([8.0, 8.9], [y, y], color=DARK, lw=1)
a.add_patch(FancyArrowPatch((4.6, y + 0.45), (5.8, y + 0.45), arrowstyle="-|>", mutation_scale=8,
                            color=RED, lw=1.2))
a.text(5.2, y + 0.75, "$I$", color=RED, ha="center", fontsize=8.5, weight="bold")
a.text(5.6, 7.3, "$I \\cdot R_{el}$ adds to the reading:", ha="center", fontsize=7)
a.text(5.6, 6.1, "1 nA × 500 MΩ = 0.5 V", ha="center", fontsize=7.5, color=RED, weight="bold")
a.text(5.6, 4.9, "> 8 pH units", ha="center", fontsize=7.5, color=RED, weight="bold")

arrow(0.315, 0.35)

# (2) the tester, drawn as its measurement principle (Figure 3)
head(0.5, "Tester (≈ EUR 15)")
b = fig.add_axes([0.355, 0.2, 0.29, 0.68])
b.set_xlim(0, 10.3); b.set_ylim(0, 11.0); b.set_aspect("equal"); b.axis("off")
b.add_patch(FancyBboxPatch((0.15, 0.6), 5.4, 10.2, boxstyle="round,pad=0,rounding_size=0.4",
                           fc="#eef6f0", ec=GREEN, lw=1))
b.text(0.45, 10.55, "tester", color=GREEN, fontsize=6.5, weight="bold", va="top")
yw = 6.6                                        # signal line
b.add_patch(Circle((0.85, yw), 0.5, fc="white", ec=DARK, lw=0.9))
b.text(0.85, yw, "$E$", ha="center", va="center", fontsize=7.5)
b.plot([1.35, 2.0], [yw, yw], color=DARK, lw=1)
x = np.linspace(2.0, 4.2, 11)
b.plot(x, yw + 0.28 * np.array([0, 1, -1, 1, -1, 1, -1, 1, -1, 1, 0]), color=DARK, lw=1)
b.text(3.1, yw - 0.6, "$R$ 50 MΩ", ha="center", va="top", fontsize=6.5)
b.plot([4.2, 6.8], [yw, yw], color=DARK, lw=1)
b.plot([1.8, 1.8, 2.6], [yw, 8.6, 8.6], color=DARK, lw=0.8)    # button across R, open
b.plot([2.6, 3.5], [8.6, 9.1], color=DARK, lw=0.8)
b.plot([3.6, 4.4, 4.4], [8.6, 8.6, yw], color=DARK, lw=0.8)
b.plot([1.8, 4.4], [yw, yw], "o", color=DARK, ms=2)
b.text(3.3, 9.3, "button", ha="center", fontsize=6.5)
b.plot([5.55, 5.55], [yw - 0.25, yw + 0.25], color=GREY, lw=2.2)   # BNC
b.text(6.2, yw + 0.3, "$V_{in}$", ha="center", va="bottom", fontsize=6.5)   # amplifier input
b.add_patch(FancyArrowPatch((3.8, yw + 0.75), (2.4, yw + 0.75), arrowstyle="-|>", mutation_scale=8,
                            color=RED, lw=1.2))                 # positive I flows out of the input node, through R
b.text(3.1, yw + 0.9, "$I$", color=RED, ha="center", va="bottom", fontsize=8.5, weight="bold")
b.add_patch(Polygon([[6.8, yw - 1.0], [6.8, yw + 1.0], [8.8, yw]], closed=True, fc="white", ec=BLUE, lw=1))
b.text(7.75, yw - 1.25, "amplifier\nunder test", ha="center", va="top", fontsize=6.5, color=BLUE)
b.plot([8.8, 9.8, 9.8, 5.35], [yw, yw, 1.9, 1.9], color=DARK, lw=0.8)    # S back into the tester
b.text(9.3, yw + 0.35, "$S$", ha="center", va="bottom", fontsize=7.5)
b.add_patch(FancyBboxPatch((0.4, 1.1), 4.95, 1.6, boxstyle="round,pad=0,rounding_size=0.2",
                           fc="white", ec=GREEN, lw=0.8))
b.text(2.875, 1.9, "ADC reads $E$, $S$:\n$I = (V_{in} - E)/R$", ha="center", va="center", fontsize=6.3)
b.plot([1.8, 1.8], [yw, 2.7], color=DARK, lw=0.8)              # E is read before R
fig.text(0.5, 0.125, "measures $I$ in circuit, through the\namplifier's own output", ha="center", va="top",
         fontsize=7, linespacing=1.15)

arrow(0.65, 0.685)

# (3) application: the titrator's pH amplifier, failed and redesigned
head(0.83, "Application: KH titrator")
c = fig.add_axes([0.765, 0.27, 0.205, 0.56])
rows = [("failed\nboard", 12e-9, 12e-9, RED), ("redesigned\nboard", 0.47e-12, 4.6e-12, GREEN)]
LEFT = 3e-13
for n, (label, lo, hi, col) in enumerate(rows):
    yy = 1 - n
    c.barh(yy, hi - LEFT, left=LEFT, height=0.45, color=col, alpha=0.35, lw=0)
    if hi > lo:
        c.barh(yy, hi - lo, left=lo, height=0.45, color=col, lw=0)  # measured range
    else:
        c.plot([lo, lo], [yy - 0.225, yy + 0.225], color=col, lw=2.2, solid_capstyle="butt")  # one value
c.set_xscale("log")
c.set_xlim(LEFT, 1e-7)
c.set_ylim(-0.75, 1.75)
c.set_yticks([1, 0])
c.set_yticklabels([r[0] for r in rows], fontsize=7)
c.set_xticks([1e-12, 1e-11, 1e-10, 1e-9, 1e-8, 1e-7])
c.set_xticklabels(["1 pA", "", "100 pA", "", "10 nA", ""], fontsize=6.5)
c.tick_params(axis="y", length=0, pad=2)
c.tick_params(axis="x", length=2, pad=1.5)
c.spines["left"].set_visible(False)
c.set_xlabel("input current", labelpad=1, fontsize=7)
c.text(1.2e-8, 1.33, "≈ 12 nA", ha="center", fontsize=7, color=RED, weight="bold")
c.text(6e-11, 1.0, "no response\nto the electrode", va="center", ha="center", fontsize=6.5, color="white")
c.text(1.5e-12, 0.33, "0.5–4.6 pA", ha="center", fontsize=7, color=GREEN, weight="bold")
fig.text(0.8675, 0.125, "the redesigned board\nruns in the titrator", ha="center", va="top", fontsize=7,
         linespacing=1.15)

fig.savefig(os.path.join(HERE, "graphical_abstract.pdf"))
fig.savefig(os.path.join(HERE, "graphical_abstract.tif"), dpi=600,
            pil_kwargs={"compression": "tiff_lzw"})
