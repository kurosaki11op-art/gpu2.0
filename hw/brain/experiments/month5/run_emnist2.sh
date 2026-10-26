#!/bin/sh
cd "$(dirname "$0")"
MODE=joint EP=8 python3 emnist_staged.py > emnist_staged_joint8.log 2>&1
MODE=stage E=20 python3 emnist_staged.py > emnist_staged_E20_fine.log 2>&1
