# OzCore single-modulus INT8 top (S_MAX=1, N=128, K=128)

Scope per 2026-11-26 instruction: **single modulus only**, no multi-modulus CRT.

- 128 columns × K=128 = **16,384 signed INT8 multipliers**.
- preprocess: single residue low-byte pass-through; postprocess: bypass int32;
  output aligner [1 slot][128 columns].
- valid-ready handshake; weight load per column; 5 activation frames.
- VCS: **5/5 PASS**, 0 errors.
- DC/TSMC 28nm: synthesis running; area in `results/area.txt` when complete.

This is the paper's **logical 16,384-MAC array** (one modulus), not the 12-residue
fully-parallel variant.
