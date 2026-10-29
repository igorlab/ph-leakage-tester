#!/usr/bin/env python3
"""Log every live reading of the calibrator to a CSV file.

The page's own "Download CSV" keeps only time, pH and S. A measurement also needs E, the
board input, the leakage and the calibration line. All of them are in /data, the JSON the
page itself polls, so this script polls it too and writes every field it finds.

    python3 tools/calibrator_log.py -o run.csv                 # until Ctrl+C
    python3 tools/calibrator_log.py -o noise.csv -d 3600       # one hour
    python3 tools/calibrator_log.py -o line.csv -g linearity    # guided 30 s points
    python3 tools/calibrator_log.py -o leak.csv -g leakage      # guided 120 s points
    python3 tools/calibrator_log.py -o tog.csv -g toggle -n 8   # button pressed/released, 60 s each

Normally, type a short note and press Enter ("Rt 1G in", "E +100"): it goes into the
"mark" column of every following row, so the phases of an experiment can be told apart.
The status line shows the seconds since the last mark, so a phase can be timed from it
(type the note first, then press Enter at the moment the phase starts).

Guided mode automates a sequence of manually adjusted points. Set the potential, wait until
it is ready, then type ``m``. The script reads the actual E from /data, records the point for
the protocol's duration and prints ``next``. Type ``r`` to repeat the last completed point;
``q`` stops. A companion ``*_summary.csv`` contains one row per attempt. A beep sounds at
'next'.

Toggle mode guides a series-resistor toggle run at a fixed E: it asks you to press the
button (resistor shorted), counts down the phase, beeps, asks you to release it (resistor in
circuit), and so on for ``-n`` cycles, ending with one more shorted phase. Do the action,
then press Enter: the phase starts at that moment. Every row is logged; the mark column reads
``wait``, ``short 1``, ``open 1``, ``short 2``... Analyse with analysis/new_runs.py toggle.

Only GET /data is sent. The calibrator is not reset and its settings are not touched.
Fields of /data: e - E, mV; s - shunt-corrected board output, V; s_raw - direct ADS
reading referred to calibrator GND, V; shunt_drop - i*Rsh, V; vin - board input, mV;
il - leakage, nA; noise - noise of shunt-corrected S, mV; noise_raw - raw S noise, mV;
gain, zero - the calibration line; r - series
resistor, MΩ; i - board current, mA.
"""
import argparse
import csv
import json
import os
import select
import socket
import statistics
import sys
import time
import urllib.request
from datetime import datetime

ap = argparse.ArgumentParser(description="Log the calibrator's /data to CSV.")
ap.add_argument("-o", "--out", required=True,
                help="CSV file to create, folders included (never overwritten)")
ap.add_argument("-H", "--host", default="calibrator.local",
                help="name or IP, optionally :port (calibrator.local)")
ap.add_argument("-i", "--interval", type=float, default=1.0, help="seconds between readings (1)")
ap.add_argument("-d", "--duration", type=float, default=0, help="stop after this many seconds")
ap.add_argument("-m", "--mark", default="", help="initial text of the mark column")
ap.add_argument("-g", "--guided", choices=("linearity", "leakage", "supply", "custom", "toggle"),
                help="guided m/r point mode: linearity=30 s, leakage=120 s, supply=60 s; "
                     "toggle = press/release the button, 60 s per phase")
ap.add_argument("-n", "--cycles", type=int, default=8,
                help="toggle mode: number of shorted+open cycles (8)")
ap.add_argument("-p", "--point-seconds", type=float,
                help="seconds per guided point (required for custom; overrides protocol)")
args = ap.parse_args()

GUIDED_SECONDS = {"linearity": 30.0, "leakage": 120.0, "supply": 60.0, "toggle": 60.0}
TOGGLE = args.guided == "toggle"
POINTS = bool(args.guided) and not TOGGLE    # the m/r point modes
if TOGGLE and args.cycles < 1:
    ap.error("--cycles must be at least 1")
if args.guided == "custom" and args.point_seconds is None:
    ap.error("--guided custom requires --point-seconds")
if args.point_seconds is not None and args.point_seconds <= 0:
    ap.error("--point-seconds must be positive")
if args.guided and args.duration:
    ap.error("--duration cannot be combined with --guided")
point_seconds = (args.point_seconds if args.point_seconds is not None else
                 GUIDED_SECONDS.get(args.guided, 0.0))

host, _, port = args.host.partition(":")
ip = socket.gethostbyname(host)               # resolve once: mDNS lookups are slow
url = f"http://{ip}{':' + port if port else ''}/data"
os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
try:
    f = open(args.out, "x", newline="")
except FileExistsError:
    sys.exit(f"{args.out} already exists: choose another name")
summary_f = summary_w = None
summary_path = ""
if POINTS:
    root, ext = os.path.splitext(args.out)
    summary_path = root + "_summary" + (ext or ".csv")
    try:
        summary_f = open(summary_path, "x", newline="")
    except FileExistsError:
        f.close()
        os.remove(args.out)
        sys.exit(f"{summary_path} already exists: choose another output name")
    summary_w = csv.writer(summary_f, lineterminator="\n")
    summary_w.writerow(["point", "attempt", "started", "duration_s", "rows",
                        "e_start_mV", "e_mean_mV", "e_sd_mV", "s_mean_V", "s_sd_V",
                        "vin_mean_mV", "il_mean_nA", "i_mean_mA"])
    print(f"guided {args.guided}: {point_seconds:g} s per point; set the potential, then type m. "
          "After 'next', type m for a new point or r to repeat the last one; q stops.",
          file=sys.stderr)
elif TOGGLE:
    print(f"toggle: {args.cycles} cycles of {point_seconds:g} s shorted + {point_seconds:g} s open, "
          f"about {(2 * args.cycles + 1) * point_seconds / 60:.0f} min. Do the action, then press "
          "Enter; q stops. Keep hands away from the BNC, cable and resistor while it is open.",
          file=sys.stderr)
else:
    print(f"logging {url} to {args.out} every {args.interval:g} s; type a note + Enter to mark, "
          "Ctrl+C to stop", file=sys.stderr)
w = None
keys = []
mark = args.mark or ("wait" if TOGGLE else "")
t0 = time.monotonic()
mark_t = t0                                   # when the current mark was set
next_t = t0
rows = fails = 0
stdin_open = True
latest = None
active = False
point = attempt = 0
point_t = 0.0
point_started = ""
point_e_start = float("nan")
point_values = {}
completed = 0
toggle_seq = ([(p, k) for k in range(1, args.cycles + 1) for p in ("short", "open")]
              + [("short", args.cycles + 1)]) if TOGGLE else []
toggle_i = 0                                  # index of the next phase to start
toggle_waiting = True                         # waiting for Enter to start that phase

def beep():
    print("\a", end="", file=sys.stderr, flush=True)

def toggle_prompt():
    phase, k = toggle_seq[toggle_i]
    if phase == "short":
        text = "PRESS the button (resistor shorted), then press Enter"
    else:
        text = "RELEASE the button, move your hand away, then press Enter"
    print(f"\n[{toggle_i + 1}/{len(toggle_seq)}] {text}", file=sys.stderr)

if TOGGLE:
    toggle_prompt()

def number(d, key):
    try:
        return float(d.get(key))
    except (TypeError, ValueError):
        return None

def mean_sd(values):
    if not values:
        return "", ""
    return f"{statistics.mean(values):.9g}", (f"{statistics.stdev(values):.9g}"
                                                  if len(values) > 1 else "0")

def begin_point(repeat=False):
    global active, point, attempt, point_t, point_started, point_e_start, point_values, mark
    if latest is None:
        print("no reading yet; wait for E to appear and type the command again", file=sys.stderr)
        return
    if active:
        print("point is already recording; wait for 'next'", file=sys.stderr)
        return
    if repeat:
        if point == 0:
            print("nothing to repeat yet; use m for the first point", file=sys.stderr)
            return
        attempt += 1
    else:
        point += 1
        attempt = 1
    point_t = time.monotonic()
    point_started = datetime.now().isoformat(timespec="milliseconds")
    e = number(latest, "e")
    point_e_start = e if e is not None else float("nan")
    point_values = {k: [] for k in ("e", "s", "vin", "il", "i")}
    mark = f"point {point} attempt {attempt} E {point_e_start:+.3f} mV"
    active = True
    verb = "repeat" if repeat else "measure"
    print(f"{verb}: point {point}, attempt {attempt}, E {point_e_start:+.3f} mV, "
          f"recording {point_seconds:g} s", file=sys.stderr)

def finish_point(now):
    global active, completed
    e_mean, e_sd = mean_sd(point_values["e"])
    s_mean, s_sd = mean_sd(point_values["s"])
    vin_mean, _ = mean_sd(point_values["vin"])
    il_mean, _ = mean_sd(point_values["il"])
    i_mean, _ = mean_sd(point_values["i"])
    summary_w.writerow([point, attempt, point_started, f"{now - point_t:.3f}",
                        len(point_values["e"]), f"{point_e_start:.9g}", e_mean, e_sd,
                        s_mean, s_sd, vin_mean, il_mean, i_mean])
    summary_f.flush()
    active = False
    completed += 1
    print(f"done: point {point}, attempt {attempt}, E mean {e_mean} mV ({e_sd} sd); next",
          file=sys.stderr)
    beep()

try:
    while not args.duration or time.monotonic() - t0 < args.duration:
        wait = max(0.0, next_t - time.monotonic())
        if stdin_open:
            ready = select.select([sys.stdin], [], [], wait)[0]
        else:
            time.sleep(wait)
            ready = []
        if ready:
            line = sys.stdin.readline()
            if line:
                command = line.strip().lower()
                if TOGGLE:
                    if command == "q":
                        break
                    if toggle_waiting:
                        phase, k = toggle_seq[toggle_i]
                        mark = f"{phase} {k}"
                        mark_t = time.monotonic()
                        toggle_waiting = False
                        print(f"started: {mark}", file=sys.stderr)
                    else:
                        print("phase is running; wait for the beep", file=sys.stderr)
                elif args.guided:
                    if command == "m":
                        begin_point(False)
                    elif command == "r":
                        begin_point(True)
                    elif command == "q":
                        break
                    else:
                        print("command: m = measure, r = repeat last point, q = quit",
                              file=sys.stderr)
                else:
                    mark = line.strip()
                    mark_t = time.monotonic()
                    print(f"mark: {mark}", file=sys.stderr)
            else:
                stdin_open = False                 # stdin closed: keep logging without marks
            continue
        next_t = max(next_t + args.interval, time.monotonic() - args.interval)  # no burst after an outage
        try:
            with urllib.request.urlopen(url, timeout=max(2.0, args.interval * 2)) as r:
                d = json.load(r)
        except (OSError, ValueError) as e:
            fails += 1
            print(f"no reading ({e})", file=sys.stderr)
            continue
        latest = d
        now = time.monotonic()
        if POINTS and not active:
            continue
        if w is None:
            keys = list(d)
            w = csv.writer(f, lineterminator="\n")
            prefix = (["time", "t_s", "mark", "point", "attempt", "point_t_s",
                       "point_duration_s", "e_start_mV"] if POINTS else
                      ["time", "t_s", "mark"])
            w.writerow(prefix + keys)
        prefix_values = ([datetime.now().isoformat(timespec="milliseconds"), f"{now - t0:.2f}",
                          mark, point, attempt, f"{now - point_t:.2f}",
                          f"{point_seconds:g}", f"{point_e_start:.9g}"] if POINTS else
                         [datetime.now().isoformat(timespec="milliseconds"),
                          f"{now - t0:.2f}", mark])
        w.writerow(prefix_values + [d.get(k, "") for k in keys])
        f.flush()
        rows += 1
        if POINTS:
            for key in point_values:
                value = number(d, key)
                if value is not None:
                    point_values[key].append(value)
            if now - point_t >= point_seconds:
                finish_point(now)
        if TOGGLE:
            if not toggle_waiting:
                left = point_seconds - (now - mark_t)
                if left > 0:
                    print(f"\r  {mark}: {left:3.0f} s left   ", end="", file=sys.stderr, flush=True)
                else:
                    beep()
                    toggle_i += 1
                    toggle_waiting = True
                    if toggle_i >= len(toggle_seq):
                        print(f"\ntoggle run finished: {len(toggle_seq)} phases", file=sys.stderr)
                        break
                    toggle_prompt()
            continue
        if rows % 10 == 1:
            phase_elapsed = now - point_t if POINTS else now - mark_t
            print(f"{now - t0:7.0f} s  E {d.get('e')} mV  S {d.get('s')} V  Vin {d.get('vin')} mV  "
                  f"I {d.get('il')} nA  [{mark} +{phase_elapsed:.0f} s]", file=sys.stderr)
except KeyboardInterrupt:
    pass
finally:
    f.close()
    if summary_f is not None:
        summary_f.close()
    if not rows:
        os.remove(args.out)                        # nothing logged: leave no empty file
    if POINTS and not completed:
        os.remove(summary_path)
    print(f"{rows} rows written to {args.out}, {fails} failed readings", file=sys.stderr)
