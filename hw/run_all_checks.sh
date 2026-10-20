#!/bin/sh
# Every bit-exact check of SPARK Cortex, one after another (never two in the same folder at once: they share files).
# usage: sh hw/run_all_checks.sh DATA_DIR [--asic]   (--asic adds the slow SRAM-macro-model runs)
# Writes hw/check_summary.txt: one PASS/FAIL line per check.
D=$1; HW=$(cd "$(dirname "$0")" && pwd); OUT=$HW/check_summary.txt
# RESUME=1: keep the PASS lines already in check_summary.txt and run only the checks that are not there yet (a container restart then costs one check, not the whole run)
if [ "$RESUME" = "1" ] && [ -s "$OUT" ]; then grep ": PASS" "$OUT" > "$OUT.keep"; mv "$OUT.keep" "$OUT"; else : > "$OUT"; fi
run() { name=$1; shift; if [ "$RESUME" = "1" ] && grep -q "^$name: PASS" "$OUT"; then echo "$name: PASS (kept from the earlier run)"; return; fi; r=$( "$@" 2>&1 | tail -1 ); echo "$name: $r" | tee -a "$OUT"; }
need() { f=$1; name=$2; if [ ! -e "$D/$f" ]; then echo "$name: SKIP (data missing: $f)" | tee -a "$OUT"; return 1; fi; return 0; }
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
run "core with host hooks (top margin, write counter)" python run_check_cortex_hooks.py "$D"
run "encoder (FPGA build)"            python run_check_encoder.py "$D" mnist 10
run "encoder (ASIC, gated clocks)"    python run_check_encoder.py "$D" fashion 10 --asic
run "encoder, finer grid (ENC_S1, ASIC build)" python run_check_encoder.py "$D" fashion 10 --s1 --asic
run "encoder learning its detectors"  python run_check_encoder_learn.py "$D" mnist 40 5 10
run "general encoder, images"         python run_check_encoder_gen.py "$D" image 10
need speech_framesums_int.npz "speech-dependent check" && run "general encoder, sound"          python run_check_encoder_gen.py "$D" sound 10
need speech_framesums_int.npz "speech-dependent check" && run "general encoder, sound finer grid (3x3/s1/pool4)" python run_check_encoder_gen.py "$D" sound3 4
run "general encoder, speckle removal" python run_check_encoder_gen.py "$D" image 10 --sup
need speech_framesums_int.npz "speech-dependent check" && run "cochlea (buffered)"              python run_check_cochlea.py "$D" 4
need speech_framesums_int.npz "speech-dependent check" && run "cochlea (streaming)"             python run_check_cochlea.py "$D" 4 --stream
need speech_framesums_int.npz "speech-dependent check" && run "cochlea (streaming, word aligned)" python run_check_cochlea.py "$D" 4 --align
run "core, two-sense width (NB 27,648, AW 15)" python run_check_cortex_twosense.py "$D" --margin=256
run "neighbour unit (sleep cleaning)" python run_check_neighbours.py "$D" 16 4
run "pooling unit (sleep cleaning, random cases with ties)" python run_check_pool.py
run "sleep cleaning, chip scores + neighbours + pooling unit == model" python run_check_sleep_clean.py "$D"
need fsdd/0_george_0.wav "whole two-sense chip (retina + cochlea + one core)" && run "whole two-sense chip (retina + cochlea + one core)" python run_check_sense_top.py "$D"
cd "$HW/rtl/cortex/sound"
need speech_framesums_int.npz "sound chip, whole chain (aligned)" && run "sound chip, whole chain (aligned)" python run_check_sound_chain.py "$D"
cd "$HW/board"
run "Tang Nano board design"          python check_cortex_board.py "$D"
run "host schedule == chip model"     python check_host_schedule.py "$D"
if [ "$2" = "--asic" ]; then
  cd "$HW/rtl/cortex"
  run "core with SKY130 SRAM models"  python run_check_cortex.py "$D" --asic --small
  run "context with SRAM models"      python run_check_cortex_ctx.py "$D" --asic
fi
echo "failures: $(grep -v ': PASS$' "$OUT" | grep -vc ': SKIP')  skipped (data missing): $(grep -c ': SKIP' "$OUT")" | tee -a "$OUT"
