#!/bin/sh
# Bisect of the stalled global routing of floor2b: the old settings (no layer adjustment, no macro extension, clock on
# met1-met5) plus only the guide file and the met1 bottom layer for the detailed router.
cd "$(dirname "$0")/.."
OUT=floor2c GRA=0 MEXT=0 CLKL=met1-met5 ITER=30 timeout 36000 /opt/eda_or/bin/openroad -no_init -exit route4.tcl > floor2c/route.log 2>&1
echo "run.sh finished" >> floor2c/route.log
