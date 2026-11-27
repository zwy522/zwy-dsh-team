set lib_db "/home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs.db"
set target_library $lib_db
set link_library [list "*" $lib_db]
set search_path [list . rtl]
set pairs [list [list weight_mem ozcore_weight_mem_s1] [list psum ozcore_psum_s1] [list aligner ozcore_aligner_s1] [list control ozcore_control_s1]]
foreach pair $pairs {
    set tag [lindex $pair 0]; set top [lindex $pair 1]
    remove_design -all
    analyze -format sverilog -library WORK rtl/ozcore_weight_mem_s1.sv
    analyze -format sverilog -library WORK rtl/ozcore_psum_s1.sv
    analyze -format sverilog -library WORK rtl/ozcore_aligner_s1.sv
    analyze -format sverilog -library WORK rtl/ozcore_control_s1.sv
    elaborate $top
    current_design $top
    link
    compile -map_effort medium
    report_area -nosplit -hierarchy > area_$tag.txt
}
exit
