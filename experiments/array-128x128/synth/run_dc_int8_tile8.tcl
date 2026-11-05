set Design int8_tile8_array
remove_design -all
set lib_db "/home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs.db"
set target_library $lib_db
set synthetic_library [list dw_foundation.sldb]
set link_library [list "*" $lib_db dw_foundation.sldb]
set search_path [list . /home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs /home/synopsys/syn/O-2018.06-SP1/libraries/syn]
analyze -format verilog -library WORK ./rtl/int8_mac.v
analyze -format verilog -library WORK ./rtl/int8_tile8_array.v
elaborate $Design
current_design $Design
link
check_design > check_design_int8_tile8.txt
source ./synopsys_tsmc_ff.sdc
compile_ultra -timing -gate_clock
report_area -nosplit -hierarchy > area_int8_tile8.txt
report_timing -max_paths 10 > timing_int8_tile8.txt
report_power > power_int8_tile8.txt
report_qor > qor_int8_tile8.txt
write -format verilog -hierarchy -output netlist_int8_tile8.v
exit
