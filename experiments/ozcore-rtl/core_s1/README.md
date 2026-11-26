# Single-modulus core support blocks + pre-layout full-core budget

Scope: single modulus INT8, no CRT. TSMC 28nm HPC+, DC medium effort, **pre-layout cell area**.

## Measured blocks

| Block | Cells | Area |
|---|---:|---:|
| weight memory 1 KB (N=128,K=8) | 14,855 | 25,690.27 µm² |
| psum 128×32 | 9,186 | 11,213.87 µm² |
| aligner 128×32 | 9,040 | 11,119.37 µm² |
| control FSM (minimal) | 14 | 12.35 µm² |
| preprocess 128 lanes (from `stages_s1`) | 2,318 | 2,803.25 µm² |
| postprocess 128 lanes | 9,040 | 11,119.37 µm² |
| MAC column K=128 (128 MACs) | 29,075 | 27,831.51 µm² |

`CORE_S1: PASS` (weight write/read, psum, aligner, control).

## 128×128 single-modulus pre-layout budget

- MAC array: 128 × 27,831.51 = **3,562,433.25 µm² = 3.5624 mm²**
- activation preprocess: 2,803.25 µm²
- postprocess: 11,119.37 µm²
- weight preprocess (parallel per column): 128 × 2,803.25 = 358,815.74 µm²
- weight memory 16 KB: 16 × 25,690.27 = **411,044.24 µm²**
- psum: 11,213.87 µm²
- aligner: 11,119.37 µm²
- control: 12.35 µm²

**Pre-layout total: 4,368,561.45 µm² = 4.3686 mm²**

## Transparent physical-overhead bracket

No CTS/routing/physical implementation is available (TSMC LEF/TLU+ missing), so this is **not** a 6.03 mm² equivalent measurement. Applying a typical 28nm CTS/route/buffer overhead factor:

| factor | total |
|---:|---:|
| 1.25 | 5.46 mm² |
| 1.30 | 5.68 mm² |
| 1.35 | 5.90 mm² |
| 1.38 | 6.03 mm² |
| 1.40 | 6.12 mm² |

At 1.38 the estimate coincides with the paper's 6.03 mm², but **1.38 is an assumption**, not a measured CTS result. Weight memory is inferred registers, not an SRAM macro; a real SRAM would change that term. Control is minimal and undercounts a production FSM.
