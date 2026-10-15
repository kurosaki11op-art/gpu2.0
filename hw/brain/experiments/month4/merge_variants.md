---
title: Moving knowledge between chips - merge vs hand-over
date: 2026-10-15
tags: [month4, transfer, merge, simulated]
---
# Moving knowledge between chips: merge vs hand-over (SIMULATED, 15 Oct 2026)

**Question.** The parallel merge (chip A learns 0-4, chip B learns 5-9, tables and counts added, one night) loses
about 7 points on sound against learning in stages (64.3 vs 71.2). Why, and is there a better way to move knowledge?

**Setup.** Exact integer chip model (month-2 rule), 3 seeds (example order and random lanes), full training sets.
Scripts: [merge_night.py](merge_night.py), [merge_rebuild.py](merge_rebuild.py), [merge_handover.py](merge_handover.py);
logs [merge_night.log](merge_night.log), [merge_rebuild.log](merge_rebuild.log), [merge_handover.log](merge_handover.log)
and the `merge_*_<task>.json` files.

| Way of moving knowledge (3-seed means, SIMULATED) | digits | clothing | sound |
|---|---|---|---|
| Parallel merge, self-ending night (today's method) | 93.3 | 81.4 | 64.3 |
| Parallel merge, looser night stop (8 surprises / 256) | - | 81.4 | 64.3 |
| Parallel merge, full night (no self-stop, 120k dreams) | - | 81.6 | 60.4 |
| Merge by rebuilding (add counters only, table from zero by dreams) | 88.5 | 73.8 | 50.4 |
| **Hand-over** (A's memory copied into B, B then learns 5-9 itself) | **95.6** | **82.7** | **71.6** |
| For reference: 10 one-class stages on one chip | 93.0 | 78.7 | 71.2 |

**What it shows.**
- After a merge the self-ending night stops after one block of 256 dreams (the merged table surprises the dreams), even
  with a looser stop. Letting it run the whole night does not help: on sound it costs 4 points. The night is not the
  problem.
- Rebuilding the table from dreams alone is much worse everywhere (failure): dreams cannot replace what real
  examples wrote into the table, least of all on sound.
- The loss is structural: in a parallel merge neither chip ever saw the other half's classes, so nothing taught the
  table to separate 0-4 from 5-9. In a hand-over, chip B learns 5-9 while 0-4 are already known, so its days and
  dreams draw that line. Hand-over gains +2.3 / +1.3 / +7.3 points over the merge (digits / clothing / sound).
- Cost: a hand-over is sequential (B must wait for A's memory); the merge lets chips learn at the same time. Both stay
  on the chip with the existing commands (export / load / learn), no new hardware.

**Board-size check (SIMULATED, emulator, 1 seed).** `hw/board/cortex_transfer.py --dry-run --per-class 300` (the
board demo: 300 examples per class, 1,000 test digits): hand-over 90.9%, merge 91.4%. At this small size they are
level; the gain above is at full training size and largest on sound. `--handover` is now an option of the transfer
demo; the merge stays the default.

**Decision.** Recommend hand-over when knowledge can move in sequence (month 5 plan: run both on the boards); keep the
merge for chips that must learn at the same time. Rebuild and longer nights rejected.

Related: [month4 index](INDEX.md), [Board README](../../../board/README.md), [Project memory](../../../../docs/PROJECT_MEMORY.md), [Results at a glance](../../../../docs/results_at_a_glance.md)
