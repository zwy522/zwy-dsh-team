# 单一格式执行部件的面积–能耗效率分析报告

> 日期：2026-11-05
> 范围：OzCore 式“单一计算基座 + 多格式统一执行”的第一步——在 INT8 / FP8 E4M3 / FP4 E2M1 三种基座格式中，按 Ozaki-II 及其 FP8/FP4 变体，比较相同目标精度下的面积–能耗效率。
> 数据来源：本仓库 `experiments/` 下的 RTL、DC 报告、数值模型；论文见文末参考文献。

## 0. 结论摘要

1. **INT8 是等精度面积–能耗最优的基座格式**。在 BF16、FP16、FP32、FP64 四个目标精度下，INT8 的归一化成本都是 1.000；FP8 为 3.17–4.23×，FP4 为 1.96–2.36×。
2. FP8/FP4 的劣势不是“每个 MAC 更贵”——FP4 的 per-MAC 面积×能量只有 INT8 的 0.795×，FP8 为 1.409×——而是**达到同一精度所需的低精度 GEMM 次数更多**：FP8 每个模数要 3 次 GEMM；FP4 base-13 分解在 FP64 下需要 19 模数 / 75 次 GEMM。
3. FP4 只有在 per-MAC 面积×能量低于约 **0.405× INT8**（或吞吐优势 >2×）时，才可能在 FP32 等精度下反超；本次实测为 0.795×，不够。
4. 因此，**统一 INT8 阵列 + 数值分解**（OzCore 路线）比给 FP8/FP4 各做一套原生数据通路更面积–能耗高效。FP8/FP4 作为被支持格式，通过分解/合并实现。
5. 证据链：Ozaki-II 算法的 pass 数（位预算 + FP8/FP4 数值仿真） + TSMC 28 nm HPC+ FF 下三种 MAC 的 DC 实测面积/能耗 + 等精度成本模型。

## 1. 问题与评价口径

### 1.1 问题

同一个 Ozaki-II 分解框架，分别以 INT8、FP8 E4M3、FP4 E2M1 作为基座计算格式，在**相同目标精度**（归一化到 BF16/FP16/FP32/FP64）下，哪一种基座的面积–能耗效率最高？

“相同算力”在本报告中定义为**达到同一目标 GEMM 精度所需的低精度 GEMM 次数**，而不是峰值 TOPS。这样比较的是“有效计算量”，避免低精度格式因单次运算便宜而天然占优。

### 1.2 成本模型

对每个格式/目标精度：

```
Q_eff  = 低精度 GEMM 次数 / 格式吞吐倍数
cost   = Q_eff × A_MAC × E_MAC          (越小越好)
AEE    = 1 / cost                       (归一化到 INT8)
```

- `A_MAC`：单 MAC 面积（µm²），DC 综合、标准单元面积；
- `E_MAC`：单 MAC 能量（pJ），默认活动率；
- `Q_eff`：达到目标精度所需的有效 GEMM 次数；FP4 按 2× 吞吐折算，INT8/FP8 按 1×；
- 目标精度用尾数位数 `B` 表示：BF16=8、FP16=11、FP32=24、FP64=53；
- CRT 乘积位预算：`R = 2B + g`，`g = ceil(log2 K) + 2`，K=128 → `g=9`。

## 2. 算法：各格式的 pass 数

### 2.1 按论文结构的位预算

| 格式 | 每模数位数 | GEMM/模数 | 说明 |
|---|---:|---:|---|
| INT8 | 8 | 1 | 模数接近 2^8；OzCore/Ozaki-II CRT |
| FP8 E4M3 | 9 | 3 | p≤513；Uchino et al. 的 FP8 Ozaki-II（Karatsuba/拆分） |
| FP4 E2M1 | 6.05 | 3.95 | base-13；FP64 下 19 模数 / 75 次 FP4 GEMM（Hayashi et al.） |

`N = ceil(R / 每模数位数)`，`Q = N × GEMM/模数`。FP4 的 6.05 bit/模数、3.95 GEMM/模数由论文 FP64 配置（19 模数、75 GEMM）反推。

### 2.2 结果

| 目标 | R | INT8 模数 / GEMM（有效） | FP8 模数 / GEMM | FP4 模数 / GEMM（有效） |
|---|---:|---:|---:|---:|
| BF16 (B=8) | 25 | 4 / 4 | 3 / **9** | 5 / 19.8 → **9.9** |
| FP16 (B=11) | 31 | 4 / 4 | 4 / **12** | 6 / 23.7 → **11.9** |
| FP32 (B=24) | 57 | 8 / 8 | 7 / **18** | 10 / 39.5 → **19.8** |
| FP64 (B=53) | 115 | 15 / 15 | 13 / **39** | 19 / 75 → **37.5** |

FP8 的 FP32 值 18 来自数值仿真（N=6，3 GEMM/模数），与位预算的 21 一致且更乐观；FP64 保留论文的 39。INT8 的 FP64 取 15，比 OzCore 的 12 保守。

### 2.3 数值校验

- **FP4 base-13（Ozaki-I，`model/fp4_limb_sim.py`）**：BF16/FP16/FP32 分别需要 p=4/5/7 个 limb，2× 吞吐折合 **8/12.5/24.5** 次有效 GEMM。OzII-FP4 会更少，但模型给的 9.9/11.9/19.8 仍高于 INT8 的 4/4/8。
- **FP8 混合法（`model/fp8_hybrid_sim.py`）**：平方模数 p=s²、每模数 3 次 FP8 GEMM；BF16/FP16/FP32 需 N=3/4/6，即 **9/12/18** 次，与位预算一致。

## 3. 硬件：三种 MAC 的实测面积/能耗

### 3.1 流程

- 库/工具：TSMC 28 nm HPC+ FF（0.99 V / 0 °C），Synopsys DC O-2018.06-SP1，3.5 ns；
- INT8：P0b 的 3 级流水 MAC（8×8 乘法 + INT32 累加）；
- FP8/FP4：`fp_mac`（格式乘法 + 归一化到 FP32 + DesignWare `DW_fp_add` FP32 累加）；
- 面积：标准单元面积（不含互连/布线）；功耗：DC 默认活动率，动态 + 漏电。

### 3.2 结果

| 格式 | 面积 (µm²) | cells | 关键路径 (ns) | slack @3.5 ns | 动态 (µW) | 漏电 (µW) | 能量 (pJ/MAC) | 面积×INT8 | 能量×INT8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| INT8 | 378.13 | 365 | 1.13 | +2.26 | 109.63 | 0.256 | **0.366** | 1.000 | 1.000 |
| FP8 E4M3 | 619.42 | 927 | 2.61 | +0.80 | 94.14 | 0.385 | **0.315** | 1.638 | 0.860 |
| FP4 E2M1 | 551.25 | 846 | 2.49 | +0.91 | 59.59 | 0.341 | **0.200** | 1.458 | 0.545 |

关键观察：

- **FP8/FP4 的面积反而比 INT8 大 1.46–1.64×**：4×4/2×2 乘法器很小，但 FP32 累加器（对齐、规格化、舍入）比 INT8 的 INT32 累加器大。
- 默认活动率下 FP8/FP4 的能量比 INT8 低（0.315/0.200 vs 0.366 pJ），来自更小的乘法器/更低的活动率；这不改变面积主导的结论。
- 与 OzCore 的 265.4 µm²/MAC 相比，本 INT8 MAC 为 1.42×；差距主要来自通用 RTL + 库/实现，而不是格式本身（P0b 已做同 RTL 换库对照）。

## 4. 等精度面积–能耗比较

### 4.1 主结果

per-MAC 成本因子（面积×能量，INT8=1）：FP8 = 1.638×0.860 = **1.409**；FP4 = 1.458×0.545 = **0.795**。

| 目标 | INT8 cost (归一) | FP8 cost (归一) | FP4 cost (归一) | 最优 |
|---|---:|---:|---:|---|
| BF16 | **1.000** | 3.170 | 1.963 | INT8 |
| FP16 | **1.000** | 4.227 | 2.355 | INT8 |
| FP32 | **1.000** | 3.170 | 1.963 | INT8 |
| FP64 | **1.000** | 3.664 | 2.094 | INT8 |

对应 `AEE_norm`（INT8=1）：BF16 的 FP8/FP4 = 0.315/0.509；FP16 = 0.237/0.425；FP32 = 0.315/0.509；FP64 = 0.273/0.478。

### 4.2 解释

- INT8 每次 GEMM 的有效位最多（8 bit），且没有 FP8 的“每模数 3 GEMM”或 FP4 的 base-13 多次分解；虽然单 MAC 不是最便宜，但**有效 GEMM 数最少**。
- FP4 的单 MAC 最便宜（0.795×）且有 2× 吞吐，但 BF16/FP32 需要 9.9/19.8 次有效 GEMM，是 INT8 的约 2.5 倍；乘起来仍贵。
- FP8 单 MAC 最贵（1.409×）且 GEMM 数多，四个目标都最差。

### 4.3 敏感性

FP4 的 per-MAC 面积×能量为 `f4`；FP32 的 cost_norm ≈ `1.963 × (f4 / 0.795)`：

| f4 | FP32 cost_norm | 结论 |
|---:|---:|---|
| 0.30 | 0.741 | FP4 反超 |
| 0.405 | ≈1.000 | 临界 |
| 0.50 | 1.234 | INT8 |
| 0.795（实测） | 1.963 | INT8 |

FP4 要在 FP32 等精度下胜出，需要 `f4 < 0.405`；考虑到它仍需 FP32 累加器/对齐/规格化/重构，0.4 以下不现实。FP8 即使面积×能量降到 INT8 的 0.5×，BF16 的 cost_norm 仍约 1.5。

## 5. 结论与建议

1. **基座格式选 INT8**。在 Ozaki-II 框架下，INT8 的“少 pass + 适中 MAC 成本”组合在 BF16/FP16/FP32/FP64 上都是最优；与 OzCore 的选择一致。
2. **FP8/FP4 作为被支持格式，不做原生数据通路**。把它们纳入统一 INT8 阵列的分解/合并路径，避免为每种格式增加专用乘法器/累加器；FP8/FP4 的峰值吞吐/存储优势留给 I/O 和内存层次。
3. **下一步验证**（按优先级）：
   - FP8/FP4 MAC 的 VCS 功能仿真（DW `DW_fp_add` 仿真模型），确认面积/能耗对应的 RTL 行为正确；
   - 真实 workload（LLaMA/Qwen PPL、ResNet Top-1）在 BF16/FP16/FP32 等价下的精度–成本曲线；
   - 先进节点（7/5 nm）缩放敏感性；
   - 若论文需要“原生 FP8/FP4 vs 分解”的强对照，再补原生基线 tile 的综合。

## 6. 限制

- **功能验证缺口**：FP8/FP4 MAC 只做了 DC 综合，未做 VCS 功能仿真；DW FP32 加法器的行为、舍入/异常语义待验证。
- **功耗口径**：默认活动率，未做 SAIF/VCD 标注；能量数值只能作相对比较，不能当真实 workload 的绝对能耗。
- **算法模型**：CRT 位预算 + 两个数值仿真（FP4 OzI、FP8 平方模数混合法）；未逐步复现论文的全部 scaling/误差界，FP64 的 INT8 s=15 比 OzCore 的 12 保守。
- **工艺/边界**：TSMC 28 nm HPC+ FF、标准单元面积、无互连/布线；128×128 阵列未整体综合。
- **未做真实 PPL/Top-1**：目标精度是尾数位数，不是任务精度。

## 7. 复现与数据

| 内容 | 路径 |
|---|---|
| P0 INT8（SMIC） | `experiments/p0-int8-baseline/results/P0_REPORT.md` |
| P0b 换库（TSMC） | `experiments/p0-int8-baseline/results/P0B_REPORT.md` |
| Ozaki-II 等精度模型 | `experiments/ozaki-format-comparison/` |
| FP8/FP4 MAC 综合 | `experiments/fp8-fp4-mac/` |
| 本报告 | `docs/analysis-report-single-format-executor.md` |

## 参考文献

1. J. Park et al., “OzCore: An Ozaki-Scheme-II-Based GEMM Architecture for Unified Integer and Floating-Point Computation,” MICRO 2026.
2. K. Ozaki, Y. Uchino, T. Imamura, “Ozaki Scheme II: A GEMM-oriented emulation of floating-point matrix multiplication using an integer modular technique,” arXiv:2504.08009, 2026.
3. Y. Uchino, K. Ozaki, T. Imamura, “Double-Precision Matrix Multiplication Emulation via Ozaki-II Scheme with FP8 Quantization,” arXiv:2603.10634, 2026.
4. S. Hayashi, D. Mukunoki, T. Hoshino, T. Katagiri, “DGEMM with Ozaki Scheme I/II on FP4 Tensor Cores: A Base-13 E2M1 Limb Representation,” arXiv:2608.06812, 2026.
5. P. Micikevicius et al., “FP8 Formats for Deep Learning,” arXiv:2209.05433, 2022.
6. M. Horowitz, “Computing's Energy Problem (and What We Can Do About It),” ISSCC 2014.
