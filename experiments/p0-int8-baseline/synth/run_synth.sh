#!/usr/bin/env bash
# P0 synthesis runner: map the INT8 MAC / array to a Sky130 HD standard-cell
# library with Yosys and report area + static timing.
#
# Usage:
#   SKY130_LIB=/path/to/sky130_fd_sc_hd__tt_025C_1v80.lib \
#     ./synth/run_synth.sh int8_mac
#   SKY130_LIB=... ./synth/run_synth.sh int8_array 4
#
# The library is not vendored in this repository (large + PDK license).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB="${SKY130_LIB:-/tmp/sky130hd.lib}"
DESIGN="${1:-int8_mac}"
N="${2:-4}"

if [[ ! -s "$LIB" ]]; then
    echo "error: liberty file not found or empty: $LIB" >&2
    echo "set SKY130_LIB to sky130_fd_sc_hd__tt_025C_1v80.lib" >&2
    exit 1
fi

OUT="$ROOT/results/synth_${DESIGN}_n${N}"
mkdir -p "$OUT"

if [[ "$DESIGN" == "int8_array" ]]; then
    TOP_CMDS="read_verilog -sv $ROOT/rtl/int8_mac.sv $ROOT/rtl/int8_array.sv; chparam -set N $N int8_array; hierarchy -top int8_array"
else
    TOP_CMDS="read_verilog -sv $ROOT/rtl/int8_mac.sv; hierarchy -top int8_mac"
fi

yowasp-yosys -Q -p "
    read_liberty -lib $LIB;
    $TOP_CMDS;
    synth -top $DESIGN -flatten;
    dfflibmap -liberty $LIB;
    abc -liberty $LIB;
    opt_clean;
    stat -liberty $LIB;
    write_verilog -noattr $OUT/${DESIGN}_netlist.v;
" -l "$OUT/synth.log" | tee "$OUT/stdout.log"

echo "--- artifacts: $OUT"
