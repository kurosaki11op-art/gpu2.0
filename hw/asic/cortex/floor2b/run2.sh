#!/bin/sh
# floor2b second stage: global + detailed routing from floor2b/cortex_cts.odb with route4.tcl (light global-route settings).
cd "$(dirname "$0")/.."
OUT=floor2b GRA=0.1 ITER=30 timeout 36000 /opt/eda_or/bin/openroad -no_init -exit route4.tcl > floor2b/route.log 2>&1
echo "run2.sh finished" >> floor2b/route.log
