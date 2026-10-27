#!/bin/sh
cd "$(dirname "$0")"
while pgrep -f run_fix10.sh >/dev/null; do sleep 15; done
for sab in 0 1; do for rep in a b; do MEMDROP=0.10 ALARM=0.10 SABCH=3 CTRL=1 SABOTAGE=$sab python3 staged_progress.py > staged_progress_mem_sab${sab}_$rep.log 2>&1; done; done
