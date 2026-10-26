#!/bin/sh
# piece 4: layer-2 clause learner over layer-1 clause bits; resumable blocks of 520 s
cd "$(dirname "$0")"
for i in 1 2 3 4 5 6; do INPUT=deep C=400 TT=40 SS=3 LMAX=256 RESET=$([ $i = 1 ] && echo 1 || echo 0) BUDGET=520 python3 tm_faithful.py >> tm_deep_c400.log 2>&1; done
