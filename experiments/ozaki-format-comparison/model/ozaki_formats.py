#!/usr/bin/env python3
"""Iso-precision area-energy model for Ozaki-II base formats.

Base formats:
  INT8  : Ozaki-II CRT, moduli near 2^8, one INT8 GEMM per modulus.
  FP8   : Uchino et al., moduli p<=513 (9 bits), three FP8 GEMMs per modulus.
  FP4   : Hayashi et al., base-13 E2M1 limbs; 19 moduli / 75 FP4 GEMMs for
          FP64, i.e. ~6.05 bits per modulus and ~3.95 GEMMs per modulus.

Target precision B is the significand bit count of the emulated GEMM
(BF16=8, FP16=11, FP32=24, FP64=53). The CRT product must cover 2*B plus
guard bits; we set guard = ceil(log2(K)) + 2, K = 128 -> 9.

Hardware cost per MAC:
  INT8 measured on TSMC 28 nm HPC+ FF (P0b): 378.13 um^2, 0.366 pJ.
  FP8/FP4 are scaled by area/energy factors (assumptions, sensitivity shown).
  FP4 has a 2x throughput factor (Blackwell-class).
"""

from __future__ import annotations

import csv
import math
import os

K = 128
GUARD = math.ceil(math.log2(K)) + 2  # 9
INT8_AREA = 378.125990  # um^2, TSMC 28 HPC+ FF, P0b
INT8_ENERGY = 0.3663    # pJ/MAC, default activity, P0b
F = 300e6               # Hz
N_LANES = 128 * 128     # 16384
TOPS_PEAK = N_LANES * 2 * F / 1e12

TARGETS = {"BF16": 8, "FP16": 11, "FP32": 24, "FP64": 53}

BASES = {
    "INT8": dict(bits_per_modulus=8.0, gemms_per_modulus=1.0,
                 area_factor=1.0, energy_factor=1.0, throughput_factor=1.0,
                 note="moduli near 2^8; one INT8 GEMM per modulus"),
    "FP8": dict(bits_per_modulus=9.0, gemms_per_modulus=3.0,
                area_factor=1.6381, energy_factor=0.8602, throughput_factor=1.0,
                note="p<=513; 3 FP8 GEMMs per modulus; measured MAC area/energy"),
    "FP4": dict(bits_per_modulus=6.05, gemms_per_modulus=3.95,
                area_factor=1.4578, energy_factor=0.5454, throughput_factor=2.0,
                note="base-13; ~19 moduli / 75 FP4 GEMMs at FP64; measured MAC"),
}


def result_bits(B: int) -> int:
    return 2 * B + GUARD


# FP8 hybrid-method simulation counts (results/fp8_pass_counts.csv);
# FP64 keeps the paper's N=13 -> 39 GEMMs.
FP8_Q_OVERRIDE = {"BF16": 9.0, "FP16": 12.0, "FP32": 18.0, "FP64": 39.0}


def passes(B: int, fmt: str, target: str = "") -> tuple[int, float]:
    cfg = BASES[fmt]
    r = result_bits(B)
    m = math.ceil(r / cfg["bits_per_modulus"])
    q = m * cfg["gemms_per_modulus"]
    if fmt == "FP8" and target in FP8_Q_OVERRIDE:
        q = FP8_Q_OVERRIDE[target]
    return m, q


def evaluate(area_factor: float | None = None,
             energy_factor: float | None = None,
             throughput_factor: float | None = None) -> list[dict]:
    rows = []
    for name, cfg in BASES.items():
        af = cfg["area_factor"] if area_factor is None else area_factor
        ef = cfg["energy_factor"] if energy_factor is None else energy_factor
        tf = cfg["throughput_factor"] if throughput_factor is None else throughput_factor
        # Apply overrides only to the format being explored by the caller.
        for tname, B in TARGETS.items():
            m, q = passes(B, name, tname)
            q_eff = q / tf
            area = INT8_AREA * af
            energy = INT8_ENERGY * ef
            cost = q_eff * area * energy  # lower is better
            t_eff = TOPS_PEAK / q_eff
            total_area = area * N_LANES / 1e6  # mm^2
            total_power = energy * 1e-12 * N_LANES * F  # W (dynamic only; energy in pJ)
            aee = t_eff / (total_area * total_power)
            rows.append(dict(
                format=name, target=tname, target_bits=B,
                result_bits=result_bits(B), moduli=m, gemms=q,
                gemms_effective=q_eff, area_um2=area, energy_pj=energy,
                cost_norm=0.0, cost=cost, aee=aee,
                area_mm2=total_area, power_w=total_power, tops_eff=t_eff,
            ))
    # Normalize cost and AEE to INT8 for each target.
    for row in rows:
        ref = next(r for r in rows if r["format"] == "INT8" and r["target"] == row["target"])
        row["cost_norm"] = row["cost"] / ref["cost"]
        row["aee_norm"] = row["aee"] / ref["aee"]
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader(); w.writerows(rows)


def main() -> None:
    rows = evaluate()
    write_csv(rows, "results/pass_counts.csv")
    print(f"K={K}, guard={GUARD}, N={N_LANES}, f={F/1e6:.0f} MHz, peak={TOPS_PEAK:.4f} TOPS")
    print(f"{'fmt':5s} {'target':6s} {'R':>3s} {'mod':>4s} {'GEMM':>5s} {'Q_eff':>6s} "
          f"{'cost_norm':>9s} {'AEE_norm':>9s}")
    for r in rows:
        print(f"{r['format']:5s} {r['target']:6s} {r['result_bits']:3d} {r['moduli']:4d} "
              f"{r['gemms']:5.1f} {r['gemms_effective']:6.2f} "
              f"{r['cost_norm']:9.3f} {r['aee_norm']:9.3f}")

    # Sensitivity: vary FP4 area*energy and throughput; vary FP8 area*energy.
    print("\nSensitivity (cost_norm; lower is better):")
    for target in ("BF16", "FP16", "FP32", "FP64"):
        base = {r["format"]: r for r in rows if r["target"] == target}
        print(f"  {target}: INT8=1.000 FP8={base['FP8']['cost_norm']:.3f} "
              f"FP4={base['FP4']['cost_norm']:.3f}")
    base_f4 = 0.7951  # measured FP4 area_factor * energy_factor
    for f4 in (0.3, 0.5, base_f4, 1.0):
        r = evaluate()  # baseline
        sel = [x for x in r if x["format"] == "FP4" and x["target"] == "FP32"][0]
        print(f"  FP4 area*energy factor {f4:.4f} -> FP32 cost_norm ~ {f4/base_f4*sel['cost_norm']:.3f}")


if __name__ == "__main__":
    main()
