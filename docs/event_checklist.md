---
title: Checklist for the 23 October event
date: 2026-10-19
tags: [pitch, checklist, event]
---
# Checklist for the 23 October event

**Files:** deck [SPARK_Cortex_pitch.pptx](SPARK_Cortex_pitch.pptx) (14 slides, speaker notes inside), spoken script [pitch_script_cortex.md](pitch_script_cortex.md), likely questions [pitch_qa_sheet.md](pitch_qa_sheet.md),
paper-style summary [paper_spark_cortex.md](paper_spark_cortex.md), numbers with labels [results_at_a_glance.md](results_at_a_glance.md) and [claims sheet](cortex_claims_sheet.md).

## Before the day (19-22 Oct)

1. Read the script aloud twice with the deck, timing it (about 8 minutes; 5-minute cut list at the top of the script).
2. Read the Q&A sheet aloud; the answers that must come out right: nothing is MEASURED on hardware yet; level with a small network (not better); not the first continual-learning chip; what failed (new words, staged learning).
3. Board day on your PC (this is the only way to get MEASURED numbers before the 23rd; about 2 hours, plan: [month 4 board plan](month4_board_plan.md)):
   `python hw\board\preflight.py --data D:\cortex_data`, then `python hw\board\board_day.py --port COMx --data D:\cortex_data`; send me the saved `board_day_*.txt` and I add the numbers as MEASURED to the deck and claims sheet.
   The Tang Nano bitstream is the base design (no slow table, no finer grid): its numbers are the base design's, say so.
4. Live demo (optional, 2 minutes): `python hw\board\cortex_demo.py --preload 300 --classes 0-7 --data D:\cortex_data` (emulator, bit-exact with the chip; add `--port COMx` for the real board):
   draw a new symbol as class 8, Teach a few times, Sleep, then "Test old digits" to show the old digits are kept. Rehearse it once; keep the emulator as the fallback if the board is not ready.
5. Print or save the deck as PDF as a backup; keep the script on your phone.

## Say, in this order

1. What it is: a chip that keeps learning after it ships, no multiplier, no backpropagation.
2. The result: learns in stages and keeps what it knew (95.8 / 78.3 / 82.9 vs a network at about 20), learning everything at once it is level with a small network with the slow-table option.
3. The limits, first and plainly: SIMULATED not MEASURED; clothing and words in stages; new spoken words from a few recordings; a CNN is ahead on clothing.
4. What is next: the board run, then learned word features (needs more speech data).

## Do not say

"First", "never forgets", "better than a network", "replaces GPUs", any measured power or speed (none exists), "74x less energy per chip" (it is per operation needed).

Related: [Pitch script](pitch_script_cortex.md), [Q&A sheet](pitch_qa_sheet.md), [Claims sheet](cortex_claims_sheet.md), [Month 4 board plan](month4_board_plan.md), [Project memory](PROJECT_MEMORY.md)
