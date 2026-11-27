# OzCore INT8 SIMD core — RTL reimplementation (first stage)

Source: artifact `src/hw/synth/hls/simd_engine/include/simd_engine_parallel_ccore.h`
(`simd_engine_core`, INT8 path). This RTL reproduces the **core formula** for a
reduced configuration: `K=8`, `S_MAX=12`, 96 signed INT8 multipliers.

- `rtl/ozcore_simd_int8.sv`: combinational 12×8 dot products + `shift_out=e+shift_in`.
- `tb/tb_ozcore_simd_int8.sv`: self-checking testbench; reads `tb/vectors.txt`.
- `scripts/gen_vectors.py`: 123 vectors (zeros, ±127/-128, random) + Python golden.
- `scripts/run_dc_simd_int8.tcl`: DC O-2018.06 + TSMC 28nm HPC+.
- `results/`: area/refs/check/sim logs.

## Results

| Item | Value |
|---|---:|
| Functional | **123/123 PASS**, 0 errors (VCS O-2018.09-SP2) |
| Area | **19,301.18 µm²** (combinational, 0 sequential) |
| Cells | 19,934 |
| Library | TSMC 28nm HPC+ FF `tcbn28hpcplus...` |
| Flow | DC O-2018.06-SP1, `compile -map_effort medium` |

## Scope / limitations

- This is **one reduced SIMD core**, not the full `simd_engine_parallel`
  (no N-way parallel engines, weight registers, channel handshakes, psum buffer).
- It covers the INT8 formula only; FP16/FP8/FP4/FPBF/FP64 ALU variants are not ported.
- No clock constraint was applied (combinational core); area only, no timing claim.
- The Python golden is independent; full HLS C++ co-simulation/SCVerify is pending.
- Area is **not** directly comparable to artifact's 52.147 mm² `simd_engine` stage
  (different scope/parallelism/parameterization).

## Reproduce

```bash
python3 scripts/gen_vectors.py
vcs -full64 -sverilog -timescale=1ns/1ps rtl/ozcore_simd_int8.sv tb/tb_ozcore_simd_int8.sv -o simv
./simv
dc_shell -f scripts/run_dc_simd_int8.tcl
```
