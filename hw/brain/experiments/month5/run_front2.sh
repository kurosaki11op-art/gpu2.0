#!/bin/sh
cd "$(dirname "$0")"
for m in none bp fa; do MODE=$m EP=8 F=32 POOL=2 python3 front_end_test.py > front_end_p2_$m.log 2>&1; done
