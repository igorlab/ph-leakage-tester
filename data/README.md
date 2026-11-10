# Measurement data

Raw logs of the calibrator, one CSV per protocol, as written by `tools/calibrator_log.py`.
**These files are not edited after recording**, except where a note below says so (one file,
`A2_known_currents_2026-11-08_run9.csv`, had rows rearranged; no value was changed). Every
correction is applied in the analysis scripts
(`analysis/paper_numbers.py`, `figures/make_paper_figures.py`, `tools/new_runs.py`).

## Series resistor R: correction of the logged current

| | value |
|---|---|
| R set in the firmware when the logs up to 2026-10-27 were recorded | 47.94 MΩ (column `r`) |
| R measured as the sum of its five resistors, 40 MΩ range, same multimeter | **49.61 MΩ** |
| R from the calibrator's own ratio Vin/E with Rt = 9.73 MΩ connected (protocol A) | 49.70 MΩ |
| Rt (test resistor of protocol A) | 9.73 MΩ |

The earlier value, 47.94 MΩ, came from two readings (four resistors in series near the top
of the 40 MΩ range, plus the fifth) and was wrong by 3.4 %.

What this affects:

- **Only the column `il`** (current, nA). The firmware computed `il = (vin − e) / r`, so the
  true current is `il × r / 49.61`. For `r = 47.94` the factor is 0.966.
- The voltages `e`, `vin`, `s` and all other columns do not depend on R and are correct.
- Each file stores its own `r`, so the scripts take the factor from the file, not from a
  constant. Files without a `r` column contain no current and need no correction.

Files with a different `r`:

- `H_old_board_I_vs_E.csv`: values transcribed by hand; the old board was measured with a
  20 MΩ resistor, set correctly on the page. No correction.
- `test.csv` (`r = 20`), `zero_check.csv` (`r = 50`): not used in the paper.

## Runs of 2026-10-28 (firmware with the E truncation fixed, `/data` with more decimals)

All runs below were made on board A (REF3040); board A is identified by its supply current, 10.5–17.8 mA in the `i` column.

| file | protocol |
|---|---|
| `T_toggle_REF3040_2026-10-28.csv` | toggle, E = −99 mV, 8 × (60 s shorted + 60 s open), button held by hand |
| `T_toggle_+100_REF3040_2026-10-28.csv` | toggle, E = +100 mV, 8 × (30 s + 30 s), button held by hand |
| `B3_noise_shorted_2026-10-28.csv` | 1 h, E = +100 mV, resistor shorted (button taped) |
| `B2_noise_open_2026-10-28.csv` | 1 h, E = +100 mV, resistor in circuit (started 5 min after B3) |

These were recorded with `r = 49.70` (the value from the ratio test), so the scripts scale
`il` by 49.70/49.61 = 1.0018. All four used the same transfer line, taken before the first
toggle run. Analyse with `tools/new_runs.py` or `analysis/paper_numbers.py` (sections T, N).

New logs should be recorded with `r = 49.61` set on the calibrator page (factor 1). The
scripts read `r` from each file, so a log recorded with another value is still handled
correctly.

## Runs of 2026-11-08 and 2026-11-09 (final firmware, `r = 49.61`, factor 1)

All on board A (REF3040), R = 49.61 MΩ. Described in the journal (`README.md` of the repository)
and in `docs/REPORT_2026-11-09.html`; analysed by `analysis/paper_numbers.py`, sections A2 and T.

| file | protocol |
|---|---|
| `A2_known_currents_2026-11-08_run7.csv` | A2, known currents through *R*ₜ = 9.73 MΩ at *E* = −3, −1, +1, +3, +10, +30, +100 mV; 2 min without, 2 min with, 2 min without *R*ₜ (Table 1b) |
| `A2_known_currents_2026-11-08_run9.csv` | A2, repeat of ±1 and ±3 mV; rows rearranged, see below (Table 2 of the paper) |
| `W_window_n25_2026-11-08.csv`, `W_window_n43_2026-11-08.csv`, `W_window_n25_b_2026-11-08.csv` | ADC diagnostics: number of samples per reading (temporary firmware, not part of the design) |
| `W_diag_sweep_2026-11-08.csv`, `W_diag_sweep2_2026-11-08.csv`, `W_diag_sweep3_E10_2026-11-08.csv`, `W_diag_sweep4_pressed_2026-11-08.csv` | ADC diagnostics: read order and pauses, resistor in circuit and shorted (temporary firmware) |
| `N_overnight_2026-11-09.csv` | 7.2 h unattended at *E* ≈ +1.08 mV, resistor in circuit (13 failed reads, rows absent) |
| `P_polarity_center_2026-11-09.csv`, `P_polarity_center_900s_2026-11-09.csv`, `P_polarity_center_100mV_2026-11-09.csv` | polarity switch plus / center / minus, phases of 5 or 15 min, at ±1.1 and ±100 mV |
| `P_polarity_shorted_100mV_2026-11-09.csv` (interrupted, no phase), `P_polarity_shorted_100mV_2026-11-09_b.csv` | the same with the resistor shorted (button taped) |
| `H_hold_2026-11-09.csv` | 81 min at *E* = −1.13 mV, no switching |
| `W_flash_restart_2026-11-09.csv`, `W_diag_100mV_2026-11-09.csv`, `W_flash_back_2026-11-09.csv` | flashing the diagnostic firmware, ADC read order at ±100 mV (columns `dg`, `dor`, `dsk`), flashing back |
| `W_flash_restart_2026-11-10.csv`, `W_flash_restart_2026-11-10_b.csv`, `W_gap_Rt_2026-11-10.csv`, `W_flash_back_2026-11-10.csv` | flashing the diagnostic firmware, known current at *E* ≈ +3 mV with and without *R*<sub>t</sub> in the normal order and with a 300 ms pause between *E* and *S* (column `dg`), flashing back. The first 125 rows of `W_gap_Rt` are a warm-up stopped early; the rest was appended by a second logger start |
| `T_toggle_-100_2026-11-09.csv`, `T_toggle_+100_2026-11-09.csv`, `T_toggle_+100_2026-11-09_b.csv` | toggle runs at −100 and +100 mV; the first +100 run started about 3 min after the polarity switch was flipped |
| `cap101_run1.csv` | open-input drift on a 100 pF capacitor, tester plug disconnected; preliminary, not used in the paper |

### Rearranged file: `A2_known_currents_2026-11-08_run9.csv`

By decision of the operator, and with no value changed: the phases marked `set +1` and `e+1`
(302 rows) had been recorded at *E* = −1.05 mV and were renamed `set -1` and `e-1`; a phase at
+1 mV was then appended in a separate start of the logger (`--append`); the rows of the
two-point calibration from the interrupted start `run8` (473 rows) were moved to the beginning
of the file; the interrupted starts `run2`–`run6` and `run8` and a warm-up record were deleted.
`A2_known_currents_2026-11-08_run7.csv` is unchanged.

## Naming note: pH 4 buffer in `F_buffers.csv`

The marks in `F_buffers.csv` call the first buffer `4p01` (for example `F_r1_4p01_start`).
This is a label typed during the run: the buffer was then mistakenly believed to be
pH 4.01. It is the nominal pH 4 buffer, which the article calls pH 4.00. The raw file is
unchanged.

## Derived file: `I_isolation_PH4502C_merged.csv`

Protocol I on the PH-4502C was logged in two pieces, both kept unchanged:
`I_isolation_PH4502C.csv` (2026-10-26 18:47–18:56, two-point calibration; 1004 rows) and
`I_ph_4052_board.csv` (19:00–19:16, baselines and both cell polarities; 1895 rows; `4052`
is a typo for 4502). The merged file is these two logs one after the other, with a 4.6 min
gap and `t_s` restarting at the second part. Every value is identical to the source rows;
only the `mark` column differs: marks were relabelled to protocol names (for example `+100` →
`I_PH4502C_cal_plus100`, `ph_4052_baseline1_start` → `I_PH4502C_baseline1_start`, and the
mistyped `I_board_plus_end` → `I_PH4502C_plus_end`), a `I_PH4502C_plus_start` phase was marked
on 138 rows that had no mark, and 32 marks at a phase edge were cleared. Use the two source
files as the raw record.
