# OzCore INT8 top, N=1 (single column, K=128)

Single-column variant of `../top_int8`, used to get a per-column top area without
the 3072-multiplier N=2 synthesis.

- `rtl/ozcore_top_k128n1.sv`: wrapper with K=128, N=1, S_MAX=12.
- `rtl/ozcore_top_int8.sv`: shared top (parameter N=1 supported via width guard).
- VCS: **5/5 activation frames pass**, 0 errors.
- DC: single-column synthesis was started; see `results/area.txt` when complete.
