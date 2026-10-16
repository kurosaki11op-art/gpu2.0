#!/bin/sh
# floor2e: floor2d (grid, placement density 0.15, light global route, no li1, guide) with ONE change: met5 power stripes at
# pitch 84 um / offset 76.2 um, so no stripe lies within 12.9 um of a macro top / bottom edge (floor2d's last 25 violations).
# route4.tcl = global route + detailed route (ITER passes), writes floor2e/cortex_routed.odb and route_drc.rpt.
cd "$(dirname "$0")/.."
OUT=floor2e GPD=0.15 SKIPGR=1 BLOCK=0 LW=0 DW=7500 DH=6200 GX=250 CH=300 PDN_HALO=20 PDN_M5_PITCH=84.0 PDN_M5_OFFSET=76.2 \
  CTS_ROOT=sky130_fd_sc_hd__clkbuf_8 CTS_BUFS="sky130_fd_sc_hd__clkbuf_2 sky130_fd_sc_hd__clkbuf_4" CTS_CLUSTER=30 \
  timeout 9000 /opt/eda_or/bin/openroad -no_init -exit flow3.tcl > floor2e/flow.log 2>&1
[ -f floor2e/cortex_cts.odb ] || { echo "flow failed" >> floor2e/flow.log; exit 1; }
OUT=floor2e GRA=0 MEXT=0 CLKL=met1-met5 ITER=40 timeout 30000 /opt/eda_or/bin/openroad -no_init -exit route4.tcl > floor2e/route_full.log 2>&1
echo "floor2e finished" >> floor2e/route_full.log
