# SPARK journal

One entry per step, newest at the bottom. Each entry: what was asked, what was done, the result (with its label),
and where the files are. Earlier history (9-13 Oct) is summarised in `docs/PROJECT_MEMORY.md` section 3 and in
`git log`.

## 2026-10-14

- **User's real-model chat run** (MEASURED, Qwen2.5-1.5B-Instruct, `--chat`): code 1.69 / 1.70 / 1.72, prose
  1.04 / 1.04 / 1.04 (prompt lookup / tables / both). Recorded in `hw/results/token_lookup_real.md`.
- **Video** the user shared (Instagram reel about a founder asking why pay for a website when AI costs $20):
  watched the frames; the audio could not be transcribed in the container; the user pasted the Tamil-English
  transcript. Point: AI writes code but does not understand the business (UX, SEO, security, indexing, rate
  limiting). Conclusion given: these are judgement limits, not hardware limits; SPARK does not fix them.
- **User rejected the helper direction** ("6% is of no use, go for something big, brain as a chip, brain
  principles only, provable in 6-8 months"). Redesign to SPARK Cortex. `docs/cortex_redesign.md`.
- **First proof** (SIMULATED): random-wiring lookup neurons, then learned features + count memory.
  `hw/results/cortex_proof.md`. Digits in stages 95.6 vs network 19.5; exact merge; few-shot loses.
- **Month 1** (user: "close the accuracy gap"): retina centre-surround, concept cells, sleep with dreams,
  resonator cochlea, 8 loudness levels for sound, Speech Commands added. Results in
  `hw/results/cortex_month1.md`. Best brain part within 1.6 points of the network on all three, keeps it in stages.
- User asked not to use the C: drive: clarified that cloud work does not touch their PC; gave D: drive commands.
- **Month 2 started** (user: "shrink the memory and close the problems"). Findings in
  `hw/results/cortex_month2_log.md`. Paused before the dream-source test (`m2h.py`).
- User asked whether everything is saved: committed all scripts and logs (`hw/brain/experiments/`), the running
  month-2 log, and created this journal, `docs/PROJECT_MEMORY.md` and `CLAUDE.md` so nothing is forgotten.
- User asked which second brain to use: chose this GitHub repo opened as an Obsidian vault (I can write it directly,
  it keeps full history, and Obsidian reads it). Added home page `README.md`, indexes for docs, results, hardware
  and prompts, `hw/brain/README.md`, Related links, and the Obsidian vault config.
- User said "continue": ran test h (dream sources, fast table as the only decision maker). Results in
  `hw/results/cortex_month2_log.md`: memory down 70-160x; count dreams match month 1 on sound (71.1 vs 71.8) but lose
  4 points on digits and 9 on clothing.
- User going to sleep, asked for non-stop work until the evening of 15 Oct. Set an every-2-hours safety check-in
  (routine `trig_01UmL6GjCFHNfqdNTvVqZPZi`, India time, delete after 20:00 IST on 15 Oct). Overnight plan: finish
  month 2 (sleep variants, v3 suite with memory budget, few-shot, merge), then month 3 (integer bit-exact model, RTL).
- Overnight tests i-l (month 2 log): a full night of all-class dreams helps images (concept 8x3-bit: digits 95.3,
  clothing 84.2); chip-honest metaplastic 8-bit rate memory (45 KB) within ~1 pt of exact counts (digits 93.1,
  clothing 78.3), image total 73 KB fits Tang Nano block RAM; low-bit on-chip concept cells failed. New code:
  `hw/brain/rate_memory.py` (RateMemory, ConceptRates).
- Overnight (cont.): tests m-q in the month-2 log. Chosen small design: 5-bit fast table + 10-bit synaptic-scaling
  counters, the table makes every decision (one rule). Images 84 KB (fits Tang Nano block RAM). v3 suite on images:
  stages digits 94.1 / clothing 78.9, merge 95.8 / 82.7, few-shot still behind the network.
- **Month 3 started early:** integer reference model `hw/brain/cortex_int.py` (one pass per example, integers only)
  gives digits 95.0 / clothing 79.2 / sound 62-68 after 5 stages. **RTL `hw/rtl/cortex/cortex_core.v` is bit-exact
  with it: 0 mismatches over 5,058 compared lines in two configurations** (`run_check_cortex.py`).
- Open: the night helps images but hurts sound; testing a self-regulated night (stop when dreams keep surprising).
- **Self-regulated night** (ends after a block of 256 dreams with >2 surprises) gives one sleep rule for all tasks:
  digits 94.6, clothing 78.7, sound 69.7 after 5 stages (integer model).
- **Month 2 closed:** `hw/results/cortex_month2.md`. Memory 137x smaller for images (84 KB), 66x for sound; one rule;
  few-shot still behind; accuracy 2.6-7.6 points under month 1 in stages.
- **Board design:** `hw/board/cortex_board_top.v` (UART protocol, CLEAR command added to the core), bit-exact over UART
  with the integer model (0 mismatches, 101 commands). Yosys: 46/46 block RAMs, ~12.5k LUT4, 0 multipliers.
- **Bitstream built** (open-source flow, `hw/pnr_cortex/`): 46/46 BSRAM, 11,223 LUT4 (54%), 2,264 FF, 0 multipliers,
  68.6 MHz max at a 27 MHz clock, no hold violations. Fixes on the way: single-port list buffer (dual-port cells could
  not be placed), all block-RAM inputs re-registered on the falling edge (1,732 hold violations gone). Core and board
  checks re-run after each change: 0 mismatches. Host script `hw/board/cortex_host.py` (dry run matches the chip
  model exactly; 300 per class -> 91.2% on 10 digits after 5 stages).
- **Split dreams** (per class, counts kept per on/off pattern of its 2-3 most 50/50 bits; float sim): clothing 79.7 ->
  82.6 (x4 memory), digits 94.5 -> 95.6 (x8). Does not fit block RAM; route for a bigger version is the board's PSRAM.
- Seed spread (3 seeds, integer model, 5 stages): digits 94.4-94.8, clothing 77.7-78.7, sound 69.0-70.0.
- Energy estimate (`hw/results/cortex_energy_estimate.md`, ESTIMATED, 45 nm op energies): 9.4 nJ per decision vs 696 nJ
  for an 8-bit network (~74x); ~0.8 uJ vs ~166 uJ per learned example including sleep (~200x).
- **Live demo** `hw/board/cortex_demo.py` (draw with the mouse, teach, ask, sleep, test old digits; board or emulator).
  Headless check: preload 0-7 (93%), new class 8 from 10 examples in 0.1 s, then 73.5% on test 8s and 90.0% on old + new.
- Few-shot with detectors learned from a broad unlabeled set: no change (digits 37/54/83), so the detectors' data is not
  the limit. Testing wider pooling next.
- Wider pooling for few-shot: no fix (1-5 shots still behind; 20 shots digits 85.5 vs network 81.2).
- **Prior art** (`docs/prior_art_cortex.md`): HDC accelerators (Clo-HDnn, ImageHD, C-FSCIL), Loihi 2 continual learning,
  replay methods. "First chip that keeps learning" and "never forgets / merges by adding" are NOT claimable.
- **Measured against HDC** (`hw/results/cortex_vs_hdc.md`): after 5 stages chip 94.6 / 78.3 / 69.4 vs best HDC 92.4 /
  78.2 / 63.5, with less memory and ~1,000x fewer additions per example.
- Split dreams on sound (float): 68.2 -> 70.3 (x4 memory).
- 10 stages of one class each: chip 93.5 / 78.7 / 70.5 vs network 10.1 / 14.0 / 9.8. Month-3 summary written:
  `hw/results/cortex_month3.md`.
- **Sensory encoder on the chip**: `hw/rtl/cortex/cortex_encoder.v` bit-exact with `Features.encode` (0 mismatching
  images, digits and clothing), integrated in the board top (commands `54` detectors, `49` raw image), board bit-exact
  over UART (115 commands). Full design placed and routed: 88% LUT4, 46/46 BSRAM, 0 multipliers, 66.2 MHz. Host
  `--onchip-encode` option added.
- **Memory transfer on the chip**: core op 7 (read/write memory words, counts, known classes), board commands 52/57/4E/4D,
  bit-exact over UART (131 commands, 333 reply bytes, 0 mismatches); core check re-run (0 mismatches). PC programs:
  `merge()` and `night()` in `cortex_host.py`, demo `hw/board/cortex_transfer.py`: one board learns 0-4 (saved) then 5-9
  (saved), merged on the PC and loaded: 78.9% before sleep, 91.4% on all ten digits after one night (emulator).
- ASIC (SKY130) synthesis: 63 SRAM macros (~17.9 mm2) + ~0.84 mm2 logic = ~18.8 mm2; pre-layout timing/power not
  meaningful (unbuffered high fanout). `hw/results/cortex_asic_estimate.md`.
- Second sensory layer (V2): no gain (clothing 83.4 vs 84.7 all at once) - rejected.
- **Limit found: new condition of known classes** (rotated digits): chip forgets the old condition (95 -> 45%), like a
  network (-> 27%). Fix in float sim: frozen copy of yesterday's dream counts -> 86.1% upright, 95.9% rotated (clothing
  75.4 / 80.3). Needs 2x dream memory. `hw/results/cortex_new_condition.md`.
- Context memory added to the integer chip model (`context=True`): rotated-digits test upright 44.8 -> 85.3 (clothing
  25.1 -> 73.4), rotated kept. RTL not updated (needs 2x dream memory).
- **ASIC build bit-exact with the SKY130 SRAM macro models** (`run_check_cortex.py --asic --small`: 0 mismatches,
  two configurations, halving exercised).
- Empty-class dream guard (chip and model): dreaming a known class with no examples returns an empty dream instead
  of redrawing forever; core re-checked (0 mismatches); board check gains that edge case; bitstreams rebuilding
  (115,200 and an optional 921,600-baud variant).
- Claims sheet `docs/cortex_claims_sheet.md`. Project memory section 4 rewritten for the current chip design.
- Sequence memory (lookup core) across text domains: keeps ~32% (TB=11) / ~60% (TB=13) of the code benefit after
  80 KB of prose (`hw/brain/experiments/month3/seq_forgetting.md`); month 6 needs capacity or context memory.
- **Few-shot narrowed with spread (population) codes** (3x3 OR of features before matching, float sim): digits 40.5 /
  61.3 / 86.6 vs network 39.1 / 67.4 / 81.2 (1 / 5 / 20 per class); clothing 42.8 / 53.3 / 70.2 vs 43.7 / 62.9 / 73.7.
- Dendritic conjunction bits (pairs of features per cell hashed into 8,192 extra bits): worse (clothing 82.9 vs 84.7,
  digits in stages 90.3 vs 94.1) - rejected.
- Month 4 board plan (`docs/month4_board_plan.md`) and `hw/board/cortex_bench.py` (power/speed phases for a USB meter).
- Optional 921,600-baud bitstream: dropped. Every variant overflowed the FPGA in place and route (106-107% LUTs) while
  the standard build fits at 93%; the design sits at the edge. Not needed: batched dreams (below) remove the link
  bottleneck.
- **Found and fixed a host/model mismatch**: the model counts night blocks of 256 over the chip's whole life, the host
  counted per night; on clothing (nights end early) the board would have drifted from the model. Host now counts like
  the model; new check `hw/board/check_host_schedule.py` (digits and clothing: identical state).
- **Dream batches** (board command 45: up to 256 dreams per message, reply = surprises): ~250x fewer USB round trips,
  identical results; board check bit-exact including a full 256 batch; host uses it for day dreams and nights.
- 03:00 IST: few-shot fusion test (episodic recall + table vote, integer shift): +1 to +3 at 20 examples and on
  clothing at 5 (56.4), but the 5-example gap to the network remains; not adopted
  ([note](../hw/brain/experiments/month3/fewshot_fusion.md)).
- OpenROAD estimate flow ran placement, clock tree and timing repair (design area 19.1 mm2, 62% utilization; setup
  WNS -3.19 ns at 20 ns before routing); stopped on a report-command error after that. Resumed from the saved
  database with `hw/asic/cortex/resume.tcl` for global routing and the reports.

- **SKY130 layout estimate done** (placement, clock tree, global routing; resumed with `resume.tcl`): 19.4 mm2 of
  cells and macros on a 31 mm2 die, setup -2.96 ns at 20 ns (~43 MHz), hold met, clock skew 3.4 ns. Power 355 mW for
  the logic at a default 10% activity (SRAM not counted) - ~13 uJ per decision, far above the 9.4 nJ operation-count
  estimate: the overhead is clock tree, 20k encoder flip-flops and no clock gating. Recorded as a contradiction in
  `hw/results/cortex_asic_estimate.md`; the claims sheet now says the 74x is per operation needed. ESTIMATED.
- **On-chip detector learning works in simulation**: a streaming rule (one update per patch in arrival order, re-seed
  dead detectors) on one pass over the first day's images gives digits 93.9 / clothing 79.2 after 5 stages vs 95.0 /
  79.2 with PC detectors (3 passes: 94.4 / 79.3). SIMULATED, integer chip model
  ([note](../hw/brain/experiments/month3/onchip_detectors.md)).
- **On-chip detector learning in RTL**: hardware rule `hw/brain/detector_learn.py` (seed windows only seed; reseed is
  a command, from a ring of the last 32 windows) gives digits 94.5 / clothing 80.0 after 5 stages vs PC detectors
  95.0 / 79.2 (SIMULATED). `cortex_encoder.v` with `ENC_LEARN` is bit-exact with it (all counters + learned codes,
  0 mismatches, digits and clothing, reseed exercised); default build unchanged and still passes. ASIC only.
- ASIC power diagnosis: power hardly changes with switching activity (338-364 mW for 1-10% input activity,
  propagated by OpenSTA): ~6 nJ per clock cycle goes to clocking 20,380 flip-flops (17,200 are encoder memories) and
  25,579 clock-type buffers. Fix is architectural (clock gating, encoder memories into SRAM, compact die); recorded in
  `hw/results/cortex_asic_estimate.md`. ESTIMATED.
- Clock gating for the ASIC build: `cortex_encoder.v` under `CORTEX_ASIC` gives each flip-flop memory (image,
  receptor map, code map, detector signs) its own gated clock (`cortex_cg`, sky130 `dlclkp` cell with `CG_SKY130`),
  running only in cycles that write it. FPGA build unchanged. `run_check_encoder.py --asic`: 0 mismatches (digits,
  clothing, 20 images each). Layout flow re-running on the gated netlist; the ungated run's logs are kept in
  `hw/asic/cortex/ungated/`.
- ASIC power, continued: the SRAM macros were 72% of the 366 mW (their library charges every clock edge, selected or
  not; my earlier note that they were not counted was wrong and is corrected). Gated every SRAM port clock by its
  bank select (`sram_array`, 126 gates) on top of the encoder gates; core still bit-exact with the macro models.
  Layout ~42 MHz; power 77 mW (10% activity) / 62 mW (1%), i.e. ~2-2.5 uJ per decision, mostly clock tree.
  ESTIMATED. Docs, claims sheet and report updated.
- FPGA bitstream with the dream-batch command (45): **does not fit yet**. 19,645 LUT4 (94%, +215 over the last
  build that fit, which itself legalised only after 330 s); nextpnr seeds 1 (stuck 1 h), 2 and 3 fail with "Unable to
  find legal placement". RTL is still bit-exact (board check re-run on the current RTL: 136 commands, 0 mismatches).
  Trying the SA placer and a higher HeAP density; fallback is to trim logic. The committed bitstream remains the
  previous one (no command 45); `cortex_host.py` must not use batches with it.
- Host safety fix: `cortex_host.py` sends dreams in batches (command 45) only with `--batch`; by default it sends
  one DREAM per message, so it works with the committed bitstream (dry run and schedule check: identical results).
- FPGA fit attempt: SA placer crashed, HeAP at higher density failed. Packed the encoder's code map 4 bits per word in
  the FPGA build (1,152 x 4 instead of 4,608 x 1 LUT-RAM bits; read-modify-write); encoder checks (FPGA, ASIC, learn)
  and the board check pass. Re-running place and route.
- **Bitstream rebuilt with dream batches**: with the packed code map the design fits: 18,522 LUT4 (89%), 46/46
  BSRAM, 363 LUT-RAMs, 0 multipliers, 69.8 MHz max at 27 MHz, placed in 253 s. Host batches dreams by default again
  (`--no-batch` for an older bitstream). Board check on this RTL: 136 commands, 0 mismatches. SIMULATED (place and
  route); not yet on the board.
- **Context memory in the RTL** (`CORTEX_CONTEXT` in `cortex_core.v`: frozen copy of the dream counters, FREEZE =
  MEM arg 3, `cmd_frozen` dreams from the copy). `run_check_cortex_ctx.py`: schedule == `CortexInt(context=True)`,
  RTL bit-exact (0 mismatches, 3 configurations, up to 48 frozen dreams); base core check still passes. ASIC cost:
  36 more SRAM macros. SIMULATED. FPGA unchanged.
- Check-script fix: the SRAM macro simulation models print a line per access; the core check scripts captured all
  of it in memory, and the context check with macros was killed (out of memory) after its first configuration
  (which had passed). `run_check_cortex.py` and `run_check_cortex_ctx.py` now filter the simulator output to its
  summary line. Re-running the macro version.
- Context-memory RTL with the SKY130 SRAM macro models: 0 mismatches in all three configurations (up to 48 frozen
  dreams); log `hw/asic/cortex/check_core_context_asic.log`. SIMULATED.
- ASIC clock tree: lighter settings (root clkbuf_8, clkbuf_2/4, 30 sinks per cluster): 47 mW at 10% / 33 mW at 1%
  activity (from 77 / 62), ~1.1-1.5 uJ per decision; setup unchanged (~42 MHz), hold -1.34 ns before routing.
  ESTIMATED; logs `hw/asic/cortex/cts_light/`.
- **Faster core (pipelined)**: the score loop takes one code bit per cycle (list read -> table read -> add, 4-cycle
  pipeline) and the dream generator prefetches dream-counter words into a 4-entry queue. Cycles per PREDICT 1,243 ->
  264, per DREAM 21,894 -> 7,109, per LEARN 3,469 -> 2,465 (same command stream). Bit-exact: core check (2
  configurations), context check (3), board check (136 commands), 0 mismatches. SIMULATED. Bitstream rebuild and
  SRAM-macro check running; until the new bitstream is committed, the committed one is from the previous core
  (same behaviour, slower).
- Pipelined core does **not fit the Tang Nano**: 21,011 LUT4 (101%), placement fails. Now a build option
  (`CORTEX_PIPE`, on in the ASIC build, off on the FPGA); the FPGA build is back to the previous loops. Checks: core
  and context, both variants, 0 mismatches; board check (FPGA variant) 0 mismatches; the committed bitstream stands.
  A first SRAM-macro run of the pipelined core showed mismatches in its second configuration while other checks were
  writing the same files in the same folder at the same time; re-running it alone.
- Pipelined core with the SKY130 SRAM macro models, run alone: 0 mismatches in both configurations
  (`hw/asic/cortex/check_core_asic_pipelined.log`). The earlier failure was the file collision. Lesson: never run two
  core checks in the same folder at once (they share cmds.hex / out_cortex.txt).
- Pipelined ASIC layout (lighter clock tree): 49 mW (10%) / 35 mW (1%), ~40 MHz, hold -0.83 ns before routing;
  **~0.18-0.26 uJ per decision** (264 cycles), from ~11 uJ at the start of the night. ESTIMATED; logs
  `hw/asic/cortex/pipe_light/`.
- 07:10 IST (user: keep working until evening). Energy per learned example from the layout: digits 45-62 uJ,
  clothing 27-38 uJ (~95% dreams); per decision 0.19-0.26 uJ. ESTIMATED
  ([note](../hw/brain/experiments/month4/energy_per_example_layout.md)).
- Dream budget: ndream 1500 with one night pass ("economy") vs the month-2 rule (6000, two passes), 3 seeds:
  digits 94.0 vs 94.6, clothing 77.7 vs 78.3, sound 68.6 vs 69.4, with 3-4x fewer dreams (~3x less learning
  energy). SIMULATED / ESTIMATED. Offered as a host-side mode, default unchanged
  ([note](../hw/brain/experiments/month4/dream_budget.md)).
- `cortex_host.py --economy` (1,500 dreams, one night pass); dry run matches the chip model exactly in both modes.
  Added as optional step 8 of the board plan.
- Few-shot: saccades (shifted copies in episodic memory) hurt everywhere - rejected; top-2 voting +1.5 / +3.3 at 5
  examples (digits 62.8, clothing 56.6), still behind the network (67.4 / 62.9). SIMULATED
  ([note](../hw/brain/experiments/month4/fewshot_saccades.md)).
- **Cochlea in RTL**: integer shift-add model `hw/brain/cochlea_int.py` (91% of pixels identical to the float
  cochlea on 50 clips, mean difference 0.7 / 255) and `hw/rtl/cortex/cortex_cochlea.v` (28 resonators, 1.35 M cycles
  per second of sound); bit-exact (`run_check_cochlea.py`, 0 mismatching clips). Sound accuracy with the integer
  cochlea: running. SIMULATED.
- Cochlea RTL bit-exact on 10 clips; sound accuracy with the integer cochlea, 3 seeds: 69.9 vs 69.4 float (the
  1-seed 67.9 was noise). User asked to "remove the noise and improve the results": from now on report seed means;
  next, a noise floor in the cochlea for sound ([note](../hw/brain/experiments/month4/cochlea_rtl.md)).
- **Noise floor in the cochlea** (user: "remove the noise and improve the results"): each resonator subtracts 4x the
  mean of its 4 quietest frames. Sound after 5 stages 69.6 -> **71.2** (5 seeds, better on 4 of 5); sweep of 8
  variants, all 3+ seeds. Adopted in `cochlea_int.py` and `cortex_cochlea.v` (bit-exact). SIMULATED
  ([note](../hw/brain/experiments/month4/noise_floor.md)).
- Lateral inhibition across resonators on top of the noise floor: 67.7 / 70.5 vs 72.0 (3 seeds) - rejected.
- General sensory encoder `hw/rtl/cortex/cortex_encoder_gen.v` (any number of channels and detectors, one channel at
  a time): bit-exact on 20 images (4 x 32, 46k cycles) and 20 sound pictures (10 x 64, 23,040-bit code, 162k cycles)
  (`check_encoder_gen.log`). Sound top `cortex_sound_top.v` (cochlea -> encoder -> core, NB 23,040) and a whole-chain
  check `hw/rtl/cortex/sound/run_check_sound_chain.py`: running. SIMULATED.
- **Whole sound chip bit-exact**: raw samples -> cochlea -> general encoder -> core (NB 23,040); 12 clips heard, two
  stages with dreams and a night, 4 decisions: 23,082 lines, 0 mismatches. SIMULATED
  ([results](../hw/results/cortex_sound_chip.md)).
- Retinal adaptation (thresholds follow the image's brightest pixel): clothing 78.4 -> 79.0 over 5 seeds (3 of 5
  better), digits unchanged - within noise, not adopted ([note](../hw/brain/experiments/month4/retina_adapt.md)).
- Few-shot replay (table practises dreams drawn from the few examples): mostly worse, below episodic recall -
  rejected ([note](../hw/brain/experiments/month4/fewshot_saccades.md)). Few-shot ideas tried today: saccades,
  top-m voting (small gain), replay; the 5-example gap remains.
- Sound chip size (SKY130, ESTIMATED): core memories 315 open SRAM macros (~90 mm^2, vs 63 for images); cochlea
  11.2 mm^2 and sound encoder 2.1 mm^2 with every buffer as flip-flops (upper bounds; a streaming cochlea would drop the
  sample buffer). `hw/asic/sound/`, [results](../hw/results/cortex_sound_chip.md).
- Container restart: lost the detailed-routing run (4th pass; violations 160k -> 96k -> 72k, not converging) and the
  streaming-cochlea checks. Routing not restarted - the floorplan needs rework first (recorded in the ASIC estimate).
- **Streaming cochlea** `cortex_cochlea_stream.v`: listens live (28 resonators per sample, ~29 cycles per sample),
  no sample buffer; bit-exact on 10 clips; 1.52 mm^2 vs 11.2 mm^2 for the buffered version (SKY130 synthesis,
  ESTIMATED). [results](../hw/results/cortex_sound_chip.md).
- Sound chip top switched to the streaming cochlea: whole chain from live samples bit-exact (23,082 lines,
  0 mismatches), half the cycles. SIMULATED.
- `docs/results_at_a_glance.md`: one page of headline results, costs and limits (labels, links), linked from the
  home page and the docs index.
- Floorplan rework launched (`hw/asic/cortex/floor2/run.sh`): wider channels (250 / 300 um) on a 7.5 x 6.2 mm die,
  then detailed routing capped at 10 passes. `flow.tcl` die and channel sizes now overridable (DW, DH, GX, CH).
- Sound with the chip cochlea + floor, all words at once: 71.9 vs 72.0 in 5 stages (3 seeds) - staged learning costs
  nothing on sound. SIMULATED.
- HDC on the new noise-floor sound codes (fairness check): 5 stages 65.5 (from 63.5), all at once 71.2; the chip
  71.2 / 71.9 - still ahead in stages by +5.7. SIMULATED.
- Three brightness receptor types for images: clothing 78.4 -> 79.1 (5 seeds, 4 of 5 better), digits 94.6 -> 94.3,
  +25% memory - ASIC option, not adopted on the FPGA ([note](../hw/brain/experiments/month4/retina_adapt.md)).
- **Full regression** `hw/run_all_checks.sh`: 14 bit-exact checks (core FPGA / pipelined / context x2, encoder x3,
  general encoder x2, cochlea x2, sound chip, board design, host schedule): **14 PASS, 0 failures**
  (`hw/check_summary.txt`). SIMULATED.
- `hw/board/preflight.py`: board-day preflight (Python, packages, data, bitstream, serial ports, ping); step 0 of
  the board plan.
- **Spoken words on today's Tang Nano bitstream**: sound pictures from the PC (integer cochlea + floor) learned by the
  image chip: 60.1 after 5 stages (3 seeds; full sound chip 71.2, network 15.9). `cortex_host.py --task sound`, dry run
  60.0% and exact. Board plan step 9. SIMULATED ([note](../hw/brain/experiments/month4/sound_on_board.md)).
- Second detailed-routing attempt (wider channels): 104k violations after pass 1, ~65k at 60% of pass 2 (better than
  the first floorplan, not converging); lost in another container restart. Routing parked; recorded in the ASIC
  estimate.
- Live sound demo `hw/board/cortex_sound_demo.py` (mic or wav; teach / ask / sleep / test). Headless: a new word
  from 10 / 30 / 60 clips of many speakers -> 15.5 / 24.7 / 44.0% on unseen clips; old words 61 -> 51-58%. Weak few-shot
  for sound; recorded honestly ([note](../hw/brain/experiments/month4/sound_on_board.md)). SIMULATED.
- User: "remove the noise that affects accuracy and quality". Sound: extra noise / silence gates after the floor are
  worse on clean clips (70.2-70.9 / 67.7-70.0 vs 72.0) - floor kept; noisy-clip robustness test running. Images:
  speckle removal (a bit needs >= 1 on-neighbour) clothing 78.4 -> 79.0, digits 94.4 -> 94.5 (5 seeds, uneven) -
  candidate. SIMULATED ([note](../hw/brain/experiments/month4/input_noise.md)).
- **Sound in noise** (trained clean, white noise added to test clips): no noise removal 69.9 / 56.2 / 44.0 / 32.1
  (clean / 20 / 10 / 5 dB) vs noise floor 72.0 / 63.9 / 54.0 / 46.6 (+7.7 to +14.5) - the floor is the chip's noise
  robustness; gates hurt. Stronger floors under noise running. SIMULATED.
- Stronger floors under noise (6x / 8x): worse at every SNR (5 dB: 40.8 / 34.1 vs 46.6) - the 4x floor stays.
- Smoothing after the floor (time or frequency, 1-2-1): -1 clean, within +-2 under noise - rejected. Noise work
  closed: the 4x noise floor stays (best clean and in noise).
- **Learning in noise** (training clips clean or noisy at random, 1/4 clean): clean 67.0 (-5.0), 20 / 10 / 5 dB
  68.7 / 64.0 / 58.0 (+4.8 / +10.0 / +11.4); mean of the four conditions 59.1 -> 64.4. Half-clean mix running. SIMULATED.
- Learning in noise, half the clips clean: clean 68.9, noisy 67.0 / 62.2 / 54.6 (mean 63.2) - a smooth dial between
  clean accuracy and robustness. Noise work summarised in [input noise](../hw/brain/experiments/month4/input_noise.md).
- Images in salt-and-pepper noise (trained clean): digits 94.6 / 94.1 / 93.4 (clean / 2% / 5%) - already robust;
  speckle removal clothing +1.3 / +1.3 / +2.1, digits neutral. Candidate for an encoder build option. SIMULATED.
- Speckle removal built as an option: `Features(support=1)` and `SUP` in `cortex_encoder_gen.v` (second pass over the
  receptor map); bit-exact on 20 images and 6 sound pictures; added to `run_all_checks.sh`. Off by default.
- Regression after the speckle option (model `feature_layer.py` + general encoder changed): 15 checks, 0 failures.
- Speckle removal on sound pictures: clean 72.0 -> 70.9, 10 dB 54.0 -> 54.3 (3 seeds) - not for sound; image-only option.
- 10 one-class stages with 3 seeds: 93.0 / 78.7 / 71.2 (single run was 93.5 / 78.7 / 70.5; sound now with the chip
  cochlea + floor). Claims sheet, glance page, memory, report updated. SIMULATED.
- All at once with several seeds: digits 96.9 (3 seeds), clothing 82.9 (6 example orders, range 82.2-83.7; the
  month-2 single run 83.7 was the top of that range), sound 71.9. Headline docs now quote the means
  (`hw/brain/experiments/month4/allatonce_seeds.log`). SIMULATED.
- Merge of two chips (0-4 + 5-9, one night), 3 seeds: 93.3 / 81.4 / 64.3 (single run was 93.0 / 82.3 / 62.6; sound
  now with the chip cochlea + floor). SIMULATED (`hw/brain/experiments/month4/merge_seeds.log`).
- 3 brightness receptors + speckle removal together: clothing 77.7, digits 94.0 (3 seeds) - worse than either alone;
  rejected as a combination. SIMULATED.
- Full regression with the SKY130 SRAM-model runs (`run_all_checks.sh --asic`): 17 checks, see `hw/check_summary.txt`.
- `hw/board/board_day.py`: runs board-plan steps 0-5 (+9 with --sound) in order, one report file to send back; tested
  with --dry-run-only (emulator matches the chip model exactly).
- New-word rehearsal (more daydreams per taught clip): inconsistent (best 44% with 30 clips but old words fall to
  49%) - no reliable gain, not adopted. SIMULATED.

### 15 Oct 2026, afternoon - why the merge loses on sound; hand-over instead

- Asked: keep working (improve results). Done: three ways to move knowledge between chips, exact integer model,
  3 seeds. Note: [merge vs hand-over](../hw/brain/experiments/month4/merge_variants.md).
- Longer night after a merge: the self-ending night stops after 256 dreams; a full night gives sound 60.4 (vs 64.3),
  clothing 81.6 (vs 81.4). Rejected. SIMULATED.
- Merge by rebuilding the table from dreams only: 88.5 / 73.8 / 50.4. Failure, rejected. SIMULATED.
- **Hand-over** (A's memory loaded into B, B learns 5-9 itself): 95.6 / 82.7 / 71.6 vs merge 93.3 / 81.4 / 64.3
  (+2.3 / +1.3 / +7.3). SIMULATED. At board-demo size (300 per class, emulator, 1 seed) level: 90.9 vs 91.4.
- `hw/board/cortex_transfer.py --handover` added (dry-run tested). Merge stays the default; month-5 plan runs both.
- Project memory: detailed routing marked parked (the plan still said running).

### 15 Oct 2026, evening - board set aside; work on the failures that matter

- Asked: leave real-board testing; work on the necessary failures with new ideas. Priority set: few-shot, sound
  accuracy, detailed routing (sound chip size handled by running sound on the image chip).
- Sound memory sweep: half the memory costs ~3 points (68.2-68.9 vs 71.9), a quarter 7-10. SIMULATED.
  [sound chip](../hw/results/cortex_sound_chip.md).
- Few-shot rarity weighting: worse everywhere (digits 5-shot 62.8 -> 53.8). Rejected. SIMULATED.
  [few-shot note](../hw/brain/experiments/month4/fewshot_saccades.md).
- Running: few-shot after shipping (chip knows 0-4, then 1/5/20 examples of 5-9) vs a network fine-tuned the same way.

- Sound onset channels (cochlear-nucleus onset cells): 71.4-71.9 vs 71.9; equal-memory swap 69.7. Rejected.
  SIMULATED. [noise floor note](../hw/brain/experiments/month4/noise_floor.md).
- Routing diagnosis: global routing shows almost no congestion (0.00% overflowing cells) but the first detailed pass
  leaves ~100k violations, so the cause is a setup fault, not too many wires. One-pass run with the violation report
  started (`hw/asic/cortex/diag/`).

- **Word alignment for sound (new):** shift each sound picture so the word's start (first frame at 3/4 of the loudest
  frame's loudness) lands at a fixed frame; integer compares and an address offset. All at once, 3 seeds: 71.9 ->
  78.3 / **79.7** / 78.3 (lead 2 / 4 / threshold 1/2). SIMULATED. Confirmation with 5 seeds and 5 stages running
  (`hw/brain/experiments/month4/sound_align.py`, `sound_align_confirm.py`).

### 15 Oct 2026, 20:00 IST - end of the working window

- Overnight check-in routine deleted as asked. Work continues while the user is active (board testing set aside).
- Day's wins (all SIMULATED): **word alignment for sound 71.9 -> 79.8 all at once, 81.1 in 5 stages (5 seeds, lead 4)**;
  hand-over beats merge (+7.3 on sound); noise floor and learning in noise; speckle option for images.
- Day's failures: merge-night variants, table rebuild, rarity-weighted few-shot, onset channels, rehearsal for new
  words, smaller sound memory costs ~3 points per halving. Detailed routing still open (one-pass diagnosis running).
- Few-shot after shipping, first row (digits, 1 example per new class): chip learns old 99.0 but new only 6.5; a
  network fine-tuned on the same examples gets new 43.9 but old falls to 82.7. A new failure to fix: one weak new
  example cannot outvote a strongly trained old class. SIMULATED; k = 5 / 20 running.

### 15 Oct 2026, night - decision: two partial redesigns

- Asked: proceed with the two partial redesigns. (1) **Hippocampus unit**: a small episodic store beside the table so
  a new class learned from a few examples is not outvoted (research:
  [new class from few examples](research_fewshot_class_incremental.md); fixes tested in
  `hw/brain/experiments/month4/fewshot_fixes.py`). (2) **Physical floorplan**: logic in its own block beside the
  SRAM array, keep-outs at the macro pins, to make detailed routing converge. The core logic and its bit-exact
  checks stay; both come in as build options / new flow scripts. Full redesign rejected (the problems are local).

- **Redesign 1 done**: IMPRINT (novelty-gated prototype imprint from the dream counters, `CORTEX_IMPRINT`) + a short
  sleep (300 dreams per class). Bit-exact (run_check_cortex_imprint.py, plain and pipelined); regression 18/18 PASS.
  One example per new class: digits 54.1 -> 69.9, clothing 49.7 -> 64.0, words 45.2 -> 48.3 (old classes kept
  within 1-5 points). SIMULATED, 3 seeds. Rejected on the way: plain imprint, norm aligning, hippocampus gate,
  distinct-bits imprint, blurred imprint. [Note](../hw/brain/experiments/month4/fewshot_imprint.md).
- Words from 1-5 recordings remain weak (new words 12-22%). Network on aligned sound all at once 85.5 vs chip 82.5.
- Running: pattern separation (mushroom-body expansion layer), alignment in noise, network vs chip on few-shot words,
  floor3 layout (redesign 2).

- Pattern separation (mushroom-body expansion: 2x / 4x cells, each adding 8 random code bits, top 5% fire): worse on
  clothing (all at once 82.3 -> 81.1 / 81.4; 1-shot 64.0 -> 61.1 / 63.9) and digits (96.9 -> 95.9; 1-shot 69.9 ->
  67.1). Rejected (the expanded code is no sparser than the encoder's own 5-6%). SIMULATED, 3 seeds; speech run
  stopped. `hw/brain/experiments/month4/expand_kc.py`, `expand_kc.log`.
- Word alignment in noise: 80.3 / 72.4 / 58.9 / 47.1 (clean / 20 / 10 / 5 dB) vs 72.0 / 63.9 / 54.0 / 46.6.
- Few-shot words vs a network: the fine-tuned network forgets old words (1%), the network kept on all old data never
  learns the new ones (0-9%); the chip keeps both (all-10 accuracy 45.4 / 50.0 / 61.4 at 1 / 5 / 20 recordings).
- Test-time saccades (image + 4 one-pixel shifts, centre counted twice): clothing all at once 82.3 -> 84.2; in 5
  stages no gain (78.3). Digits running. SIMULATED, 3 seeds.

- **Test-time saccades** (image + 4 one-pixel shifts, centre counted twice, table scores added): digits 96.9 -> 97.9
  all at once (network 97.8), 94.6 -> 95.5 in 5 stages; clothing 82.3 -> 84.2 all at once, no gain in stages.
  5x decision work, no learning change. SIMULATED, 3 seeds. `image_saccades_test.py`.
- Sound tempo normalisation (stretch the word to 16 frames): 82.4 -> 69.9. Rejected. `sound_warp.py`.
- Started redesign 3 (two-layer senses V1 -> V2) in the model: `senses_v2.py`.

- Few-shot after shipping, clothing, chip (IMPRINT + sleep) vs network: 64.0 / 70.1 / 76.1 vs fine-tuned 38.3 / 37.2 /
  41.8 and all-old-data 44.6 / 56.0 / 71.5 (1 / 5 / 20 examples). Chip ahead everywhere. SIMULATED.
- Sound pitch normalisation (centre row shifted to a fixed row, +-2): 82.4 -> 79.4. Rejected.
- Redesign 2: floor3 stopped (global route stalled; an earlier note blamed hold violations, wrongly - corrected 16 Oct).

- Sound, listen more than once (views at word starts 5, 6, 6, 7, scores added via LOOK AGAIN): 82.4 -> 84.2 all at
  once, 80.3 -> 81.4 in 5 stages (network all at once 85.5). SIMULATED, 3 seeds.

### 15 Oct 2026, 10:20 PM IST - user asleep; overnight standing instruction

- Asked: keep going overnight; notify when the redesign finishes; when something fails, change the architecture or
  tune it and apply the necessary fixes without waiting for input. Hourly self check-in scheduled
  (trig_017qb4SEFn3pNLZpn3NYRUwD; delete after 10:00 AM IST on 16 Oct).
- Expected (IST): regression ~11:00 PM; redesign 3 first answer ~12:00 AM; floor2b detailed-routing trend ~1:00 AM;
  full routing (if it converges) ~4:00-6:00 AM.

- Redesign 3 first answer (clothing, 3 seeds, SIMULATED): detectors learned from all images instead of classes 0/1: no
  gain (82.7 vs 82.9 all at once). Second sensory layer V2 (64 / 128 detectors over 4x4 blocks of V1 winners): 83.6 /
  84.0 all at once (+0.7 / +1.1), 5 stages 78.7 / 78.2 (vs 78.1): small, costs +35% / +70% code bits. Digits running.
  Next: V2 variants (larger fields, stride 1, V2 replacing V1 channels) and V2 on words.

- Redesign 3, digits: V2 gives no gain (96.8 / 96.8 / 96.9 all at once; 94.4 / 94.6 / 94.1 in 5 stages for V1-all /
  +64 / +128). So V2 is +0.7 to +1.1 on clothing only, nothing on digits. Running: V2 on words and clothing variants
  (larger fields, stride 1, 192 detectors); a first words run was OOM-killed (speech maps 5x larger) and relaunched
  with smaller batches (`senses_v3.py`).

- Chip (IMPRINT + sleep) vs network after shipping, digits and words added: chip best on all-10 accuracy at 1 / 5 / 20
  examples on all three tasks (digits 69.9 / 81.0 / 87.5 vs fine-tuned 63.8 / 53.3 / 53.2; words 48.3 / 52.5 / 61.4
  vs 21.2 / 32.5 / 36.4). SIMULATED, 3 seeds. [note](../hw/brain/experiments/month4/fewshot_imprint.md).

### 16 Oct 2026, 12:25 AM IST - night work

- **Correction**: floor3 / floor2b did not fail on hold timing (17k hold violations are normal for this flow, floor2 had
  them too). They stalled in global routing with the heavy reference settings (100 iterations, adjustment 0.3).
  Restarted from floor2b's saved clock tree with `route4.tcl` (adjustment 0.1, 30 iterations, then detailed routing on
  met1-met5, or_seed 42, 30 passes): `floor2b/run2.sh`, log `floor2b/route.log`.
- **Redesign 3 verdict** (second sensory layer V2, `senses_v2.py`, `senses_v3.py`, SIMULATED, 3 seeds, all at once /
  5 stages): clothing 82.7 -> 83.6 / 84.0 (V2 64 / 128 detectors; 6x6 fields 83.7; stride 1 83.8), 5 stages 78.1 ->
  78.7 / 78.2; digits no gain (96.8); words 82.5 -> 80.4 / 82.0, 5 stages 80.9 / 80.9 (no gain). Not worth +35-70% code
  bits: **rejected for the chip** (model only, nothing in RTL). Detectors learned from all images: no gain either.
  The limit is the linear table, not the features.

- 1:20 AM IST: margin sweep (SIMULATED, 3 seeds, all at once; today's margin 8): clothing 82.3 -> 83.4 / 84.0 / 84.1 /
  84.4 at margin 32 / 48 / 64 / 96 (5 stages flat, 78.3-78.6); words flat (81-83 at every margin); digits 97.0 / 97.4 at
  32 / 48 (96.9 today). A wider margin is a free parameter (MARGIN = 8 in cortex_core.v); to adopt after the
  few-shot / sleep interplay is re-checked.
- floor2b routing (route4.tcl: light global-route settings) shows no progress after 1 hour of CPU at 0.9 GB: probably a
  loop in this old OpenROAD with the macro extension or the clock-layer setting. Bisect running in floor2c (old
  settings + guide file only).

- **Margin 8 -> 32 adopted** (`CortexInt` default, `cortex_core.v` MARGIN, `cortex_host.py` RULE; regression re-running,
  results below): all at once (3 seeds, SIMULATED) clothing 82.3 -> 83.4, digits 96.9 -> 97.0, words 82.4 -> 82.6;
  5 stages 78.3 -> 78.6 / 94.6 -> 94.9 / 80.3 -> 82.1; few-shot recipe (IMPRINT + sleep) within +-1 point of margin 8
  (digits 1 example 69.9 -> 69.0, 5 examples 81.0 -> 82.5; margin 96 hurts digits few-shot by 5, so not taken).
  Experiments before this entry used margin 8 (their logs say so by date); the board bitstream also needs a rebuild
  with MARGIN = 32. `margin_tune*.py`, `fewshot_margin.py`.

- 2:20 AM IST: container restart killed the regression (4 of 19 checks done with margin 32) and the floor2c routing run
  (pass 1 at 60%: 116k violations, heading for ~150k, no better than floor2's 103k: so no li1, the guide file and
  power halos did NOT fix routing). Restarted: the regression (margin 32), and a one-pass routing run that writes the
  violation report (`floor2c/diag.sh`, `floor2c/drc_summary.txt` when done) to see what kind of violations they are.

- 3:20 AM IST: second container restart at 3:19 (and the one at 2:20): both follow ~1 h with no tool activity (the
  hourly check-in fires into a fresh container). Background jobs die with it. Fix: two more check-ins
  (trig_01YK7BAneLSH4CcpSLGZ6Vzu at :09, trig_01E8ziMvX6pvuu1tUBa4QCwe at :29) so activity comes every 20 minutes;
  long jobs launched with setsid nohup must be re-checked at each wake and restarted if killed (uptime ~0). All three
  night scheduled tasks to be deleted after 10:00 AM IST on 16 Oct. Restarted: regression (margin 32) and the
  one-pass routing diagnostic (`floor2c/diag.sh`).

- 3:42 AM IST, **correction to the 3:20 entry**: the extra check-ins did not help. Each scheduled wake-up starts the
  session in a fresh container (`uptime` 0 min) and background jobs die with the old one; earlier jobs survived only
  while the user was connected. So long jobs now run only while a turn is kept open (blocking waits of up to 10 min),
  and the three night scheduled tasks are a safety net, not a keep-alive. Regression and the one-pass routing run
  restarted at 3:42 AM IST in the open turn.

- 4:10 AM IST: **regression with margin 32: 18 checks, 0 failures** (model, RTL, board, host emulator bit-exact;
  IMPRINT, LOOK AGAIN, aligned cochlea and sound chain included).
- **Final numbers with all adopted options** (margin 32, word alignment, LOOK AGAIN; exact integer chip model, 5 seeds,
  SIMULATED; `final_numbers.py`): all at once / 5 stages, single view -> with LOOK AGAIN:
  digits 97.0 -> **98.0** / 94.9 -> **95.8**; clothing 83.4 -> **84.8** / 78.4 -> 78.3; words 83.1 -> **84.7** / 82.0 -> **82.9**.
  (Earlier headline numbers, all at once: digits 96.9, clothing 82.9, words 71.9 -> now 98.0 / 84.8 / 84.7.)
  Network all at once: digits 97.8, clothing 87.3, words 85.5 on the aligned pictures.

- 4:57 AM IST: worker restart #3 (also kills jobs inside an open turn); full routing run (15 min in) and the speech half
  of the counter-range sweep killed; relaunched. Routing diagnostic result before that: floor2c after 2 passes 60,575
  violations (174,309 after pass 1): 90% met1 shorts / spacing among standard cells, 10% near macros, 4% on power
  nets - i.e. local std-cell congestion, converging much faster than floor2 (103k -> 96k -> 72k).
- Counter range (clothing, 3 seeds, SIMULATED; all at once / 5 stages): cmax 15 + margin 32 (today) 83.4 / 78.6; cmax 7
  + margin 16 78.7 / 77.5; cmax 31 + margin 32 84.3 / 79.2; cmax 31 + margin 64 84.5 / 79.1; cmax 63 + margin 64 85.1 /
  78.9. A 6-bit table (+20% table memory) buys about +0.9 / +0.6; 7-bit +1.7 / +0.3. Not adopted yet (memory vs gain);
  words and digits to follow (`cmax_tune.py`).

- 5:55 AM IST, redesign 2 diagnosis: the full detailed-routing run on floor2c went 174,309 -> 60,575 -> 54,168 violations
  (passes 1-3), slowing to ~10% per pass. Spatial analysis of the violation report: **88% of the met1 violations lie
  in 100 bins of 200 x 200 um (about 4 mm2 near the die centre), 1 of the 12 worst bins is inside a macro**: the
  standard cells are packed into a dense central blob (placement target density 0.45) while the rest of the 46 mm2 die
  is empty. Fix being tried (floor2d): global placement density 0.15 (cells spread ~3x wider), same grid, then global
  and detailed routing again. Counter range on words: 6-bit table 82.7 vs 82.6 (no gain; clothing +0.9): 5-bit stays.

- 6:25 AM IST: floor2d (placement density 0.15, same grid, clock tree + route4 global route) detailed-routing passes 1-2:
  145,484 -> 45,632 violations (floor2c: 174,309 -> 60,575; floor2: 103,658 -> 96k), hotspots now spread (top 10 bins
  hold 11% instead of 25%). Full multi-pass run started (`floor2d/full.sh`, log `route_full.log`).

- 7:40 AM IST, **research-driven experiments** (SIMULATED, 3 seeds; [research note](research_weak_spots.md)):
  - **Dreams with k prototypes per class** (clothing, 5 stages, margin 32; `dream_variants.py`): base 78.2; 2 prototypes
    81.8; **4 prototypes 82.4** (+4.3 of the 6.5 points lost to independent-bit dreams); stored-exemplar replay (10 / 20
    codes per class, half the dreams) 79.1 / 79.5; cue-and-complete 79.7 / 80.1. Co-occurrence is what the dreams were
    missing. Next: 3 / 8 prototypes, lower counter precision, digits and words.
  - **Clothing encoder** (`clothing_gap.py`, all at once / 5 stages): today 83.4 / 78.6; histogram-quantile thresholds
    83.4 / 77.4 (+0 bits), 3 quantile channels 82.8 / 77.9, coarse 5x5 centre-surround pair 83.5 / 78.5 (+50% bits): all
    rejected; the capacity gap is not in these knobs.
  - **New words, virtual examples** (shifted word starts 5,6,7; `fewshot_words_aug.py`), 1 recording per word, accuracy over
    all 10: 48.2 -> 49.5 single view, 49.2 -> 51.1 with LOOK AGAIN; new words 11.5 -> 15.0 / 22.2%. k = 2, 5 running.
  - Routing (floor2d): passes 5-8 = 2,675 / 2,227 / 1,943 violations; slowing.

- 8:00 AM IST, **Redesign 4: multi-prototype dreams** (the dream memory keeps K count-sets per class; `hw/brain/cortex_proto.py`,
  `experiments/month4/proto_dreams.py`, `dream_variants.py`; exact integer model, margin 32, 3 seeds, SIMULATED):
  - Floating-rate prototypes (upper bound): staged clothing 78.2 -> 81.8 (K=2) / 82.4 (K=4) / 83.9 (K=8); exemplar replay
    only 79.1-80.1.
  - **Integer version** (assignment by a shifted counter sum, dream = pick prototype by example count, then the chip's
    L-bit draws): 5 stages / all at once, clothing 78.7 / 83.3 (K=1) -> 80.3 / 82.6 (K=2) -> **81.5 / 83.5 (K=4)** -> **82.1 /
    83.9 (K=8)**; digits 94.7-94.8 vs 94.9 (no gain); words (float variant) 81.9 -> 82.8.
  - Cost: dream memory x K (K=4: 1.84 Mbit instead of 0.46 Mbit for images), narrower counters lose the gain (K=4 with
    8-bit counters 80.2, K=8 with 7-bit 81.7). Verdict: **an optional ASIC "high-fidelity dreams" setting for clothing-like
    data (+2.8 to +3.4 points staged), not a default**; no RTL (would need K prototype counter memories and a K-way
    overlap pass per learned example). Low-precision runs with plain rounding were wrong tests (rare bits lost).
  - Ensemble of two tables with different encoders: +1.4 / +0.6 for 2.5x memory: rejected.
  - Routing floor2d: passes 9-14 = 1,785 -> 945 -> 438 -> 364 -> 245 -> 178 -> 137 violations.

### 16 Oct 2026, 8:45 AM IST - redesign 2 finished: detailed routing 174,309 -> 25 violations

- floor2d (same grid, placement density 0.15, light global route, no li1, guide, 64 passes, ~2h20m): violations by pass
  145,484 / 45,632 / 38,217 / 9,240 / 4,027 / 2,675 / ... / 137 / ... / 28 / 25. The **25 remaining are all at 8 SRAM macro edges
  (met4 shorts, met5 spacing against the VDD stripe)**: a PDN stripe offset fix, then a re-route (~2.5 h), would take them to
  zero. Details and the five-run comparison: [ASIC estimate](../hw/results/cortex_asic_estimate.md). User notified.

### 16 Oct 2026, 10:30 AM IST - detailed routing: 1 violation

- floor2e (floor2d + met5 power stripes at pitch 84 um, offset 76.2 um so none lies within 12.9 um of a macro edge): 145,480 ->
  45,506 -> 37,849 -> 8,876 -> ... -> 453 -> ... -> 7 -> 4 -> **1 violation** after 40 passes (2h). The last one is a VDD-vs-signal
  short on met5 at one spot. The 25 macro-edge violations of floor2d were indeed the stripe clash. [ASIC estimate](../hw/results/cortex_asic_estimate.md).
- Night scheduled tasks deleted at 10:00 AM IST (trig_017qb4SEFn3pNLZpn3NYRUwD, trig_01YK7BAneLSH4CcpSLGZ6Vzu, trig_01E8ziMvX6pvuu1tUBa4QCwe).

### 16 Oct 2026 - regression re-run, views_more, rea-agents

- Full regression re-run on a fresh container: **18/18 checks PASS** (`hw/check_summary.txt`, bit-exact RTL vs integer model).
- `views_more.py` (diagonal, 2-pixel and row-shift extra views): no gain on fashion or speech. Recorded as a failure, not adopted.
- `rea-agents` (reverse-engineering helper the user asked for): the global install succeeded (173 packages); running it was blocked
  by the permission classifier, so it is installed but unused until the user adds a Bash rule for `rea`. Not part of the chip design.
- floor2f (router seed 43, retry to clear floor2e's last violation) restarted after a container restart; result to follow.

### 16 Oct 2026 - floor2f (router seed 43): 6 violations, no better

- Same global-route database as floor2e, router seed 43, 30 passes: 840 -> 523 -> 7 -> 6 violations at the end (SIMULATED/ESTIMATED layout
  result, no hardware). Of the 6: 3 met4 spacing, 2 met4 shorts, 1 met5 short; **all 6 at SRAM macro edges**, only 1 touches a power net.
  floor2e (seed default) stays the best at 1 violation. Seeds only move the last handful around the macros; a fix would need a larger
  keep-out around macro edges or a manual patch of the last shorts. Not pursued further now. Files: `hw/asic/cortex/floor2f/`.

### 16 Oct 2026 - redesign step: pool prototypes and broader detectors (small / no gain)

- Asked "will redesigning help"; answered yes in three places and started with multi-prototype dreams. A shared prototype pool (spawn on
  novelty) gives no saving over uniform K=2/K=4, so no RTL for it (clothing 5 stages: pool 20 -> 80.3-80.6, K=2 80.3, K=4 81.5; SIMULATED).
- New words: sound detectors fitted on words 0-4 instead of 0-1: new-word accuracy +5 (2 rec) / +3 (5 rec) points, -4 at 1 recording
  (SIMULATED, 3 seeds); near noise. Details: [the note](../hw/brain/experiments/month4/multiproto_dreams.md). Next idea, not started: a word-level embedding (match to known words).

### 16 Oct 2026 - Redesign 5 started, then paused by the user

- User paused the project ("stop for now"). Redesign 5 (sound layer with rectangular receptive fields, `hw/brain/sound_features.py`,
  `hw/brain/experiments/month4/sound_rf.py`, SIMULATED, 3 seeds, words, all at once / 5 stages): today's 5x5 reproduces 82.6 / 82.1;
  wider-in-time fields lose about 2 points (5x9 80.2 / 78.7, 3x9 80.0 / 78.7, 7x9 80.3 / 79.8, 5x9 stride 3 80.9 / 79.6). Failure, recorded.
  Not yet run: taller fields (9x5, 7x5), narrower (5x3), 128 detectors, wider pooling. No RTL change.
- State at pause: regression 18/18 PASS, floorplan at 1 violation (floor2e), board test still paused, `rea-agents` installed but not run
  (needs a Bash rule for `rea`).

### 18 Oct 2026 - event on 23 Oct: pitch material built

- User: there is an event on 23 Oct (pitch / project / paper presentation); get everything ready and keep redesigning and fixing failures. Deck hold lifted.
- Built `docs/SPARK_Cortex_pitch.pptx` (13 slides, native charts, speaker notes, labels on every number; generator `docs/SPARK_Cortex_pitch_build.js`),
  `docs/pitch_script_cortex.md`, `docs/pitch_qa_sheet.md`, `docs/paper_spark_cortex.md`. All numbers taken from the claims sheet and results page; failures stated on slide 10.
- Redesign 5 (rectangular sound receptive fields) continues in the background (`sound_rf2.log`).

### 18 Oct 2026 - exemplar memory for new words: no gain; the limit is the features

- Tested a hippocampus-like exemplar memory (k stored codes per new word, nearest neighbour by cosine overlap) against the table after IMPRINT: 5-way among
  new words 35.3 / 45.5 / 48.7 (exemplar) vs 37.7 / 45.0 / 47.4 (table) for 1 / 2 / 5 recordings; fusing them in the 10-way test is worse (SIMULATED).
  Failure recorded. Insight: among new words alone the chip is at 38-47% (chance 20%); the low "new word" figure is mostly confusion with known words. The
  gap is in the word features, which need speech from many words to learn; only 10 words are available here, so this needs a bigger speech set.
  Rectangular sound fields so far: 9x5 82.5 / 81.8 and 7x5 81.7 / 82.2 (all at once / 5 stages), equal to 5x5 (82.6 / 82.1) with 17% fewer code bits. Notes: [multiproto_dreams](../hw/brain/experiments/month4/multiproto_dreams.md).

### 18 Oct 2026 - what limits the scores: the readout, not the senses (corrects an earlier answer); slow table adopted in the model

- User: "can't we redesign and fix this", then "look what limits the staged training accuracy and redesign it".
- Ceiling test (floating-point networks on the chip's own code): linear readout 87.9% clothing, 98.3% digits vs chip 83.4 / 97.0. **The code is not the limit; the chip's online 5-bit readout is.**
  This corrects my chat answer that blamed the senses. Redesign 6, a slow table that follows the fast table (shift-add averaging): all at once clothing 83.4 -> 86.7, words 82.6 -> 85.3,
  digits 97.0 -> 97.6; in 5 stages no change; few-shot unchanged (SIMULATED, 3 seeds). Model only so far (`hw/brain/cortex_slow.py`); RTL not yet.
- Staged limit diagnosed: recency bias (last-stage classes absorb older classes, 7 -> 9 +21 points) from dream fidelity. Cheap fixes failed: more daydreams, margins, group-structured dreams (worse), dream-calibrated
  bias (+0.9), homeostatic bias (+0.8). Only prototypes help (K = 2 / 4). Details: [note](../hw/brain/experiments/month4/slow_table_and_staged_limits.md).
- Sound receptive-field sweep ended equal to 5x5 (9x5, 7x5, 5x3). `rea-agents` still blocked (needs a Bash rule for `rea`).

### 18-19 Oct 2026 - slow table in the RTL; stages and features, in that order

- User: "do as you wish", then "both on, which comes first": **stages first, then features**.
- Slow consolidating table (Redesign 6) is in the RTL as option `CORTEX_SLOW` (`cortex_core.v`, MEM args 5-7), 8-bit entries (5 + 3 fractional bits), round-to-nearest follow step. Bit-exact with `CortexSlow`
  (`run_check_cortex_slow.py`: plain, pipelined, SKY130 macro models; 0 mismatches; added to `run_all_checks.sh`). Precision sweep: FR 1 hurt staged learning (floor-shift bias), FR 3 + rounding does not.
- 5-seed final numbers (SIMULATED, LOOK AGAIN): clothing 87.9, words 87.2, digits 98.3 all at once (today 84.8 / 84.7 / 98.0). No change in stages. Level with a small MLP, not better (a CNN and a longer-trained MLP are ahead on clothing).
- Prototype dreams combined with the slow table: staged clothing 80.7 with K = 4 (4x dream memory), words +0.5 (note section 5). No RTL for prototypes yet.
- Details: [limits and slow table](../hw/brain/experiments/month4/slow_table_and_staged_limits.md).

### 19 Oct 2026 - finer-grid encoder option in the RTL

- Features step: image detectors at stride 1 with 4 x 4 pooling (same 4,608-bit code): clothing 88.0 all at once (5 seeds, slow table), staged 80.0 (+1.5); digits all at once 98.3 (+0.7) but staged 93.2 (-1.4);
  sound no gain. RTL option `ENC_S1` in `cortex_encoder.v`, bit-exact (`run_check_encoder.py --s1 [--asic]`, added to `run_all_checks.sh`). It is an option, not the default (staged digits worse).
  ASIC cost of the slow table (+9 mm2 estimated) and of ENC_S1 (2.3x encoder cycles) in [ASIC estimate](../hw/results/cortex_asic_estimate.md). Details: [note](../hw/brain/experiments/month4/slow_table_and_staged_limits.md).

### 19 Oct 2026 - regression 21/21 on the final design

- Full regression on the final RTL (slow table + ENC_S1 + all earlier options): **21/21 PASS** (`hw/check_summary.txt`). Pitch material (deck 14 slides, script, Q&A, short paper) refreshed with the slow-table numbers.
- Open: board day (`python hw\board\board_day.py --port COMx --data D:\cortex_data` on the user's PC; the Tang Nano bitstream has neither the slow table nor ENC_S1, which are ASIC options), prototype dreams in RTL (optional),
  learned word features (needs more speech data), `rea-agents` run (needs a Bash rule for `rea`).

### 19 Oct 2026 - where new spoken words fail

- User asked where new words fail and whether the architecture limits it. Breakdown (SIMULATED): 69% (k = 1) / 59% (k = 5) of new-word clips are called an old word; only 11-18% correct; old words 84% kept. A novelty gate (low old-class score -> new word) only trades old for new (total 48.0 -> 47.6 at best). Prototype dreams + slow table with the finer image grid (mnist, 5 stages): K = 0 93.7, K = 2 93.6 (no recovery of the staged-digits loss). The 30-word Speech Commands set cannot be downloaded here (network policy blocks download.tensorflow.org). Note: [multiproto_dreams](../hw/brain/experiments/month4/multiproto_dreams.md).

### 19 Oct 2026 (autonomous 2 h) - research and a round of fixes: none helps

- Research agent report (GPU few-shot / class-incremental tricks, integer analogues): [research note](research_fewshot_gpu.md). Tested: logit adjustment, cosine / mass alignment, max-over-shift matching, trace-rule (slowness) detectors, top-k cell competition, more sleep, neurogenesis (balanced) - all within noise or a trade of old for new classes.
  Details: [new-word sections 6-8](../hw/brain/experiments/month4/multiproto_dreams.md), [staged section 7](../hw/brain/experiments/month4/slow_table_and_staged_limits.md).

### 19 Oct 2026 - consolidation lag: slow table K = 5 lifts staged clothing 78.4 -> 81.6

- Idea (user: brain concepts, redesign): systems consolidation is slow. A much slower slow table (time constant 16,000 ticks, K = 5 instead of 3) averages the table across stages and damps the recency bias: 5 seeds, SIMULATED: clothing staged 78.4 -> 81.6 (all at once 83.4 -> 87.6), digits staged 94.9 -> 95.0 (all at once 97.0 -> 97.8), words staged 82.0 -> 82.6 (all at once 83.1 -> 86.4).
  RTL SLOWK = 5, bit-exact (plain, pipelined, macros). Few-shot unchanged. Details: [note section 9](../hw/brain/experiments/month4/slow_table_and_staged_limits.md). Deck, script, Q&A, paper to be refreshed.

### 19 Oct 2026 - regression 21/21 with SLOWK = 5; two-hour autonomous round summary

- Final regression on the K = 5 slow-table RTL: **21/21 PASS** (`hw/check_summary.txt`). Pitch deck, script, Q&A and paper carry the K = 5 numbers.
- Round summary (autonomous): the one change that worked was consolidation lag (slow table K = 5: staged clothing 78.4 -> 81.6, all-at-once and noise up). Not helping (all recorded): logit adjustment, cosine / mass alignment, max-over-shift matching, trace-rule detectors,
  neurogenesis (balanced), novelty gate, top-k cell competition, more sleep, two time constants, finer grid in stages. New words remain the open failure (needs more speech data).

### 20 Oct 2026 - more words found; table-score embedding lifts new words without lowering old words

- User: if words are the problem, try more words; do not trade off other qualities. 10 extra words (FSDD spoken digits, 3,000 clips) fetched from raw.githubusercontent.com (the one data host reachable). Fitting detectors on them does not help; more known classes in the table hurts;
  a GPU-style CNN baseline (backprop, diagnostic) beats the chip on new words (63.7 vs 51.5 at k = 5). Finer sound grid 3,3,1,1,4,4: new words 32.3 vs 18.5 (k = 5), old unchanged.
- Table-score embedding (describe a new word by its scores over 15 known words, integer L1 nearest prototype, 3 competitive prototypes per old word): all ten 49.3 / 55.8 / 61.5 vs 48.0 / 50.0 / 51.5 shipped (k = 1 / 2 / 5), old 86.3 / 84.9 / 83.8 vs 84.0 / 86.3 / 83.6: no trade-off. Details: [note section 11](../hw/brain/experiments/month4/multiproto_dreams.md).

### 20 Oct 2026 - embedding path built into the RTL

- `CORTEX_EMBED` option in `cortex_core.v` (ENROLL / WINNER / MATCH, prototype memory), reference `hw/brain/cortex_embed.py`, check `run_check_cortex_embed.py` (3 scenarios, 0 mismatches plain and pipelined), added to `run_all_checks.sh`. Hardware-exact accuracy with K = 3: all ten words 50.2 / 56.4 / 62.3, old words 86.8 / 85.1 / 83.6 (k = 1 / 2 / 5). Details: [note section 12](../hw/brain/experiments/month4/multiproto_dreams.md).

### 18-20 Oct 2026 - embedding path + finer sound grid (model), ASIC-macro embed check

- ASIC-macro and pipelined embed RTL checks: PASS, 0 mismatches (SIMULATED).
- Embedding path on finer sound-grid codes (3,3,1,1,4,4,64), hardware-exact rules, K=3 (k=1/2/5): all-ten 52.5/60.7/66.0, new 14.5/32.9/44.7, old 89.5/87.8/86.7 (SIMULATED). Previous grid: 50.2/56.4/62.3, 12.6/27.0/40.4, 86.8/85.1/83.6. Better on every number; K=1 trades old words for new (k=5 new 54.7, old 79.9).
- Still open: finer grid on all-at-once/staged/noise (sound_geom_full running), sound-encoder RTL for the grid, floor2g routing.
- Logs: hw/brain/experiments/month4/sound_geom_full.log.

### 21 Oct 2026 - finer sound grid adopted (model + encoder RTL)

- Full check of sound geometry 3,3,1,1,4,4,64 (3x3 windows, stride 1, 4x4 pool; same 23,040-bit code), 3 seeds, slow table K=5, SIMULATED. Shipped 5,5,2,2,2,2,64 -> finer: all-at-once 86.0 -> 88.9, 5 stages 82.65 -> 84.4, few-shot k=1/2/5 all-ten 48.0/50.0/51.5 -> 50.9/53.6/58.5, new 11.1/12.7/18.5 -> 16.8/24.1/32.3, old 84.0/86.3/83.6 -> 84.2/82.3/84.1. One number is lower (old words at k=2: 86.3 -> 82.3); every other number is better, so the grid is adopted with that noted. Noise robustness of the new grid is not yet checked.
- `cortex_encoder_gen.v` is now parameterised (WH, WW, LS, NS, LP, NC, MINON); defaults keep the shipped behaviour. New check `run_check_encoder_gen.py DATA sound3` is bit-exact (0 mismatches), the shipped `sound` check still passes. Cost: 537,883 cycles per picture against 161,923 (about 3.3x; ESTIMATED 5 ms per word at 100 MHz); active bits per picture 1,040 against 392.
- Full regression before this change: 23/23 PASS (`hw/check_summary.txt`). Re-run needed for 24.
- Embedding path on these codes: see previous entry (all-ten 52.5/60.7/66.0 at k=1/2/5).

### 21 Oct 2026 - floor2g routing: 0 violations

- Routing with signal/clock layers limited to met1-met4 on the floor2e database finished with 0 detail-routing violations (floor2e: 1, floor2f: 6). Files: `hw/asic/cortex/route5.tcl`, `floor2g/run.sh`, `floor2g/route_full.log`; details in `hw/results/cortex_asic_estimate.md`. SIMULATED (open-flow routed database), not sign-off.

### 18 Oct 2026 - bigger base vocabulary (35-word Speech Commands subset from the user)

- Data: `data/sc_subset` (35 words, 100 clips each, pushed by the user), converted by `hw/brain/experiments/month4/sc35_prep.py`; test script `sc35_embed.py`, log `sc35_embed.log`. New words: left, right, up, off, on; base = T table words (T = 5/10/15, fixed random order), speaker-disjoint test (about 20 clips per word, so every number has roughly +-5 points of noise), finer sound grid, 3 draws. SIMULATED.
- Learning all T+5 words together (reference): T=5 79.0, T=10 76.7, T=15 68.0 all-word accuracy (new words 70-78). This subset is harder than the earlier 10-word set (35-word pool, about 80 training clips per word), so the ceiling itself is lower.
- New-word accuracy, shipped IMPRINT path vs embedding path (k = 1 / 2 / 5 recordings):
  - T=5: shipped 34.3 / 34.0 / 47.2, embedding 32.3 / 32.7 / 44.2 (embedding no better with a 5-word base).
  - T=10: shipped 28.7 / 30.4 / 37.0, embedding 38.0 / 42.9 / 55.1.
  - T=15: shipped 17.8 / 21.1 / 33.3, embedding 24.4 / 39.3 / 51.2.
- Reading: the embedding path needs a base vocabulary of about 10 or more words to pay off, as predicted (+8 to +18 points on new words at k = 2 and 5), and the shipped path gets worse as more base words compete. One recording per new word is still weak (24-38%). Old-word accuracy with the embedding path stays 71-75% (shipped 66-82%), all-word accuracy at T=15, k=5: 65.7 vs 58.1.
- Not fixed: one-shot new words, and accuracy drops as the pool grows (68% all-at-once at T=15, so the readout, not only the new-word rule, is limiting).

### 19 Oct 2026 - where the 35-word limit sits (diagnostic)

- `hw/brain/experiments/month4/sc35_ceiling.py`, log `sc35_ceiling.log`. All 35 words learned together, 2,783 training clips (about 80 per word), 717 test clips from held-out speakers. SIMULATED.
- Chip table 70.1 %; float linear on the same sparse code 76.2 %; float MLP on the code 76.6 %; float CNN on the 28x28 cochlea picture 75.2 %.
- Reading: the sparse code is not the limit (the CNN on the raw picture is no better than a linear readout on the code). Float readouts beat the 5-bit table by about 6 points, so the table readout / learning rule is the part that can still be improved, and the data (about 80 clips per word) caps everything near 76 %. One recording per new word cannot be fixed by design.

### 19 Oct 2026 - finer sound grid in noise, readout sweeps

- Finer sound grid 3,3,1,1,4,4 in white noise (5 stages, slow table K=5, word alignment, 3 seeds, `noisy_slow_geom.py`, SIMULATED): clean / 20 / 10 / 5 dB = 84.4 / 77.5 / 67.7 / 57.0 against the shipped grid 82.7 / 75.2 / 64.4 / 52.3, so better at every noise level (+1.7 to +4.7 points). The finer grid is now checked on all-at-once, staged, few-shot and noise.
- 35-word set readout sweeps (`sc35_readout_sweep.log`, `sc35_epochs.log`): weight range, margin, dream count and sleep length give no gain (70.1 % -> at most 70.7 %); repeating the data 2-5 times gives 71.5-72.4 % (diagnostic, the chip keeps no data); float readouts reach about 76 %.

### 19 Oct 2026 - noisy dreams: script written, NOT yet run

- User asked for brain-principled fixes (no CNN, no matrices) after the laptop noise run (trained clean, SIMULATED: clean 79.3, 20 dB 68.3, 10 dB 54.5, 5 dB 44.2; the noise-trained stages had not finished). Proposed: noisy dreams, cascade synapses, twin-word specialist, multi-scale vote (all PROJECTED, untested).
- Wrote `hw/brain/experiments/month4/noisy_dreams_laptop.py`: the chip learns from clean clips only, night dreams get dropped and spurious bits (xorshift draws, integer only); five variants against a clean-dream baseline. **Untested**: the smoke test was interrupted, no result exists. Open before running: report old-word and new-word clean accuracy separately (pass condition: old words do not get worse) and add a half-noisy-night variant.

### 19 Oct 2026 - strict brain-principles rule and audit

- User: follow the principles of the brain strictly in every process (after asking whether the chip really learns like a brain; honest answer: brain-inspired, not brain-like in labels, host schedule, hand-made word alignment, offline detectors).
- Wrote [brain-principles audit](brain_principles_audit.md): a six-point test, every process checked, order of fixes (few-label self-labelling, onset-triggered words, internal sleep pressure and novelty, on-chip detector learning default, noisy dreams last). Added standing rule 11 to project memory. No experiment run; all fixes PROJECTED.

### 19 Oct 2026 - brain-strict digits: first results (self-labelling fails as built)

- Script `hw/brain/experiments/month4/brain_strict_digits.py`, logs `brain_strict_digits_fit.log` / `_chip.log` (MNIST, 2,000 examples per stage, 5 stages of 2 digits, 2,000 test images, 3 seeds, slow-table chip, SIMULATED). DET=fit is the shipped offline detector fit, DET=chip the one-pass on-chip rule.
- Accuracy fit / chip: shipped path (labels on every example, host-scheduled night) 93.5 / 94.1; same labels fed in chunks with one separate night call 94.0 / 94.3; **sleep pressure** (night only when surprise writes reach 3,000) 94.0 / 94.6, but it slept only once, at the end, so the threshold was too high and this does not yet test internal sleep.
- **On-chip detectors cost nothing here** (94.1 against 93.5), so the offline fit is not needed for digits.
- **Few labels with self-labelling FAILED**: 10 % labelled 65.2 / 63.1, 25 % labelled 73.5 / 78.3, against 94 with all labels. Pseudo-label precision only 64-71 %, so the chip's own mistakes poisoned its table. Next, running: pseudo-labels restricted to classes rewarded in the current context (`fewc`) with a stricter margin cut, and sleep thresholds 200 / 500 / 1,000.
- Also added `noisy_dream_chip.py` (noisy night dreams) and `brain_strict_sound.py` (causal onset trigger and noisy dreams on 20 words of the 35-word subset); a smoke test of the sound script was still running, no sound result yet.

### 19 Oct 2026 - brain-strict digits and Fashion: results so far (SIMULATED, 3 seeds, on-chip detectors, 2,000 examples per stage)

- Logs and json: `hw/brain/experiments/month4/brain_strict_digits_chip{,2,3,4,5}.log`, `brain_strict_fashion_chip.log`.
- **Sleep from inside (WIN on digits):** host-scheduled night 94.1; sleep when surprise writes reach 200 / 500 / 1,000 gives 94.1 (4 sleeps) / 94.7 (2) / 94.6 (1). Level or slightly better with fewer sleeps.
- **On-chip detectors (WIN on digits):** 94.1 against 93.5 for the offline fit.
- **Few labels, rewards first, pseudo-labels only among classes rewarded in this context ("fewc"), margin cut at percentile 50:** 25 % labels 93.8, 10 % 93.4, 5 % 88.4, 2 % 83.3, 1 % 75.8 (full labels 94.1). Without the context limit it failed (10 % 63-65, 25 % 73-78, precision 64-71 %).
- **Loosening the cut helps at low label counts:** 5 % labels, cut 50 / 10 / none = 88.4 / 90.8 / 91.4; 2 % labels with no cut: first seed 91.5 against 83.3 (cut 50); runs unfinished. Precision stays 96-99 %.
- **Rewards scattered through the stream FAILED to help ("mixc"):** 10 % 91.1, 5 % 91.4, 2 % 88.6, below rewards-first at 10 %.
- **Fashion-MNIST:** full labels 80.8; 10 % labels 78.9, 25 % 79.1 (gap about 2 points, not level).
- Bug found and fixed: the sound test used 20 words but the chip model defaults to 10 classes (heap corruption); `n_cls=20` now passed. Sound results (onset-triggered words, noisy dreams) still pending.
- Not yet clear wins: few labels at 5 % and below, Fashion. The architecture-change plan for the limits (unsupervised category layer, neighbour-conditioned dreams, temporal sound layer, context signal, pruning, cascade synapses) is the next step.

### 19 Oct 2026 - redesign tests: pruning, category layer, cascade synapses, Fashion checks (SIMULATED, chip detectors, 2,000 per stage, 3 seeds unless noted)

- **Synaptic pruning (WIN)** (`brain_strict_prune.py`, 2 seeds; memory saving ESTIMATED from the count of nonzero synapses, a sparse store also needs indices): zero slow-table synapses below a threshold after the last night. Digits 94.0 (40 % of synapses nonzero) -> 93.9 (30 %) -> 93.5 (19 %) -> 91.9 (12 %) -> 89.3 (7.5 %). Fashion 80.35 (54 %) -> 80.35 (30 %) -> 79.6 (21 %) -> 78.5 (16 %).
- **Unsupervised category layer with sparse naming FAILED** (`brain_strict_clusters.py`, small test, 1 seed): competitive categories with novelty recruitment and error-driven recruitment reach 53-66 % at 10 % labels and fill every category slot; homeostasis (win-count handicap) changed little (62.5 -> 65.8 at best); penalising missing expected bits made it worse (12-37 %). Not tuned further; the table-based self-labelling (fewc) is the working route.
- **Cascade synapses FAILED on Fashion** (`cortex_casc.py`, `brain_strict_casc.py`): staged 80.8 -> 80.6 / 80.1 / 80.3 and all-at-once 86.0 -> 85.3 / 84.5 / 84.1 for hidden levels 1 / 2 / 3, and they cost 3 extra bits per synapse. Not adopted. (Digits not run.)
- **Few labels on Fashion** (no confidence cut, context-limited): 10 / 5 / 2 % labelled = 78.3 / 78.4 / 78.1 against 80.8 with all labels, so the loss is about 2.5 points and does not grow as labels shrink to 2 %. Digits with no cut: 10 / 5 / 2 % = 93.1 / 91.3 / 90.7 against 94.1.
- **Sleep from inside on Fashion:** 79.3-79.7 at thresholds 200-4,000, equal to the chunked-feeding control (79.7) and 1.1 below the shipped path (80.8). The loss comes from feeding each stage in chunks (each chunk call replays the interleaved dreams again), not from the sleep trigger; digits were level or better (94.1-94.7 vs 94.1).
- Sound arm `peak` (shipped alignment, 20 words, 5 stages of 4): clean 68.5, 20 dB 62.2, 10 dB 47.3, 5 dB 33.3; first-stage words 77.5, last-stage words 50.6 (1 seed set of 3, `brain_strict_sound.log`). Onset-trigger and noisy-dream arms still running.

### 19 Oct 2026 - redesign tests, round 2: context, sound, final status (SIMULATED)

- **Context on its own (partly solved)** (`brain_strict_digits.py` arm `ctx`, 3 seeds): stages blended into one stream, no stage boundary, sleep from pressure, context = classes rewarded among the last 30 / 60 rewards. All-labelled control 94.6; 10 % labelled 92.7 / 93.1; 5 % labelled 91.8.
- **Dreams with lateral inhibition FAILED** (`cortex_wta.py`): staged clothing 80.8 -> 79.9 / 78.6 / 74.7, digits 94.1 -> 93.7 / 93.0 / 90.4 for at most 4 / 3 / 2 features per spot; all at once level.
- **Sound, 20 words, 414 test clips (about +-3 points):** shipped alignment clean 68.5, fixed-loudness onset 60.7 / 65.1 (800 / 1600), adaptive onset 57.4 / 62.4 (not better). With look-again at test: shipped 69.2, onset 1600 66.3 (near parity, first-stage words 4.7 lower). Noisy night dreams that drop bits: clean +0.3 to +2.0, 5 dB +2.4 to +2.6, first-stage words -2.2 (within noise, guard slips, not adopted); adding spurious bits hurt new words by 8.
- Final write-up: [brain-strict redesign tests](../hw/results/brain_strict_redesign.md). Audit status and project memory updated. Still open: novelty from inside, a temporal layer for twin words, neighbour-conditioned dreams (needs several times the dream memory), RTL for sleep pressure and self-labelling, clearly settling the onset trigger with a larger test set.

### 19 Oct 2026 - agreement-gated labels and novelty signal (SIMULATED, 3 seeds)

- Agreement gate (`fewa` in `brain_strict_digits.py`): digits 10 / 5 / 2 % labels 93.65 / 91.6 / 91.1, clothing 10 / 2 % 79.7 / 77.5; gap to full labels 0.5 (digits) and 1.1 (clothing) at 10 %.
- Novelty from inside (`brain_strict_novelty.py`): margin between the top two classes separates unseen from known digits, AUROC 0.88 (best score 0.84, score per active bit 0.85); 60 % of unseen flagged at the threshold that keeps 90 % of known.
- User asked what the chip is for if it fails at training too; answered in chat: the training claims that hold (learning in stages without forgetting, tiny memory, merging, few labels) and the ones that do not (one recording per new word, beating a CNN).

### 19 Oct 2026 - failure round: readout gap closed, second layer failed again, prototype dreams are a memory trade (SIMULATED, 3 seeds)

- **Readout gap (F4) closed** (`brain_strict_ceiling.py`, a float ridge readout on the chip's own code, diagnostic only): clothing 86.05 vs chip 85.97, digits 96.95 vs 96.98, all data at once. The counting readout matches a float linear readout; the remaining gap to a CNN is the code, not the readout.
- **Second sensory layer failed again** (`brain_strict_v2.py`, clothing): layer 1 + layer 2 staged 80.6 / all-at-once 85.65 against 80.8 / 86.0 for layer 1 alone; layer 2 alone 66.3 / 74.6.
- **Prototype dreams are a memory trade, not a free fix** (`brain_strict_proto.py`): K = 4 gives staged clothing 83.3 (from 80.8) and digits 93.9 (from 94.1) for about 4x the dream memory; pruning the dream counts to buy memory back loses the gain (clothing 80.0 at 1/16 pruning, 74.0 at 1/8, 69.9 at 1/4; K = 1 pruned 74.9). Digits pruned 1/16: K = 1 92.6, K = 4 92.9.

### 19 Oct 2026 - novelty recruitment FAILED; eye movements close the few-label gap on digits (SIMULATED, 2 seeds)

- **Novelty recruitment on the margin signal FAILED** (`brain_strict_novel.py`, blended stream, 1 % and 2 % labels): novelty cut at the 2nd / 5th / 10th percentile of recent rewarded margins gives 52.5 / 46.6 / 45.2 at 1 % labels and 58.2 / 55.2 at 2 % (2nd, 5th), against 62.0 without novelty (1 % labels, 1 seed). Cause: the margin flags about as many ambiguous known examples as unseen ones (60 % precision at the loose cut), so the anonymous slot is contaminated. Note: the json file was overwritten by parallel runs; the logs `brain_strict_novel_nov2.log` / `_nov5.log` hold the numbers.
- **Eye movements (`fews`, `brain_strict_digits.py`)**: labelled and pseudo-labelled examples are learned with their 4 one-pixel-shifted views, and an unlabelled example is pseudo-labelled only when all 5 views name the same class. Digits, 5 stages, 2 seeds: 2 % labels 93.9, 5 % labels 94.2 (own-label precision 99.5-99.7 %), against 90.7 / 91.3 without eye movements and 94.1 with every example labelled (no views). The fully labelled control with views, 1 % and 0.5 % labels, and Fashion-MNIST are running before this is called a win.

### 19 Oct 2026 - eye-movement controls, sound second layer, 35-word look-again (SIMULATED); container restarted

- **Eye movements (`fews`) are a digits result, not general.** Fully labelled control with views: digits 92.0 (below the 94.1 no-view baseline, so views alone hurt), clothing 78.4 (below 80.8). Digits with few labels and views: 2 % 93.9, 5 % 94.2, 1 % 91.1 (2 seeds), 0.5 % 80.3 (1 seed). Clothing with views: 10 % 78.4 (the same as its fully labelled control but below the 79.7 of the no-view agreement gate), 2 % 73.7. Reading: on digits the agreement-gated selection of confident, view-consistent examples beats learning from every example; on clothing it does not help.
- **Temporal second layer for sound did not help** (`brain_strict_sound.py` arm `v2`, 20 words): clean 69.2 (shipped single view 68.5), 20 / 10 / 5 dB 63.1 / 48.3 / 35.0 (62.2 / 47.3 / 33.3), first-stage words 75.8 (77.5), last-stage words 45.6 (50.6); within the +-3 noise, newest words lower. Not adopted.
- **35-word, 717-clip test:** shipped alignment with look-again clean 64.2, 20 / 10 / 5 dB 55.3 / 37.5 / 25.2, first / last stage words 71.2 / 44.9. The onset-trigger arm was killed by a container restart (the machine restarted at about 14:20; background jobs die on restarts) and was relaunched.
- Prototype-dream pruning on digits: K = 4 with 1/16 / 1/8 / 1/4 pruning 92.9 / 91.0 / 80.7 against 93.9 unpruned.

### 19 Oct 2026 - novelty from view agreement, few-shot words with shifted views started (SIMULATED)

- **Novelty signal improves with eye movements** (`brain_strict_novelty2.py`, digits, trained on 8 classes, 3 seeds, AUROC unseen vs known): single-view margin 0.882, mean margin over 5 views 0.910, mean margin plus view disagreement 0.912; share of unseen flagged at the threshold that keeps 90 % of known 72 % (was 60 %). Real but modest; recruitment on it not yet retested.
- Started `sc35_views.py`: new spoken words (k = 1 / 2 / 5 recordings, base T = 15) with each recording enrolled at three window starts (look again), against the single-view embedding path.

### 19 Oct 2026 - runs on the user's PC: few-shot words with views (no gain) and 35-word onset trigger (3 points lower) (SIMULATED)

- Run by the user on their PC (`sc35_views.py`, `brain_strict_sound.py`; their push to GitHub failed with a 403 so the numbers were read from their screenshots; the local logs are on their machine only).
- **Few-shot new words with time-shifted views (F9) FAILED to help**, base T = 15 words, 3 draws, single (shipped embedding path) vs views (3 window starts per recording, look-again at test): k = 1: all 62.5 vs 62.3, new 24.4 vs 24.1, old 75.0 vs 74.8; k = 2: all 65.0 vs 64.4, new 39.3 vs 40.9, old 73.4 vs 72.1; k = 5: all 65.7 vs 65.2, new 51.2 vs 50.8, old 70.5 vs 69.9. No gain beyond noise, old words slightly lower.
- **Word alignment on all 35 words (717 test clips, F1):** onset trigger 1600 with look-again clean 60.7, 20 / 10 / 5 dB 52.8 / 36.6 / 26.1, first / last stage words 68.6 / 42.6, against the shipped alignment with look-again 64.2, 55.3 / 37.5 / 25.2, 71.2 / 44.9. The causal trigger is about 3 points lower clean and 2.5 lower at 20 dB; equal only at 5 dB. With the larger test set the 20-word near-parity does not hold. The shipped rule stays.

### 19 Oct 2026 - agreement-gated learning with every label (run on the user's PC, SIMULATED, 3 seeds): a small win on digits only

- Arm `gate` in `brain_strict_digits.py`: every label present; an example is learned with its true label only if its 5 one-pixel-shifted views agree on one class (about 60 % of examples pass). `gate:1` = centre view only, `gate:v` = all 5 views.
- Digits: normal learning 94.1; views without gate 92.0; gate only 92.1 (92.85 / 92.85 / 90.65); **gate + views 94.9** (95.15 / 94.65 / 94.80, every seed above the best baseline seed 94.4). Clothing: normal 80.8; views without gate 78.4; gate only 77.9; gate + views 78.9 (79.2 / 78.9 / 78.7), i.e. no win.
- Reading: on digits the gate is what lets the views help (the combination beats each part alone); on clothing one-pixel shifts do not suit large shapes. The earlier few-label digits result (2 % labels 93.9) is the same mechanism.

### 19 Oct 2026 - view types for agreement-gated learning (run on the user's PC, SIMULATED, 3 seeds, gate + views, every label present)

- Clothing / digits (normal learning 80.8 / 94.1; 1-pixel shifts `s1` 78.9 / 94.9): 2-pixel shifts `s2` 77.9 / 92.8; diagonal 1-pixel `d` 77.3 / 93.4; scale 0.93 and 1.07 `sc` 78.5 / 94.0; `s1`+`s2` 76.7 / 91.5; `s1`+`sc` 78.0 / 94.1; `s1`+`d` 77.0 / 93.1.
- **No view type lifts clothing above its normal-learning 80.8** (best 78.9 and 78.5), so the clothing gap is not about the kind of view. On digits only the 1-pixel shifts give a clear win (94.9); larger shifts, diagonals and more views are worse (91.5-93.4), which points to the table being diluted by extra copies. The eye-movement gain is specific to digits.
- Next idea for clothing: stack the partial wins already known (stride-1 encoder `ENC_S1` +1.5 staged, prototype dreams +2.5 staged, slow table) instead of views.

### 19 Oct 2026 - F11: RTL hooks for the host-side logic (bit-exact, SIMULATED)

- `hw/rtl/cortex/cortex_core.v` build option `CORTEX_HOOKS`: `top_margin` (top score minus the runner-up among known classes, valid after PREDICT, saturated when one class is known) and `wr_count` (number of surprise-gated table writes, cleared by reset and CLEAR). With these the host can do self-labelling (confidence margin) and sleep from pressure (writes since the last sleep) with no other state in the core. No new arithmetic: a compare and an add.
- Check `hw/rtl/cortex/run_check_cortex_hooks.py` (+ `tb_cortex_core_hooks.v`, added to `hw/run_all_checks.sh`): 160 LEARN lines and 40 PREDICT lines on real digit codes, **0 mismatches** against the integer model (writes 41, margins 3 to 279). The default build (option off) gives identical predictions and update flags to the hooks build (200 lines compared). iverilog had to be installed in the container (`apt-get update` first).
- Not yet done: the full 24-check regression after this change (the other checks need data files that are not in the cloud scratchpad), and the sleep-pressure / self-labelling logic itself is still host software.

### 19 Oct 2026 (overnight, cloud) - stacking, detector count, parameter sweep: a memory-neutral staged-clothing fix (SIMULATED, 3 seeds unless noted)

- **Stacking** (`brain_strict_stack.py`; staged / all at once; memory): clothing shipped 80.8 / 86.0 (129 KB); prototype dreams 83.3 / 85.9 (298 KB); stride-1 encoder 81.5 / 87.3 (129 KB); both 82.55 / 87.3 (298 KB). Digits: shipped 94.1 / 97.0; prototype dreams 93.9 / 96.8; stride-1 93.5 / 97.6; both 94.2 / 97.7. The gains do not add up; the stride-1 encoder lifts all-at-once on both datasets, prototype dreams lift staged clothing only.
- **More detectors do not help** (clothing, shipped encoder, staged / all at once): 32 detectors per channel 80.8 / 86.0; 64: 82.0 / 85.9 (2x memory, 259 KB); 128: 80.7 / 85.9 (4x memory, 518 KB). With the stride-1 encoder 64 detectors: 81.1 / 88.0.
- **One-knob sweep** (`brain_strict_sweep.py`, clothing, 2 seeds, default 80.35 / 86.1 staged / all at once): fewer dreams per old class (1,500 / 3,000) 81.5, one night pass 81.5, update margin 128 82.3, cmax 7 / 31 81.3; more dreams worse (24,000: 78.5); slow-table shift K = 7 collapses (52.6); everything else within about 1 point.
- **Second sweep, margin x dreams x night** (3 seeds): shipped encoder, margin 256 + 1,500 dreams + 1 night pass **83.3 staged / 86.55 all at once** (default 80.8 / 86.0); margin 128 + 1,500 + 1: 82.9 / 86.6; margin 1,024 hurts (81.0 / 85.2). Stride-1 encoder, margin 256 + 1,500 + 1: **83.65 / 87.2** (default 81.5 / 87.3). Same memory as the shipped chip (129 KB), against 298 KB for prototype dreams at 83.3. Digits check running.

### 19 Oct 2026 (overnight, cloud) - the new chip settings also win on digits (SIMULATED, 3 seeds, staged / all at once)

- `brain_strict_sweep.py` GRID=2, digits, on-chip detectors, 2,000 per stage. Shipped settings (margin 32, 6,000 dreams per old class, 2 night passes): shipped encoder 94.1 / 97.0, stride-1 encoder 93.5 / 97.6. **Margin 256, 1,500 dreams, 1 night pass: shipped encoder 95.5 / 97.5, stride-1 encoder 95.1 / 98.05.** Other combinations: margin 128 95.1 / 97.4 (shipped encoder); margin 1,024 hurts the shipped encoder (92.5-94.0 staged) but suits the stride-1 encoder (95.7-95.95 staged, 97.9).
- Same on clothing (previous entry): 83.3 / 86.55 and 83.65 / 87.2 against 80.8 / 86.0 and 81.5 / 87.3. The change is the update margin (a core parameter, MARGIN) and the host's dream / night schedule; no extra memory. Not yet adopted as the default: spoken words are being checked first (`brain_strict_sound.py` with MARGIN / NDREAM / NIGHT env).

### 19 Oct 2026 (overnight, cloud) - F6 noise robustness: training on noisy copies raises every number (SIMULATED, 20 words, 3 seeds, ch = 50)

- `brain_strict_noise_gate.py`. Test clean / 20 / 10 / 5 dB; first-stage words; last-stage words. Clean clips only: 69.2 / 62.7 / 47.5 / 33.5; 77.1; 53.3. **Clean clips, then one noisy copy of every clip (SNR 20 / 10 / 5 dB at random): 73.3 / 73.3 / 65.6 / 56.4; 77.9; 65.1.** Gated (a noisy copy is learned only if its 3 window starts agree; 41 % kept): 72.6 / 68.4 / 57.9 / 48.9; 77.1; 70.1.
- Noisy-copy training raised clean speech (+4.1), every noise level (+10.6 / +18.1 / +22.9) and old words (+0.9); the earlier noise-training attempts lowered clean accuracy. The agreement gate lowers the noise gains because it drops the hard noisy copies. Caveat: this doubles the number of training examples; a control (the same clean clips a second time) is running to separate more data from noisy data. The noise is added to training clips by the simulator, standing for a chip that hears speech in varying noise during its day.

### 19 Oct 2026 (overnight, cloud) - ADOPTED: update margin 256, 1,500 dreams per old class, 1 night pass (SIMULATED, 3 seeds)

- Spoken words, 20 words, shipped settings -> new settings (`brain_strict_sound.py` with MARGIN / NDREAM / NIGHT env): clean 68.5 -> **73.35**, 20 / 10 / 5 dB 62.2 / 47.3 / 33.3 -> 65.7 / 51.5 / 39.5, first-stage words 77.5 -> 77.5, last-stage words 50.6 -> **57.1**. With the digits and clothing results above the new settings win on all three data types at no extra memory: digits staged 94.1 -> 95.5, clothing staged 80.8 -> 83.3, words clean +4.8.
- RTL: the update margin is already the core parameter `MARGIN`; `run_check_cortex_hooks.py --margin=256` passes bit-exact (200 lines, 0 mismatches, writes 87 against 41 at margin 32), and 0 mismatches at 32. Dream count and night passes are host schedule. Defaults in the repo are unchanged; the recommended setting is written in `docs/PROJECT_MEMORY.md` and `hw/results/brain_strict_redesign.md`.

### 20 Oct 2026 - few-shot new words improve a lot under the new settings; novelty recruitment fails again (SIMULATED)

- **F9** (`sc35_views.py` with MARGIN env, 35-word subset, base 15 words, new words left / right / up / off / on, 3 draws, k = 1 / 2 / 5 recordings; the table learns with the stated margin). New-word accuracy / old-word accuracy: margin 32 single view 24.4 / 39.3 / 51.2 and 75.0 / 73.4 / 70.5 (reproduces the PC run); **margin 256 single view 30.4 / 46.9 / 61.7 and 77.5 / 76.3 / 73.6**; margin 256 with three time-shifted views per recording and look-again at test **31.4 / 49.8 / 64.4** and 77.4 / 76.1 / 73.9. All-word accuracy at k = 1 / 2 / 5: 62.5 / 65.0 / 65.7 -> 66.0 / 69.6 / 71.6. One recording is still weak (about 31 %).
- **F7** (`brain_strict_novel.py`, blended stream, margin 256 / 1,500 dreams / 1 night, 2 seeds): with 2 % labels and no novelty rule 79 %; with novelty recruitment (2nd-percentile cut) 50-57 %. The recruitment rule still hurts.

### 20 Oct 2026 - stacking and second layer re-run under the new settings (margin 256, 1,500 dreams, 1 night; SIMULATED, 3 seeds, staged / all at once)

- Clothing: shipped encoder 83.3 / 86.55; prototype dreams 84.65 / 86.6 (2.3x dream memory); stride-1 encoder 83.65 / 87.2; both 83.8 / 87.5. Digits: 95.5 / 97.5; prototype dreams 95.7 / 97.3; stride-1 95.1 / 98.05; both 95.05 / 97.95. Under the new settings prototype dreams add only +1.3 on clothing staged and nothing on digits, so the settings capture almost all of the earlier prototype-dream gain at no memory cost; the stride-1 encoder is worth its all-at-once gain (+0.65 clothing, +0.55 digits) and nothing more.
- **F10 second sensory layer FAILED again** (clothing, new settings): layer 1 + layer 2 82.7 / 86.4 against 83.3 / 86.55 for layer 1 alone; layer 2 alone 70.2 / 72.1.

### 20 Oct 2026 - sweep around the new settings: a plateau (SIMULATED, 3 seeds, staged / all at once)

- `brain_strict_sweep.py` GRID=3, centre margin 256 / 1,500 dreams / 1 night. Clothing centre 83.3 / 86.55; every one-knob change stays within 83.8-80.7 staged (best: 1,000 dreams 83.5, margin 192 83.4, 2 daydreams 83.4; worst: slow-table shift K = 6 80.7, ch = 200 81.2); digits centre 95.5 / 97.5, every change within 93.7-95.7 (500 dreams 93.65 worst). No setting beats the centre by more than the noise (about +-0.5), so the staged result is at a plateau for these knobs; the remaining gap to all-at-once (clothing 86.55, digits 97.5) is not a settings problem.

### 20 Oct 2026 - F6 control done: the noise gains are real (SIMULATED, 20 words, 3 seeds, ch = 50)

- Control "the same clean clips a second time" (`brain_strict_noise_gate.py` arm `twice`): clean / 20 / 10 / 5 dB 71.7 / 64.5 / 52.2 / 36.8; first-stage words 75.3; last-stage words 60.2. Against clean-only (69.2 / 62.7 / 47.5 / 33.5; 77.1) and noisy copies (73.3 / 73.3 / 65.6 / 56.4; 77.9): more data alone explains +2.5 of the clean gain, but noisy copies are +8.8 / +13.4 / +19.6 points above the control at 20 / 10 / 5 dB, +1.6 on clean, and keep old words level (the control lowers them by 1.8). **F6 fixed.**

### 20 Oct 2026 - F7 active labelling FAILED; twin-word geometry first results (SIMULATED)

- **Active labelling** (`act:P` in `brain_strict_digits.py`, new settings, 3 seeds): a random seed of at most 40 labels, then labels requested for the chip's lowest-margin examples up to the budget, then agreement-gated pseudo-labels. Clothing 10 / 5 / 2 % labels 75.0 / 78.9 / 78.0 against random labels 79.1 / (n.a.) / 78.4; digits 92.75 / 93.8 / 91.9 against random 95.0 (5 %) / 94.7 (2 %) with `fews`. Hard examples are no more useful than random ones (10 % clothing is worse); the margin signal (AUROC 0.91 for unseen classes) does not translate into a better label set.
- **Twin words, 35 words, 717 test clips** (`geom:` arms in `brain_strict_sound.py`, shipped margin 32; twin = no/go, left/right, up/off, on/off, bed/bird, down/dog, three/tree, four/forward): shipped grid 3 x 3 window, pool 4 x 4: clean 63.9, twin words 62.3, other words 65.1; 3 x 5 window (wider in time): clean 63.7, twin 64.4, other 63.1. Two more shapes still running.

### 20 Oct 2026 - F11 energy: the new settings cut learning energy (ESTIMATED); pruning is a modest memory saving

- Dreams per learned example 45.6 -> 7.2 (6.3x fewer) with the new settings; the earlier layout-based 45-62 uJ per learned example (about 95 % dreams) scales to about 9-12.5 uJ. Pruning the slow table saves 8-15 % of chip memory (sparse store with indices); dream counts cannot be pruned. Details in the results note ("Memory and energy"). Not a layout re-run.

### 20 Oct 2026 - F10 multi-scale vote: small gains for 2-3x memory (SIMULATED, 3 seeds, new settings, staged / all at once)

- `brain_strict_ens.py`: chips with different encoders (base, stride-1 `s1`, a differently fitted base `base2`) learn the same data; their slow-table scores are added at test. Clothing: base 83.3 / 86.55, s1 83.65 / 87.2, base2 83.2 / 86.3; vote base + s1 83.9 / 87.55; vote of three 84.0 / 87.8. Digits: base 95.5 / 97.5, s1 95.1 / 98.05; vote base + s1 95.6 / 98.1; three 95.95 / 97.95. At most +0.7 staged and +1.3 all at once for 2-3x memory; the gap to a CNN is not closed. Consistent with the code, not the number of chips, being the limit.

### 20 Oct 2026 - F1 under the new margin: the causal onset trigger is near parity (SIMULATED, 20 words, 3 seeds, look-again)

- `brain_strict_sound.py` with MARGIN 256 / NDREAM 1,500 / NIGHT 1. Shipped alignment (loudest-frame rule) clean / 20 / 10 / 5 dB 73.4 / 64.7 / 52.9 / 39.0; first-stage words 78.8; last-stage words 55.9; twin words 72.0; other words 73.7. Causal onset trigger (threshold 1600): 72.5 / 66.9 / 52.8 / 37.8; 74.9; 62.8; 73.0; 72.4. Under the old margin the trigger was 2.9 points lower on clean speech; now 0.9 lower, 2.3 higher at 20 dB, twin words +1.0, last-stage words +6.9, first-stage words -3.9. 35-word confirmation running.

Related: [Project memory](PROJECT_MEMORY.md), [Home](../README.md)
