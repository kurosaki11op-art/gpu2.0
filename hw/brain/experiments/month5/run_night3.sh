#!/bin/sh
cd "$(dirname "$0")"
while pgrep -f run_night2.sh >/dev/null || pgrep -f run_night.sh >/dev/null; do sleep 20; done
for cfg in "1 8 1.0 1" "20 8 0.5 1" "1 8 1.0 0"; do set -- $cfg; E=$1 K=$2 PD=$3 SEED=$4 python3 staged_mixture.py > staged_mixture_v3_E$1_K$2_PD$3_s$4.log 2>&1; done
