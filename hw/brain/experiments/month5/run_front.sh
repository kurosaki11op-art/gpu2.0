#!/bin/sh
cd "$(dirname "$0")"
for m in none bp fa sparse; do MODE=$m EP=4 python3 front_end_test.py > front_end_$m.log 2>&1; done
