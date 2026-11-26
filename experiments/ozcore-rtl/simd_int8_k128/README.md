# OzCore INT8 SIMD engine, K=128 — RTL + TSMC 28nm area

This is the full-length INT8 SIMD engine for the reduced single-engine port:
`K=128`, `S_MAX=12`, **1536 signed INT8 multipliers**, combinational.

- `rtl/ozcore_simd_int8_k128.sv`: wrapper instantiating `ozcore_simd_int8 #(.K(128), .S_MAX(12))`.
- `tb/tb_ozcore_simd_int8_k128.sv`: self-checking TB, 20 vectors (zeros, ±127/−128, 17 random).
- `tb/vectors.txt`: Python golden vectors.
- `scripts/gen_vectors.py`, `scripts/run_dc_simd_int8_k128.tcl`.
- `results/`: area/ref/sim logs.

## Results

| Item | Value |
|---|---:|
| Functional | **20/20 PASS**, 0 errors (VCS O-2018.09-SP2) |
| Area | **334,190.30 µm²** (combinational, 0 sequential) |
| Cells | 349,011 |
| Library/flow | TSMC 28nm HPC+ FF, DC O-2018.06-SP1, `compile -map_effort medium` |
| Area per MAC | ≈217.6 µm²/MAC |

**Scaling estimate only:** 128 such engines (one per column) would be
`334,190.30 × 128 ≈ 42.78 mm²`; artifact's `simd_engine` sanitized stage is
52.147 mm². The gap includes array wiring, weight/psum buffers, channel/control,
and parameterization differences. This is **not** a synthesized 128×128 array.

## Limitations

- One engine only; no N=128 array, psum buffer, weight registers, channel handshake.
- No clock constraint → area only, no timing claim.
- Python golden model, not full HLS C++ co-simulation.
- K=128 area is for the reduced single-engine configuration; full OzCore still
  needs preprocess, postprocess, control/top integration.

## Reproduce

```bash
python3 scripts/gen_vectors.py
vcs -full64 -sverilog -timescale=1ns/1ps \
  ../simd_int8/rtl/ozcore_simd_int8.sv rtl/ozcore_simd_int8_k128.sv \
  tb/tb_ozcore_simd_int8_k128.sv -o simv
cp tb/vectors.txt . && ./simv
dc_shell -f scripts/run_dc_simd_int8_k128.tcl
```
