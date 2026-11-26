# OzCore INT8 top path (N=2, K=128) — functional prototype

This is the first **full INT8 data path** prototype:

```
preprocess INT8 pass-through (low byte of 16-bit slot)
  → N=2 columns × 12 planes × K=128 signed INT8 dot products
  → postprocess bypass (raw int32)
  → output aligner [slot 12][column N]
```

- `rtl/ozcore_top_int8.sv`: single-cycle compute; weight memory per column; preprocess/pass-through; bypass output.
- `tb/tb_ozcore_top_int8.sv`: loads N weight frames, 5 activation frames, checks all 12×N int32 outputs vs Python golden.
- `scripts/gen_vectors.py`: K=128, N=2, 12 planes; Python golden.
- `scripts/run_dc_top_int8.tcl`: DC/TSMC 28nm.

## Results

| Item | Value |
|---|---:|
| Functional | **5/5 PASS**, 0 errors (VCS O-2018.09-SP2) |
| Handshake | `weight_ready`/`act_ready`/`out_ready` valid-ready added; N=2/4/8 all pass |
| Configuration | K=128, N=2, S_MAX=12, INT8×INT8 |
| Area | **735,954.15 µm²** (726,372 cells), combinational (pre-handshake) |

**Scaling:** 735,954.15 / 2 = 367,977.07 µm² per column; 128 columns
→ **47.10 mm²**. Artifact `simd_engine` sanitized stage is 52.147 mm² (ratio 0.903).
This is a scaling estimate, not a synthesized 108×128 array; it excludes the
control/aligner/pipeline and uses a single-cycle combinational datapath.

## Limitations

- This is **INT8×INT8 s=1 bypass** only; no CRT/float path.
- N=2 columns (not 128); no channel valid/ready backpressure, no psum buffer, no pipelining.
- Single-cycle combinational dot products; area/latency not representative of the full N=128 chip.
- Full N=128 needs the array/control integration and a pipelined schedule.
