# P0b: 16x16 weight-stationary INT8 tile on TSMC 28nm HPC+ FF.
set Design int8_tile16
remove_design -all

set lib_db "/home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs.db"
set target_library $lib_db
set link_library [list "*" $lib_db]
set search_path [list . /home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs]

analyze -format verilog -library WORK ./rtl/int8_tile16.v
elaborate $Design
current_design $Design
link
check_design > check_design_tile16.txt

source ./synopsys_tsmc_ff_tile.sdc
compile_ultra -timing -gate_clock
report_area -nosplit -hierarchy > area_tile16.txt
report_timing -max_paths 10 > timing_tile16.txt
report_power > power_tile16.txt
report_qor > qor_tile16.txt
report_constraint -all_violators > constraints_tile16.txt
write -format verilog -hierarchy -output netlist_tile16.v
exit
