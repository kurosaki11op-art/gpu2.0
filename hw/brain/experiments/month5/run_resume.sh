#!/bin/sh
cd "$(dirname "$0")"
CTRL=1 SABOTAGE=1 python3 staged_progress.py > staged_progress_sab.log 2>&1
for cfg in "1 8 1.0 1" "1 4 1.0 0" "1 8 1.0 2" "20 8 0.5 2" "20 8 0.0 2"; do set -- $cfg; E=$1 K=$2 PD=$3 SEED=$4 python3 staged_mixture.py > staged_mixture_E$1_K$2_PD$3_s$4.log 2>&1; done
