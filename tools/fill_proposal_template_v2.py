# -*- coding: utf-8 -*-
"""Fill the graduate proposal template with the improved Ozaki-OGE draft (v2)."""
import sys, os
sys.path.insert(0, "tools")
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from fill_proposal_template import _set_para_mark, _set_cell_margins

TEMPLATE = "literature_docs/开题报告模板.docx"
OUT_DOCX = "docs/proposal/开题报告-初稿-模板版.docx"
OUT_MD = "docs/proposal/开题报告-初稿-模板版.md"
FIG = "docs/proposal/figures"

TITLE = "面向多精度统一执行的 Ozaki 模拟 GEMM 加速器关键技术研究"

SEC1 = [
"1.1 课题来源",
"本课题为自选课题，依托导师课题组在多精度计算与体系结构方向的研究基础。课题来源/资助信息：________（如国家自然科学基金、国家重点研发计划、实验室开放基金等，待补充）。",
"1.2 选题依据",
"大模型与科学计算对矩阵乘（GEMM）的精度需求正在同时向两端扩张：一端是 FP64/FP32 的科学计算与训练梯度，另一端是 FP16/BF16/FP8/FP4/INT8 的推理与低精度训练。GPU 厂商把面积与功耗持续投向低精度，公开规格中 INT8 与 FP64 的峰值比已达到 10²–10³ 量级；而 HPC 与科学计算仍依赖 FP64，二者形成结构性矛盾。传统数据通路融合在一个 MAC 中复用多格式，每增加一种格式就增加一份大多数时间空闲的硬件，持续稀释单位面积算力。",
"Ozaki Scheme II 给出了另一条路线：把高精度浮点矩阵按行/列共享指数缩放为整数，对一组两两互素的模数取余，在低精度整数阵列上做精确 GEMM，再用中国剩余定理（CRT）重构。其关键性质是中间乘积精确、误差可分析、GEMM 次数随模数个数线性增长。OzCore（MICRO 2026）把该方案做成整数化的 GEMM 架构，在 INT8 阵列上仅增加 27.9% 前/后处理面积，就在 LLaMA-3.1 上匹配 BF16 困惑度，并相对融合多格式基线取得 1.91× TOPS/mm² 与 1.40× TOPS/W。",
"但 OzCore 留下三个工程问题。其一，小/中矩阵（K=1024–4096）的非 GEMM 开销占 27–55%：分解、取模、CRT 重构无法被 GEMM 充分摊薄，K 从 8192 降到 1024 时开销占比约升 8 倍。其二，精度由分解次数 s 隐式决定：应用只能选 s，不能声明“正确舍入/≤2 ulp/容差 ε”，也拿不到最坏情况保证与逐层误差统计。其三，N 倍余数平面带来存储/带宽压力，且缺少“同面积原生 FP64/FP32”的公平对照与 CPU+加速器的可运行系统验证。",
"1.3 研究意义",
"本课题以 OzCore 为直接基线，提出 OGE（Ozaki GEMM Engine）：在 INT8-only 主阵列上，向前融合尺度不变缩放与指数感知取模，向后融合宽整数 CRT 重构与正确舍入；用“精度合同 + 硬件守卫”把精度变成可调度、可验证的资源；以小矩阵非 GEMM 开销压缩为核心，把 K=1024–4096 的困难区间压到 <10%；用同面积 a64/a32 包络与 Chipyard/FireSim/U250 系统验证回答“统一引擎在什么条件下真正占优”。",
"预期价值：学术上，给出“精度虚拟化”的体系结构抽象、可证明的精度合同、小矩阵融合数据流与同面积评估方法，弥补现有工作“只报峰值、只对融合基线、缺少 RTL/系统证据”的不足；应用上，为 HPC 与 AI 混合负载提供一套可复用的统一 GEMM 引擎，减少独立 FP64/FP32 单元的面积闲置，提高阵列在多种精度下的利用率。",
]

SEC2 = [
"2.1 国内外研究现状",
"2.1.1 多精度计算与精度碎片化",
"过去十年，矩阵引擎的峰值算力持续向低精度迁移。A100 的 INT8 峰值约为 FP64 的 64 倍，RTX 4090 达到 512 倍，B200 为 122 倍；B300 把 INT8 削减到约 150 TOPS、FP64 仅约 1.2 TFLOPS，同时把 FP4 提升到 14 PFLOPS 量级。LLM 训练/推理混合使用 BF16、FP8、FP4 与 INT8，科学计算仍依赖 FP64。精度碎片化使“一个阵列支持多精度”成为体系结构的重要问题。",
"数据通路融合（Bitfusion、Stripes、Laconic、UNPU 等）通过子字打包、乘法器复用、位串行/可重构数据通路支持多格式；但每增加一种格式就增加一份空闲硬件。Bitfusion 以位级可组合见长，Stripes 用位串行换取精度可调，Laconic 面向 FPGA 量化推理，UNPU 做可变权重位宽；它们都不改变 MAC 的精度语义，难以用低精度 MAC 直接获得 FP64 级精度。",
"2.1.2 Ozaki 方案与 FP8/FP4 变体",
"Ozaki I 沿尾数切片，GEMM 次数随切片数平方增长；Ozaki II 用 CRT，GEMM 次数随模数线性增长。对 FP64，INT8 基下 I 约需 28–35 次 GEMM，II 约 14–16 次；FP8 基把每个模数压缩为 3 次 FP8 GEMM（12–13 个模数、36–39 次）；FP4 base-13 基利用 E2M1“加倍后为整数”的性质，用 19 个模数、75 次 FP4 GEMM 达到 FP64。",
"Ozaki II 可写成：A′=trunc(D·A)，B′=trunc(B·E)；对模数 p_i 取余 A′_i=A′ mod p_i、B′_i=B′ mod p_i；整数 GEMM 得 C′_i=A′_iB′_i；CRT 重构 C′≡Σ C′_i·(P/p_i)·y_i (mod P)，最后 C≈D⁻¹C′E⁻¹。P=∏p_i 必须覆盖整数乘积范围，缩放必须保证截断误差与动态范围匹配；模数越多，P 越大、精度越高，但 GEMM/CRT 次数线性增加。",
"FP8 变体的关键是把模数 p≤513 的余数拆成两个 E4M3 可表示的部分，用 Karatsuba/3 次 GEMM 完成一个模数的乘积；FP4 base-13 变体则利用 E2M1 加倍后为整数、以及 13 的幂覆盖所有整数的性质，把每个元素表示为若干 base-13 limb，用 19 个模数/75 次 GEMM 达到 FP64。两者都把“低精度峰值”转化为“高精度有效吞吐”，但代价是更多的 GEMM 与更复杂的编码/重构。",
"2026 年的三项进展进一步完善工程可用性：FP8 量化版、FP4 base-13 版，以及 fast-mode 缩放改进。后者指出现有 fast 公式缺乏尺度不变性，输入整体乘 2^s 会导致精度退化甚至 CRT 恢复失败，并给出零额外开销的修正。这些工作把“算法可行”推进到“可硬件化”，但软件实现仍受非 GEMM 开销与中间平面存储的制约。",
"从数学上看，Ozaki II 的精度由 CRT 模数乘积 P 与缩放指数共同决定：P 必须覆盖整数乘积范围，缩放必须保证截断误差与动态范围匹配；模数越多，P 越大、精度越高，但 GEMM 与 CRT 次数线性增加。fast-mode 的尺度不变性正是针对“输入整体乘 2^s 时缩放/模数不匹配”的问题；若硬件实现不处理该问题，极端动态范围下会出现 CRT 恢复失败。",
"Ozaki II 的 GEMM 次数由模数个数 N 决定，而 N 由目标有效位 b、内维 K 与模数位宽共同决定：对 INT8 基，N≈ceil((2b+log2 K)/8)；对 FP8 基，每个模数需 3 次 FP8 GEMM；对 FP4 base-13 基，每个模数约 4 次 FP4 GEMM。动态范围越大，缩放指数 μ/ν 的跨度越大，所需的 P 与 N 也越大；因此“同一 N 覆盖所有输入”并不成立，精度合同/动态范围自适应是必要的。",
"FP8 变体的关键是把模数 p≤513 的余数拆成两个 E4M3 可表示的部分，用 Karatsuba/3 次 GEMM 完成一个模数的乘积；FP4 base-13 变体则利用 E2M1 加倍后为整数、以及 13 的幂覆盖所有整数的性质，把每个元素表示为若干 base-13 limb，用 19 个模数/75 次 GEMM 达到 FP64。两者都把“低精度峰值”转化为“高精度有效吞吐”，但代价是更多的 GEMM 与更复杂的编码/重构。",
"2.1.3 硬件架构与 OzCore 基线",
"OzCore 是第一个把 Ozaki-II 做成整数化 GEMM 架构的工作：预处理、模归约、CRT 重构全部整数化，消除 FP64/FP32 辅助运算；用更紧的缩放界减少达到目标精度所需的 INT8 GEMM 次数；用 12 个 CRT slot 支持 s∈{2,3,4,6,12} 的运行时切换；相对 INT8 阵列仅增加 27.9% 面积。在 LLaMA-3.1 8B/70B 上 s=3 匹配 BF16 困惑度，相对融合多格式基线取得 1.91× TOPS/mm²、1.40× TOPS/W。",
"OzCore 的微架构由预处理、INT8 阵列、后处理三部分组成：预处理做缩放、指数感知取模与 8-bit 余数打包；后处理用 12 个 CRT slot 做模归约、加权与 128-bit 累加，支持 s∈{2,3,4,6,12} 的分组重构。其 27.9% 面积开销主要来自前/后处理与 CRT；但论文的评估集中在 8192³ 级 GEMM 与 LLaMA 推理，没有给出 K=1024–4096 的非 GEMM 分解，也没有同面积原生 FP64/FP32 的对照。",
"多精度阵列方面，Bitfusion、Stripes、Laconic、UNPU 等工作证明“一套数据通路支持多精度”的可行性，但精度上限仍由 MAC 位宽/累加器决定；RNS/CRT 加速器多用于密码/信号处理，未与 Ozaki 的缩放/重构闭环结合。OzCore 的 INT8-only 对自研 ASIC 不是缺陷，而是合理基线；我们的实测也显示 INT8 在 BF16/FP16/FP32/FP64 等精度下面积—能耗最优。",
"OzCore 的微架构由预处理、INT8 阵列、后处理三部分组成：预处理做缩放、指数感知取模与 8-bit 余数打包；后处理用 12 个 CRT slot 做模归约、加权与 128-bit 累加，支持 s∈{2,3,4,6,12} 的分组重构。其 27.9% 面积开销主要来自前/后处理与 CRT；但论文的评估集中在 8192³ 级 GEMM 与 LLaMA 推理，没有给出 K=1024–4096 的非 GEMM 分解，也没有同面积原生 FP64/FP32 的对照。",
"硬件数据流方面，OGE 的前端需要按行/列统计、缩放、取模、打包；中端 INT8 阵列按模数串行复用；后端在每个模数 GEMM 后立即做 mod p_i、加权与 128-bit 累加，全部模数完成后 mod P/反缩放/舍入。关键不是单个模块，而是 FTU、阵列、CRT 三者的吞吐匹配与双缓冲：FTU 必须在阵列跑当前模数时生成下一模数平面，CRT 必须在上一个 tile 的 GEMM 结束前完成重构。",
"2.1.4 软件/产业实现与精度控制",
"GPU 侧，GEMMul8、ozIMMU、cuBLAS 13.x 的 FP64 emulation + ADP、Intel Arc Xe2 的 Ozaki-II 实现，已把“用低精度张量核模拟高精度”产品化。ADP 在库层做“自动选参 + 默认精度不低于原生 + 无收益回退”；Matsuoka 2026 的 Ozaki 2.5 与“FP8 is All You Need”给出 B300/Rubin 上的模型级硬件选项，但作者明确其为 projected floor，没有 RTL/综合证据；Intel 的 US12455722B2 等专利布局了浮点分解电路与动态精度。",
"在精度控制上，ADP 与 OzCore 的 s 都只是“选参”：ADP 在库层用启发式估计动态范围，OzCore 用 s 寄存器控制重构吞吐；两者都没有把“误差界”作为硬件可执行合同，也没有在最坏输入下提供守卫/回退的 RTL 证据。对科学计算用户，缺少最坏情况保证意味着无法在提交作业前判断结果是否可信；对 LLM 用户，缺少精度统计意味着无法做逐层精度—吞吐权衡。",
"现有精度控制多为“选参”而非“合同”：ADP 用启发式估计动态范围，OzCore 用 s 寄存器控制重构吞吐；二者都没有把“最坏情况误差界”作为硬件可执行约束，也没有在输入越界/溢出时提供 RTL 级守卫与回退。对科学计算用户，缺少最坏情况保证意味着无法在提交作业前判断结果是否可信；对 LLM 用户，缺少精度统计意味着无法做逐层精度—吞吐权衡。",
"此外，Ozaki I 与 II 的取舍并非绝对：I 的后端只需按切片指数移位与宽定点累加，II 的后端需要 CRT 模归约/加权/宽整数累加；当 K 较小、CRT 后端无法被 GEMM 摊薄时，I 可能更优；当 K 较大、目标精度高时，II 的 GEMM 次数优势更明显。因此本课题默认 II，但保留 I 作为小 K/低精度回退，并在 WP1 用代价模型给出交叉点。",
"2.1.5 同面积评估与系统验证",
"现有加速比多相对“原生 FP64 DGEMM”或融合多格式基线报告。GPU 厂商的 FP64 单元面积极小，这种比较会系统性高估模拟收益；真正公平的做法是用 a64（FP64 FMA/INT8 MAC 面积比）、a32 把原生阵列缩放到与统一引擎相同面积，再比较有效吞吐/能效。OzCore 相对融合基线做了公平比较，但没有回答同面积原生 FP64/FP32 的问题。",
"同面积评估方面，Demmel 等提出的 BLAS 精度分级（A/B/C 与 ungameable tests）为“精度保证”提供了可复现的测试方法；但现有 Ozaki 硬件工作尚未把该方法与 a64/a32 面积归一化结合。Chipyard/Gemmini 提供了可复用的 SoC 与脉动阵列基础设施，FireSim 可在 U250 上做周期精确的 FPGA 加速仿真；但 Ozaki 硬件工作多停留在综合/模型级，缺少 CPU+加速器的端到端验证。",
"评估方面，除吞吐/面积/能耗外，还需报告非 GEMM 开销分解、HBM 流量、SRAM 带宽、精度统计（ulp 分布、正确舍入比例）、以及同面积原生 FP64/FP32 的加速比/能效比；工作负载覆盖 K=1024–16384、LLaMA PPL、HPL trailing update、量子化学 DGEMM 与张量网络收缩，避免只报单一形状的峰值。",
"本课题的边界是有限、非特殊值的 GEMM；NaN/Inf/带符号零/次正规采用检测+回退，不在低精度流水线内实现完整 IEEE 754 语义；这一边界与 OzCore/现有 Ozaki 实现一致，但需要在精度合同中明确声明。",
"此外，现有文献的评估口径也不统一：有的报告相对原生 FP64 的峰值加速比，有的相对融合多格式基线，有的只报 kernel 吞吐；GPU 厂商的 FP64 单元面积极小，前一种口径会系统性高估模拟收益。公平比较需要同时固定工艺、面积、功耗、带宽与精度保证，并报告纯计算与系统级两个口径。OzCore 相对融合基线做了较好的等精度比较，但仍未覆盖同面积原生 FP64/FP32 与 CPU+加速器系统；这正是本课题要把 a64/a32 包络与 FPGA 系统验证纳入开题的原因。",
"从研究范式看，本课题不追求“再做一个更快的 Ozaki 内核”，而是把精度合同、小矩阵数据流、同面积评估与系统验证串成闭环；这四件事分别对应体系结构抽象、微架构、方法学与系统四个层面，任何一个层面的缺口都会让“统一引擎”停留在口号。开题阶段先把问题定义、基线、可行性与 36 个月路线定清楚，再进入 RTL 迭代。文献综述的结论是：算法与软件已相对成熟，硬件与评估仍有空间；本课题的机会在工程闭环而不是算法首创。",
"本文的文献综述以公开论文、开源实现与厂商白皮书为主，未引用未公开的工业内部数据；对专利只做定位性引用，不作为性能证据。这样既保证可复现，也避免把不同口径的数字混在一起。",
"2.1.6 研究空白与本课题定位",
"综上，现有工作已经证明“算法可行、整数阵列可实现、软件可产品化”，但尚未回答：小/中矩阵的非 GEMM 开销能否压到 <10%；精度能否作为硬件合同被最坏情况保证；N 倍余数平面能否在片上数据流中不落 HBM；统一引擎在同面积原生 FP64/FP32 下是否真正占优；CPU+加速器系统能否端到端运行。这些空白构成本课题的四个切入点。",
"与 OzCore 相比，本课题的增量不在算法本身，而在工程闭环：OzCore 证明了整数化前/后处理与可重构 CRT 的可行性；本课题进一步把精度合同、最坏情况守卫、小矩阵双缓冲/批处理、同面积 a64/a32 包络与 Chipyard/FireSim/U250 系统验证串成一条可复现的证据链。若 M1 的 a64 低于阈值，本课题将转向 FP32-first 或负结果/测量论文，而不是强行包装加速比。",
"2.2 阅读文献范围与查阅方式",
"文献检索以 Ozaki II、FP8/FP4 emulation、CRT/RNS、multi-precision accelerator、same-area evaluation、Chipyard/FireSim 为关键词，覆盖 2016–2026 年 ISCA/MICRO/HPCA/SC/TCAD/arXiv；阅读方式包括原文精读、开源代码/文档核对，以及与我们前期 RTL/综合数据的对照。此外，本文也参考了 OpenROAD/ASAP7 与 TSMC 28 nm 公开库文档，用于面积/能耗口径的统一；所有引用数字均标注来源，避免把不同工艺/口径的数字直接比较。",
]

SEC3 = [
("3.1 研究目标",
["总体目标：证明“精度虚拟化的 INT8-only Ozaki GEMM 引擎”在同面积、同功耗、可证明精度的约束下，相对原生 FP64/FP32 与 OzCore 具有可辩护的 Pareto 优势，并交付可综合、可复现的原型。",
"L1 模型与算法：精度—代价—面积—能耗模型；Ozaki I/II 交叉规则；三基 pass 数复核；目标工艺 a64/a32 综合标定。验收：复现文献 ≥80% 数字；给出目标工艺的 Go/No-Go。",
"L2 架构与仿真：OGE 架构规格；周期级模拟器；精度合同 API；DSE 结果。验收：模拟器 vs RTL 误差 <5%；K=1024–4096 非 GEMM 开销 <10%。",
"L3 原型与系统：可综合 RTL；综合面积/功耗；Chipyard/FireSim/U250 的 CPU+加速器系统；软件栈。验收：全配置对 MPFR 黄金模型；a64≥30 时 FP64 ≥1.5×，否则 ≥1.0× 且能效 ≥2×；FPGA 端到端应用可运行。"]),
("3.2 主要研究内容",
["（1）精度虚拟化与硬件合同（I1）：定义 EXACT/BOUNDED/FAST 三级合同；缩放上界 vs P/2、重构后范围检查、越界增大 N 或回退；ulp 分布/正确舍入比例/实际 N 统计回读；合同跨 INT8/FP32/FP64 与 I/II 算法族生效。",
"（2）小矩阵非 GEMM 开销压缩（I2，核心）：FTU（尺度不变缩放、指数感知取模、limb 编码、TN 布局）+ CRT epilogue（mod p_i、加权、128-bit 累加、mod P、反缩放/舍入）+ 余数平面双缓冲 + 自适应 N/算法/分块 + 批处理/持久化 kernel。",
"（3）存储/数据流协同（I3）：余数平面片上双缓冲；tile（128×128 输出）与 k-block（64–128）；SRAM 容量/带宽与 tile 调度；HBM 流量不随 N 线性增长；小矩阵 batch/流式与子阵列并行。",
"（4）同面积评估 + FPGA 系统验证（I4）：综合 INT8/FP32/FP64 MAC 与阵列，标定 a64/a32/e64/e32；同面积/同功耗/同带宽/同精度归一化；可行性包络与 Go/No-Go；Chipyard + FireSim/Alveo U250 的 Rocket/BOOM + OGE SoC；U250 用 32×32/16×16 缩比阵列，全尺寸用 FireSim/ASIC 综合。"]),
("3.3 需要解决的关键理论问题或技术问题",
["① 最坏情况精度界的构造性证明与硬件守卫的完备性：如何在有限非特殊值范围内给出可证明误差界，并在输入越界/溢出时安全回退；② FTU/阵列/CRT 的吞吐匹配：指数感知取模、双缓冲与 epilogue 如何重叠，使 K=1024–4096 的非 GEMM 开销 <10%；③ 低算术强度下的数据流：余数平面、SRAM 带宽与 tile/K-block 如何协同，使 HBM 流量不随 N 线性增长；④ 同面积口径：a64/a32 的目标工艺标定、原生阵列缩放与系统级收益如何区分；⑤ FPGA 资源/时序：U250 放不下完整 128×128 时，如何用缩比阵列 + FireSim 全尺寸评估保持结论可信。"]),
("3.4 工作方案（研究方法、技术路线等）及可行性分析",
["技术路线：模型 → 模拟 → RTL → FPGA/系统四条线迭代。先用 Python 建立精度—代价—面积—能耗模型，复现文献数字并给出 a64/a32 相图/Go-No-Go；再用周期级模拟器验证小矩阵数据流、双缓冲、N/算法/分块；随后实现 FTU、CRT 后端、守卫与 INT8 阵列接口，用 Verilator 对 MPFR 黄金模型；最后用 Chipyard + FireSim/U250 搭 CPU+OGE 系统，跑 BLAS 风格库与 1–2 个应用，做同面积/端到端评估。",
"OGE 数据流：A/B tile → FTU 生成余数平面 → INT8 阵列逐模数 GEMM → epilogue 立即 mod/加权/128-bit 累加 → 全部模数完成后 mod P/反缩放/舍入 → 写回 C；余数平面双缓冲，FTU(i+1) 与 GEMM(i)、CRT(t-1) 与 GEMM(t) 重叠。主阵列 INT8-only；FP8/FP4 仅 WP6 可选；算法族默认 II，I 作小 K/低精度回退。",
"可行性：① 算法侧已有 Ozaki II/FP8/FP4/fast scaling 四篇论文与我们的位预算/数值仿真，三基 pass 数已复核；② 硬件侧已有 P0/P0b INT8 MAC 与 128×128 阵列实测：TSMC 28 nm HPC+ FF 下 INT8 378.13 µm²/0.366 pJ，阵列 5.903 mm²/1.800 W（8×8 tile 实测 + 256 tile 组合），FP8/FP4 也已完成综合对照；③ EDA 侧有 DC/VCS/TSMC 28 nm 与开源 ASAP7/OpenROAD 备选；④ 系统侧有 Chipyard/Gemmini/FireSim 开源基础设施与 Alveo U250；⑤ 风险可控：a64 不足则转 FP32-first/能效/负结果论文，RTL 工期紧则关键模块优先，FPGA 资源不足则用缩比阵列 + FireSim 全尺寸。"]),
("3.5 预期创新点",
["I1 精度合同：相对 OzCore 的 s 寄存器，增加应用级 EXACT/BOUNDED/FAST 语义、最坏情况守卫、跨精度/算法族的统计回读；把“精度”从隐式参数变成可验证合同。",
"I2 小矩阵非 GEMM 开销压缩：以 K=1024–4096 的困难区间为目标，用指数感知 FTU、CRT epilogue、余数平面双缓冲、自适应 N/算法/分块、批处理/持久化 kernel，把非 GEMM 开销从 27–55% 压到 <10%，有效吞吐相对 GPU 软件模拟 ≥2×；OzCore 以中大规模 GEMM 为主，未系统解决该区间。",
"I3 存储/数据流协同：余数平面片上双缓冲、tile/K-block、SRAM 带宽/容量协同，使 HBM 流量不随 N 线性增长；相对 OzCore 的 tile 级 pre/post，补充小矩阵低算术强度的数据流设计。",
"I4 同面积 + 系统验证：用目标工艺 a64/a32 标定与同面积/同功耗/同带宽包络，补 OzCore 缺失的“原生 FP64/FP32”一维；用 Chipyard/FireSim/U250 做 CPU+加速器端到端验证，把 kernel 级结论推进到系统级。",
"说明：不使用“首个/首次”作为无条件表述；所有“首次”限定在“据我们所知 + 可综合 RTL + 同面积/系统证据”的组合上。多基不作为核心新颖性主张；算法族选择作为 WP1 的次要规则。"]),
]

SEC4 = [
"4.1 应具备的条件",
"完成本课题需要：多精度 GEMM/体系结构/数值分析基础；Python/C++ 建模能力；Verilog/SystemVerilog 与 Verilator/DC/VCS 流程；目标工艺标准单元库与 EDA 资源；FPGA（Alveo U250）与 Chipyard/FireSim 环境；以及导师课题组在体系结构/EDA/数值分析方向的指导。",
"4.2 已具备的条件",
"① 文献与算法基础：Ozaki II、FP8/FP4 变体、fast scaling、OzCore 四篇核心论文已精读，完成三基 pass 数复核与数值仿真；② 硬件/EDA：TSMC 28 nm HPC+ FF 库、Synopsys DC/VCS、P0/P0b INT8 MAC 与 128×128 阵列的综合/功耗数据；③ 计算资源：Python/C++ 模型、Linux 服务器、8 GB EDA VM（可扩内存）、Alveo U250 与 Chipyard/FireSim 开源基础设施（计划）；④ 团队/导师：体系结构、数值分析、EDA 方向可获指导；⑤ 前期结果：INT8 MAC 378.13 µm²/0.366 pJ、阵列 5.903 mm²/1.800 W；FP8/FP4 MAC/阵列对照；等精度成本 INT8 最优。",
"4.3 可能遇到的困难与问题和解决措施",
"① a64/a32 目标工艺综合不确定——先用 ASAP7/OpenROAD 与 TSMC 28 nm 双口径，给出区间包络；若低于阈值，转 FP32-first/能效/负结果论文（Plan B）。② RTL 工期紧——关键模块优先（FTU/CRT/守卫），系统集成后置，复用 Gemmini/Chipyard 接口。③ 精度证明难——限定有限非特殊值，特殊值回退；差分测试 + 形式化守卫；与数值分析合作。④ FPGA 资源不足——U250 用 32×32/16×16 缩比阵列验证系统，全尺寸用 FireSim/ASIC 综合；提前做资源估算。⑤ 非 GEMM 开销压不下——调整 tile/双缓冲/子阵列，必要时把主战场移到大规模并诚实报告。",
]

PLAN = [
("2026.11.01—2027.01.31","文献精读与批注；Python 模型骨架；Ozaki I/II、三基 pass 数复核；GPU/文献基线复现。","阅读笔记；oge_model v0.1；三基 pass 数/成本表。"),
("2027.02.01—2027.04.30","精度—代价模型；a64/a32 综合标定；I/II 交叉规则；可行性包络与 Go/No-Go。","模型 v1；a64/a32 报告；Go/No-Go 报告。"),
("2027.05.01—2027.07.31","OGE 架构规格；周期级模拟器 v0.1；小矩阵数据流/双缓冲 DSE。","架构规格 v1；模拟器 v0.1；第一组 DSE 数据。"),
("2027.08.01—2027.10.31","精度合同/守卫定义；自适应 N/算法/分块；模拟器验证。","合同定义；守卫规格；模拟器 v1。"),
("2027.11.01—2028.01.31","FTU RTL（缩放/指数感知取模/limb/布局）；Verilator 对 MPFR。","FTU RTL；验证报告。"),
("2028.02.01—2028.04.30","CRT 后端/守卫 RTL；与 INT8 阵列接口；小规模综合。","CRT/守卫 RTL；综合报告。"),
("2028.05.01—2028.07.31","阵列集成；综合/功耗/关键路径；顶会论文初稿。","完整 RTL；综合报告；论文初稿。"),
("2028.08.01—2028.10.31","Chipyard/FireSim/U250 原型；CPU+OGE 系统 bring-up；BLAS 库雏形。","FPGA 原型；系统 demo；库 v0.1。"),
("2028.11.01—2029.01.31","软件栈；LLaMA/HPL/量子化学应用；同面积/同功耗评估。","应用结果；Pareto 报告。"),
("2029.02.01—2029.04.30","系统级评估；论文投稿/修改；artifact 整理。","系统论文；artifact v1。"),
("2029.05.01—2029.07.31","学位论文撰写；结果复核；答辩准备。","学位论文初稿。"),
("2029.08.01—2029.10.31","论文修改；答辩；最终提交。","学位论文定稿；答辩。"),
]

REFS = [
"J. Park, J. Lee, H. Lee, J. Kim, J. Kim, J.-J. Kim. OzCore: An Ozaki-Scheme-II-Based GEMM Architecture for Unified Integer and Floating-Point Computation. MICRO 2026, pp. 2101–2115.",
"K. Ozaki, Y. Uchino, T. Imamura. Ozaki Scheme II: A GEMM-oriented emulation of floating-point matrix multiplication using an integer modular technique. arXiv:2504.08009, 2026.",
"Y. Uchino, K. Ozaki, T. Imamura. Double-Precision Matrix Multiplication Emulation via Ozaki-II Scheme with FP8 Quantization. arXiv:2603.10634, 2026.",
"S. Hayashi, D. Mukunoki, T. Hoshino, T. Katagiri. DGEMM with Ozaki Scheme I/II on FP4 Tensor Cores: A Base-13 E2M1 Limb Representation. arXiv:2608.06812, 2026.",
"Improved Scaling for Fast Mode of Ozaki. 2026.",
"H. Ootomo, et al. GEMMul8 / ozIMMU: FP64 emulation on tensor cores. 2024–2026.",
"NVIDIA. cuBLAS 13.x FP64 emulation and Automatic Dynamic Precision (ADP). 2026.",
"Matsuoka. Ozaki 2.5 / FP8 is All You Need. 2026 (projected floor, model-level).",
"H. Sharma, et al. Bitfusion: Bit-Level Dynamically Composable Architecture for Accelerating Deep Neural Networks. ISCA 2018.",
"H. Sharma, et al. Stripes: Bit-Serial Deep Neural Network Computing. MICRO 2016.",
"S. Sharify, et al. Laconic: FPGA Acceleration of Deep Neural Networks with Quantized Precision. MICRO 2019.",
"J. Lee, et al. UNPU: An Energy-Efficient Deep Neural Network Accelerator with Fully Variable Weight Bit Precision. JSSC 2019.",
"Intel. US12455722B2, US20220391470A1, US11669586 (floating-point decomposition / low-precision emulation patents).",
"M. Horowitz. Computing's Energy Problem (and What We Can Do About It). ISSCC 2014.",
"N. J. Higham. Accuracy and Stability of Numerical Algorithms. SIAM, 2002.",
"B. Parhami. Computer Arithmetic: Algorithms and Hardware Designs. Oxford, 2010.",
"K. Asanović, et al. Chipyard: Integrated Design, Simulation, and Implementation Framework for Custom SoCs. IEEE Micro, 2020.",
"S. Karandikar, et al. FireSim: FPGA-Accelerated Cycle-Exact Scale-Out System Simulation in the Public Cloud. ISCA 2018.",
"H. Genc, et al. Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration. DAC 2021.",
"J. Demmel, et al. BLAS accuracy grading and ungameable tests. 2026.",
"P. Micikevicius, et al. FP8 Formats for Deep Learning. arXiv:2209.05433, 2022.",
"K. Ozaki, T. Ogita, S. Oishi, S. M. Rump. Error-free transformations of matrix multiplication by using fast routines of matrix multiplication and its applications. Numerical Algorithms, 2012.",
"G. M. Amdahl. Validity of the single processor approach to achieving large scale computing capabilities. AFIPS 1967.",
"N. P. Jouppi, et al. In-Datacenter Performance Analysis of a Tensor Processing Unit. ISCA 2017.",
"NVIDIA. NVIDIA B200 Tensor Core GPU / Blackwell Architecture Whitepaper. 2024–2026.",
"RIKEN R-CCS. GEMMul8 / ozIMMU: FP64 emulation libraries. 2024–2026.",
"Intel. Intel AMX and Arm SVE2 INT8-based FP64 emulation. 2023–2026.",
"OpenROAD / ASAP7. Open-source RTL-to-GDS flow and predictive 7 nm PDK. 2018–2026.",
"IEEE. IEEE Standard for Floating-Point Arithmetic (IEEE 754-2019). 2019.",
"H. Esmaeilzadeh, et al. Neural Acceleration for General-Purpose Approximate Programs. MICRO 2012.",
]

def add_para(cell, text, bold=False, size=12):
    p = cell.add_paragraph()
    p.paragraph_format.space_after = Pt(2); p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text); r.font.name = "宋体"; r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体"); r.font.size = Pt(size); r.bold = bold
    _set_para_mark(p, size)

def fill_cell(cell, paras):
    cell.text = ""
    first = True
    for text in paras:
        if first:
            p = cell.paragraphs[0]; first = False
        else:
            p = cell.add_paragraph()
        p.paragraph_format.space_after = Pt(2); p.paragraph_format.line_spacing = 1.15
        r = p.add_run(text); r.font.name = "宋体"; r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体"); r.font.size = Pt(12)
        # bold headings
        if text[:1].isdigit() or text[:1] in "一二三四五六七" or text[:2] in ("课题","选题","研究"):
            r.bold = True
        _set_para_mark(p, 12)

def add_fig(cell, path, caption, width=13.2):
    p = cell.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Cm(width))
    cp = cell.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(6)
    r = cp.add_run(caption); r.font.name = "宋体"; r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体"); r.font.size = Pt(10.5)
    _set_para_mark(cp, 10.5)

def main():
    d = Document(TEMPLATE)
    # remove two leading blank paragraphs
    removed = 0
    for para in list(d.paragraphs[:6]):
        if removed < 2 and not para.text.strip():
            para._element.getparent().remove(para._element); removed += 1
    # cover
    t = d.tables[0]
    vals = [
        "论文题目：面向多精度统一执行的 Ozaki 模拟 GEMM 加速器",
        "关键技术研究",
        "姓    名：________        学号：________",
        "学科专业：计算机科学与技术",
        "研究方向：计算机体系结构 / 多精度矩阵计算",
        "指导教师：________        职称：________",
        "协助指导教师：________  职称：________",
        "学    院：________",
        "开题时间：2026 年 11 月    日",
    ]
    # table 0 has 8 rows; put title on first row with two paragraphs, then rows 1-7
    t.rows[0].cells[0].text = ""
    p = t.rows[0].cells[0].paragraphs[0]
    for j, txt in enumerate(["论文题目：面向多精度统一执行的 Ozaki 模拟 GEMM 加速器", "关键技术研究"]):
        pp = p if j == 0 else t.rows[0].cells[0].add_paragraph()
        r = pp.add_run(txt); r.font.name = "仿宋"; r._element.rPr.rFonts.set(qn('w:eastAsia'), "仿宋"); r.font.size = Pt(12)
        pp.paragraph_format.space_before = Pt(0); pp.paragraph_format.space_after = Pt(0); pp.paragraph_format.line_spacing = 1.0
    for i, v in enumerate(vals[2:], start=1):
        cell = t.rows[i].cells[0]; cell.text = ""
        p = cell.paragraphs[0]; r = p.add_run(v)
        r.font.name = "仿宋"; r._element.rPr.rFonts.set(qn('w:eastAsia'), "仿宋"); r.font.size = Pt(12)
        p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
    # cover date
    for p in d.paragraphs:
        if "二〇二六年四月" in p.text:
            p.text = "二〇二六年十一月"
    # section fills
    fill_cell(d.tables[1].rows[0].cells[0], SEC1)
    add_fig(d.tables[1].rows[0].cells[0], os.path.join(FIG, "fig1_peak_ratio.png"), "图 1  低精度峰值相对 FP64 的倍数（公开规格示意）")
    fill_cell(d.tables[2].rows[0].cells[0], SEC2)
    add_fig(d.tables[2].rows[0].cells[0], os.path.join(FIG, "fig2_ozaki_flow.png"), "图 2  Ozaki-II 分解与 CRT 重构流程")
    t3 = d.tables[3]
    while len(t3.rows) < len(SEC3):
        t3.add_row()
    for i, (head, paras) in enumerate(SEC3):
        cell = t3.rows[i].cells[0]
        cell.text = ""
        p = cell.paragraphs[0]; r = p.add_run(head); r.bold = True
        r.font.name = "宋体"; r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体"); r.font.size = Pt(12)
        _set_para_mark(p, 12)
        for txt in paras:
            add_para(cell, txt)
        if i == 3:
            add_fig(cell, os.path.join(FIG, "fig3_oge_arch.png"), "图 3  OGE 架构：FTU + INT8 阵列 + CRT epilogue + 精度合同")
            add_fig(cell, os.path.join(FIG, "fig4_overhead.png"), "图 4  小/中矩阵非 GEMM 开销随 K 的变化（示意，目标 <10%）")
    fill_cell(d.tables[4].rows[0].cells[0], SEC4)
    add_fig(d.tables[4].rows[0].cells[0], os.path.join(FIG, "fig5_roadmap.png"), "图 5  36 个月技术路线与里程碑")
    # plan
    t5 = d.tables[5]
    while len(t5.rows) < len(PLAN) + 1:
        t5.add_row()
    for i, (dates, content, result) in enumerate(PLAN, start=1):
        for j, v in enumerate([dates, content, result]):
            cell = t5.rows[i].cells[j]; cell.text = ""
            p = cell.paragraphs[0]; r = p.add_run(v)
            r.font.name = "宋体"; r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体"); r.font.size = Pt(10.5)
    # refs
    t6 = d.tables[6]
    for i, ref in enumerate(REFS, start=1):
        if i >= len(t6.rows):
            t6.add_row()
        cells = t6.rows[i].cells
        cells[0].text = str(i); cells[1].text = ""
        p = cells[1].paragraphs[0]; r = p.add_run(ref)
        r.font.name = "宋体"; r._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体"); r.font.size = Pt(10.5)
    # advisor
    d.tables[7].rows[0].cells[0].text = "（由导师填写）"
    # widths and margins
    widths = {1: [13.5], 2: [13.5], 3: [13.5], 4: [13.5], 5: [3.0, 8.0, 2.5], 6: [1.1, 12.4], 7: [13.5]}
    for ti, ws in widths.items():
        t = d.tables[ti]; t.autofit = False; t.allow_autofit = False; t.alignment = WD_TABLE_ALIGNMENT.LEFT
        tblPr = t._tbl.tblPr
        tblW = tblPr.find(qn('w:tblW'))
        if tblW is None: tblW = OxmlElement('w:tblW'); tblPr.append(tblW)
        tblW.set(qn('w:w'), str(int(sum(ws) * 567))); tblW.set(qn('w:type'), 'dxa')
        layout = tblPr.find(qn('w:tblLayout'))
        if layout is None: layout = OxmlElement('w:tblLayout'); tblPr.append(layout)
        layout.set(qn('w:type'), 'fixed')
        ind = tblPr.find(qn('w:tblInd'))
        if ind is not None:
            ind.set(qn('w:w'), '0')
        for ci, w in enumerate(ws):
            t.columns[ci].width = Cm(w)
            for row in t.rows: row.cells[ci].width = Cm(w)
        for row in t.rows:
            for cell in row.cells: _set_cell_margins(cell)
        for row in t.rows: row.allow_break_across_pages = True
    # university name
    for sec in d.sections:
        sec.left_margin = Cm(2.0)
        sec.right_margin = Cm(2.0)
    roots = [d.element.body]
    for sec in d.sections:
        roots += [sec.header._element, sec.footer._element]
    for root in roots:
        for t in root.iter(qn('w:t')):
            if t.text and "科技大学" in t.text:
                t.text = t.text.replace("科技大学", "国防科技大学")
    d.save(OUT_DOCX)
    # markdown
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {TITLE}\n\n## 一、学位论文选题的立论依据\n\n" + "\n\n".join(SEC1) + "\n\n")
        f.write("## 二、文献综述\n\n" + "\n\n".join(SEC2) + "\n\n")
        f.write("## 三、研究内容\n\n")
        for head, paras in SEC3:
            f.write(f"### {head}\n\n" + "\n\n".join(paras) + "\n\n")
        f.write("## 四、研究条件\n\n" + "\n\n".join(SEC4) + "\n\n")
        f.write("## 五、学位论文工作计划\n\n| 起止日期 | 主要完成研究内容 | 预期成果 |\n|---|---|---|\n")
        for dates, content, result in PLAN: f.write(f"| {dates} | {content} | {result} |\n")
        f.write("\n## 六、主要参考文献\n\n")
        for i, ref in enumerate(REFS, 1): f.write(f"{i}. {ref}\n")
        f.write("\n## 七、导师评语\n\n（由导师填写）\n")
    print("saved", OUT_DOCX, OUT_MD)

if __name__ == "__main__":
    main()
