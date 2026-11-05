# 300 MHz constraint set for the SMIC 28 nm TT library.
# Kept free of cell names from the 130 nm tutorial so it works with the
# sc12mcpp140z library.

set clk_period 3.333
create_clock -name clk -period $clk_period [get_ports clk]
set_clock_uncertainty 0.05 [get_clocks clk]
set_clock_transition 0.05 [get_clocks clk]
set_clock_latency 0.05 [get_clocks clk]

set_input_transition 0.05 [remove_from_collection [all_inputs] [get_ports clk]]
set_load 0.05 [all_outputs]
set_input_delay 0.2 -clock clk [remove_from_collection [all_inputs] [get_ports clk]]
set_output_delay 0.2 -clock clk [all_outputs]

# The async reset is not timed as a data path.
set_false_path -from [get_ports rst_n]
set_false_path -to [get_ports valid_out]
