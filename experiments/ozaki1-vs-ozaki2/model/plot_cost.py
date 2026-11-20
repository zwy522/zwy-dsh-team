#!/usr/bin/env python3
"""Plot the Ozaki I/II cost model results."""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fp = font_manager.FontProperties(fname=FONT)
plt.rcParams["axes.unicode_minus"] = False
os.makedirs("results", exist_ok=True)

rows = list(csv.DictReader(open("results/cost_by_k.csv")))
fmt = {8: "BF16", 11: "FP16", 24: "FP32", 53: "FP64"}
colors = {"I": "#2f75b5", "II": "#c00000"}

# 1) Q vs precision
fig, ax = plt.subplots(figsize=(6.4, 3.6))
labels = [fmt[b] for b in (8, 11, 24, 53)]
qI = [int(next(r["Q"] for r in rows if int(r["B"]) == b and r["which"] == "I" and int(r["K"]) == 4096)) for b in (8, 11, 24, 53)]
qII = [int(next(r["Q"] for r in rows if int(r["B"]) == b and r["which"] == "II" and int(r["K"]) == 4096)) for b in (8, 11, 24, 53)]
x = range(len(labels)); w = 0.36
ax.bar([i - w/2 for i in x], qI, w, label="Ozaki I: k(k+1)/2", color=colors["I"])
ax.bar([i + w/2 for i in x], qII, w, label="Ozaki II: s", color=colors["II"])
for i, v in enumerate(qI): ax.text(i-w/2, v+0.5, str(v), ha="center", fontsize=9, fontproperties=fp)
for i, v in enumerate(qII): ax.text(i+w/2, v+0.5, str(v), ha="center", fontsize=9, fontproperties=fp)
ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontproperties=fp)
ax.set_ylabel("GEMM 次数 Q", fontproperties=fp); ax.set_title("不同精度下的 GEMM 次数", fontproperties=fp)
ax.legend(prop=fp); ax.grid(axis="y", alpha=0.3)
fig.tight_layout(); fig.savefig("results/fig_q_vs_precision.png", dpi=160); plt.close(fig)

# 2) total time vs K (per precision, two lines)
fig, axes = plt.subplots(2, 2, figsize=(9, 6.2))
for ax, b in zip(axes.ravel(), (8, 11, 24, 53)):
    for which in ("I", "II"):
        ks = sorted(int(r["K"]) for r in rows if int(r["B"]) == b and r["which"] == which)
        ts = [float(next(r["total_ns"] for r in rows if int(r["B"]) == b and r["which"] == which and int(r["K"]) == k))/1e6 for k in ks]
        ax.plot(ks, ts, marker="o", label=f"Ozaki {which}", color=colors[which])
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_title(fmt[b], fontproperties=fp); ax.set_xlabel("K", fontproperties=fp)
    ax.set_ylabel("总时间 (ms)", fontproperties=fp); ax.grid(alpha=0.3); ax.legend(prop=fp)
fig.suptitle("总时间随 K 的变化（1 GHz, 128×128 INT8）", fontproperties=fp)
fig.tight_layout(); fig.savefig("results/fig_time_vs_k.png", dpi=160); plt.close(fig)

# 3) breakdown at K=1024 and 4096
for K in (1024, 4096):
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    xs=[]; labels=[]; data={"GEMM":[], "变换":[], "重构/归约":[], "存储":[]}
    idx=0
    for b in (8, 11, 24, 53):
        for which in ("I", "II"):
            r=next(x for x in rows if int(x["B"])==b and x["which"]==which and int(x["K"])==K)
            xs.append(idx); labels.append(f"{fmt[b]}-{which}")
            for key, col in [("gemm_pct","GEMM"),("pre_pct","变换"),("post_pct","重构/归约"),("mem_pct","存储")]:
                data[col].append(float(r[key]))
            idx+=1
    bottom=[0]*len(xs)
    for col,c in zip(data, ["#2f75b5","#70ad47","#c00000","#a5a5a5"]):
        ax.bar(xs, data[col], bottom=bottom, label=col, color=c)
        bottom=[b+v for b,v in zip(bottom,data[col])]
    ax.set_xticks(xs); ax.set_xticklabels(labels, rotation=45, fontproperties=fp)
    ax.set_ylabel("时间占比 (%)", fontproperties=fp); ax.set_title(f"K={K} 的时间分解", fontproperties=fp)
    ax.legend(prop=fp); ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); fig.savefig(f"results/fig_breakdown_k{K}.png", dpi=160); plt.close(fig)
print("plots saved")
