#!/bin/sh
cd "$(dirname "$0")"
SEED=0 python3 routed_selected_eval.py > routed_selected_eval_seed0.log 2>&1
SEED=1 python3 routed_selected_eval.py > routed_selected_eval_seed1.log 2>&1
