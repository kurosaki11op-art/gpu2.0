#!/bin/sh
# Striping checks S-a to S-d. Needs the M1 exports in /tmp/gpu_m1 (see hw/gpu/M1_result.md) and torch. usage: sh run_stripe_checks.sh SCRATCHDIR
SC=${1:-/tmp/stripe_chk}; mkdir -p $SC; rustc -O hw/gpu/sim/gpu_sim.rs -o $SC/gpu_sim || exit 1
echo "== S-a: md5 of simulator outputs at stripe widths 1, 4, 16 (must be equal per row)"
for d in lm lm_dec cnn; do for m in int8 w8 fp32; do for S in 1 4 16; do rm -rf $SC/x; cp -r /tmp/gpu_m1/$d $SC/x
  case $d in lm_dec) GPU_STRIPE=$S $SC/gpu_sim $SC/x $m 64 4194304 decode 2>/dev/null;; cnn) GPU_STRIPE=$S $SC/gpu_sim $SC/x $m 200 2>/dev/null;; *) GPU_STRIPE=$S $SC/gpu_sim $SC/x $m 16 2>/dev/null;; esac
  echo "$d $m S=$S $(md5sum < $SC/x/out_$m.bin | cut -d' ' -f1)"; done; done; done
echo "== S-b: counters of the transformer (int8) at stripe widths 1, 4, 16"
for S in 1 4 16; do rm -rf $SC/x; cp -r /tmp/gpu_m1/lm $SC/x; GPU_STRIPE=$S $SC/gpu_sim $SC/x int8 16 2>/dev/null; echo "S=$S $(python3 -c "import json;t=json.load(open('$SC/x/counters_int8.json'))['total'];print({k:t[k] for k in ['macs','sram_read_bytes','sram_write_bytes','mesh_byte_hops','cycles']})")"; done
echo "== S-c: scaled decoder (16 layers, d 512, ff 2048, 4 heads, vocab 8000), M3 tile rates 256 MAC and 256 B per cycle, 1 GHz"
python3 hw/gpu/stripe/gen_decoder.py $SC/dec 64
for S in 1 8 16; do for N in 1 64; do GPU_MACPC=256 GPU_SRAMBW=256 GPU_STRIPE=$S $SC/gpu_sim $SC/dec int8 $N 4194304 decode 2>/dev/null; python3 -c "import json;t=json.load(open('$SC/dec/counters_int8.json'))['total'];print('S=$S steps=$N cycles_per_token',t['cycles']/$N,'macs_per_token',t['macs']/$N)"; done; done
echo "== S-d: PyTorch hook counts"
python3 hw/gpu/stripe/torch_count.py 0; python3 hw/gpu/stripe/torch_count.py 63
