#!/bin/sh
cd "$(dirname "$0")"
CC=400 TT=30 EPS=3 SD=0 python3 part3_specialist.py > part3_specialist_c400_s0.log 2>&1
CC=400 TT=30 EPS=3 SD=1 python3 part3_specialist.py > part3_specialist_c400_s1.log 2>&1
CC=800 TT=60 EPS=3 SD=0 python3 part3_specialist.py > part3_specialist_c800_s0.log 2>&1
