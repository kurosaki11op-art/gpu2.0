---
title: Vision review 01 - independent review of the energy, speed, cost, simulator and row K claims (31 Oct 2026)
tags: [spark, gpu, review, vision, failures]
---

# Vision review 01 (31 Oct 2026)

## Summary

1. **Reproduction is good.** The cost and energy logs, M1 and M2 reproduce to the printed digits or nearly so from a clean clone, after path edits. The arithmetic engine is mostly what the notes say.
2. **Speed, 21 to 36 microseconds per token: does not survive as a validated claim.** It needs every tile to serve every operation, which the instruction set and simulator cannot do. With the weight placement they implement, the same constants give about 1.2 ms (55x slower).
3. **Speed, 7x to 20x per user: does not survive.** The 20x end is the abandoned wafer option, and the GPU's 49 tokens/s comes from the service floor, not from a limit of the GPU.
4. **Energy, 5x floor: does not survive.** Each of five single, defensible corrections takes the worst corner below or to about 5x. Energy advantage in general survives, at about 2x to 5x with the corrections combined, and about 8x to 12x centrally with any one of them (6x at 2.78 pJ/bit).
5. **Cost: the 2.74x "bar met" does not survive.** Our side has no host or network cost, the worst-corner bar was replaced by a central one, and the $150 is unsourced. With a small host cost and compute limited by the 20% non-SRAM area it is about 1.2x central and 0.8x worst.
6. **Published arithmetic is wrong in two places:** design-cost recovery is 179 systems, not 113, and the $960 case is 1.40x, not 1.9x.
7. **Simulator: survives as a functional simulator.** PyTorch match, causal attention and the key-value cache hold up. Its count checks cannot detect a wrong counting rule, and its "INT8" leaves embeddings, attention and the stored activations in FP32.
8. **Quantisation:** INT8 survives on this one tiny model. **All large-model figures use 4-bit weights, which the simulator cannot run.** My 4-bit test costs +0.011 nats, just over the project's own 0.01 bar.
9. **Row K: survives, smaller.** The counting recipe reproduces at 88.9%; at equal accuracy the compute ratio is about 80x to 120x (counted), not 352x. I found no test-set leakage. "The code caps accuracy" is an inference, not a measured cap.
10. **Cannot be judged without data or hardware:** real SRAM energy on the target node, GPU decode power, packaging cost, buildability of an 80% SRAM die, any latency overhead. **Language cascade:** the drop stands.

All numbers I produced are **MODELLED** (a labelled patch of the project's model) unless marked **SIMULATED** or **MEASURED**. They show sensitivity. They are not better predictions than the originals. Test files: [`vision_01_tests/`](vision_01_tests/README.md).

## Findings

### V-01 The 1B latency depends on a mapping the machine does not implement
- **Severity:** BLOCKING. **Claim:** speed. **Location:** [`m2_model.py`](../../hw/gpu/m2/m2_model.py) lines 30 and 56 to 57; [`gpu_sim.rs`](../../hw/gpu/sim/gpu_sim.rs) line 68; [ISA note](../../hw/gpu/ISA_M1.md) line 13.
- **What is wrong:** the 1B case sets `R = tiles`, so all 168 tiles share every operation. The ISA places a weight tensor in one tile, and the simulator asserts this. M2-b validated the model only at `R=1`, so the `R=168` case was never simulated. An 8.4 MB feed-forward matrix does not even fit a 4 MB tile, so the simulator could not load this model.
- **Evidence (arithmetic, same constants, each matrix on only as many tiles as it needs):** 2.1 MB matrices 11,398 cycles; attention 3,799; feed-forward matrices 22,795 each; 72,185 per layer; head 22,261. Total 1,177,214 cycles = **1.18 ms, about 850 tokens/s: 55x above 21.4 microseconds, 33x above 35.6.**
- **Fairness:** striping every matrix over all tiles is a legitimate design that might reach far lower figures. It is untested: it needs a new ISA and mapper, and its broadcast and reduction traffic must be simulated. The step 5 reference gets its figure the same way (`peak * cpl` with `cpl = 1` gives each of 16 layers a whole chip), so the two models agree partly because they share this assumption.
- **Fix:** add split tensors to the ISA and mapper, then simulate the 1B model or a scaled copy. Until then quote "1.2 ms as implemented; 21 to 36 microseconds only with an unimplemented striped mapping". Do this before M4 calls any latency figure a result.

### V-02 "7x to 20x per-user speed" mixes designs and compares against a sized-down GPU
- **Severity:** BLOCKING. **Claim:** speed. **Location:** [charter](../own_gpu_charter.md) table; [step 7](../../new_start/step7_cost_basis_result.md) verdict; [step 12 log](../../new_start/experiments/step12_equal_speed.log).
- **What is wrong:** (a) 950 tokens/s, the 20x end, is the wafer option. The product's reticle chips give 321 to 481, or **6.5x to 9.8x**. (b) The GPU's 49 tokens/s is the fewest GPUs that meet a 30 tokens/s floor. The same model gives 101 tokens/s at 29 GPUs, and step 12 shows 400 tokens/s at 115 GPUs at the same cost per token. Within the model, the ratio is a sizing choice. (c) The real limit, GPU-to-GPU communication, is not modelled, so the model cannot show a capability gap either. (d) The charter cites step 4, which is marked superseded.
- **Fix:** withdraw the range. Either model GPU interconnect and report maximum per-user speed for each machine, or say only "speed advantage unquantified".

### V-03 The 5x energy floor is not robust
- **Severity:** BLOCKING. **Claim:** energy. **Location:** [`step5_worst_case_model.rs`](../../new_start/experiments/step5_worst_case_model.rs) lines 37, 42, 70.
- **What is wrong:** the headline is 13.2x central and 6.2x worst. The largest error is that attention multiply-adds use a 16-bit cache but are charged the 4-bit price of 0.12 pJ, when the model's own table says 1.5 pJ at 16 bits. Other items are the unequal cooling factor (V-04), and no clock, control or vector energy in the MAC figure. Logic leakage is 0.5 W for a chip with 160 mm2 of N5 logic (unsourced), and leakage stops when the chip is idle although SRAM must keep its weights.

| one change at a time (MODELLED; 0.55 pJ/bit, $480) | central | worst |
|---|---|---|
| as published | 13.2x | 6.2x |
| attention MACs at 1.5 pJ (`V_ATTPJ=1.5`) | 9.7x | **4.7x** (about 9.9x and 5.0x if the GPU is also charged 1.5 pJ) |
| same cooling factor on both | 10.8x | 5.1x |
| HBM 3.9 pJ/bit instead of 5.74 (my illustrative value) | 12.0x | 5.1x |
| all MAC energy x3 for clock and control (illustrative) | 8.1x | **4.0x** |
| logic leakage 5 W (illustrative) | 9.3x | **4.0x** |
| leakage during the 50% idle time | 10.4x | **4.6x** |
| SRAM at 1.0 / 2.78 pJ/bit | 10.6x / 6.0x | 5.1x / **3.0x** |
| attention 1.5 pJ, equal cooling, MAC x2, HBM 3.9 | **4.9x** | **2.2x** |

- **Fix:** correct the attention price (no judgement needed) and the cooling factor, then publish a range with these terms itemised. Do not call the row "closed, passes": its worst corner holds SRAM at the optimistic-side 0.55 pJ/bit, where step 5's worst corner used 2.78.

### V-04 Cooling and GPU power inputs are not what they are labelled
- **Severity:** MAJOR. **Claim:** energy. **Location:** model lines 36, 50, 59; [step 15](../../new_start/step15_packaged_cost_result.md); [step 3](../../new_start/step3_cost_power_result.md) inputs.
- **What is wrong:** (a) We get a liquid-cooling factor of 1.15 and the GPU an air-hall 1.4, while step 15 says our chip needs no cold plate. That hides 1.22x in every energy ratio. (b) "GPU 350 W" is described as board power while decoding, but the code adds HBM and MAC energy on top. The modelled board draws **538 W central and 287 W in the "100 W" worst corner** (0.150 and 0.080 J per token x 1,024 / 20.4 ms / 14). If 350 W were the total, the central ratio falls from 13.2x to about 8.6x. If the true figure is the 287 W the worst corner already implies, that corner is correctly harsh but wrongly named.
- **Fix:** use one cooling factor for one hall. Define a total board power and split it.

### V-05 The cost comparison gives our machine no host or network
- **Severity:** BLOCKING. **Claim:** cost. **Location:** model lines 50 and 70.
- **What is wrong:** the GPU pays `price x 1.5` for host and network. Ours pays `n x per_chip` only, and step 15's $150 lists package, board, regulation, cooling and chassis. Yet 630 chips on boards of 8 to 16 need 40 to 80 hosts or controllers, a network and racks.
- **Evidence (`V_ADD`, MODELLED, $480 chip):** +$125 per chip gives **2.19x central, 1.33x worst**; +$400 gives **1.52x, 0.92x**. For scale, the GPU's overhead at manufacturing cost is $1,660 per GPU.
- **Fix:** apply the same overhead per board slot on both sides and source it.

### V-06 Compute and bandwidth are taken from a wafer with a very different area split
- **Severity:** MAJOR. **Claim:** cost, speed. **Location:** model lines 35, 66; [step 2](../../new_start/step2_wafer_sram_result.md) table.
- **What is wrong:** the 10 PMAC/s peak is itself ASSUMED and is scaled by area to our chip. Step 2 derives that the cited wafer spends about 32% of its area on SRAM, leaving 68% for everything else; ours leaves 20%. Keeping peak MACs per mm2 of die therefore implies 3.4x higher compute density, with fabric, vector units and link circuits also inside the 20%. Bandwidth is likewise scaled per GB, which implies about 2.5x the wafer's total.
- **Evidence (`V_PEAK=2.94e15`, MODELLED):** $480 gives **1.68x central, 1.02x worst**, and speed falls to 291 and 194 tokens/s. Together with V-03's combined energy changes and a $125 host adder: **1.24x central, 0.77x worst, energy 4.5x and 2.0x.**
- **Fix:** make an area budget for the 20%. M3 synthesis can supply the MAC area.

### V-07 The cost bar changed after failing, and the input was cut 6.7x
- **Severity:** BLOCKING. **Claim:** cost. **Location:** model lines 8, 15, 18, 28; [step 7](../../new_start/step7_cost_basis_result.md); [step 15](../../new_start/step15_packaged_cost_result.md).
- **What is wrong:** the W1 bar and the step 10 and 11 bars were set in the worst corner. After repeated failures, step 15 wrote a new bar in the central corner and reports "Bar: PASS". On the original terms it **still fails (1.67x against 2x)**. Step 7 says "I will not move the bar" and that a lower packaging price cannot close the gap; its note has no correction banner. Step 15 calls the old $1,000 "a cautious placeholder for a hot chip", but the original source comment says only "ASSUMED $1,000 (no source)". The new $150 is also unsourced and is justified by an 11 W figure from the same model.
- **Fix:** write "W1 still fails in the worst corner" on the index line and in step 15's title. Add a banner to step 7. Treat $150 as an open number until a quote exists.

### V-08 Two published calculations are wrong
- **Severity:** BLOCKING. **Claim:** cost. **Location:** [step 13](../../new_start/step13_buyer_price_result.md), [step 14](../../new_start/step14_price_cut_result.md), [step 15](../../new_start/step15_packaged_cost_result.md), the journal.
- **(a) Design-cost recovery.** The notes say about 113 systems and 71,000 chips at $1,330 profit per chip. $150M / $1,330 = **112,782 chips = 179 systems**. 113 systems recover only $94.7M. It looks as if 113 thousand chips was read as 113 systems.
- **(b) $960 case.** Step 15 says $960 per chip still gives the buyer 1.9x. The model gives **1.40x** (`V_ADD=480`, 0.020 against 0.028 dollars per million tokens).
- **Checked and correct:** dies per wafer 64.8; Poisson yield 44.9%; $634 and $335 per die; the price-cut table and its margin table; the $650 and $400 limits. Note that 85% yield is the same as exp(-0.8 x 0.2), so it assumes every SRAM and periphery defect is repaired free, with no spare area, test cost or assembly loss.
- **Fix:** correct the notes and journal with a dated correction line.

### V-09 The project states its cost position in incompatible ways
- **Severity:** MAJOR. **Claim:** cost. **Location:** [charter](../own_gpu_charter.md), [finish plan](../product_finish_plan.md), [index](../INDEX.md) line 111, [review prompt](../vision_review_prompt.md).
- **What is wrong:** "parity with the unsourced $150" is not what the model gives. **Parity (1.02x) is at $1,330; at the $150 case ($480) the output is 2.74x.** The charter and finish plan say parity, the index says "bar met", and the workload map says conditional win. A reader cannot tell which is the claim.
- **Fix:** one sentence, used everywhere: cost advantage against assumed all-in chip cost, with the worst corner and V-05 applied.

### V-10 The count checks cannot fail on a wrong rule, and "independent" overstates the energy match
- **Severity:** MAJOR. **Claim:** simulator. **Location:** [`m1_check.py`](../../hw/gpu/m1/m1_check.py) lines 11 to 28; [`m2_model.py`](../../hw/gpu/m2/m2_model.py) lines 11 to 24; [M2 result](../../hw/gpu/M2_result.md); [index](../INDEX.md) line 96.
- **What is wrong:** M1's note admits this. **M2's does not:** `step_ops` copies the simulator instruction by instruction, so M2-a is a typo check. M2-b differs only by the omitted mesh cycles (4,603 against 4,735). Rules that both share are invisible, for example one weight read per batch regardless of batch size, no operand buffer energy, and no scale-computation energy. "Energy is consistent across two independent builds" is too strong: both multiply nearly the same bytes by the same 0.55 pJ/bit. M2-d could hardly fail, and it does not validate energy. "Validated against the simulator" on the index line overclaims.
- **Independent checks proposed:** (1) count MACs and tensor bytes from the PyTorch module with hooks, with no knowledge of the program; (2) replay an address trace through a cache and bank model to count actual SRAM accesses, including batch reuse; (3) compare one tile's RTL activity with the counters at M3, which is the only check that tests the rules against hardware; (4) a mutation test showing what each check catches.

### V-11 All large-model numbers use 4-bit weights with no quality evidence
- **Severity:** MAJOR. **Claim:** energy, cost, simulator. **Location:** `w_bits()` in the model; [`gpu_sim.rs`](../../hw/gpu/sim/gpu_sim.rs) (`int8` is the only integer path).
- **What is wrong:** the simulator has no INT4 path. Step 10 warns only about weights "below 4-bit", as though 4-bit were known safe.
- **Evidence (SIMULATED, patched simulator, M1 small transformer, original evaluation windows, 1,008 predicted positions, W8A8, change in nats per character against 1.7296):**

| weight bits | matrices only | with embeddings too |
|---|---|---|
| 8 | -0.0005 | +0.0003 |
| 6 | +0.0008 | +0.0013 |
| 5 | -0.0003 | +0.0049 |
| 4 | +0.0049 | **+0.0111** |
| 3 | +0.0628 | +0.1054 |

  4-bit with embeddings misses the 0.01 bar narrowly. A briefly trained character model near 1.73 nats is probably forgiving, so this is weak evidence either way.
- **Partial reassurance (MODELLED):** at 8-bit weights the ratios barely move (2.90x central, 1.77x worst, energy 12.2x and 5.7x), though the system grows from 630 to 958 chips.
- **Fix:** add a loss-at-4-bit row to M4, for INT8 and INT4, as a stated bar. Add 8-bit figures beside every 4-bit claim.

### V-12 "INT8" in the simulator is narrower than the notes say
- **Severity:** MAJOR. **Claim:** simulator. **Location:** `gather` line 113 to 116, `attn` and `attnc` lines 79 to 99, `mm` lines 52 to 57.
- **What is wrong:** the ISA says activations are stored in 2 bytes and embeddings in 1, and bytes are charged that way. But the values stay FP32 throughout: embeddings are **not quantised**, the key-value cache is not reduced to 16 bits, and attention scores and softmax run at full FP32 while being charged the integer MAC price. Each row's scale is computed live from its maximum, a step with no energy, cycles or hardware. Only tile weights get a capacity check, so the cache can overflow a tile silently. These are not stated limits in the M1 notes.
- **Effect:** embeddings at 8 bits change little (+0.0008 nats, table above). The 16-bit cache and integer attention are untested.
- **Fix:** add a strict mode in which every stored value passes through its stated width. Run M4-c in that mode.

### V-13 The 352x training-compute ratio uses a baseline that is not at equal accuracy
- **Severity:** MAJOR. **Claim:** row K. **Location:** [step 17](../../new_start/step17_k2_result.md); [`k2_strong_baselines.py`](../../new_start/experiments/k2/k2_strong_baselines.py) lines 154, 203.
- **What is wrong:** the 4.84 J network figure adds two full learning-rate runs and ends at 88.2%, below a plain network. The bar's condition, "both at least 85%", ignores that L is then at 88.85% and the network at another accuracy. No tuning energy is charged to L, although step 16 admits L was tuned earlier on the full training set.
- **Evidence (MEASURED accuracy, COUNTED energy; plain network, 3 seeds, per-epoch test accuracy used only for this measurement, so slightly favourable to the network):** the network passes L's 88.9% at epochs 9, 8 and 6, which is 1.07 to 1.61 J at 0.179 J per epoch, or **about 80x to 120x** against L x28 (13.8 mJ). It reaches 85% at epoch 2 (0.36 J, 26x). It ends at 89.6% to 90.0% after 15 epochs, above L. The ratio is linear in the assumed 1.5 pJ and 0.03 pJ.
- **What survives:** a large counted compute advantage, passing the 20x bar, with L's x28 being genuinely conservative. Quote about 100x at equal accuracy, not 352x or 5,096x.

### V-14 Cost assumes 10x the tokens per system at equal utilisation
- **Severity:** MAJOR. **Claim:** cost. **Location:** model line 73; step 12.
- **What is wrong:** both machines hold the same 1,024 caches at 50% utilisation, and ours is credited with 492,000 tokens/s against 50,000. The system costs about 4.3x the GPU cluster at $480 ($302k against $70k), so the cost result rests on actually selling the extra throughput. If demand is 30 to 50 tokens/s per session and sessions keep their cache, utilisation falls to about 5% and the advantage collapses by about 10x. Faster completion frees caches sooner only if requests really finish and leave.
- **Fix:** model a request arrival rate with cache occupancy for both machines.

### V-15 One laptop run does not show the model's GPU energy is a floor
- **Severity:** MAJOR. **Claim:** energy. **Location:** [step 12](../../new_start/step12_close_i_j_final.md); [workload map](../gpu_workload_map.md).
- **What is wrong:** the 1.375 J per token is real (43.2 W, consistent with 31.4 tokens/s). But it comes from a GDDR laptop GPU in an unoptimised Python loop at batch 1, and step 8 itself says the loop is the limit. Compared with an HBM batch-1,024 model, the 2.4x says nothing about a data-centre GPU. It is used as support for closing row J.
- **Fix:** remove "floor confirmed". Measure an optimised engine, then a data-centre GPU.

### V-16 SRAM energy: the source now exists, but the use goes beyond it
- **Severity:** MAJOR. **Claim:** energy. **Location:** [step 6](../../new_start/step6_sram_energy_result.md); [`step6_sram_bank_energy_model.rs`](../../new_start/experiments/step6_sram_bank_energy_model.rs).
- **In the project's favour:** [an IEEE SSCS listing](https://sscs.ieee.org/tag/dual-rail-dr/) confirms the title: a 3 nm 563-kbit, 35.5 Mbit/mm2 dual-rail SRAM with 3.89 pJ/access and 27.5 microwatts/Mbit in a low-leakage mode. That is about 225 mm2 per GB and about 0.22 W/GB, so 420 mm2 per GB and 1.6 W/GB look conservative on that node. I read the listing only, not the paper.
- **Problems:** (a) the anchor is a 3 nm mobile macro while cost and density are N5; (b) access width and test conditions remain unknown, and everything per-bit depends on that assumed 64; (c) the design points do not match the chip's other assumptions: 128 KB banks at 256 bits give 32 x 32 = **1,024 bytes/cycle per 4 MB tile against the 2,000 assumed**, and at the 32-bit width behind the 0.55 figure only 128 bytes/cycle, below the 184 needed for 368 4-bit MACs; (d) the 0.077 pJ point implies 64 multipliers per bank, 2,048 per tile, against 368; (e) the note says the 45 nm check was fitted to the 1 MB point, yet it prints 2.04 against 1.56; (f) the figure is applied unchanged to key-value cache reads, which were not the case modelled, and step 5 charges no SRAM writes.
- **Fix:** read the paper. Choose one bank design and use its energy, bandwidth and MAC count throughout.

### V-17 The GPU baseline is a 2022-class part compared with a chip that does not exist yet
- **Severity:** MAJOR. **Claim:** all. **Location:** model line 34.
- **What is wrong:** every comparison uses an H100-class GPU (80 GB, 3.35 TB/s). A chip from this project could not ship for years, and current parts have more memory and bandwidth. No test applies a newer GPU, and I did not source figures for one, so the size of this effect is **unclear**. HBM cost and capacity are what drive the GPU count, so it could matter.
- **Fix:** add a sourced current-generation GPU column and a projected one.

### V-18 The vendor cross-check does not support the latency model
- **Severity:** MINOR. **Claim:** speed. **Location:** `m2_model.py` lines 66 to 69; [step 4](../../new_start/step4_close_i_j_result.md).
- **What is wrong:** configurations are not comparable: vendor quantisation, overheads and context are unknown; the machine is a 16-bit wafer system, not our chip; the tile figures derive from the same vendor's specifications or an assumption. Weights count 3 feed-forward matrices (`* 1.5`) but `step_ops` runs only 2, which understates MACs and reads. The ratios drift from 1.33 to 0.77 across a 5.8x size change, so the scaling is off. The 1.8 factor is a one-parameter fit to two launch-era figures, then applied to a different machine. Reproduced: 2,799 and 750 tokens/s. The note's "informational" label is right; "the right order" is as far as it goes.

### V-19 The single-chip correction is valid but incomplete
- **Severity:** MINOR. **Claim:** speed. **Location:** model lines 67 to 69.
- **Verified:** reverting it reproduces 122 and 159 microseconds and 3.88 and 1.44 mJ. For the 1T case, the full output at the settings of steps 7 to 15 is **identical**, so earlier 1T results are unaffected, as stated.
- **Remaining:** the boundary term uses `LINK_S` = 1 microsecond while the chip link is 0.5, so 11 microseconds of the 92.7 (before x1.8) are double the stated link time. There is a jump at `cpl` = 1 to 2, and no boundary term at all when `cpl > 1` (about 3% at 1T). The larger issue, a whole chip of compute per layer, is in V-01.

### V-20 "The code caps accuracy" is not established
- **Severity:** MINOR. **Claim:** row K. **Location:** [step 20](../../new_start/step20_k5_result.md); charter.
- **What is wrong:** accuracy still rises with head width (90.02%, 90.31%, 90.60%), and 90.92% was measured earlier. The statement that a limit lies near 90% to 91% is extrapolation from small trained heads, and the figures quoted vary between notes. "Linear readouts stop near 88.9%" is supported. Retiring the work is a fair decision, but the reason should read "no route found", not "capped".

### V-21 The encoder is not "fitted without labels"
- **Severity:** MINOR. **Claim:** row K. **Location:** [`k1_data_efficiency.py`](../../new_start/experiments/k1/k1_data_efficiency.py) line 24 (`np.isin(ytr, (0, 1))`); step 16 and 17 notes.
- **What is wrong:** labels select the two classes. The cost is small and no test data is touched. But in the "unlabelled" and few-label claims, the 12,000 images imply about 12,000 labels at fitting time, or at least class selection, that are not counted at N = 100.
- **Leakage check:** encoder from training data only; validation splits used for early stopping in K1, K2 and K5; K3 and K4 prototypes from training data. **No test leakage found in these scripts.** Whether L's settings were chosen on test data in earlier months is **unclear**.

### V-22 M2 note: the batch-1 energy description is wrong
- **Severity:** MINOR. **Claim:** energy. **Location:** [M2 result](../../hw/gpu/M2_result.md) line 22.
- **What is wrong:** "the weights dominate (3.2 mJ of 3.3)". Weights are 435 MB x 4.4 pJ/byte = **1.92 mJ**; the key-value cache is 268 MB = **1.18 mJ**. 3.2 mJ is the whole dynamic energy. The same applies to the claim that the gap is explained only by model size.

### V-23 INT8 sample size and the loss metric
- **Severity:** MINOR. **Claim:** simulator. **Location:** [M1 fix result](../../hw/gpu/M1_fix_result.md).
- **Checked:** no leakage: calibration and evaluation windows do not overlap, and all come from the test split, not the training text. W8A8 needs no calibrated scale because it computes scales live (V-12).
- **What is wrong:** 1,024 positions from 16 correlated windows, one tiny model. "As good as fp32 for the quantity a model is trained and judged on" generalises too far. A mean loss hides large changes on rare positions, and my rerun gave 12 disagreements, not 13 (98.83%), confirming that near-tie noise. Moving to loss is reasonable, and it was openly declared for new work only.
- **Fix:** add a real pretrained model (M4 plans this), more windows, a paired confidence interval and a tail measure.

### V-24 Reproducibility from a clean checkout
- **Severity:** MINOR. **Claim:** all.
- **Result:** M1 and M2 ran after edits. CNN 86.0% here against the note's 86.8% to 86.9% (platform difference, seed fixed); loss 1.7296 identical; M2 counts, 4,603 and 4,735 cycles, 3.26 and 1.41 mJ identical. Row K: codes rebuilt from scratch give L 88.90% (seeds 88.77 to 89.06), against 88.85%.
- **Problems:** `/tmp` paths in six scripts, breaking native Windows; a fixed container scratch path in `k1_data_efficiency.py` line 14; `M1_result.md` has **no simulator commands**, and the `decode` argument appears only in a source comment; no requirements file or pinned versions; `mnist.npz` is required but not mentioned in setup; two `.pyc` files are tracked; the step 5 log predates the current code (the header says 64 to 1,024, the code 8 to 1,024, and price rows differ); several logs depend on unrecorded command lines; dead code at `m2_model.py` line 59.
- **Fix:** one script per milestone, data paths from the environment, a pinned requirements file, and each log headed by its exact command.

### V-25 Vault and rule problems
- **Severity:** NIT. **Location:** see below.
- `CLAUDE.md` names an old working branch, and its label list omits MODELLED. `COUNTED` is used in row K notes but is not an allowed label.
- **Rule break:** AI model identifiers appear in [`M4_plan.md`](../../hw/gpu/M4_plan.md) lines 8 and 13 and others, [`product_finish_plan.md`](../product_finish_plan.md) line 22, and `m2_model.py` line 65. I do not repeat them here.
- The charter's M4 (import a small ONNX model) differs from the M4 plan without a recorded decision. The charter's M2 cites step 6 and the plan cites step 5. The charter's "next action" is out of date.

## Claims against evidence

| claim | verdict |
|---|---|
| Energy 5x to 13x | **Not as stated.** Roughly 8x to 12x central with one correction; worst corner 2x to 5x |
| Speed 7x to 20x | **Withdraw** |
| 1B at 21 to 36 microseconds | **Not validated**; about 1.2 ms as implemented (V-01) |
| Cost | **Unsupported either way.** Original bar fails; about 0.8x to 2.7x depending on unsourced inputs |
| Simulator functional match | **Survives**, within V-12's limits |
| Counters equal analytic | **True, but no evidence about hardware** |
| Energy within 20% of the earlier model | **True, not independent** |
| Row K compute | **Survives at about 100x counted**, on two small tasks |
| Few labels mostly a readout effect | **Plausible**; K3 reported fairly; not rerun by me |
| Language cascade dropped | **Stands** |

## What I could not verify

- Real SRAM energy, leakage, MAC energy, area and clock on any node; there is no RTL or hardware.
- GPU decode power, GPU overhead and third-party cost figures, including the $3,320. I did not reopen the cited sites, apart from the SRAM listing.
- The SRAM paper's full text, and whether $150, 0.1 defects per cm2 or 85% yield are realistic.
- Rows K2 to K5 in full: I reran L and a plain network on clothing only. MNIST was not run (`mnist.npz` not available) and baselines were not rerun.
- M1 fix end to end: I ran the loss on the original windows only, not `m1_fix.py`. Steps 1 to 4, the older L Cortex and L Deep results in `hw/results/`, and the cascade logs were read in part, not rerun.
- Vault lint: the lint script was not available here.

Related: [Reviews index](README.md), [Review test files](vision_01_tests/README.md), [Finish plan](../product_finish_plan.md), [Own GPU charter](../own_gpu_charter.md), [M2 result](../../hw/gpu/M2_result.md), [Step 15 packaged cost](../../new_start/step15_packaged_cost_result.md)
