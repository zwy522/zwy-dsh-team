# OzCore INT8 top, N=32 (functional scaling)

Same INT8 pass-through/bypass path as `../top_int8`, parameter N=32, K=128, S_MAX=12.

- VCS: **5/5 activation frames pass**, 0 errors.
- No synthesis for N=32; area scaling from N=2 per-column 367,977.07 µm² gives ~11.78 mm² for 32 columns (excludes shared control/aligner).
- Demonstrates parameter scaling to 32 columns; not a full 128×128 array.
