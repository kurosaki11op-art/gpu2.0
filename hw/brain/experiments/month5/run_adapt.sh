#!/bin/sh
cd "$(dirname "$0")"
for sab in 0 1; do for rep in a b; do ALARMMODE=adaptive SABCH=3 CTRL=1 SABOTAGE=$sab python3 staged_progress.py > staged_progress_adapt_sab${sab}_$rep.log 2>&1; done; done
for sab in 0 1; do CTRL=0 SABCH=3 SABOTAGE=$sab python3 staged_progress.py > staged_progress_uniform_sab${sab}.log 2>&1; done
