# P0 DC synthesis: 4-lane INT8 array on SMIC 28 nm.
set Design int8_array_n4
set dc_date [exec date +%Y_%m%d_%H%M]
remove_design -all

set lib_dir "/home/host/zonghe_am3_ex/synopsys"
set lib_db "$lib_dir/sc12mcpp140z_l28hpc_hpk_rvt_c30_tt_ctypical_max_0p90v_85c.db"
set target_library $lib_db
set link_library [list "*" $lib_db]
set search_path [list . $lib_dir]

analyze -format verilog -library WORK ./rtl/int8_mac.v
analyze -format verilog -library WORK ./rtl/int8_array.v
analyze -format verilog -library WORK ./rtl/int8_array_n4.v
elaborate $Design
current_design $Design
link
check_design > check_design.txt

source ./synopsys.sdc
compile_ultra -no_autoungroup

report_area -nosplit -hierarchy > area.txt
report_timing -max_paths 10 > timing.txt
report_power > power.txt
report_qor > qor.txt
report_constraint -all_violators > constraints.txt
write -format verilog -hierarchy -output netlist.v
exit
