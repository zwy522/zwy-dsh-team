# Single-modulus preprocess / postprocess / INT8 MAC stage synthesis

Scope: single modulus, INT8×INT8 `s=1` pass-through/bypass; no multi-modulus CRT.

## RTL

- `rtl/ozcore_preprocess_s1.sv`: K=128 lanes, 16-bit int slots → low 8 bits.
- `rtl/ozcore_postprocess_s1.sv`: K=128 lanes, int32 bypass (no CRT).
- `rtl/ozcore_mac_col_s1.sv`: K=128 signed INT8 dot product (128 MACs).
- `rtl/ozcore_lane_s1.sv`: preprocess → MAC column → postprocess lane.
- `tb/tb_stages_s1.sv`: pre/post/MAC/lane vs Python golden.
- VCS: **STAGES_S1 PASS**, 0 errors.

## TSMC 28nm HPC+ DC area (medium effort)

| Block | Cells | Area |
|---|---:|---:|
| preprocess (K=128, 128 lanes) | 2,318 | **2,803.25 µm²** |
| postprocess (K=128, 128 lanes) | 9,040 | **11,119.37 µm²** |
| MAC column (K=128 = 128 MACs) | 29,075 | **27,831.51 µm²** |
| lane (pre + MAC + post) | 33,994 | **33,607.98 µm²** |

## Single-modulus 128×128 combination (block-level estimate)

- MAC array: 128 × 27,831.51 = **3.5624 mm²**.
- + one activation preprocess + one postprocess: **3.5764 mm²** (optimistic; weight preprocess shared/time-multiplexed).
- + 128 weight preprocess blocks: **3.9352 mm²** (weights preprocessed in parallel per column).
- Per-lane fully parallel upper bound (2 pre + MAC + post per lane): 128 × 33,607.98 = **4.3018 mm²**.

These are **block-level sums**, not a single 16,384-MAC top synthesis; control, weight memory, and aligner are not separately included. Full-array DC was impractical in the VM (16k MACs: 43 min, still mapping).
