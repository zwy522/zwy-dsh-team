# 128x128 array-level comparison

Flat 128x128 synthesis (16384 lanes) was not feasible in the 8 GB EDA VM
(>3M cells for INT8, ~15M for FP8/FP4). Instead, an 8x8 tile (64 lanes) was
synthesized for each format on TSMC 28 nm HPC+ FF at 3.5 ns, and the 128x128
array is composed of 256 such tiles (area = 256 x tile; top-level glue small).

- `rtl/`: 8x8 tile wrappers (int8_tile8_array, fp8_tile8, fp4_tile8).
- `synth/`: DC scripts + SDC.
- `results/{int8,fp8,fp4}_tile8/`: area/timing/power/qor reports.
- `results/array_summary.csv`: per-lane and composed 128x128 numbers.

Power: the tile DC power does not scale linearly (clock-network modeling), so
the 128x128 power column uses the measured single-lane default-activity power
x 16384, not tile_power x 256.
