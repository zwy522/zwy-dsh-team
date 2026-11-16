#!/usr/bin/env python3
"""Ozaki I vs Ozaki II: pass counts, time breakdown and GEMM cost.

Theory follows Ozaki, Uchino, Imamura, "Ozaki Scheme II" (2026):
  Ozaki I : k slices, fast mode Q_I = k(k+1)/2 GEMMs;
  Ozaki II: s moduli, Q_II = s GEMMs, CRT reconstruction.

The model is deliberately simple and transparency-first: it counts GEMMs
and element-wise / CRT / memory work, then converts to cycles with a
configurable 128x128 INT8 array (16384 MACs/cycle). It is a relative
analysis, not a calibrated chip simulator.
"""
from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass, asdict

import numpy as np

PRECISIONS = {"BF16": 8, "FP16": 11, "FP32": 24, "FP64": 53}
SLICE_BITS = 8
SLICE_GUARD = 6       # k = ceil((B + 6) / 8); calibrated to paper's 7-8 slices at FP64
MOD_BITS = 8
MOD_GUARD = 10        # s = ceil((2B + 10) / 8); conservative vs paper's 16 at FP64

@dataclass
class CostConfig:
    macs_per_cycle: int = 128 * 128     # 128x128 INT8 array
    freq_ghz: float = 1.0
    elem_ops_per_cycle: int = 128       # scaling / split / residue
    crt_ops_per_cycle: int = 16         # wide integer mul-add per output per modulus
    bytes_per_cycle: int = 256          # HBM/SRAM streaming budget
    bytes_slice: int = 1                # INT8 residue/slice
    bytes_product: int = 4              # INT32/FP32 partial product

def ozaki1(B: int) -> dict:
    k = math.ceil((B + SLICE_GUARD) / SLICE_BITS)
    q = k * (k + 1) // 2
    return {"k": k, "Q": q, "pre_ops": 2 * k, "post_ops": 2 * q,
            "mem_planes": 2 * k, "mem_products": q}

def ozaki2(B: int) -> dict:
    s = math.ceil((2 * B + MOD_GUARD) / MOD_BITS)
    return {"s": s, "Q": s, "pre_ops": 2 * s, "post_ops": s,
            "mem_planes": 2 * s, "mem_products": s}

def cost_row(B: int, K: int, cfg: CostConfig, which: str) -> dict:
    m = ozaki1(B) if which == "I" else ozaki2(B)
    q = m["Q"]
    macs = q * (K ** 3)
    gemm_cycles = macs / cfg.macs_per_cycle
    pre_cycles = m["pre_ops"] * (K ** 2) / cfg.elem_ops_per_cycle
    if which == "I":
        post_cycles = m["post_ops"] * (K ** 2) / cfg.elem_ops_per_cycle
    else:
        post_cycles = m["post_ops"] * (K ** 2) / cfg.crt_ops_per_cycle + (K ** 2) / cfg.elem_ops_per_cycle
    mem_bytes = m["mem_planes"] * (K ** 2) * cfg.bytes_slice + m["mem_products"] * (K ** 2) * cfg.bytes_product
    mem_cycles = mem_bytes / cfg.bytes_per_cycle
    total = gemm_cycles + pre_cycles + post_cycles + mem_cycles
    out = dict(which=which, B=B, K=K, **m,
                gemm_cycles=gemm_cycles, pre_cycles=pre_cycles,
                post_cycles=post_cycles, mem_cycles=mem_cycles,
                total_cycles=total,
                gemm_pct=100*gemm_cycles/total,
                pre_pct=100*pre_cycles/total,
                post_pct=100*post_cycles/total,
                mem_pct=100*mem_cycles/total,
                total_ns=total/cfg.freq_ghz,
                macs=macs, mem_bytes=mem_bytes)
    out.setdefault("k", None); out.setdefault("s", None)
    return out

def verify_paper_counts() -> list[dict]:
    rows = []
    for k in range(2, 11):
        rows.append({"k": k, "Q_I": k*(k+1)//2, "Q_II_same_k": k})
    return rows

def verify_moduli() -> dict:
    # paper's INT8 moduli set (example, s=16)
    moduli = [256, 255, 253, 251, 247, 239, 233, 229, 227, 223, 217, 211, 199, 197, 193, 191]
    M = math.prod(moduli)
    bits = math.log2(M)
    q = 1024
    k_eff = math.floor(math.log2((M/2 - 1) / q))
    return {"s": len(moduli), "M_bits": bits, "k_eff_q1024": k_eff}

def main():
    os.makedirs("results", exist_ok=True)
    cfg = CostConfig()
    rows = []
    for B in PRECISIONS.values():
        for K in (1024, 4096, 16384):
            for which in ("I", "II"):
                rows.append(cost_row(B, K, cfg, which))
    # summary at K=4096
    summary = [r for r in rows if r["K"] == 4096]
    keys = list(summary[0].keys())
    with open("results/cost_summary_k4096.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(summary)
    allkeys = list(rows[0].keys())
    with open("results/cost_by_k.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=allkeys); w.writeheader(); w.writerows(rows)
    vrows = verify_paper_counts()
    with open("results/verify_counts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(vrows[0].keys())); w.writeheader(); w.writerows(vrows)
    vmod = verify_moduli()
    print("=== pass counts and time at K=4096 (cycles, ns; 1 GHz) ===")
    print(f"{'B':>4} {'fmt':>5} {'Q':>3} {'gemm%':>7} {'pre%':>6} {'post%':>7} {'mem%':>6} {'total ns':>10}")
    for r in summary:
        fmt = [k for k,v in PRECISIONS.items() if v==r["B"]][0]
        print(f"{r['B']:4d} {fmt:>5} {r['Q']:3d} {r['gemm_pct']:7.1f} {r['pre_pct']:6.1f} {r['post_pct']:7.1f} {r['mem_pct']:6.1f} {r['total_ns']:10.1f}")
    print("paper Table 2 check Q_I(k):", [v["Q_I"] for v in vrows])
    print("moduli check:", vmod)

if __name__ == "__main__":
    main()
