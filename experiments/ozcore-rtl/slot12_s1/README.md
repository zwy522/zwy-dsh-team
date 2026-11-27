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

## Divider-free + shared CRT (paper method)

- `ozcore_crt_int2fp_s1.sv` replaces `%` with paper `red16` (`comp=256-m`, Horner).
- `ozcore_crt_seq_s1.sv` **shares one red16/mod32 unit and one 96×8 multiply over 12 cycles**;
  the slot uses this sequential CRT slot (no 12 parallel CRT datapaths).
- VCS: **SLOT12 PASS 5/5**; `out_valid` is now sticky until the next `start`, fixing the
  previous off-by-one sampling.
- Area: sequential shared CRT **26,313.08 µm² / 29,276 cells**, vs 49,763 µm² for the
  parallel divider-free version (≈47% smaller).
- Slot lower bound: 27,831.51 + 26,313.08 = **54,144.59 µm² = 0.0541 mm²**.
- ×128 columns: **6.93 mm²** lower bound; + 128 weight preprocess (~0.36 mm²) ≈ **7.29 mm²**,
  still above paper 6.03; control/aligner not included.

## Area status