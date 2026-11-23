set Design VX_tcu_fedp_tfr
remove_design -all
set lib_db "/home/host/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs/tcbn28hpcplusbwp40p140ffg0p99v0c_ccs.db"
set target_library $lib_db
set link_library [list "*" $lib_db]
set search_path [list . /home/host/tenfour /home/host/tenfour/rtl/versions/v1_fp16 /home/host/tenfour/rtl/lib_shared /home/host/vortex/hw/rtl /home/host/vortex/hw/rtl/libs /home/host/vortex/hw/rtl/tcu /home/host/vortex/hw/rtl/tcu/tfr]
set D {-define "VX_CFG_XLEN=64 VX_CFG_XLEN_64 NUM_THREADS=32 NUM_TCU_LANES=4 ASIC"}
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/VX_gpu_pkg.sv
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/libs/VX_csa_32.sv
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/libs/VX_csa_42.sv
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/libs/VX_csa_mod4.sv
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/libs/VX_csa_tree.sv
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/libs/VX_ks_adder.sv
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/libs/VX_pipe_register.sv
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/libs/VX_find_first.sv
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/libs/VX_lzc.sv
analyze -format sverilog {*}$D -library WORK /home/host/vortex/hw/rtl/libs/VX_wallace_mul.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_pkg.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/lib_shared/VX_tcu_tfr_classifier.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_tfr_lane_mask.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_tfr_mul_f16.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_tfr_mul_join.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_tfr_mul_exp.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_tfr_align.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_tfr_max_exp.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_tfr_norm_round.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_tfr_acc.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_tfr_pipe_register.sv
analyze -format sverilog {*}$D -library WORK /home/host/tenfour/rtl/versions/v1_fp16/VX_tcu_fedp_tfr.sv
elaborate $Design -parameters "N=64"
current_design $Design
link
check_design > check_fp16.txt
create_clock -name clk -period 3.333 [get_ports clk]
set_clock_uncertainty -setup 0.10 [get_clocks clk]
set_input_delay 0.50 -clock clk [remove_from_collection [all_inputs] [get_ports clk]]
set_output_delay 0.50 -clock clk [all_outputs]
set_load 0.05 [all_outputs]
set_false_path -from [get_ports reset]
compile_ultra -timing
report_area -nosplit -hierarchy > area_fp16.txt
report_timing -max_paths 5 > timing_fp16.txt
report_qor > qor_fp16.txt
exit
