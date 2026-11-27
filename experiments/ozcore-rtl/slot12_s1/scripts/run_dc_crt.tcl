set Design ozcore_crt_int2fp_s1
remove_design -all
set lib_db "/home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs.db"
set target_library $lib_db
set link_library [list "*" $lib_db]
set search_path [list . rtl]
analyze -format sverilog -library WORK rtl/ozcore_crt_int2fp_s1.sv
elaborate $Design
current_design $Design
link
compile -map_effort medium
report_area -nosplit -hierarchy > area_crt.txt
exit
