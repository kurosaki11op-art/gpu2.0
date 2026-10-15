#!/bin/sh
# floor2b: the floor2 grid (8 x 8 macros, 250 / 300 um channels, standard cells in the channels) with only the
# routing fixes from the research note: power grid 20 um from the macros, router guide + layer adjustment 0.3, macro
# extension 2, detailed routing on met1-met5 (no li1), or_seed 42, up to 64 passes. Isolates the router setup.
cd "$(dirname "$0")/.."
OUT=floor2b BLOCK=0 LW=0 DW=7500 DH=6200 GX=250 CH=300 PDN_HALO=20 \
  CTS_ROOT=sky130_fd_sc_hd__clkbuf_8 CTS_BUFS="sky130_fd_sc_hd__clkbuf_2 sky130_fd_sc_hd__clkbuf_4" CTS_CLUSTER=30 \
  timeout 9000 /opt/eda_or/bin/openroad -no_init -exit flow3.tcl > floor2b/flow.log 2>&1
[ -f floor2b/cortex_groute.odb ] || { echo "flow failed" >> floor2b/flow.log; exit 1; }
OUT=floor2b timeout 60000 /opt/eda_or/bin/openroad -no_init -exit route3.tcl > floor2b/route.log 2>&1
echo "run.sh finished" >> floor2b/route.log
