set lib_db "/home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs.db"
set target_library $lib_db
set link_library [list "*" $lib_db]
set search_path [list . rtl]
set pairs [list [list preprocess ozcore_preprocess_s1] [list postprocess ozcore_postprocess_s1] [list mac ozcore_mac_col_s1] [list lane ozcore_lane_s1]]
foreach pair $pairs {
    set tag [lindex $pair 0]; set top [lindex $pair 1]
    remove_design -all
    analyze -format sverilog -library WORK rtl/ozcore_preprocess_s1.sv
    analyze -format sverilog -library WORK rtl/ozcore_postprocess_s1.sv
    analyze -format sverilog -library WORK rtl/ozcore_mac_col_s1.sv
    analyze -format sverilog -library WORK rtl/ozcore_lane_s1.sv
    elaborate $top
    current_design $top
    link
    compile -map_effort medium
    report_area -nosplit -hierarchy > area_$tag.txt
}
exit
