#!/bin/sh
cd "$(dirname "$0")"
E=20 PICK=random AUG=cross PL=1.0 python3 staged_rehearse2.py > staged_rehearse2_share_20.log 2>&1
