set Design fp16_mac
remove_design -all
set lib_db "/home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs.db"
set target_library $lib_db
set synthetic_library [list dw_foundation.sldb]
set link_library [list "*" $lib_db dw_foundation.sldb]
set search_path [list . /home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs /home/synopsys/syn/O-2018.06-SP1/libraries/syn]
analyze -format verilog -library WORK ./rtl/fp_mac.v
analyze -format verilog -library WORK ./rtl/fp16_mac.v
elaborate $Design
current_design $Design
link
check_design > check_design_fp16_mac.txt
source ./synopsys_tsmc_ff.sdc
compile_ultra -timing -gate_clock
report_area -nosplit -hierarchy > area_fp16_mac.txt
report_timing -max_paths 10 > timing_fp16_mac.txt
report_power > power_fp16_mac.txt
report_qor > qor_fp16_mac.txt
report_constraint -all_violators > constraints_fp16_mac.txt
write -format verilog -hierarchy -output netlist_fp16_mac.v
exit
