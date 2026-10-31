#!/bin/sh
# S-e: sweep of the assumed network constants. usage: sh sweep_network.sh GPU_SIM_BINARY DECODER_DIR(with 512 steps from gen_decoder.py)
SIM=$1; DEC=$2
echo "link_bytes_per_cycle hop_cycles us_per_token_near_480_context"
for L in 16 32 64 128 256; do for H in 2 16 200 2000; do
  for N in 448 512; do GPU_LINKBW=$L GPU_HOPCYC=$H GPU_STRIPE_ATTN=1 GPU_MACPC=256 GPU_SRAMBW=256 GPU_STRIPE=16 $SIM $DEC int8 $N 8388608 decode 2>/dev/null; python3 -c "import json;print(json.load(open('$DEC/counters_int8.json'))['total']['cycles'])" > /tmp/sw_$N.txt; done
  python3 -c "a=float(open('/tmp/sw_448.txt').read());b=float(open('/tmp/sw_512.txt').read());print($L,$H,round((b-a)/64/1000,1))"
done; done
