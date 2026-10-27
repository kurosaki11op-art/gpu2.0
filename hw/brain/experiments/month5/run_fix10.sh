#!/bin/sh
cd "$(dirname "$0")"
while pgrep -f run_adapt.sh >/dev/null; do sleep 15; done
for sab in 0 1; do for rep in a b; do ALARM=0.10 SABCH=3 CTRL=1 SABOTAGE=$sab python3 staged_progress.py > staged_progress_fix10_sab${sab}_$rep.log 2>&1; done; done
