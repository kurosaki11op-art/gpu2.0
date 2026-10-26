#!/bin/sh
cd "$(dirname "$0")"
CTRL=1 SABOTAGE=1 python3 staged_controller.py > staged_controller_sab_on.log 2>&1
CTRL=0 SABOTAGE=1 python3 staged_controller.py > staged_controller_sab_off.log 2>&1
CTRL=1 SABOTAGE=0 python3 staged_controller.py > staged_controller_clean_on.log 2>&1
CTRL=0 SABOTAGE=0 python3 staged_controller.py > staged_controller_clean_off.log 2>&1
