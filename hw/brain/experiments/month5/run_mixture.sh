#!/bin/sh
cd "$(dirname "$0")"
for cfg in "20 8 0.0 0" "20 8 0.5 0" "1 8 1.0 0" "20 32 0.5 0" "20 8 0.0 1" "20 8 0.5 1"; do set -- $cfg; E=$1 K=$2 PD=$3 SEED=$4 python3 staged_mixture.py > staged_mixture_E$1_K$2_PD$3_s$4.log 2>&1; done
