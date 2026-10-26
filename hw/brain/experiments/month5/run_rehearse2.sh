#!/bin/sh
cd "$(dirname "$0")"
for e in 20 50; do E=$e PICK=random AUG=cross PL=1.0 python3 staged_rehearse2.py > staged_rehearse2_off_$e.log 2>&1; done
