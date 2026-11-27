# OzCore INT8 top, N=16 (functional scaling)

Same INT8 pass-through/bypass path as `../top_int8`, parameter N=16, K=128, S_MAX=12.

- VCS: **5/5 activation frames pass**, 0 errors.
- No synthesis for N=16; area scaling from N=2 per-column 367,977.07 µm² gives ~5.89 mm² for 16 columns (excludes shared control/aligner).
- Demonstrates parameter scaling toward N=128; N=16 is not a full 128×128 array.
