# Complete single OzCore slot — INT8 MAC + pre/post + CRT + int2fp + control

Scope: one slot, 12 moduli, K=128. This is the full Ozaki-II slot datapath (not the
INT8-bypass single-modulus variant).

## RTL

- `rtl/ozcore_slot_s1.sv`: two preprocess blocks (weight/act) → `ozcore_simd_int8_k128`
  (12 lanes × K=128 = 1,536 INT8 MACs) → `ozcore_crt_int2fp_s1` (12-modulus CRT,
  balanced mod-P wrap, int32→binary32) → valid handshake.
- `rtl/ozcore_preprocess_s1.sv`: 16→8 bit low-byte packing.
- `rtl/ozcore_crt_int2fp_s1.sv`: 12 moduli, CRT constants, mod-P wrap, int2fp.
- `tb/tb_slot_s1.sv`: 5 random vectors, replicated across the 12 residue planes,
  Python golden dot/CRT/float.
- VCS: **SLOT_FULL PASS**, 0 errors.

## Measured block areas (TSMC 28nm HPC+, DC medium)

| Block | Area |
|---|---:|
| 12-lane MAC, K=128 | **334,190.30 µm²** |
| preprocess (12×128 lanes), each | **33,638.98 µm²** |
| preprocess ×2 (weight + act) | 67,277.95 µm² |
| CRT + mod-P + int2fp | **35,172.65 µm²** |
| slot block sum | **436,640.90 µm² = 0.4366 mm²** |

- Full 128 slots by scaling: 128 × 0.4366 = **55.89 mm²** (12-lane architecture).
- Flat slot synthesis is running; see `results/area_slot.txt` when complete.
- This is the 12-lane Ozaki slot; it is not the 6.03 mm² single-modulus 128×128 estimate.
