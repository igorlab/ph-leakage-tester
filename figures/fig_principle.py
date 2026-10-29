"""Figure: measurement principle of the calibrator (block diagram). Run: python3 fig_principle.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle
import numpy as np
import os
HERE = os.path.dirname(os.path.abspath(__file__))
GREEN, BLUE, DARK, GREY, ORANGE = "#2e8b3e", "#2f6db5", "#333333", "#888888", "#c77a00"
fig, ax = plt.subplots(figsize=(7.2, 3.3))
ax.set_xlim(0, 10.6); ax.set_ylim(-1.35, 3.55); ax.axis("off")
def wire(xs, ys, c=DARK, lw=1.4): ax.plot(xs, ys, color=c, lw=lw, solid_capstyle="round")
def dot(x, y, c=DARK): ax.add_patch(Circle((x, y), 0.055, color=c, zorder=5))
# simulator box
ax.add_patch(FancyBboxPatch((0.1, 1.25), 2.1, 1.5, boxstyle="round,pad=0.04", fc="#f3f3f3", ec=DARK, lw=1))
ax.text(1.15, 2.35, "Electrode simulator", ha="center", fontsize=8, weight="bold")
ax.text(1.15, 1.75, "LR44, polarity switch,\n6.8 kΩ + 10 kΩ trimmer", ha="center", va="center", fontsize=7)
# E node and wire
wire([2.2, 3.0], [2.0, 2.0]); dot(3.0, 2.0)
ax.text(2.9, 2.1, "E", ha="right", fontsize=9, weight="bold", color=ORANGE)
# resistor zigzag 3.4-5.0
x = np.linspace(3.45, 4.95, 13); y = 2.0 + 0.13 * np.array([0, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, 0])
wire([3.0, 3.45], [2.0, 2.0]); ax.plot(x, y, color=DARK, lw=1.4); wire([4.95, 5.6], [2.0, 2.0])
ax.text(4.2, 1.62, "R = 50 MΩ", ha="center", fontsize=8)
# push button across R
wire([3.0, 3.0, 3.75], [2.0, 2.9, 2.9]); wire([4.65, 5.6, 5.6], [2.9, 2.9, 2.0])
wire([3.75, 4.65], [3.12, 3.12]); wire([4.2, 4.2], [3.12, 3.3])
dot(3.75, 2.9); dot(4.65, 2.9)
ax.text(4.2, 3.38, "push button", ha="center", fontsize=7.5)
# Vin node
dot(5.6, 2.0, GREEN); ax.text(5.7, 2.1, "Vin", ha="left", fontsize=9, weight="bold", color=GREEN)
ax.text(6.1, 1.42, "high-impedance node:\nonly R and the BNC", ha="right", va="top", fontsize=6.8, color=GREEN)
# amplifier triangle
wire([5.6, 6.3], [2.0, 2.0])
ax.add_patch(Polygon([[6.3, 1.4], [6.3, 2.6], [7.5, 2.0]], closed=True, fc="white", ec=DARK, lw=1.4))
ax.text(6.72, 2.0, "amplifier\nunder test", ha="center", va="center", fontsize=6.6)
wire([7.5, 8.1], [2.0, 2.0]); dot(8.1, 2.0)
ax.text(8.1, 2.18, "S", ha="center", fontsize=9, weight="bold", color=BLUE)
# reference line
wire([1.15, 1.15, 6.9, 6.9], [1.25, 0.75, 0.75, 1.68], c=GREY, lw=1.1)
ax.text(5.05, 0.5, "REF: electrode-side ground (BNC shield)", ha="center", fontsize=6.8, color=GREY)
dot(2.6, 0.75, GREY)
ax.annotate("", xy=(2.6, -0.48), xytext=(2.6, 0.75), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1.1))
# ADC
ax.add_patch(FancyBboxPatch((2.4, -1.25), 6.2, 0.75, boxstyle="round,pad=0.04", fc="#eef3fa", ec=BLUE, lw=1))
ax.text(5.5, -0.87, "ADS1115:  A0−A1 = E    A2 = S (÷2)    A3 = supply current", ha="center", va="center", fontsize=7.5)
ax.annotate("", xy=(3.0, -0.48), xytext=(3.0, 2.0), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.1))
ax.annotate("", xy=(8.1, -0.48), xytext=(8.1, 2.0), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.1))
# states
ax.text(8.55, 3.15, "Button pressed (R shorted):", fontsize=7.5, weight="bold")
ax.text(8.55, 2.82, "Vin = E; two points give\nthe transfer line S(E)", fontsize=7.2, va="top")
ax.text(8.55, 1.95, "Button released:", fontsize=7.5, weight="bold")
ax.text(8.55, 1.62, "Vin from S via the line;\nI = (Vin − E) / R", fontsize=7.2, va="top")
fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(HERE, f"fig_principle.{ext}"), dpi=300)
