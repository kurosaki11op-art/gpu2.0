#!/bin/sh
cd "$(dirname "$0")"
MODE=joint EP=4 python3 emnist_staged.py > emnist_staged_joint.log 2>&1
MODE=stage EP=3 E=20 python3 emnist_staged.py > emnist_staged_E20.log 2>&1
