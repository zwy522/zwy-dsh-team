# TSMC 28nm HPC+ substitute synthesis of Ten-four RTL

Same Ten-four FEDP RTL as the OzCore artifact (`src/hw/synth/ten-four`),
synthesized with **TSMC 28nm HPC+ FF** (not the paper's NDA 28nm FDSOI),
Design Compiler O-2018.06-SP1, 300 MHz (3.333 ns), K=128 (N=64).

- Vortex headers/modules: `github.com/vortexgpgpu/vortex` (cloned from the
  Gitee mirror `gitee.com/jasonuiao/vortex` because GitHub is unreachable here).
- `VX_config.vh`/`VX_types.vh` generated from `VX_config.toml` with
  `gen_config.py` (XLEN=64).
- DC defines: `VX_CFG_XLEN=64 VX_CFG_XLEN_64 NUM_THREADS=32 NUM_TCU_LANES=4 ASIC`.
- Top: `VX_tcu_fedp_tfr -parameters "N=64"`.

Result (INT8 variant):

| RTL | TSMC 28nm HPC+ area | cells | CP | artifact FDSOI | ratio |
|---|---:|---:|---:|---:|---:|
| Ten-four INT8 | **62,969.0 µm²** | 63,897 | 1.06 ns | 59,901.9 µm² | **1.051×** |

FP16 variant synthesis is still running / pending; see the report.

Files: `run_dc_int8_n64.tcl`, `area_int8.txt`, `qor_int8.txt`, `timing_int8.txt`.

Caveat: TSMC 28nm HPC+ is not the paper's FDSOI library; this is a
library-substituted check, not an exact reproduction of the paper's absolute
area. It validates the RTL/flow and the relative area trend.
