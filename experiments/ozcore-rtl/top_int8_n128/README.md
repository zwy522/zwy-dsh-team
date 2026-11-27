# OzCore INT8 top, N=128, K=128 — full functional array

This is the **full N=128 × K=128 INT8 path** at the functional level:

```
preprocess INT8 pass-through (low byte)
  → 128 columns × 12 planes × K=128 signed INT8 dot products
  → postprocess bypass (raw int32)
  → output aligner [12 slots][128 columns]
```

- `rtl/ozcore_top_int8.sv`: shared parameterized top (N=128, K=128, S_MAX=12).
- `tb/tb_ozcore_top_int8_n128.sv`: loads 128 weight columns + 5 activation frames, checks 12×128 int32 outputs vs Python golden.
- `scripts/gen_vectors.py`: Python golden (196,608 MACs per frame).
- VCS: **5/5 activation frames pass**, 0 errors.

## Limits

- **Functional only**: no full N=128 synthesis (196,608 multipliers; monolithic DC impractical in this environment).
- Area estimate from N=2 per-column 367,977.07 µm² × 128 = **47.10 mm²**, excluding shared control/aligner; not a synthesized number.
- INT8×INT8 `s=1` bypass only; no CRT/float preprocess/postprocess.
- Single-cycle combinational dot products; no pipelining/timing.
