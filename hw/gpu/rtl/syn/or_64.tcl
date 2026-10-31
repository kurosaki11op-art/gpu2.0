read_liberty /tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/asicsyn/hd_tt.lib
read_verilog netlist_64.v
link_design tile_mm
create_clock -name clk -period 10 [get_ports clk]
set_input_delay 1 -clock clk [get_ports {w_data* a_data* k* m* nb* start rst}]
set_output_delay 1 -clock clk [all_outputs]
puts "fanout of the worst nets before repair:"
report_check_types -max_slew -max_capacitance -max_fanout -violators
repair_design
report_checks -path_delay max -format full
report_worst_slack -max
report_design_area
