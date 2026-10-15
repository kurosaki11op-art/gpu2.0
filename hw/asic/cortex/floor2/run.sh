#!/bin/sh
# Floorplan rework: 8x8 macro grid with wider channels (250 um between columns, 300 um between rows) on a
# 7.5 x 6.2 mm die, lighter clock tree, pipelined clock-gated netlist; then detailed routing (route.tcl, 10 passes).
cd "$(dirname "$0")/.."
DW=7500 DH=6200 GX=250 CH=300 CTS_ROOT=sky130_fd_sc_hd__clkbuf_8 CTS_BUFS="sky130_fd_sc_hd__clkbuf_2 sky130_fd_sc_hd__clkbuf_4" CTS_CLUSTER=30 \
  timeout 9000 /opt/eda_or/bin/openroad -no_init -exit flow.tcl > floor2/flow.log 2>&1
timeout 30000 /opt/eda_or/bin/openroad -no_init -exit route.tcl > floor2/route.log 2>&1
[ -f route_drc.rpt ] && mv route_drc.rpt floor2/
