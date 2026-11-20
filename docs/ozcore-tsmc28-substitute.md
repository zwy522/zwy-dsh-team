# OzCore Ten-four RTL：TSMC 28nm HPC+ 替代综合

> 目的：在用户确认“用 TSMC 28nm HPC+ 替代 FDSOI”后，用 **同一份 Ten-four RTL** 做一次独立综合，验证 artifact 的面积趋势与 RTL 可综合性。
> 环境：IC_EDA VM（CentOS 7）、Design Compiler O-2018.06-SP1、TSMC 28nm HPC+ FF `tcbn28hpcplusbwp40p140ffg0p99v0c_ccs`、300 MHz（3.333 ns）、K=128（N=64）。
> 非 exact：论文面积来自 28nm FDSOI + Catapult/DC 流程；这里是 TSMC 28nm HPC+，不能替换论文绝对值。

## 1. 方法

- Ten-four RTL：artifact `src/hw/synth/ten-four/rtl/versions/v_int8_only`。
- Vortex 共享依赖：`VX_define.vh`、`VX_gpu_pkg.sv`、`VX_csa_32/42/mod4/tree`、`VX_ks_adder`、`VX_pipe_register`、`VX_lzc`、`VX_wallace_mul` 等，来自 `github.com/vortexgpgpu/vortex`（本环境 GitHub 不可达，改用 Gitee 镜像 `gitee.com/jasonuiao/vortex` 克隆）。
- `VX_config.vh`/`VX_types.vh`：用 Vortex `ci/gen_config.py` 从 `VX_config.toml`/`VX_types.toml` 生成（XLEN=64）。
- DC 定义：`VX_CFG_XLEN=64 VX_CFG_XLEN_64 NUM_THREADS=32 NUM_TCU_LANES=4 ASIC`；`ASIC` 使 `STRING` 为空、`UNUSED_SPARAM` 为 no-op，符合 DC 综合。
- 顶层 `VX_tcu_fedp_tfr -parameters "N=64"`（TCK=128）。

## 2. 结果（INT8，K=128）

| 项 | 数值 |
|---|---:|
| TSMC 28nm HPC+ 面积 | **62,969.0 µm²** |
| cells | 63,897 |
| 关键路径 | 1.06 ns（slack +1.64 ns @3.333 ns） |
| artifact FDSOI 面积（per column） | 59,901.9 µm² |
| 比值（TSMC/FDSOI） | **1.051×** |

结论：同一份 INT8 Ten-four RTL 在 TSMC 28nm HPC+ 上综合得到 62,969 µm²，与 artifact 的 FDSOI 59,902 µm² 只差 **5.1%**。这说明：

1. Ten-four RTL 与综合流程是可复现的（在补齐 Vortex 依赖后）；
2. TSMC 28nm HPC+ 与论文 FDSOI 在该设计上的面积密度接近（至少对 INT8 变体），
   因此用 TSMC 做替代趋势验证是合理的；
3. 但不能把 62,969 当作论文的绝对面积——工艺/库/flow 不同。

## 3. FP16 变体

FP16 Ten-four（artifact 134,284.7 µm²/column）正在同一流程下综合；
需要 `VX_lzc`/`VX_wallace_mul`/`VX_find_first` 等额外依赖，DC 运行时间明显更长。
完成后会补上 TSMC/FDSOI 比值与 FP16/INT8 融合税对比。

## 4. 复现

```bash
# Vortex (Gitee mirror, because github.com is unreachable here)
git clone --depth 1 https://gitee.com/jasonuiao/vortex.git /home/host/vortex
# generate configs on a Python>=3.7 host, then copy to VM:
python3 ci/gen_config.py -c VX_config.toml -f verilog -o VX_config.vh
XLEN=64 python3 ci/gen_config.py -c VX_types.toml -f verilog -o VX_types.vh --resolved
# DC
cd /home/host/tenfour && dc_shell -f run_dc_int8_n64.tcl
```

脚本与结果：`reproduction/ozcore/tsmc28/`。

## 5. 限制

- 库/工艺不同（TSMC 28nm HPC+ vs 论文 FDSOI），不能复现 27.9%/1.91×/1.40× 的绝对面积/密度；
- 这是 Ten-four（开源 baseline）的替代综合，不是 OzCore HLS stages；OzCore stages 仍需 Catapult + FDSOI 才能精确复现；
- 300 MHz、DC O-2018.06 与论文 flow 不完全一致（论文 Ten-four 用 DC V-2023.12-SP5-3 gate-mapping）；
- 结果用于趋势/RTL 可综合性验证，不作为论文数值的替代。
