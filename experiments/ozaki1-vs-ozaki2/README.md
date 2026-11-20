# Ozaki I vs Ozaki II: cost model and analysis

Theory and cost comparison of Ozaki Scheme I (slice decomposition,
`Q_I = k(k+1)/2` GEMMs) and Ozaki Scheme II (CRT with `s` moduli,
`Q_II = s` GEMMs) for BF16/FP16/FP32/FP64.

- `model/ozaki_cost.py`: pass counts, pre/post element-wise work, memory
  traffic, and a cycle-level time model (128×128 INT8 array, 1 GHz).
- `model/plot_cost.py`: Q vs precision, time vs K, and breakdown plots.
- `results/`: CSV tables and PNG figures, including `moduli_table.csv`
  (s, m_s, M bits, kA+kB, exactness checks).
- `docs/ozaki1-vs-ozaki2-analysis.md`: full write-up (theory, tables,
  verification, discussion).

Run:

```bash
cd experiments/ozaki1-vs-ozaki2
python3 model/ozaki_cost.py
python3 model/plot_cost.py
```

Assumptions: `R_mac=16384`, `R_e=128`, `R_c=16`, `BW=256 B/cycle`, 1 GHz;
time is a conservative serial sum (no overlap). The model is for relative
comparison, not a calibrated chip simulator.
