# OzCore HLS → 可综合 RTL 移植评估与分阶段计划

> 目标：基于 artifact 的 Catapult HLS C++ 源码，将 OzCore 各 stage 重写为可综合 RTL，并做功能等价验证。
> 结论：**这不是一个单次可交付的局部改动**；需要先冻结接口/参数并确定验证基线。当前环境没有 Catapult HLS，artifact 也不提供 OzCore 的 RTL。

## 1. 源码盘点

路径：`reproduction/ozcore/ozcore-artifact/src/hw/synth/hls/`

| 目录 | 非 testbench 行数 | 内容 |
|---|---:|---|
| `common/` | 358 | 全局参数、Ozaki 表 |
| `modulo/` | 161 | 模运算/基变换头文件 |
| `preprocess/` | 1,025 | scaler、压缩、取模、shift、pack |
| `simd_engine/` | 3,293 | INT8/FP16/FP8/FPBF/FP4/FP64 ALU 六类 dot-product 引擎 |
| `postprocess/` | 722 | CRT/模归约、int→FP、输出 |
| `top/` | 368 | top_parallel、path chooser、output selector/aligner |
| **合计（非 tb）** | **5,927** | 另有 testbench 570 行 |

- 63 个文件；模板参数 `K`、`N`、`S_MAX=12`；`ac_int`/`ac_fixed`/`ac_std_float`/`ac_channel`；`mc_scverify`。
- `top_parallel` 例化 1 个 preprocess、N 个 SIMD engine、N 个 postprocess、N 个 path chooser/selector、1 个 output aligner；SIMD engine 内部还按模式选择 INT8/FP16/FP8/FP4/FP64 ALU 变体。
- artifact 只 vendored Ten-four 的开源 RTL；OzCore stages 没有 RTL，只有 HLS C++ 与 Catapult TCL。

## 2. 为什么不能直接“一次性全量重写”

1. **接口/协议重构**：`ac_channel` 的阻塞/非阻塞语义、package struct、K/N/S_MAX 模板参数、N 路并行与 S_MAX 个 slot 必须在 RTL 中重新定义；这不是替换一个函数，而是重划模块边界与握手。
2. **六类 SIMD 变体**：INT8、FP16、FP8、FP4、FPBF、FP64 ALU 的位宽/指数/舍入/特殊值语义不同；全变体都要等价，工作量和验证矩阵都很大。
3. **位精确的数值语义**：scaling/取模/CRT/宽整数累加/int→FP 舍入必须逐位一致；没有统一黄金模型，无法“保证功能正确性”。
4. **缺少验证基线**：HLS testbench 依赖 `ac_channel`/`mc_scverify`；RTL 需要重写 testbench 或生成 C++/Python 黄金向量。没有 Catapult SCVerify，等价性验证要自建。
5. **缺少工具**：artifact 的流程是 Catapult HLS → RTL → DC；当前 EDA VM 没有 Catapult，只有 DC + TSMC 28 nm HPC+。手工重写无法复用 Catapult 的位精确语义与验证环境。

## 3. 建议的分阶段方案

### Stage 0：接口冻结（必须先做）

- 选定一个 **缩减配置**：如 `K=4/8`、`N=4`、`S_MAX=12`、INT8 路径优先；明确 top 端口、package 字段、clock/reset、channel valid/ready、tile 边界。
- 从 `tb_top_parallel.cpp` 提取激励/输出序列，定义 RTL testbench 的帧格式。
- 输出《RTL 接口规范 v0.1》与《黄金模型说明》。

### Stage 1：preprocess RTL

- `scaler_compressing_see_mantissa_v2`、`base_shift_mod_vec`、shift/pack。
- 验证：Python/C++ 黄金模型逐元素对比；随机 + 边界（次正规/溢出/零/符号）；综合 TSMC 28 nm 面积/CP。

### Stage 2：SIMD engine RTL（先 INT8）

- `simd_engine_fdot_tree_int8` 的 dot-product tree、累加、lane mask。
- 验证：与 HLS C++ 的 INT8 引擎逐周期/逐输出对比；再用 `simd_engine_parallel` 的 N 路/模式选择扩展。

### Stage 3：postprocess RTL

- CRT 模归约/加权/宽整数累加；`int_fp_change` 的 int→FP 舍入。
- 验证：MPFR/黄金模型；边界指数/舍入模式；与 preprocess/SIMD 联调。

### Stage 4：top/path/aligner 集成

- `top_parallel` 的 N 路流水、path chooser、output selector/aligner；channel 握手；S_MAX slot 调度。
- 验证：复用 `tb_top_parallel.cpp` 的激励序列；端到端 bit-exact；综合。

### Stage 5：其余变体与系统

- FP16/FP8/FP4/FPBF/FP64 ALU；Catapult/DC 面积对比；Chipyard/FireSim 接入。

## 4. 验收标准（建议）

- **功能**：Stage 1–4 的 RTL 与 HLS C++ 黄金模型在随机/边界/对抗向量上逐位一致；top 级端到端一致。
- **时序/面积**：TSMC 28 nm HPC+ DC 综合，报告 area/CP；与 HLS 结果对比，标注库/flow 差异。
- **覆盖**：INT8 主路径优先；其余变体在 Stage 5 增量验证，不能把“INT8 通过”当成“全部通过”。

## 5. 当前进展（2026-11-26）

已完成 Stage 2 的 **INT8 SIMD core 第一版 RTL**（缩减配置 K=8、S_MAX=12，96 个 INT8 乘法器）：

- 功能：VCS 123/123 向量通过（零、±127/-128、随机；Python 黄金模型逐位对比）。
- 综合：TSMC 28nm HPC+ FF、DC O-2018.06，**19,301.18 µm²**，19,934 cells，纯组合。
- 位置：`experiments/ozcore-rtl/simd_int8/`。
- 范围限制：不是完整 `simd_engine_parallel`（无 N 路并行/权重寄存器/通道握手/psum buffer）；不含 FP16/FP8/FP4/FPBF/FP64 变体；无时钟约束，只有面积；与 artifact 52.147 mm² 的 SIMD stage 不可直接比较。
- 下一步：补 wrapper/权重寄存器/通道握手，再按同一方法做 preprocess、postprocess、top；每步都需要 HLS/C++ 或 Python 黄金模型 + VCS/Verilator 等价验证。

## 5.1 K=128 SIMD 里程碑（2026-11-26）

- `experiments/ozcore-rtl/simd_int8_k128/`：K=128、S_MAX=12、1536 个 INT8 乘法器。
- 功能：VCS 20/20 向量通过（零、±127/−128、随机）。
- 综合：TSMC 28nm HPC+、DC O-2018.06，**334,190.30 µm² / 349,011 cells**，纯组合；无时钟约束。
- 128 engine 的**缩放估计**为 334,190.30×128≈42.78 mm²，artifact SIMD stage 52.147 mm²；差值是阵列布线/psum/权重/通道/参数化，不能当作 128×128 实测。
- 规格已就绪：`docs/ozcore-rtl/preprocess-spec.md`、`docs/ozcore-rtl/postprocess-control-spec.md`。

**已发现的 artifact HLS 功能问题**（RTL 默认按“修正语义”实现，另设 `BITEXACT` 参数用于 bug-for-bug 对比）：

1. postprocess 的 denormalization shift 用 `shift[2*si+1]`，但 preprocess 在 lane `i*s..i*s+s-1` 复制 chunk 的 shift；仅 s=2/12 正确，s=3/4/6 会取错指数。
2. int2fp 的 24-bit normal rounding 加法丢 carry（0xFFFFFF800000,d=0 → 2^47 而非 2^48）；23-bit subnormal 加法也丢 carry（0xFFFFFF,d=150 → 0 而非 2^-126）；无 sticky。
3. `s` 在 preprocess 是 3 bit（s=12 截断为 4），postprocess 是 4 bit；必须统一为 4 bit。
4. 随附 TB 基本不检查：postprocess 用独立随机 lane（非 CRT 一致），active_outputs 也错；top TB 是 print-only 且 s=12 实际跑成 s=4。SCVerify 只能证明“RTL==HLS”，不能证明 HLS 正确；必须用独立 golden model。

## 6. 预计工期（缩减 INT8 全加速器）

以“K=8、N=4、S_MAX=12、INT8 主路径、单个 OzCore 实例”为目标，按当前已验证的 RTL/VCS/DC 流程估算（工作日，非承诺）：

| 阶段 | 内容 | 预计 |
|---|---|---:|
| SIMD wrapper | 权重寄存器、channel/valid-ready、psum、N 路 | 3–5 天 |
| preprocess | scaler、取模、shift/pack、接口 | 8–12 天 |
| postprocess | CRT/模归约、int→FP、舍入 | 8–12 天 |
| top 集成 | top_parallel、path chooser、output aligner、联调 | 8–12 天 |
| 回归/综合 | 黄金模型回归、DC/TSMC 面积/CP | 3–5 天 |
| **合计** | 缩减 INT8 单个实例 | **约 4–8 周** |

- 全参数、六类 SIMD 变体（FP16/FP8/FP4/FPBF/FP64）另计，约 **3–6 个月**。
- 若提供 Catapult 许可：生成 RTL + SCVerify + DC 面积，约 **1–2 周**。
- 若只接受“sanitized/缩放估算”：现在即可给 72.3 mm²（artifact 重绘）或 76.0 mm²（×1.051 粗略缩放），但都不是独立综合。
- 已有的缩减 SIMD core 面积：**19,301.18 µm²**（96 MAC，纯组合）；不是单个 OzCore 总面积。

## 7. 当前需要的决策/资源

**A. 提供 Catapult HLS 许可/路径**：可直接用 Catapult 生成 RTL + SCVerify，再跑 DC/TSMC；这是最快且最可靠的路径。

**B. 授权缩减范围的分阶段手工 RTL**：先做 `K=4/8, N=4, S_MAX=12, INT8` 的 preprocess→SIMD→postprocess→top，交付 RTL + Verilator 对黄金模型的等价报告；其余变体后续增量。

**C. 只做接口/计划**：先冻结规范，不写全量 RTL。

在没有 A 或 B 的明确边界前，直接开始“全参数、全变体”的手工重写无法保证功能正确性，也不符合单次可交付的范围。
