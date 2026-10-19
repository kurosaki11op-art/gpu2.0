#!/bin/sh
# resumable: re-run this script after any restart, finished pieces are cached in DATA_DIR/noisy_cache
cd "$(dirname "$0")" && python3 noisy_train.py "$1" >> noisy_train.log 2>&1
