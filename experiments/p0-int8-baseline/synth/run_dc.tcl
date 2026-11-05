# P0 DC synthesis script for the INT8 MAC on the SMIC 28 nm library.
# Run inside the EDA VM from the experiment directory:
#   dc_shell -f run_dc.tcl -output_log_file dc.log
#
# The library path and cell names are specific to the user's environment
# (/home/host/zonghe_am3_ex/synopsys). Adjust if the environment moves.

set Design int8_mac
set dc_date [exec date +%Y_%m%d_%H%M]
remove_design -all

set lib_dir "/home/host/zonghe_am3_ex/synopsys"
set lib_db "$lib_dir/sc12mcpp140z_l28hpc_hpk_rvt_c30_tt_ctypical_max_0p90v_85c.db"
set target_library $lib_db
set link_library [list "*" $lib_db]
set search_path [list . $lib_dir]

# Read the RTL. The design files are Verilog-2001 compatible.
analyze -format verilog -library WORK ./rtl/int8_mac.v
elaborate $Design
current_design $Design
link
check_design > check_design.txt

# 300 MHz target (period 3.333 ns), 28 nm TT corner.
source ./synopsys.sdc

# Keep hierarchy for a per-block area breakdown; flatten for timing.
compile_ultra -no_autoungroup

report_area -nosplit -hierarchy > area.txt
report_timing -max_paths 20 > timing.txt
report_power > power.txt
report_qor > qor.txt
report_constraint -all_violators > constraints.txt
write -format verilog -hierarchy -output netlist.v
write -format ddc -hierarchy -output int8_mac.ddc
exit
