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
Related: [Project memory](PROJECT_MEMORY.md), [Home](../README.md)
