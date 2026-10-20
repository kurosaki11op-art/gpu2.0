# Sensory node: two senses in one chip (20 Oct 2026)

What was built, what it measured, and what it still lacks. Numbers are labelled SIMULATED (software model of the chip), MEASURED (software run of an ordinary network, used only as a ruler) or bit-exact (RTL simulation equals the model, 0 mismatches). Journal entries: [journal](../../docs/journal.md) (20 Oct 2026, night).

## The idea
A brain senses with eyes and ears and combines them: a heard word can name a seen thing (no teacher), and one sense covers for the other. SPARK now has a retina and a cochlea feeding **one** table. A picture alone, a sound alone, or both work; the sound bits keep a fixed offset in the list.

## What is in the chip (RTL)
| Part | File | Check (bit-exact) |
|---|---|---|
| Two senses into one core (retina 4 x 32 detectors, cochlea with noise floor and word alignment, sound encoder 4 x 32; NB = 9,216, AW = 14) | `hw/rtl/cortex/cortex_sense_top.v`, `tb_sense_top.v` | `run_check_sense_top.py`: 48 commands, 9,270 lines, 0 mismatches |
| Core at the full two-sense width with the big sound code (NB = 27,648, AW = 15) | `cortex_core.v` (parameters only) | `run_check_cortex_twosense.py`: 200 lines, 0 mismatches |
| All 10 class scores after a PREDICT (`rd_scores`, hooks build) | `cortex_core.v` | `run_check_cortex_hooks.py` (now with `S` lines): PASS |
| Sleep neighbours: the K buffered codes sharing the most active bits with a query (two-pointer merge, no multiplier) | `cortex_neighbours.v`, `tb_neighbours.v` | `run_check_neighbours.py`: 0 mismatches |
| Pooling of the scores over the neighbours: the new name of each buffered picture (adds and one compare per class; 3,521 cycles for 32 pictures) | `hw/rtl/cortex/cortex_pool.v`, `tb_pool.v`; software twin `hw/brain/cross_modal.py` (`pool_names`) | `run_check_pool.py`: 0 names differing (ties, negative scores, 10 / 6 / 1 known classes) |
| Whole sleep cleaning on the chip's own parts: core scores + neighbour unit + pooling unit | the three above | `run_check_sleep_clean.py`: scores, neighbours, names (software and pooling unit) identical to the model |
All are in `hw/run_all_checks.sh`. The grouping step (competitive learning for label-free categories) is the part still in software; the overlap unit costs about 26,000 cycles per query at 64 slots (a 64-picture buffer in about 1.7 M cycles, ESTIMATED).

## Size
A smaller sound code works as well as the big one (SIMULATED, [soundsize log](../../hw/brain/experiments/month4/brain_strict_soundsize.log)): 4 channels x 32 detectors = 4,608 sound bits give both-senses accuracy 98.97 against 98.33 for 10 x 64 (23,040 bits). The two-sense table is then 9,216 bits, about 2x the one-sense chip (129 KB for 4,608 bits), not 6x.

## Results (SIMULATED unless marked; MNIST digits + FSDD spoken digits; one pass, margin 256 / 1,500 dreams / 1 night; CNN rows MEASURED)
| Test | SPARK | small CNN (ruler, never in the chip) |
|---|---|---|
| picture learner, true labels | 97.40 | 98.52 |
| both senses in one table (labelled pairs) | 98.97 (4 x 32 sound code) | 99.45 |
| picture 25 % damaged + sound | 97.3 | 99.25 |
| picture 25 % damaged, no sound | 85.4 | 80.8 |
| **zero picture labels**: the ear (right on 72-74 % of unfamiliar speakers) names the pictures | **89.67** | 83.45 |
| zero picture labels + cleaning | **93.88** (sleep neighbour pooling, names 95 % right) | 82.87 (self-training) |
With labels the CNN is 0.5-1 point ahead; with **no picture labels SPARK is ahead by 10 points**, because sleep-time neighbour pooling cleans the ear's noisy names, whereas the CNN's self-training reinforces its own mistakes. Damage was not identical (25 % of lit pixels for the CNN, 25 % of active code bits for SPARK).

## Second dataset pair (SIMULATED, 3 seeds)
MNIST pictures + Speech Commands spoken digits (many speakers, varied microphones): ear alone on unseen speakers 75.6, its names 72.5 % right; picture learner true labels 97.40; **zero picture labels 92.30 as given, 96.93 after sleep cleaning** (names 98.1 % right); both senses 98.87; picture 25 % damaged + sound 98.42 (87.15 without sound). See the [journal](../../docs/journal.md).

## Clothing with no picture labels (SIMULATED ear, 3 seeds, one pass)
With a name source that is right only 60-73 % of the time (errors random, or confusable: shirt / T-shirt / pullover / coat), sleep cleaning lifts clothing from 83.2 / 78.7 (names as given, confusable errors) to **85.4 / 85.2**, against 86.55 with every true label (cleaned names 94-95 % right). This is the digits result carried to the class set that limited the few-label tests (78 vs 83.3). The ear is simulated; there is no spoken clothing set. See the [journal](../../docs/journal.md).

## Categories with no labels (SIMULATED, 2 seeds)
A seen digit and a heard clip of the same digit occur together. Competitive learning (k-means by overlap) on the joined picture + sound code forms the groups with **no labels**; each group is named by one label; a joint table then re-names every pair with both senses pooled over buffered neighbours (sleep). With **30 groups (30 labels in total, 3 per class)**: names right 92-93 % at the start, 96-97 % after sleep; a picture learner on the final names reaches **96.1 / 97.0** (FSDD / Speech Commands pairs) against 97.4 with all 10,000 labels; with 10 groups only 73 / 86. Picture-only groups reach about 67; sound-only groups 42-44. The second sense is what makes the category layer work. Grouping runs as host-side k-means (not in RTL). See the [journal](../../docs/journal.md).

## Noticing a new class by itself (SIMULATED, 2 seeds)
The chip knows digits 0-7 (picture + sound) and sees an unlabelled stream where 20 % of the pairs belong to digits 8 and 9 with unfamiliar words. A pair is flagged when its top score is below the 10th percentile of known pairs (AUROC **0.96 / 0.97**, flag precision **99.2 / 99.3 %**; picture bits alone 0.53-0.57, so the two senses together do it); flagged pairs form groups, each group is named with one label, sleep cleans the names, and the chip learns them as one stage with dreams. All 10 digits **93.7 / 97.3** (oracle with true labels 96.8 / 97.6), new digits 87.9 / 98.3, old digits not forgotten (95.1 / 97.1). The earlier picture-only recruitment failed because its slots were contaminated; with two senses almost nothing is. Grouping runs as host-side k-means. See the [journal](../../docs/journal.md).

## Limits
- SIMULATED model plus RTL simulation; nothing measured on silicon or the board.
- Two dataset pairs (MNIST + FSDD spoken digits, MNIST + Speech Commands digits); 2 seeds for the CNN rows, 3 seeds for SPARK.
- The ear for the zero-label test was trained on 3 speakers and the paired clips come from 2 others; test speaker is a sixth.
- The grouping step (k-means for the label-free categories) is not in RTL; the buffer is 64 pictures (K = 8); the all-pairs overlap grows with the square of the buffer.
- The sound path needs the cochlea RTL and its detectors loaded (`tma_*`), like the one-sense sound chip.

Related: [Results index](INDEX.md), [Journal](../../docs/journal.md), [Project memory](../../docs/PROJECT_MEMORY.md), [Hardware index](../HARDWARE_INDEX.md), [Redesign tests](brain_strict_redesign.md)
