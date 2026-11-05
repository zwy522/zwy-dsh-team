#!/usr/bin/env python3
"""Base-13 FP4 limb simulation (Ozaki-I variant) for pass-count calibration.

Inputs are random FP32 matrices. They are scaled to integers, decomposed into
base-13 limbs whose values are representable as doubled FP4 E2M1 values, and
reconstructed from p x q limb GEMMs. The relative L2 error vs the FP64 product
is measured as p=q grows. This calibrates how many FP4 GEMMs are needed for
BF16/FP16/FP32-equivalent accuracy; it is the Ozaki-I variant (OzII-FP4 uses
fewer moduli, so these counts are an upper bound).
"""

from __future__ import annotations

import csv
import math
import os
from typing import List

import numpy as np

TARGETS = {"bf16": 1e-2, "fp16": 1e-3, "fp32": 1e-6}


def gen(m: int, n: int, phi: float, rng: np.random.Generator) -> np.ndarray:
    exps = rng.uniform(-phi, phi, size=(m, n))
    return rng.standard_normal((m, n)) * np.exp2(exps)


def scale_pair(A: np.ndarray, B: np.ndarray, p: int):
    # Scale so the truncated integers fit the p-limb base-13 range
    # X_p = (13^p - 1) / 3; then the limb decomposition is exact and the
    # only error is the initial truncation.
    xp = (13 ** p - 1) // 3
    bits = max(1, math.floor(math.log2(xp)) - 1)
    mu = bits - math.floor(math.log2(float(np.max(np.abs(A))))) - 1
    nu = bits - math.floor(math.log2(float(np.max(np.abs(B))))) - 1
    return np.trunc(np.ldexp(A, mu)).astype(np.int64), np.trunc(np.ldexp(B, nu)).astype(np.int64), mu, nu


def limb(x: int) -> int:
    """Smallest-magnitude base-13 representative in the doubled FP4 value set.

    S_doubled = {0, +-1, +-2, +-3, +-4, +-6, +-8, +-12}; 5 and -5 are replaced
    by -8 and +8 respectively (same residue class mod 13).
    """
    r = x % 13
    c = r if r <= 6 else r - 13
    if c == 5:
        c = -8
    elif c == -5:
        c = 8
    return c


def decompose(M: np.ndarray, p: int) -> List[np.ndarray]:
    limbs = []
    X = M.copy()
    for _ in range(p):
        C = np.vectorize(limb)(X)
        limbs.append(C)
        X = (X - C) // 13
    return limbs


def emulate(A: np.ndarray, B: np.ndarray, p: int, q: int):
    A_int, B_int, mu, nu = scale_pair(A, B, p)
    Al = decompose(A_int, p)
    Bl = decompose(B_int, q)
    C = np.zeros((A.shape[0], B.shape[1]), dtype=np.float64)
    for i, Ai in enumerate(Al):
        for j, Bj in enumerate(Bl):
            C += (13.0 ** (i + j)) * (Ai @ Bj).astype(np.float64)
    C = np.ldexp(C, -(mu + nu))
    ref = A @ B
    err = np.linalg.norm(C - ref) / np.linalg.norm(ref)
    return float(err)


def main():
    size = 32
    phi = 1.0
    seeds = 3
    max_p = 8
    rows = []
    for p in range(1, max_p + 1):
        errs = []
        for seed in range(seeds):
            rng = np.random.default_rng(1000 + seed)
            A = gen(size, size, phi, rng)
            B = gen(size, size, phi, rng)
            errs.append(emulate(A, B, p, p))
        mean = float(np.mean(errs))
        rows.append({"p": p, "gemms": p * p, "gemms_eff_2x": p * p / 2.0,
                     "rel_l2": mean, "rel_l2_std": float(np.std(errs)),
                     "bf16": int(mean <= TARGETS["bf16"]),
                     "fp16": int(mean <= TARGETS["fp16"]),
                     "fp32": int(mean <= TARGETS["fp32"])})
        print(f"p=q={p}: GEMMs={p*p} effective={p*p/2:.1f} relL2={mean:.3e}")
    os.makedirs("results", exist_ok=True)
    with open("results/fp4_pass_counts.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("targets", TARGETS)


if __name__ == "__main__":
    main()
