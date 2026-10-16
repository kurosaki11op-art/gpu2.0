#!/bin/sh
# floor2f: floor2e's global-routed database again with another router seed (or_seed 43) to try to clear its single last
# violation (VDD vs a signal on met5). ITER = 30 passes.
cd "$(dirname "$0")/.."
OUT=floor2f SEED=43 ITER=30 timeout 30000 /opt/eda_or/bin/openroad -no_init -exit route3.tcl > floor2f/route_full.log 2>&1
echo "floor2f finished" >> floor2f/route_full.log
