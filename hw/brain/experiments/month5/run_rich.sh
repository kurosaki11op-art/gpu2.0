#!/bin/sh
# clause layer on the richer code: resumable blocks of 520 s, 300 clauses per class
cd "$(dirname "$0")"
for i in 1 2 3 4 5 6 7 8; do
  if [ $i = 1 ]; then R=1; else R=0; fi
  INPUT=rich C=300 TT=25 SS=3 LMAX=256 RESET=$R BUDGET=520 python3 tm_faithful.py >> tm_rich_c300.log 2>&1
done
