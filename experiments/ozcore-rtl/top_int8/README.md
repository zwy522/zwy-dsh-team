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
| Configuration | K=128, N=2, S_MAX=12, INT8×INT8 |
| Area | pending DC; see `results/area.txt` when complete |

## Limitations

- This is **INT8×INT8 s=1 bypass** only; no CRT/float path.
- N=2 columns (not 128); no channel valid/ready backpressure, no psum buffer, no pipelining.
- Single-cycle combinational dot products; area/latency not representative of the full N=128 chip.
- Full N=128 needs the array/control integration and a pipelined schedule.
