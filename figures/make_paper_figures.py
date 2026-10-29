"""Figures of the paper, made from the raw CSV in ../data.

    python3 make_paper_figures.py            # all figures
    python3 make_paper_figures.py known      # one of them

Each figure is written as PNG (300 dpi) and PDF next to this script.
"""
import csv
import os
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
R_SERIES, R_T = 49.61, 9.73            # MOhm: R as the sum of its five resistors, Rt, same multimeter
# Each log stores the R the firmware used (column r). Logged currents il = (vin - e) / r are
# rescaled to the measured R with firmware_r(rows) / R_SERIES. Raw CSV files are not modified.


def firmware_r(rs):
    """The single R value (MOhm) the firmware used for these rows."""
    values = {x["r"] for x in rs if x.get("r")}
    if len(values) != 1:
        sys.exit(f"expected one value of r in the log, found {values}")
    return float(values.pop())

plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "axes.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.dpi": 300, "savefig.bbox": "tight"})
GREEN, BLUE, GREY = "#2b8a3e", "#2f6db5", "#888888"
DARK = "#555555"                       # theory and fitted lines, dashed


def rows(name):
    return list(csv.DictReader(open(os.path.join(DATA, name))))


def known_points(r):
    """Per E step: the reading with Rt minus the reading without it (medians)."""
    out = []
    for mark in ("e100", "e30", "e10"):
        idx = [i for i, x in enumerate(r) if x["mark"] == mark]
        if not idx:
            continue
        start = idx[0]
        nxt = [i for i, x in enumerate(r) if i > start and x["mark"].startswith("e") and x["mark"] != mark]
        seg = r[start:nxt[0] if nxt else len(r)]
        e = st.median(float(x["e"]) for x in seg)          # median: the step ends while E is turned
        on = [float(x["il"]) for x in seg if float(x["vin"]) < 0.6 * e]
        off = [float(x["il"]) for x in seg if float(x["vin"]) >= 0.6 * e]
        k = firmware_r(seg) / R_SERIES
        out.append(dict(e=e, measured=(st.median(on) - st.median(off)) * k, expected=-e / (R_SERIES + R_T)))
    return out


def fig_known():
    r = rows("A_10M_run3.csv")
    pts = known_points(r)
    t = [float(x["t_s"]) / 60 for x in r]
    k = firmware_r(r) / R_SERIES
    il = [float(x["il"]) * k for x in r]

    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1.5, 1]})
    on = [float(x["vin"]) < 0.6 * float(x["e"]) for x in r]   # Rt connected
    i = 0
    while i < len(on):                          # shade the time with Rt connected, as the nights in Fig. 10
        if on[i]:
            j = i
            while j < len(on) and on[j]:
                j += 1
            a.axvspan(t[i], t[j - 1], color=GREEN, alpha=0.08, lw=0)
            i = j
        else:
            i += 1
    a.plot(t, il, color=GREEN, lw=1.2)
    a.axhline(0, color=GREY, lw=0.6, ls=":")
    for i, p in enumerate(pts):
        a.axhline(p["expected"], color=DARK, lw=0.8, ls="--", label="−E / (R + Rt)" if i == 0 else None)
    a.set_ylim(-2.0, 0.35)                 # two handling spikes (+1.6, +1.9 nA) leave the frame
    a.set_xlabel("Time, min")
    a.set_ylabel("Leakage reading, nA")
    a.set_title("(a) Rt on and off at E = 100, 30, 10 mV", fontsize=8.5, loc="left")
    a.legend(loc="lower right", fontsize=7.5, frameon=False)

    ex = [-p["expected"] * 1000 for p in pts]
    me = [-p["measured"] * 1000 for p in pts]
    lo, hi = 100, 3000
    b.plot([lo, hi], [lo, hi], color=DARK, lw=0.8, ls="--")
    b.plot(ex, me, "o", color=GREEN, ms=6)
    for x, y, p in zip(ex, me, pts):
        err = (p["measured"] - p["expected"]) / p["expected"] * 100
        b.annotate(f"{p['e']:.0f} mV: {err:+.1f} %", (x, y), xytext=(6, -10), textcoords="offset points",
                   fontsize=7.5)
    b.set_xscale("log")
    b.set_yscale("log")
    b.set_xlim(lo, hi)
    b.set_ylim(lo, hi)
    b.set_xlabel("Expected current, pA")
    b.set_ylabel("Measured current, pA")
    b.set_title("(b) Measured against expected", fontsize=8.5, loc="left")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"fig_known_currents.{ext}"))
    plt.close(fig)
    for p in pts:
        print(f"E {p['e']:.1f} mV  expected {p['expected']*1000:.1f} pA  measured {p['measured']*1000:.1f} pA")



def plateaus(r, tol=0.3, min_len=15, tail=10):
    """Steps of E held for at least min_len s: mean E and S over the last tail s of each."""
    e = [float(x["e"]) for x in r]
    s = [float(x["s"]) for x in r]
    out, start = [], 0
    for i in range(1, len(e) + 1):
        if i == len(e) or abs(e[i] - e[start]) > tol:
            if i - start >= min_len:
                out.append((st.mean(e[i - tail:i]), st.mean(s[i - tail:i])))
            start = i
    return out


def ref3040_linearity_points():
    """Eight stable REF3040 levels, selected by measured E rather than late marks."""
    r = rows("A_REF3040_linearity_2026-10-26_run2.csv")
    targets = [219.9, 200.3, 154.9, 100.2, 0.0, -99.9, -150.2, -201.0]
    out = []
    for target in targets:
        seg = [x for x in r if abs(float(x["e"]) - target) < 0.25]
        out.append((st.mean(float(x["e"]) for x in seg),
                    st.mean(float(x["s"]) for x in seg)))
    return out


def fig_linearity():
    import numpy as np
    r = rows("A_REF3040_linearity_2026-10-26_run2.csv")
    lin = ref3040_linearity_points()
    sat = [x for x in r if x["mark"] == "lin_p250"][-20:]
    out = [(st.mean(float(x["e"]) for x in sat),
            st.mean(float(x["s"]) for x in sat))]
    e = np.array([p[0] for p in lin])
    s = np.array([p[1] for p in lin])
    k, z = np.polyfit(e, s, 1)
    res = (s - (k * e + z)) / abs(k)                     # residual referred to the input, mV

    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8))
    xs = np.linspace(-220, 260, 2)
    a.plot(xs, k * xs + z, color=DARK, lw=0.8, ls="--",
           label=f"fit, {k * 1000:.2f} V/V")
    a.plot(e, s, "o", color=GREEN, ms=4.5, label="measured")
    if out:
        a.plot([p[0] for p in out], [p[1] for p in out], "o", mfc="white", mec=GREEN, ms=4.5,
               label="saturated")
    a.set_xlabel("Board input E, mV")
    a.set_ylabel("Board output S, V")
    a.set_title("(a) Transfer, series resistor shorted", fontsize=8.5, loc="left")
    a.legend(fontsize=7, frameon=False, loc="lower left")

    b.axhspan(-59.16 * 0.01, 59.16 * 0.01, color=GREEN, alpha=0.08, lw=0)   # ±0.01 pH
    b.axhline(0, color=GREY, lw=0.6)
    b.plot(e, res, "o", color=GREEN, ms=4.5)
    b.set_xlabel("Board input E, mV")
    b.set_ylabel("Residual at the input, mV")
    b.set_ylim(-1.5, 1.5)
    b.set_title("(b) Deviation from the line", fontsize=8.5, loc="left")
    ph = b.secondary_yaxis("right", functions=(lambda v: v / 59.16, lambda v: v * 59.16))
    ph.set_ylabel("pH")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"fig_linearity.{ext}"))
    plt.close(fig)
    print(f"gain {k * 1000:.3f} V/V zero {z:.4f} V, residuals {np.round(res, 2)} mV")



def fig_kh():
    from datetime import datetime
    import matplotlib.dates as mdates
    r = rows("K_station_kh_history.csv")
    t = [datetime.fromisoformat(x["time"]) for x in r]
    k = [float(x["kh_dKH"]) for x in r]
    out = [i for i in range(1, len(k) - 1) if abs(k[i] - (k[i - 1] + k[i + 1]) / 2) > 0.2]
    fig, a = plt.subplots(figsize=(7.2, 2.6))
    day0 = t[0].replace(hour=0, minute=0)
    for d in range((t[-1] - day0).days + 1):        # shade 01:00-09:00, the steady part of each night
        s = day0.replace(day=day0.day) + __import__("datetime").timedelta(days=d, hours=1)
        a.axvspan(s, s + __import__("datetime").timedelta(hours=8), color=GREEN, alpha=0.08, lw=0)
    good = [i for i in range(len(k)) if i not in out]
    # smoothed line: centred mean of up to 5 readings (5 h) within one unbroken run
    runs, cur = [], []
    for i in good:
        if cur and (t[i] - t[cur[-1]]).total_seconds() > 2.5 * 3600:
            runs.append(cur); cur = []
        cur.append(i)
    runs.append(cur)
    for n_run, run in enumerate(runs):
        sm = [st.mean(k[j] for j in run[max(0, m - 2):m + 3]) for m in range(len(run))]
        a.plot([t[j] for j in run], sm, "-", color=GREEN, lw=1.6,
               label="5 h moving mean" if n_run == 0 else None)
    a.plot([t[i] for i in good], [k[i] for i in good], "o", color=GREEN, ms=2.2, alpha=0.45,
           mec="none", label="single results")
    a.plot([t[i] for i in out], [k[i] for i in out], "o", mfc="white", mec=BLUE, ms=4,
           label="single outliers (3 of 208)")
    a.xaxis.set_major_locator(mdates.DayLocator())
    a.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    a.set_ylabel("KH, dKH")
    a.set_title("Hourly KH of a reef aquarium, 10-19 Oct 2026 (shaded: 01:00-09:00)",
                fontsize=8.5, loc="left")
    a.legend(fontsize=7, frameon=False, loc="lower right", ncol=3)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"fig_kh_history.{ext}"))
    plt.close(fig)



def steps(rs, tol=0.4, min_len=20, skip=5):
    """Steps of E held at least min_len s: (E, mean leakage pA, sem pA, mean S) after skip s."""
    e = [float(x["e"]) for x in rs]
    out, start = [], 0
    for i in range(1, len(e) + 1):
        if i == len(e) or abs(e[i] - e[start]) > tol:
            if i - start >= min_len:
                seg = rs[start + skip:i]
                il = [float(x["il"]) * 1000 for x in seg]
                out.append((st.mean(float(x["e"]) for x in seg), st.mean(il),
                            st.stdev(il) / len(il) ** 0.5, st.mean(float(x["s"]) for x in seg)))
            start = i
    return out


def fig_ph4502c():
    import numpy as np
    r = rows("G_ph4502c.csv")
    r = r[[i for i, x in enumerate(r) if x["gain"] == "2.863" and float(x["vin"]) != 0.0][0]:]
    t_press = 898                                  # the button is taped down from here on
    rel_all = steps([x for x in r if float(x["t_s"]) < t_press])
    rel = [p for p in rel_all if abs(p[0]) > 5]
    rel0 = [p for p in rel_all if abs(p[0]) <= 5]   # 0 mV with the resistor in circuit
    pre = steps([x for x in r if float(x["t_s"]) >= t_press])   # 0 mV kept: checked again at +1.9 mV
    r_fw = firmware_r(r)
    K = r_fw / R_SERIES
    R = r_fw * 1e6                                 # logged current x firmware R = voltage drop
    # nonlinearity: with the resistor shorted, any "current" is the bend of the transfer
    nl_e = [p[0] for p in pre]
    nl_mv = [p[1] * 1e-12 * R * 1e3 for p in pre]
    # the redesigned board, same reference: a line through its two points nearest +-100 mV
    own = ref3040_linearity_points()
    pa = min(own, key=lambda p: abs(p[0] - 100)); pb = min(own, key=lambda p: abs(p[0] + 100))
    k = (pa[1] - pb[1]) / (pa[0] - pb[0]); z = pa[1] - k * pa[0]
    own_e = [p[0] for p in own]
    own_mv = [(p[1] - (k * p[0] + z)) / k for p in own]   # input-referred, mV
    # true input current: released minus shorted at the same E
    leak = []
    for e, i_rel, sem, _ in rel:
        m = min(pre, key=lambda p: abs(p[0] - e))
        if abs(m[0] - e) < 15:
            leak.append((e, (i_rel - m[1]) * K, sem * K))

    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8))
    a.axhline(0, color=GREY, lw=0.6)
    a.plot(nl_e, nl_mv, "o-", color=BLUE, ms=4, lw=0.9, label="PH-4502C")
    # the 0 mV point of the sweep with the resistor in circuit disagrees with the shorted one
    # by about 3.4 mV for a reason not identified; both are shown (open marker: resistor in)
    if rel0:
        a.plot([p[0] for p in rel0], [p[1] * 1e-12 * R * 1e3 for p in rel0], "o", mfc="none",
               mec=BLUE, ms=5, mew=1.0, label="PH-4502C, 0 mV, resistor in circuit")
    a.plot(sorted(own_e), [m for _, m in sorted(zip(own_e, own_mv))], "o-", color=GREEN, ms=4,
               lw=0.9, label="isolated amplifier")
    a.set_xlabel("Input E, mV")
    a.set_ylabel("Error at the input, mV")
    a.set_title("(a) Error after a ±100 mV calibration", fontsize=8.5, loc="left")
    a.legend(fontsize=7, frameon=False, loc="upper left")
    ph = a.secondary_yaxis("right", functions=(lambda v: v / 59.16, lambda v: v * 59.16))
    ph.set_ylabel("pH")

    b.axhline(0, color=GREY, lw=0.6)
    b.errorbar([x[0] for x in leak], [x[1] for x in leak], yerr=[2 * x[2] for x in leak], fmt="o",
               color=BLUE, ms=4, capsize=2, lw=0.8)
    b.set_ylim(-60, 60)
    b.set_xlabel("Input E, mV")
    b.set_ylabel("Input current, pA")
    b.set_title("(b) PH-4502C input current (±2 SEM)", fontsize=8.5, loc="left")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"fig_ph4502c.{ext}"))
    plt.close(fig)
    for x in leak:
        print(f"E {x[0]:7.1f}  leak {x[1]:6.1f} pA  sem {x[2]:.1f}")
    print("bend mV", [round(v, 1) for v in nl_mv], "own", [round(v, 2) for v in own_mv])



def fig_leak_error():
    """pH error = input current x electrode resistance / Nernst slope, with both boards marked."""
    import numpy as np
    S25 = 59.16                                   # mV per pH at 25 C
    i = np.logspace(-13, -7, 200)
    fig, a = plt.subplots(figsize=(7.2, 3.4))
    lo, hi = i * 100e6 * 1e3 / S25, i * 1e9 * 1e3 / S25
    a.fill_between(i, lo, hi, color=GREY, alpha=0.12, lw=0)
    a.plot(i, hi, color=DARK, lw=1.2, label="1 GΩ electrode")
    a.plot(i, lo, color=DARK, lw=1.2, ls="--", label="100 MΩ electrode")
    for y in (0.01, 1):
        a.axhline(y, color=GREY, lw=0.6, ls=":")
        a.text(1.15e-13, y * 1.15, f"{y:g} pH", fontsize=7.5, color=GREY)
    a.axvspan(8e-9, 13e-9, color=BLUE, alpha=0.25, lw=0)
    a.text(7e-9, 0.04, "Failed amplifier\n8–13 nA", fontsize=8, color=BLUE, ha="right", fontweight="bold")
    a.axvspan(1e-12, 3.5e-12, color=GREEN, alpha=0.3, lw=0)   # toggle runs at -99 and +100 mV
    a.text(4.2e-12, 3, "Isolated amplifier\n1–3.5 pA", fontsize=8, color=GREEN, fontweight="bold")
    a.set_xscale("log"); a.set_yscale("log")
    a.set_xlim(1e-13, 1e-7); a.set_ylim(1e-3, 1e2)
    a.set_xticks([1e-13, 1e-12, 1e-11, 1e-10, 1e-9, 1e-8, 1e-7])
    a.set_xticklabels(["0.1 pA", "1 pA", "10 pA", "100 pA", "1 nA", "10 nA", "100 nA"])
    a.set_yticks([1e-3, 1e-2, 1e-1, 1, 10, 100])
    a.set_yticklabels(["0.001", "0.01", "0.1", "1", "10", "100"])
    a.set_xlabel("Input current of the amplifier")
    a.set_ylabel("Reading error, pH")
    a.legend(fontsize=7.5, frameon=False, loc="upper left")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"fig_leak_error.{ext}"))
    plt.close(fig)

def fig_supply_sensitivity():
    """Revision A divider against revision B REF3040, with the 10 ohm shunt removed."""
    import numpy as np
    raw = rows("E_supply2.csv")
    groups = {"Earlier divider prototype": [], "REF3040 reference": []}
    for x in raw:
        if x["kind"] != "mark":
            continue
        try:
            usb = float(x["volt"])
            current = float(x["i"])
            out = float(x["s_noshunt"])
        except ValueError:
            continue
        name = "REF3040 reference" if current > 20 else "Earlier divider prototype"
        groups[name].append((usb, out))

    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    styles = {
        "Earlier divider prototype": (BLUE, "o"),
        "REF3040 reference": (GREEN, "s"),
    }
    for name, pts in groups.items():
        # Duplicate marked points at the same setting are averaged, preserving raw CSV unchanged.
        by_v = {}
        for v, s in pts:
            by_v.setdefault(v, []).append(s)
        x = np.array(sorted(by_v))
        y = np.array([st.mean(by_v[v]) for v in x])
        k, z = np.polyfit(x, y, 1)
        color, marker = styles[name]
        ax.plot(x, y, marker, color=color, ms=5, label=name)
        xx = np.linspace(x.min(), x.max(), 100)
        gain = 6.087 if name == "REF3040 reference" else 6.27
        ph_per_v = abs(k) / gain / 0.05916
        ax.plot(xx, k * xx + z, color=color, lw=1.2,
                label=f"fit: {k*1000:.1f} mV/V = {ph_per_v:.3f} pH/V")
        print(name, f"slope {k*1000:.3f} mV/V, {ph_per_v:.4f} pH/V")

    ax.set_xlabel("USB supply, V")
    ax.set_ylabel("Board output S, V (10 Ω shunt removed)")
    ax.set_title("Supply sensitivity of the isolated amplifier",
                 fontsize=9, loc="left")
    ax.legend(fontsize=6.8, frameon=False, loc="upper left")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"fig_supply_sensitivity.{ext}"))
    plt.close(fig)


def toggle_phases(name, lo, hi):
    """Phase means (lo..hi s after each switch) and per-cycle toggle / line-based currents."""
    import numpy as np
    r = [x for x in rows(name) if x["valid"] == "1"]
    k = firmware_r(r) / R_SERIES
    marks = [x["mark"] for x in r]
    ts = np.array([float(x["t_s"]) for x in r])                            # s
    t = ts / 60
    dv = np.array([float(x["vin"]) - float(x["e"]) for x in r])          # mV
    il = np.array([float(x["il"]) for x in r]) * 1000 * k                # line-based, pA
    phases, start = [], 0
    for i in range(1, len(r) + 1):
        if i == len(r) or marks[i] != marks[start]:
            if marks[start].split()[0] in ("short", "open"):
                t0 = t[start]
                sel = [j for j in range(start, i) if lo <= ts[j] - ts[start] <= hi]
                phases.append(dict(state=marks[start].split()[0], t0=t0, t1=t[i - 1],
                                   dv=dv[sel].mean(), il=il[sel].mean()))
            start = i
    cur, line = [], []
    for j, p in enumerate(phases):
        if p["state"] != "open":
            continue
        nb = [phases[m]["dv"] for m in (j - 1, j + 1) if 0 <= m < len(phases) and phases[m]["state"] == "short"]
        cur.append((p["dv"] - np.mean(nb)) / R_SERIES * 1000)
        line.append(p["il"])
    return t, dv / R_SERIES * 1000, phases, np.array(cur), np.array(line)


def fig_toggle():
    """Toggle runs: resistor shorted / open at a fixed E; the shorted phases carry the zero drift."""
    import numpy as np
    runs = [("T_toggle_REF3040_2026-10-28.csv", 30, 60, "−99 mV", GREEN),
            ("T_toggle_+100_REF3040_2026-10-28.csv", 10, 30, "+100 mV", BLUE)]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1.6, 1]})
    t, app, phases, _, _ = toggle_phases(runs[0][0], runs[0][1], runs[0][2])
    for p in phases:
        if p["state"] == "short":
            a.axvspan(p["t0"], p["t1"], color=GREY, alpha=0.15, lw=0)
    a.plot(t, app, color=GREEN, lw=0.7)
    for p in phases:
        a.plot([p["t0"] + runs[0][1] / 60, p["t0"] + runs[0][2] / 60], [p["dv"] / R_SERIES * 1000] * 2,
               color=DARK, lw=1.4)
    a.axhline(0, color=GREY, lw=0.6, ls=":")
    a.set_ylim(-6, 2.5)                    # spikes while the button is handled leave the frame
    a.set_xlabel("Time, min")
    a.set_ylabel("(Vin − E) / R, pA")
    a.set_title("(a) E = −99 mV; shorted phases grey", fontsize=8.5, loc="left")
    for name, lo, hi, label, col in runs:
        _, _, _, cur, line = toggle_phases(name, lo, hi)
        n = np.arange(1, len(cur) + 1)
        sem = cur.std(ddof=1) / len(cur) ** 0.5
        b.axhline(cur.mean(), color=col, lw=0.8)
        b.plot(n, cur, "o", color=col, ms=5, label=f"{label}: {cur.mean():.2f} ± {sem:.2f} pA")
        b.plot(n, line, "o", mfc="none", mec=col, ms=5)
        print(label, "toggle pA", np.round(cur, 2), "mean", round(cur.mean(), 2), "sem", round(sem, 2),
              "line mean", round(line.mean(), 2))
    b.set_xlabel("Cycle")
    b.set_ylabel("Input current, pA")
    b.set_xticks(range(1, 9))
    b.set_ylim(-4.2, 0)
    b.set_title("(b) Toggle (filled), transfer line (open)", fontsize=8.5, loc="left")
    b.legend(fontsize=7, frameon=False, loc="center right")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"fig_toggle.{ext}"))
    plt.close(fig)

FIGS = {"leak": fig_leak_error, "known": fig_known, "linearity": fig_linearity,
        "supply": fig_supply_sensitivity, "kh": fig_kh, "ph4502c": fig_ph4502c, "toggle": fig_toggle}
if __name__ == "__main__":
    for name in sys.argv[1:] or FIGS:
        FIGS[name]()
