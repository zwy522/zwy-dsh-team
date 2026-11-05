# FP8 / FP4 MAC synthesis (TSMC 28 nm HPC+ FF)

Parameterized format-native FP MAC with FP32 accumulation, used to replace the
assumed per-MAC area/energy factors in the Ozaki-II comparison.

- `rtl/fp_mac.sv`: format multiply + product normalization to FP32 +
  DesignWare `DW_fp_add` (sig_width=23, exp_width=8).
- `rtl/fp8_mac.sv`, `rtl/fp4_mac.sv`: wrappers (E4M3: SIG_W=4/EXP_W=4/BIAS=7;
  E2M1: SIG_W=2/EXP_W=2/BIAS=1).
- `synth/`: DC scripts + 3.5 ns SDC for TSMC 28HPC+ FF.
- `results/fp8`, `results/fp4`: area/timing/power/qor/constraints/netlist.

Measured (3.5 ns, default activity):

| format | area um^2 | cells | CP ns | slack | energy pJ/MAC |
|---|---:|---:|---:|---:|---:|
| INT8 (P0b) | 378.13 | 365 | 1.13 | +2.26 | 0.366 |
| FP8 E4M3 | 619.42 | 927 | 2.61 | +0.80 | 0.315 |
| FP4 E2M1 | 551.25 | 846 | 2.49 | +0.91 | 0.200 |

Only synthesis was run; the DW FP32 adder was not functionally simulated yet.
