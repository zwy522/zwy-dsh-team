# OzCore INT8 top, N=8 (functional scaling)

Same INT8 pass-through/bypass path as `../top_int8`, parameter N=8, K=128, S_MAX=12.

- VCS: **5/5 activation frames pass**, 0 errors.
- No synthesis for N=8 yet; area scaling from N=2 (735,954.15/2 per column) gives ~2.94 mm² for 8 columns, excluding shared control/aligner.
- This is a functional scaling check, not a full N=128 array.
