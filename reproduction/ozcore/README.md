# OzCore (MICRO 2026) reproduction

Reproduction of the Zenodo artifact `micro2026-ozcore-artifact-evaluation`
v1.2 (DOI 10.5281/zenodo.22748465) on a CPU-only Linux host.

- `reproduce_cpu.sh`: runs all Category-A CPU launchers.
- `generated/`: command outputs (`tab*.txt`) and regenerated figures.
- `results/repro_summary.csv`: target, depth, computed vs paper.
- Full report: `docs/ozcore-reproduction.md`.

The artifact source/ZIP is not committed here (third-party code/data, ~13 MB);
download it from Zenodo, extract, then run:

```bash
bash reproduce_cpu.sh /path/to/ozcore-artifact
```

Requirements: Python 3, numpy, pandas, matplotlib, jupyter/nbconvert, adjustText.

Scope: CPU redraw/recompute of the shipped data; the report distinguishes
CPU-reproducible tables/figures from GPU/NDA results that cannot be independently
re-run here.
