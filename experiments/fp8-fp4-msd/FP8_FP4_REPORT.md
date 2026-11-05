# FP8/FP4 阶段：MSD-Core 多格式模式的面积–能耗分析

> 日期：2026-11-05
> 来源数据：用户环境 `/home/host/03_ASIC综合/dc-package/results/实验结果总结.md`（v2.0，2026-10-07）、`results_baseline_compare.md`、`results/saif/` 与 TSMC 28 nm HPC+ FF 的 DC 报告。
> 本阶段的定位：在用户已有的 MSD-Core（一个 INT8 计算阵列 + 格式分解/合并）上，补齐 FP8/FP4 模式的对比口径，回答“哪种单一格式执行部件最适合做统一基座”。

## 1. 结论

1. MSD-Core v2.0 在 TSMC 28 nm HPC+ FF、3.5 ns 下面积 **615,262.15 µm²**，MSD 峰值 **2048 MAC/cycle**（1.1703 TOPS @285.71 MHz），折合 **300.4 µm²/MAC**。与 OzCore 的 265.4 µm²/MAC 只差 1.13×，说明“一个 INT8 阵列 + 格式分解”的路线在面积上已经接近 OzCore。
2. 在**单一物理阵列**上，FP8/FP4 不是独立的数据通路：它们通过 `msd_decomp_engine` 的块对齐定点分解和 `scale_merge_unit` 的重构来支持，**不增加阵列面积**。因此“选哪个格式作为基座”在面积上等价于“选哪个格式做分解的公共原语”；INT8 是唯一被三种模式共同复用的基座。
3. 物理上界口径（引脚电容 × 频率）给出的能效下界：MSD 各模式（INT8/MXFP4/FP4/FP8）统一为 **≥3.817 TOPS/W**（v2.0；对应每 op 能量上界 0.262 pJ），Native 模式 **≥1.908 TOPS/W**。这里 FP8/FP4 与 INT8 共享同一个下界，因为面积和引脚电容由阵列/分解/合并决定，而不是由格式乘法器决定。
4. 相同测试窗口下的动态功耗（口径 B，含 decomp/sa_tile/merge）：INT8 8.636 mW、MXFP4 6.248 mW、FP4 4.313 mW、FP8 4.840 mW；但各窗口的激励占空比不同，**不能直接据此给格式排序**。可靠的排序是“统一阵列 + 分解”路线相对三个格式专用基线 tile 的优势：MSD `sa_tile` 上界能效 4.97 TOPS/W，而 fp16/w4a16/w4a4 基线分别只有 0.76/0.68/0.72 TOPS/W（5–7× 差）。
5. 因此，本阶段支持 **INT8 作为唯一基座格式**：FP8/FP4 作为被支持格式，由分解/合并逻辑实现；为 FP8/FP4 各做一套原生数据通路没有面积–能耗优势。这个结论与 OzCore 的“single INT8 fabric + numerical decomposition”一致。

## 2. 数据与口径

### 2.1 面积与吞吐

| 项 | 值 | 来源 |
|---|---:|---|
| MSD-Core v2.0 总面积 | 615,262.15 µm² | 总结 §5.2 |
| MSD 峰值 | 2048 MAC/cycle = 4096 ops/cycle | 总结 §2.5 |
| 时钟 | 3.5 ns（285.71 MHz） | 总结 §5 |
| 峰值吞吐 | 1.1703 TOPS | 2048 × 2 × 285.71 MHz |
| 面积 / MAC | 300.4 µm² | 615,262 / (2048) |
| 面积密度 | 1.902 TOPS/mm² | 1.1703 / 0.615262 |

### 2.2 能效下界（可引用，口径 B）

v2.0 的全芯片引脚电容 ΣC_pin = 1,094.8 pF；在 0.99 V、285.71 MHz 下，即使每个输入引脚每周期翻转一次，开关功耗 ≤ **306.6 mW**；加漏电约 0.48 mW，整机 ≤307.1 mW。于是：

- MSD 模式（INT8/MXFP4/FP4/FP8 共用同一阵列与分解逻辑）：**≥3.817 TOPS/W**，每 op 能量 **≤0.262 pJ**。
- Native 模式（1024 MAC/cycle）：**≥1.908 TOPS/W**。
- 这是**与测试激励无关**的下界，适合写论文；绝对功耗的 DC 值（数 W 级）已由总结 §2.4 证明是时钟网络建模伪影，不可引用。

### 2.3 格式模式的分部件动态功耗（口径 B，窗口相关）

数据取自总结 §2.4（9 个 SAIF 窗口；dyn 为 decomp_engine + sa_tile + scale_merge + control 的合计）：

| 模式 | decomp (mW) | sa_tile (mW) | merge (mW) | 合计 dyn (mW) | 备注 |
|---|---:|---:|---:|---:|---|
| `power_msd_int8` | 5.109 | 0.669 | 2.858 | **8.636** | INT8 分解/合并 |
| `power_msd_mxfp4` | 5.288 | 0.675 | 0.285 | **6.248** | MXFP4 权重 |
| `power_msd_fp4` | 3.592 | 0.469 | 0.252 | **4.313** | FP4 模式 |
| `power_msd_fp4_true` | 0.013 | 0.044 | 0.023 | **0.080** | 低占空比窗口 |
| `power_msd_fp8` | 3.777 | 0.602 | 0.460 | **4.840** | FP8 模式 |
| `power_msd_fp8_true_e4m3` | 1.400 | 0.044 | 1.110 | **2.554** | E4M3 真输入 |
| `power_msd_fp8_true_e5m2` | 1.432 | 0.052 | 1.298 | **2.782** | E5M2 真输入 |
| `power_native` | 0.007 | 0.464 | 0.022 | **0.493** | 1024 MAC/cycle，无分解 |

> ⚠️ 这些窗口的激励占空比不同（`tb_power_dump` 每窗口只做少量 MAC 与配置），所以**不能**用 4.313 vs 8.636 直接说 FP4 比 INT8 省电。它们只用于定位功耗热点：`decomp_engine` 在 MSD 模式占 59–85%，`sa_tile` 因权重驻留只占 8–11%。

### 2.4 与格式专用基线 tile 的对比

`results_baseline_compare.md` 用同一 TSMC 28 nm HPC+ FF、3.5 ns、同 256 MAC/cycle 吞吐综合三个格式专用 tile：

| 设计 | 面积 µm² | 功耗上界 mW | 能效下界 TOPS/W | 面积密度 TOPS/mm² |
|---|---:|---:|---:|---:|
| `fp16_tile` (W16A16) | 309,669 | 192.3 | 0.76 | 0.472 |
| `w4a16_tile` | 348,872 | 216.4 | 0.68 | 0.419 |
| `w4a4_tile` | 331,317 | 204.4 | 0.72 | 0.441 |
| MSD `sa_tile` | 58,932 | 29.4 | **4.97** | **2.48** |

即使只比较单个 16×16 tile，MSD 的 INT8 阵列 + 分解路线也比三个格式专用 tile 好 5–7× 能效、4–5× 面积密度。FP8/FP4 的专用 tile 尚未综合；从统一阵列的复用关系看，没有理由认为新增一套 FP8/FP4 乘法器会比共享 INT8 阵列更优。

## 3. 对原问题的回答

“哪一种单一计算执行部件的面积–能耗效率最高？”

- **INT8**：作为唯一基座，面积 300.4 µm²/MAC（MSD v2.0，TSMC 28 nm），能效下界 3.817 TOPS/W；FP8/FP4 通过分解复用同一阵列，不增加面积。
- **FP8 / FP4 原生数据通路**：在现有证据下没有优势；它们需要新增指数/对齐/规格化/舍入或专用 FP4 乘法器，而分解路线已经能在同一 INT8 阵列上支持这些格式。若要做原生对照，需要另建 FP8/FP4 tile 并重新综合，这是后续工作，不是本阶段结论。
- **统一性**：MSD-Core 的 300.4 µm²/MAC 已接近 OzCore 的 265.4 µm²/MAC（1.13×），说明 INT8 基座 + 格式分解是面积–能耗效率最高的路线。

## 4. 限制与下一步

- 口径 B 的窗口功耗受测试激励占空比限制；绝对功耗不可引用，只有能效下界可引用（总结 §2.4）。
- MSD-Core 的 FP8/FP4 是**块对齐分解**，不是逐元素 IEEE FP8/FP4；与原生 FP8/FP4 的精度语义不同，比较时应注明。
- 未做 FP8/FP4 专用 tile 的综合；若论文需要“原生 vs 分解”的强对照，下一步应实现并综合 `fp8_tile`/`fp4_tile`。
- 本阶段只做分析，没有改 RTL；MSD-Core v2.0 的 RTL/综合结果在用户环境中保留。

## 5. 复现

```bash
# 用户 EDA VM
cd /home/host/03_ASIC综合/dc-package/cwd_v20
SAIF_NET_DIR=.../results_clk3p5_v20/netlist \
SAIF_RPT_DIR=.../results_clk3p5_v20/reports_power \
SAIF_CLK_PERIOD=3.5 \
SAIF_ONE=.../results/saif/power_msd_fp8.saif \
dc_shell -f ../scripts/power_saif_ff.tcl
```

FP8/FP4 的 DC 全芯片报告已生成（`results_clk3p5_v20/reports_power/power_saif_power_msd_fp{8,4}_ff.rpt`），但其绝对值同样是时钟网络建模伪影（见总结 §2.4），本报告只使用口径 B。
