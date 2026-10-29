#!/usr/bin/env python3
"""Analyse the new runs: toggle (short/open) and noise.

    python3 analysis/new_runs.py toggle data/T_toggle_REF3040_2026-10-28.csv
    python3 analysis/new_runs.py noise  data/B2_open.csv data/B3_shorted.csv

The toggle log comes from tools/calibrator_log.py -g toggle: the mark column reads
"short 1", "open 1", "short 2", ... Only rows from --settle to --phase seconds after the
start of each phase are used, so rows logged while you are already switching are dropped.

toggle: for every open phase, the input current is
        I = [(vin - e)_open - (vin - e)_short] / R,
    where (vin - e)_short is the mean of the shorted phases before and after it. A slow
    drift of the calibration zero appears in both and cancels, so this does not depend
    on the zero of the transfer line. The first --settle seconds of every phase are dropped.
    It also reports the line-based current (column il) for the same open phases; the
    difference is the zero error of the line-based method.

noise: mean, SD, Allan deviation and ten-minute means of il for each file, rescaled to
    R_TRUE with the R the firmware used (column r).

R_TRUE is the series resistor measured as the sum of its five resistors.
"""
import argparse
import sys

import numpy as np
import pandas as pd

R_TRUE = 49.61   # MOhm


def toggle(path, settle, phase_len):
    d = pd.read_csv(path)
    m = d["mark"].astype(str).str.extract(r"^(short|open) (\d+)$")
    d["phase"] = m[0]
    d = d[d.phase.notna() & (d.valid == 1)].copy()
    d["phase_n"] = (d["mark"] != d["mark"].shift()).cumsum()       # 1, 2, 3 ... in order
    d["t_phase"] = d.t_s - d.groupby("phase_n").t_s.transform("min")
    d["dv"] = d.vin - d.e                                   # mV
    g = (d[(d.t_phase >= settle) & (d.t_phase <= phase_len)].groupby("phase_n")
         .agg(phase=("phase", "first"), n=("dv", "size"), dv=("dv", "mean"),
              dv_sd=("dv", "std"), e=("e", "mean"), il=("il", "mean"), r=("r", "first")))
    print(f"file: {path}")
    print(f"window: {settle:.0f} to {phase_len:.0f} s of each phase; R_TRUE = {R_TRUE} MOhm")
    print(f"firmware R in the log: {sorted(d.r.unique())} MOhm")
    print(" phase  state   n   E mV      (vin-e) mV")
    for k, r in g.iterrows():
        print(f" {k:5d}  {r.phase:5s} {r.n:4d}  {r.e:8.3f}  {r.dv:+9.4f}")
    cur, line = [], []
    for k, r in g[g.phase == "open"].iterrows():
        nb = [g.loc[j, "dv"] for j in (k - 1, k + 1) if j in g.index and g.loc[j, "phase"] == "short"]
        if not nb:
            continue
        i_pa = (r.dv - np.mean(nb)) / R_TRUE * 1000.0       # mV / MOhm = nA -> pA
        cur.append(i_pa)
        line.append(r.il * 1000.0 * r.r / R_TRUE)           # line-based, rescaled to R_TRUE
    if not cur:
        sys.exit("no open phase with a shorted neighbour")
    cur, line = np.array(cur), np.array(line)
    print("\n open phase   toggle I, pA   line-based I, pA")
    for a, b in zip(cur, line):
        print(f"             {a:+10.2f}     {b:+10.2f}")
    sem = cur.std(ddof=1) / np.sqrt(len(cur)) if len(cur) > 1 else float("nan")
    print(f"\ntoggle current: {cur.mean():+.2f} pA, SD {cur.std(ddof=1):.2f} pA, "
          f"SEM {sem:.2f} pA, n = {len(cur)}")
    print(f"line-based current, same phases: {line.mean():+.2f} pA")
    print(f"difference (zero error of the line method): {line.mean() - cur.mean():+.2f} pA")


def allan(y, m):
    n = len(y) // m
    if n < 2:
        return np.nan
    b = y[: n * m].reshape(n, m).mean(axis=1)
    return np.sqrt(0.5 * np.mean(np.diff(b) ** 2))


def noise(paths, seconds):
    for path in paths:
        d = pd.read_csv(path)
        d = d[(d.valid == 1) & (d.t_s <= seconds)]
        k = d.r.iloc[0] / R_TRUE
        y = (d.il * 1000.0 * k).to_numpy()
        print(f"== {path}")
        print(f"readings {len(y)}, firmware R {d.r.iloc[0]} MOhm -> scale {k:.4f}, "
              f"E {d.e.mean():.2f} mV")
        print(f"mean {y.mean():+.3f} pA, SD {y.std(ddof=1):.3f} pA")
        print("Allan deviation, pA:  " + "  ".join(
            f"{m}s {allan(y, m):.3f}" for m in [1, 3, 10, 30, 60, 120, 300, 600]))
        ten = [y[i * 600:(i + 1) * 600].mean() for i in range(len(y) // 600)]
        print("ten-minute means, pA: " + ", ".join(f"{v:+.2f}" for v in ten))
        print()


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
t = sub.add_parser("toggle")
t.add_argument("csv")
t.add_argument("--settle", type=float, default=30.0, help="seconds dropped per phase (30)")
t.add_argument("--phase", type=float, default=60.0, help="phase length used in the run (60)")
n = sub.add_parser("noise")
n.add_argument("csv", nargs="+")
n.add_argument("--seconds", type=float, default=3600.0, help="use the first N s (3600)")
a = ap.parse_args()
if a.cmd == "toggle":
    toggle(a.csv, a.settle, a.phase)
else:
    noise(a.csv, a.seconds)
