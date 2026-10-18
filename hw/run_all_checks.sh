#!/bin/sh
# Every bit-exact check of SPARK Cortex, one after another (never two in the same folder at once: they share files).
# usage: sh hw/run_all_checks.sh DATA_DIR [--asic]   (--asic adds the slow SRAM-macro-model runs)
# Writes hw/check_summary.txt: one PASS/FAIL line per check.
D=$1; HW=$(cd "$(dirname "$0")" && pwd); OUT=$HW/check_summary.txt; : > "$OUT"
run() { name=$1; shift; r=$( "$@" 2>&1 | tail -1 ); echo "$name: $r" | tee -a "$OUT"; }
cd "$HW/rtl/cortex"
run "core (FPGA build)"               python run_check_cortex.py "$D"
run "core (pipelined)"                python run_check_cortex.py "$D" --pipe
run "core with context memory"        python run_check_cortex_ctx.py "$D"
run "core with context, pipelined"    python run_check_cortex_ctx.py "$D" --pipe
run "core with IMPRINT (few-shot fix)" python run_check_cortex_imprint.py "$D"
run "core with IMPRINT, pipelined"   python run_check_cortex_imprint.py "$D" --pipe
run "core with slow table (Redesign 6)" python run_check_cortex_slow.py "$D"
run "core with slow table, pipelined" python run_check_cortex_slow.py "$D" --pipe
run "core with embedding path (Redesign 8)" python run_check_cortex_embed.py "$D"
run "core with embedding path, pipelined" python run_check_cortex_embed.py "$D" --pipe
run "encoder (FPGA build)"            python run_check_encoder.py "$D" mnist 10
run "encoder (ASIC, gated clocks)"    python run_check_encoder.py "$D" fashion 10 --asic
run "encoder, finer grid (ENC_S1, ASIC build)" python run_check_encoder.py "$D" fashion 10 --s1 --asic
run "encoder learning its detectors"  python run_check_encoder_learn.py "$D" mnist 40 5 10
run "general encoder, images"         python run_check_encoder_gen.py "$D" image 10
run "general encoder, sound"          python run_check_encoder_gen.py "$D" sound 10
run "general encoder, sound finer grid (3x3/s1/pool4)" python run_check_encoder_gen.py "$D" sound3 4
run "general encoder, speckle removal" python run_check_encoder_gen.py "$D" image 10 --sup
run "cochlea (buffered)"              python run_check_cochlea.py "$D" 4
run "cochlea (streaming)"             python run_check_cochlea.py "$D" 4 --stream
run "cochlea (streaming, word aligned)" python run_check_cochlea.py "$D" 4 --align
cd "$HW/rtl/cortex/sound"
run "sound chip, whole chain (aligned)" python run_check_sound_chain.py "$D"
cd "$HW/board"
run "Tang Nano board design"          python check_cortex_board.py "$D"
run "host schedule == chip model"     python check_host_schedule.py "$D"
if [ "$2" = "--asic" ]; then
  cd "$HW/rtl/cortex"
  run "core with SKY130 SRAM models"  python run_check_cortex.py "$D" --asic --small
  run "context with SRAM models"      python run_check_cortex_ctx.py "$D" --asic
fi
echo "failures: $(grep -vc ': PASS$' "$OUT")" | tee -a "$OUT"
