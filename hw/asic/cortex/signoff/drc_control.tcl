load ctrl
box 0 0 100 20
paint metal1
box 110 0 210 20
paint metal1
drc style drc(full)
drc on
drc catchup
puts "CONTROL TOTAL: [drc count total]"
puts "CONTROL RULES: [drc listall count]"
quit -noprompt
