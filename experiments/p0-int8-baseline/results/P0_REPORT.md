# P0 基线报告：INT8 MAC 的 28 nm 面积/功耗/时序与 Ozaki-II pass 数

> 状态：P0 基线流程与数据已建立；**与 OzCore 的绝对数值复现未达标**（M1 的 <20% 门槛未通过），差距已定位。
> 日期：2026-11-05
> 环境：`/home/oem/zwy.work/Graduationthesis`（EDA VM：CentOS 7.9 + Synopsys DC O-2018.06-SP1 + VCS O-2018.09 + SMIC 28 nm HPC 库）

## 1. 结论摘要

在 SMIC 28 nm HPC RVT TT 库（0.90 V、85 °C）、300 MHz（3.333 ns）约束下：

| 设计 | 总面积 (µm²) | cells | 时序 | 动态功耗 | 漏电 | 总功耗 |
|---|---:|---:|---|---:|---:|---:|
| `int8_mac`（1 lane，3 级流水） | 1281.67 | 767（697 comb / 70 seq） | 3.25 ns，slack 0.00 | 504.85 µW | 80.16 µW | 585.01 µW |
| `int8_array_n4`（4 lane） | 4847.14 | 3214（2930 comb / 279 seq） | 3.25 ns，slack 0.00 | 1.809 mW | 323.97 µW | 2.133 mW |

- 4 lane 阵列近似线性扩展，per-lane 面积 1211.78 µm²、per-lane 功耗 0.533 mW（默认活动率）。
- 外推 128×128（16384 lane）：面积约 **19.85 mm²**、功耗约 **8.74 W**（默认活动率）、峰值 **9.83 TOPS** → **1.13 TOPS/W**、**0.495 TOPS/mm²**。
- OzCore 论文的 128×128 INT8 阵列为 **4.35 mm²**、单 OzCore 功耗 **0.47 W**、**21 TOPS/W**；本基线面积约为其 **4.6×**，功耗约为 **18.6×**。
- 位精确 Ozaki-II 模型（简化版）给出：BF16 等价（相对 L2 ≤1e-2）约需 **s=4**；FP32 等价（≤1e-6）约需 **s=7**。OzCore 报告 s=3 达到 BF16 等价（其缩放更紧），本模型偏保守。
- VCS 定向功能测试通过（`PASS int8_mac directed cases`）。

**判断**：P0 的流程已经跑通，28 nm 数据可复现；但“复现 OzCore 绝对面积/功耗”这一 M1 目标未达成。原因主要是通用 RTL + 高功耗标准单元库 + 每 lane 独立控制/缓冲，而不是比较方法本身。后续 FP8/FP4 若沿用同一 RTL/库/活动率口径，**相对**面积/功耗比较仍然有效；绝对数值需在优化或标定后使用。

## 2. 环境与流程

| 项 | 值 |
|---|---|
| 主机工作区 | `/home/oem/zwy.work/Graduationthesis` |
| EDA VM | CentOS 7.9，用户 `host`，IP `192.168.18.128`（VMware NAT） |
| DC | Synopsys DC O-2018.06-SP1 |
| VCS | Synopsys VCS O-2018.09-1 |
| 综合库 | `sc12mcpp140z_l28hpc_hpk_rvt_c30_tt_ctypical_max_0p90v_85c.db`（SMIC 28 nm HPC RVT，TT，0.90 V，85 °C） |
| 时钟 | 300 MHz（3.333 ns），`compile_ultra -no_autoungroup` |
| 面积口径 | DC `report_area` 标准单元面积，不含互连/布线 |
| 功耗口径 | DC `report_power` 默认活动率（未标注 SAIF/VCD）；动态 + 漏电 |

VM 内综合目录：`/home/host/p0_int8`；本仓库保留了 RTL、脚本和报告（见 `results/`）。

## 3. RTL 与功能验证

- `rtl/int8_mac.sv`：3 级流水（操作数寄存器 → 8×8 有符号乘法 + 符号扩展 → INT32 累加），`valid` 门控累加，`acc_clear` 与 `valid` 对齐。
- `rtl/int8_array.sv`：N lane 复制；`rtl/int8_array_n4.v` 为 4 lane 顶层。
- 修复了两个在 P0 中发现的问题：
  1. 乘法结果与 `prod_ext_s2` 的流水对齐（原实现多延迟一拍，`valid_out` 与 `acc` 错位）；
  2. 累加未受 `valid` 门控（空闲周期会重复累加最后一个乘积）。
- `rtl/tb_int8_mac.v`：3 个定向用例（3×4 清零加载、−2×5 累加、7×−3 累加），VCS 通过。

## 4. 综合结果

### 4.1 面积与单元

| 指标 | `int8_mac` | `int8_array_n4` |
|---|---:|---:|
| Total cell area (µm²) | 1281.672 | 4847.136 |
| Combinational area (µm²) | 991.368 | 3697.848 |
| Noncombinational area (µm²) | 290.304 | 1149.288 |
| Buf/Inv area (µm²) | 541.800 | 1832.040 |
| cells | 767 | 3214 |
| comb / seq | 697 / 70 | 2930 / 279 |
| buf/inv count | 145 | 489 |

- 4 lane 阵列中 4 个 lane 的面积分别为 1281.3、1158.9、1158.2、1144.4 µm²，另有 104.3 µm² 顶层逻辑；平均 per-lane 1211.8 µm²。
- **Buf/Inv 面积占比很高**（MAC 42.3%，阵列 37.8%），主要来自每 lane 的 clock/reset/valid/clear 缓冲。这是后续共享控制、减小面积的主要着力点。

### 4.2 时序

- 关键路径：`acc_reg` → 32-bit 累加反馈（55 级逻辑）→ `acc_reg`，3.25 ns；300 MHz 下 slack 0.00（刚好满足）。
- 也就是说，该实现的最高频率约 300 MHz；若目标更高频率，需要把累加器改为更快的结构（CLA/分段流水）或插流水级。

### 4.3 功耗与能量

| 指标 | 值 |
|---|---:|
| MAC 动态/漏电/总功耗 | 504.85 / 80.16 / 585.01 µW |
| 4-lane 阵列总功耗 | 2.133 mW |
| per-MAC 能量（默认活动率，300 MHz） | 1.778 pJ/MAC |
| 128×128 外推功耗 | 8.74 W |
| 128×128 外推能量/有效 MAC | 1.778 pJ（默认活动率） |

**重要限制**：DC 未标注 SAIF/VCD，默认活动率通常偏悲观；真实 workload 的活动率可能低一个数量级。若按 10× 活动率折算，128×128 功耗约 0.87 W，对应约 11.3 TOPS/W，仍低于 OzCore 的 21 TOPS/W，但差距从 18.6× 缩小到约 1.9×。该折算尚未实测，下一步用 VCS SAIF + DC `read_saif` 复核。

### 4.4 流程标定（同一 DC 脚本综合环境自带的 FP16 乘法器）

为排除“流程/库配置错误”导致的面积偏差，用同一 28 nm 库和同一 DC 脚本综合用户环境中的 `floatMuilt`（16-bit 乘法器），并与该环境 2025-06-06 的历史报告对比：

| 设计 | 本次 (DC O-2018.06) | 历史报告 (DC L-2016, 2025-06-06) | 差异 |
|---|---:|---:|---:|
| `floatMuilt` 面积 | 1653.12 µm² | 1984.58 µm² | −16.7% |
| cells | 1076 | 1119 | −3.8% |

两者同量级，说明流程和库读数正常；INT8 MAC 的 1281.67 µm² 不是流程异常放大的结果。历史报告见 `results/calib_floatMuilt/` 的对比记录（原始文件在用户环境的 `zonghe_am3_ex/area/2025_0606_0222_floatMuilt_area.txt`）。

### 4.5 为什么面积和默认功耗差距这么大（定量拆解）

**面积（4.6×）主要不是“逻辑多”，而是“单元大”**：

- 本实现 767 cells/MAC，平均 cell 面积 1.671 µm²；其中 buffer/inverter 平均 3.737 µm²、DFF 平均 4.147 µm²。
- OzCore 阵列 4.35 mm² / 16384 = 265.4 µm²/MAC。如果论文实现的 cell 数与本文同量级（767/MAC，对 8×8 乘法器 + 32-bit 累加器是合理量级），其平均 cell 仅 0.346 µm²/MAC，约为本文的 1/4.8。
- 也就是说，**4.6× 面积差基本可以由标准单元库密度解释**：SMIC 28 nm HPC（hpk）是偏高性能的大单元库；论文的 28 nm 库/单元即使 cell 数相近，平均面积也可能小 4–5×。本文没有论文的库，无法直接归一。
- 次要因素：每 lane 独立的 clock/reset/valid/clear 缓冲占 38–42% 面积（buf/inv 541.8 µm²/MAC）；论文的 HLS 阵列共享控制，128×128 时这部分会被摊薄。本文的 128×128 是 4-lane 线性外推，没有计共享控制，偏保守。

**默认功耗（18.6×）≈ 面积（4.6×）× 活动率/功耗密度（约 4×）**：

- 本实现 0.585 mW/MAC @300 MHz = 1.95 pJ/MAC（默认活动率）；论文 0.47 W / (16384 × 300 MHz) ≈ 0.096 pJ/MAC（真实 INT8 workload）。
- 18.6 / 4.6 ≈ 4，剩下的约 4× 来自：DC 默认活动率不是 LLM 真实活动率、HPC 库的动态/漏电功耗密度更高、以及每 lane 缓冲在所有周期都翻转。
- 本文尝试用 VCS SAIF 标注，但 SAIF 的 duration/timescale 在 DC 侧被拒绝（SAIF-9），尚未得到可信的活动率；下一步修 SAIF 后再报“真实活动率”下的 pJ/MAC。按活动率低 4–10× 估算，功耗比预计降到约 2–4×。

**P0b 已定量验证**：把同一份 RTL 换到用户环境的 TSMC 28 nm HPC+ FF 库后，面积从 1281.67 µm² 降到 **378.13 µm²**（1/3.39），与 OzCore 的 265.4 µm²/MAC 只差 **1.42×**；默认功耗从 585 µW 降到 **109.9 µW**（1/5.3），每 MAC 能量 0.366 pJ，与 OzCore 的 0.0956 pJ 差 3.83×。详见 `results/P0B_REPORT.md`。

**结论**：4.6×/18.6× 是“大单元库 + 每 lane 缓冲 + 默认活动率”的工程差距，不是 4.6× 的逻辑规模差，也不是 18.6× 的算法效率差。P0b 的换库实验已经证实库密度是第一主因；绝对复现还需要论文同款库或一版共享控制/优化 MAC。相对比较应使用同一库/同一 RTL 风格/同一活动率口径（P0b 起统一用 TSMC 28 HPC+ FF、3.5 ns）。

## 5. Ozaki-II pass 数模型

`model/ozaki2_int8.py` 是一个**简化**的 Ozaki-II / CRT 模型：全局 2 的幂缩放、接近 2⁸ 的两两互素模数、任意精度整数 CRT、随机 FP64 矩阵（32×32，φ=1.0，3 seeds）。结果（`results/pass_count.csv`）：

| s | P bits | bA/bB | 相对 L2（mean ± std） | BF16 (≤1e-2) | FP32 (≤1e-6) |
|---:|---:|---|---:|---|---|
| 1 | 8.0 | 0/1 | 1.00e+00 | no | no |
| 2 | 15.9 | 3/4 | 5.27e-01 | no | no |
| 3 | 23.8 | 7/8 | 4.08e-02 | no | no |
| 4 | 31.6 | 11/12 | **2.50e-03** | **yes** | no |
| 5 | 39.5 | 15/16 | 1.56e-04 | yes | no |
| 6 | 47.3 | 19/20 | 9.83e-06 | yes | no |
| 7 | 55.1 | 23/24 | **5.92e-07** | yes | **yes** |
| 8 | 62.8 | 27/28 | 5.09e-08 | yes | yes |
| 9 | 70.5 | 31/32 | 3.07e-09 | yes | yes |
| 10 | 78.1 | 35/36 | 1.92e-10 | yes | yes |
| 11 | 85.7 | 39/40 | 1.96e-11 | yes | yes |
| 12 | 93.3 | 43/44 | 1.15e-12 | yes | yes |

- 本模型给出 BF16 等价 **s=4**、FP32 等价 **s=7**；OzCore 论文的紧致缩放给出 s=3（BF16），说明本模型偏保守。报告以“本模型值”和“论文值”并列，不混用。
- 若用本基线的 9.83 TOPS 峰值，等精度有效吞吐为：s=4 → 2.46 TOPS；s=7 → 1.40 TOPS。
- 对应的等精度 AEE（按默认活动率、外推 128×128）：s=4 约 **14.2 GOP/(s·mm²·W)**；s=7 约 **8.1**。这些数值只用于流程演示，不能与论文的 28 nm 实现直接比。

## 6. 与 OzCore 的差距分析

| 指标 | 本基线（外推 128×128） | OzCore 论文 | 比值 |
|---|---:|---:|---:|
| INT8 阵列面积 | 19.85 mm² | 4.35 mm² | 4.57× |
| 单阵列功耗 | 8.74 W（默认活动率） | 0.47 W | 18.6× |
| TOPS/W | 1.13 | 20.9 | 1/18.6 |
| 每 MAC 面积 | 1211.8 µm² | 265.6 µm² | 4.56× |

可能原因，按影响排序：

1. **实现风格**：OzCore 用 Catapult HLS 做面向阵列的优化，共享控制/缓冲；本基线是逐 lane 通用 RTL，buf/inv 面积占 38–42%，且未做 Booth/Wallace/CLA 优化。
2. **标准单元库**：本环境是 SMIC 28 nm HPC RVT（偏高性能、面积大）；论文的 28 nm 库/单元面积可能更紧凑。没有论文的库无法直接归一。
3. **活动率口径**：默认活动率使功耗偏高约一个数量级；需 SAIF 复核。
4. **累加器结构**：55 级逻辑的 32-bit 累加链在 300 MHz 刚好收敛，面积和功耗都不最优。
5. **阵列外推**：128×128 是按 4-lane 线性外推，未包含真实阵列的共享控制/布线；可能高估也可能低估。

**结论**：本基线不能用于“绝对复现 OzCore”，但可以作为**同流程、同库、同活动率口径**下的相对比较基线。后续 FP8/FP4 必须用同一 RTL 风格和同一 DC 脚本；若最终需要绝对数值，应先做一版共享控制/优化 MAC 的 P0b。

## 7. 下一步

1. **P0b（建议优先）**：优化 MAC/阵列——共享 valid/clear/clock 缓冲、累加器 CLA/分段流水、乘法器 Booth/Wallace；目标把 per-MAC 面积降到 ~400–500 µm²，接近论文量级。
2. **功耗复核**：VCS 随机 workload → SAIF → DC `read_saif` → `report_power`；给出 50%/100% 利用率下的 pJ/MAC。
3. **P1 FP8 E4M3**：同一模板实现 FP8 乘法 + FP32 累加，DC 面积/功耗；用同一 pass 数模型估计 FP8 的模数/3-GEMM 开销。
4. **P2 FP4 E2M1**：base-13 limb 的 MAC + 编解码；同样口径。
5. **精度模型**：把全局缩放换成 per-row/per-column 缩放，向 OzCore 的 s=3 靠拢；加 LLM/GEMM 工作负载。

## 8. 复现

### 8.1 主机侧文件

```
experiments/p0-int8-baseline/
├── rtl/int8_mac.sv, int8_array.sv, int8_array_n4.v, tb_int8_mac.v
├── synth/run_dc.tcl, run_dc_array4.tcl, synopsys.sdc
├── model/ozaki2_int8.py
└── results/
    ├── dc_int8_mac/{area,timing,power,qor,constraints}.txt, netlist.v
    ├── dc_int8_array_n4/{...}
    ├── pass_count.csv, metrics.csv, P0_REPORT.md
```

### 8.2 VM 侧命令

```bash
# 进入 EDA VM 后
cd /home/host/p0_int8
dc_shell -f run_dc.tcl -output_log_file dc.log            # 单 MAC
dc_shell -f run_dc_array4.tcl -output_log_file dc_array4.log  # 4 lane
vcs -full64 -sverilog tb_int8_mac.v rtl/int8_mac.v -o simv && ./simv
```

### 8.3 主机侧模型

```bash
cd experiments/p0-int8-baseline
python3 model/ozaki2_int8.py --out results/pass_count.csv
```

## 9. 限制

- 依赖用户的 EDA VM（DC/VCS + SMIC 28 nm 库）；仓库不包含商业库。
- 功耗为默认活动率，未做 SAIF/VCD 标注；数值只能作相对参考。
- 128×128 为线性外推，不是完整阵列综合。
- Ozaki-II 模型是简化版（全局缩放、随机矩阵），pass 数偏保守；不是 OzCore 的逐位复刻。
- 仅完成 INT8；FP8/FP4 尚未实现。
