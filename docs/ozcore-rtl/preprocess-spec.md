# OzCore Preprocess Stage — RTL Porting Specification

Status: extracted from the Catapult HLS C++ in the artifact, read-only.
Scope: the **parallel compressed preprocess** (`preprocess_parallel<K,N>`), its
`preprocess_parallel_core`, `scaler`, `element_shift_fn`, and the (missing)
`base_shift_mod_vec` modulo reducer.
Target: a hand-written RTL block that is functionally (bit-)exact to the HLS
C++ for a reduced configuration, with an explicit list of HLS quirks and open
risks.

All paths below are relative to the HLS root

```
HLS = reproduction/ozcore/ozcore-artifact/src/hw/synth/hls
```

Citation form is `HLS/<path>:<line>`. Line numbers refer to the artifact as
checked out in this workspace (the Zenodo zip of the same artifact was also
checked and contains the same files; see Risk R1).

---

## 1. Module hierarchy and parameterization

### 1.1 Hierarchy

```
preprocess_parallel<K,N>                         HLS/preprocess/include/preprocess_parallel_compressed_ccore.h:93
├── preprocess_parallel_core<K,N> core[6]        :114   (ozaki_npu::S_MAX/2 = 6, always)
│   ├── scaler<K> scaler_inst                    :36
│   │   └── arr_max_compress<E_max,M_max,K,log2K,8>   scaler_...v2.h:185
│   └── element_shift_fn<K>() × K                preprocess_...ccore.h:85
│       (free function, see scaler_...v2.h:127)
└── base_shift_mod_vec<19,120,8,6,8,true,true,K> modops[11]   :111-112 (S_MAX-1)
```

`shifter<K>` in `HLS/preprocess/include/shifter.h` is **not instantiated** by
this design. It is an older implementation of the same `element_shift` math
(`shifter.h:39-124`); `element_shift_fn` in
`scaler_compressing_see_mantissa_v2.h:127-158` is the function actually used.
Do not port both.

`preprocess_parallel_core` is a `ccore` (`preprocess_...ccore.h:43-44`); the
wrapper is a normal `interface` block (`:124-125`). Both are annotated
`#pragma hls_pipeline_init_interval 1`.

The two `.cpp` files are identical template instantiations, differing only in
include style:

- `HLS/preprocess/src/preprocess_parallel_compressed_ccore.cpp:1-9` — ccore flow,
  `K_VAL=32, N_VAL=32` defaults.
- `HLS/preprocess/src/preprocess_parallel_compressed.cpp:1-9` — full-block flow,
  same defaults.

`modules.json` uses `K=4,N=4` for the ccore entry
(`HLS/modules.json:102-119`) and `K=128,N=128` for the published-area
full-block entry (`HLS/modules.json:392-410`, area 4.961 mm² at 3.3 ns).

### 1.2 Parameters

| Symbol | Value / derivation | Notes | Source |
|---|---|---|---|
| `K` | template, default 4 | elements per channel/plane | `params.h:16`, `params_parallel.h:23` |
| `N` | template, default 8 | weight columns per tile; only affects `col_no` | `params_parallel.h:23` |
| `S_MAX` | 12 | global Ozaki-2 modulus count | `common/include/global_params.h:23` |
| `S_max` | template override, default `S_MAX`=12 | **local** count used by package types | `params_parallel.h:24,33` |
| `W_max` | 16 | storage width per element | `params.h:21` |
| `E_max` | 8 | max exponent field width | `params.h:23` |
| `E_min` | 5 | used only to derive `M_max` | `params.h:24` |
| `M_max` | `W_max-E_min-1` = 10 | significance alignment position | `params.h:25` |
| `M_bw` | `ceil(log2(M_max))` = 4 | unused in main datapath | `params.h:26` |
| `shift_bw` | 9 | `shift_t` width, also `sa_latched` width | `params.h:31` |
| `mod_bw` | 8 (`MOD_BW`) | residue width | `params.h:32`, `global_params.h:26` |
| `comp_bw` | 6 (`COMP_BW` for S_MAX=12) | complementary-modulus width | `params.h:44`, `global_params.h:32` |
| `q_base_bw` | `M_max+9` = 19, signed | 1 sign + 1 hidden + 10 mantissa + 7 shift align | `params.h:37,62` |
| `q_shift_max` | 120 | max byte-shift bound | `params.h:38` |
| `q_shift_bw` | 8 | `q_shift_t` width | `params.h:39,63` |
| `log2_K` | `ceil(log2 K)` | mask/max index width | `params.h:34` |
| `counter_bw` | `ceil(log2 N)` | `col_no` width | `params_parallel.h:46-47` |

**`S_max` override is unsafe in this source** (Risk R3). Keep `S_max = 12`.

### 1.3 Types

| Type | Definition | Width | Source |
|---|---|---|---|
| `packed_data_t` | `ac_int<16*K,false>` | `16K` bits (fp8 uses only `8K`) | `params.h:55` |
| `element_t` | `ac_int<16,false>` | 16 | `params.h:56` |
| `mod_t` | `ac_int<8,true>` | 8 signed | `global_params.h:49` |
| `mod_unsigned_t` | `ac_int<8,false>` | 8 unsigned | `global_params.h:52` |
| `shift_t` | `ac_int<9,true>` | 9 signed | `global_params.h:59` |
| `q_base_t` | `ac_int<19,true>` | 19 signed | `params.h:62` |
| `q_shift_t` | `ac_int<8,false>` | 8 unsigned | `params.h:63` |
| `q_base_row_t` | `ac_array<q_base_t,K>` | `19K` | `params.h:64` |
| `q_shift_row_t` | `ac_array<q_shift_t,K>` | `8K` | `params.h:65` |
| `mod_row_t` | `ac_array<mod_t,K>` | `8K` signed | `params.h:68` |
| `all_mod_row_t` | `ac_array<mod_row_t,S_max>` | `8*K*S_max` | `params.h:69` |
| `S_t` | `ac_int<3,false>` | **3** | `params.h:59` |
| `E_t` | `ac_int<4,false>` | 4 | `params.h:58` |
| `dType_mode_t` | `ac_int<4,false>` | 4 | `params.h:61` |
| `counter_t` | `ac_int<ceil(log2 N),false>` | `ceil(log2 N)` | `params_parallel.h:46-47` |
| `arr_max` `bitmask_t` | `ac_int<K,false>` | K | `scaler_...v2.h:50` |
| `lz_temp` | `ac_int<log2K+17,false>` | `ceil(log2K)+17` | `scaler_...v2.h:79` |
| `lz` | `ac_int<6,true>` | 6 signed | `scaler_...v2.h:96` |
| `shift_tmp` | `ac_int<7,true>` | 7 signed | `scaler_...v2.h:288`, `preprocess_...ccore.h:49` |
| `exp_diff` | `ac_int<8,false>` | 8 unsigned | `preprocess_...ccore.h:50` |
| `mantissas` | `ac_int<11,false>` | `M_max+1` | `preprocess_...ccore.h:53` |

### 1.4 `cfg_t`

```c
typedef struct Cfg {          // HLS/preprocess/include/params.h:83-88
    E_t           E;          // 4 bits, exponent width 4..8
    S_t           s;          // 3 bits, number of moduli
    dType_mode_t  dTypeA;     // 4 bits, activation dtype
    dType_mode_t  dTypeB;     // 4 bits, weight dtype
} cfg_t;
```

`dType_e` (`params.h:90-98`):

| value | name | meaning |
|---:|---|---|
| 0 | `FP16` | FP16, E=5, W=16 |
| 1 | `BF16` | BF16, E=8, W=16 |
| 2 | `AC_FP16` | FP8 marker; W=8 (`E=4` → E4M3, `E=5` → E5M2) |
| 3 | `INT8` | INT8, W=16 packing |
| 4 | `UINT8` | declared, not implemented in preprocess |
| 5 | `INT4` | declared, not implemented |
| 6 | `UINT4` | declared, not implemented |

C++ struct layout (padding, field order) is compiler/tool dependent. For RTL,
flatten to `cfg_E[3:0]`, `cfg_s[2:0]`, `cfg_dTypeA[3:0]`, `cfg_dTypeB[3:0]`.

### 1.5 Packages

```c
struct in_pkg_t {                       // params_parallel.h:49-53
    ac_array<packed_data_t, S_max> data; // 12 planes × 16K bits
    cfg_t cfg;                           // 15 bits of fields
    bool is_weight;                      // 1
};

struct out_pkg_t {                      // params_parallel.h:55-62
    all_mod_row_t data;                  // 12 × K × 8-bit signed residues
    ac_array<shift_t, S_max> shift;      // 12 × 9-bit signed
    S_t s;                               // 3-bit copy of cfg.s
    bool intint;                         // 1
    bool is_weight;                      // 1
    counter_t col_no;                    // ceil(log2 N) bits
};
```

Flattened bit counts for `N=4`, `S_max=12`:

| K | `in_pkg.data` | `out_pkg.data` | `out_pkg.shift` | total in (excl. cfg) | total out |
|---:|---:|---:|---:|---:|---:|
| 8 | 1536 | 768 | 108 | 1552 | 883 |
| 16 | 3072 | 1536 | 108 | 3088 | 1651 |
| 32 | 6144 | 3072 | 108 | 6160 | 3187 |
| 64 | 12288 | 6144 | 108 | 12304 | 6355 |
| 128 | 24576 | 12288 | 108 | 24592 | 12403 |

(`cfg` 15 bits + `is_weight` 1 bit added to input totals; output totals add
`s`=3, `intint`=1, `is_weight`=1, `col_no`=2.)

### 1.6 Plane vs. channel semantics (important)

The 12 input planes are **not** 12 residues of one vector. For a data type /
`s` combination the K-dimension tile is cut into `12/s` independent chunks of K
elements, each chunk is RNS-decomposed into `s` residues, and the 12 output
channels are laid out as

```
channel c = chunk g = c / s , residue index r = c % s
```

This is visible in the HLS mapping arrays:
`base_select[c] = floor(c/s)` and `shift[c] = shift_core[c/s]`
(`preprocess_...ccore.h:182-209`) and
`moduli_select[c-1] = c mod s` (`:211-221`) for all supported `s`.

| s | chunks = 12/s | residues/chunk | plane inputs used | cores semantically used | modops semantically used |
|---:|---:|---:|---:|---:|---:|
| 1 | 12 (INT8×INT8 bypass only) | 1 (raw int8) | 12 | 0 (computed, unused) | 0 |
| 2 | 6 | {256,255} | 6 | 6 | 6 |
| 3 | 4 | {256,255,253} | 4 | 4 | 8 |
| 4 | 3 | {256,255,253,251} | 3 | 3 | 9 |
| 6 | 2 | {256,255,253,251,247,241} | 2 | 2 | 10 |
| 12 | 1 | 12 moduli | 1 | 1 | 11 | **not reachable, see R2** |

HLS always instantiates 6 cores and 11 modops; the "used" columns are what can
be dropped in RTL without changing any valid output channel.

---

## 2. Top-level preprocess interface

### 2.1 HLS signature and derived RTL ports

HLS (`preprocess_...ccore.h:126-127`):

```c
void CCS_BLOCK(run)(ac_channel<in_pkg_t>& in_ch, ac_channel<out_pkg_t>& out_ch);
```

There are **no** `reset`, `is_int`, `is_fp8`, `reset_sa`, or `apply_adjust`
ports. Those are derived internally. `ac_channel` supplies blocking/non-blocking
handshake; RTL must add valid/ready explicitly.

Recommended RTL port list:

| Signal | Dir | Width | Meaning |
|---|---|---:|---|
| `clk` | in | 1 | 3.3 ns target (`modules.json:3`) |
| `rst` | in | 1 | sync active-high recommended; see 4.3 |
| `in_valid` | in | 1 | packet present |
| `in_data` | in | `12*16*K` | `in_pkg.data`, plane-major |
| `in_cfg_E` | in | 4 | |
| `in_cfg_s` | in | 3 | |
| `in_cfg_dTypeA` | in | 4 | |
| `in_cfg_dTypeB` | in | 4 | |
| `in_is_weight` | in | 1 | |
| `in_ready` | out | 1 | `!out_valid || out_ready` |
| `out_valid` | out | 1 | one packet per accepted input |
| `out_data` | out | `12*K*8` | signed residues / q_base |
| `out_shift` | out | `12*9` | signed shift |
| `out_s` | out | 3 | `cfg.s` |
| `out_intint` | out | 1 | |
| `out_is_weight` | out | 1 | |
| `out_col_no` | out | `ceil(log2 N)` | |
| `out_ready` | in | 1 | |

For FP8 (`is_fp8_in=1`) only the low 8 bits of each 16-bit plane slot are
used; the element stride inside `packed_data_t` becomes 8 bits, not 16
(`scaler_...v2.h:208-251` uses `i*cfg_W` with `cfg_W=8`).

### 2.2 Derived control flags (per packet)

```c
is_int_in    = is_weight ? (cfg.dTypeB == 3) : (cfg.dTypeA == 3);
is_fp8_in    = is_weight ? (cfg.dTypeB == 2) : (cfg.dTypeA == 2);
is_int_eff   = is_int_in || (cfg.dTypeA == 3);         // HLS quirk, see R7
apply_adjust = (cfg.dTypeB == 3) && !is_weight && (cfg.dTypeA != 3);
update_sa    = (cfg.dTypeB == 3) && is_weight;
reset_sa     = is_weight && (col_counter == N-1);
intint       = (cfg.dTypeA == 3) && (cfg.dTypeB == 3);
```

Sources: `preprocess_...ccore.h:63-64, 155-159, 306`.

`is_int_eff` is used both in `scaler` (`scaler_...v2.h:222`) and in the core
(`preprocess_...ccore.h:64`). Note that it forces "int" when `dTypeA==3` even
for weight packets whose own dtype is float.

### 2.3 Packet types and channel semantics

Per tile of `N` weight columns and `M` activation rows:

1. **Weight packets** (`is_weight=1`), `N` packets, in reverse column order
   (`col_no = N-1, N-2, ..., 0`). Each packet carries, per used plane `g`, one
   K-element slice of weight column `col_no`. Preprocess computes one `shift`
   per core/chunk (common to all elements of that chunk for that column) and,
   for int weights, a per-column `sa` candidate.
2. **Activation packets** (`is_weight=0`), `M` packets forward, one K-element
   slice per used plane. Preprocess computes per-element `q_base/q_shift`, then
   residues for each channel. `col_no` stays at `N-1` after the weight tile
   (see 4.2).

For float paths, each channel carries
`residue_r(q_base_g * 2^{q_shift_g})` (Section 3.7). For INT8 weights, each
channel carries the same signed integer `q_base` (`preprocess_...ccore.h:241-256`);
this is a valid residue for every modulus, because `q_base` is the scaled
integer weight and postprocess reduces each channel modulo its own modulus
(3.7.2/R6). For INT8×INT8, each channel carries the low 8 bits of the
corresponding input plane (pass-through, `:223-240`).

### 2.4 Supported `cfg` combinations

`s` is stored in 3 bits (`S_t`) and `moduli_select` is also `S_t`
(`preprocess_...ccore.h:132`), so **only s ≤ 7 is representable and only
s ∈ {1,2,3,4,6} tiles 12 channels correctly**. s=5,7 do not divide 12; s≥8
truncate.

| Mode | `dTypeA` | `dTypeB` | s | Status |
|---|---:|---:|---:|---|
| INT8 × INT8 | 3 | 3 | 1 | **coherent**, pass-through bypass |
| BF16 act × INT8 weight | 1 | 3 | 2/3/4/6 | **coherent**, recommended full INT8 path (R6) |
| FP16 act × INT8 weight | 0 | 3 | 2/3/4/6 | **coherent**, same branch |
| BF16/FP16 × BF16/FP16 | 0/1 | 0/1 | 2/3/4/6 | **coherent**, full scalar+modop math |
| FP8 × INT8 / FP8 × FP8 | 2 | 3/2 | 2/3/4/6 | code exists, untested |
| INT8 act × FP weight | 3 | 0/1 | any | **unsupported/broken** (R7) |
| s = 8/12 | any | any | — | **unsupported in this source** (R2) |
| `S_max_override` ≠ 12 | any | any | — | **unsupported/broken** (R3) |

The INT8 weight path repeats one signed integer on every residue channel; this
is valid because postprocess reduces each channel modulo its own modulus
(3.7.2). The remaining work is the range/scaling proof in R6.

### 2.5 State

Two state elements exist, both per core:

- `sa_latched` (`shift_t`, 9-bit signed) per `preprocess_parallel_core`
  (`preprocess_...ccore.h:37`). Reset value written on `reset_sa` is
  `(1<<(9-1))-1 = 255` (`:68`). It is **not initialized in the constructor**.
- `col_counter` (int) in the wrapper, initialized to `N-1` (`:116-121`).

Update:

```c
if (reset_sa)  sa_latched = 255;
if (update_sa) sa_latched = (sa_latched < shift)
                            ? sa_latched
                            : (shift >= 0 ? shift : (shift_t)0);
```

Because `sa_latched` is always ≥0 after the first update, this is exactly

```
sa_latched = min over processed weight columns of max(shift_col, 0)
```

(not a single `min(shift)` when negatives exist). `apply_adjust` selects
`sa = sa_latched`, otherwise 0 (`:74`). Each core has its own `sa_latched`, so
each chunk gets its own weight-min shift.

`col_counter` sequencing:

```c
data_out.col_no = col_counter;                 // :309
out_ch.write(data_out);                        // :310
if (is_weight) {
    if (col_counter == 0) col_counter = N-1;   // :313-314
    else                  col_counter--;       // :317
}
```

Consequences:
- First weight of a tile has `col_no = N-1`; last has 0; then it wraps to N-1.
- Activation packets always carry the post-wrap value (`N-1` for a complete
  tile), because they do not modify the counter.
- A tile **must contain exactly N weight packets**; otherwise `reset_sa` will
  not fire at the next tile's first weight.
- `N=1` is illegal: `ceil(log2 1)=0` would create `ac_int<0,false>`
  (`params_parallel.h:46-47`). Use N≥2.

### 2.6 Reset

The HLS code has no explicit reset. For RTL:

- `col_counter <= N-1`
- `sa_latched <= 255` in every core (defensive; HLS relies on the first
  `reset_sa`)
- output valid = 0.

Catapult's reset configuration is
`-RESET_SYNC_NAME rst -RESET_ASYNC_NAME arst_n -RESET_KIND async
-RESET_SYNC_ACTIVE high -RESET_ASYNC_ACTIVE low` (`scripts/catapult.tcl:126`).
Pick one reset style for the block and document it.

---

## 3. Algorithm

### 3.1 Notation

```
W    = is_fp8_in ? 8 : 16
E    = cfg.E
M    = W - E - 1
bias = 2^(E-1) - 1
S    = cfg.s
ME   = M_EXPONENT[S-1]
MF   = M_FRAC[S-1]
L2K  = ceil(log2 K)
```

For each plane `g` and lane `j ∈ [0,K)` the element occupies bits
`[j*W +: W]` of `data[g]`.

### 3.2 Unpacking (scaler)

For each lane (`scaler_...v2.h:224-283`):

1. `sign[j] = data[g][j*W + W-1]` (`:226`).
2. Exponent/fraction fields by `cfg.E` (`:228-257`):

| E | W | M | exponent field | fraction field | dtype |
|---:|---:|---:|---|---|---|
| 4 | 8 | 3 | `[i*W+3 +: 4]` | `[i*W +: 3]` | FP8 E4M3 |
| 5 | 8 | 2 | `[i*W+2 +: 5]` | `[i*W +: 2]` | FP8 E5M2 |
| 5 | 16 | 10 | `[i*W+10 +: 5]` | `[i*W +: 10]` | FP16 |
| 6 | 16 | 9 | `[i*W+9 +: 6]` | `[i*W +: 9]` | E6M9 |
| 7 | 16 | 8 | `[i*W+8 +: 7]` | `[i*W +: 8]` | E7M8 |
| 8 | 16 | 7 | `[i*W+7 +: 8]` | `[i*W +: 7]` | BF16 |
| other | — | — | 0 | 0 | default |

3. `subnormal = (exponent == 0)` (`:258`).
4. `e_eff` and the significand:
   - **int path** (`is_int_eff`, `:260-269`):
     ```
     mag7 = data[g][j*W +: 7]                 // low 7 bits of the int8
     mag8 = mag7
     if (sign) { mag8[7] = 1; mag8 = (~mag8) + 8'd1; }   // 8-bit two's complement of the packed low bits
     f_out = mag8                              // 0..128, 8-bit magnitude
     sig_lz = f_out << (M_max - 7) = f_out << 3
     e_eff  = parsed exponent (must be 0)
     ```
   - **float path** (`:270-281`):
     ```
     f = fraction field (M bits), zero-extended to 11 bits
     if (!subnormal) f[M] = 1                  // implicit leading one
     f_out = f                                 // aligned at bit M, NOT at M_max
     if (subnormal) { e_eff = 1; sig_lz = (1<<M) << (M_max-M); }  // flushed to 1.0
     else           { e_eff = exponent; sig_lz = f << (M_max-M); }
     ```
   `f_out` is the value used later by `element_shift_fn`; `sig_lz` is the
   M_max-aligned value used only for the scale computation inside
   `arr_max_compress`. They are different arrays in HLS
   (`mantissas_out` vs. local `mantissas`).

   **INT8 packing requirement**: bits `[14:7]` of each 16-bit int slot must be
   zero. The int scaling path still runs `arr_max_compress` over the parsed
   exponent field; stray bits there change `exp_diff`, the `left_mantissa`
   truncation length, and therefore `shift_tmp`.

5. `sign` is the raw sign bit; the magnitude in `f_out` is always non-negative.

### 3.3 Common exponent and exponent differences (`arr_max_compress`)

Given `e_eff[i]` (8-bit) and `sig_lz[i]` (11-bit) for K lanes
(`scaler_...v2.h:56-95`):

```
// argmax mask
mask = K'b111...1
for bit = W-1 downto 0:
    slice[j] = e_eff[j][bit]
    t = mask & slice
    if (t != 0) mask = t

max_exp = OR over j of (e_eff[j] & {W{mask[j]}})   // = max(e_eff)
exp_diff[j] = max_exp - e_eff[j]                    // 8-bit, 0..255
```

`max_idx` (`:73-78`) selects the highest lane with the maximum exponent and is
then written back (`arr[max_idx] = max`, `:78`); it has no effect on any value
and can be dropped.

### 3.4 `lz`, `frac_M`, `borrow`, `shift_tmp`

`visible = 8`, `M_max = 10` (`scaler_...v2.h:79-120`).

```
L = 0                                                   // width L2K+17
for j in 0..K-1:
    d = exp_diff[j]
    if (d >= 8):
        lm = (sig_lz[j] == 0) ? 0 : 1
    else:
        tlen = max(0, (M_max+1) - 8 + d) = 3 + d        // 3..10
        trunc = sig_lz[j] & ((1<<tlen) - 1)
        lm = sig_lz[j] >> tlen
        if (trunc != 0) lm = lm + 1
    if (lm >= 256): L += 1<<16                          // lm[8] set
    else:           L += lm*lm

lz0 = (L2K + 17) - bit_length(L)      // == AC leading_sign() on unsigned = leading zeros
lz  = is_int_eff ? lz0 : lz0 - 14     // 2*visible - 2

frac_M = 0
if (lz0 >= 8):
    frac_M = ((L >> (lz0-8)) & 0xFF) + 1                // 8-bit, wraps on 255+1
    frac_M = frac_M & 0xFF

borrow = (frac_M > MF) ? 1 : 0
shift_tmp = floor( (ME - lz - (borrow+1)) / 2 )         // arithmetic >>1
```

Notes:

- `bit_length(0) = 0`, so `lz0 = width` for `L = 0` (all significands zero).
- `frac_M` uses the **unadjusted** `lz0`, before the `-14` float correction.
- The `+1` in `frac_M` is performed in 8 bits in HLS; `255+1` wraps to 0. This
  is a bit-exact quirk to preserve (Risk R9).
- `shift_tmp` is 7-bit signed; for all legal `s`/`K` it stays within
  `[-16, 54]`, so no overflow.

The scaler output is (`scaler_...v2.h:301-303`):

```
amax = (signed 8-bit)(max_exp - bias)
shift_raw = is_int_eff ? shift_tmp : shift_tmp - amax
```

`shift_raw` is the per-chunk scalar output `s` in the HLS `scaler`.

### 3.5 `sa` adjustment

In the core (`preprocess_...ccore.h:63-79`):

```
update_sa = (dTypeB == 3) && is_weight
apply_adjust = (dTypeB == 3) && !is_weight && (dTypeA != 3)

if (reset_sa)  sa_latched = 255
if (update_sa) sa_latched = min(sa_latched, max(shift_raw, 0))

sa       = apply_adjust ? sa_latched : 0
shift_out = shift_raw + sa              // 9-bit
adj_st    = shift_tmp + sa              // 10-bit
```

`sa` is per core/chunk. It is nonzero only in the fp×int mode (RTL-2), for
activation packets, where it adds the minimum non-negative INT8-weight shift
for that chunk. It is zero in all float×float and INT8×INT8 configurations.

### 3.6 Per-lane `q_base` / `q_shift` (`element_shift_fn`)

For each lane (`preprocess_...ccore.h:82-86`,
`scaler_...v2.h:145-157`):

```
if (is_int_eff):
    A = adj_st > 0 ? 0 : adj_st       // only right shifts for int
else:
    A = adj_st - M - exp_diff[j]      // 10-bit intermediate, then 9-bit
```

Then:

```
neg = sign
sig = f_out            // float: (M+1)-bit magnitude, implicit one at bit M
                       // int:   8-bit magnitude |x| (0..128), not M-aligned

if (A < 0):
    dropped = (sig & ((1 << (-A)) - 1)) != 0
    mag = (sig >> (-A)) + (dropped ? 1 : 0)     // round away from zero
    q_shift = 0
else:
    mag = sig << (A & 7)                        // low 3 bits of A
    q_shift = (A >> 3) << 3                     // multiple of 8

q_base = neg ? -mag : mag                       // 19-bit signed
```

Important details:

- The right shift adds 1 whenever **any** discarded bit is nonzero. This is
  round-half-away-from-zero on the magnitude, not round-to-nearest-even.
- The left shift is split into a 3-bit shift on `q_base` and an 8-bit-multiple
  shift in `q_shift`. This is why `q_shift` is always a multiple of 8 and why
  the float `q_base` needs only `11 + 7 + 1 = 19` bits.
- The sign is applied after the magnitude shift/round.
- For float, `sig` is aligned at bit `M` (format mantissa width), **not** at
  `M_max`; `A` already accounts for this via `-M`. For int, `A` does not use
  `M` and `sig` is the unaligned 8-bit magnitude.

For float lanes the exact identity (before the rounding above) is

```
q_base * 2^q_shift  ==  x * 2^shift_out
```

where `x` is the element value. This is the key invariant for verification.
For int lanes the invariant is different. The scaler passes `f_out = |x|` for
int lanes (the `<<3` value `sig_lz` is used only inside `arr_max_compress`, not
by `element_shift_fn` — `scaler_...v2.h:267-268`), so

```
q_base = sign * round(|x| / 2^{-A})          with A = min(adj_st, 0)
q_shift = 0
```

i.e. an INT8 value is either carried exactly (`A=0`, `q_base=w`) or
right-shifted/rounded by the negative scaler shift. The wrapper then clamps
INT8-weight `shift_out` to `≤0` (`preprocess_...ccore.h:258-265`), which is
exactly what makes the scaling consistent: a positive weight shift is not
applied (the weight is exact and `shift=0`), while a negative weight shift is
applied to `q_base` and also appears in `shift_out`.

The INT8 invariant for verification is therefore

```
INT8 weight lane:  q_base * 2^{-min(shift_tmp,0)} == w   (up to right-shift rounding)
float activation: q_base * 2^q_shift == x * 2^shift_out  (up to rounding)
```

and the total SIMD product is de-scaled by `e_reg + shift_in`, so the
weight/activation scalings cancel. The clamp is essential for the weight
invariant: without it, a positive `shift_tmp` would be counted twice (once as
an unused scale on `q_base=w` and once in `shift_out`). An INT8 **activation**
gets no such clamp (`preprocess_...ccore.h:241-256` applies it only for
`is_weight`), so a positive `shift_tmp` leaves `q_base=w` but a positive
`shift_out`; that mode is not self-consistent (R7) and should not be supported.

### 3.7 Channel assembly and modulo reduction

Two cases in the wrapper (`preprocess_...ccore.h:223-296`).

#### 3.7.1 INT8 × INT8 (`dTypeA==3 && dTypeB==3`)

```
for c in 0..11: data_out.data[c][j] = (int8) data[g=c][j*W +: 8]   // low byte
data_out.shift[c] = shift_out[mapped core]                          // no clamp
data_out.intint = 1
```

No scaler result, no modulo. `intint=1` makes the downstream SIMD/path chooser
bypass CRT (`HLS/top/include/path_chooser.h:24-31`).

#### 3.7.2 Current packet is INT8, other side is float

```
for c in 0..11: data_out.data[c] = (int8) q_base[floor(c/s)]      // truncated low 8 bits
if (dTypeB==3 && is_weight):
    for c in 0..11: data_out.shift[c] = min(shift_out[floor(c/s)], 0)
else:
    data_out.shift[c] = shift_out[floor(c/s)]
```

No modulo reduction is performed on int packets: **every residue channel of a
chunk receives the same 8-bit truncation of the chunk's `q_base`**
(`preprocess_...ccore.h:241-256`). At first sight this looks wrong, but it is
valid for INT8 because `q_base` is itself the scaled integer weight:

- `q_base ∈ [-128, 127]`: the magnitude is `|w| ≤ 128`, and `+128` cannot occur
  (magnitude 128 only arises for `w = -128`, with the sign applied), so the
  `(int8)` cast is exact, not lossy.
- For residue channel `r`, the true residue is `q_base mod m_r`. The value
  stored in the channel is the signed integer `q_base`; the postprocess signed
  reducer (`iterated_new_s12_scalar<32,8,6,3,true,false>`) maps it to
  `q_base mod m_r` correctly (`postprocess_parallel.h:115`). No per-modulus
  reduction is therefore required in preprocess.
- For `r=0` (m=256), postprocess masks the low byte (`postprocess_parallel.h:117`),
  which is also `q_base mod 256`.
- `q_base` is `w` when `adj_st ≥ 0`; otherwise it is the rounded
  `w / 2^{-adj_st}` (Section 3.6). `shift_out` is clamped to `≤0` for INT8
  weights, so the applied scaling is exactly consistent with the postprocess
  de-scaling.

This is the "INT8 weight / INT8 activation while the other side is float"
path of fp×int. It is coherent; the remaining verification item is the
`q_base` range/rounding proof (R6).

#### 3.7.3 Current packet is float

Map every channel `c` to core `g = c/s`, residue index `r = c%s`:

- If `r == 0` (modulus 256, power of two):
  ```
  data_out.data[c] = (int8) ( q_base[g] & (0xFF >> q_shift[g]) )
  ```
  Since `q_shift` is a multiple of 8, this simplifies exactly to
  ```
  data_out.data[c] = (q_shift[g] == 0) ? (int8)q_base[g][7:0] : 8'h00
  ```
  (HLS also calls the modop with modulus 0 first and overwrites the result;
  bypass that call in RTL.)
- If `r >= 1` (modulus `OZ2_MODULI_8BIT[r-1]`):
  ```
  q = q_shift[g] >> 3                         // 0..15, 4-bit
  data_out.data[c] = base_shift_mod(q_base[g], q,
                                    m = OZ2_MODULI_8BIT[r-1],
                                    d = 256 - m)
  ```
  HLS passes the whole `POWER_OF_COMP_MOD_M[r-1]` row plus
  `POWER_OF_COMP_MOD_M[r-1][0]` (= d) to `base_shift_mod_vec`
  (`preprocess_...ccore.h:283-289`).

- `data_out.shift[c] = shift_out[g]` (`:182-193` implements `shift_out[c/s]`).

All 12 channels are meaningful for `s ∈ {2,3,4,6}`; no "don't care" channels
appear on the 12-channel output for supported `s`.

### 3.8 `base_shift_mod` contract

`base_shift_mod_vec` is declared in
`HLS/modulo/include/base_shift_mod_vec.h`, which is **not shipped** (R1).
The only facts extractable from the caller are:

```c
using modop_t = base_shift_mod_vec<q_base_bw=19, q_shift_max=120,
                                   mod_bw=8, comp_bw=6, mod_bw=8,
                                   true /*in_sign*/, true /*out_sign*/, K>;
modops[S_MAX-1];                              // preprocess_...ccore.h:111-112
modops[s_idx-1].run(q_base_row, q_shift_bytes,
                    POWER_OF_COMP_MOD_M[mi], // d^1..d^10 (8-bit)
                    moduli[mi],              // m (8-bit)
                    POWER_OF_COMP_MOD_M[mi][0], // d = 256-m
                    out_row);                // preprocess_...ccore.h:283-289
```

The **required** function is unambiguous; the internal reduction style is not:

```
base_shift_mod(qb, q, m) :
    r = qb * 2^(8*q)  mod m
    return r in the canonical balanced signed range:
        r in [0, m/2]        if r <= (m>>1)
        r - m                otherwise
```

That the output must be the *balanced* representative, not merely any
congruent 8-bit value, follows from the postprocess input:
`iterated_new_s12_scalar<32,8,6,3,true,false>` treats `data_in.data[i]` as a
**signed** value and reduces it modulo `m` (`postprocess_parallel.h:115`);
the signed reduction maps negative inputs to `m - r`
(`modulo/include/iterated_new_s12_scalar.h:81-93`). An unsigned residue cast to
`int8` would change its residue value (e.g. 200 cast to -56 is ≡199 mod 255,
not 200), so the balanced form is mandatory.

Reference algorithm (bit-exact by the uniqueness of the balanced residue; use
this for RTL and for the golden model):

```
d = 256 - m                                   // 1 <= d <= 83, m = 256-d
neg = qb < 0
u = neg ? -qb : qb                            // 18-bit magnitude
b0 = u[7:0]; b1 = u[15:8]; b2 = u[17:16]
D[i] = d^i mod m, i = 0..max_q+2              // D[0]=1

// Horner over the three bytes, then apply the byte shift:
r = b2
r = (r*d + b1) mod m
r = (r*d + b0) mod m
r = (r*D[q]) mod m

if (neg && r != 0) r = m - r
if (r > (m>>1)) r = r - m
return signed8(r)
```

Equivalently, using the HLS power table with
`P[i] = D[i+1] = d^(i+1) mod m`:

```
r = (b0*P[q] + b1*P[q+1] + b2*P[q+2]) mod m
```

Both forms produce the same `r` for every `q` for which the `D` indices exist.
The HLS table has only `P[0..9]`; the RTL can size `D` to the actual `q` range
(Section 5) and does not need to match the HLS table limit.

Special case `m = 255` (d=1): `r = (b0+b1+b2) mod 255`, independent of `q`,
because `2^8 ≡ 1 (mod 255)`. This is the only modulus in the `s=2` path and is
extremely cheap in RTL.

Verification of the power table formula: `P[j][i] = (256 -
OZ2_MODULI_8BIT[j])^(i+1) mod OZ2_MODULI_8BIT[j]`
(`HLS/common/include/ozaki_tables.h:137-159`); e.g. j=10, m=217, d=39:
39, 39² mod 217 = 2, 39³ mod 217 = 78, ... which is the shipped row.

### 3.9 Output shift semantics

- Float path: `q_base*2^q_shift ≈ x * 2^shift_out`. `shift_out` is the exponent
  the downstream `int2fp` uses to remove the scale
  (`postprocess_parallel.h:192`, `int_fp_change_parallel.h:50-90`).
- INT8 path: `q_base = round(|x| / 2^{-A})` with `A=min(adj_st,0)`, so either
  `q_base=x` (positive/zero shift, exact) or a right-shifted/rounded value.
  `q_shift=0`. For INT8 weights the wrapper forces `shift_out ≤ 0`; this is
  exactly the scale that was applied to `q_base`, so the postprocess de-scaling
  `e_reg + shift_in` reconstructs `w*x` (Section 3.6). The 12 output channels
  all carry the same signed integer `q_base`, which is a valid residue
  representative for every modulus (3.7.2).

### 3.10 Worked example (BF16, K=4, s=3, M=7, bias=127)

Inputs `[1.0, 0.5, -2.0, 0.25]`. From the model in Appendix B:

```
M_EXP[2] = 23, M_FRAC[2] = 248
e_eff       = [128, 127, 128, 125]
exp_diff    = [0, 1, 0, 3]
max_exp     = 128
lz_temp     = 21505, lz0 = 4, lz = -10, frac_M = 0, borrow = 0
shift_tmp   = 16, shift_raw = 15
sa          = 0 (no INT8 weight adjustment in this example)
```

Per lane (`A = 16 - 7 - exp_diff`):

| x | sig | A | q_base | q_shift | q_base·2^q | r(m=255) | r(m=253) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 128 | 8 | 128 | 8 | 32768 | -127 | -122 |
| 0.5 | 128 | 7 | 16384 | 0 | 16384 | 64 | -61 |
| -2.0 | 128 | 9 | -256 | 8 | -65536 | -1 | -9 |
| 0.25 | 128 | 6 | 8192 | 0 | 8192 | 32 | 96 |

Channel 0 (mod 256) of each chunk is 0 here because all `q_base` low bytes are
zero or `q_shift=8`. `r` values are the balanced signed residues required in
`data_out.data`.

### 3.11 Constant tables

#### 3.11.1 Ozaki-2 moduli, complementary values, and scale constants

`m_i = OZ2_MODULI_8BIT[i]`, `d_i = 256 - m_i = COMP_SEQ[i+1]`
(`ozaki_tables.h:48-51,65-68`). `ME/MF` are the integer/fractional
decomposition of the modulus product `M_s = Π_{i=0}^{s-1} m_i` (with
`m_0=256`): `ME = floor(log2 M_s)`, `MF = floor((M_s/2^ME - 1)*256)`
(confirmed against `config.py:226-246` and all 12 rows).

| s | `m_{s-1}` (last) | `ME` | `MF` | `d` | `COMP_SEQ[s]` |
|---:|---:|---:|---:|---:|---:|
| 1 | 256 | 8 | 0 | — | — |
| 2 | 255 | 15 | 254 | 1 | 1 |
| 3 | 253 | 23 | 248 | 3 | 3 |
| 4 | 251 | 31 | 238 | 5 | 5 |
| 5 | 247 | 39 | 220 | 9 | 9 |
| 6 | 241 | 47 | 192 | 15 | 15 |
| 7 | 239 | 55 | 163 | 17 | 17 |
| 8 | 233 | 63 | 125 | 23 | 23 |
| 9 | 229 | 71 | 85 | 27 | 27 |
| 10 | 227 | 79 | 46 | 29 | 29 |
| 11 | 223 | 87 | 7 | 33 | 33 |
| 12 | 217 | 94 | 190 | 39 | 39 |

`M_EXPONENT[]` and `M_FRAC[]` are hard-coded at
`scaler_compressing_see_mantissa_v2.h:22-27`; only indices `0..S-1` are used.

#### 3.11.2 Full 12-modulus sequence (needed for s≥7 only)

```
OZ2_MODULI_8BIT = 255,253,251,247,241,239,233,229,227,223,217,211,199,197,193,191,181,179,173
COMP_SEQ[1..]   =   1,  3,  5,  9, 15, 17, 23, 27, 29, 33, 39, 45, 57, 59, 63, 65, 75, 77, 83
```

For supported `s ≤ 6`, only the first five entries are ever selected.

#### 3.11.3 `POWER_OF_COMP_MOD_M[j][i] = d_j^(i+1) mod m_j`

Rows `j=0..10` (`ozaki_tables.h:147-159`). Row `j` is used for modulus
`OZ2_MODULI_8BIT[j]`; only rows 0..5 are reachable for supported `s`.

```
j=0  m=255 d=1 : {  1,  1,  1,  1,  1,  1,  1,  1,  1,  1}
j=1  m=253 d=3 : {  3,  9, 27, 81,243,223,163,236,202,100}
j=2  m=251 d=5 : {  5, 25,125,123,113, 63, 64, 69, 94,219}
j=3  m=247 d=9 : {  9, 81,235,139, 16,144, 61, 55,  1,  9}
j=4  m=241 d=15: { 15,225,  1, 15,225,  1, 15,225,  1, 15}
j=5  m=239 d=17: { 17, 50,133,110,197,  3, 51,150,160, 91}
j=6  m=233 d=23: { 23, 63, 51,  8,184, 38,175, 64, 74, 71}
j=7  m=229 d=27: { 27, 42,218,161,225,121, 61, 44, 43, 16}
j=8  m=227 d=29: { 29,160,100,176,110, 12,121,104, 65, 69}
j=9  m=223 d=33: { 33,197, 34,  7,  8, 41, 15, 49, 56, 64}
j=10 m=217 d=39: { 39,  2, 78,  4,156,  8, 95, 16,190, 32}
```

#### 3.11.4 Reachable `q` range for supported `s`

`q = floor((adj_st - M)/8)` for float lanes, where
`adj_st = shift_tmp + sa`; `sa` is the per-chunk minimum INT8-weight shift.
Using the worst cases (`lz0=0` for float, `lz0=2` for int, `M=7`):

| s | `ME` | max float `shift_tmp` | max INT8-weight `shift_tmp` | max `adj_st` | max `q` | max table index `q+2` |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 15 | 14 | 6 | 20 | 1 | 3 |
| 3 | 23 | 18 | 10 | 28 | 2 | 4 |
| 4 | 31 | 22 | 14 | 36 | 3 | 5 |
| 6 | 47 | 30 | 22 | 52 | 5 | 7 |
| 12 (unsupported) | 94 | 53 | 45 | 98 | 11 | 13 |

So for supported `s ≤ 6` the shipped 10-entry power table is sufficient
(max index 7). A hypothetical fixed `s=12` would need at least 13 entries
(R2/R5).

---

## 4. Pipeline, latency, handshake, and testbench

### 4.1 HLS scheduling facts

- `#pragma hls_pipeline_init_interval 1` on both the wrapper and the core
  (`preprocess_...ccore.h:44,125`), so the intended throughput is one packet
  per cycle.
- Input is read with non-blocking `nb_read` (`:135`); when no input is
  available, no output is produced.
- Output is written with blocking `write` (`:310`); if the channel is full the
  process stalls.
- The datapath is combinational SSA in C++; Catapult may add pipeline registers
  to meet 3.3 ns (`modules.json:3`). Expect at least one output register for
  K≥16 at 3.3 ns. Functional latency is not specified by the C++.
- Only state is `col_counter` (wrapper) and `sa_latched` (per core); there is no
  multi-cycle arithmetic engine.

### 4.2 Recommended RTL cycle protocol

- Single-stage pipeline: 1 accepted packet → 1 output packet, latency 1.
- `in_ready = !out_valid || out_ready`.
- Compute `next_sa`, `next_col` from the current packet, but **commit state only
  on `in_valid && in_ready`** (exactly once). Do not let a backpressured output
  cause `col_counter` to decrement twice for the same weight packet.
- Hold `out_*` and `out_valid` stable while `out_valid && !out_ready`.
- No internal buffering is required for correctness; if the reducer is
  multi-cycle, add a skid buffer and ensure `sa`/`col` commit once.

### 4.3 Reset and initialization

See 2.6. HLS relies on `reset_sa` on the first weight of every tile; RTL should
also reset `sa_latched` to 255 so activation-before-weight is not X.

### 4.4 Preprocess testbench: intended vs. actual

The shipped testbench header documents a file-based protocol
(`HLS/preprocess/tb/tb_preprocess_parallel_compressed_ccore.cpp:5-10`):

- weight file: `N` entries (columns); activation file: `M` entries (rows);
- every `S_MAX / s_in` consecutive non-comment lines form one entry;
- within an entry, line 0 = channel/plane 0, line 1 = plane 1, ...;
- each line has K space-separated values;
- weight entries are fed in reverse column order internally; activations
  forward;
- output expected in `preprocess_parallel_output.txt`.

Config in the TB: `TEST_K=32`, `TEST_N=32`, `TEST_W_E=8`, `TEST_I_E=8`,
`TEST_W_DT=1`, `TEST_I_DT=1`, `TEST_S=3` (`:29-35`), i.e. BF16 × BF16, s=3.

**The actual `CCS_MAIN` body is empty** (`:117-131`): it constructs channels,
prints a banner, prints "TEST COMPLETED", and returns 0. It never reads a file,
never drives the DUT, never checks output. There is **no executable preprocess
golden test** in the artifact (R12).

### 4.5 Top-level testbench as a de-facto packet protocol

`HLS/top/tb/tb_top_parallel.cpp` is the only TB that actually drives packets.
It confirms the intended packet sequence:

- `top_in.data` is filled for `s < S/s_in` planes only, packed 16-bit per
  element (`:157-176` for weights, `:186-205` for activations).
- Weight packets: `cfg.dTypeA=I_DT_IN`, `dTypeB=W_DT_IN`, `E=WE`, `s=s_in`,
  `is_weight=true` (`:176-182`). Weight columns are fed in reverse index order
  (`N2-1-n2`, `:165-167`).
- Activation packets: same but `E=IE`, `is_weight=false` (`:205-211`).
- One output packet is expected per activation packet (`:215-239`).
- The reference output is a plain FP dot product (`:144-151`) and the check is
  print-only; `test_pass` is never set false (`:246-249`). This TB is not a
  scoreboard.

It also sets `pre_params::S_t s_in = 12` (`:55`), which truncates to 4 in the
3-bit `S_t`; the loops then use `S/s_in=1`. Treat that TB as an interface
example, not a correctness reference (R2/R12).

### 4.6 Recommended RTL testbench

Drive the packet sequence of 4.5 and compare **all** output fields exactly:

1. Reset; check `out_valid=0`, `col_no` after first accepted weight.
2. Feed `N` weight packets with `col_no` expected `N-1..0`.
3. Feed `M` activation packets; expect `out_valid` one cycle after each
   `in_valid`, `col_no=N-1`, `s=cfg.s`, `intint` as expected.
4. Compare `data` and `shift` against the Appendix B model, not against the
   FP dot product (preprocess output is scaled residues, not the final result).
5. Repeat for `s=2/3/4/6`, `K=8`, `N=4`, and both BF16×INT8 and INT8×INT8.

---

## 5. Minimal reduced configuration for the first RTL port

### 5.1 Recommendation

Two INT8 targets exist:

- **INT8×INT8 (`dTypeA=dTypeB=3`, s=1)** is a coherent pass-through. It is
  RTL-0; it needs no scaler or modop.
- **INT8 weight × BF16 activation** is the INT8 path that exercises the full
  preprocess. The HLS branch emits the same signed integer `q_base` on every
  residue channel; that is a valid residue representation for INT8 (3.7.2),
  not a per-modulus reduction bug. It is RTL-1 and is the recommended first
  full port.

**RTL-0 — INT8 × INT8 (literal INT8 path, smoke test)**

| Item | Value |
|---|---|
| `K` | 8 (grow to 16/32/64/128) |
| `N` | 4 (`col_no` 2 bits) |
| `S_MAX`/`S_max` | 12 / 12 |
| `s` | 1 |
| dtype | `dTypeA=dTypeB=3` |
| datapath | 12 × K × 8-bit pass-through: `data_out[c][j] = signed8(data[c][j][7:0])` |
| shift | `shift_out[0]` replicated (HLS s=1 mapping); unused downstream because `intint=1` |
| state | `col_counter` only |

This is small, but it does not exercise the scaler, exponent normalization,
rounding, or modular reduction. It validates the interface, packet order,
`col_no`, `intint`, and channel pass-through.

**RTL-1 — BF16 activation × INT8 weight, s=3 (recommended first full port)**

| Item | Value |
|---|---|
| `K` | 8 (grow to 16/32/64/128; all datapaths are K-parallel) |
| `N` | 4 (`col_no` 2 bits) |
| `S_MAX`/`S_max` | 12 / 12 (do **not** use `S_max_override`) |
| `s` | 3 (constant at elaboration; accept only `cfg.s==3`) |
| activation dtype | BF16: `dTypeA=1`, `E=8`, `W=16`, `M=7`, `bias=127` |
| weight dtype | INT8: `dTypeB=3` |
| channels | 4 chunks × 3 residues = 12 |
| scaler cores | 4 (not 6) |
| modops | 8: per chunk `m=255` (d=1) and `m=253` (d=3) |
| power ROM | `D[0..7]` for m=253; `D[i]=1` for m=255 |
| `q` range | 0..7 (actual max 2; leave margin) |
| `q_base` | 19-bit signed |
| state | 4 × `sa` (9-bit) + one `col_counter` (2-bit) |
| FP8 | not implemented (`is_fp8=0`) |

The only additional arithmetic versus a float×float port is:

- the per-core `sa_latched` accumulator and the `min(max(shift,0))` update on
  weight packets (`preprocess_...ccore.h:67-74`);
- the int unpack (`mag7 → 8-bit magnitude`) and `A=min(adj_st,0)`;
- the INT8-weight output path: all residues get `signed8(q_base)` (3.7.2) and
  `shift` is clamped to `≤0`;
- on activation packets, `shift_out += sa`, `adj_st = shift_tmp + sa`.

**RTL-2 — BF16 × BF16, s=3 (fallback if RTL-1 semantics need to be deferred)**

Identical to RTL-1 with `dTypeA=dTypeB=1` and without `sa`
(`apply_adjust=0`, so `sa=0` and the state is only `col_counter`, `q ≤ 1`).
This is the cleanest way to validate the scaler/modop math without the INT8
weight branch.

Why s=3:

- All 12 channels are meaningful, no unused-output ambiguity.
- Both residue moduli are tiny and cheap: `m=255` is a byte-sum mod 255;
  `m=253` is a 3-byte Horner with `d=3`.
- `q ≤ 2` in the worst fp×int case (`q ≤ 1` for float×float), so a 0..7 power
  ROM leaves ample margin.
- It fits `S_t` (3 bits) and keeps every `moduli_select` value ≤2.
- It exercises every interesting mechanism: max/exponent diff, lz, subnormal
  flush, rounding, `sa` min over 4 weight columns, power-of-two channel, and
  INT8-weight pass-through.

If area is more important than coverage, `s=2` is smaller (6 scalers, 6 modops)
but only exercises `m=255`; `s=6` uses 2 scalers but 10 modops and exercises all
five odd moduli.

If area is more important than coverage, `s=2` is smaller (6 scalers, 6 modops)
but only exercises `m=255`; `s=6` uses 2 scalers but 10 modops and exercises all
five odd moduli.

### 5.2 What can be simplified without changing valid-channel semantics

1. **Drop unused cores/modops.** Instantiate `12/s` cores and `(12/s)*(s-1)`
   modops; HLS's extra cores/modops produce only channels that are not selected
   by `base_select/moduli_select` for supported `s`.
2. **Replace comparator chains with wiring.** For supported `s`,
   `base_select[c]=floor(c/s)` and `moduli_select[c-1]=c%s`; with `s` constant
   these are free bit-slices (`preprocess_...ccore.h:198-221`).
3. **Power-of-two channels**: no modop; output is
   `q_shift==0 ? q_base[7:0] : 0` (`:270,294`).
4. **Drop dead `s` branches**: s=5/7/8/12 mapping and the `cfg.s==12`
   comparators are unreachable for legal `cfg` (`:216-221`); remove or keep as
   elaboration-time assertions.
5. **Drop FP8**: `is_fp8=0`, `W=16`; the `E=4` and `E=5-and-fp8` switch cases
   and the `cfg_W=8` path can be removed.
6. **Drop unused dtype parsing**: RTL-1 needs BF16 float parsing (activations)
   and INT8 parsing (weights); `E=4/5/6/7` can be tied off. RTL-0 needs only
   the INT8 pass-through.
7. **Drop `shifter.h` entirely**; it is not instantiated.
8. **Drop `subn_flags`, `max_idx`, `arr[max_idx]=max`**; they do not affect
   outputs.
9. **Specialize the modop to a single modulus.** `m=255`: sum three bytes,
   conditionally subtract 255. `m=253`: three Horner steps with `d=3`, each
   step `r = 3*r + byte` reduced modulo 253 (values <1024, so 3 conditional
   subtractions suffice).
10. **Replace the general `q_shift` multiplier with a byte shift.** `q_shift` is
    a multiple of 8; `q` is 0..7 in the reduced config. `A & 7` is 3 bits.
11. **`sa` accumulation**: `N=4` means a 4-input min of `max(shift,0)`, or the
    HLS incremental form; both are equivalent. The accumulator is per chunk
    and is only used on activation packets.
12. **If only BF16 activations are supported**, the `E` switch becomes
    `E==8`; `M=7` is a constant and `bias=127`.
13. **`q_base` width** can be reduced only if the maximum `A` is proven; keep
    19 bits for the first port to preserve exactness for all input exponents.
14. **Output `shift`** can be 9 bits; do not truncate to 8 (bf16 tiny values
    produce shifts beyond 8-bit signed range).

### 5.3 What must not be simplified

- Rounding: right shifts round **away from zero** if any discarded bit is 1
  (`scaler_...v2.h:145-153`); not truncation, not nearest-even.
- The split `A < 0` vs `A >= 0` behavior, including `q_shift=0` for right
  shifts and `q_base` low-3-bit shift for left shifts.
- Sign application after the magnitude shift/round.
- Subnormal flush to `e_eff=1` and `1.0` significand for the scale computation,
  while `f_out` keeps the true subnormal fraction.
- `frac_M` from the unadjusted `lz0`, and the 8-bit `+1` wrap.
- `borrow` comparison against the hard-coded `M_FRAC[s-1]`.
- `sa = min over columns of max(shift,0)`, per chunk; do not use plain min.
- INT8 weight shift clamp to `≤0`, and INT8 `q_base = sign*round(|x|/2^{-A})`
  with `A=min(adj_st,0)` (no `M_max-7` alignment in `element_shift`; that
  `<<3` is only for `arr_max_compress`).
- Repeating the same signed `q_base` on all residue channels of an INT8 chunk
  (3.7.2); do not "fix" it to per-modulus reduction if bit-exact HLS behavior
  is required — both are congruent, but the HLS output differs.
- Balanced signed residue mapping `r > (m>>1) ? r-m : r` for float channels.
- `col_no` reverse order and the exact-N weight-tile protocol.

### 5.4 Verification plan for RTL-1 (and RTL-0)

1. Build the Appendix B golden model (Python or C++), validated against the
   HLS formulas line by line.
2. Directed vectors:
   - BF16 activations: `0`, `±min normal`, `±max finite`, subnormals, values
     near 2.0 (to force `frac_M` wrap and `lm=256`), wide-dynamic-range
     vectors (`exp_diff` up to ~250), ties in exponent.
   - INT8 weights: `0`, `±1`, `±127`, `-128` (magnitude 128), random; all four
     columns so `sa` min is exercised.
   - RTL-0 INT8 activations/weights: same set, all 12 planes.
3. Check invariants:
   - `q_shift % 8 == 0` for float lanes;
   - float: `q_base*2^q_shift == x*2^shift_out` (up to rounding);
   - INT8 weight: `q_base == w` when `adj_st≥0`, else
     `q_base == round(w/2^{-adj_st})`; `shift_out=min(shift_tmp,0)`;
   - activation: `q_base*2^q_shift == x*2^shift_out` (up to rounding);
   - residues `r` in `[-(m-1)/2, (m-1)/2]` and `r ≡ q_base*2^q_shift (mod m)`
     for float channels;
   - channel mapping `c → (c/3, c%3)`;
   - `col_no` sequence and `intint/is_weight/s` fields.
4. For RTL-0, check `data_out[c][j] == signed8(data[c][j][7:0])` for all 12
   planes and `intint=1`.
5. Cross-check at least one vector against a C++ rebuild of the HLS function
   **including** `base_shift_mod` semantics, once R1 is resolved.

---

## 6. Open questions and risks for bit-exact RTL

**R1 (blocker) — `base_shift_mod_vec.h` is absent.**
`HLS/preprocess/include/preprocess_parallel_compressed_ccore.h:10` includes
`../../modulo/include/base_shift_mod_vec.h`, but `HLS/modulo/include/` contains
only `iterated_new_s12_scalar.h` and `new_single_s12.h`; the published Zenodo
zip (`ozcore-artifact.zip`, record 21541964) also lacks it. The template
signature, stage count, pipelining, and any internal table truncation are
unknown. The contract in 3.8 is inferred from the caller, the power table, the
postprocess signed reduction, and the GPU reference kernel
(`src/emulation/llm/fast_mod/fast_mod_cuda_kernel.cu:148-205`). Obtain the file
from the authors/upstream, or co-simulate against an HLS build, before claiming
bit-exactness for large `q`.

**R2 (blocker for s>7) — `cfg.s` and `moduli_select` are 3 bits.**
`S_t = ac_int<3,false>` (`params.h:59`) and `S_t moduli_select[S_MAX-1]`
(`preprocess_...ccore.h:132`). Therefore:
`s=12` is unrepresentable (`12 & 7 = 4`), all `cfg.s==12` branches are dead,
and `moduli_select` values 8..11 truncate to 0..3, which would mis-select the
power-of-two path and duplicate moduli. The effective supported set is
`{1,2,3,4,6}`. The top TB's `s_in=12` (`top/tb/tb_top_parallel.cpp:55`) silently
becomes 4. Either restrict RTL to `{1,2,3,4,6}` or widen `S_t`/`moduli_select`
to 4 bits and extend the power table (a deliberate functional change).

**R3 (blocker for variants) — `S_max_override` is inconsistent.**
`preprocess_parallel_params` can set `S_max=6/8`
(`params_parallel.h:24,33-44`), but the wrapper still uses
`ozaki_npu::S_MAX/2 = 6` for `preprocess_parallel_core_inst`
(`preprocess_...ccore.h:114`) and `ozaki_npu::S_MAX` for loop bounds
(`:140,149,152,262,274`). With `S_max=6`, `data[6..11]` and `shift[6..11]` are
out of bounds; with `S_max=8`, loops still run 6 cores and the `s=8` mapping is
not implemented (12/8 is not an integer). Do not use these variants.

**R4 (high) — unsupported `s` values produce silently wrong mappings.**
The comparator chains cover only `{2,3,4,6,12}`. `s=5`, `s=7` do not divide 12;
`s=8` does not divide 12 and has no mapping. There is no assertion. RTL should
assert `s ∈ {1,2,3,4,6}` and `12 % s == 0`.

**R5 (high) — power-table depth vs. `q` for a fixed s=12.**
The shipped table has 10 entries (`ozaki_tables.h:147-159`), enough for `s≤6`
(max index 7, Section 3.11.4). A widened-s=12 design needs `D[q+2]` up to 13
(Section 3.11.4). If the missing `base_shift_mod_vec` indexes the table with
`q+i` without clipping, `q>8` reads out of bounds. Confirm the HLS behavior
before supporting s=12.

**R6 (medium) — INT8 scaling/range needs a numerical proof, but the branch is
coherent.** In the `dTypeA!=3, dTypeB==3` path the HLS writes
`(int8)q_base[floor(c/s)]` to all 12 channels (`preprocess_...ccore.h:241-256`)
and clamps INT8-weight `shift` to `min(shift,0)` (`:258-265`). This is valid,
but three properties must be proven/verified:
1. **No `<<3` in `element_shift`.** `f_out` for int is `mag` (0..128); the
   `<< (M_max-7)` value (`scaler_...v2.h:268`) is only the local `mant_lz`
   used by `arr_max_compress`. The core receives `mantissas_out = mag`
   (`:267`), so `q_base = w` when `adj_st≥0` and
   `q_base = round(w/2^{-adj_st})` otherwise.
2. **Range/truncation.** `mag ≤ 128`; `+128` cannot reach the output (only
   `w=-128` has magnitude 128 and its sign is negative), so
   `q_base ∈ [-128,127]` and the `(int8)` cast is exact.
3. **Repeated residues are valid.** All channels carry the same signed integer
   `q_base`; postprocess reduces signed values modulo `m_r`
   (`postprocess_parallel.h:115`) and masks the low byte for `m=256`
   (`:117`), so channel `r` is `q_base mod m_r`. No per-modulus reduction in
   preprocess is required. The `m=255`/`m=253` residues of `-128`, `-127`,
   `+127` are the interesting boundary cases.

The scaling consistency to check at top level is
`q_base * 2^{-min(shift_tmp,0)} ≈ w` for weights (with right-shift rounding)
and `q_base * 2^{q_shift} ≈ x * 2^{shift_out}` for activations; the SIMD
de-scaling is `e_reg + shift_in` (`simd_engine_parallel_ccore.h:36-37`,
`postprocess_parallel.h:192`), so the weight shift and the `sa` adjustment
cancel. Verify with four weight columns that mix positive and negative
`shift_tmp`; this is the main new failure mode of RTL-1 versus a float×float
port.

**R7 (high) — INT8 activation modes are not self-consistent.**
Two separate problems:
1. `is_int_eff = is_int_in || (cfg.dTypeA == 3)` (`preprocess_...ccore.h:64`,
   `scaler_...v2.h:222`) forces the int path for **weight** packets whenever
   the activation dtype is INT8, even if `dTypeB` is FP16/BF16. Float weights
   are then parsed as sign-magnitude INT8.
2. INT8 **activation** packets do not get the weight shift clamp
   (`preprocess_...ccore.h:241-256` clamps only `is_weight`), so a positive
   `shift_tmp` leaves `q_base=w` and a positive `shift_out`, which the
   postprocess divides out (3.6).

Do not support `dTypeA==3` with `dTypeB!=3`; assert against it. INT8
activations are only meaningful in the INT8×INT8 bypass (RTL-0).

**R8 (medium) — INT8 packing convention differs between paths.**
The scaler int path expects bit15=sign and bits[6:0] = low 7 bits of the int8
two's-complement value (`scaler_...v2.h:260-268`). The INT8×INT8 bypass uses
the low 8 bits (`preprocess_...ccore.h:145`). The compatible packing is:
`bit15 = int8[7]`, `bits[7:0] = int8[7:0]` (full two's complement),
`bits[14:8] = 0`. The TB packer only sets bits[6:0] and bit15, so it works for
the scaler path but not for the bypass path
(`preprocess/tb/...cpp:54-58`). Define this in the RTL TB.

**R9 (medium) — `frac_M` 8-bit wrap.**
`frac_M = L.slc<8>(lz0-8) + 1` is an `ac_int<8,false>`
(`scaler_...v2.h:97-102`). If the slice is 0xFF, the result is 0x00, changing
`borrow`. Python's `frac_m` can be 256 in the same situation
(`config.py:236-239`). Preserve the HLS wrap if bit-exactness with the HLS
simulation is required; test with a mantissa just below 2.0.

**R10 (medium) — special values are not handled.**
There is no Inf/NaN/zero special case. Zero is treated as subnormal:
`e_eff=1`, `sig_lz=1.0`, `f_out=0`. Inf/NaN have `exponent=all ones` and are
scaled like finite values. If inputs can be non-finite, define the intended
behavior explicitly.

**R11 (medium) — large/variable shifts.**
`element_shift_fn` computes `(1 << (-A)) - 1` and `sig >> (-A)` with an `int`
shift count (`scaler_...v2.h:145,148`); `A` can be below -32 for wide-range
BF16. In C++ this is undefined for shifts ≥32; AC overloads may clamp, Catapult
may differ. Implement the RTL as a saturating barrel shift: if `-A >= 11`, the
right-shift result is 0 and `dropped = (sig != 0)`, so `mag = (sig != 0) ? 1 : 0`.
Similarly `0xFF >> q_shift` in HLS (`preprocess_...ccore.h:270`) is only defined
for `q_shift<8`; since `q_shift` is a multiple of 8, use the mux form in 3.7.3.

**R12 (medium) — no executable preprocess testbench.**
The shipped `CCS_MAIN` is a stub (`preprocess/tb/...cpp:117-131`); the top TB
prints but never fails (`top/tb/tb_top_parallel.cpp:246-249`). There is no
golden output file or reference model. All verification must be built from
this specification plus a fresh C++/Python model.

**R13 (low) — `sa_latched` uninitialized.**
It has no constructor initialization (`preprocess_...ccore.h:37`); only
`reset_sa` on the first weight of a tile sets it to 255 (`:67-69`). Activation
packets before any weight, or a tile with fewer than N weight packets, use
stale/X state. Reset to 255 in RTL and assert the protocol.

**R14 (low) — backpressure and state update order.**
HLS updates `col_counter` *after* `out_ch.write` (`:310-319`). If the write
stalls, the state update must still happen exactly once. In RTL, commit on the
handshake, not on `in_valid` alone.

**R15 (low) — `N=1` and non-power-of-two K.**
`counter_t = ac_int<0,false>` for N=1 (`params_parallel.h:46-47`); K must be
≥2 because `max_idx` is `ac_int<log2K,false>` (`scaler_...v2.h:73`). Use N≥2
and K power-of-two in the reduced configuration.

**R16 (low) — struct layout/padding.**
`cfg_t` and the packages are C++ structs of `ac_int`/`ac_array`. Their bit
layout in Catapult RTL is tool-defined. For hand-written RTL, define the
flattened port order explicitly (Section 2.1) and do not rely on C++ padding.

**R17 (low) — unused planes may be X.**
HLS computes all 6 cores regardless of `s` (`preprocess_...ccore.h:166-170`).
For `s=3` planes 4/5 are unused, but a hand-written RTL can legitimately
ignore them. For HLS co-simulation, drive them to zero to avoid X differences
in the (unused) cores and in `sa` if the core is later reused.

---

## Appendix A — one-to-one HLS quirks checklist

| Quirk | HLS site | RTL action |
|---|---|---|
| `is_int_eff` includes `dTypeA==3` | `preprocess_...ccore.h:64`, `scaler_...v2.h:222` | assert unsupported combos |
| `sa` min of `max(shift,0)` | `preprocess_...ccore.h:71` | implement exactly |
| weight shift clamp `≤0` | `:258-265` | implement for INT8 weights |
| power-of-two channel is low-byte mask | `:270,294` | mux `(q_shift==0)?low:0` |
| modop called with modulus 0 then overwritten | `:283-294` | bypass modop for `r==0` |
| `frac_M` 8-bit wrap | `scaler_...v2.h:99` | preserve or document deviation |
| subnormal flush for scale only | `:275-281` | two arrays: `f_out` vs `sig_lz` |
| `lz0` from unadjusted lz | `:96-102,117` | compute `frac_M` before `-14` |
| round away from zero | `:145-153` | add 1 if any dropped bit |
| q_shift multiple of 8 | `:151-153` | enforce |
| `max_idx` write-back is a no-op | `:73-78` | drop |
| `col_no` reverse sequence | `preprocess_...ccore.h:309-319` | implement |
| `intint` bypass | `:306` | output flag only |

---

## Appendix B — reference model (Python-like, integer-exact)

```python
def preprocess_packet(data, cfg, is_weight, state):
    # data[g][j] : W-bit integer, g in 0..11, j in 0..K-1
    W = 8 if is_fp8(cfg, is_weight) else 16
    E, S = cfg.E, cfg.s
    M, bias = W - E - 1, (1 << (E - 1)) - 1
    is_int = is_int_packet(cfg, is_weight) or cfg.dTypeA == 3
    is_fp8 = is_fp8_packet(cfg, is_weight)

    # 1) unpack all 6 cores (only ceil(12/S) are used)
    per_core = []
    for g in range(6):
        sign = [bit(data[g][j], W - 1) for j in range(K)]
        e, f = parse_fields(data[g], W, E, M)          # per dtype switch
        sub = [x == 0 for x in e]
        f_out, sig_lz, e_eff = [], [], []
        for j in range(K):
            if is_int:
                mag7 = data[g][j] & 0x7F
                mag = mag7
                if sign[j]:
                    mag = ((1 << 7) | mag7)
                    mag = ((~mag) + 1) & 0xFF          # 8-bit two's complement magnitude
                f_out.append(mag)
                sig_lz.append(mag << 3)
                e_eff.append(e[j])                     # must be 0
            else:
                v = f[j]
                if not sub[j]:
                    v |= (1 << M)
                f_out.append(v)
                if sub[j]:
                    e_eff.append(1)
                    sig_lz.append((1 << M) << (10 - M))
                else:
                    e_eff.append(e[j])
                    sig_lz.append(v << (10 - M))
        max_exp = max(e_eff)
        diff = [max_exp - x for x in e_eff]

        L = 0
        for j in range(K):
            d = diff[j]
            if d >= 8:
                lm = 0 if sig_lz[j] == 0 else 1
            else:
                tlen = max(0, 11 - 8 + d)              # 3..10
                trunc = sig_lz[j] & ((1 << tlen) - 1)
                lm = sig_lz[j] >> tlen
                if trunc:
                    lm += 1
            L += (1 << 16) if lm >= 256 else lm * lm
        width = ceil_log2(K) + 17
        lz0 = width - bit_length(L)
        lz = lz0 if is_int else lz0 - 14
        frac = 0
        if lz0 >= 8:
            frac = (((L >> (lz0 - 8)) & 0xFF) + 1) & 0xFF
        borrow = 1 if frac > M_FRAC[S - 1] else 0
        shift_tmp = floor((M_EXP[S - 1] - lz - (borrow + 1)) / 2)
        shift_raw = shift_tmp if is_int else shift_tmp - (max_exp - bias)
        per_core.append((sign, f_out, diff, shift_tmp, shift_raw, max_exp))

    # 2) sa bookkeeping (per core)
    if is_weight and cfg.dTypeB == 3:
        if state.col == N - 1:
            for g in range(6):
                state.sa[g] = 255
        for g in range(6):
            state.sa[g] = min(state.sa[g], max(per_core[g][4], 0))

    apply_adjust = (cfg.dTypeB == 3) and (not is_weight) and (cfg.dTypeA != 3)
    sa_eff = [state.sa[g] if apply_adjust else 0 for g in range(6)]
    intint = (cfg.dTypeA == 3) and (cfg.dTypeB == 3)

    # 3) per-lane q_base/q_shift and channel assembly
    out_data = [[0] * K for _ in range(12)]
    out_shift = [0] * 12

    if intint:
        # HLS bypass: low byte of every plane, no scaler/modop, no clamp.
        for c in range(12):
            for j in range(K):
                out_data[c][j] = signed8(data[c][j] & 0xFF)
        # s=1 mapping selects core 0 for every channel; apply_adjust is false,
        # so sa_eff is 0 in this mode.
        out_shift = [per_core[0][4]] * 12
    else:
        for g in range(12 // S):                       # used cores
            sign, f_out, diff, shift_tmp, shift_raw, _ = per_core[g]
            adj_st = shift_tmp + sa_eff[g]
            out_shift_group = shift_raw + sa_eff[g]
            for j in range(K):
                A = (0 if adj_st > 0 else adj_st) if is_int \
                    else adj_st - M - diff[j]
                qb, qs = element_shift(sign[j], f_out[j], A)
                if is_int:
                    # HLS 241-256: same low byte on every residue channel.
                    # This is NOT qb mod m_r; see R6.
                    for r in range(S):
                        out_data[g * S + r][j] = signed8(qb & 0xFF)
                else:
                    for r in range(S):
                        c = g * S + r
                        if r == 0:
                            out_data[c][j] = (qb & 0xFF) if qs == 0 else 0
                        else:
                            out_data[c][j] = base_shift_mod(qb, qs >> 3,
                                                            OZ2_MODULI_8BIT[r - 1])
            for r in range(S):
                out_shift[g * S + r] = min(out_shift_group, 0) \
                    if (cfg.dTypeB == 3 and is_weight) else out_shift_group

    # 4) col_no sequencing
    col_no = state.col
    if is_weight:
        state.col = N - 1 if state.col == 0 else state.col - 1

    return out_data, out_shift, col_no, intint, is_weight, cfg.s
```

`element_shift` and `base_shift_mod` are exactly the pseudocode in 3.6 and
3.8. `ceil_log2(K)+17` is the `lz_temp` width; `signed8(x) = x-256 if x>=128
else x`.

---

## Appendix C — source map (most relevant lines)

| Topic | File:line |
|---|---|
| Top wrapper `run` | `HLS/preprocess/include/preprocess_parallel_compressed_ccore.h:126-322` |
| Core `run` | same:45-89 |
| `sa` logic | same:63-75 |
| Per-lane shift call | same:82-86 |
| Modop type/instantiation | same:111-112 |
| Core array (6) | same:114-116 |
| Input read / plane split | same:135-147 |
| Mode flags | same:155-159 |
| Core loop | same:166-170 |
| Shift mapping | same:182-193 |
| `base_select` | same:198-209 |
| `moduli_select` | same:211-221 |
| INT8×INT8 path | same:223-240 |
| INT8/current path | same:241-266 |
| Float/modop path | same:267-296 |
| Output flags / col counter | same:306-319 |
| Params/widths | `HLS/preprocess/include/params.h:20-39,55-88` |
| Packages | `HLS/preprocess/include/params_parallel.h:33-62` |
| Global types | `HLS/common/include/global_params.h:23,32,49-59,94-98` |
| Tables | `HLS/common/include/ozaki_tables.h:35-51,65-68,147-159` |
| Scaler top | `HLS/preprocess/include/scaler_compressing_see_mantissa_v2.h:191-304` |
| Parse | same:224-283 |
| `arr_max` | same:30-122 |
| `element_shift_fn` | same:127-158 |
| `M_EXP/M_FRAC` | same:22-27 |
| Legacy shifter | `HLS/preprocess/include/shifter.h:39-124` |
| Postprocess signed use | `HLS/postprocess/include/postprocess_parallel.h:115,192` |
| Iterated signed reduction | `HLS/modulo/include/iterated_new_s12_scalar.h:81-93` |
| CUDA reference reduction | `reproduction/ozcore/ozcore-artifact/src/emulation/llm/fast_mod/fast_mod_cuda_kernel.cu:148-205` |
| Preprocess TB (stub) | `HLS/preprocess/tb/tb_preprocess_parallel_compressed_ccore.cpp:5-10,29-35,117-131` |
| Top TB packet protocol | `HLS/top/tb/tb_top_parallel.cpp:55,157-211,215-249` |
| Modules config | `HLS/modules.json:3,102-119,392-410` |
| Reset config | `HLS/scripts/catapult.tcl:126` |
| Missing header | `HLS/modulo/include/base_shift_mod_vec.h` (absent) |
