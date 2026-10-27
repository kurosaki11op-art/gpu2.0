#!/bin/sh
cd "$(dirname "$0")"
while pgrep -f run_front3.sh >/dev/null; do sleep 10; done
for thr in "50,150" "32,80,128,176,224" "16,48,80,112,144,176,208,240"; do
  for m in bp none; do THR=$thr MODE=$m EP=8 F=32 POOL=2 python3 front_end_test.py > front_end_thr_$(echo $thr | tr ',' '_')_$m.log 2>&1; done
done
