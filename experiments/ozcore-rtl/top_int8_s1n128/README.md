# OzCore single-modulus INT8 top (S_MAX=1, N=128, K=128)

Scope per 2026-11-26 instruction: **single modulus only**, no multi-modulus CRT.

- 128 columns × K=128 = **16,384 signed INT8 multipliers**.
- preprocess: single residue low-byte pass-through; postprocess: bypass int32;
  output aligner [1 slot][128 columns].
- valid-ready handshake; weight load per column; 5 activation frames.
- VCS: **5/5 PASS**, 0 errors.
- DC/TSMC 28nm: 16,384-MAC synthesis ran 43 min (low effort) and a 4,096-MAC K=32 calibration ran 30 min; both still in mapping, terminated without an area report.
- **Estimates only**: K=128 single-engine measured area 334,190.30 µm² for 1,536 MACs → 16,384 MACs ≈ **3.56 mm²**; adding weight/control ≈ **3.6–4.0 mm²**. This is not a synthesized array area.

This is the paper's **logical 16,384-MAC array** (one modulus), not the 12-residue
fully-parallel variant.
