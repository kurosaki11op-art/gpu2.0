#!/bin/sh
cd "$(dirname "$0")"
while pgrep -f run_front2.sh >/dev/null; do sleep 10; done
for m in bp none; do REAL=1 MODE=$m EP=8 F=32 POOL=2 python3 front_end_test.py > front_end_real_p2_$m.log 2>&1; done
