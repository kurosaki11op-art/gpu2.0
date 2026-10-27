#!/bin/sh
cd "$(dirname "$0")"
SEED=1 KS=64 python3 detector_selection2.py > detector_selection2_seed1.log 2>&1
SEED=0 KS=48,96 NOCTRL=1 python3 detector_selection2.py > detector_selection2_k48_96.log 2>&1
python3 routed_rich_eval.py > routed_rich_eval.log 2>&1
