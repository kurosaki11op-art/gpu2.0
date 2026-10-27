#!/bin/sh
cd "$(dirname "$0")"
for sab in 1 0; do for rep in a b; do AGDROP=0.04 SABCH=3 CTRL=1 SABOTAGE=$sab python3 staged_progress.py > staged_progress_agree_sab${sab}_$rep.log 2>&1; done; done
