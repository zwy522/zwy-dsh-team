# Ozaki-II format comparison (INT8 / FP8 / FP4)

This directory re-runs the Ozaki-II decomposition for three base formats and
compares area-energy efficiency at the same target precision (BF16/FP16/FP32/FP64).

- `OZAKI_FORMAT_REPORT.md` — method, pass counts, results and sensitivity.
- `model/ozaki_formats.py` — pass-count + area-energy model.
- `results/pass_counts.csv` — generated table.

The INT8 per-MAC area/energy comes from P0b (TSMC 28 nm HPC+ FF, 3.5 ns).
FP8/FP4 per-MAC area/energy are scaling assumptions; replacing them with
synthesized MACs is the next step.

Run:

```bash
python3 model/ozaki_formats.py
```
