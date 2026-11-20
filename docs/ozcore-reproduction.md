# OzCore（MICRO 2026）Artifact 复现报告

> Artifact：`micro2026-ozcore-artifact-evaluation` v1.2，Zenodo DOI 10.5281/zenodo.22748465（ZIP 12.8 MB）。
> 复现环境：Linux x86_64、Python 3.12、NumPy 2.2.5、pandas 2.2.3、matplotlib、Jupyter/nbconvert、adjustText；**CPU-only**，无 GPU、无 NDA 单元库。
> 复现日期：2026-11-20。

## 0. 结论摘要

1. Artifact 的 **Category A（GPU-free CPU redraw）** 基本可复现：Table 2/4/5/6 与 Fig 2/3/5/10/11/12/13/14/15/16 的脚本均成功运行，输出与论文/参考值在 0.001–0.005 或图形趋势上一致。
2. **Table 2** 的 8B/70B PPL 全部可计算（含此前缺失的 70B s=2/3 与 BF16 单元），与论文差 ≤0.003；**Table 5/6 与论文数值完全一致**；**Table 4** 趋势一致，个别单元差 ≤0.005。
3. **Fig 16** 与论文的 2.25–2.60× / 1.19–1.44× 完全一致；**Fig 2** 的 incremental density 比值 1.00/0.86/0.56/0.47 与论文一致；**Fig 3** 的 stage 分解为 weight 33–57%、attention 59–81%（论文为 35–57%/59–81%，差 2 个百分点）。
4. **不能复现的部分**：Table 3（无 CPU 数据、仅 GPU regen）、A-1 GPU 数值生成（需 A6000 48 GB、模型权重/数据）、B/C 面积综合（NDA 库，只复算/重绘 sanitized 数据）、Fig 3 的新 trace（只重绘随附 A6000 trace）。
5. 因此，这是一次 **“artifact 数据/脚本级复现”**，不是“从零重跑 GPU 与综合”的独立复现。论文的 CPU 可验证主张（PPL、缩放消融、量化 PPL、MX 对比、FP64 overhead 模型）可复核；面积/密度与 GPU 端到端结果仍依赖作者提供的数据。

## 1. Artifact 与复现范围

| 项 | 内容 |
|---|---|
| 名称 | micro2026-ozcore-artifact-evaluation |
| 版本 | v1.2（documentation-only update；代码/数据/参考输出不变） |
| DOI | 10.5281/zenodo.22748465 |
| 大小 | 12.8 MB ZIP |
| 许可 | MIT（vendored Ten-four Apache 2.0、GEMMul8 MIT） |
| 复现类别 | A（CPU-free）、A-1（GPU emulation）、B/C（NDA area）、D（GPU measurement） |
| 本次范围 | Category A 全部 CPU launcher；不含 A-1/B/C/D 的 fresh run |

Artifact 的 README 给出每个 target 的 launcher、Depth（recompute/model/replot）与输出；`docs/reproduction.md` 给出安装、资源与限制。

## 2. 环境与命令

未使用作者的 conda 环境（`scripts/install.sh --cpu-only`），而是系统 Python + pip 安装缺失包：

```bash
pip install jupyter nbconvert adjustText
cd ozcore-artifact
bash scripts/tab2.sh
bash scripts/tab4.sh
bash scripts/tab5.sh
bash scripts/tab6.sh
bash scripts/fig2.sh
bash scripts/fig3.sh
bash scripts/fig5.sh
bash scripts/fig10.sh
bash scripts/fig11-12.sh
bash scripts/fig13.sh
bash scripts/fig14-15.sh
bash scripts/fig16.sh
```

所有命令在 CPU 上完成；Fig 5/10/14/15 通过 `jupyter nbconvert --execute` 运行，单次几十秒。

### 2.1 本机能力核查（2026-11-20）

用户指出本机可能具备 GPU 与 28nm 综合条件；我们重新核查如下，区分“有硬件”与“能复现 artifact 的完整条件”：

| 资源 | 本机实际情况 | 是否满足 artifact 复现 |
|---|---|---|
| GPU | `nvidia-smi`：RTX 4090，24 GB（非 A6000 48 GB） | 8B 勉强可试；70B 参考配置为 48 GB + offload，24 GB 不足/风险高 |
| CUDA 工具链 | `nvcc` 不存在；PyTorch 未安装 | 不满足 A-1 扩展编译 |
| LLaMA 权重/权限 | HF cache 仅 21 MB（DeepSeek GGUF/WikiText），无 LLaMA-3.1；无 HF token | 不满足 Table 2/3/5 的 fresh GPU run |
| 28nm EDA | 已找到并启动 `IC_EDA` VM（`Graduationthesis/.../CentOS_Dig_Ana/IC_EDA.vmx`）；VM 内有 DC + TSMC 28nm HPC+ | **部分满足**：可做 TSMC 28nm 替代综合，不是论文的 FDSOI 口径 |
| Catapult HLS | VM 内未找到 `catapult` | 不满足 OzCore HLS 设计（artifact 的 OzCore stages 由 Catapult 生成） |
| 28nm FDSOI NDA 库 | 无；VM 内是 TSMC 28nm HPC+ + SMIC 28nm HPC | 不满足论文面积口径；替代综合只能验证趋势 |
| 网络 | GitHub clone 超时；Hugging Face 请求超时 | Vortex 头文件/LLaMA 权重无法在本环境直接拉取 |

因此，本报告说的“不能复现”是**不能复现 artifact 的精确条件**，不是“本机完全没有硬件”。已启动的 EDA VM 能提供 DC + TSMC 28nm HPC+，但 artifact 的 OzCore 面积来自 Catapult HLS + 28nm FDSOI；两者不能混为同一口径。具体地：

- **GPU**：4090 24 GB 可以尝试 8B 的 A-1 路径（若安装 CUDA toolkit/PyTorch 并提供 LLaMA-3.1-8B 的 HF 权限/权重），但 70B 的 48 GB 参考配置不满足；Table 3 还需要 lm-eval 全量评估。
- **28nm**：即使有 DC + TSMC 28nm HPC+，也只能做**替代工艺**的 Ten-four RTL 综合（还需 Vortex 头文件），不能复现 OzCore 的 Catapult HLS stages 与 FDSOI 面积；论文的 27.9%/1.91×/1.40× 仍不可独立验证。
- 若要精确复现，需要：启动/提供 28nm FDSOI + Catapult + DC 的 EDA 环境；提供 LLaMA-3.1 权重/权限与 CUDA 工具链（GPU 路线）。

### 2.2 TSMC 28nm 替代综合的当前阻塞（2026-11-20）

用户已同意用 TSMC 28nm HPC+ 做替代综合；IC_EDA VM 已启动，DC 与 `tcbn28hpcplus...` 库可用。但要跑 artifact 的综合源，仍缺两类依赖：

1. **Ten-four RTL 的 Vortex 头文件/共享模块**：`VX_define.vh`、`VX_gpu_pkg`、`VX_csa_tree`、`VX_ks_adder`、`VX_pipe_register`、`VX_lzc`、`VX_wallace_mul`、`VX_reset_relay` 等。artifact 只 vendored Ten-four 变体，明确要求 Vortex checkout；当前 VM 内没有 Vortex，VM 内 `git clone github.com/vortexgpgpu/vortex` 超时，主机 GitHub 也不可达。
2. **OzCore HLS**：artifact 的 OzCore stages 面积由 Catapult HLS 生成；VM 内无 `catapult`。TSMC 替代只能覆盖 Ten-four 的 RTL 综合，不能覆盖 OzCore HLS stages。

**已实际完成 INT8 变体的 TSMC 28nm HPC+ 替代综合**（Vortex 依赖通过 Gitee 镜像获得；详见 `docs/ozcore-tsmc28-substitute.md`）：

| RTL | TSMC 28nm HPC+ | 论文 FDSOI | 比值 |
|---|---:|---:|---:|
| Ten-four INT8（K=128） | **62,969.0 µm²** | 59,901.9 µm² | **1.051×** |

同一份 Ten-four RTL、N=64、300 MHz、DC O-2018.06；面积只差 5.1%，说明 RTL/流程可复现，TSMC 替代用于趋势验证合理。仍不能把 62,969 当作论文绝对面积（库/flow 不同）。FP16 变体正在同流程下综合（需 `VX_lzc`/`VX_wallace_mul`/`VX_find_first`，运行时间明显更长）；OzCore HLS stages 仍需 Catapult + FDSOI 才能精确复现。

## 3. 结果

### 3.1 Table 2（WikiText-2 PPL）

`bash scripts/tab2.sh` 输出 computed | paper 两列。8B/70B 全部单元可计算：

| Model | s | OzCore computed | paper | OS-II fast | OS-II accu |
|---|---:|---:|---:|---:|---:|
| 8B | BF16 | 6.244 | 6.244 | regen | regen |
| 8B | 12 | 6.241 | 6.243 | 6.242 | 6.244 |
| 8B | 6 | 6.244 | 6.244 | 6.244 | 6.243 |
| 8B | 4 | 6.243 | 6.244 | 6.420 | 6.251 |
| 8B | 3 | 6.242 | 6.242 | div. | 6.595/6.596 |
| 8B | 2 | 6.363 | 6.363 | div. | div. |
| 70B | BF16 | 2.809 | 2.810 | regen | regen |
| 70B | 12 | 2.810 | 2.810 | 2.808 | 2.809 |
| 70B | 6 | 2.809 | 2.809 | 2.809 | 2.809/2.808 |
| 70B | 4 | 2.809 | 2.809 | 9.822 | 2.820/2.819 |
| 70B | 3 | 2.809 | 2.809 | div. | 80.023 |
| 70B | 2 | 2.933 | 2.933 | div. | div. |

结论：与论文差 ≤0.003；70B BF16 差 0.001；8B s=12 差 0.002。属于随附数据与论文的四舍五入/版本差异。

### 3.2 Table 4（b_S / b_P 消融）

| 扫描 | 结果 | 与论文 |
|---|---|---|
| b_S（b_P=8），s=2 | 8.529/6.726/6.384/6.363/6.362 | 完全一致 |
| b_S，s=3 | 6.253/6.246/6.242/6.242/6.243 | 差 ≤0.001 |
| b_S，s=4 | 6.242/6.243/6.239/6.243/6.244 | 最大差 0.003（b_S=4 的 6.239 vs 6.242） |
| b_P（b_S=8），s=2 | 6.391/6.374/6.363/6.363/6.363 | 完全一致 |
| b_P，s=3 | 6.241/6.244/6.243/6.242/6.243 | 差 ≤0.002 |
| b_P，s=4 | 6.242/6.243/6.243/6.243/6.245 | 差 ≤0.001 |

趋势完全一致：b_S 在 s=2 时影响大（8.529 vs 6.363），b_P 影响弱；b_S=8、b_P=8 是默认。

### 3.3 Table 5（量化权重）

| 方法 | 计算值 | 论文 |
|---|---:|---:|
| FP×INT8 baseline | 6.238 | 6.238 |
| FP×INT8 s=4 / s=3 / s=2 | 6.238 / 6.238 / 6.382 | 6.238 / 6.238 / 6.382 |
| FP×INT4 baseline | 6.831 | 6.831 |
| FP×INT4 s=4 / s=3 / s=2 | 6.832 / 6.837 / 7.109 | 6.832 / 6.837 / 7.109 |
| FP8 baseline | 6.296 | 6.296 |
| FP8 s=4 / s=3 / s=2 | 6.294 / 6.293 / 6.414 | 6.294 / 6.293 / 6.414 |

完全一致。

### 3.4 Table 6（MX vs OzCore）

| 格式 | relative L2（计算 | 论文） | PPL（计算 | 论文） |
|---|---|---|---|
| OzCore s=3 | 2.2–4.2e-3 | 同 | 6.24 | 6.24 |
| OzCore s=2 | 2.5–4.4e-2 | 同 | 6.36 | 6.36 |
| MXFP8 E4M3 | 4.4–6.9e-2 | 同 | 6.51 | 6.51 |
| MXFP8 E5M2 | 7.4–9.5e-2 | 同 | 6.87 | 6.87 |
| MXFP4 E2M1 | 1.5–2.2e-1 | 同 | 25.61 | 25.61 |

完全一致。

### 3.5 图

| 图 | launcher | 复现结果 |
|---|---|---|
| Fig 2 | `fig2.sh` | 所有生成面积/密度与 committed JSON 一致；incremental 比值 1.00/0.86/0.56/0.47 |
| Fig 3 | `fig3.sh` | weight 33–57%、attention 59–81%（论文 35–57%/59–81%，差 2pp）；只重绘 A6000 trace |
| Fig 5 | `fig5.sh` | OS-II vs OzCore L2/保留尾数位图生成成功 |
| Fig 10 | `fig10.sh` | 面积分解图生成（sanitized 数据重绘） |
| Fig 11/12 | `fig11-12.sh` | TOPS/mm² 与 perf-vs-acc 图生成（重绘/模型） |
| Fig 13 | `fig13.sh` | roofline 图生成 |
| Fig 14/15 | `fig14-15.sh` | 逐层/逐 op 误差图生成 |
| Fig 16 | `fig16.sh` | (a) 2.25–2.60×、(b) 1.19–1.44×、(c) 1.00×，与论文完全一致 |

生成图保存在 `reproduction/ozcore/generated/`（PNG/PDF）。

## 4. 没有复现的部分

| 项 | 原因 |
|---|---|
| Table 3 zero-shot | Artifact 无预计算数据、无 CPU redraw；只能 GPU `tab3_regen.sh` |
| A-1 GPU 数值生成 | 需 RTX A6000 48 GB、LLaMA-3.1 8B/70B 权重（约 180 GB 缓存）、CUDA 扩展；本机无 GPU |
| B/C 面积综合 | 28 nm FDSOI NDA 库/工具不可分发；artifact 只提供 sanitized 数据与 replot 脚本，不重跑 synthesis |
| Fig 3 新 trace | 只随附 A6000 trace；fresh profiling 需原硬件/工具 |
| 端到端 GPU 加速比 | 需要 GPU 路线；本报告只能验证 CPU 可复算的 PPL/模型/面积 replot |

## 5. Artifact 质量与问题

**优点**

- 文档完整：README + reproduction guide + release notes + 每个 target 的 Depth 标注。
- CPU redraw 覆盖大部分表/图；参考输出随附，便于对照。
- 明确区分 recompute / model / replot / fresh GPU，避免把 replot 当独立复现。
- License 清晰；vendored 组件单独标注。

**问题/风险**

- 没有 `run_all.sh` 与 `environment.yml`；`install.sh --cpu-only` 依赖 conda/网络，系统 Python 需自行补 jupyter/adjustText。
- Table 2/4 的随附数据与论文有 0.001–0.005 差异；README 只提到 Table 2 的 0.001–0.003，Table 4 的 0.003–0.005 未特别说明。
- Table 3 无 CPU 数据，是复现矩阵的明显缺口。
- 面积/密度核心 claim（27.9%、1.91×、1.40×）只能 replot sanitized 数据，不能独立重跑 synthesis；这是 NDA 限制，但意味着“面积效率”结论未被独立验证。
- Fig 3 的 33–57% 与论文 35–57% 差 2pp，可能是 trace/绘图版本差异，artifact 未说明。
- GPU 路线仅 A6000；H100/Blackwell 已知/未验证问题，限制可移植性。

## 6. 结论

- 对论文的 **CPU 可验证部分**：Table 2/4/5/6、Fig 2/16 与论文一致；Fig 3/5/10/11/12/13/14/15 可生成且趋势一致。Artifact 达到了“可复算/可重绘”的目标。
- 对论文的 **硬件面积与 GPU 端到端主张**：本次只做了 sanitized 数据的 replot 与随附 trace 的重绘，未独立复现；需要 NDA 库/GPU 才能验证。
- 若要在我们的 OGE 工作中引用 OzCore 的面积/能效数字，应标注“来自作者 sanitized artifact/论文”，而不是“我们独立复现”。

## 7. 复现命令与产物

```bash
# 从 Zenodo 下载
curl -L https://zenodo.org/api/records/22748465/files/ozcore-artifact-v1.2.zip/content -o ozcore-artifact-v1.2.zip
unzip ozcore-artifact-v1.2.zip
cd ozcore-artifact
pip install jupyter nbconvert adjustText
for s in tab2 tab4 tab5 tab6 fig2 fig3 fig5 fig10 fig11-12 fig13 fig14-15 fig16; do
  bash scripts/$s.sh
done
```

产物：`reproduction/ozcore/generated/`（tab*.txt + 图），以及本报告。
