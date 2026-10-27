#!/bin/sh
cd "$(dirname "$0")"
while pgrep -f run_night.sh >/dev/null; do sleep 20; done
ALARM=0.12 CTRL=1 SABOTAGE=0 python3 staged_progress.py > staged_progress_clean_v3.log 2>&1
ALARM=0.12 CTRL=1 SABOTAGE=1 python3 staged_progress.py > staged_progress_sab_v3.log 2>&1
