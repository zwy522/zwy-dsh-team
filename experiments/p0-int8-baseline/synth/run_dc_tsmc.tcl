# P0b: same INT8 RTL, re-synthesized with the user's TSMC 28 nm HPC+ FF library.
# This isolates the standard-cell library density effect from the RTL effect.
set Design int8_mac
remove_design -all

set lib_db "/home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs.db"
set target_library $lib_db
set link_library [list "*" $lib_db]
set search_path [list . /home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs]

analyze -format verilog -library WORK ./rtl/int8_mac.v
elaborate $Design
current_design $Design
link
check_design > check_design_tsmc.txt

source ./synopsys_tsmc_ff.sdc
compile_ultra -timing -gate_clock
report_area -nosplit -hierarchy > area_tsmc.txt
report_timing -max_paths 10 > timing_tsmc.txt
report_power > power_tsmc.txt
report_qor > qor_tsmc.txt
report_constraint -all_violators > constraints_tsmc.txt
write -format verilog -hierarchy -output netlist_tsmc.v
exit
