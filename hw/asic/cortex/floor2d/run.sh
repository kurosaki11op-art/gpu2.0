#!/bin/sh
# floor2d: the floor2 grid again, but global placement target density 0.15 instead of 0.45 (88% of floor2c's met1
# violations sat in a ~4 mm2 central blob where the cells were packed); clock tree as before; then global routing with
# route4.tcl (no layer adjustment, no macro extension: the settings that finished global routing in floor2c).
cd "$(dirname "$0")/.."
OUT=floor2d GPD=0.15 SKIPGR=1 BLOCK=0 LW=0 DW=7500 DH=6200 GX=250 CH=300 PDN_HALO=20 \
  CTS_ROOT=sky130_fd_sc_hd__clkbuf_8 CTS_BUFS="sky130_fd_sc_hd__clkbuf_2 sky130_fd_sc_hd__clkbuf_4" CTS_CLUSTER=30 \
  timeout 9000 /opt/eda_or/bin/openroad -no_init -exit flow3.tcl > floor2d/flow.log 2>&1
[ -f floor2d/cortex_cts.odb ] || { echo "flow failed" >> floor2d/flow.log; exit 1; }
OUT=floor2d GRA=0 MEXT=0 CLKL=met1-met5 ITER=1 timeout 12000 /opt/eda_or/bin/openroad -no_init -exit route4.tcl > floor2d/route.log 2>&1
echo "global route done" >> floor2d/route.log
