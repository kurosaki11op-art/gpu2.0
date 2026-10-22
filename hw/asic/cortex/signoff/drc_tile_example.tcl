gds readonly true
gds flatten false
gds read tile_0_0.gds
load tile_0_0
select top cell
drc style drc(full)
drc euclidean on
drc on
drc catchup
puts "TILE 0_0 TOTAL: [drc count total]"
puts "TILE 0_0 RULES: [drc listall count]"
quit -noprompt
