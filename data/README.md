# Measurement data

Raw logs of the calibrator, one CSV per protocol, as written by `tools/calibrator_log.py`.
**These files are never edited.** Every correction is applied in the analysis scripts
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
