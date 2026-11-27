set Design ozcore_simd_int8
remove_design -all
set lib_db "/home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs.db"
set target_library $lib_db
set link_library [list "*" $lib_db]
set search_path [list . rtl]
analyze -format sverilog -library WORK rtl/ozcore_simd_int8.sv
elaborate $Design
current_design $Design
link
check_design > check.txt
compile -map_effort medium
report_area -nosplit -hierarchy > area.txt
report_reference > refs.txt
report_timing -max_paths 5 > timing.txt
exit
