#!/bin/sh
cd "$(dirname "$0")"
while pgrep -f run_mixture.sh >/dev/null; do sleep 20; done
CTRL=1 SABOTAGE=0 python3 staged_progress.py > staged_progress_clean.log 2>&1
CTRL=1 SABOTAGE=1 python3 staged_progress.py > staged_progress_sab.log 2>&1
