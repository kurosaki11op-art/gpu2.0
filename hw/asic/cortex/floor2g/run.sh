#!/bin/sh
# floor2g (20 Oct 2026): floor2e's clock-tree database routed with NO signal or clock routing on met5 (SIGL / CLKL = met1-met4, top detailed-routing layer met4), so no signal can short a met5 VDD stripe
# (floor2e's last violation: VDD vs net9254 on met5, floor2f's six all sit at macro edges). ITER = 40 passes, or_seed 42.
cd "$(dirname "$0")/.."
OUT=floor2g GRA=0 MEXT=0 SIGL=met1-met4 CLKL=met1-met4 TOPL=met4 ITER=40 timeout 30000 /opt/eda_or/bin/openroad -no_init -exit route5.tcl > floor2g/route_full.log 2>&1
echo "floor2g finished" >> floor2g/route_full.log
