#!/usr/bin/env python3
"""Recompute the numbers used in the metapaper from the raw CSV logs.

Usage (from the repository root):
    python3 analysis/paper_numbers.py            # data in ./data
    python3 analysis/paper_numbers.py --data DIR # other data folder

Writes the results to stdout and to analysis/paper_numbers.txt.
Requires: numpy, pandas.

Sections:
  H  early failed board: current vs E, bound on a resistive leak
  B  noise run: logging resolution, Allan deviation, ten-minute drift
  A  known currents through Rt: deviation from expected, effective Rt/R
  G  PH-4502C: two sweeps in opposite directions, point at 0 mV
  F  electrode in buffers at 23 degC: slope, zero, residual
  T  toggle runs at -99 and +100 mV (2026-10-28)
  N  one-hour runs shorted / in circuit, unattended transition (2026-10-28)
  U  uncertainty helpers: multimeter spec, E truncation in readA()
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = []

# R as the sum of its five resistors and Rt, both on the 40 MOhm range of one multimeter.
# Each log stores the R the firmware used (column r, MOhm). The firmware computed
# il = (vin - e) / r, so il * r is the voltage drop and il * r / R_TRUE the true current.
# Raw CSV files are never modified; see data/README.md.
R_TRUE, RT = 49.61, 9.73   # MOhm


def firmware_r(d):
    """The single R value (MOhm) the firmware used for this log."""
    values = d["r"].dropna().unique()
    if len(values) != 1:
        sys.exit(f"expected one value of r in the log, found {values}")
    return float(values[0])


def say(text=""):
    print(text)
    OUT.append(text)


# ---------------------------------------------------------------- H
def section_h(data):
    say("== H. Early failed board (H_old_board_I_vs_E.csv) ==")
    say("Values transcribed by hand from the logger display; raw log not preserved.")
    d = pd.read_csv(data / "H_old_board_I_vs_E.csv")
    e_v = d.E_mV / 1000.0
    i_na = d.il_nA
    p, cov = np.polyfit(e_v, i_na, 1, cov=True)
    slope, slope_se = p[0], np.sqrt(cov[0, 0])
    say(f"points: {len(d)}, E from {d.E_mV.min()} to {d.E_mV.max()} mV")
    say(f"mean current: {i_na.mean():.2f} nA, SD (n-1): {i_na.std(ddof=1):.3f} nA")
    say(f"slope dI/dE: {slope:.3f} +- {slope_se:.3f} nA/V (least squares, 1 SE)")
    bound = abs(slope) + 3 * slope_se          # nA/V, upper bound on conductance
    r_min_gohm = 1.0 / bound                   # 1/(nA/V) = GOhm
    v_needed = i_na.mean() * r_min_gohm        # nA * GOhm = V
    say(f"3-sigma bound on |dI/dE|: {bound:.3f} nA/V -> resistive leak > {r_min_gohm:.2f} GOhm")
    say(f"voltage needed to drive the mean current through it: > {v_needed:.1f} V")
    r_series_mohm = 20.0
    say(f"slope expected if the output saturated (R = {r_series_mohm:.0f} MOhm): "
        f"-1/R = {-1000.0 / r_series_mohm:.0f} nA/V")
    say()


# ---------------------------------------------------------------- B
def allan(y, m):
    """Non-overlapping Allan deviation for blocks of m consecutive readings."""
    n = len(y) // m
    if n < 2:
        return np.nan, n
    blocks = y[: n * m].reshape(n, m).mean(axis=1)
    return np.sqrt(0.5 * np.mean(np.diff(blocks) ** 2)), n


def section_b(data):
    say("== B. Noise run (B_noise_REF3040_2026-10-26.csv) ==")
    d = pd.read_csv(data / "B_noise_REF3040_2026-10-26.csv")
    d = d[(d.valid == 1) & (d.t_s <= 3600)].reset_index(drop=True)
    r_fw = firmware_r(d)
    k = r_fw / R_TRUE
    y = (d.il * 1000.0 * k).to_numpy()         # pA, rescaled to R_TRUE
    say(f"selection: valid == 1 and t_s <= 3600 s; il in pA, scaled by r/R_TRUE = "
        f"{r_fw}/{R_TRUE} = {k:.4f}")
    say(f"readings: {len(y)}, median interval {d.t_s.diff().median():.2f} s")
    say(f"mean: {y.mean():.2f} pA, SD of single readings: {y.std(ddof=1):.2f} pA")
    say("logging resolution: il is written with 3 decimals in nA, i.e. 1 pA steps (before scaling)")
    counts = pd.Series(np.round(y / k)).value_counts().sort_index()
    say("distribution of logged values before scaling (pA: count): "
        + ", ".join(f"{int(k)}: {v}" for k, v in counts.items()))
    in_band = (np.abs(y - y.mean()) <= 1.5).mean() * 100
    say(f"share within 1.5 pA of the mean: {in_band:.1f} %")

    clean = y[np.abs(y - y.mean()) < 5]
    say(f"clean set: |I - mean| < 5 pA, {len(y) - len(clean)} readings removed")
    say("Allan deviation, pA (block = number of consecutive ~1 s readings):")
    say("  block   all      clean    n_blocks")
    for m in [1, 3, 10, 30, 60, 120, 300, 600, 900]:
        a_all, n = allan(y, m)
        a_cl, _ = allan(clean, m)
        say(f"  {m:5d}   {a_all:6.3f}   {a_cl:6.3f}   {n}")
    ten = [y[i * 600:(i + 1) * 600].mean() for i in range(len(y) // 600)]
    say("ten-minute means, pA: " + ", ".join(f"{v:.2f}" for v in ten))
    say(f"  range: {min(ten):.2f} to {max(ten):.2f} pA")
    one = [y[i * 60:(i + 1) * 60].mean() for i in range(len(y) // 60)]
    say(f"SD of {len(one)} one-minute means: {np.std(one, ddof=1):.2f} pA "
        "(includes the slow drift)")
    say()


# ---------------------------------------------------------------- A
def section_a(data, r_mohm=R_TRUE, rt_mohm=RT):
    say("== A. Known currents (A_10M_run3.csv) ==")
    d = pd.read_csv(data / "A_10M_run3.csv")
    # Marks: 'e100', 'e30', 'e10' start a voltage; 'on' = Rt connected; 'off' = removed.
    label, state, blk = None, None, []
    for m in d.mark:
        if isinstance(m, str):
            if m.startswith("e"):
                label, state = m, "before"
            elif m == "on":
                state = "on"
            elif m == "off":
                state = "after"
        blk.append(f"{label}_{state}")
    d["blk"] = blk
    r_fw = firmware_r(d)
    k = r_fw / r_mohm
    say(f"R = {r_mohm} MOhm, Rt = {rt_mohm} MOhm; logged currents (firmware r = {r_fw}) "
        f"scaled by {k:.4f}")
    say("method: median current with Rt minus median current without Rt (before and after)")
    say("  E      expected nA   measured nA   dev %   Rt/R from Vin/E")
    for ev in ["e100", "e30", "e10"]:
        on = d[d.blk == f"{ev}_on"]
        off = d[(d.blk == f"{ev}_before") | (d.blk == f"{ev}_after")]
        e_mv = on.e.median()
        base = off.il.median()
        d_i = (on.il.median() - base) * k
        expected = -e_mv / (r_mohm + rt_mohm)           # mV / MOhm = nA
        vin = on.vin.median() - base * r_fw             # remove the baseline drop, mV
        x = vin / e_mv                                  # = Rt / (R + Rt)
        ratio = x / (1 - x)
        say(f"  {e_mv:5.1f}  {expected:10.4f}   {d_i:10.4f}   {100 * (d_i / expected - 1):+5.2f}"
            f"   {ratio:.4f}")
        after = d[d.blk == f"{ev}_after"]
        if len(after) and abs(after.e.median() - e_mv) > 1:
            say(f"    note: the 'after' phase of {ev} was logged at E = {after.e.median():.1f} mV")
    say(f"Rt/R from the multimeter: {rt_mohm / r_mohm:.4f}")
    say("e10 uses vin logged with 0.1 mV resolution on ~1.8 mV, so its ratio is imprecise;")
    say("the e100 ratio gives R independently of the multimeter value of R:")
    on = d[d.blk == "e100_on"]
    off = d[(d.blk == "e100_before") | (d.blk == "e100_after")]
    x = (on.vin.median() - off.il.median() * r_fw) / on.e.median()
    say(f"  R_eff = {rt_mohm / (x / (1 - x)):.2f} MOhm")
    say()


# ---------------------------------------------------------------- G
def section_g(data):
    say("== G. PH-4502C (G_ph4502c.csv) ==")
    d = pd.read_csv(data / "G_ph4502c.csv")
    d = d[d.gain == 2.863].copy()           # rows recorded with the module's own line
    d["seg"] = (d.e.diff().abs() > 2).cumsum()
    g = d.groupby("seg").agg(t0=("t_s", "min"), n=("e", "size"), e=("e", "median"),
                             vin=("vin", "median"), il_sd=("il", "std"))
    g = g[g.n >= 8].copy()
    # Protocol G: all voltages first with the resistor in circuit (sweep up to +425 mV),
    # then with it shorted (sweep down). The button is taped down from t = 898 s
    # (same split as figures/make_paper_figures.py), which falls inside the +425 mV
    # plateau, so plateaus are cut there.
    t_press = 898.0
    d["seg"] = ((d.e.diff().abs() > 2) | ((d.t_s >= t_press) & (d.t_s.shift() < t_press))).cumsum()
    g = d.groupby("seg").agg(t0=("t_s", "min"), n=("e", "size"), e=("e", "median"),
                             vin=("vin", "median"), il_sd=("il", "std"))
    g = g[g.n >= 8].copy()
    g["err_mv"] = g.vin - g.e
    g["state"] = np.where(g.t0 >= t_press, "shorted", "resistor")
    say("plateaus: E steps > 2 mV, or the button press at t = 898 s, start a new plateau;")
    say("plateaus with < 8 readings dropped; plateaus from t >= 898 s are the shorted sweep")
    say("note: the shorted 0 mV plateau includes a re-check at about +1.9 mV")
    say("  t0 s    E mV    state      error at input mV   SD of il, nA")
    for _, r in g.iterrows():
        say(f"  {r.t0:6.0f}  {r.e:7.1f}  {r.state:9s}  {r.err_mv:+6.2f}"
            f"              {r.il_sd:.3f}")
    say("pairs at the same E (within 3 mV), resistor vs shorted sweep:")
    res, sh = g[g.state == "resistor"], g[g.state == "shorted"]
    for _, a in res.iterrows():
        m = sh[(sh.e - a.e).abs() < 3]
        if len(m):
            b = m.iloc[0]
            say(f"  E {a.e:7.1f}: {a.err_mv:+6.2f} vs {b.err_mv:+6.2f} mV "
                f"(difference {a.err_mv - b.err_mv:+5.2f})")
    say()


# ---------------------------------------------------------------- F
def section_f(data, temp_c=23.0):
    say("== F. Electrode in buffers (F_buffers.csv) ==")
    d = pd.read_csv(data / "F_buffers.csv", usecols=["t_s", "mark", "vin"])
    # Buffer values from the manufacturer's table on the sachet (20 and 25 degC),
    # interpolated linearly to the solution temperature.
    table = {"4p01": (4.00, 4.00), "6p86": (6.88, 6.86), "9p18": (9.23, 9.18)}
    ph, mv = [], []
    say(f"solution temperature: {temp_c} degC; window: 300 s before the first '_end' row")
    say("  buffer  pH at T   vin mean mV   SD mV   n")
    for key, (p20, p25) in table.items():
        t_end = d.loc[d.mark == f"F_r1_{key}_end", "t_s"].iloc[0]
        w = d[(d.t_s > t_end - 300) & (d.t_s <= t_end)]
        p_t = p20 + (p25 - p20) * (temp_c - 20.0) / 5.0
        ph.append(p_t)
        mv.append(w.vin.mean())
        say(f"  {key:6s}  {p_t:6.3f}   {w.vin.mean():10.3f}   {w.vin.std():6.3f}   {len(w)}")
    ph, mv = np.array(ph), np.array(mv)
    k, b = np.polyfit(ph, mv, 1)
    res = mv - (k * ph + b)
    ideal = 8.314462618 * (273.15 + temp_c) / 96485.33212 * np.log(10) * 1000.0
    say(f"slope: {k:.2f} mV/pH, ideal at {temp_c} degC: {ideal:.2f} mV/pH "
        f"({-100 * k / ideal:.1f} %)")
    say(f"pH at 0 mV: {-b / k:.3f}; largest residual: {np.abs(res).max():.2f} mV")
    say()


# ---------------------------------------------------------------- T, N (runs of 2026-10-28)
def toggle_currents(d, lo, hi):
    """Per-cycle toggle and line-based currents (pA) from a log with marks short N / open N."""
    m = d["mark"].astype(str).str.extract(r"^(short|open) (\d+)$")
    d = d.assign(st=m[0])
    d = d[d.st.notna() & (d.valid == 1)].copy()
    d["ph"] = (d["mark"] != d["mark"].shift()).cumsum()
    d["tp"] = d.t_s - d.groupby("ph").t_s.transform("min")
    k = firmware_r(d) / R_TRUE
    w = d[(d.tp >= lo) & (d.tp <= hi)]
    g = w.groupby("ph").agg(st=("st", "first"), e=("e", "mean"), vin=("vin", "mean"), il=("il", "mean"))
    cur, line, de = [], [], []
    for j, r in g[g.st == "open"].iterrows():
        nb = [g.loc[x] for x in (j - 1, j + 1) if x in g.index and g.loc[x, "st"] == "short"]
        dv_s = np.mean([x.vin - x.e for x in nb])
        cur.append(((r.vin - r.e) - dv_s) / R_TRUE * 1000)
        line.append(r.il * 1000 * k)
        de.append((r.e - np.mean([x.e for x in nb])) * 1000)
    return np.array(cur), np.array(line), np.array(de)


def section_t(data):
    say("== T. Toggle runs on the REF3040 board (2026-10-28) ==")
    say("window: lo..hi s after each switch; current = [(vin-e)_open - mean (vin-e)_shorted "
        "neighbours] / R_TRUE")
    for name, lo, hi in [("T_toggle_REF3040_2026-10-28.csv", 30, 60),
                         ("T_toggle_+100_REF3040_2026-10-28.csv", 10, 30)]:
        d = pd.read_csv(data / name)
        cur, line, de = toggle_currents(d, lo, hi)
        sem = cur.std(ddof=1) / np.sqrt(len(cur))
        say(f"{name}: E {d.e.mean():.1f} mV, window {lo}-{hi} s")
        say("  toggle pA: " + ", ".join(f"{v:+.2f}" for v in cur))
        say(f"  mean {cur.mean():+.2f} pA, SEM {sem:.2f} pA; line-based mean {line.mean():+.2f} pA")
        say(f"  E open minus E shorted (button held by hand): mean {de.mean():+.1f} uV")
    say()


def section_n(data):
    say("== N. One-hour runs at E = +100 mV, resistor shorted (B3) and in circuit (B2) ==")
    out = {}
    for name in ["B3_noise_shorted_2026-10-28.csv", "B2_noise_open_2026-10-28.csv"]:
        d = pd.read_csv(data / name)
        d = d[d.valid == 1].reset_index(drop=True)
        y = (d.il * 1000.0 * firmware_r(d) / R_TRUE).to_numpy()
        out[name] = d
        say(f"{name}: {len(y)} readings, mean {y.mean():+.3f} pA, SD {y.std(ddof=1):.3f} pA")
        say("  Allan deviation, pA: " + ", ".join(
            f"{m} s {allan(y, m)[0]:.3f}" for m in [1, 10, 60, 300, 600]))
        ten = [y[i * 600:(i + 1) * 600].mean() for i in range(len(y) // 600)]
        say("  ten-minute means, pA: " + ", ".join(f"{v:+.2f}" for v in ten))
    # unattended transition: B3 (shorted, button taped) -> B2 (open), 5 min apart
    b3, b2 = out["B3_noise_shorted_2026-10-28.csv"], out["B2_noise_open_2026-10-28.csv"]
    t3, t2 = pd.to_datetime(b3.time), pd.to_datetime(b2.time)
    x3 = (t3 - t3.iloc[0]).dt.total_seconds() / 60
    x2 = (t2 - t3.iloc[0]).dt.total_seconds() / 60
    p = np.polyfit(x3[-1200:], b3.e[-1200:], 1)            # E trend over the last 20 min of B3
    e_pred = np.polyval(p, x2[:300].mean())
    say(f"transition B3 -> B2: E jump beyond the trend {1000 * (b2.e[:300].mean() - e_pred):+.1f} uV")
    dv3 = (b3.vin - b3.e)[-300:].mean()
    dv2 = (b2.vin - b2.e)[:300].mean()
    say(f"  current from (vin-e): {(dv2 - dv3) / R_TRUE * 1000:+.2f} pA "
        "(last 5 min of B3 vs first 5 min of B2)")
    say()


# ---------------------------------------------------------------- U
def section_u(r_mohm=R_TRUE):
    say("== U. Uncertainty helpers ==")
    # MS8229, 40 MOhm range: +-(2 % + 5 digits), 1 digit = 0.01 MOhm.
    readings = 5                                   # each resistor separately
    u_r = 0.02 * r_mohm + readings * 5 * 0.01
    say(f"R from {readings} readings on the 40 MOhm range: +-{u_r:.2f} MOhm "
        f"(+-{100 * u_r / r_mohm:.1f} %)")
    lsb_uv = 62.5                                   # ADS1115, +-2.048 V range
    say(f"E truncation in readA(): up to 1 LSB = {lsb_uv} uV -> "
        f"{lsb_uv / r_mohm:.2f} pA at R = {r_mohm} MOhm")
    say()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path,
                    default=Path(__file__).resolve().parent.parent / "data")
    args = ap.parse_args()
    for f in (section_h, section_b, section_a, section_g, section_f, section_t, section_n):
        f(args.data)
    section_u()
    out = Path(__file__).resolve().parent / "paper_numbers.txt"
    out.write_text("\n".join(OUT) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
