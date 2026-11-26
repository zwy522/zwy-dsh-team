# OzCore Postprocess + Top/Control — RTL Porting Specification

Status: **implementation-ready draft (v0.1), derived read-only from the Catapult HLS C++ artifact.**
Scope: postprocess stage and top/control stage of OzCore, plus the interfaces they share with
preprocess and the SIMD engine.
Root for all citations: `reproduction/ozcore/ozcore-artifact/src/hw/synth/hls/`
(abbreviated below as `hls/`). Paths outside that root are given in full.

This document is concrete enough to write RTL and a self-checking testbench without re-reading the
HLS, **except** for the internals of preprocess/SIMD, which are covered by their own specs (see §7
for the exact list of shared facts that must match).

---

## 0. Orientation

### 0.1 What this stage computes (one paragraph)

OzCore replaces an FP dot product by an integer dot product modulo a product of coprime-ish
moduli. Let `s` be the number of moduli used for one dot product and
`P_s = Π_{j=0..s-1} m_j` with `m = (256,255,253,251,247,241,239,233,229,227,223,217,...)`.
Preprocess quantizes each input element into signed 8-bit centered residues `r_i = x mod m_j`
(centered into `[-m_j/2, m_j/2]`); the SIMD engine (INT8) accumulates `K` products per modulus
lane in a 32-bit signed accumulator; postprocess reconstructs the integer dot product by CRT,
reduces the CRT sum modulo `P_s` into the balanced range `[-P_s/2, P_s/2]`, and normalizes it by
`2^{-d}` (the accumulated scaling exponent `d = shift_weight + shift_activation`) into an IEEE-754
binary32 value. For pure INT8 x INT8 the CRT is bypassed and the raw int32 accumulator bits are
forwarded in the same 32-bit output container.

### 0.2 Notational conventions

| Symbol | Meaning in this spec | HLS name |
|---|---|---|
| `S_MAX` | 12, number of physical SIMD/modulus lanes | `S_MAX` / `S_max` |
| `s` | number of moduli per reconstructed dot product (config, in-band) | `cfg.s`, `data_in.s` |
| `C` | number of independent dot products (chunks) processed per frame; `C = S_MAX/s` | derived (not named) |
| lane `i` | physical lane `0..11`; belongs to chunk `c = i/s` and modulus index `j = i%s` | loop index |
| chunk / channel | one dot product (one K-slice) | "channel" in TB, `col_no` is a different thing |
| column | one output feature / one SIMD engine, indexed by `SIMD_ID`; `N` of them | `col_no`, `SIMD_ID` |
| `P_s` (or `P`) | product of the `s` active moduli; paper's modulus product | `mod_product_all` |
| `d` | total denormalization exponent (`weight shift + activation shift`) | `data_in.shift[i]`, `de_t` |
| `si` | slot index of the 6-wide postprocess output `0..5` | `out_r[i]`, `out_select_r[i]` |

`S_MAX = 12` is a hard build constant in this artifact; `COMP_BW` depends on it.
The postprocess only supports `s ∈ {2, 3, 4, 6, 12}` (divisors of 12). INT8 x INT8 uses the
bypass and is nominally `s = 1` (12 chunks per frame); see §3.6 and §5.1.

### 0.3 Source files actually used

| Area | File | Lines |
|---|---|---|
| global constants/types | `hls/common/include/global_params.h` | 23–71 |
| tables | `hls/common/include/ozaki_tables.h` | 35–242 |
| postprocess wrapper | `hls/postprocess/include/postprocess_parallel.h` | 15–213 |
| postprocess core+wrap | `hls/postprocess/include/postprocess_parallel_ccore.h` | 15–240 |
| postprocess params | `hls/postprocess/include/params_parallel.h`, `params.h` | 23–61, 17–69 |
| int→FP | `hls/postprocess/include/int_fp_change_parallel.h` | 15–125 |
| modular reduction primitive | `hls/modulo/include/new_single_s12.h` | 8–61 |
| iterated reduction | `hls/modulo/include/iterated_new_s12_scalar.h` | 10–96 |
| top params | `hls/top/include/params_parallel.h` | 15–44 |
| top hierarchy | `hls/top/include/top_parallel.h` | 13–125 |
| path chooser | `hls/top/include/path_chooser.h` | 9–45 |
| output selector | `hls/top/include/output_selector.h` | 12–38 |
| output aligner | `hls/top/include/output_aligner.h` | 10–40 |
| SIMD wrapper (interface source) | `hls/simd_engine/include/simd_engine_parallel_ccore.h` | 30–133 |
| SIMD params | `hls/simd_engine/include/params_parallel.h`, `params.h` | 15–40, 15–45 |
| preprocess lane expansion (needed by postprocess) | `hls/preprocess/include/preprocess_parallel_compressed_ccore.h` | 154–193, 198–266, 306–319 |
| preprocess params | `hls/preprocess/include/params_parallel.h`, `params.h` | 23–63, 16–98 |
| postprocess TB | `hls/postprocess/tb/tb_postprocess_parallel_ccore.cpp` | 1–102 |
| top TB | `hls/top/tb/tb_top_parallel.cpp` | 1–255 |
| flow/module registry | `hls/modules.json` | top/postprocess entries |

Citation bases used below (besides `hls/`): `data/...` =
`reproduction/ozcore/ozcore-artifact/data/...`; `src/emulation/...` =
`reproduction/ozcore/ozcore-artifact/src/emulation/...`; `experiments/...` = workspace root.
The CUDA reference cited in §2.5.4/R4 is
`reproduction/ozcore/ozcore-artifact/src/emulation/llm/crt_reconst/int128_arithmetic.cuh`.

The `.cpp` files are not logic: `postprocess/src/postprocess_parallel.cpp` and
`postprocess_parallel_ccore.cpp` are a one-line `#include` plus a class forward declaration;
`top/src/top_parallel.cpp` is an include plus a wrapper declaration; `top/src/path_chooser.cpp`,
`output_selector.cpp`, `output_aligner.cpp` add explicit template instantiations (N=32) and, for the
aligner, a concrete `output_aligner_wrap` for SCVerify (`top/src/output_aligner.cpp:18–34`). The
arithmetic source of truth is the headers listed above.

The `core` (`postprocess_parallel_ccore.h:15–197`) and non-core
(`postprocess_parallel.h:15–213`) postprocess bodies are **arithmetically identical** (verified by
normalized diff); only the interface wrapper differs. The synthesized area in
`data/hw/synth_raw/ozcore_um2.json` (`postprocess_per_lane = 107861.478 µm²`,
`output_selector = 4244.21`, `path_chooser = 4412.708`, `output_aligner = 319433.617` at 128
columns) corresponds to the non-core `postprocess_parallel` (`hls/modules.json`, entry
`postprocess_parallel`).

---

## 1. Global parameters, types, and exact tables

### 1.1 Constants (`hls/common/include/global_params.h`)

| Constant | Value | Cite | Used for |
|---|---:|---|---|
| `S_MAX` | 12 | 23 | lanes / moduli |
| `MOD_BW` | 8 | 26 | residue width |
| `ACC_BW` | 32 | 29 | SIMD accumulator |
| `COMP_BW` | 6 (when `S_MAX==12`) | 32 | complementary modulus width |
| `DE_BW` | 10 | 35 | total shift `d` |
| `S_BW` | 4 | 38 | `s` counter (`ozaki_npu::s_t`) |
| `RUN_MODE_BW` | 2 | 42 | unused here |
| `LOAD_WEIGHTS` / `COMPUTE` | 1 / 0 | 83–84 | unused here (SIMD uses `is_weight`) |

Types (same header): `mod_t = ac_int<8,true>` (49), `mod_unsigned_t = ac_int<8,false>` (52),
`acc_t = ac_int<32,true>` (55), `de_t = ac_int<10,true>` (58),
`shift_t = ac_int<9,true>` (59), `s_t = ac_int<4,false>` (62), `comp_t = ac_int<6,false>` (68),
`acc128_t = ac_int<128,true>` (71). `counter_params<maxN>::width = ac::log2_ceil<maxN>::val`
(94–98).

Note the asymmetry that matters for RTL: **a single input's shift is 9 bits (`shift_t`), but the
summed `d` carried by SIMD/postprocess is 10 bits (`de_t`)**.

### 1.2 Ozaki-2 tables (`hls/common/include/ozaki_tables.h`)

Only the first 12 entries are used by a `S_MAX=12` build.

Moduli and complements (35–38, 65–68):

| j | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `m_j` | 256 | 255 | 253 | 251 | 247 | 241 | 239 | 233 | 229 | 227 | 223 | 217 |
| `comp_j = 256-m_j` | 0 | 1 | 3 | 5 | 9 | 15 | 17 | 23 | 27 | 29 | 33 | 39 |
| `INV_S[s-1][j]` for s=12 | 185 | 211 | 124 | 76 | 72 | 231 | 45 | 78 | 45 | 217 | 10 | 149 |

`INV_S[s-1][j]` is the modular inverse of `P_s/m_j` modulo `m_j`
(`hls/common/include/ozaki_tables.h:229–242`). This identity was verified numerically for every
supported `s` and `j`; it is what makes the CRT work.

The 96-bit constants used by postprocess are stored as two arrays of 64-bit/32-bit words and
recombined as `(hi << 64) | lo` (`postprocess_parallel.h:135`, `:157`):

* `MOD_PRODUCT_LOWER[12][12]` (170–183), `MOD_PRODUCT_UPPER[12][12]` (190–203) hold
  `mi[s-1][j] = P_s / m_j`, 96-bit.
* `MOD_PRODUCT_ALL_LOWER[12]` (210–213), `MOD_PRODUCT_ALL_UPPER[12]` (220–222) hold `P_s`, 96-bit.
* `INV_S[12][12]` (229–242) holds the inverses above.

The headers also contain `OZ2_MODULI_PRODUCT[15]` (115–131), `INV_COMB[20][20]` (82–103) and
`POWER_OF_COMP_MOD_M[11][10]` (147–159); **postprocess does not use them** (they belong to other
variants / preprocess). They are cited here so nobody ports dead tables.

### 1.3 Supported `s` and the channel count

| `s` | active moduli | `P_s` | bits of `P_s` | chunks per frame `C=12/s` | postprocess? |
|---:|---|---:|---:|---:|---|
| 1 | `{256}` | 256 | 9 | 12 | **no** — INT8 bypass only |
| 2 | `{256,255}` | 65 280 = `0x00000000000000000000ff00` | 16 | 6 | yes |
| 3 | `{256,255,253}` | 16 515 840 = `0x000000000000000000fc0300` | 24 | 4 | yes |
| 4 | `{256,255,253,251}` | 4 145 475 840 = `0x0000000000000000f716f100` | 32 | 3 | yes |
| 6 | `{...241}` | 246 767 740 327 680 = `0x000000000000e06f17811700` | 48 | 2 | yes |
| 12 | all 12 | 34 567 513 620 616 987 484 638 644 480 = `0x006fb193bc3ea899dc188f8900` | 95 | 1 | yes |

Any other `s` (0, 5, 7, 8, 9, 10, 11, 13–15) is **not implemented**: the per-lane constant muxes
in the HLS encode only the five rows above (and the tree only works for divisors of 12). `s = 0`
also causes an out-of-range table index (`s-1 = 15`) — see risk R5. `s = 1` is special-cased to the
bypass path in top.

### 1.4 Exact postprocess constants per `s`

`mi = P_s / m_j` (96-bit, decimal and hex); these are exactly what `MOD_PRODUCT_*` store.

**s = 2, P = 65 280 (`0xff00`, 16 bits)**

| j | m_j | comp | inv | mi |
|---:|---:|---:|---:|---:|
| 0 | 256 | 0 | 255 | 255 (`0x0000000000000000000000ff`) |
| 1 | 255 | 1 | 1 | 256 (`0x000000000000000000000100`) |

**s = 3, P = 16 515 840 (`0xfc0300`, 24 bits)**

| j | m_j | comp | inv | mi |
|---:|---:|---:|---:|---:|
| 0 | 256 | 0 | 171 | 64 515 (`0x00000000000000000000fc03`) |
| 1 | 255 | 1 | 127 | 64 768 (`0x00000000000000000000fd00`) |
| 2 | 253 | 3 | 211 | 65 280 (`0x00000000000000000000ff00`) |

**s = 4, P = 4 145 475 840 (`0xf716f100`, 32 bits)**

| j | m_j | comp | inv | mi |
|---:|---:|---:|---:|---:|
| 0 | 256 | 0 | 17 | 16 193 265 (`0x000000000000000000f716f1`) |
| 1 | 255 | 1 | 32 | 16 256 768 (`0x000000000000000000f80f00`) |
| 2 | 253 | 3 | 21 | 16 385 280 (`0x000000000000000000fa0500`) |
| 3 | 251 | 5 | 182 | 16 515 840 (`0x000000000000000000fc0300`) |

**s = 6, P = 246 767 740 327 680 (`0xe06f17811700`, 48 bits)**

| j | m_j | comp | inv | mi |
|---:|---:|---:|---:|---:|
| 0 | 256 | 0 | 167 | 963 936 485 655 (`0x00000000000000e06f178117`) |
| 1 | 255 | 1 | 146 | 967 716 628 736 (`0x00000000000000e15067e900`) |
| 2 | 253 | 3 | 53 | 975 366 562 560 (`0x00000000000000e31860a300`) |
| 3 | 251 | 5 | 243 | 983 138 407 680 (`0x00000000000000e4e79d9500`) |
| 4 | 247 | 9 | 206 | 999 059 677 440 (`0x00000000000000e89c98e100`) |
| 5 | 241 | 15 | 184 | 1 023 932 532 480 (`0x00000000000000ee67228700`) |

**s = 12, P = 34 567 513 620 616 987 484 638 644 480
(`0x006fb193bc3ea899dc188f8900`, 95 bits)**

| j | m_j | comp | inv | mi (decimal) | mi (96-bit hex, lo64 / hi32) |
|---:|---:|---:|---:|---:|---|
| 0 | 256 | 0 | 185 | 135 029 350 080 535 107 361 869 705 | `0x006fb193bc3ea899dc188f89` / `bc3ea899dc188f89`,`006fb193` |
| 1 | 255 | 1 | 211 | 135 558 876 943 596 029 351 524 096 | `0x007021b571b058f2cee77700` / `71b058f2cee77700`,`007021b5` |
| 2 | 253 | 3 | 124 | 136 630 488 619 039 476 223 868 160 | `0x007104a1a1220ec62ea47d00` / `a1220ec62ea47d00`,`007104a1` |
| 3 | 251 | 5 | 76 | 137 719 177 771 382 420 257 524 480 | `0x0071eb2b962d8c5791f24b00` / `962d8c5791f24b00`,`0071eb2b` |
| 4 | 247 | 9 | 72 | 139 949 447 856 748 937 184 771 840 | `0x0073c372c52d3fd878537f00` / `c52d3fd878537f00`,`0073c372` |
| 5 | 241 | 15 | 231 | 143 433 666 475 589 159 687 297 280 | `0x0076a542a3d8559e1ff81900` / `a3d8559e1ff81900`,`0076a542` |
| 6 | 239 | 17 | 45 | 144 633 948 203 418 357 676 312 320 | `0x0077a36e0af935210e070700` / `0af935210e070700`,`0077a36e` |
| 7 | 233 | 23 | 78 | 148 358 427 556 296 083 625 058 560 | `0x007ab81e79209615d1f5a100` / `79209615d1f5a100`,`007ab81e` |
| 8 | 229 | 27 | 45 | 150 949 841 138 065 447 531 173 120 | `0x007cdcdf48eff7ba887dd500` / `48eff7ba887dd500`,`007cdcdf` |
| 9 | 227 | 29 | 217 | 152 279 795 685 537 389 800 170 240 | `0x007df68043f0f445c335a300` / `43f0f445c335a300`,`007df680` |
| 10 | 223 | 33 | 10 | 155 011 271 841 331 782 442 325 760 | `0x008038e9e26ef65bad749700` / `e26ef65bad749700`,`008038e9` |
| 11 | 217 | 39 | 149 | 159 297 297 790 861 693 477 597 440 | `0x0083c483d1198d189bd63100` / `d1198d189bd63100`,`0083c483` |

The `INV_S` rows for the other `s` are in `ozaki_tables.h:229–242` and reproduced in Appendix A.

**Width budget.** For `s=12`: `P < 2^95` (95 bits) and `P/2 < 2^94`; `mi·t` with
`|t| ≤ m_j/2` is at most `P/2 < 2^94`; a pre-wrap sum of two such terms is at most `P < 2^95`.
Therefore **signed 96-bit arithmetic is exactly sufficient** (96-bit signed max `2^95-1 > P`),
but with only ~0.2 bit of headroom. Any RTL that adds three terms before the wrap, or that
computes `mi·t + mi·t` without the `±P` correction, will overflow. This is a hard rule.

### 1.5 Per-`s` datapath width (recommended RTL parameter)

Because every intermediate is bounded by `±P_s`, a bit-exact narrow datapath can be used:

| `s` | bits(`P_s`) | minimum signed data width `W_s = bits(P_s)+1` |
|---:|---:|---:|
| 2 | 16 | 17 |
| 3 | 24 | 25 |
| 4 | 32 | 33 |
| 6 | 48 | 49 |
| 12 | 95 | 96 |

Using `W_s` gives bit-identical results to the HLS 96-bit datapath (the HLS values are sign
extensions of the narrow values); it is the single largest area simplification when `s` is fixed at
elaboration (≈5.6× narrower for `s=2`). If `s` is runtime-selectable, use 96 bits.

---

## 2. Postprocess stage

### 2.1 Hierarchy and files

The stage has exactly one arithmetic body and two wrappers:

* `postprocess_parallel` with channels — `postprocess_parallel.h:15–213`
  (`#pragma hls_pipeline_init_interval 1`, `#pragma hls_design interface // top`, run at :44–46).
* `postprocess_parallel_core` (ccore) + `postprocess_parallel` wrapper —
  `postprocess_parallel_ccore.h:15–197` and `:199–240`.
  The wrapper reads one `in_pkg_t` and calls the core (`:232–238`).

There is **no state** in either variant: every output is a pure function of the input frame
(`data`, `shift`, `s`). This is important for the RTL: the postprocess can be freely pipelined,
stalled, or time-multiplexed without a context save.

Internal instances (identical in both files):

| Instance | Declaration | Cite |
|---|---|---|
| `moduli_1st_inst[11]` | `iterated_new_s12_scalar<32,8,6,3,true,false>` | :36 |
| `moduli_2nd_inst[11]` | `iterated_new_s12_scalar<16,8,6,1,false,true>` | :37 |
| `int2fp_inst[12]` (only 6 used) | `int_fp_change<ac_int<96,true>, outType, S_MAX/2>` | :38 |

The templates' arguments mean: input width, modulus width, complement width, number of serial
base-256 stages, input-signed, output-signed.

### 2.2 Interfaces

Logical packages (from `postprocess_parallel_params<true>`, `params_parallel.h:23–61`, with base
`postprocess_params<16,true>`, `params.h:17–45`):

```
accType      = ac_int<32,true>            // one SIMD lane accumulator
deType       = de_t = ac_int<10,true>     // total shift d
SType        = ac_int<4,false>            // s
outType      = ac_std_float<32,8>         // IEEE-754 binary32 payload
in_pkg_t {                                // postprocess_parallel_params.h:51-56
  ac_array<accType,12> data;              // 12 * 32 = 384 bits
  ac_array<deType,12>  shift;             // 12 * 10 = 120 bits
  SType                s;                 // 4 bits
  bool                 intint;            // 1 bit, DEAD in this version (see note)
}
out_vec_t = ac_array<outType,6>           // 6 * 32 = 192 bits
```

* `intint` is present in `in_pkg_t` but **never read** by the postprocess
  (`postprocess_parallel.h:46–211`; the ccore interface at `:46–51` does not even have it). The
  path chooser does not set it either (`path_chooser.h:38–41`). Treat it as tie-0 and drop it from
  the RTL port.
* There is no valid/ready in the HLS type; channel handshaking is discussed in §3.4.

For the RTL, the recommended flat port (postprocess per SIMD lane) is:

| Port | Dir | Width (S_MAX=12) | Meaning |
|---|---|---:|---|
| `data_i[12*32-1:0]` | in | 384 | signed 32-bit lane accumulators |
| `shift_i[12*10-1:0]` | in | 120 | signed 10-bit `d` per lane |
| `s_i[3:0]` | in | 4 | active modulus count; legal `{2,3,4,6,12}`, illegal otherwise (see R5) |
| `out_o[6*32-1:0]` | out | 192 | IEEE-754 bit patterns; slots `0..C-1` valid |
| `valid_i`, `ready_o`, `valid_o`, `ready_i` | — | 1 each | streaming handshake |

The 6 output slots correspond 1:1 to chunks; invalid slots are don't-care (HLS produces partial
sums there) — the RTL should zero them for determinism.

### 2.3 Parameters and exact types

From `params.h` and `params_parallel.h`:

| Item | Value | Cite |
|---|---|---|
| `S_max` | `S_MAX` = 12 | `params.h:20` |
| `mod_w` | `MOD_BW` = 8 | `params.h:24` |
| `comp_w` | `COMP_BW` = 6 | `params.h:26` |
| `acc_w` | `ACC_BW` = 32 | `params.h:23` |
| `outType` | `ac_std_float<32,8>` | `params.h:42` |
| `modType` | `ac_int<8,true>` (mod_sign=true) | `params.h:39` |
| `mod_unsigned_t` | `ac_int<8,false>` | `params.h:31` |
| `deType` | `ac_int<10,true>` | `params.h:44` |
| `SType` | `ac_int<4,false>` | `params.h:45` |
| `accType` | `ac_int<32,true>` (override in parallel trait) | `params_parallel.h:41` |
| `out_vec_t` | `ac_array<outType,6>` | `params_parallel.h:48` |
| `compType` | `ac_int<6,false>` | `postprocess_parallel.h:35` |

The `postprocess_params<16, ...>` template's first argument (`N=16`) only affects an unused
`data_array_t`; it is irrelevant to RTL.

### 2.4 Lane → (chunk, modulus) mapping

The postprocess does **not** compute `i % s` arithmetically; it selects constants and the adder
tree through per-`s` muxes. The muxes were decoded and compared against the preprocess's
`base_select` / `moduli_select` (`preprocess_parallel_compressed_ccore.h:198–221`): both implement

```
chunk   c = i / s          (integer division, 0..C-1)
modulus j = i % s          (0..s-1)
m_i     = m_j, comp_i = comp_j, inv_i = INV_S[s-1][j], mi_i = P_s / m_j
```

for every `s ∈ {2,3,4,6,12}` and every lane `i ∈ [0,12)`. This is the single most important shared
contract with preprocess and SIMD; put it in all three specs verbatim.

Expanded view:

| s | lane 0..11 → (chunk, modulus) |
|---:|---|
| 2 | (0,0)(0,1) (1,0)(1,1) (2,0)(2,1) (3,0)(3,1) (4,0)(4,1) (5,0)(5,1) |
| 3 | (0,0)(0,1)(0,2) (1,0)(1,1)(1,2) (2,0)(2,1)(2,2) (3,0)(3,1)(3,2) |
| 4 | (0,0)(0,1)(0,2)(0,3) (1,0)(1,1)(1,2)(1,3) (2,0)(2,1)(2,2)(2,3) |
| 6 | (0,0)…(0,5) (1,0)…(1,5) |
| 12 | (0,0)…(0,11) |
| 1 (bypass only) | (0,0)…(11,0) — lane `i` is independent chunk `i`; postprocess not used |

The HLS muxes for `moduli_r`, `yi`, `comp_r`, `mod_product` are at
`postprocess_parallel.h:81–105` (`moduli`/`comp`), `:68–79` (`yi`), `:138–149` (`mi` mux). They
contain dozens of ternary terms each; in RTL replace them with a ROM indexed by `(s, i)` returning
`{m (9b), comp (6b), inv (8b), mi (96b)}`. The ROM contents are exactly §1.4. This is proven
equivalent (the mux expressions were decoded exhaustively for all five `s`).

### 2.5 Arithmetic datapath, step by step

All line numbers below refer to `hls/postprocess/include/postprocess_parallel.h` (the ccore body has
the same operations at `postprocess_parallel_ccore.h:106–196`).

#### 2.5.1 Stage 1 — reduce the signed 32-bit accumulator modulo `m_i` (`r1`)

For lanes `i = 1..11` (`:111–116`):

```
a   = |data[i]|                      // 32-bit unsigned; -2^31 maps to 2^31 correctly
r   = red16(a >> 16, m_i)            // limb = bits 31:16
r   = red16((r << 8) | ((a >> 8) & 0xFF), m_i)
r   = red16((r << 8) | ( a        & 0xFF), m_i)
r1  = (data[i] < 0 && r != 0) ? (m_i - r) : r      // 8-bit unsigned, 0..m_i-1
```

For lane 0 (`:117`): `r1[0] = data[0] & 0xFF` (low byte, because `m_0 = 256`).

`red16(x, m)` is `new_single_s12::run` (`hls/modulo/include/new_single_s12.h:17–58`) with
`in` 16 bits, `out`/`N` 8 bits, `comp = 256-m`:

```
q1 = comp*(x >> 8) + (x & 0xFF)          // 14 bits for comp<=39, 16-bit x
q2 = comp*(q1 >> 8) + (q1 & 0xFF)        // 13 bits
q3 = comp*(q2 >> 8) + (q2 & 0xFF)        //  9 bits (simulated max 450, m=217)
q4 = comp*(q3 >> 8) + (q3 & 0xFF)        //  simulated max 255 over all 2^16 inputs
out = (q4 < m) ? q4 : (q4 - m)           // one conditional subtract is sufficient
```

Exactness (brute-forced over all `x ∈ [0,65536)` for every `m ∈ {255,253,251,247,241,239,233,229,
227,223,217}`): `out = x mod m`, and `q4 < 2m` so a single subtract suffices. The simulated maximum
of `q4` is exactly 255 for every `m` in the set, so the 8-bit output never truncates for `m ≤ 255`.

The 32-bit composition is exact because it reduces the top 16-bit limb modulo `m` and then performs
two Horner steps `r ← (r << 8) | next_byte`, each congruent modulo `m`; each 16-bit limb reduction
is exact. The negative fix produces the canonical residue in `[0, m)`.

**Lane 0** is special only because `m_0 = 256` does not fit the 8-bit `nType` argument. The
special case `data & 0xFF` is mathematically the same as reducing modulo 256; §5.4 shows how to
absorb it into a 9-bit uniform reducer.

#### 2.5.2 Stage 2 — multiply by the CRT inverse and center (`t`)

For all lanes (`:119–130`):

```
p_i  = r1_i * inv_i                       // 16-bit unsigned; max 255*255 = 65025
u_i  = red16(p_i, m_i)                    // 8-bit unsigned, 0..m_i-1
t_i  = (u_i > (m_i >> 1)) ? (u_i - m_i) : u_i     // signed 8-bit (ac_int<8,true>)
```

HLS lane 0 uses the same mask trick instead of `red16` (`:130`), which is equivalent because
`inv_0` is not necessarily 1 (e.g. `INV_S[1][0] = 255` for `s=2`); do **not** hardwire lane 0.

`t_i` is the centered representative of `r_i · inv_i (mod m_i)`. For odd `m` it lies in
`[-(m-1)/2, (m-1)/2]`. For `m=256` the pre-cast integer lies in `[-127, 128]`; `+128` is stored as
the 8-bit pattern `0x80` and is read back by `ac_int<8,true>` as `-128` (still congruent mod 256,
magnitude 128), so the set of signed `t` values is `[-128,127]` with `abs(t) <= 128`. This
asymmetry matters only at the `P/2` boundary (risk R4).

#### 2.5.3 Stage 3 — weighted accumulation (`amyi`)

```
mi_i   = P_s / m_j                        // 96-bit, from §1.4
amyi_i = mi_i * t_i                       // signed; |amyi_i| <= P_s/2 by construction
```

Bound: `|t_i| ≤ m_j/2` (with equality only for `m=256`), so
`|amyi_i| ≤ (P_s/m_j)·(m_j/2) = P_s/2`. The HLS computes the product at the full `ac_int`
multiplication width and assigns it to `ac_int<96,true>` (`:154`); because `P_s/2 < 2^94` no bits
are lost for `S_MAX=12`. **An RTL
96×8 multiplier with a 96-bit output is exact; do not truncate the product to fewer than 96 bits
unless `s` is fixed and `W_s` from §1.5 is used.**

#### 2.5.4 Stage 4 — reconfigurable adder tree and `mod P` (balanced reduction)

Define the wrap used after every 2-input addition:

```
wrapP(v):                      // v is a signed W-bit value, |v| <= P
  if (v >  (P >> 1)) return v - P;
  if (v < -(P >> 1)) return v + P;
  return v;
```

HLS exact tree (`:160–181`), with `s = data_in.s`:

```
p[0]  = wrapP(amyi[0]  + amyi[1]);
p[2]  = wrapP(amyi[2]  + amyi[3]);
p[4]  = wrapP(amyi[4]  + amyi[5]);
p[6]  = wrapP(amyi[6]  + amyi[7]);
p[8]  = wrapP(amyi[8]  + amyi[9]);
p[10] = wrapP(amyi[10] + amyi[11]);
p[1]  = wrapP(p[0]  + (s==3 ? amyi[2] : p[2]));
p[9]  = wrapP(p[10] + (s==3 ? amyi[9] : p[8]));
p[3]  = wrapP(p[4]  + (s==3 ? amyi[3] : p[1]));
p[7]  = wrapP(p[6]  + (s==3 ? amyi[8] : p[9]));
p[5]  = wrapP((s==4) ? (p[4] + p[6]) : (p[3] + p[7]));
```

**Equivalent formulation (recommended for RTL).** For chunk `c`, compute the balanced sum of its `s`
terms `amyi[c*s .. c*s+s-1]` with a binary adder tree and one `wrapP` after every 2-input adder:

```
group_sum(c) = tree_wrap(amyi[c*s], ..., amyi[c*s+s-1])
```

This was verified to produce identical output to the HLS tree for random vectors and all five `s`.
Associativity holds because every partial sum is reduced to the unique representative in
`[-P/2, P/2]` before the next add, and any two such representatives sum into `[-P, P]`, where one
`wrapP` suffices. Use this formulation to avoid porting the irregular `s==3`/`s==4` mux tree.

Valid group membership (slot = chunk):

| s | C | slot 0 | slot 1 | slot 2 | slot 3 | slot 4 | slot 5 |
|---:|---:|---|---|---|---|---|---|
| 2 | 6 | lanes 0–1 | 2–3 | 4–5 | 6–7 | 8–9 | 10–11 |
| 3 | 4 | 0–2 | 3–5 | 6–8 | 9–11 | invalid (dup of 3) | invalid |
| 4 | 3 | 0–3 | 4–7 | 8–11 | invalid | invalid | invalid |
| 6 | 2 | 0–5 | 6–11 | invalid (all 12) | invalid | invalid | invalid |
| 12 | 1 | 0–11 | invalid | invalid | invalid | invalid | invalid |

For INT8 bypass, slot `i` = chunk `i` (12 slots valid), see §3.6.

`wrapP` thresholds: **strict** `>` and `<` are used (`:161` etc.), so the result range is the closed
interval `[-P/2, P/2]`. This differs from the software CRT helper, which maps `val >= M/2` to
`val - M` (`crt_reconst/int128_arithmetic.cuh:convert_to_signed_modulo_SM`), i.e. software maps
`+P/2 → -P/2` while this hardware keeps `+P/2`. Only reachable when the scaled dot product is
exactly `±P/2`; the scheme's scaling aims for `< P/2`, but the corner must be decided (R4).

#### 2.5.5 Stage 5 — output slot selection

HLS (`:183–188`, `:204–209`):

```
o[0] = (s==2) ? p[0] : p[1];     o[1] = (s==2) ? p[2] : p[3];
o[2] = (s==2) ? p[4] : p[5];     o[3] = (s==2) ? p[6] : p[7];
o[4] = (s==2) ? p[8] : p[9];     o[5] = p[10];

r[0] = (s==12) ? o[2] : (s==6) ? o[1] : o[0];
r[1] = (s==6)  ? o[3] : (s==4) ? o[2] : o[1];
r[2] = (s==4)  ? o[4] : (s==3) ? o[3] : o[2];
r[3] = (s==3)  ? o[4] : o[3];
r[4] = o[4];
r[5] = o[5];
```

For the valid slots this is exactly `r[c] = group_sum(c)` (table above); the other `r[]` values are
partial sums and are don't-care. RTL should implement `r[c] = group_sum(c)` directly and zero the
rest.

#### 2.5.6 Stage 6 — denormalization and int→FP (`int_fp_change`)

The conversion is in `hls/postprocess/include/int_fp_change_parallel.h:15–124`. It implements
"`R · 2^{-d}` to binary32" with a **one-bit round at the 24-bit boundary and no sticky bit**.

Instantiated as `int_fp_change<ac_int<96,true>, ac_std_float<32,8>, 6>`:
`in_t = 96-bit signed`, `out_t = binary32 payload`, `N` unused. Constants (`:21–31`):
`mantissa_bits=23`, `exponent_bits=8`, `in_w=96`, `out_w=32`, `BIAS=127`, `idx_t=ac_int<7,false>`.

Exact algorithm (all widths as in the HLS):

```
in : signed 96-bit R
d  : signed 10-bit d

sign = R[95]
u    = |R|                                  // 96-bit unsigned
if u == 0: output_bits = 0; done            // +0.0

lz        = leading_zeros(u)                // 0..96; 96 when u==0 (special-cased above)
first1    = 95 - lz                         // 0..95
start     = (first1 > 23) ? first1-23 : 0
useful    = (u >> start) & 0xFFFFFF         // 24 bits, implicit-1 at bit 23

if start > 0:
    round  = (u >> (start-1)) & 1
    useful = (useful + round) & 0xFFFFFF    // NOTE: carry out of bit 23 is DROPPED (bug)
else:
    useful = (useful << (23 - first1)) & 0xFFFFFF   // exact, no lost bits

diff = first1 - d                           // then truncated to signed 10-bit (deType)

case:
  diff >= 128          : exp=255; mant=0                         // ±Inf
  -126 <= diff <= 127  : exp=diff+127; mant=useful[22:0]          // normal
  -150 <= diff <= -127 : sh = -diff-126 (1..24)
                         mant = ((useful >> sh) + ((useful >> (sh-1)) & 1)) & 0x7FFFFF
                         exp = 0                                 // subnormal (carry DROPPED, bug)
  diff < -150          : exp=0; mant=0                            // ±0 (sign kept)

bits = (sign<<31) | (exp<<23) | mant
```

Value assigned: `R · 2^{-d}`, rounded with the single bit above; the subnormal case computes
`mant = round(useful / 2^sh)` and interprets it with exponent `-126` (value
`mant · 2^{-149}`), which is the correct scaling for `-150 ≤ diff ≤ -127`.

Important properties / deviations (all verified against a bit-exact Python model):

1. **Rounding is round-to-nearest, ties away from zero** (not IEEE ties-to-even). Adding the single
   bit at `start-1` is exactly the nearest decision: bit=1 with any lower bits → above half → up;
   bit=0 → below half → down; bit=1 with all lower bits zero → exact tie → up. The missing sticky
   bit does not change the nearest decision; it only means exact ties are resolved away from zero
   instead of to even. Apart from the two carry bugs below, the difference from a correctly-rounded
   (RNE) converter is at most 1 ulp at exact ties (relative error ≤ 2^-23). This matches the CUDA
   helper's 1-bit rounding
   (`int128_arithmetic.cuh:418–419`), whose comment is "round to nearest, tie to away".
2. **Normal mantissa carry is lost.** If `useful = 0xFFFFFF` and `round=1`, the correct result is
   `2^{diff+1}` (mantissa 0, exponent+1) or Inf at the top; the HLS wraps to `0x000000`, yielding
   `2^{diff}` (factor 2 low). Example: `R = 0xFFFFFF800000`, `d = 0` → HLS `2^47`
   (`0x57000000`) instead of `2^48`.
3. **Subnormal mantissa carry is lost.** If the rounded subnormal mantissa reaches `2^23`, the
   correct result is the smallest normal; the 23-bit add wraps to 0. Example: `R = 0xFFFFFF`,
   `d = 150` → HLS `0.0` instead of `2^-126`.
4. `diff` is computed as `deType(first_1_idx - denom_exp)`; the documented `d` range is
   `-104..416`, for which `diff ∈ [-416, 198]` fits signed 10-bit. Outside that range the value is
   silently truncated; add an assertion in RTL.
5. Zero input always yields `+0.0`; a non-zero input that underflows keeps its sign, so `-0.0` is
   produced for negative underflow. (`:114–116` only clears the sign for `R == 0`.)
6. The case split `diff >= 128 → Inf` is correct for a value with msb `diff` (i.e. `≥2^128`), but
   because of bug 2 the `diff=127` all-ones case is wrong in the same way as bug 2.

For an RTL implementation that is *bit-exact to the HLS*, implement the two wrap behaviors
(24-bit `useful` add and 23-bit `mant` add). For a *numerically correct* implementation, carry the
overflow into `exp` (and to Inf/smallest-normal as appropriate); this is a semantics change that
must be recorded in the golden-model delta (R3, §5.5).

#### 2.5.7 Denormalization shift routing

HLS computes slot `si` with `shift_in[2*si+1]` (`postprocess_parallel.h:192`):

```
out_r[si] = int2fp(output_select[si], shift_in[2*si + 1])
```

But the per-chunk shift produced by preprocess is replicated across all `s` lanes of the chunk
(`preprocess_parallel_compressed_ccore.h:182–193`), i.e. lane `c*s + j` carries chunk `c`'s shift.
Comparing the two:

Cell notation: the HLS reads the value on the stated **lane**; `chK` = the shift of chunk `K`
(replicated on lanes `K*s..K*s+s-1` by preprocess).

| s | slot 0 | slot 1 | slot 2 | slot 3 | slot 4 | slot 5 |
|---:|---|---|---|---|---|---|
| 2 | lane1 = ch0 ✔ | lane3 = ch1 ✔ | lane5 = ch2 ✔ | lane7 = ch3 ✔ | lane9 = ch4 ✔ | lane11 = ch5 ✔ |
| 3 | lane1 = ch0 ✔ | lane3 = ch1 ✔ | lane5 = **ch1** ✘ (want ch2) | lane7 = **ch2** ✘ (want ch3) | invalid | invalid |
| 4 | lane1 = ch0 ✔ | lane3 = **ch0** ✘ (want ch1) | lane5 = **ch1** ✘ (want ch2) | invalid | invalid | invalid |
| 6 | lane1 = ch0 ✔ | lane3 = **ch0** ✘ (want ch1) | invalid | invalid | invalid | invalid |
| 12 | lane1 = ch0 ✔ (all 12 lanes carry ch0) | — | — | — | — | — |

So the HLS is correct only for `s=2` and `s=12`. Concrete `s=4` example (generated with the
bit-exact model): chunk values `x = (100, 200, 300)`, `d = (1, 2, 3)`; expected
`(50, 50, 37.5)`; HLS produces `(50, 100, 75)` because slot 1 uses `d=1` and slot 2 uses `d=2`.
Decision: **fix in RTL** (use `shift[si*s]`, or better pass a `[C]`-element per-chunk shift vector
to postprocess); this is a semantics change vs the HLS, so the HLS golden model must be patched for
comparison, otherwise the two will disagree for `s ∈ {3,4,6}` (R1).

For a fixed `s` at elaboration, generate the shift as a `C`-element vector (`C = 12/s`) and index it
by slot. This removes the mux and the bug and halves the shift port for large `s`.

#### 2.5.8 Worked reference numbers (for the RTL TB)

| Case | Input | Expected |
|---|---|---|
| CRT, s=2, chunk `x=4663` | lane0 `4663`, lane1 `4663` (any congruent values) | `4663.0` |
| CRT, s=3, chunk `x=2^22+12345` (=4 206 929 < P/2) | lanes congruent to `x` mod 256/255/253 | exact `x` as binary32 (exact < 2^24) |
| CRT, s=12, `x` up to ±(P/2) | lanes congruent to `x` | `int2fp(x, d)` |
| int2fp normal | `R=100`, `d=0` | `0x42C80000` (100.0) |
| int2fp shift | `R=100`, `d=1` | `50.0` (`0x42480000`) |
| int2fp negative | `R=-100`, `d=0` | `-100.0` (`0xC2C80000`) |
| int2fp zero | `R=0`, any `d` | `0x00000000` |
| int2fp overflow | `R=(1<<94)`, `d=-40` (diff≈134) | `0x7F800000` (+Inf) |
| int2fp underflow | `R=1`, `d=200` | `0x00000000` |
| int2fp neg underflow | `R=-1`, `d=200` | `0x80000000` (-0.0) |
| normal carry bug | `R=0xFFFFFF800000`, `d=0` | HLS `0x57000000` (2^47); correct `2^48` |
| subnormal carry bug | `R=0xFFFFFF`, `d=150` | HLS `0x00000000`; correct `2^-126` |

### 2.6 Input validity rules

The HLS performs **no** checks. For RTL and for the golden model, define:

* `s ∈ {2,3,4,6,12}` for the normal path; `s=1` is bypass-only; anything else is illegal.
  `s=0` indexes `INV_S[-1]`/`MOD_PRODUCT_*[-1]` (out of bounds) — must be guarded (R5).
* `d` is a 10-bit signed value; the documented practical range is `-104..416`. `diff = msb - d`
  must stay in `[-512, 511]` (10-bit signed). Add an assertion or saturate.
* Residue inputs from SIMD may be any 32-bit value congruent to the chunk dot product; the stage-1
  reduction handles the full `int32` range, including `-2^31`.
* The exact-reconstruction invariant is `|x| ≤ P_s/2` for every chunk (enforced by the preprocess
  scaling, not here). If it is violated, the CRT output wraps modulo `P_s` (aliasing); the RTL
  cannot detect this without extra range checks.
* Valid output slots: `C = 12/s`; slots `≥ C` are don't-care. Recommend zeroing them.

### 2.7 RTL microarchitecture proposal (per lane)

Suggested module `ozcore_postprocess` with parameters `S_MAX=12`, `W=96` (or `W_s` if fixed `s`),
`S_CFG=0` (runtime `s`) or fixed.

Pipeline (II=1), 6 stages:

| Stage | Work | Notes |
|---|---|---|
| 0 | input skid/register | `data`, `shift`, `s`; one frame/cycle |
| 1 | ROM lookup + stage-1 reduction (3 limb reductions × 4 base-256 rounds) | 11 (or 12) small multipliers by `comp` (6b), adders ≤16b; lane-0 mask absorbed by 9-bit reducer |
| 2 | `r1·inv` (8×8) + stage-2 reduction (4 rounds) + center | 12 small multipliers |
| 3 | `mi·t` (96×8 signed) | 12 multipliers; or 1 multiplier × 12 cycles if area-bound |
| 4 | group adder trees + `wrapP` | 12-input, 96-bit adders; `P` from ROM |
| 5 | `int2fp` for `C` slots | 1..6 instances; leading-zero + 24-bit normalize + pack |

Resource sketch (S_MAX=12, W=96): 12 small reduction multipliers, 12 × 96×8 multipliers
(≈ 12 × 800 gates), about 20 × 96-bit adders, 6 × (96-bit LZC + shifter), 5 ROMs
(`(s,i) → {m,comp,inv}` and `(s,i) → mi`, plus `P`). At 28 nm this matches the artifact's
`107,861 µm²` per lane order-of-magnitude. For `s=2` with `W=17`, the multipliers and adders shrink
by ≈5.6×, which is the recommended first normal-path configuration.

Options:

* **Share one `mi` multiplier across the 12 lanes** (12 cycles per frame) — only viable if the
  frame rate is ≤ 1/12 of the clock, or if the top is time-multiplexed; output alignment then
  needs a frame buffer.
* **Share one postprocess across the N SIMD lanes** (N cycles/frame) — same trade-off.
* **Fix `s` at elaboration** (`S_CFG`) to remove the ROM muxes, tree reconfiguration, and the
  output mux; the in-band `s` field is then checked and ignored. Recommended for phase B.
* Keep the `int2fp` bit-exact (bugs included) behind a parameter `INT2FP_BITEXACT` (default 1 for
  equivalence runs, 0 for the corrected variant). Do not mix modes in one regression.

### 2.8 Postprocess equivalence checklist

A postprocess RTL is "bit-exact to the HLS" iff all of the following hold:

1. Lane→modulus mapping is `i % s` for `s ∈ {2,3,4,6,12}` and no other `s` reaches the datapath.
2. Stage-1 reduction is the 3-limb `red16` composition with the negative fix, lane 0 included.
3. Stage-2 multiply is by `INV_S[s-1][i%s]` (not 1 for lane 0) and the center rule is
   `u > m>>1 → u-m`, with 8-bit signed storage.
4. `mi = P_s/m_j` exactly (96 bits), product not truncated below 96 bits.
5. `wrapP` uses strict `>` / `<` and `P>>1`, after **every** 2-input add.
6. Valid slots are `0..C-1` with slot `c` = lanes `c*s..c*s+s-1`.
7. `int2fp` reproduces the 24-bit round with dropped carry and the 23-bit subnormal add with
   dropped carry, plus the `R==0 → +0` and `diff<-150 → signed 0` behaviors.
8. `d` routing is the HLS `shift[2*si+1]` **only if** the goal is bug-for-bug equivalence; the
   intended behavior is chunk `si`'s shift (see R1). State explicitly which one is implemented.
9. `s` is 4 bits and legal values are enforced; `s=0` cannot index tables.

---

## 3. Top / control stage

### 3.1 Hierarchy and instances

`top_parallel<K,N>` (`hls/top/include/top_parallel.h:13–96`) instantiates:

| Instance | Count | Type | Cite |
|---|---:|---|---|
| `preprocess_inst` | 1 | `preprocess_parallel<K,N>` | :33 |
| `simd_engine_inst[i]` | N | `simd_engine_parallel<K,N>` | :34 |
| `postprocess_inst[i]` | N | `postprocess_parallel` (no template args ⇒ S_MAX=12, out width 6) | :35 |
| `path_chooser_inst[i]` | N | `path_chooser<simd_out_pkg, postp_in_pkg, outType, S_MAX>` | :36 |
| `output_selector_inst[i]` | N | `output_selector<outType, S_MAX, S_MAX/2>` | :37 |
| `output_aligner_inst` | 1 | `output_aligner<outType, N, S_MAX>` | :38 |

Channels (`:41–52`):

| Channel | Count | Depth pragma | Payload |
|---|---:|---:|---|
| `simd_in_ch` | N+1 (chain: preprocess→lane0→…→lane N-1) | 0 | `simd_in_pkg` = preprocess `out_pkg_t` |
| `simd_out_ch` | N | 0 | `simd_out_pkg` |
| `posp_in_ch` | N | 0 | `postp_in_pkg` |
| `posp_out_ch` | N | 0 | `postp_out_t` (6×32) |
| `bypass_ch` | N | 0 | `ac_array<outType,12>` |
| `selected_out_ch` | N | **N** | `ac_array<outType,12>` |

`SIMD_ID[i] = i` for `i=0..N-1` (`:54–62`). `run(top_in, top_out)` (`:64–95`) executes
preprocess → N SIMD lanes → N path choosers → N postprocess → N selectors → 1 aligner, in that
order, inside one invocation.

The SIMD chain is **functionally a broadcast**: each `simd_engine_parallel` forwards its input
package unchanged (`simd_engine_parallel_ccore.h:123–130`), so lane `i` sees exactly the frame that
preprocess produced. RTL may distribute the frame to all N lanes in parallel instead of chaining;
this removes N-1 combinational hops and is semantically identical (weight loading is filtered by
`col_no`, not by position).

The concrete top is `top_parallel_wrap` (`:100–125`), parameterized by macros `K_VAL`/`N_VAL`,
defaults **4 and 4** (`:100–107`). `hls/modules.json`'s `"K":8,"N":8` metadata is **not** wired into
`catapult.tcl` (no compile flags are generated), so the synthesized top in this artifact is
K=4, N=4 unless the flow is changed. Do not quote the top area as K=8/N=8 without checking this.

### 3.2 Interfaces / packages (exact widths)

`top_params<K,N>` (`hls/top/include/params_parallel.h:15–44`) defines:

```
outType      = ac_std_float<32,8>                       // 32-bit binary32 payload
s_t          = ac_int<4,false>
top_in_pkg   = preprocess_parallel_params<K,N>::in_pkg_t
simd_in_pkg  = simd_parallel_params<K,N>::in_pkg_t      // = preprocess out_pkg_t
simd_out_pkg = simd_parallel_params<K,N>::out_pkg_t
postp_in_pkg = postprocess_parallel_params<true>::in_pkg_t
postp_out_t  = postprocess_parallel_params<true>::out_vec_t   // 6 x 32
top_out_t    = ac_array<ac_array<outType,N>, S_MAX>     // [slot 0..11][lane 0..N-1]
```

Preprocess input package (`hls/preprocess/include/params_parallel.h:49–53`, `params.h:55–59,83–88`):

```
in_pkg_t {
  ac_array<ac_int<16*K,false>, 12> data;   // 12 "lanes", each K 16-bit elements
  cfg_t cfg;                               // { E:4, s:3, dTypeA:4, dTypeB:4 } (logical)
  bool  is_weight;
}
```

Preprocess output = SIMD input package (`preprocess/include/params_parallel.h:55–62`,
`simd_engine/include/params_parallel.h:31`):

```
out_pkg_t / simd_in_pkg {
  ac_array<ac_array<ac_int<8,true>,K>, 12> data;  // 12 x K signed int8 residues
  ac_array<ac_int<9,true>, 12> shift;             // shift_t (9-bit signed)
  ac_int<3,false> s;                              // S_t (3 bits!) -- see R2
  bool intint;
  bool is_weight;
  ac_int<log2ceil(N),false> col_no;
}
```

SIMD output package (`simd_engine/include/params_parallel.h:34–39`):

```
out_pkg_t {
  ac_array<ac_int<32,true>, 12> data;   // 384 bits
  ac_array<ac_int<10,true>, 12> shift;  // 120 bits, de_t
  ac_int<4,false> s;                    // s_t (4 bits)
  bool intint;
}
```

Postprocess input = same `data`/`shift`/`s` plus the dead `intint` (§2.2); postprocess output is
6×32. The selector widens to 12×32; the aligner transposes to 12×N×32.

Logical payload widths (no handshake bits):

| Package | K=8 | K=128 | Formula |
|---|---:|---:|---|
| `top_in_pkg.data` | 1536 | 24576 | 12·K·16 |
| `top_in_pkg.cfg` | 15 | 15 | 4+3+4+4 |
| `simd_in_pkg.data` | 768 | 12288 | 12·K·8 |
| `simd_in_pkg.shift` | 108 | 108 | 12·9 |
| `simd_in_pkg.s/intint/is_weight/col_no` | 3+1+1+log2N | same | |
| `simd_out_pkg` | 509 | 509 | 384+120+4+1 |
| `postp_in_pkg` | 509 | 509 | 384+120+4+1 |
| `postp_out_t` | 192 | 192 | 6·32 |
| `bypass/selected` | 384 | 384 | 12·32 |
| `top_out_t` | 12·N·32 (1536 for N=4) | same | 12·N·32 |

Per-SIMD-lane weight storage: `12·K·8` bits (`768` for K=8, `12288` for K=128) plus `12·9` bits of
`e_reg`. For N=4, K=128 this is 49,152 flops of weight registers — a major area item to consider
before committing to the reduced configuration.

The config is **in-band per frame**, not a top-level register. There is no start/busy/done, no
address map, no CSRs.

### 3.3 Frame types and config encoding

A frame is one `top_in_pkg` transaction. Two types:

| Frame | `is_weight` | Meaning | Output |
|---|---|---|---|
| weight | 1 | load one column's weights into the matching SIMD lane | none |
| activation | 0 | compute one row/chunk for all N columns | one `top_out_t` frame |

`cfg.dTypeA` is the activation dtype; `cfg.dTypeB` is the weight dtype
(`preprocess_parallel_compressed_ccore.h:154–158` uses exactly this convention). `cfg.E` is the
exponent width of the **current frame's** data: the TB sets `cfg.E = WE` on weight frames and
`cfg.E = IE` on activation frames (`tb_top_parallel.cpp:176–181`, `:205–210`). `cfg.s` is the
modulus count and is used for both frame types.

`dType` encoding (`preprocess/include/params.h:90–98`):

| value | enum name | actual use in this datapath |
|---:|---|---|
| 0 | `FP16` | fp16 |
| 1 | `BF16` | bf16 |
| 2 | `AC_FP16` | **treated as FP8** by the scaler flags (`curr_is_fp8`, ccore:156) |
| 3 | `INT8` | int8 |
| 4 | `UINT8` | not exercised |
| 5 | `INT4` | not exercised |
| 6 | `UINT4` | not exercised |

`cfg.s` is only **3 bits** (`S_t = ac_int<3,false>`; `preprocess/include/params.h:28,59`), so values
`≥ 8` silently wrap. In particular `cfg.s = 12` becomes 4. This is a real integration bug:
`top/tb/tb_top_parallel.cpp:55` declares `s_in = 12` as `pre_params::S_t`, so the "s=12" TB actually
runs `s=4`, and `S/s_in = 3` chunks. The postprocess input `s` is 4 bits, but the value can never
exceed 7 because it originates here. **The shared spec must widen `S_t` to 4 bits** (R2).

### 3.4 Channel / handshake semantics

HLS semantics (what the source assumes):

* A module reads only when `ch.available(1)` is true (`postprocess_parallel.h:64`,
  `path_chooser.h:25`, `simd_engine_parallel_ccore.h:92`, `preprocess...ccore.h:135`) or uses
  `nb_read` (`output_selector.h:26,33`).
* Writes are blocking: the producer may not proceed until the consumer accepts
  (`out_ch.write`, `select_out_ch.write`, `top_out_ch.write`).
* FIFO depths are fixed by pragmas (`top_parallel.h:41–52`): 0 for everything except
  `selected_out_ch`, which is `N`. Depth 0 is Catapult's "wire" (no extra buffering).
* There is no frame ID, sequence number, or backpressure status outside the channels.

RTL contract to implement (recommended):

1. Every channel is `valid`/`ready` with one frame per beat. All payload fields are stable while
   `valid=1`.
2. `top_in` accepts one frame per cycle when `top_in_ready=1`. Weight frames and activation frames
   share the port and are distinguished by `is_weight`.
3. `postprocess`, `path_chooser`, `output_selector` are stateless streaming blocks; they must
   accept a new frame every cycle once their output register is free.
4. `output_aligner` is an **N-way join**: it emits one output frame only when all N
   `selected_out_ch` lanes are valid; otherwise it deasserts `ready` on all lanes. It must not emit
   a partial frame.
5. The aligner output is one frame per activation frame, at the input activation-frame rate
   (subject to downstream `ready`).
6. No reordering is allowed. The HLS's output selector uses "postprocess priority, else bypass"
   (`output_selector.h:26–36`); if a lane ever has both queues non-empty (mixed intint and FP
   frames in flight), frames can be **reordered** relative to input. For RTL, use a single unified
   per-lane queue with a mode tag, or require the host to drain between `intint` and non-`intint`
   frames (R7).
7. Backpressure: if the aligner stalls, all N lanes stall; if one lane stalls, all stall (lockstep).
   There is no per-lane independent progress in this design.
8. Weight frames produce no output but must still be accepted and must update state in order.
   Do not drop or coalesce them.

The HLS `run()` has no clock/reset in its signature; Catapult adds them at the interface. For the
RTL, use one clock and a reset whose values match §3.9.

### 3.5 Weight-load control and counters

All control state lives in preprocess and SIMD; there is no top-level scheduler.

#### 3.5.1 preprocess `col_counter`

* Declared `int col_counter = N - 1` and set to `N-1` in the constructor
  (`preprocess_parallel_compressed_ccore.h:116,120`).
* On a **weight** frame only: if `col_counter == 0` → `N-1`, else decrement
  (`:312–319`). Activation frames do not change it.
* The value **before** the decrement is exported as `data_out.col_no` on that frame (`:309`).
  Therefore the first weight frame after reset is tagged `col_no = N-1`, the next `N-2`, …,
  the N-th is tagged 0.
* Width: `log2ceil(N)` bits (`counter_params<maxN>::width`, `global_params.h:94–98`); for N=4 it
  is 2 bits, so values 0..3 are representable.

#### 3.5.2 weight shift accumulation (`sa_latched`)

Used only for the mixed int-weight × float-activation mode:

* `reset_sa = is_weight && (col_counter == N-1)` → `sa_latched = (1<<(shift_bw-1))-1 = 255`
  (`:67–69`, `shift_bw=9`).
* `update_sa = (cfg.dTypeB == 3) && is_weight`; on such a frame
  `sa_latched = min(sa_latched, max(scaler_shift, 0))` (`:63,70–72`).
* `apply_adjust = (cfg.dTypeB == 3) && !is_weight && (cfg.dTypeA != 3)`; if set,
  `sa = sa_latched`, else `sa = 0`; then `shift = shift + sa` (`:74–75`).
* Consequence: the postprocess's `d` for a chunk includes the minimum positive weight shift of the
  last weight tile in this mode. For all-float modes `sa=0`; for int×int the bypass ignores `d`.

`sa_latched` has **no reset/initial value in the HLS** (it is only written on a `reset_sa` weight
frame). RTL must reset it to 255 to be deterministic (R13).

#### 3.5.3 SIMD weight registers

Per lane `i` (`simd_engine_parallel_ccore.h:71–79,103–108`):

```
weight_reg[12][K]   // int8 signed per modulus lane
e_reg[12]           // 9-bit signed, weight-side shift
constructor: all zero
if (is_weight && col_no == SIMD_ID[i]):
    weight_reg = data_in.data;        // all 12 lanes
    e_reg      = data_in.shift;       // 9-bit
```

The lane does **not** load on activation frames, and does not check that a full N-frame tile has
arrived. The host contract is: send exactly N weight frames (one per column, tagged with descending
`col_no`) before using the lane; otherwise stale/partial weights are used silently. Add a
weight-load watchdog/status in the RTL if robustness matters.

Column mapping: because `col_no` descends from `N-1` to 0 and lane `k` loads the frame with
`col_no == k`, the net mapping is **lane k ⇔ column k** provided the host sends the frame for
column `c` while `col_no = c` (i.e. columns in descending order `N-1, N-2, …, 0`). The top TB does
exactly this by reversing the column index when packing (`tb_top_parallel.cpp:165–167` vs the
reference at `:147`). Document this in the host/driver spec; a wrong order silently transposes the
output.

#### 3.5.4 Other counters

* `SIMD_ID[i]` is a constant per lane (`top_parallel.h:54–62`).
* No frame counter, no output counter, no tile counter in hardware. The TB has `out_counter`
  (`tb_top_parallel.cpp:153,238`) but that is software.
* `preprocess` uses `col_counter` only for weight frames; there is no activation-frame counter.

### 3.6 `S_MAX` slot scheduling

The 12 physical lanes are a 2-D array: `C` chunks × `s` moduli, with `C = 12/s`.

| Mode | `s` | `C` | Input lanes the host must pack | preprocess behavior | postprocess | valid output slots |
|---|---:|---:|---|---|---|---:|
| INT8×INT8 (intint) | 1 (nominal) | 12 | all 12 (12 independent chunks) | int branch copies all 12 lanes (`ccore:223–240`) | bypass | 12 |
| float / mixed, s=2 | 2 | 6 | lanes 0..5 | expand to 12 residue lanes | normal | 6 |
| float / mixed, s=3 | 3 | 4 | lanes 0..3 | expand | normal | 4 |
| float / mixed, s=4 | 4 | 3 | lanes 0..2 | expand | normal | 3 |
| float / mixed, s=6 | 6 | 2 | lanes 0..1 | expand | normal | 2 |
| float / mixed, s=12 | 12 | 1 | lane 0 | expand | normal | 1 (unreachable today, R2) |

Expansion in preprocess (float current frame; `ccore:267–295`): each of the `C` input lanes is a
chunk's K-vector; core `c` computes `q_base` and `shift` for that chunk; lane `c*s+j` is produced by
reducing `q_base[c]` modulo `m_j` (j=0 uses the mask `q_base & (0xFF >> q_shift)`). `base_select`
and `moduli_select` encode exactly `c = i/s`, `j = i%s` (`ccore:198–221`). For the int-current
branch (`ccore:241–266`) the chunk's scaled int8 value (the 8-bit truncation of `q_base[c]`) is
used as-is; stage 1 of postprocess restores modularity when the accumulator is reduced; for intint
(`ccore:223–240`) the raw bytes are copied to all 12 lanes.

Consequences for the top/control spec:

* The host's frame payload size depends on the mode: `C·K` useful values in `C` input lanes
  (float/mixed), or `12·K` values in 12 lanes (INT8 intint). The HLS interface always carries 12
  lanes; unused lanes are don't-care (but must not create X-propagation into used slots — in the
  float path they are ignored by `base_select`).
* The number of **columns** `N` and **chunks** `C` are independent: one activation frame computes
  `N·C` partial dot products (N columns × C chunks). The final result for an output element is the
  FP32 sum over chunks and over K-tiles/frames, done in software.
* The output slots carry chunks, not columns. `top_out[slot][lane]` = chunk `slot`, column `lane`.
  A consumer must sum over slots `0..C-1`.
* In INT8 intint mode the "slots" are the 12 chunks; `s` is irrelevant to the datapath and all 12
  slots are valid. The TB's `s_in=12` (→4) with INT8 therefore only initializes 3 lanes
  (`S/s_in = 3`) and reads 3 slots; it is a lane-0..2 smoke test, not a 12-chunk test.

### 3.7 Path chooser, output selector, output aligner

#### 3.7.1 `path_chooser` (`hls/top/include/path_chooser.h:9–45`)

```
if (simd_out_ch.available(1)) {
    in_data = simd_out_ch.read();
    if (in_data.intint) {
        for i in 0..11: bypass_data[i].set_data(in_data.data[i]);   // raw int32 bits
        bypass_ch.write(bypass_data);
    } else {
        postp_in_data.data  = in_data.data;
        postp_in_data.shift = in_data.shift;
        postp_in_data.s     = in_data.s;
        postp_in_ch.write(postp_in_data);
    }
}
```

* Exactly one of the two outputs is written per input frame.
* `set_data` writes the **bit pattern**; the 32-bit int32 accumulator is carried in an
  `ac_std_float<32,8>` slot and later read with `.data()` by software/TB
  (`tb_top_parallel.cpp:232`). There is no numeric int→float conversion in the bypass.
* `intint` is not copied to `postp_in_data` (the field exists but is unused).
* No valid/ready; one input frame → one output frame on one of two channels.

#### 3.7.2 `output_selector` (`hls/top/include/output_selector.h:12–38`)

```
if (posp_out_ch.nb_read(fp_data)) {                 // priority 1
    for i in 0..11: int_data[i] = (i < 6) ? fp_data[i] : outType(0);
    select_out_ch.write(int_data);
} else if (bypass_ch.nb_read(int_data)) {            // priority 2
    select_out_ch.write(int_data);
}
```

* In FP mode, slots 6..11 are forced to binary32 `+0.0` (bit pattern 0). In INT8 bypass mode all 12
  slots come from the SIMD accumulators, so slots 6..11 are **not** zero.
* The postprocess priority can reorder mixed frames (R7).
* No output if neither input is available.

#### 3.7.3 `output_aligner` (`hls/top/include/output_aligner.h:10–40`)

```
all_available = AND over i in 0..N-1 of selected_out_ch[i].available(1);
if (all_available) {
    for i in 0..N-1:
        sel_data = selected_out_ch[i].read();
        for j in 0..11: top_out_data[j][i] = sel_data[j];
    top_out_ch.write(top_out_data);
}
```

* It is a strict N-way barrier + transpose, **not** a FIFO: it waits for one item from every lane.
* `top_out_t[slot][lane]`, slot = chunk (FP) or chunk (INT8), lane = output column.
* It does not carry `s`, `intint`, or a valid-slot mask. The consumer must know the mode and the
  number of valid slots (`C` or 12). Recommend adding a sideband `s_o[3:0]`/`chunks_o[3:0]` in the
  RTL (not in HLS) to make the output self-describing (R17).
* The aligner's `selected_out_ch` depth is N, the only elastic buffer in the chain
  (`top_parallel.h:51–52`); all other channels are depth 0.
* If any lane is disabled/unused, the aligner hangs forever (no timeout). N must equal the number
  of instantiated/active lanes.

### 3.8 Throughput, latency, and lockstep invariants

* HLS processes one frame per `run()` call; all N lanes see the same frame. All submodules carry
  `#pragma hls_pipeline_init_interval 1`, so Catapult's scheduled design targets II=1 per module.
* **Invariant I1 (lockstep):** all N lanes receive every activation frame; none may skip or stall
  independently. The weight-load filter (`col_no == SIMD_ID`) is the only per-lane divergence and
  it does not consume an activation frame.
* **Invariant I2 (one-in/one-out):** each activation frame produces exactly one `top_out_t` frame;
  each weight frame produces none. The ratio of output frames to activation frames is 1.
* **Invariant I3 (chunk consistency):** all lanes of one chunk (`i/s` equal) must belong to the same
  frame and same `s`. The host must not change `s` in the middle of a frame (trivially true) and
  should not change it in the middle of a K-tile without draining.
* **Invariant I4 (weight tile):** exactly N weight frames per tile, descending `col_no`, before the
  activation frames that use them. No hardware check exists.
* Latency: choose a fixed pipeline latency in RTL (e.g. 8–16 cycles for preprocess+SIMD+postprocess+
  aligner). The TB must not assume availability in the same cycle. The HLS TB reads immediately
  (`tb_top_parallel.cpp:215`) because HLS executes the whole chain per call; this does not transfer
  to RTL.
* Throughput: with II=1 and no backpressure, the steady-state activation rate is 1 frame/cycle and
  the output rate is 1 frame/cycle (wide 12·N·32-bit frames). For K=128, a 24,576-bit input frame
  per cycle is not routable; plan a K-serialized variant (R16).

### 3.9 State and reset

| State | Owner | Width | HLS init | RTL reset |
|---|---|---|---:|---|
| `weight_reg[12][K]` | each SIMD lane | 12·K·8 | 0 (`simd...ccore.h:71–79`) | 0 |
| `e_reg[12]` | each SIMD lane | 12·9 | 0 | 0 |
| `col_counter` | preprocess | `int` in HLS; only log2ceil(N) bits are exported as `col_no` | N-1 (`ccore:116,120`) | N-1 |
| `sa_latched` | preprocess | 9 signed | **none** (uninitialized) | 255 (`(1<<8)-1`) |
| `SIMD_ID[N]` | top | log2ceil(N) each | 0..N-1 (`top_parallel.h:57–62`) | constants |
| everything else | chooser/post/selector/aligner | — | stateless | — |

`#pragma hls_fifo_depth` buffers are not state to reset beyond their valid bits.

The Catapult flow configures a clock named `clk` with async active-low reset `arst_n` and sync reset
`rst` (`hls/scripts/catapult.tcl:131–136`); pick one convention for the RTL and state it in the
top-level spec.

### 3.10 Proposed RTL top interface

Parameters: `K` (8..128), `N` (4), `S_MAX=12`, `MODE` (INT8-only vs full), optional `S_CFG`.

```
module ozcore_top #(parameter int K=8, N=4, ...) (
  input  logic clk,
  input  logic rst_n,

  // input stream: one frame per beat
  input  logic                     in_valid,
  output logic                     in_ready,
  input  logic [12*K*16-1:0]       in_data,      // 12 lanes x K x 16b (INT8: low byte)
  input  logic [3:0]               in_E,
  input  logic [3:0]               in_s,         // 4b here; the HLS preprocess field is only 3b (R2)
  input  logic [3:0]               in_dTypeA,
  input  logic [3:0]               in_dTypeB,
  input  logic                     in_is_weight,

  // output stream: one frame per activation frame
  output logic                     out_valid,
  input  logic                     out_ready,
  output logic [12*N*32-1:0]       out_data,     // [slot][lane][31:0]
  output logic [3:0]               out_s,        // recommended sideband (not in HLS)
  output logic                     out_intint    // recommended sideband (not in HLS)
);
```

Optional sideband/robustness additions (not in HLS, do not break bit-exact payload comparison):
`out_s`, `out_intint`, `weight_load_done`, `err_illegal_s`, `err_weight_tile_short`.

---

## 4. Testbench stimulus and expected protocol

### 4.1 Postprocess TB (`hls/postprocess/tb/tb_postprocess_parallel_ccore.cpp`)

What it actually does:

| Item | Value | Cite |
|---|---|---|
| DUT | `postprocess_parallel` (channel wrapper from `postprocess_parallel_ccore.h`) | :33 |
| Inputs | `in_pkg_t`: 12 lanes of `accType` (32-bit), 12 shifts, `s` | :35–38 |
| Stimulus | each lane independently uniform in `[-65536, 65535]` | :43, :61 |
| Shift | all zero | :62 |
| `s` values | `{2, 3, 4, 6}` only | :46 |
| Expected active outputs | `{3, 2, 1, 1}` | :47 |
| Iterations | 2 per `s` | :57 |
| Check | none: `test_pass` is never assigned false | :27, :93–100 |
| Output | prints the 6 output floats | :85–89 |

Deficiencies that matter for RTL verification:

1. **The 12 lanes are independent random values**, so they are not residues of a common integer.
   The CRT reconstruction is mathematically meaningless; the TB only exercises toggling and
   latency. It cannot detect a wrong `inv`, wrong `mi`, wrong lane mapping, or a broken tree.
2. **`active_outputs` is wrong.** The correct valid-slot counts are `C = 12/s`:
   `s=2 → 6`, `s=3 → 4`, `s=4 → 3`, `s=6 → 2` (and `s=12 → 1`). The TB's `{3,2,1,1}` understates
   each count (2×, 2×, 3×, 2×) and would mislead a scoreboard writer.
3. **No `s=12`** — the only configuration that exercises the full 96-bit `P`, the largest `mi`,
   and the single-group path.
4. **No shift values** — the entire denormalization/int2fp path is tested only with `d=0`.
5. **No boundary values**: zero, ±1, `-2^31`, `±P/2`, the int2fp carry boundaries, and the
   subnormal/overflow thresholds are absent.
6. **No checks at all**, and the closing message always says "All tests passed!".

SCVerify context: the Catapult flow enables `/SCVerify` (`hls/scripts/catapult.tcl:95`) and runs
cosim (`:245–247`). SCVerify compares the RTL/C++ outputs for this stimulus, i.e. it can establish
"RTL == HLS C++ for these vectors", **not** "postprocess is correct". Since the HLS itself contains
the bugs in §2.5.7 and §2.5.6, SCVerify would bless a bug-for-bug RTL. The RTL project needs an
**independent** golden model (§4.3).

Proposed self-checking postprocess protocol (standalone TB / UVM sequence):

For each `s ∈ {2,3,4,6,12}`:
1. `C = 12/s`; `P = Π_{j<s} m_j`.
2. For each chunk `c ∈ [0,C)`:
   * choose `x_c` from `{0, +1, -1, ±(P/2-1), ±(1<<23), ±((1<<23)+1), random(-P/2+1, P/2-1)}`;
   * choose `d_c` from `{-104, -23, -1, 0, 1, 23, 126, 127, -126, -127, -150, -151, 416}`
     (only the meaningful subset for the chosen `x_c`);
   * for every `j`: `data[c*s+j] = ((x_c mod m_j) + k*m_j)` with `k` random such that the value
     fits int32 (this proves the stage-1 reducer and the modularity of the whole datapath);
     `shift[c*s+j] = d_c` (replicated; this is what preprocess produces).
3. Drive the frame with `s`, wait for `valid_o`, and compare the `C` valid slots against
   `int2fp_model(x_c, d_c)` (bit pattern). Slots `≥ C` are ignored.
4. Include a variant where all lanes are congruent to the **same** `x` (single chunk repeated) to
   check the lane mapping; a wrong `i%s` mapping will fail for `s ≥ 3`.
5. Include `s=0`, `s=1`, `s=5` as error/robustness tests (expect a defined error flag, no hang, no
   out-of-range table read).
6. Include `int2fp` vectors directly (bypass CRT) for the carry cases in §2.5.8.

A single frame per cycle with random backpressure on `ready_i` is sufficient to cover the
handshake; the block is stateless, so no ordering checks are needed.

### 4.2 Top TB (`hls/top/tb/tb_top_parallel.cpp`)

What it actually does (default compile-time constants):

| Item | Value | Cite |
|---|---|---|
| `M1` | 4 (rows per group) | :9 |
| `W_DT_IN` / `I_DT_IN` | 1 (BF16) / 2 (treated as FP8) | :11–12 |
| widths / exponents | `W_WIDTH=16, I_WIDTH=8, WE=8, IE=4` | :14–17 |
| DUT | `top_parallel_wrap` with `K=K_VAL`, `N2=N_VAL` (both default 4) | :20, `top_parallel.h:100–107` |
| `S` | 12 (`pre_params::S_max`) | :25 |
| `N` | `N2*2 = 8` (total columns over 2 blocks) | :26 |
| `M` | `M1*2 = 8` (rows) | :27 |
| `s_in` | `pre_params::S_t s_in = 12` → **4** (3-bit type) | :55 |
| `S/s_in` | 3 chunks | derived |
| Weight order | frame `n2` packs column `N2-1-n2`; `col_no` descends N-1..0 | :165–167 |
| Reference | `out_ref[n][m][s][n2] = Σ_k weight_fp[..] * act_fp[..]`, FP values | :136–152 |
| Check | none; `test_pass` never set false | :49, :246–253 |
| Output read | immediately after each `top_inst.run`, if available | :213–239 |
| Print | `.data()` only when both dtypes are INT8, else float | :231–235 |

Frame sequence per `n` block (`n = 0..N/N2-1`, i.e. 2 blocks):

1. For `n2 = 0..N2-1`: pack `in_array[0..S/s_in-1]` with the weights of column `N2-1-n2` for the
   chunks, set `cfg.dTypeA=I_DT_IN, cfg.dTypeB=W_DT_IN, cfg.E=WE, cfg.s=s_in,
   is_weight=true`, write, call `run` (`:155–185`). **No output is expected** for these frames.
2. For `m = 0..M-1`: pack the activation row `m`, set `cfg.E=IE`, `is_weight=false`, write, call
   `run`, then read one output (`:187–243`).
3. The reference for output frame `out_counter` is indexed by `n = out_counter/M`,
   `m = out_counter%M` (`:224`).

Deficiencies and traps:

1. **`s_in=12` is truncated to 4 by `S_t` (3 bits)**, so the default run is `s=4`, `C=3`, not
   `s=12`. All "s=12" claims about this TB are false. For INT8, the TB initializes only 3 of the 12
   lanes (`S/s_in = 3`) and reads only 3 slots.
2. **Default dtype is BF16 weight × FP8 activation**, not INT8; the `dType` value 2 is FP8 in the
   datapath (see §3.3), even though the enum calls it `AC_FP16`.
3. **The reference is exact floating point**, while the DUT is a scaled/quantized integer
   datapath; the two differ by quantization and by the `int2fp` rounding. The TB prints both and
   never compares. In fact, with `s=4` the HLS's shift bug (§2.5.7) makes slots 1 and 2 wrong, and
   the TB would not notice.
4. **INT8 mode is not exercised by default.** If enabled (`W_DT_IN=I_DT_IN=3`), the raw output is
   `.data()` and can be compared exactly; but only 3 lanes are initialized because of the `s`
   truncation. Use `s=1` (12 chunks) for a real INT8 test.
5. **No latency tolerance**: the TB reads immediately after `run`; an RTL pipeline will need a
   valid/wait loop.
6. The weight column reversal is easy to misread; net effect is lane `k` ↔ column `k` only if the
   host sends frames in descending `col_no` order with matching data (see §3.5.3).

Proposed self-checking INT8 top protocol (phase A, §5):

```
K=8, N=4, S_MAX=12, s=1, dTypeA=dTypeB=3 (intint=1), C=12

for each weight tile:
  for c = N-1 downto 0:
     frame.data[chunk] = K int8 weights of output column c, chunk = 0..11
     frame.is_weight = 1, cfg.s = 1
     drive; check no output frame for the next L cycles (L = latency)
for each activation row r:
  frame.data[chunk] = K int8 activations of chunk 0..11
  frame.is_weight = 0, cfg.s = 1
  drive; wait for one output frame
  for slot in 0..11, lane in 0..3:
     expected = Σ_k W[lane][slot][k] * A[r][slot][k]        // exact int32
     check out[slot][lane].data == expected
```

Bound: `|Σ| ≤ K·128·128`; for K=8 it is 131,072 (fits int32 with huge margin). Generate weights and
activations from `{0, ±1, ±127, -128, random}` and include rows that make each lane zero, max
positive, max negative.

For the FP/mixed path, an end-to-end self-checking TB requires the full golden chain
(preprocess + SIMD + postprocess). Until that exists, verify the top with the postprocess bypassed
(INT8) and verify postprocess standalone (§4.1); do not claim end-to-end FP correctness from the
shipped TB.

### 4.3 Golden model contract

The RTL project must ship an independent model implementing, bit-exactly:

1. the lane→(chunk, modulus) map and the s-dependent constants (§1.4);
2. the stage-1/stage-2 reduction (`red16`, 3-limb signed composition, negative fix, center rule);
3. `wrapP` with strict comparisons and `P>>1`;
4. the output slot map;
5. `int_fp_change` in two modes: `HLS_BITEXACT` (carry-dropping, §2.5.6) and `CORRECTED`
   (carry-propagating; use only after the delta is approved);
6. for the top, the preprocess lane expansion and the SIMD int8 accumulation. The postprocess-only
   model does not need preprocess.

Recommended flow: a Python model validated against the HLS on 10k+ random vectors per `s` (the
model in Appendix D reproduces the HLS for `s=2,3,4,6,12` on the CRT and int2fp tests above), then
a testbench that reads vectors generated by the model and compares RTL outputs bit-for-bit.

### 4.4 What SCVerify covers, and what it does not

* It compares the DUT against the C++ model for the same stimulus. This is useful for
  "RTL == HLS" but not for "HLS == math".
* The preprocess TB is currently a stub: it creates channels, prints a banner, and returns without
  ever calling the DUT (`hls/preprocess/tb/tb_preprocess_parallel_compressed_ccore.cpp:118–130`),
  so SCVerify would compare nothing for preprocess.
* The postprocess TB stimulus is not CRT-consistent (§4.1) and the top TB is print-only (§4.2).
* Therefore: **do not accept an RTL sign-off based on SCVerify alone.** Require the §4.3 model and
  the §5.7 vector set.

---

## 5. Minimal reduced configuration for the first RTL port

### 5.1 Target parameters

| Parameter | First port | Stretch | Notes |
|---|---|---|---|
| `K` | 8 | 16/32/64/128 | power of two; postprocess is K-independent |
| `N` | 4 | 4 | 4 SIMD columns/lanes |
| `S_MAX` | 12 | 12 | hard-coded by tables |
| dtype | INT8×INT8 | add BF16 | `dTypeA=dTypeB=3`, `intint=1` |
| `s` | 1 (12 chunks) | 2,3,4,6,12 | postprocess bypass in phase A |
| `ACC_BW` | 32 | 32 | signed |
| `MOD_BW` | 8 | 8 | |
| `DE_BW` | 10 | 10 | unused in phase A |
| clock | 3.3 ns (303 MHz) | same | artifact flow `hls/modules.json` `clock_period: 3.3` |
| top_in payload | 12·K·16 bits (HLS) or 12·K·8 (INT8-only, new packing) | | §5.4 item 11 |
| top_out payload | 12·N·32 = 1536 bits | | |

### 5.2 Phased plan

| Phase | Content | Verification |
|---|---|---|
| P0 | Python/C++ golden model of postprocess + int2fp; vector generator | model vs HLS on 10k vectors/s |
| P1a | postprocess RTL, fixed `s=12` (C=1, 96-bit), bypass-free | §4.1 vectors, all int2fp boundaries |
| P1b | postprocess RTL, fixed `s=2` (C=6, 17-bit) | §4.1 vectors; area check |
| P2 | top/control RTL: preprocess-int, N=4 SIMD INT8, chooser, selector, aligner, **postprocess bypassed** | §4.2 INT8 protocol, exact int32 |
| P3 | enable postprocess normal path (`s=2` first, then 3/4/6 after R1 fix; `s=12` after R2 fix) | §4.1 + end-to-end golden |
| P4 | K=128 variant (K-serialized interface recommended, R16) | same vectors, throughput/area |

Phase A ("first RTL") is P2: it delivers a working INT8 top with all control/alignment paths and
exact integer outputs. It deliberately excludes the 96-bit CRT and the FP conversion; those are
P1/P3. This matches the already-existing INT8 SIMD core work
(`experiments/ozcore-rtl/simd_int8`, 123/123 vectors, 19,301 µm² at K=8).

### 5.3 Phase A datapath (exact)

1. Host packs 12 chunks × K int8 values in `top_in.data` as 16-bit lanes (HLS packing) or 8-bit
   lanes (new packing). For the HLS-compatible packing, the int8 sits in bits `[7:0]` of each
   16-bit word; preprocess extracts `slc<8>(j*16)` (`preprocess...ccore.h:145`).
2. preprocess (INT8×INT8 branch) copies all 12 lanes to `data_out.data` unchanged
   (`ccore:223–240`). It also computes shifts, but they are irrelevant to the bypass; the RTL can
   omit the scaler entirely in an INT8-only build if `data_out.shift` is tied to 0 and the SIMD
   `e_reg`/`shift_out` are unused.
3. SIMD (per lane): `acc[i] = Σ_{k<K} weight[i][k] * data[i][k]` signed int8 × int8 → int32
   (`simd_engine_parallel_ccore.h:33–51`). All 12 lanes are independent chunks.
4. path chooser: `intint=1` → all 12 `bypass` slots = `acc` bit patterns (`path_chooser.h:28–35`).
5. output selector: bypass path chosen (postprocess queue empty) (`output_selector.h:33–36`).
6. output aligner: `top_out[slot][lane] = lane_acc[slot]` (`output_aligner.h:28–38`).
7. Expected: `out[slot][lane] = Σ_k W[column=lane][chunk=slot][k] * A[row][chunk=slot][k]`, exact
   int32. There is no scaling, no shift, no rounding, no CRT: a bit-exact comparison is possible.

Notes:
* Set `cfg.s=1` (not 12). With `s=1`, `C=12`, and the host packs 12 chunks; the HLS `intint` path
  ignores `s`, but software should use the semantically correct value.
* Weight order: N frames per tile, descending `col_no`; the frame for column `c` must be the one
  tagged `col_no=c` (§3.5.3).
* No output for weight frames; one output per activation frame.
* Reset `col_counter=N-1`, `weight_reg=0`, `e_reg=0`.

### 5.4 Simplifications that preserve semantics

Each of these was checked against the HLS arithmetic (proof sketch in parentheses):

1. **Fix `S_MAX=12` at elaboration.** The tables and muxes only make sense for 12. (Direct.)
2. **ROM instead of the per-`s` constant muxes.** `(s,i) → {m,comp,inv,mi}` with the contents of
   §1.4 is exactly the mux output (decoded exhaustively for all five `s`).
3. **Generic group tree** (`group_sum(c)` with `wrapP` after each 2-input add) instead of the
   irregular tree. (Balanced representative is unique; verified on random vectors for all `s`.)
4. **Unified reducer with 9-bit modulus.** Feed `m_0=256, comp=0` to the same `red16`-style
   primitive; `q4 ≤ 255 < 256` so it degenerates to the low byte, and the negative fix reproduces
   two's-complement mod 256. This removes the lane-0 special case
   (`postprocess_parallel.h:117,130`). (Verified for all 32-bit values by construction; the
   primitive with `m=256` is exact for its full 16-bit input range.)
5. **Narrow datapath `W_s = bits(P_s)+1`** when `s` is fixed (17/25/33/49/96). All intermediates are
   bounded by `±P_s`; it is a pure sign-extension of the HLS 96-bit values.
6. **Fix `s` per elaboration (`S_CFG`).** Removes the ROM muxing, the reconfigurable tree, and the
   output mux; the in-band `s` is checked and ignored. Arithmetic is identical for that `s`.
7. **Drop the dead `intint` field** from the postprocess input package (never read; §2.2).
8. **Merge core + wrapper** into one module (the split exists only for Catapult ccore pragmas).
9. **Broadcast instead of the N-lane SIMD chain** (the forwarded package is unchanged;
   `simd...ccore.h:123–130`).
10. **Zero the invalid postprocess output slots** (HLS leaves partial sums; they are don't-care and
    never selected by the HLS's own out-muxes for valid slots).
11. **New 8-bit INT8 packing** (`12·K·8` instead of `12·K·16`) if the host is also new. The HLS
    preprocess only uses the low byte (`ccore:145`), so this is equivalent; it halves the top input
    bus. Keep the 16-bit packing if the HLS TB/host is the reference.
12. **Omit the preprocess scaler and shift network in an INT8-only build.** The bypass ignores
    `shift`; the SIMD `e_reg` is then dead. This removes the largest preprocess sub-block. (Do not
    do this in a build that also supports FP; keep it behind `MODE_INT8_ONLY`.)
13. **Omit the postprocess block in phase A** and hardwire the bypass path, while keeping the port
    reserved. This is the single biggest area saving (≈0.43 mm² for N=4 full-width).

### 5.5 Changes that are *not* semantics-preserving (must be recorded)

* Fixing the denormalization shift routing (§2.5.7) — changes outputs for `s ∈ {3,4,6}`.
* Fixing the int2fp mantissa carries (§2.5.6) — changes outputs at rare boundaries.
* Changing the `±P/2` boundary rule (strict `>` vs `>=`) — changes `x = ±P/2`.
* Changing ties-away to ties-to-even (RNE) — changes exact ties only (up to 1 ulp). Adding a sticky
  bit alone does not change the nearest decision (the HLS is already nearest).
* Dropping the 12-slot duplication in INT8 bypass (if the consumer expects 12) — interface change.
* Widening `cfg.s` from 3 to 4 bits — interface change; required to reach `s=12`.
* Replacing the selector priority with a unified queue — changes ordering for mixed frames.

Keep these behind compile-time flags and state clearly, in the regression report, which mode was
compared against the HLS.

### 5.6 Expected resources / area (order of magnitude, 28 nm)

| Item | Artifact number | Reduced-config expectation |
|---|---:|---|
| postprocess per lane (96-bit) | 107,861 µm² | full: ×N=4 ≈ 0.43 mm² |
| postprocess per lane (`s=2`, 17-bit) | — | ≈5.6× smaller than 96-bit |
| output selector (128 cols) | 4,244 µm² | shrinks with N |
| path chooser (128 cols) | 4,413 µm² | shrinks with N |
| output aligner (128 cols) | 319,434 µm² | N=4: 12·4·32 = 1536 flops + mux, much smaller |
| INT8 SIMD core K=8 | 19,301 µm² (existing RTL, 96 MACs, combinational) | N=4 lanes: 4× the datapath + weight regs |
| weight regs | — | N·12·K·8 = 3072 flops (K=8), 49,152 (K=128) |

Phase A (bypass) area is dominated by the SIMD lanes and weight registers, not by postprocess.
Phase P1b (`s=2`) is the first configuration where postprocess area matters; use it to calibrate
the `W_s` scaling assumption.

### 5.7 Verification plan for the reduced config

1. Unit: `red16`/3-limb reducer exact for all 16-bit inputs and all `m`, all 32-bit random inputs
   (compare to `%`); `center8`; `wrapP`; `mi·t` bounds.
2. Postprocess: §4.1 vector set for `s=12` and `s=2` first, then 3/4/6, then 12 after the `s` fix.
   At least 10k random + all boundary vectors. Compare bits.
3. Top INT8: §4.2 protocol, at least 10k random frames, including zero/max rows and weight-tile
   boundaries; check no output on weight frames, exactly one on activation frames, and correct
   ordering.
4. Handshake: random `ready` backpressure; ensure no frame loss/duplication and no deadlock;
   assert the aligner never emits a frame with a lane missing.
5. Reset: reset in the middle of a weight tile, then reload; verify weights are not stale.
6. Timing: synthesize the postprocess and top with the 3.3 ns target; the 96-bit multiply/tree path
   will need pipelining; report the achieved period.
7. Regression report: state the mode (HLS-bit-exact vs corrected) and the exact bug flags used.

---

## 6. Risks and open questions

Severity: **H** = wrong silicon / silent data corruption; **M** = interface or verification gap;
**L** = documentation/robustness.

| ID | Sev | Risk | Evidence | Recommendation / decision needed |
|---|---|---|---|---|
| R1 | H | Denormalization shift is routed with `shift[2*si+1]`, wrong for `s=3,4,6` slots ≥1 | `postprocess_parallel.h:192`; preprocess shift replication `ccore:182–193`; §2.5.7 example | Fix RTL to use chunk `si`'s shift (`shift[si*s]`); patch the HLS golden model or compare only `s=2/12` until fixed. Decide whether the HLS bug is in scope for "bit-exact". |
| R2 | H | `cfg.s` is 3 bits; `s=12` truncates to 4; top TB's `s_in=12` is really 4 | `preprocess/include/params.h:28,59`; `tb_top_parallel.cpp:55` | Widen `S_t`/`in_s` to 4 bits (or define `s` as a 4-bit field in the top package) in the shared preprocess spec; update host and TB. Until then, restrict supported `s` to `{2,3,4,6}` and treat `s=12` as unreachable. |
| R3 | H | int2fp drops the 24-bit and 23-bit mantissa carries | `int_fp_change_parallel.h:59–64,102`; §2.5.8 vectors | Choose `INT2FP_BITEXACT` (for HLS equivalence) or `CORRECTED` (for numerical correctness); document both and run both regressions. |
| R4 | M | `+P/2` representative differs from software (`wrapP` strict `>` vs software `>=`) | `postprocess_parallel.h:161`; `crt_reconst/int128_arithmetic.cuh:convert_to_signed_modulo_SM` | Confirm the scaling invariant is `< P/2`; if not, align the boundary rule. Add a directed test at `±P/2`. |
| R5 | H | No guard for illegal `s`; `s=0` indexes `INV_S[-1]`/`MOD_PRODUCT_*[-1]`; `s=5,7..11,13..15` produce wrong lane mapping/tree | `postprocess_parallel.h:68,135` (no check); muxes only encode five `s` | Implement a legal-`s` check and a defined error output; the top should refuse/flag frames with `s ∉ {1,2,3,4,6,12}` (1 only for bypass). |
| R6 | M | INT8 mode uses `s=1` (12 chunks) but the TB uses `s=12` (truncated to 4) and only initializes 3 lanes | `ccore:223–240`; `tb_top_parallel.cpp:55,83–108` | Define INT8 `s=1` in the host spec; rewrite the TB to fill 12 lanes. |
| R7 | M | Output selector priority can reorder mixed `intint`/FP frames; no tags | `output_selector.h:26–36`; §3.7.2 | Use a unified per-lane queue with a mode tag, or require software to drain between modes. Add a sequence tag if mixed traffic is real. |
| R8 | M | HLS channels have no explicit ready; the aligner barrier is the only join; a disabled lane deadlocks | `output_aligner.h:22–27`; `top_parallel.h:41–52` | Define the valid/ready contract in §3.4; add a timeout/error counter for aligner stall; N must equal active lanes. |
| R9 | H | Shipped TBs do not check anything and are not CRT-consistent; SCVerify only proves RTL==HLS | §4.1, §4.2, `catapult.tcl:95,245–247` | Independent golden model + self-checking vectors is a deliverable, not optional. |
| R10 | M | `d` range/`diff` truncation: `deType(first1-d)` wraps outside ~`[-416,198]`; `d` documented `-104..416` | `int_fp_change_parallel.h:69–70`; §2.5.6 item 4 | Assert `d` range in RTL; define saturation/error behavior. |
| R11 | M | INT8 packing ambiguity: bypass reads two's-complement low byte; the scaler's int path expects sign at bit 15 + magnitude in `[6:0]` | `ccore:145`; `scaler_compressing_see_mantissa_v2.h:260–268`; `tb_top_parallel.cpp:34–44` vs the (gutted) preprocess TB packing | Standardize one INT8 word encoding in the shared preprocess spec; for phase A only the low byte matters. |
| R12 | L | Weight column order (descending `col_no`) is implicit; a wrong order silently transposes | §3.5.3; `tb_top_parallel.cpp:165–167` | Document in the driver spec; add a weight-tile watchdog/status. |
| R13 | L | `sa_latched` has no reset value in HLS | `ccore:67–72` | Reset to 255; state it. |
| R14 | L | 96-bit `mi`/`P` storage split as 64+32 with signed 32-bit upper fields; `mi[0]` uses only 24 upper bits | `ozaki_tables.h:170–222`; §1.4 | Use unsigned 96-bit constants in RTL; do not misinterpret the signed upper word. |
| R15 | M | Per-SIMD weight storage is huge (12·K·8 per lane); for K=128,N=4 it is 49k flops | `simd...ccore.h:71–79`; §3.2 | Decide K granularity and whether weights are shared/time-multiplexed; include in the area budget. |
| R16 | H | The HLS top port is one full K-vector per beat: 12·K·16 bits (24,576 for K=128); single-cycle frames are not routable at 3.3 ns | `params.h:55`; `tb_top_parallel.cpp:64–70` | For K≥32, define a K-serialized interface (e.g. 8 or 16 elements/beat) with an internal accumulation buffer; keep the HLS-wide frame only for the unit TB. |
| R17 | L | `top_out_t` has no `s`/`intint`/valid-slot mask; slots 6..11 are zero in FP but valid in INT8 | `output_selector.h:28–29`; `output_aligner.h:33–37` | Add `out_s`, `out_intint`, and (optionally) a valid-slot mask as sideband in RTL, or a mode register in the driver. |
| R18 | M | `s`/mode changes mid-tile are not guarded; the selector/aligner can mix frames from different modes | §3.4, §3.8 | Require a drain at mode/s change; add a generation tag or a CSR that blocks changes until idle. |
| R19 | L | The top TB's default is BF16×FP8, not INT8; the "FP8" dType value 2 is named `AC_FP16` | `tb_top_parallel.cpp:11–12`; `preprocess/include/params.h:90–98`; `ccore:156` | Rename/document in the shared spec; keep the table above. |
| R20 | M | The postprocess `intint` field is dead; a port may accidentally rely on it | `params_parallel.h:55`; `path_chooser.h:38–41` | Remove from the RTL package and from the golden model. |

Open questions to resolve before P1:

* Q1: Is the goal "bit-exact HLS" or "mathematically correct OzCore"? This decides R1/R3/R4 and the
  golden-model mode.
* Q2: Is `s` runtime-variable in the final accelerator, or fixed per model? A fixed `s` gives a much
  smaller postprocess (§5.4 item 6).
* Q3: Is K fixed at 128 (paper) or variable? The top interface width depends on it (R16).
* Q4: Does the system need INT8 and FP modes interleaved in one stream? If yes, R7/R18 must be
  fixed; if no, a drain-at-mode-change contract is enough.
* Q5: What is the area/throughput budget for the reduced config? It decides whether N postprocess
  instances or one shared/time-multiplexed instance is used.

---

## 7. What must be shared with the preprocess / SIMD specs

These items are cross-stage contracts; they must appear identically in all three specs.

| # | Item | Value / convention | Evidence |
|---:|---|---|---|
| S1 | `S_MAX`, `MOD_BW`, `ACC_BW`, `COMP_BW`, `DE_BW`, `S_BW` | 12, 8, 32, 6, 10, 4 | `global_params.h:23–38` |
| S2 | `s` encoding and width | 4 bits; legal `{1,2,3,4,6,12}`; 1 only for INT8 bypass; **do not use the 3-bit preprocess `S_t`** | `params.h:28,59`; `tb_top_parallel.cpp:55`; R2 |
| S3 | Lane map | lane `i` = chunk `i/s`, modulus `i%s`; `C=12/s` | §2.4; `ccore:198–221` |
| S4 | Residue format | signed int8, centered in `[-m/2, m/2]`; for `m=256`, `+128` appears as `-128` | `ccore:282–295`; §2.5.2 |
| S5 | Accumulator format | signed int32; stage-1 handles full int32 range | `global_params.h:55`; §2.5.1 |
| S6 | Shift format | per input 9-bit signed `shift_t`; total `d` 10-bit signed `de_t`; `d = e_reg(weight) + shift_in(activation)`; semantics `out = int·2^{-d}` | `global_params.h:58–59`; `simd...ccore.h:49`; §2.5.6 |
| S7 | Shift replication | chunk `c`'s shift replicated on lanes `c*s..c*s+s-1`; postprocess must index `c`, not `2c+1` | `ccore:182–193`; R1 |
| S8 | Weight-load protocol | N frames/tile, descending `col_no`; lane `k` loads `col_no==k`; `e_reg=shift`; no completion status | §3.5; `simd...ccore.h:103–108` |
| S9 | `intint` generation/consumption | set by preprocess = `(dTypeA==3 && dTypeB==3)`; consumed only by path chooser; postprocess must not see it | `ccore:306`; `path_chooser.h:28`; R20 |
| S10 | Frame contract | weight frame → no output; activation frame → exactly one output frame; all N lanes lockstep | §3.8 |
| S11 | Chunk count / valid slots | `C=12/s`; postprocess slots `0..C-1`; INT8 bypass 12 slots; slots 6..11 zero in FP | §3.6, §3.7.2 |
| S12 | Exact-reconstruction invariant | `abs(x) <= P_s/2` per chunk, enforced by scaling; postprocess cannot detect aliasing | §2.6 |
| S13 | Scale/shift semantics of preprocess | `q_base ≈ value·2^{shift}`; `sa` adjustment for mixed int-weight mode | `ccore:63–85`; §3.5.2 |
| S14 | Reset values | `col_counter=N-1`, `sa_latched=255`, weights/e=0 | §3.9; R13 |
| S15 | INT8 word packing | HLS: int8 in bits `[7:0]` of each 16-bit element; scaler int path expects sign at bit 15 + magnitude | `ccore:145`; `scaler_compressing_see_mantissa_v2.h:260–268`; R11 |
| S16 | Value of `d` for the first/last chunk | preprocess core `c` produces `shift[c]`; postprocess chunk `c` uses it | `ccore:182–193`; §2.5.7 |
| S17 | Mode/s change policy | drain between `intint` and FP, and between different `s`, unless tags are added | R7/R18 |

Change requests to the preprocess/SIMD specs (needed for a clean RTL):

1. Widen the frame `s` field to 4 bits and use the same encoding everywhere (S2).
2. Define the INT8 packing once (low byte two's complement vs sign-magnitude) and use it in both
   the bypass and scaler paths (S15).
3. Export a per-chunk shift vector `[C]` (or document the exact lane replication) and have
   postprocess consume `shift[c]`; fix the HLS bug in the golden model (S7, R1).
4. State the `sa` adjustment behavior and its range; expose `sa_latched` reset (S13, R13).
5. State the weight-load/tile contract and the column ordering in the driver interface (S8, R12).
6. Decide the K serialization of the top input for K≥32 (R16) and propagate it to the
   SIMD/preprocess port definitions.
7. Add a mode/generation tag to the output (or a CSR) if mixed-mode traffic is supported (R17/R18).

---

## 8. Acceptance criteria for the RTL milestone

A milestone is accepted only when all of the following are attached:

1. Golden model (Appendix D) and vector set (at least the §4.1/§4.2 boundary classes), with a hash
   of the vectors and the exact mode flags (HLS-bit-exact vs corrected).
2. RTL vs model bit-exact comparison: 0 mismatches on ≥10k random vectors per `s`, plus all
   boundary vectors.
3. Top INT8 phase A: 0 mismatches on ≥10k frames, including weight-tile boundaries, zero/max
   rows, reset-in-tile, and random backpressure.
4. Documented deviations: R1/R3/R4 decisions, `s` width, INT8 packing, and any interface
   narrowing, each with the affected test set.
5. Synthesis report (area + achieved period) for the reduced config, with the K/N/s settings and
   the library/flow stated (the artifact's numbers are TSMC 28 nm FDSOI at 3.3 ns; do not compare
   across libraries).
6. A one-page "what is still not verified" list (FP end-to-end, s=12 reachability, mixed-mode
   ordering, K=128 timing).

---

## Appendix A — `INV_S` rows used by the reference model

Full table: `hls/common/include/ozaki_tables.h:229–242`. Rows for the supported `s`
(`INV_S[s-1][j]`, `j=0..s-1`):

| s | inverses |
|---:|---|
| 2 | 255, 1 |
| 3 | 171, 127, 211 |
| 4 | 17, 32, 21, 182 |
| 6 | 167, 146, 53, 243, 206, 184 |
| 12 | 185, 211, 124, 76, 72, 231, 45, 78, 45, 217, 10, 149 |

Identity: `INV_S[s-1][j] · (P_s/m_j) ≡ 1 (mod m_j)`, verified for all rows.

## Appendix B — Exact HLS selection code (for bit-exact re-derivation)

The RTL should use the ROM of §1.4, not these muxes. They are listed so a reviewer can diff the
generated ROM against the HLS:

* `yi` (inverse) mux: `postprocess_parallel.h:68–79`.
* `moduli_r` mux: `:81–92`.
* `comp_r` mux: `:94–105`.
* `mod_product` (`mi`) mux: `:138–149`.
* adder tree: `:160–181`.
* `output_select`: `:183–188`.
* final output mux: `:204–209`.
* ccore equivalents: `postprocess_parallel_ccore.h:67–105,130–144,154–196`.

Example of the mapping encoded by the muxes (s=4): `moduli_r[6] = (s==4)? m2 : ... = m_{6%4}`,
`mod_product[9] = (s==4)? mi[1] = mi_{9%4}`, `yi[10] = (s==4)? INV_S[3][2]`, etc. Every entry is
`index = lane % s`, which is why the ROM formulation is exact.

## Appendix C — int2fp reference implementation (bit-exact pseudocode)

```
function int2fp_hls(R: signed[95:0], d: signed[9:0]) -> bits[31:0]:
    if R == 0: return 0
    sign = R[95]
    u    = R[95] ? (-R) : R                  // 96-bit unsigned two's complement abs
    first1 = msb_index(u)                    // 95 - clz(u)
    start  = max(first1 - 23, 0)
    useful = (u >> start) & 0xFFFFFF
    if start > 0:
        useful = (useful + ((u >> (start-1)) & 1)) & 0xFFFFFF    // carry dropped
    else:
        useful = (useful << (23 - first1)) & 0xFFFFFF
    diff = trunc10(first1 - d)
    if diff >= 128:          exp = 255; mant = 0
    elif diff >= -126:       exp = diff + 127; mant = useful[22:0]
    elif diff >= -150:       sh = -diff - 126
                             mant = ((useful >> sh) + ((useful >> (sh-1)) & 1)) & 0x7FFFFF
                             exp = 0
    else:                    exp = 0; mant = 0
    return (sign << 31) | (exp << 23) | mant
```

Corrected variant: in the two rounding adds, if the add overflows (bit 24 for normal, bit 23 for
subnormal), increment `exp` (and handle `exp == 255` → Inf; for subnormal, `exp = 1, mant = 0`).

## Appendix D — Validated Python golden model (skeleton)

The following was used to validate §2.5 and §4.1; it reproduces the HLS CRT exactly for all
`s ∈ {2,3,4,6,12}` and the int2fp bit patterns above. It is a compact reference for the RTL TB
generator (not production code).

```python
MODS=[256,255,253,251,247,241,239,233,229,227,223,217]
COMP=[0,1,3,5,9,15,17,23,27,29,33,39]
INV=[[1,1,1,1,1,1,1,1,1,1,1,1],
     [255,1,1,1,1,1,1,1,1,1,1,1],
     [171,127,211,1,1,1,1,1,1,1,1,1],
     [17,32,21,182,1,1,1,1,1,1,1,1],
     [55,251,123,80,246,1,1,1,1,1,1,1],
     [167,146,53,243,206,184,1,1,1,1,1,1],
     [201,214,195,168,36,149,41,1,1,1,1,1],
     [225,83,180,158,68,132,33,115,1,1,1,1],
     [77,242,119,221,106,230,164,146,161,1,1,1],
     [15,46,83,64,217,18,66,131,34,54,1,1],
     [209,142,90,177,63,240,205,150,147,100,163,1],
     [185,211,124,76,72,231,45,78,45,217,10,149]]

def red16(x,m):                      # exact for 0<=x<2^16, m in 217..255
    c=256-m
    for _ in range(4): x=c*(x>>8)+(x&0xFF)
    return x if x<m else x-m

def red32(x,m):                      # signed 32-bit -> [0,m)
    neg=x<0; a=(-x)&0xFFFFFFFF if neg else x
    r=red16(a>>16,m); r=red16((r<<8)|((a>>8)&0xFF),m); r=red16((r<<8)|(a&0xFF),m)
    return (m-r) if (neg and r) else r

def center8(u,m):
    v=u-m if u>(m>>1) else u
    v&=0xFF
    return v-256 if v>=128 else v

def int2fp_bits(R,d):                # bit-exact HLS
    if R==0: return 0
    sign=1 if R<0 else 0; u=(-R)&((1<<96)-1) if R<0 else R
    first1=u.bit_length()-1; start=max(first1-23,0)
    useful=(u>>start)&0xFFFFFF
    if start>0: useful=(useful+((u>>(start-1))&1))&0xFFFFFF
    else:       useful=(useful<<(23-first1))&0xFFFFFF
    diff=((first1-d+512)&1023)-512
    if diff>=128:      exp,mant=255,0
    elif diff>=-126:   exp,mant=diff+127,useful&0x7FFFFF
    elif diff>=-150:
        sh=-diff-126; mant=((useful>>sh)+((useful>>(sh-1))&1))&0x7FFFFF; exp=0
    else:              exp,mant=0,0
    return (sign<<31)|((exp&0xFF)<<23)|mant

def post(data, shift, s):            # data[12] int32, shift[12] int, s valid
    P=1
    for j in range(s): P*=MODS[j]
    def wrapP(v):
        if v>(P>>1): return v-P
        if v<-(P>>1): return v+P
        return v
    t=[]
    for i in range(12):
        j=i%s; r1=(data[0]&0xFF) if i==0 else red32(data[i],MODS[j])
        t.append(center8(red16((r1*INV[s-1][j])&0xFFFF,MODS[j]),MODS[j]))
    a=[(P//MODS[i%s])*t[i] for i in range(12)]
    p=[0]*11
    p[0]=wrapP(a[0]+a[1]); p[2]=wrapP(a[2]+a[3]); p[4]=wrapP(a[4]+a[5])
    p[6]=wrapP(a[6]+a[7]); p[8]=wrapP(a[8]+a[9]); p[10]=wrapP(a[10]+a[11])
    p[1]=wrapP(p[0]+(a[2] if s==3 else p[2]))
    p[9]=wrapP(p[10]+(a[9] if s==3 else p[8]))
    p[3]=wrapP(p[4]+(a[3] if s==3 else p[1]))
    p[7]=wrapP(p[6]+(a[8] if s==3 else p[9]))
    p[5]=wrapP((p[4]+p[6]) if s==4 else (p[3]+p[7]))
    o=[p[0] if s==2 else p[1], p[2] if s==2 else p[3],
       p[4] if s==2 else p[5], p[6] if s==2 else p[7],
       p[8] if s==2 else p[9], p[10]]
    r=[o[2] if s==12 else (o[1] if s==6 else o[0]),
       o[3] if s==6 else (o[2] if s==4 else o[1]),
       o[4] if s==4 else (o[3] if s==3 else o[2]),
       o[4] if s==3 else o[3], o[4], o[5]]
    return [int2fp_bits(r[i], shift[2*i+1]) for i in range(6)]   # HLS routing; use shift[i*s] for the fix
```

Usage: choose `x_c`, set `data[c*s+j] = (x_c % m_j) + k*m_j` for random `k`, set
`shift[c*s+j] = d_c`, call `post`, compare `bits2float(out[c])` with `x_c * 2^{-d_c}` (the CRT path)
or compare bits directly for the int2fp path.

## Appendix E — Citation index (quick lookup)

| Topic | File:line |
|---|---|
| global widths | `hls/common/include/global_params.h:23–38,49–71` |
| moduli/complements | `hls/common/include/ozaki_tables.h:35–38,65–68` |
| `INV_S` | `hls/common/include/ozaki_tables.h:229–242` |
| `mi` / `P` tables | `hls/common/include/ozaki_tables.h:170–222` |
| postprocess params/types | `hls/postprocess/include/params.h:17–45`; `params_parallel.h:23–61` |
| postprocess body | `hls/postprocess/include/postprocess_parallel.h:44–211` |
| postprocess ccore | `hls/postprocess/include/postprocess_parallel_ccore.h:44–196` |
| lane muxes | `postprocess_parallel.h:68–105,138–149` |
| stage-1/2 reduction | `postprocess_parallel.h:111–130`; `iterated_new_s12_scalar.h:30–95`; `new_single_s12.h:17–58` |
| tree / `mod P` | `postprocess_parallel.h:157–181` |
| output mux / shift routing | `postprocess_parallel.h:183–209,192` |
| int2fp | `int_fp_change_parallel.h:42–123` |
| top params | `hls/top/include/params_parallel.h:15–44` |
| top hierarchy/channels | `hls/top/include/top_parallel.h:33–95` |
| top wrapper defaults | `hls/top/include/top_parallel.h:100–125` |
| path chooser | `hls/top/include/path_chooser.h:17–43` |
| output selector | `hls/top/include/output_selector.h:19–36` |
| output aligner | `hls/top/include/output_aligner.h:17–39` |
| preprocess lane expansion | `hls/preprocess/include/preprocess_parallel_compressed_ccore.h:154–193,198–295` |
| preprocess intint / col_no | `hls/preprocess/include/preprocess_parallel_compressed_ccore.h:223–240,306–319` |
| preprocess `S_t` width | `hls/preprocess/include/params.h:28,59,83–98` |
| SIMD core / wrapper | `hls/simd_engine/include/simd_engine_parallel_ccore.h:29–51,85–133` |
| SIMD packages | `hls/simd_engine/include/params_parallel.h:31–39` |
| postprocess TB | `hls/postprocess/tb/tb_postprocess_parallel_ccore.cpp:20–101` |
| top TB | `hls/top/tb/tb_top_parallel.cpp:9–253` |
| flow / SCVerify | `hls/scripts/catapult.tcl:95,131–136,245–247`; `hls/modules.json` |

---

*End of specification.*



