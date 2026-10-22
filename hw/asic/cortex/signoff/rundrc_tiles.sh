#!/bin/sh
# usage: rundrc.sh <tiledir> ; runs magic DRC on the 6 tiles, 3 at a time, writes why_i_j.txt
D=$1; export PATH=/opt/eda_pdk/bin:$PATH PDK_ROOT=/opt/eda_pdk/share/pdk PDK=sky130A
RC=$PDK_ROOT/$PDK/libs.tech/magic/sky130A.magicrc
for t in 0_0 0_1 1_0 1_1 2_0 2_1; do cat > $D/d_$t.tcl <<EOT
gds readonly true
gds flatten false
gds read $D/tile_$t.gds
load tile_$t
select top cell
drc style drc(full)
drc euclidean on
drc on
drc catchup
set f [open $D/why_$t.txt w]
puts \$f [drc listall why]
close \$f
puts "TILE $t DONE"
quit -noprompt
EOT
done
printf "1_1\n1_0\n0_0\n0_1\n2_0\n2_1\n" | xargs -P 3 -I{} sh -c "magic -dnull -noconsole -rcfile $RC $D/d_{}.tcl > $D/d_{}.log 2>&1"
echo done > $D/drcdone.txt
