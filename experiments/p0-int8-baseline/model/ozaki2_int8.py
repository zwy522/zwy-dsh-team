#!/usr/bin/env python3
"""P0 prototype of an Ozaki-II / CRT pass-count model for INT8 residue domains.

This is a *reduced* model, not a bit-exact replica of OzCore:
  - global (not per-row/per-column) power-of-two scaling;
  - pairwise-coprime moduli near 2^8;
  - exact integer CRT reconstruction at arbitrary precision;
  - random FP64 matrices with a controllable exponent spread phi.

It is used to estimate how many INT8 GEMM passes (split count s) are needed
to reach a target relative-L2 error, which is the `Q` input of the P0 plan's
iso-accuracy efficiency metric.

Run:
    python3 model/ozaki2_int8.py --out results/pass_count.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from typing import List, Sequence, Tuple

import numpy as np

# Pairwise-coprime primes just below 2^8. Same spirit as OzCore's moduli
# near 2^8; the list is long enough for s up to 12.
MODULI = [
    251, 241, 239, 233, 229, 227, 223, 211,
    199, 197, 193, 191, 181, 179, 173, 167,
]

# Tentative target thresholds from the research plan. These are not claims
# about a particular workload; they define the pass-count sweep.
TARGETS = {"bf16_equiv": 1e-2, "fp32_equiv": 1e-6}


def choose_moduli(s: int) -> List[int]:
    if not 1 <= s <= len(MODULI):
        raise ValueError(f"split count s must be in [1, {len(MODULI)}], got {s}")
    return MODULI[:s]


def gen_matrix(m: int, n: int, phi: float, rng: np.random.Generator) -> np.ndarray:
    """Random FP64 matrix with exponent spread controlled by phi.

    Entries are standard-normal magnitudes scaled by 2^u with u ~ U(-phi, phi),
    which makes the dynamic range of the matrix controllable from narrow
    (phi small) to heavy-tailed (phi large).
    """
    exps = rng.uniform(-phi, phi, size=(m, n))
    return rng.standard_normal((m, n)) * np.exp2(exps)


def scale_pair(
    A: np.ndarray, B: np.ndarray, s: int
) -> Tuple[np.ndarray, np.ndarray, int, int, int, int]:
    """Choose global power-of-two scales so products fit the CRT modulus.

    Returns (A_int, B_int, mu, nu, bA, bB), where
        A_int = trunc(2^mu * A), B_int = trunc(2^nu * B),
    and |A_int| < 2^bA, |B_int| < 2^bB.
    """
    moduli = choose_moduli(s)
    P = math.prod(moduli)
    p_bits = math.log2(P)
    K = A.shape[1]
    budget = p_bits - 3.0 - math.ceil(math.log2(K))
    if budget < 2:
        # Too few moduli to buy fractional bits: fall back to a coarse
        # integer-only scaling. Useful for the s=1 end of the sweep.
        budget = 1.0
    bA = int(budget // 2)
    bB = int(budget - bA)

    a_max = float(np.max(np.abs(A)))
    b_max = float(np.max(np.abs(B)))
    mu = bA - math.floor(math.log2(a_max)) - 1
    nu = bB - math.floor(math.log2(b_max)) - 1

    A_int = np.trunc(np.ldexp(A, mu)).astype(np.int64)
    B_int = np.trunc(np.ldexp(B, nu)).astype(np.int64)
    return A_int, B_int, mu, nu, bA, bB


def _mod_matrix(M: np.ndarray, p: int) -> List[List[int]]:
    return [[int(v) % p for v in row] for row in M.tolist()]


def _matmul_int(A: Sequence[Sequence[int]], B: Sequence[Sequence[int]]) -> List[List[int]]:
    n = len(B[0])
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(n)] for i in range(len(A))]


def crt_reconstruct(
    residues: Sequence[List[List[int]]], moduli: Sequence[int]
) -> List[List[int]]:
    """Incremental CRT, then map the result into the symmetric range."""
    s = len(moduli)
    m, n = len(residues[0]), len(residues[0][0])
    x = [[int(residues[0][i][j]) for j in range(n)] for i in range(m)]
    M = int(moduli[0])
    for idx in range(1, s):
        p = int(moduli[idx])
        inv = pow(M % p, -1, p)
        for i in range(m):
            xr = x[i]
            rr = residues[idx][i]
            for j in range(n):
                t = ((rr[j] - xr[j]) % p) * inv % p
                xr[j] += M * t
        M *= p
    half = M // 2
    for i in range(m):
        for j in range(n):
            if x[i][j] > half:
                x[i][j] -= M
    return x


def emulate(
    A: np.ndarray, B: np.ndarray, s: int
) -> Tuple[np.ndarray, float, dict]:
    """Emulate A @ B with s integer residue passes and return the FP64 estimate."""
    A_int, B_int, mu, nu, bA, bB = scale_pair(A, B, s)
    moduli = choose_moduli(s)

    # Residue-domain GEMMs. The residues are small; products fit int64 easily.
    residue_products: List[List[List[int]]] = []
    for p in moduli:
        A_mod = _mod_matrix(A_int, p)
        B_mod = _mod_matrix(B_int, p)
        # Reduce the product sum modulo p before CRT: the CRT loop assumes
        # residues are canonical representatives in [0, p).
        C_mod = [[v % p for v in row] for row in _matmul_int(A_mod, B_mod)]
        residue_products.append(C_mod)

    C_int = crt_reconstruct(residue_products, moduli)
    scale = -(mu + nu)
    C_est = np.array(
        [[math.ldexp(float(v), scale) for v in row] for row in C_int], dtype=np.float64
    )
    meta = {"s": s, "moduli": moduli, "bA": bA, "bB": bB, "mu": mu, "nu": nu}
    return C_est, 0.0, meta


def relative_l2(C_est: np.ndarray, C_ref: np.ndarray) -> float:
    num = np.linalg.norm(C_est - C_ref)
    den = np.linalg.norm(C_ref)
    return float(num / den) if den else float("nan")


def run_sweep(size: int, phi: float, seeds: int, max_s: int) -> List[dict]:
    rows: List[dict] = []
    for s in range(1, max_s + 1):
        errs = []
        meta = None
        for seed in range(seeds):
            rng = np.random.default_rng(seed + 1000 * s)
            A = gen_matrix(size, size, phi, rng)
            B = gen_matrix(size, size, phi, rng)
            C_ref = A @ B
            C_est, _, meta = emulate(A, B, s)
            errs.append(relative_l2(C_est, C_ref))
        assert meta is not None
        rows.append(
            {
                "s": s,
                "moduli": " ".join(str(p) for p in meta["moduli"]),
                "p_bits": round(sum(math.log2(p) for p in meta["moduli"]), 2),
                "bA": meta["bA"],
                "bB": meta["bB"],
                "phi": phi,
                "size": size,
                "seeds": seeds,
                "rel_l2_mean": float(np.mean(errs)),
                "rel_l2_std": float(np.std(errs)),
                "meets_bf16": int(np.mean(errs) <= TARGETS["bf16_equiv"]),
                "meets_fp32": int(np.mean(errs) <= TARGETS["fp32_equiv"]),
            }
        )
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=32)
    ap.add_argument("--phi", type=float, default=1.0)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--max-s", type=int, default=12)
    ap.add_argument("--out", default="results/pass_count.csv")
    args = ap.parse_args(argv)

    rows = run_sweep(args.size, args.phi, args.seeds, args.max_s)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {args.out}")
    for r in rows:
        print(
            f"s={r['s']:2d}  Pbits={r['p_bits']:5.1f}  "
            f"relL2={r['rel_l2_mean']:.3e} ± {r['rel_l2_std']:.1e}  "
            f"bf16={'Y' if r['meets_bf16'] else 'n'}  "
            f"fp32={'Y' if r['meets_fp32'] else 'n'}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
