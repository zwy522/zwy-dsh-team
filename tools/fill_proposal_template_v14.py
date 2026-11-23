# -*- coding: utf-8 -*-
"""Fill the graduate proposal template with the v1.4 dual-mode content."""
import os, sys
sys.path.insert(0, "tools")
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from fill_proposal_template import _set_para_mark, _set_cell_margins

TEMPLATE = "literature_docs/开题报告模板.docx"
OUT_DOCX = "docs/proposal/开题报告-模板版-v1.4.docx"
OUT_MD = "docs/proposal/开题报告-模板版-v1.4.md"
FIG = "docs/proposal/figures"
TITLE = "面向多格式 AI 计算的可重构—Ozaki 双模加速器关键技术研究"

SEC1 = [
"1.1 课题来源",
"本课题为自选课题，依托导师课题组在多格式矩阵计算与体系结构方向的研究基础。课题来源/资助信息：________（如国家自然科学基金、国家重点研发计划、实验室开放基金等，待补充）。",
"1.2 选题依据",
"大模型与科学计算对矩阵乘（GEMM）的精度需求正在同时向两端扩张：一端是 FP64/FP32 的科学计算与训练梯度，另一端是 FP16/BF16/FP8/FP4/INT8 的推理与低精度训练。GPU 厂商把面积与功耗持续投向低精度，公开规格中 INT8 与 FP64 的峰值比已达到 10²–10³ 量级；而 HPC 与科学计算仍依赖 FP64，二者形成结构性矛盾。传统数据通路融合在一个 MAC 中复用多格式，每增加一种格式就增加一份大多数时间空闲的硬件，持续稀释单位面积算力；单一 INT8 阵列 + Ozaki 虽然能以较低面积支持高精度，却让 FP4/INT8 等低精度格式仍走多 pass 模拟，牺牲了原生效率。",
"Ozaki Scheme II 给出了高精度侧的一条可行路线：把高精度浮点矩阵按行/列共享指数缩放为整数，对一组两两互素的模数取余，在低精度整数阵列上做精确 GEMM，再用中国剩余定理（CRT）重构。其关键性质是中间乘积精确、误差可分析、GEMM 次数随模数个数线性增长。OzCore（MICRO 2026）把该方案做成整数化 GEMM 架构，在 INT8 阵列上仅增加 27.9% 前/后处理面积，就在 LLaMA-3.1 上匹配 BF16 困惑度，并相对融合多格式基线取得 1.91× TOPS/mm² 与 1.40× TOPS/W。",
"但 OzCore 的“统一”只覆盖了高精度侧：对 FP4、FP8、INT8 这些低精度格式，若仍走 Ozaki 的多 pass 分解/取模/CRT，会付出不必要的计算、存储与重构开销；若为每种低精度格式单独造阵列，又回到格式融合的面积税。现有融合架构（Bitfusion、Stripes、BitWave、Laconic、UNPU 等）虽然能在 MAC 级复用乘法资源，但多数不区分“高精度模拟”与“低精度原生”两种语义，且缺少子阵列级的物理组合与系统级验证。",
"本课题因此提出 ODA（Ozaki–Dual-mode Accelerator，双模加速器）：高精度侧（>8 bit）用 Ozaki-II 在 INT8 子阵列上低精度模拟高精度；低精度侧（≤8 bit）用 BSP lane（8×8 乘法器由 4×4 切片物理组合）+ 16×16 子阵列原生执行，靠子阵列组合适配格式与 GEMM 形状，不用其中一种格式逼近另一种；最后用 Chipyard + FireSim + Alveo U250 做 CPU+加速器的系统验证。三个论文点分别对应高精度模拟、低精度可重组数据通路、FireSim/U250 原型。",
"1.3 研究意义",
"学术上，本课题把“高精度模拟”和“低精度原生”放进同一物理 Fabric，研究格式—模式—子阵列组合的联合设计空间，给出可综合 RTL、同面积评估与系统级证据；相对 OzCore 补上低精度原生、双模调度与 CPU+加速器原型，相对融合架构补上子阵列级物理组合与原生低精度语义。应用上，为 HPC 与 AI 混合负载提供一套可复用的双模 GEMM 引擎：高精度任务不必为 FP64/FP32 造大面积原生单元，低精度任务不必为 FP4/INT8 走多 pass 模拟，从而减少面积闲置、提高阵列在多格式负载下的利用率。",
"预期成果包括：双模 ODA 架构与 RTL、BSP lane/子阵列组合方法、Ozaki 高精度引擎与精度合同、Chipyard/FireSim/U250 原型与同面积评估；形成 2–3 篇高水平论文与可复现 artifact。",
]

SEC2 = [
"2.1 国内外研究现状",
"2.1.1 多精度计算与精度碎片化",
"过去十年，矩阵引擎的峰值算力持续向低精度迁移。A100 的 INT8 峰值约为 FP64 的 64 倍，RTX 4090 达到 512 倍，B200 为 122 倍；B300 把 INT8 削减到约 150 TOPS、FP64 仅约 1.2 TFLOPS，同时把 FP4 提升到 14 PFLOPS 量级。LLM 训练/推理混合使用 BF16、FP8、FP4 与 INT8，科学计算仍依赖 FP64。精度碎片化使“一个阵列支持多精度”成为体系结构的重要问题，但“支持”不等于“每种格式都高效”：高精度需要模拟，低精度需要原生，二者对数据通路的要求不同。",
"2.1.2 融合架构与统一可重构 MAC",
"融合架构的核心是在同一 MAC/阵列中复用乘法器、加法器、指数与舍入逻辑，按格式配置位宽、流水与累加宽度。Bitfusion [9] 用位级可组合乘法器支持可变位宽/多格式，面积可调、灵活性强；但位级 mux、移位与布线开销会降低低精度峰值，且未处理 FP4 指数/NaN 等原生语义。Stripes [10] 用位串行计算换取精度可调与面积效率，延迟随位宽线性增长，控制复杂，不适合高吞吐低精度 GEMM。BitWave [26] 利用列级位切片与稀疏性做可重构/高效计算，主要面向量化 DNN，未覆盖 FP8/FP4 原生格式与 Ozaki 高精度模拟。",
"格式级融合与可变精度阵列方面，Laconic [11] 面向 FPGA 量化推理，UNPU [12] 做可变权重位精度，Gemmini [19] 提供脉动阵列 + 量化数据流与完整软硬件栈；它们证明了“一套阵列支持多精度”的可行性，但格式集合固定、精度上限由 MAC 位宽/累加器决定，缺少子阵列级组合与双模共享。NVIDIA Tensor Core [25] 在一个 MAC 中融合多格式，峰值高、生态成熟；但每种格式仍需独立的 datapath/面积，低精度原生效率与可编程性受限于固定指令/数据流。",
"从设计维度看，统一可重构 MAC 需要同时决定：① 乘法资源（位切片、子字打包、4×4/8×8 切片）；② 累加宽度与对齐（INT32、FP32、宽整数）；③ 格式前端（符号/指数/尾数/特殊值/舍入）；④ 重组粒度（MAC、lane、tile、子阵列）与控制/门控。现有工作多集中在 MAC/lane 级，靠细粒度 mux 或位串行实现灵活；其代价是低精度峰值下降、格式语义不完整，且难以把“高精度模拟”和“低精度原生”放进同一物理阵列。",
"本课题的 BSP lane 取“粗粒度物理重组”：8×8 乘法器由 4 个 4×4 切片组成，INT8 用全部切片，FP4/FP6/FP8 用切片子集 + 原生指数/舍入；16×16 tile 作为格式人格与电源/时钟门控单位，tile 之间可组合为 1×1/2×1/2×2/4×4 逻辑 tile。相对 Bitfusion/Stripes 的位级/位串行方案，重点在保留低精度原生语义与峰值；相对格式融合，重点在子阵列级组合与空闲门控。这构成本课题论文点 2 的切入点。",
"2.1.3 Ozaki 方案与 FP8/FP4 变体",
"Ozaki I 沿尾数切片，GEMM 次数随切片数平方增长；Ozaki II 用 CRT，GEMM 次数随模数线性增长。对 FP64，INT8 基下 I 约需 28–35 次 GEMM，II 约 14–16 次；FP8 基把每个模数压缩为 3 次 FP8 GEMM（12–13 个模数、36–39 次）；FP4 base-13 基利用 E2M1“加倍后为整数”的性质，用 19 个模数、75 次 FP4 GEMM 达到 FP64。",
"Ozaki II 可写成：A′=trunc(D·A)，B′=trunc(B·E)；对模数 p_i 取余 A′_i=A′ mod p_i、B′_i=B′ mod p_i；整数 GEMM 得 C′_i=A′_iB′_i；CRT 重构 C′≡Σ C′_i·(P/p_i)·y_i (mod P)，最后 C≈D⁻¹C′E⁻¹。P=∏p_i 必须覆盖整数乘积范围，缩放必须保证截断误差与动态范围匹配；模数越多，P 越大、精度越高，但 GEMM/CRT 次数线性增加。",
"2026 年的三项进展进一步完善工程可用性：FP8 量化版 [3]、FP4 base-13 版 [4]，以及 fast-mode 缩放改进 [5]。后者指出现有 fast 公式缺乏尺度不变性，输入整体乘 2^s 会导致精度退化甚至 CRT 恢复失败，并给出零额外开销的修正。这些工作把“算法可行”推进到“可硬件化”，但软件实现仍受非 GEMM 开销与中间平面存储的制约。",
"2.1.4 硬件架构与 OzCore 基线",
"OzCore [1] 是第一个把 Ozaki-II 做成整数化 GEMM 架构的工作：预处理、模归约、CRT 重构全部整数化，消除 FP64/FP32 辅助运算；用更紧的缩放界减少达到目标精度所需的 INT8 GEMM 次数；用 12 个 CRT slot 支持 s∈{2,3,4,6,12} 的运行时切换；相对 INT8 阵列仅增加 27.9% 面积。在 LLaMA-3.1 8B/70B 上 s=3 匹配 BF16 困惑度，相对融合多格式基线取得 1.91× TOPS/mm²、1.40× TOPS/W。",
"OzCore 的微架构由预处理、INT8 阵列、后处理三部分组成：预处理做缩放、指数感知取模与 8-bit 余数打包；后处理用 12 个 CRT slot 做模归约、加权与 128-bit 累加，支持 s∈{2,3,4,6,12} 的分组重构。其 27.9% 面积开销主要来自前/后处理与 CRT；但论文的评估集中在 8192³ 级 GEMM 与 LLaMA 推理，没有给出 K=1024–4096 的非 GEMM 分解，也没有同面积原生 FP64/FP32 的对照，更没有低精度原生/双模系统验证。",
"2.1.5 软件/产业实现与精度控制",
"GPU 侧，GEMMul8/ozIMMU [6]、cuBLAS 13.x 的 FP64 emulation + ADP [7]、Intel Arc Xe2 的 Ozaki-II 实现，已把“用低精度张量核模拟高精度”产品化。ADP 在库层做“自动选参 + 默认精度不低于原生 + 无收益回退”；Matsuoka 2026 的 Ozaki 2.5 与“FP8 is All You Need” [8] 给出 B300/Rubin 上的模型级硬件选项，但作者明确其为 projected floor，没有 RTL/综合证据；Intel 的 US12455722B2 等专利 [13] 布局了浮点分解电路与动态精度。",
"在精度控制上，ADP 与 OzCore 的 s 都只是“选参”：ADP 在库层用启发式估计动态范围，OzCore 用 s 寄存器控制重构吞吐；两者都没有把“误差界”作为硬件可执行合同，也没有在最坏输入下提供守卫/回退的 RTL 证据。对科学计算用户，缺少最坏情况保证意味着无法在提交作业前判断结果是否可信；对 LLM 用户，缺少精度统计意味着无法做逐层精度—吞吐权衡。",
"2.1.6 同面积评估与系统验证",
"现有加速比多相对“原生 FP64 DGEMM”或融合多格式基线报告。GPU 厂商的 FP64 单元面积极小，这种比较会系统性高估模拟收益；真正公平的做法是用 a64（FP64 FMA/INT8 MAC 面积比）、a32 把原生阵列缩放到与统一引擎相同面积，再比较有效吞吐/能效。OzCore 相对融合基线做了公平比较，但没有回答同面积原生 FP64/FP32 的问题。",
"同面积评估方面，Demmel 等提出的 BLAS 精度分级与 ungameable tests [20] 为“精度保证”提供了可复现的测试方法；但现有 Ozaki 硬件工作尚未把该方法与 a64/a32 面积归一化结合。Chipyard [17] 提供 Rocket/BOOM + 加速器的 SoC 生成框架，FireSim [18] 在 Alveo U250 等 FPGA 上做周期精确的 FPGA 加速模拟；但 Ozaki/多格式加速器工作多停留在综合/模型级，缺少 CPU+加速器的端到端验证。",
"2.1.7 研究空白与本课题定位",
"综上，现有工作已经证明“算法可行、整数阵列可实现、软件可产品化”，但尚未回答：低精度格式能否不经过高精度模拟、在同一物理阵列上原生执行；高精度模拟与低精度原生能否在子阵列级共享/组合；BSP/子阵列重组的面积/时序/峰值代价是多少；双模在 CPU+加速器系统中是否真正占优。这些空白分别对应本课题的三个论文点。",
"与 OzCore 相比，本课题的增量不在 Ozaki 算法，而在双模共存、低精度原生可重组数据通路与系统验证；与 Bitfusion/Stripes/BitWave 等融合架构相比，增量在粗粒度物理组合、原生 FP4/INT8 语义与同面积/系统证据。本课题不使用“首个/首次”作为无条件表述，所有新颖性限定在“据我们所知 + 可综合 RTL + 同面积/系统证据”的组合上。",
"2.1.8 进一步讨论：代价、精度与评估口径",
"从可重构 MAC 的物理实现看，位切片方案的关键代价在乘法器阵列的 mux、部分积移位与符号扩展；子字打包（subword packing）可提高低精度吞吐，但需要处理进位/饱和与跨 lane 对齐。Bitfusion [9] 的位级组合在低位宽下面积效率高，但高位宽需要多次组合，控制复杂；Stripes [10] 的位串行延迟随位宽线性增长，不适合 K 大的 GEMM；BitWave [26] 的列级位切片依赖稀疏模式，通用性受限。格式融合（Tensor Core [25]/Laconic [11]/UNPU [12]）为每类格式保留独立乘法/累加路径，峰值高但面积随格式数增长；Gemmini [19] 的量化脉动阵列在 INT8/INT16 上成熟，但缺少 FP4/FP8 原生指数/舍入与子阵列组合。",
"从代价模型看，Ozaki II 的 GEMM 次数由模数个数 s 决定，s 由目标有效位 b、内维 K、模数位宽与缩放动态范围共同决定；对 INT8 基，容量下界约为 ceil((2b+log2K)/8)，工程上还需加 1–2 个模数余量。s 增大时 GEMM 线性增加，CRT/前处理的非 GEMM 开销也线性增加；小 K 时 CRT/取模/重构无法被 GEMM 摊薄，这正是高精度侧需要与低精度原生模式共存、按负载选择的原因。",
"精度合同方面，EXACT/BOUNDED/FAST 的差异不只是 s 的取值，而是缩放上界、模数集、守卫阈值与回退策略的联合约束；最坏情况误差界需要覆盖截断、取模、CRT 重构与最终舍入，且要对 NaN/Inf/次正规/溢出做显式回退。现有工作多给平均误差或 PPL，缺少对最坏输入的构造性证明与 RTL 守卫；这是论文点 1 要补的工程闭环。",
"子阵列级重组的研究相对空白：Bitfusion/Stripes 在 MAC/lane 级做位级组合，Laconic/UNPU 在格式级做固定 datapath，Gemmini 在阵列级做数据流；尚缺少“16×16 tile 人格 + 1×1/2×1/2×2/4×4 组合 + 双模共享”的物理重组方案。其难点是 tile 边界碎片、配置/drain 开销、格式前端的面积摊销，以及 O-mode 余数平面与 R-mode 原生 tile 的 SRAM/NoC 共存。",
"同面积评估还需要区分纯计算面积与系统面积：a64/a32 只归一化 MAC/FMA 面积，未计入 SRAM/NoC/前处理/CRT；系统级比较应同时报告等面积、等功耗、等带宽与等精度保证，并用 FireSim/U50 跑端到端负载。现有 Ozaki 工作多报 kernel 加速比，融合架构多报峰值，二者口径不同；本课题用同一 TSMC 28 nm 工艺、同一精度合同与同一系统栈对比。",
"文献检索按算法（Ozaki/FP8/FP4）、微架构（融合/可重构/脉动阵列）、系统（Chipyard/FireSim/U50）与评估（同面积/精度分级）四类展开，选取 2016–2026 年代表性工作精读，并复核其公开数字的工艺/精度口径，避免把不同口径的数字直接比较。",
"从硬件实现角度，OzCore 的 27.9% 面积开销主要来自 CRT/前处理；其 12 个 slot 支持 s 切换，但 slot 数与模数上界固定，动态范围极端时需软件回退。若把低精度原生模式加入同一阵列，还必须回答 tile 级共享/隔离、配置/drain 开销与 O-mode 余数平面的带宽冲突；这些是 OzCore 未覆盖的。",
"系统验证方面，FireSim 的 FPGA 加速模拟可在 U250 上跑周期精确的 CPU+加速器，但资源限制决定了全 128×128 阵列需缩比或分块；因此需要把缩比原型的端到端结果与全尺寸 FireSim/ASIC 综合交叉验证，并报告频率/带宽/精度口径，避免把缩比结论直接外推到全尺寸。",
"此外，还应关注 2025–2026 年工业界的 FP8/FP4 训练与推理实践，其格式比例与精度需求可为双模模式选择提供真实负载依据；本文不把厂商白皮书中的峰值当作可复现实验，而是作为需求与趋势证据。",
"文献综述的结论是：算法与软件已相对成熟，融合架构/可重构 MAC 已有丰富积累，但“高精度模拟 + 低精度原生”的双模共存、子阵列级物理组合与 CPU+加速器系统验证仍是空白；本课题的机会在工程闭环与可复现证据，而不是重复 Ozaki 算法或再做一个格式融合阵列。",
"2.2 阅读文献范围与查阅方式",
"文献检索以 Ozaki II、FP8/FP4 emulation、bit-sliced/reconfigurable MAC、multi-precision accelerator、same-area evaluation、Chipyard/FireSim 为关键词，覆盖 2016–2026 年 ISCA/MICRO/HPCA/SC/TCAD/JSSC/arXiv；阅读方式包括原文精读、开源代码/文档核对，以及与我们前期 RTL/综合数据的对照。所有引用数字标注来源与工艺口径，避免把不同工艺/精度保证的数字直接比较。",
]

SEC3 = [
("1.研究目标",
["总体目标：证明“高精度模拟 + 低精度原生”的双模架构在同面积、同精度、同带宽约束下，相对 OzCore（单模模拟）与格式融合阵列具有可辩护的 Pareto 优势，并交付可综合、可复现、可运行的系统原型。",
"L1 模型与算法：建立格式—模式—代价模型；给出 O-mode 模数/s 选择与 R-mode 子阵列组合规则；用 TSMC 28 nm 标定 a32/a64；复现文献 ≥80% 数字并给出 Go/No-Go。",
"L2 架构与仿真：BSP lane、16×16 tile、可组合 Fabric、双模调度器与周期级模拟器；BSP 相对 INT8 面积开销 ≤20%，模拟器 vs RTL 误差 <5%，模式切换/重组开销 <5%。",
"L3 原型与系统：可综合 RTL、Chipyard + FireSim/U250 原型、软件栈；端到端相对基线 ≥1.3×（目标），并给出同面积 Pareto 与适用边界。",
"三个论文点：① 高精度侧 Ozaki 低精度模拟；② 低精度侧物理可动态重组数据通路；③ FireSim + U250 系统验证。"]),
("2.主要研究内容、需要解决的关键理论问题或技术问题",
["（1）论文点 1：高精度侧 Ozaki 低精度模拟。目标 >8 bit（FP16/BF16/FP32/FP64）；以 INT8 为主基，研究模数集/分解次数 s 的选择、尺度不变缩放、CRT 重构、精度合同（EXACT/BOUNDED/FAST）与守卫；在双模上下文中与 R-mode 共享 INT8 tile、SRAM/NoC 与舍入资源；补同面积原生 FP32/FP64 对照。",
"（2）论文点 2：低精度侧物理可动态重组数据通路。目标 ≤8 bit（INT8/FP8/FP6/FP4/INT4）；设计 BSP lane（8×8 乘法器由 4 个 4×4 切片组成）与 16×16 子阵列；子阵列可按 1×1/2×1/2×2/4×4 组合；格式前端/指数/舍入按原生格式工作，不做格式转换、不用一种格式逼近另一种；研究 tile 级配置、时钟/电源门控、碎片与重组开销。",
"（3）论文点 3：FireSim + Alveo U250 系统验证。用 Chipyard 生成 Rocket/BOOM + ODA 的 SoC；U250 用 32×32/16×16 缩比阵列（完整 128×128 约 16K MAC，资源放不下），全尺寸用 FireSim/ASIC 综合；验证双模切换、子阵列组合、精度合同回读、端到端收益与同面积 Pareto。",
"（4）双模统一层：格式/精度/形状 → 模式选择 → tile 组合 → 调度/存储/软件栈；研究空间分区 vs 时间复用、tile 边界与碎片、O-mode 余数平面与 R-mode 原生 tile 的 SRAM/NoC 共存。",
"关键理论/技术问题：① 高精度侧最坏情况误差界与硬件守卫的完备性；② BSP lane 的 4×4 切片组合能否在 ≤1.2× 面积、1 GHz 下保留 INT8/FP4/FP8 原生语义；③ tile 级组合的碎片/重组开销能否 <5%；④ 给定混合负载，O/R 模式与 tile 组合的在线/编译期选择；⑤ U250 缩比与 128×128 全尺寸结论如何交叉验证。"]),
("3.工作方案（研究方法、技术路线等）及可行性分析",
["总体架构：ODA 由统一前端、可组合子阵列 Fabric（128×128 = 64 个 16×16 tile）、O-mode 通路（缩放/取模 → INT8 GEMM → CRT/舍入）、R-mode 通路（格式前端 → BSP MAC → 原生累加/舍入）与共享 SRAM/NoC/调度器组成（图 3）。",
"PE 粒度约定：1 个 PE = 1 个 BSP lane，128×128 = 16,384 PE = 64 tile × 256 PE/tile。PE 内含 4 个 4×4 乘法切片、A/B/乘积/部分和寄存器、模式 mux/移位/符号扩展、本地部分和/累加、符号/尾数前端；指数对齐/规格化/舍入/特殊值、权重/激活广播、归约树由 16×16 tile 共享；O-mode 时 PE 切 INT8 人格，FTU/CRT 在 tile/芯片级。该划分是 M1 综合前的设计假设，若共享单元成瓶颈可把指数单元下放到 lane group。",
"子阵列组合：tile 可组合为 1×1（16×16，小 GEMM/FP4 低延迟）、2×1（32×16，FP8）、2×2（32×32，INT8/O-mode）、4×4（64×64，大 GEMM）；格式人格在 kernel/tile 边界配置，clock/power gating，双缓冲权重/激活；不做格式转换（图 4）。",
"模式选择：>8 bit → O-mode；≤8 bit → R-mode；混合负载按层/GEMM 分流，tile 不足时时间复用；以“计算 + 变换 + 重组 + 存储”总代价选择模式与 tile 组合；精度合同优先分配 O-mode 守卫资源。",
"技术路线：模型 → 模拟 → RTL → FPGA/系统四条线迭代。先用 Python 建立格式×模式×tile×工艺模型，复现文献数字、标定 a32/a64；再用周期级模拟器验证数据流/双缓冲/重组；随后实现 BSP lane、tile、Fabric、FTU/CRT 与双模调度器，用 Verilator 对 MPFR；最后用 Chipyard + FireSim/U250 跑 BLAS 库与 LLM/CNN/科学计算负载，做同面积/端到端评估（图 5）。",
"详细实验计划：上一版《开题报告 v1.3》作为本课题的《实验计划 v1.3》，含 36 个月实验矩阵、RTL/综合/U250 里程碑、前期数据与风险；本节只给总体路线，具体实验（E1–E7）以该附件为准。",
"可行性：① 算法侧已完成 Ozaki-I/II 代价模型、三基 pass 数复核与 OzCore artifact CPU 复现；② 硬件侧已有 TSMC 28 nm HPC+ 的 INT8/FP8/FP4 MAC 与 128×128 阵列数据：INT8 378.13 µm²/0.366 pJ、阵列 5.903 mm²/1.800 W（8×8 tile 实测 + 256 tile 组合），FP8 619.42 µm²/0.315 pJ、FP4 551.25 µm²/0.200 pJ；③ EDA 侧有 DC/VCS/TSMC 28 nm 与 ASAP7/OpenROAD 备选；④ 系统侧已有 Chipyard/FireSim 软件环境与 Alveo U250；⑤ 风险有 Plan B：BSP 面积/时序超预算则退回“INT8 tile + FP4 tile 分离”的粗粒度方案；a64 不足则转 FP32-first/能效/负结果论文；U250 资源不足则 16×16 缩比 + FireSim 全尺寸。"]),
("4.创新性",
["论文点 1：把 Ozaki-II 高精度模拟放进双模架构，用精度合同/守卫/统计把“选 s”升级为可验证合同；相对 OzCore 增加应用级语义、与低精度侧共享 tile/存储、同面积原生对照。",
"论文点 2：提出 BSP lane + 16×16 tile 的粗粒度物理重组：4×4 切片物理组合、tile 级格式人格、1×1/2×1/2×2/4×4 子阵列组合；相对 Bitfusion/Stripes/BitWave 的位级/位串行方案，保留低精度原生语义与峰值；相对格式融合，降低面积税/空闲并支持双模共享。",
"论文点 3：用 Chipyard + FireSim/U250 验证双模切换、子阵列组合、精度回读与同面积收益；相对 OzCore（无 CPU+加速器原型）和多数融合架构（kernel/模拟级）补上系统级证据。",
"表述边界：不使用“首个/首次”作为无条件主张；新颖性限定在“据我们所知 + 可综合 RTL + 同面积/系统证据”的组合上；Ozaki 算法、Bitfusion/Stripes 等已有工作不重复声明。"]),
]

SEC4 = [
"4.1 应具备的条件",
"完成本课题需要：多格式 GEMM/体系结构/数值分析基础；Python/C++ 建模能力；Verilog/SystemVerilog 与 Verilator/DC/VCS 流程；TSMC 28 nm 标准单元库与 EDA 资源；Chipyard/FireSim 环境与 Alveo U250；以及导师课题组在体系结构、EDA、数值分析方向的指导。",
"4.2 已具备的条件",
"① 文献/算法：OzCore、Ozaki-II、FP8/FP4 变体、fast scaling 已精读；完成三基 pass 数复核、等精度成本模型与 OzCore artifact 的 CPU-only 复现（Table 2/4/5/6、Fig 2/3/5/10–16；Table 2 差 ≤0.003，Table 5/6 一致）。② 硬件/EDA：TSMC 28 nm HPC+ FF、DC/VCS；P0/P0b INT8 MAC 378.13 µm²/0.366 pJ；FP8/FP4 MAC 619.42/551.25 µm²；128×128 阵列 INT8 5.903 mm²/1.800 W、FP8 10.765/1.549、FP4 9.633/0.982（tile 实测 + 组合；功耗为模型值）。③ 系统：Chipyard/FireSim 软件环境与 Alveo U250；④ 团队：体系结构/EDA/数值分析指导；⑤ 计算资源：Linux 服务器、Python/C++ 模型、EDA VM。",
"4.3 可能遇到的困难与问题和解决措施",
"① BSP lane 面积/时序超预算：先用 TSMC 28 nm 综合 BSP/原生 INT8/FP4 tile；若 >1.3× 或 CP 不收敛，退回 tile 级分离（INT8/FP4 独立 tile）、缩小切片或降低频率。② a64/a32 标定不确定：用 ASAP7/OpenROAD 与 TSMC 28 nm 双口径给区间；若 a64 < s(1+η)，转 FP32-first/能效/负结果论文。③ tile 碎片/重组开销：tile 边界对齐、2×2 为主、批处理/同格式分组；若 >10% 简化组合。④ U250 资源/时序：16×16 缩比 + FireSim 全尺寸/分块；提前资源估算。⑤ 精度/特殊值：限定有限非特殊值，NaN/Inf/饱和检测+回退；差分测试 + 黄金模型。⑥ 范围蔓延：三个论文点收敛，FP6/FP8 增量实现，先 INT8/FP4。",
]

PLAN = [
("2026.11—2027.01","文献/格式刻画；OzCore/融合架构基线；代价模型骨架；Chipyard/FireSim 环境。","阅读笔记；oda_model v0.1；基线报告。"),
("2027.02—2027.04","BSP lane/tile RTL 与 TSMC 28 nm 综合；O-mode 模数/s 模型；a32/a64 综合。","BSP 面积/时序；O-mode 模型；Go/No-Go。"),
("2027.05—2027.07","16×16 Fabric/组合 RTL；双模调度器；周期级模拟器 v0.1。","Fabric RTL；模拟器；组合规则。"),
("2027.08—2027.10","FTU/CRT/精度合同/守卫；BSP 功能验证；Verilator/MPFR。","O-mode RTL；合同 API；验证报告。"),
("2027.11—2028.01","双模集成；SRAM/NoC/调度；小规模综合。","集成 RTL；综合/功耗报告。"),
("2028.02—2028.04","Chipyard SoC + FireSim/U250 缩比；软件栈；BLAS 库。","原型；库 v0.1；系统 demo。"),
("2028.05—2028.07","U250 系统 bring-up；双模切换/组合/精度回读；首篇论文。","系统结果；论文投稿。"),
("2028.08—2028.10","全尺寸 FireSim/分块；LLaMA/CNN/科学计算；同面积评估。","应用结果；Pareto 报告。"),
("2028.11—2029.01","第二篇论文；系统/工具论文；artifact 整理。","论文；artifact v1。"),
("2029.02—2029.04","结果复核；学位论文撰写；补实验。","学位论文初稿。"),
("2029.05—2029.07","论文修改；答辩准备；最终实验。","答辩材料；定稿候选。"),
("2029.08—2029.10","答辩；最终提交。","学位论文定稿；答辩。"),
]

REFS = [
"J. Park, J. Lee, H. Lee, J. Kim, J. Kim, J.-J. Kim. OzCore: An Ozaki-Scheme-II-Based GEMM Architecture for Unified Integer and Floating-Point Computation. MICRO 2026.",
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
"P. Judd, et al. BitWave: Exploiting Column-Based Bit-Level Sparsity for Deep Learning Acceleration. HPCA 2020.",
"V. Sze, et al. Efficient Processing of Deep Neural Networks: A Tutorial and Survey. Proceedings of the IEEE, 2017.",
"IEEE. IEEE Standard for Floating-Point Arithmetic (IEEE 754-2019). 2019.",
"OpenROAD / ASAP7. Open-source RTL-to-GDS flow and predictive 7 nm PDK. 2018–2026.",
"H. Esmaeilzadeh, et al. Neural Acceleration for General-Purpose Approximate Programs. MICRO 2012.",
]

def add_para(cell, text, size=12, bold=False):
    p = cell.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    r.font.name = "宋体"
    r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), "宋体")
    r.font.size = Pt(size); r.bold = bold
    _set_para_mark(p, size)

def fill_cell(cell, paras, size=12):
    cell.text = ""
    first = True
    for text in paras:
        if first:
            p = cell.paragraphs[0]; first = False
        else:
            p = cell.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(text)
        r.font.name = "宋体"
        r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), "宋体")
        r.font.size = Pt(size)
        if text[:2] in ("1.", "2.", "3.", "4.") or text[:2] in ("（1", "（2", "（3", "（4"):
            r.bold = True
        _set_para_mark(p, size)

def add_fig(cell, path, caption, width=11.4):
    p = cell.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Cm(width))
    cp = cell.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(5)
    r = cp.add_run(caption); r.font.name = "宋体"
    r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), "宋体")
    r.font.size = Pt(10.5)
    _set_para_mark(cp, 10.5)

def set_table_width(t, widths):
    # use 100% of the text column, with proportional column widths; this avoids
    # LibreOffice extending fixed twip tables past the right margin.
    total = sum(widths)
    widths = [w * 12.2 / total for w in widths]
    t.autofit = False; t.allow_autofit = False; t.alignment = WD_TABLE_ALIGNMENT.LEFT
    tblPr = t._tbl.tblPr
    tblW = tblPr.find(qn('w:tblW'))
    if tblW is None:
        tblW = OxmlElement('w:tblW'); tblPr.append(tblW)
    tblW.set(qn('w:w'), str(int(12.2 * 567))); tblW.set(qn('w:type'), 'dxa')
    ind = tblPr.find(qn('w:tblInd'))
    if ind is not None:
        ind.set(qn('w:w'), '0')
    layout = tblPr.find(qn('w:tblLayout'))
    if layout is None:
        layout = OxmlElement('w:tblLayout'); tblPr.append(layout)
    layout.set(qn('w:type'), 'fixed')
    for ci, w in enumerate(widths):
        t.columns[ci].width = Cm(w)
        for row in t.rows:
            row.cells[ci].width = Cm(w)
    for row in t.rows:
        for cell in row.cells:
            _set_cell_margins(cell)
            mar = cell._tc.tcPr.find(qn('w:tcMar'))
            if mar is not None:
                right = mar.find(qn('w:right'))
                if right is not None:
                    right.set(qn('w:w'), '120')
        try: row.allow_break_across_pages = True
        except Exception: pass

def main():
    d = Document(TEMPLATE)
    # remove empty spacer paragraphs (but keep ones carrying page breaks)
    for p in list(d.paragraphs):
        if not p.text.strip() and not p._p.xpath('.//w:br'):
            p._element.getparent().remove(p._element)
    # cover
    t = d.tables[0]
    t.rows[0].cells[0].text = ""
    lines = ["论文题目：面向多格式 AI 计算的可重构—Ozaki", "双模加速器关键技术研究"]
    for j, line in enumerate(lines):
        p = t.rows[0].cells[0].paragraphs[0] if j == 0 else t.rows[0].cells[0].add_paragraph()
        p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(line); r.font.name = "仿宋"
        r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), "仿宋")
        r.font.size = Pt(15.5)
    cover_fields = [
        "姓    名：________        学号：________",
        "学科专业：计算机科学与技术",
        "研究方向：计算机体系结构 / 多格式矩阵计算",
        "指导教师：________        职称：________",
        "协助指导教师：________  职称：________",
        "学    院：________",
        "开题时间：2026 年 11 月    日",
    ]
    for i, v in enumerate(cover_fields, start=1):
        cell = t.rows[i].cells[0]; cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(v); r.font.name = "仿宋"
        r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), "仿宋")
        r.font.size = Pt(15)
    # date/university
    for p in d.paragraphs:
        if "二〇二六年四月" in p.text:
            p.text = "二〇二六年十一月"
    for root in (d.element.body,):
        for node in root.iter(qn('w:t')):
            if node.text and node.text.strip() == "科技大学":
                node.text = "国防科技大学"
            elif node.text and node.text.strip() == "科技大学研究生院制":
                node.text = "国防科技大学研究生院制"
    for sec in d.sections:
        for root in (sec.header._element, sec.footer._element):
            for node in root.iter(qn('w:t')):
                if node.text and node.text.strip() == "科技大学":
                    node.text = "国防科技大学"
    # section 1
    fill_cell(d.tables[1].rows[0].cells[0], SEC1)
    add_fig(d.tables[1].rows[0].cells[0], os.path.join(FIG, "fig1_peak_ratio.png"),
            "图 1  低精度峰值相对 FP64 的倍数（公开规格示意）")
    # section 2
    fill_cell(d.tables[2].rows[0].cells[0], SEC2)
    add_fig(d.tables[2].rows[0].cells[0], os.path.join(FIG, "fig2_ozaki_flow.png"),
            "图 2  Ozaki-II 分解与 CRT 重构流程")
    # section 3
    t3 = d.tables[3]
    while len(t3.rows) < len(SEC3):
        t3.add_row()
    for i, (head, paras) in enumerate(SEC3):
        cell = t3.rows[i].cells[0]
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(head); r.bold = True
        r.font.name = "宋体"; r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), "宋体")
        r.font.size = Pt(12); p.paragraph_format.space_after = Pt(3)
        _set_para_mark(p, 12)
        for txt in paras:
            add_para(cell, txt)
        if i == 2:
            add_fig(cell, os.path.join(FIG, "fig3_oda_arch.png"), "图 3  ODA 双模加速器总体架构")
            add_fig(cell, os.path.join(FIG, "fig4_subarray.png"), "图 4  子阵列组合：同一 Fabric 适配不同格式/GEMM 形状")
            add_fig(cell, os.path.join(FIG, "fig5_roadmap.png"), "图 5  36 个月技术路线与里程碑")
    # section 4
    fill_cell(d.tables[4].rows[0].cells[0], SEC4)
    # plan table
    t5 = d.tables[5]
    while len(t5.rows) < len(PLAN) + 1:
        t5.add_row()
    while len(t5.rows) > len(PLAN) + 1:
        t5._tbl.remove(t5.rows[-1]._tr)
    for i, (dates, content, result) in enumerate(PLAN, start=1):
        for j, v in enumerate([dates, content, result]):
            cell = t5.rows[i].cells[j]; cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
            r = p.add_run(v); r.font.name = "宋体"
            r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), "宋体")
            r.font.size = Pt(10.5)
    # note after plan table
    note = d.add_paragraph()
    note.paragraph_format.space_before = Pt(4); note.paragraph_format.space_after = Pt(4)
    r = note.add_run("注：详细实验计划（E1–E7 实验矩阵、RTL/综合/U250 里程碑、前期数据与风险）见附件《实验计划 v1.3》（即上一版报告）。")
    r.font.name = "宋体"; r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), "宋体")
    r.font.size = Pt(10.5)
    t5._tbl.addnext(note._p)
    # refs
    t6 = d.tables[6]
    while len(t6.rows) < len(REFS) + 1:
        t6.add_row()
    while len(t6.rows) > len(REFS) + 1:
        t6._tbl.remove(t6.rows[-1]._tr)
    for i, ref in enumerate(REFS, start=1):
        cells = t6.rows[i].cells
        cells[0].text = str(i); cells[1].text = ""
        p = cells[1].paragraphs[0]
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
        r = p.add_run(ref); r.font.name = "宋体"
        r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), "宋体")
        r.font.size = Pt(10.5)
    d.tables[7].rows[0].cells[0].text = "（由导师填写）"
    # each major section starts on a new page
    for para in d.paragraphs:
        if para.text.strip().startswith(("一、","二、","三、","四、","五、","六、","七、")):
            para.paragraph_format.page_break_before = True
    # widths
    set_table_width(d.tables[0], [14.6])
    set_table_width(d.tables[1], [14.6])
    set_table_width(d.tables[2], [14.6])
    set_table_width(d.tables[3], [14.6])
    set_table_width(d.tables[4], [14.6])
    set_table_width(d.tables[5], [3.1, 8.2, 3.3])
    set_table_width(d.tables[6], [0.9, 13.7])
    set_table_width(d.tables[7], [14.6])
    # keep template margins (3.0 cm) but avoid table overflow by 14.6 < 15.0
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
        for dates, content, result in PLAN:
            f.write(f"| {dates} | {content} | {result} |\n")
        f.write("\n详细实验计划见附件《实验计划 v1.3》。\n\n")
        f.write("## 六、主要参考文献\n\n")
        for i, ref in enumerate(REFS, 1):
            f.write(f"{i}. {ref}\n")
        f.write("\n## 七、导师评语\n\n（由导师填写）\n")
    print("saved", OUT_DOCX, OUT_MD)

if __name__ == "__main__":
    main()
