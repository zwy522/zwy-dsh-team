# Corrected 12-pass single-column slot (K=128, 16,384-MAC architecture family)

This replaces the earlier 12-lane spatial slot. One K=128 MAC column is reused for 12
modulus passes; no 12× spatial multipliers.

- `rtl/ozcore_slot12_s1.sv`: preprocess residue generation (mask for m=256, shift-based
  constant mod for odd m), 12 sequential residue dot products, CRT + mod-P tree + int2fp,
  pass FSM.
- `rtl/ozcore_crt_int2fp_s1.sv`: 12-modulus CRT, reconfigurable wrap tree, int2fp.
- `tb/tb_slot12_s1.sv`: 5 random K=128 vectors, Python golden dot/CRT/float.
- Data outputs match the Python golden for all 5 cases; the `out_valid` pulse timing in
  the TB still needs a fix (data comparison passes, valid sampling is off by one edge).

## Divider-free CRT (paper method)

- `ozcore_crt_int2fp_s1.sv` now uses the paper's `red16` (`comp = 256-m`, four Horner steps)
  plus a 32-bit three-limb reduction; **no behavioral `%`/divider remains in the CRT**.
- VCS data still matches Python golden 5/5; valid sampling still off by one edge.
- DC `report_area` did not complete (process died after mapping); the last compile table
  showed ~**49,763 µm²**, so the divider-free version is not yet smaller than the old
  `%` version (35,172.65 µm²). The Horner multipliers need sharing/pipelining.
- Slot lower bound with 49,763: 27,831.51 + 49,763 = **77,594.5 µm² = 0.0776 mm²**;
  ×128 = **9.93 mm²** (worse than the 8.06 mm² behavioral-CRT estimate).

## Area status

- MAC column (K=128 = 128 MACs): **27,831.51 µm²** (measured).
- CRT + mod-P + int2fp: **35,172.65 µm²** (measured).
- Slot lower bound without preprocess/FSM: **63,004.16 µm² = 0.0630 mm²**.
- ×128 columns: **8.06 mm²** lower bound for the 16,384-MAC core.
- Flat slot DC was attempted but did not complete (memory/time); block sum is the current
  number. This is larger than the paper's 6.03 mm² because the CRT uses behavioral
  `%`/divider-style arithmetic and is not yet optimized/shared.
