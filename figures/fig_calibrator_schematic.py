#!/usr/bin/env python3
"""Wiring diagram of the pH calibrator (tester): figures/fig_calibrator_schematic.png

Everything is drawn from the coordinate lists below (units: pixels of a 2000 x 1209 canvas,
y downwards). A dot is drawn where a wire is connected to another wire (T junction) or lands on a
component terminal; plain corners get no dot. Where wires only cross, one of them hops over the other.

Usage (from the repository root):  python3 figures/fig_calibrator_schematic.py
Requires: matplotlib, numpy.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Polygon

W, H = 2000, 1209
U = 0.64                      # font points per canvas unit (dpi 125)
RED, ORANGE, BLUE, GREEN = "#d62728", "#f28e2b", "#1f6fd1", "#2ca02c"
YELLOW, PURPLE, BROWN, GREY = "#e0a800", "#8e44ad", "#8c564b", "#7a7a7a"
BLACK, TEAL, PINK = "#111111", "#17a2b8", "#e0529c"
INK = "#1a1a1a"
LW = 3.6 * 0.576              # wire width in points (about 3.6 px at 125 dpi)
HOP = 9

fig = plt.figure(figsize=(20, H / 100.0), dpi=125)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)
ax.axis("off")


def text(x, y, s, size=14, color=INK, weight="normal", ha="center", va="center", **kw):
    z = kw.pop("zorder", 20)
    ax.text(x, y, s, fontsize=size * U, color=color, fontweight=weight, ha=ha, va=va,
            family="DejaVu Sans", zorder=z, **kw)


# ---------------------------------------------------------------- wires
wires = []          # (color, points)


def wire(color, *pts):
    wires.append((color, list(pts)))


# crossings of a horizontal and a vertical wire: the horizontal one hops, except for these
# vertical wires (identified by colour and x) which hop over the horizontal ones.
VERTICAL_HOPS = {(ORANGE, 421), (PURPLE, 232), (RED, 634)}

wire(BLACK, (128, 94), (87, 94), (87, 158), (1952, 158), (1952, 773), (1862, 773))         # GND bus
wire(BLACK, (385, 235), (385, 158))
wire(BLACK, (594, 215), (594, 158))
wire(BLACK, (1132, 158), (1132, 293), (1200, 293))
wire(PURPLE, (217, 94), (249, 94))                                                         # R6-R7 node
wire(PURPLE, (232, 94), (232, 175), (312, 175), (312, 235))                                # GPIO4
wire(ORANGE, (338, 94), (1928, 94), (1928, 740), (1558, 740), (1558, 809))                 # 5 V
wire(ORANGE, (421, 235), (421, 94))
wire(RED, (349, 235), (349, 127), (1156, 127), (1156, 259), (1200, 259))                   # 3.3 V
wire(RED, (634, 215), (634, 127))
wire(GREEN, (384, 348), (384, 428), (843, 428), (843, 183), (674, 183), (674, 215))        # SCL
wire(GREEN, (843, 326), (1200, 326))
wire(BLUE, (421, 348), (421, 400), (819, 400), (819, 196), (714, 196), (714, 215))         # SDA
wire(BLUE, (819, 359), (1200, 359))
wire(YELLOW, (661, 792), (661, 462), (1200, 462))                                          # A
wire(YELLOW, (722, 617), (722, 553), (803, 553))
wire(YELLOW, (661, 617), (790, 617))
wire(TEAL, (867, 553), (939, 553), (939, 617), (967, 617), (967, 898), (1000, 898))        # after 50 MOhm
wire(TEAL, (880, 617), (939, 617))
wire(PURPLE, (690, 792), (690, 793), (739, 793), (739, 986), (489, 986), (489, 745), (401, 745))   # reference
wire(PURPLE, (739, 986), (1100, 986), (1100, 495), (1200, 495))
wire(PURPLE, (1100, 898), (1068, 898))
wire(BROWN, (232, 773), (297, 773), (297, 797), (352, 797))                                # battery, switch, 6.8k
wire(BROWN, (232, 821), (257, 821), (257, 934), (466, 934), (466, 797), (401, 797))
wire(BROWN, (352, 745), (352, 681), (489, 681))
wire(BROWN, (577, 681), (634, 681), (634, 792))
wire(PINK, (1200, 529), (1136, 529), (1136, 681), (1400, 681))                             # S
wire(PINK, (1490, 681), (1518, 681), (1518, 809))
wire(PINK, (1373, 681), (1373, 690))                                                       # R4 hangs from S
wire(BLACK, (1373, 750), (1373, 760))                                                      # R4 to ground symbol
wire(GREY, (1200, 563), (1155, 563), (1155, 650), (1679, 650), (1679, 773), (1771, 773))   # board GND
wire(GREY, (1679, 773), (1598, 773), (1598, 809))

# T junctions: the dot marks a wire connected to another wire
JUNCTIONS = [
    ((232, 94), PURPLE), ((421, 94), ORANGE), ((385, 158), BLACK), ((594, 158), BLACK),
    ((634, 127), RED), ((1132, 158), BLACK), ((843, 326), GREEN), ((819, 359), BLUE),
    ((661, 617), YELLOW), ((722, 617), YELLOW), ((939, 617), TEAL), ((739, 986), PURPLE),
    ((1100, 898), PURPLE), ((1373, 681), PINK), ((1679, 773), GREY),
]


def segs(points):
    return list(zip(points[:-1], points[1:]))


def crossings():
    """Return {(wire index, segment index): [positions where this segment must hop]}."""
    hops = {}
    items = [(i, j, a, b, c) for i, (c, p) in enumerate(wires) for j, (a, b) in enumerate(segs(p))]
    for (i, j, a, b, c) in items:
        if a[1] != b[1]:                       # horizontal segments only
            continue
        for (k, m, p, q, d) in items:
            if k == i or p[0] != q[0]:
                continue
            x, y = p[0], a[1]
            if min(a[0], b[0]) < x < max(a[0], b[0]) and min(p[1], q[1]) < y < max(p[1], q[1]):
                if any(abs(x - jx) < 1 and abs(y - jy) < 1 for (jx, jy), _ in JUNCTIONS):
                    continue
                if (d, x) in VERTICAL_HOPS:
                    hops.setdefault((k, m), []).append((x, y))
                else:
                    hops.setdefault((i, j), []).append((x, y))
    return hops


HOPS = crossings()


def draw_wire(i):
    color, pts = wires[i]
    xs, ys = [pts[0][0]], [pts[0][1]]
    for j, (a, b) in enumerate(segs(pts)):
        horizontal = a[1] == b[1]
        d = 1 if ((b[0] > a[0]) if horizontal else (b[1] > a[1])) else -1
        hs = sorted(HOPS.get((i, j), []), key=(lambda h: d * h[0]) if horizontal else (lambda h: d * h[1]))
        for (hx, hy) in hs:
            t = np.linspace(0, np.pi, 17)
            if horizontal:
                xs += [hx - d * HOP + d * HOP * (1 - np.cos(k)) for k in t]
                ys += [hy - HOP * np.sin(k) for k in t]
            else:
                xs += [hx + HOP * np.sin(k) for k in t]
                ys += [hy - d * HOP + d * HOP * (1 - np.cos(k)) for k in t]
        xs.append(b[0]); ys.append(b[1])
    ax.plot(xs, ys, color=color, lw=LW, solid_capstyle="butt", solid_joinstyle="miter", zorder=9)


# ---------------------------------------------------------------- components
def resistor(cx, cy, bands, vertical=False, length=90, thick=22):
    tan = "#e8d5a6"
    if vertical:
        ax.add_patch(FancyBboxPatch((cx - thick / 2, cy - length / 2), thick, length,
                                    boxstyle="round,pad=0,rounding_size=8", fc=tan, ec="#b9a36a", lw=1.2, zorder=5))
        for n, c in enumerate(bands):
            ax.add_patch(Rectangle((cx - thick / 2, cy - length / 2 + 14 + n * 12), thick, 7, fc=c, ec="none", zorder=6))
    else:
        ax.add_patch(FancyBboxPatch((cx - length / 2, cy - thick / 2), length, thick,
                                    boxstyle="round,pad=0,rounding_size=8", fc=tan, ec="#b9a36a", lw=1.2, zorder=5))
        for n, c in enumerate(bands):
            ax.add_patch(Rectangle((cx - length / 2 + 14 + n * 12, cy - thick / 2), 7, thick, fc=c, ec="none", zorder=6))


def pad(x, y, r=8, fc="#e8a317", ec="#8a5a00"):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=1.5, zorder=7))
    ax.add_patch(Circle((x, y), r * 0.38, fc="#ffffff", ec="none", zorder=8))


# title
text(24, 22, "pH calibrator: wiring diagram", 28, weight="bold", ha="left")
text(24, 54, "ESP32-C3 SuperMini, ADS1115, OLED and the pH electrode simulator. "
     "Wire by the pin names printed on the boards.", 15.5, color="#333333", ha="left")

# wire labels
text(1139, 83, "5 V to the pH board (from the 5V pin)", 15, ORANGE, "bold")
text(822, 113, "3.3 V", 15, RED, "bold")
text(1012, 145, "GND", 15, INK, "bold")
text(57, 174, "GPIO4: 5 V × 0.4 = 2.0 V", 12.5, PURPLE, "bold", ha="left")
text(505, 389, "SDA", 15, BLUE, "bold")
text(503, 417, "SCL", 15, GREEN, "bold")
text(881, 451, "A: simulator voltage, taken BEFORE the 50 MΩ resistor", 14, "#b58900", "bold")
text(505, 1003, "reference: pot leg 1, BNC shield,", 14, PURPLE, "bold", ha="left")
text(505, 1020, "input A1", 14, PURPLE, "bold", ha="left")
text(1022, 792, "to BNC center", 14, "#0e7c8c", "bold", ha="left")
text(1140, 701, "S: up to 5 V, the ADS gets half", 12.5, "#c2336f", "bold", ha="left")
text(1180, 666, "A3: board current (V on Rsh)", 13, "#555555", "bold", ha="left")
text(1608, 763, "board GND", 12, "#555555", "bold", ha="left")

# resistors
resistor(172, 94, ["#7a4a2a", "#111111", "#f28e2b"])
text(172, 124, "R6 10 kΩ", 14, weight="bold")
resistor(293, 94, ["#7a4a2a", "#2ca02c", "#f28e2b"])
text(293, 124, "R7 15 kΩ", 14, weight="bold")
resistor(533, 681, ["#1f6fd1", "#7a7a7a", "#d62728"])
text(533, 711, "6.8 kΩ", 14, weight="bold")
resistor(835, 617, ["#2ca02c", "#111111", "#1f6fd1"])
text(835, 646, "50 MΩ", 14, weight="bold")
resistor(1445, 681, ["#7a4a2a", "#111111", "#f28e2b"])
text(1445, 706, "R3 10 kΩ", 14, weight="bold")
resistor(1373, 720, ["#7a4a2a", "#111111", "#f28e2b"], vertical=True, length=60, thick=22)
text(1389, 728, "R4 10 kΩ", 14, weight="bold", ha="left")
resistor(1816, 773, ["#7a4a2a", "#111111", "#111111"])
text(1816, 802, "Rsh 10 Ω", 14, weight="bold")
text(1816, 819, "shunt", 11.5, "#555555")
for dy, w in ((0, 14), (6, 9), (12, 4)):
    ax.plot([1373 - w, 1373 + w], [762 + dy, 762 + dy], color=INK, lw=2, zorder=5)

# ESP32-C3 SuperMini
text(112, 199, "ESP32-C3 SuperMini", 19, weight="bold", ha="left")
ax.add_patch(FancyBboxPatch((111, 214), 355, 155, boxstyle="round,pad=0,rounding_size=10", fc="#161b22", ec="none", zorder=4))
ax.add_patch(Rectangle((123, 255), 28, 72, fc="#e8dcc0", ec="none", zorder=5))
ax.add_patch(Rectangle((460, 266), 36, 50, fc="#c8ccd2", ec="#9aa0a8", zorder=5))
ax.add_patch(FancyBboxPatch((470, 280), 16, 22, boxstyle="round,pad=0,rounding_size=4", fc="#2a2f36", ec="none", zorder=6))
ax.add_patch(Rectangle((233, 262), 82, 59, fc="#2a2f36", ec="#444b55", zorder=5))
text(274, 284, "ESP32-C3", 12, "#ffffff", "bold")
text(274, 303, "FH4", 10, "#aab0b8")
ax.add_patch(Rectangle((344, 268), 21, 15, fc="#e8e8e8", ec="none", zorder=6))
ax.add_patch(Rectangle((344, 300), 21, 15, fc="#e8e8e8", ec="none", zorder=6))
text(375, 276, "RST", 9, "#aab0b8", ha="left")
text(375, 308, "BOOT", 9, "#aab0b8", ha="left")
ax.add_patch(Circle((413, 291), 5, fc="#e0443a", ec="none", zorder=6))
for x, lab in zip([167, 203, 239, 276, 312, 349, 385, 421], ["0", "1", "2", "3", "4", "3.3", "G", "5V"]):
    pad(x, 235)
    text(x, 252, lab, 11, "#ffffff", "bold")
for x, lab in zip([167, 203, 240, 276, 312, 349, 385, 421], ["21", "20", "10", "9", "8", "7", "6", "5"]):
    pad(x, 348)
    text(x, 330, lab, 11, "#ffffff", "bold")

# OLED
ax.add_patch(Rectangle((553, 200), 226, 153, fc="#1f4e9a", ec="#16386f", lw=2, zorder=4))
ax.add_patch(Rectangle((565, 237), 202, 104, fc="#05080d", ec="none", zorder=5))
text(666, 273, "SSD1306", 17, "#4fc3f7", "bold")
text(666, 297, "128 × 64", 14, "#4fc3f7")
for x, lab in zip([594, 634, 674, 714], ["GND", "VCC", "SCL", "SDA"]):
    pad(x, 215, 8)
    text(x, 228, lab, 8.5, "#ffffff", "bold")
text(666, 372, "OLED SSD1306, address 0x3C", 14, weight="bold")

# ADS1115
ax.add_patch(FancyBboxPatch((1180, 230), 153, 403, boxstyle="round,pad=0,rounding_size=8", fc="#2d55a3", ec="#0e2a63", lw=2, zorder=4))
for y, lab in zip([259, 293, 326, 360, 394, 428, 462, 495, 529, 563],
                  ["VDD", "GND", "SCL", "SDA", "ADDR", "ALRT", "A0", "A1", "A2", "A3"]):
    pad(1200, y)
    text(1216, y, lab, 14, "#ffffff", "bold", ha="left")
for y in (259, 293, 326, 360, 563):
    ax.add_patch(Rectangle((1277, y - 6), 22, 11, fc="#1a1a1a", ec="none", zorder=5))
ax.add_patch(Rectangle((1265, 472), 38, 46, fc="#14181e", ec="none", zorder=5))
text(1323, 425, "ADS1115", 30, "#14243f", "bold", rotation=270)
text(1341, 394, "ADDR to GND", 14, weight="bold", ha="left")

# push button, trimmer, BNC, battery, switch
text(834, 518, "push button", 14, weight="bold")
ax.add_patch(FancyBboxPatch((803, 533), 64, 40, boxstyle="round,pad=0,rounding_size=5", fc="#2a2a2a", ec="none", zorder=5))
ax.add_patch(Circle((835, 553), 14, fc="#444444", ec="#111111", lw=2, zorder=6))
ax.add_patch(Rectangle((610, 833), 105, 98, fc="#2d55a3", ec="#1a3a7a", lw=2, zorder=5))
ax.add_patch(Circle((662, 882), 29, fc="#f1ead6", ec="#b9a36a", lw=2, zorder=6))
ax.plot([642, 682], [862, 902], color="#555", lw=3, zorder=7)
ax.plot([642, 682], [902, 862], color="#555", lw=3, zorder=7)
for x in (634, 661, 690):
    ax.plot([x, x], [792, 833], color="#aaaaaa", lw=3, zorder=4)
for x, n in ((634, "3"), (661, "2"), (690, "1")):
    text(x, 782, n, 13, weight="bold")
text(661, 945, "trimmer 10 kΩ", 14, weight="bold")
text(661, 962, "(leg 2 = wiper)", 12, "#555555")
ax.add_patch(Circle((1036, 898), 31, fc="#d9d9d9", ec="#888888", lw=2, zorder=5))
ax.add_patch(Circle((1036, 898), 17, fc="#f3f3f3", ec="#777777", lw=2, zorder=6))
ax.add_patch(Circle((1036, 898), 6, fc="#e0a800", ec="#8a6a00", zorder=7))
ax.add_patch(Rectangle((1058, 892), 14, 12, fc="#c8c8c8", ec="#888", zorder=5))
ax.add_patch(Rectangle((998, 892), 14, 12, fc="#e0a800", ec="#8a6a00", zorder=5))
text(1035, 837, "BNC female", 16, weight="bold")
text(989, 920, "center", 12, "#8a6a00", "bold")
text(1127, 880, "shield", 12, "#555555", "bold")
text(172, 741, "LR44 battery, 1.5 V", 14, weight="bold")
ax.add_patch(FancyBboxPatch((111, 753), 121, 89, boxstyle="round,pad=0,rounding_size=8", fc="#1c1c1c", ec="none", zorder=5))
ax.add_patch(Circle((172, 798), 31, fc="#d9d9d9", ec="#999", lw=2, zorder=6))
text(172, 784, "+", 20, "#333", "bold", zorder=8)
text(172, 809, "LR44", 11, "#333", "bold", zorder=8)
ax.add_patch(FancyBboxPatch((312, 713), 129, 169, boxstyle="round,pad=0,rounding_size=12", fc="#2b2b2b", ec="#000000", lw=2, zorder=4))
# lever: a grey cone, light on the left
lever = Polygon([[359, 713], [393, 713], [388, 676], [364, 676]], fc="#bdbdbd", ec="#7a7a7a", lw=1.5, zorder=5)
ax.add_patch(lever)
ax.add_patch(Polygon([[359, 713], [375, 713], [375, 678], [364, 678]], fc="#e6e6e6", ec="none", zorder=5))
for (x, y) in ((352, 745), (401, 745), (352, 797), (401, 797), (352, 849), (401, 849)):
    ax.add_patch(FancyBboxPatch((x - 11, y - 8), 22, 16, boxstyle="round,pad=0,rounding_size=4", fc="#d0d0d0", ec="#9a9a9a", lw=1, zorder=6))
ax.plot([352, 401], [745, 849], color="#e08a2b", lw=2.6, zorder=7)
ax.plot([401, 352], [745, 849], color="#e08a2b", lw=2.6, zorder=7)
text(291, 745, "1", 14, weight="bold")
text(291, 849, "2", 14, weight="bold")
text(377, 901, "polarity switch", 14, weight="bold")
text(377, 918, "(DPDT, ON-OFF-ON)", 12, "#555555")

# JST connector to the pH board
ax.add_patch(FancyBboxPatch((1492, 791), 132, 48, boxstyle="round,pad=0,rounding_size=5", fc="#f3ead6", ec="#b9a36a", lw=1.5, zorder=4))
for x, lab, c in ((1518, "S", PINK), (1558, "+5V", ORANGE), (1598, "GND", GREY)):
    pad(x, 809, 9)
    ax.add_patch(Circle((x, 809), 5, fc=c, ec="none", zorder=9))
    text(x, 831, lab, 12, weight="bold")
text(1558, 858, "to pH board (JST 3-pin, P2)", 14.5, weight="bold")

# Key points box
ax.add_patch(FancyBboxPatch((1461, 191), 386, 355, boxstyle="round,pad=0,rounding_size=10", fc="#f6f7f9", ec="#cfd4da", lw=1.5, zorder=2))
text(1478, 213, "Key points", 19, weight="bold", ha="left")
KEY = [
    "A1: to the pot leg that goes to the BNC shield,",
    "not to the leg with the 6.8 kΩ resistor.",
    "A0: only BEFORE the 50 MΩ resistor.",
    "Never wire the BNC center to the ADS.",
    "Button pressed: 50 MΩ shorted (calibration).",
    "Button released: leak measurement.",
    "Power the ADS1115 and OLED from 3.3 V.",
    "Feed S to the ADS only through R3 and R4.",
    "Board current: I = V(A3) / Rsh.",
    "S in firmware: 2 × V(A2).",
    "A1 has no divider: A is valid only with a board.",
    "Cable to P2 is crossed: connect by function.",
    "Dot = connection. Arc = wires only cross.",
]
for n, line in enumerate(KEY):
    text(1478, 244 + n * 22.4, line, 13.2, "#222222", ha="left")

# legend
ax.add_patch(FancyBboxPatch((11, 1005), 458, 187, boxstyle="round,pad=0,rounding_size=10", fc="#f6f7f9", ec="#cfd4da", lw=1.5, zorder=2))
LEG = [(RED, "3.3 V"), (ORANGE, "5 V to the pH board"), (BLUE, "SDA"), (TEAL, "after 50 MΩ, to BNC center"),
       (PINK, "S, pH board output"), (GREY, "pH board GND, through Rsh")]
LEG2 = [(BLACK, "GND (calibrator ground)"), (GREEN, "SCL"), (YELLOW, "A, wiper (before 50 MΩ)"),
        (PURPLE, "reference: pot leg 1, shield, A1"), (BROWN, "battery, switch, 6.8 kΩ")]
for n, (c, s) in enumerate(LEG):
    ax.plot([22, 53], [1026 + n * 29] * 2, color=c, lw=LW, zorder=4)
    text(58, 1026 + n * 29, s, 11.5, ha="left")
for n, (c, s) in enumerate(LEG2):
    ax.plot([251, 282], [1026 + n * 29] * 2, color=c, lw=LW, zorder=4)
    text(287, 1026 + n * 29, s, 11.5, ha="left")

# wires and junction dots on top of everything else
for i in range(len(wires)):
    draw_wire(i)
TERMINALS = [((352, 745), BROWN), ((401, 745), PURPLE), ((352, 797), BROWN), ((401, 797), BROWN),
             ((634, 792), BROWN), ((661, 792), YELLOW), ((690, 792), PURPLE)]
for (x, y), c in TERMINALS:
    ax.add_patch(Circle((x, y), 6.5, fc=c, ec="none", zorder=11))
for (x, y), c in JUNCTIONS:
    ax.add_patch(Circle((x, y), 6.5, fc=c, ec="none", zorder=10))

fig.savefig("figures/fig_calibrator_schematic.png", dpi=125, facecolor="white")
print("wrote figures/fig_calibrator_schematic.png")
