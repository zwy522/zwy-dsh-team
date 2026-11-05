#!/usr/bin/env python3
"""FP8 E4M3 Ozaki-II hybrid-method simulation (square moduli).

Implements the square-modulus branch of Uchino et al.'s hybrid method:
  p = s^2, A' = s*A1 + A2, B' = s*B1 + B2,
  C' = mod(s*A1*B2 + s*A2*B1 + A2*B2, p),
which uses three FP8 GEMMs per modulus. A1/A2/B1/B2 are small integers
representable exactly in E4M3; products are accumulated exactly in FP32
(no rounding), so the simulation isolates the scaling/CRT accuracy.

The number of FP8 GEMMs is 3*N; N is swept to find the minimum for
BF16/FP16/FP32-equivalent relative L2.
"""

from __future__ import annotations

import csv
import math
from typing import List

import numpy as np

# Distinct primes; p = s^2 <= 1024, pairwise coprime.
SQUARE_BASES = [32, 31, 29, 25, 23, 19, 17, 13, 11, 7, 3]  # pairwise coprime
TARGETS = {"bf16": 1e-2, "fp16": 1e-3, "fp32": 1e-6}


def gen(m, n, phi, rng):
    exps = rng.uniform(-phi, phi, size=(m, n))
    return rng.standard_normal((m, n)) * np.exp2(exps)


def scale_pair(A, B, N, K):
    P = 1
    for s in SQUARE_BASES[:N]:
        P *= s * s
    budget = math.log2(P) - 2.0 - math.ceil(math.log2(K))
    bits = int(budget // 2)
    mu = bits - math.floor(math.log2(float(np.max(np.abs(A))))) - 1
    nu = bits - math.floor(math.log2(float(np.max(np.abs(B))))) - 1
    return np.trunc(np.ldexp(A, mu)).astype(np.int64), np.trunc(np.ldexp(B, nu)).astype(np.int64), mu, nu


def split_square(X, s):
    A1 = np.rint(X / s).astype(np.int64)
    A2 = X - s * A1
    return A1, A2


def crt_object(residues: List[np.ndarray], moduli: List[int]):
    m, n = residues[0].shape
    x = residues[0].astype(object).copy()
    M = int(moduli[0])
    for r, p in zip(residues[1:], moduli[1:]):
        inv = pow(M % p, -1, p)
        t = ((r.astype(object) - x) % p) * inv % p
        x = x + M * t
        M *= p
    half = M // 2
    for i in range(m):
        for j in range(n):
            if x[i, j] > half:
                x[i, j] -= M
    return x


def emulate(A, B, N):
    A_int, B_int, mu, nu = scale_pair(A, B, N, A.shape[1])
    Ps = [s * s for s in SQUARE_BASES[:N]]
    residues = []
    for s, p in zip(SQUARE_BASES[:N], Ps):
        # Split the *residue* modulo p, not the full integer.
        rA = A_int % p
        rA = np.where(rA > p // 2, rA - p, rA)
        rB = B_int % p
        rB = np.where(rB > p // 2, rB - p, rB)
        A1, A2 = split_square(rA, s)
        B1, B2 = split_square(rB, s)
        if max(np.max(np.abs(A1)), np.max(np.abs(A2)),
               np.max(np.abs(B1)), np.max(np.abs(B2))) > 16:
            raise ValueError(f"limb exceeds E4M3 exact integer range at s={s}")
        C1 = A1 @ B2
        C2 = A2 @ B1
        C3 = A2 @ B2
        Cmod = (s * (C1 + C2) + C3) % p
        residues.append(Cmod.astype(np.int64))
    C_int = crt_object(residues, Ps)
    C = np.array(C_int, dtype=object)
    ref = A @ B
    num = sum((float(C[i, j]) * 2.0 ** (-(mu + nu)) - ref[i, j]) ** 2
              for i in range(A.shape[0]) for j in range(B.shape[1]))
    den = float(np.sum(ref * ref))
    return math.sqrt(num / den)


def main():
    size = 24
    phi = 1.0
    seeds = 2
    rows = []
    for N in range(1, len(SQUARE_BASES) + 1):
        errs = []
        for seed in range(seeds):
            rng = np.random.default_rng(2000 + seed)
            A = gen(size, size, phi, rng)
            B = gen(size, size, phi, rng)
            try:
                errs.append(emulate(A, B, N))
            except ValueError as e:
                errs.append(float("nan"))
                print("warn", e)
        mean = float(np.nanmean(errs))
        rows.append({"N": N, "gemms": 3 * N, "rel_l2": mean,
                     "bf16": int(mean <= TARGETS["bf16"]),
                     "fp16": int(mean <= TARGETS["fp16"]),
                     "fp32": int(mean <= TARGETS["fp32"])})
        print(f"N={N:2d} GEMMs={3*N:2d} relL2={mean:.3e}")
    with open("results/fp8_pass_counts.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
