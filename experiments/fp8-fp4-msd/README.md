# FP8/FP4 stage: MSD-Core mode analysis

This directory analyzes the FP8/FP4 modes of the user's MSD-Core (TSMC 28 nm
HPC+ FF, v2.0) and compares them with the INT8/MXFP4/native modes and the
format-specific baseline tiles.

- `FP8_FP4_REPORT.md` — main analysis and conclusion.
- `results/mode_power.csv` — per-mode component dynamic power (口径 B, window-dependent).

Source data lives in the user's EDA environment:
`/home/host/03_ASIC综合/dc-package/results/实验结果总结.md` (§2.4/§2.5/§5.6)
and `results_baseline_compare.md`. The DC full-chip FP8/FP4 reports were
regenerated for the FP8/FP4 phase but their absolute values are the known
clock-network modeling artifact; only the pin-cap lower-bound methodology is
used for conclusions.
