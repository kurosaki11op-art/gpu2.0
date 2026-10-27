#!/bin/sh
cd "$(dirname "$0")"
MAXLEN=8 DAMAGE=0.2 python3 hypothesis_loop.py > hypothesis_loop_v4.log 2>&1
CTRL=1 SABOTAGE=0 python3 staged_progress.py > staged_progress_clean_v2.log 2>&1
CTRL=1 SABOTAGE=1 python3 staged_progress.py > staged_progress_sab_v2.log 2>&1
for cfg in "1 8 1.0 1" "1 8 1.0 0" "20 8 0.5 0" "1 4 1.0 0" "1 8 1.0 2" "20 8 0.0 2"; do set -- $cfg; E=$1 K=$2 PD=$3 SEED=$4 python3 staged_mixture.py > staged_mixture_v2_E$1_K$2_PD$3_s$4.log 2>&1; done
