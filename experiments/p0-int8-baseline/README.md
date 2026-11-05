# P0 — INT8 baseline calibration

Status: P0 INT8 baseline complete (28 nm DC + VCS; power is default-activity);
the absolute OzCore reproduction gate is not met (see `results/P0_REPORT.md`).
This directory holds the artifacts for P0 of
[`docs/single-format-executor-area-energy-plan.md`](../../docs/single-format-executor-area-energy-plan.md):

- reproduce the OzCore-style INT8 MAC baseline (area / timing / power estimate);
- estimate the INT8 pass count needed for BF16- and FP32-equivalent accuracy;
- record the deviations from the paper's 28 nm HLS + Design Compiler/PrimePower
  setup.

## Contents

| Path | Purpose |
|---|---|
| `rtl/int8_mac.sv` | 3-stage signed INT8 MAC lane, INT32 accumulator |
| `rtl/int8_array.sv` | Replicated N-lane array wrapper |
| `synth/run_dc.tcl` | 28 nm DC script for one MAC (SMIC HPC RVT TT) |
| `synth/run_dc_array4.tcl` | 28 nm DC script for the 4-lane array |
| `synth/synopsys.sdc` | 300 MHz constraints for the 28 nm DC flow |
| `synth/run_synth.sh` | Optional open-source fallback (Yosys + Sky130 HD) |
| `model/ozaki2_int8.py` | Reduced Ozaki-II / CRT pass-count model |
| `results/pass_count.csv` | s vs relative-L2 error sweep |
| `results/P0_REPORT.md` | P0 findings, deviations and next steps |
| `results/metrics.csv` | Computed area/power/energy-extrapolation metrics |
| `results/dc_int8_mac/` | DC reports + netlist for one MAC |
| `results/dc_int8_array_n4/` | DC reports + netlist for the 4-lane array |
| `results/calib_floatMuilt/` | Flow calibration with the environment FP16 multiplier |

## Reproduce (28 nm DC/VCS in the user's EDA VM)

The reported numbers come from the EDA VM in
`/home/oem/zwy.work/Graduationthesis` (CentOS + Synopsys DC O-2018.06-SP1,
VCS O-2018.09, SMIC 28 nm HPC RVT TT library). The commercial library is not
vendored.

```bash
# Inside the EDA VM, with the files copied to /home/host/p0_int8:
cd /home/host/p0_int8
dc_shell -f run_dc.tcl -output_log_file dc.log              # 1 MAC
dc_shell -f run_dc_array4.tcl -output_log_file dc_array4.log # 4-lane array
vcs -full64 -sverilog tb_int8_mac.v rtl/int8_mac.v -o simv && ./simv

# On the host, regenerate the reduced Ozaki-II pass-count model:
cd experiments/p0-int8-baseline
python3 model/ozaki2_int8.py --out results/pass_count.csv
```

`synth/run_synth.sh` is an optional open-source (Yosys + Sky130 HD) fallback.
It was not used for the reported 28 nm numbers.

## Known limitations

- Power is DC `report_power` with default activity, not SAIF/VCD-annotated;
  treat it as an order-of-magnitude estimate. SAIF-based power is the next step.
- The full 128×128 array is inferred by linear scaling from the 4-lane array,
  not synthesized as one block; array-level control/wire overhead is not fully
  captured.
- The Ozaki-II model uses global power-of-two scaling and a conservative
  modulus budget; it is a reduced model, not a bit-exact OzCore replica. Its
  pass counts are conservative relative to OzCore's tighter scaling.
- Only INT8 is implemented; FP8 and FP4 are the next phases.
- The absolute OzCore reproduction gate (<20% area/power) is not met; see
  `results/P0_REPORT.md` for the gap analysis.
