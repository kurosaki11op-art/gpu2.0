gds readonly true
gds flatten false
gds read /tmp/aw/hw/asic/cortex/floor2e/cortex.gds
load cortex_board_top
select top cell
drc style drc(full)
drc euclidean on
drc on
puts "starting catchup"
drc catchup
puts "catchup done"
puts "DRC count total: [drc count total]"
puts "DRC by rule: [drc listall count]"
quit -noprompt
