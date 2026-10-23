# L journal

One entry per step, newest at the bottom. Each entry: what was asked, what was done, the result (with its label),
and where the files are. Earlier history (9-13 Oct) is summarised in `docs/PROJECT_MEMORY.md` section 3 and in
`git log`.

## 2026-10-14

- **User's real-model chat run** (MEASURED, Qwen2.5-1.5B-Instruct, `--chat`): code 1.69 / 1.70 / 1.72, prose
  1.04 / 1.04 / 1.04 (prompt lookup / tables / both). Recorded in `hw/results/token_lookup_real.md`.
- **Video** the user shared (Instagram reel about a founder asking why pay for a website when AI costs $20):
  watched the frames; the audio could not be transcribed in the container; the user pasted the Tamil-English
  transcript. Point: AI writes code but does not understand the business (UX, SEO, security, indexing, rate
  limiting). Conclusion given: these are judgement limits, not hardware limits; L does not fix them.
- **User rejected the helper direction** ("6% is of no use, go for something big, brain as a chip, brain
  principles only, provable in 6-8 months"). Redesign to L Cortex. `docs/cortex_redesign.md`.
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

## 20 Oct 2026 (late) - Own learning rule (prioritised replay) FAILED; timing cells for sound help a little; geometry layer FAILED

**Asked:** proceed with Group A redesign and the training-method test; if no known method helps, create our own.

**Training rules (SIMULATED, margin 256, 1500 dreams, 1 night, 3 seeds, staged accuracy):** shipped rule: clothing 83.27 / digits 95.52. Graded surprise 83.7-83.9 / 93.4-94.7 (hurts digits). Synaptic budget ~83.1-83.4 (no effect). Night downscaling 82.9 clothing. **Our own rule, surprise-prioritised replay** (`prio:B`, dream classes drawn with weight 1 + the surprise writes they caused in the last block; xorshift + adds only): B=64 80.5 / 95.3, B=256 80.3 / 95.1, B=1024 79.8 / 95.2. **FAILED** - it takes replay away from stable classes, which then drift. Conclusion: the shipped margin + fewer dreams rule stays; no training-rule variant beat it. Code: `hw/brain/cortex_rules.py`, `hw/brain/experiments/month4/brain_strict_rules.py`, logs `prio_fashion.log`, `prio_mnist.log`.

**Sound, 20 words (SIMULATED, margin 256):** peak baseline clean 73.35, newest 57.1, twin 69.1. Timing cells (rise/fall vs previous time column, `tm:32`): clean 74.15, newest 61.3, twin 73.9 (+0.8 / +4.2 / +4.8) - a small real gain, still far from a clear win. `tm:16`: 74.07 / 61.7 / 74.4. Noise: 10 dB 53.4 vs 51.5. Geometry layer (`geom:3:3:1:1:4:2`): clean 58.2 - **FAILED**, much worse than peak. 35-word onset run only finished its look-ahead arm (68.3 clean); no matched peak arm, so F1 at 35 words is still **unconfirmed**.

**Status:** F8 partly improved (timing cells), F7/F10/F3 still open. Next: Module 2 (category formation in sleep, bounded 64-code buffer).


## 20 Oct 2026 (night) - Ceiling check (SIMULATED, clothing, float ridge readout on the same images)

Shipped code 86.35, shifted-stride code 87.4, both side by side 87.75, 64 detectors per channel 87.65. The chip's one-pass (non-staged) result is already 86.55, so a richer visual code can add at most about 1.2 points. The 3.2-point loss that remains is staged (83.27 vs 86.55), so it is a continual-learning loss, which a training method can attack; Module 3 (richer code) is low value. Script `hw/brain/experiments/month4/brain_strict_ceiling2.py`.


## 20 Oct 2026 (night) - Where the staged loss comes from; real-trace replay (SIMULATED, clothing, margin 256, 3 seeds)

Per-class check (`forget_diag.py`): the 3.2-point staged loss is spread over old classes (trouser 99 -> 89, bag 94 -> 89, sandal/shirt/coat -3 each), a recency bias, not one broken class. Test: our own "stored real traces" night (`real:E`, `cortex_rules.py`; each replay is a stored real code with probability mix/16, else a dream). Half real: E=4 83.45, E=16 83.27; all real: E=16 83.58, E=200 **84.52** (one-pass 86.55, shipped 83.27). So dream fidelity explains at most ~1.2 of the 3.2 points, and only with 200 stored traces per class (far too much memory). The rest is inherent to learning classes in order with a margin table. Replay-side fixes are capped near 84.5; next targets are the order effect itself (new vs old competition) not the replay.


## 20 Oct 2026 (night) - Module 2 (sleep category formation, bounded buffer) works for digits, partly for clothing (SIMULATED, 3 seeds, margin 256)

Unlabelled codes wait in a buffer of B (64 / 128); the K buffered codes that overlap each code most (popcount of AND) pool their class scores with it; the pooled winner must clear the margin cut (percentile Q of the labelled examples) and agree with the fast table; pseudo-labels only among classes rewarded in the context. Arm `fewk:P:Q:K:B` in `brain_strict_digits.py`; logs `k_mnist.log`, `k_fashion.log`.

| labels | digits: gate only (`fewa`) | digits: Module 2 | clothing: gate only | clothing: Module 2 |
|---|---|---|---|---|
| 5 %, Q=25, K=5, B=64 | 89.92 | 90.77 | 74.63 | 73.50 (worse) |
| 5 %, Q=25, K=5, B=128 | 89.92 | 91.62 | 74.63 | 74.63 (same) |
| 5 %, Q=10, K=5, B=64 | - | **93.68** | - | **76.98** (+2.35) |
| 2 %, Q=25, K=5, B=64 | 85.10 | 87.45 (+2.35) | 73.05 | 72.50 (worse) |

Pseudo-label precision stays 99.5 % on digits, 97.9-98.8 % on clothing (gate only: 99.7 %). So Module 2 is a clear win on digits (+1.7 to +3.8 with a lower margin cut, which the buffer makes safe), and a +2.35 gain on clothing only with the lower cut. Second round (Q=0/10, B=128/256) running.


## 20 Oct 2026 (night) - Module 2 round 2 (SIMULATED, 3 seeds, 5 % labels)

Matched cut Q=10: gate only digits 91.33 / clothing 76.28; Module 2 digits 92.7-93.6, clothing 75.8-76.1 (no gain). Q=0, B=128: digits 93.75, clothing **78.32** (+2.0), clothing label precision 97.2 %. 2 % labels, Q=10: digits 93.5, clothing 76.1. Pattern across every idea so far: digits gain, clothing and words gain little or nothing; the ceiling check puts the limit in the code (confusable shirt/T-shirt/pullover/coat classes, twin words), so the next redesign target is Module 3, a code that separates those classes. Logs `k2_mnist.log`, `k2_fashion.log`.


## 20 Oct 2026 (night) - Graded code ceiling probe: FAILED to raise the ceiling (SIMULATED, clothing, float dual-ridge readout)

Shipped OR-pooled code 86.35; pooled counts as thermometer planes (>=1,2) 86.70; (>=1..4) 86.85; OR + strong-match plane 87.05; counts + strong match 87.50 (13,824 bits, three times the memory). Graded counts add at most about 1.1 points, so a graded code is not the missing piece; the limit is what the single detector layer can see (a 5x5 patch, one winner per spot), not how finely its firing is measured. Next probe: whether depth (a second layer of detectors over the first layer's map) raises the ceiling. Script `hw/brain/experiments/month4/brain_strict_graded.py`, log `brain_strict_graded_fashion.log`.


## 20 Oct 2026 (night) - Depth probe: a second unsupervised detector layer does NOT raise the ceiling (SIMULATED, clothing, float dual-ridge)

Layer 1 alone 86.35. Layer 2 (competitive Hebbian over 3x3 / 2x2 neighbourhoods of the layer-1 map, learned on stage-0 images): alone 67.7 / 68.1 / 74.8 / 80.3 (s=3 F2=64 k=1; s=3 F2=128 k=1; s=3 F2=128 k=3; s=2 F2=128 k=3); layer 1 + 2: 86.2 / 86.1 / 86.7 / 86.6. No gain (best +0.3). This is the third negative for a second layer (earlier: two chip-level attempts). Conclusion: the limit is not depth or grading but that all detectors are learned without any signal about what separates the classes. A GPU's advantage is task-driven feature learning (backprop). The brain-principled counterpart is reward-gated local learning (a three-factor rule: detector activity x neighbour activity x reward / surprise), the next thing to test. Script `brain_strict_depth.py`, log `brain_strict_depth_fashion.log`.


## 20 Oct 2026 (night) - Reward-gated detector recruitment: tiny gain (SIMULATED, clothing, replace mode, 6 recruits/channel/round, 4 rounds)

After the table learns, an error image points at its most misleading active bit (largest table entry for the rival minus the right class); the patch behind that bit replaces the least-used detector. Chip one-pass 86.50 -> 86.70 / 86.80 / 86.75 / 87.00; ridge ceiling 86.35 -> 86.60 / 86.30 / 86.55 / 86.75; chip staged 83.10 -> 82.60 (worse). Gain at most +0.5 one-pass, none staged. Stronger variants (grow, 12-16 recruits) not run. Next hypothesis (untested): detectors are learned from the first stage's two classes only (T-shirt, trouser), so later classes are coded by detectors that never saw them; test the ceiling with detectors learned from all classes, then fix by neurogenesis (new detectors recruited from poorly matched patches when a new class arrives, old bits unchanged). Script `brain_strict_reward_det.py`, log `brain_strict_reward_det_fashion.log`.


## 20 Oct 2026 (night) - Detector coverage hypothesis REFUTED (SIMULATED, ridge / chip one-pass / chip staged)

Detectors learned from the first 2 / 4 / 6 / all 10 classes. Clothing: 86.35 / 86.50 / 83.10, 86.25 / 86.00 / 81.90, 86.55 / 86.70 / 83.05, 86.20 / 86.05 / 83.60. Digits: 96.95 / 97.40 / 95.60, 97.05 / 97.45 / 94.95, 97.10 / 97.20 / 95.60, 97.10 / 97.50 / 95.75. No effect: the shipped two-class detectors are as good as all-class ones, so detector coverage is not the limit and neurogenesis is not needed. Script `brain_strict_allcls.py`, logs `brain_strict_allcls_{fashion,mnist}.log`.


## 20 Oct 2026 (night) - Is the information in the code? (SIMULATED, clothing, float classifiers on the shipped code)

Linear ridge 86.35; kNN on Hamming distance k=1/5/15: 77.9 / 79.8 / 80.0; exp-Hamming kernel ridge (nonlinear): 87.3 / 88.3 / 88.35. A strongly nonlinear float readout gains only +2 over linear, so the shipped code holds at most about 88 % of clothing; the chip's one-pass 86.5 is already within 2 points of the best any readout can do on this code. Together with the negative probes (graded counts 87.5, depth 86.7, 64 detectors 87.65, all-class detectors 86.2, reward recruitment 87.0) the single-layer 5x5 detector code saturates near 88 for clothing. Reaching the 93 of a trained CNN would need features learned by task error through many layers, which this design forbids (no backprop). Script `brain_strict_info.py`, log `brain_strict_info_fashion.log`.


## 20 Oct 2026 (night) - Fovea probe and delay-line coincidence probe (SIMULATED, float dual-ridge ceilings, not chip runs)

**Clothing, fovea.** Coarse (shipped) 86.35; fine code (3x3 patches, stride 1, pooled 3x3; 8,192 bits) alone 88.25; coarse + full fine 88.25 (12,800 bits). So finer looking adds about +1.9 of new information, but costs 2.8x the code. Fovea restricted to the 25 % of cells where the top-2 rival templates differ most: 86.95; random 25 % cells (control): 86.75. The rival-template fovea beats its control by only +0.2: **the fovea as designed FAILED**; the gain is in the fine code as a whole, not in the selected places. Script `brain_strict_fovea.py`, log `brain_strict_fovea_fashion.log`.

**Words, delay-line coincidence cells** (7 frequency bands x 7 bands x delays 0..8 over onset and level events, any time, so independent of window position; 1,323 bits). Shipped peak code overall 79.95 / twin words 72.5; coincidence alone 57.5 / 53.6; shipped + coincidence **81.6 / 79.7** (+1.7 overall, +7.2 twin). A real ceiling gain on the twin-word weak spot; chip run still to do. Script `brain_strict_delay.py`, log `brain_strict_delay.log`.


## 20 Oct 2026 (night) - Fine code on the chip: better one-pass, worse staged (SIMULATED, margin 256 / 1,500 dreams / 1 night, 3 seeds)

| code | clothing once / staged | digits once / staged | active bits per image (clothing) |
|---|---|---|---|
| coarse (shipped), 4,608 bits | 86.55 / 83.27 | 97.47 / 95.52 | 263 |
| fine 3x3 stride 1, 8,192 bits | **88.13** / 82.85 | **98.03** / 94.70 | 537 |
| coarse + fine, 12,800 bits | 87.78 / 82.50 | 98.13 / 94.25 | 801 |

The fine code gives +1.6 clothing and +0.6 digits one-pass (the float ceiling of 88.25 is reached), but staged learning gets worse (-0.4 clothing, -0.8 digits) and a decision reads twice as many bits. More bits = more forgetting in staged learning: the staged loss (clothing 5.3 points with the fine code) grows with code size. So the single remaining bottleneck for clothing is the staged-learning loss, not the code. Script `brain_strict_fine_chip.py`, logs `brain_strict_fine_chip_{fashion,mnist}.log`.


## 20 Oct 2026 (night) - Delay-line coincidence cells on the chip, 20 words (SIMULATED, margin 256 / 1,500 dreams / 1 night, 3 seeds)

Peak baseline: clean 73.35, 20 / 10 / 5 dB 65.7 / 51.5 / 39.5, oldest 77.5, newest 57.1, twin 69.1. Peak + coincidence (1,323 bits, `coin` arm in `brain_strict_sound.py`): clean 72.95, 66.6 / 53.9 / 40.3, oldest 75.8, newest 56.7, **twin 73.9**. Twin +4.8 and noise +1 to +2.4, but clean -0.4 and old words -1.7: the same size of gain as the simple timing cells (twin 73.9-74.4), not additive evidence of a clear win; the float probe's +7.2 twin did not carry to the chip. Log `brain_strict_coin.log`. Common pattern across clothing, digits and words: a richer code helps one-pass but the staged loss (clothing 3-5 points, words newest 57 vs oldest 77) eats it, so staged learning is the shared bottleneck.


## 20 Oct 2026 (night) - Concept cells (per-class prototypes, no interference) on today's code (SIMULATED, shipped coarse code, 1 seed)

Staged equals one-pass by construction (a class touches only its own cells). Clothing P=4 / 16 / 32: 80.45 / 83.20 / 82.95; digits 95.05 / 96.10 / 96.50. Chip staged for reference: clothing 83.27, digits 95.52. So the concept cells match the chip's staged result on clothing and beat it on digits by +0.6 to +1.0, but need 10 x P x 4,608 counters (P=16: 737 K counters, several times the chip's 129 KB), and their one-pass is below the chip's (clothing 83.2 vs 86.55). Correction to an earlier remark: this mechanism was the month-1 design (`ConceptMemory`), not untried; what was untested is its staged behaviour on today's code. Script `brain_strict_concept.py`, logs `brain_strict_concept_{fashion,mnist}.log`.


## 20 Oct 2026 (night) - Where the staged loss comes from; cut-and-paste dreams FAILED; early exit WINS on energy (SIMULATED)

**Isolation (`staged_diag2.py`, 3 seeds, coarse code, margin 256 / 1,500 dreams / 1 night).** Clothing: one pass 86.55; blocked by class with no dreams and no night **44.8**; shipped staged 83.27; every stage re-presenting all earlier real examples **87.07**. Digits 97.47 / 58.5 / 95.52 / 97.15. So the dreams carry almost all of the retention (44.8 -> 83.3) and the whole remaining staged loss (3.8 points clothing, 1.6 digits) is the fidelity of the replayed data (note the upper bound also gives old examples extra training passes).

**Cut-and-paste dreams (our own, `xover:E` in `cortex_rules.py`):** each spatial cell of a dream copied from a randomly chosen one of E stored real traces per class (replay recombining fragments), mixed with the usual dreams at rate mix/16. All-cut-and-paste (E=8): staged **62.7**, far worse (overfits the few stored traces). Mixed 2/16, 4/16, 8/16 with E=8 or 32: 82.5-83.4 vs 83.3 baseline (1 seed). **FAILED**: no gain over independent-bit dreams.

**Early exit (`brain_strict_exit.py`, seed 1, staged chip):** the code is read channel by channel; after each channel the chip answers if the top-2 score gap clears a threshold set on training examples (partial winner agreed with the full winner on >= 99 % of them). Clothing 83.10 -> 83.05 reading 58 % of the active bits (-42 % table reads); digits 95.60 -> 95.20 reading 29 % (-71 %). A real, free efficiency gain: compares and one threshold per step, no accuracy cost on clothing, -0.4 on digits. Memory layout note (not simulated): store the 10 class entries of one input bit side by side so one read returns all 10 contributions.


## 20 Oct 2026 (night) - Hard-example replay buffer: +1.2 clothing, but costs digits (SIMULATED, 3 seeds, margin 256 / 1,500 dreams / 1 night; stage-time store, night replay mixed with dreams)

Store, per class, the E real examples the day found hardest (smallest gap between the right class and its best rival, found by comparing table scores), replay them at night in place of a share mix/16 of the dreams (`real:E` with env HARD=1, `cortex_rules.py`).
Clothing staged: E=2 83.75, 4 83.92, 8 84.08, 16 84.23 (mix 16) / 84.37 (mix 8), 64 84.52 vs 83.27 shipped (random first-E traces: 83.3-83.6). So hard examples carry far more than random ones (16 hard traces = 200 random traces). Digits staged: E=4 95.13, E=16 94.78, E=8 94.5-94.9 at every mix, noisy copies (drop 25 % / 12.5 %) 94.5-94.7, replay writes only on errors (margin 0) 94.55, hardest-among-correct 94.6-94.8, vs 95.52 shipped; even 8 random traces at 6 % share gave 92.6. **Not a clear win**: clothing +0.7 to +1.2, digits -0.4 to -1.0; the digits damage was not removed by noise, a smaller write margin or excluding misclassified outliers. Memory would also grow (16 traces x 10 classes x 263 indices x 13 bit = 68 KB). Staged loss on clothing stays ~2.3 points from the one-pass number.


## 20 Oct 2026 (night) - Adaptive real-replay share FAILED on digits (SIMULATED, 3 seeds)

The share of real replay per class was set by a self-test (fraction of its stored hard traces the table now gets wrong; 0 = dreams only). Clothing E=8 / 32: 83.88 / 84.62; digits E=8 / 32: 94.53 / 94.77 vs 95.52 shipped. The digits loss is not removed by an adaptive share (the hardest traces are nearly always among the "wrong", so the share stays high), nor by noisy copies, a write margin of 0, or excluding outliers; random traces at a 6 % share cost digits 3 points, so replaying a few real items hurts digits for a reason I have not found. Under the no-regression rule the hard-example buffer is not merged. Started: 35-word matched baseline (`peak`, `coin`, margin 256) to settle F1 and the coincidence cells at scale; log `brain_strict_peak35_m256.log`.


## 20 Oct 2026 (night) - 35 words, matched baseline (SIMULATED, margin 256 / 1,500 dreams / 1 night, 3 seeds)

Shipped `peak`: clean 68.29, 20 / 10 / 5 dB 56.5 / 39.8 / 27.4, oldest 68.8, newest 60.8, twin 65.2. Causal onset look-ahead (`onsetla:1600`, earlier run): clean 65.64, newest 56.5, twin 64.1: **F1 not at parity at 35 words (-2.7)**. Peak + delay-line coincidence cells (`coin`): clean 67.09 (-1.2), 57.1 / 43.3 / 31.9 dB (+0.6 / +3.5 / +4.5), oldest 69.3, newest 57.0 (-3.8), twin 66.0 (+0.9). Helps noise, hurts clean and newest words, twin gain shrinks to +0.9: fails the no-regression rule at scale. Logs `brain_strict_peak35_m256.log`.


## 20 Oct 2026 (night) - Five new methods from the literature search, ALL FAILED the no-regression rule (SIMULATED)

1. **Direct feedback alignment, binary hidden cells** (`brain_strict_dfa.py`, 1,024 cells, 64 fire, 3 seeds, clothing, chip-style table): table on input only 83.72 (1 epoch) / 84.77 (3); hidden cells fixed random (control) 84.70 / 84.43; hidden cells learned by feedback alignment **82.82 / 83.92**. Learning the hidden cells made it worse than fixed random cells. **FAILED.**
2. **Protect-on-overlap (synaptic tagging)** (`protect:SH`, `cortex_rules.py`; a real example's write on a bit is skipped with probability 1 - 2^-p, p = (sum of |W| over classes) >> SH): SH 2 / 3 / 4 / 6 / 8 clothing staged 75.1 / 76.0 / 77.7 / 82.98 / 83.27 (shipped 83.27), once 80.1 / 83.7 / 85.7 / 86.7 / 86.55. Strong protection hurts; weak protection equals the baseline. **FAILED.**
3. **Dentate pattern separation** (`brain_strict_dg.py`, 8,192 random-subset cells, 3 % fire): expansion alone clothing ridge 82.25, chip once / staged 81.9 / 80.3; input + expansion 86.15 ridge, chip 86.25 / 82.95 vs shipped 86.55 / 83.27. **FAILED** (no gain from separating the confusable classes this way).
4. **Hyperdimensional temporal binding for words** (`brain_strict_hdc.py`, 4,096-bit order-bound bundles of event hypervectors, 20 words, ridge): HDC code alone 48.6 overall / 46.4 twin; shipped + HDC 78.3 / 72.5 vs shipped 79.95 / 72.5. **FAILED.**
5. **Context gating (active-dendrite style)** (`gate:P`: each stage's classes own a random P % of the input bits, entries outside never written): P=50 / 75 clothing staged 82.2 / 82.4, once 86.1 / 86.2 vs 83.27 / 86.55. **FAILED.**

Taken with the earlier probes (graded code, depth, fovea, all-class detectors, reward-gated detectors, kernel readout), the single-layer counting chip appears to be at a local optimum for its principles: every added mechanism either adds nothing or trades one dataset against another. Things that did win: margin / dream / night settings, early exit (energy), Module 2 (few labels, digits), noisy-copy training and timing cells (small).


## 20 Oct 2026 (night) - Class-aware pair cells ceiling probe, and an overdue fairness point about the CNN comparison (SIMULATED)

**Pair cells** (`brain_strict_pairs.py`): 45 class pairs x R integer perceptron cells, each learning only a-vs-b over a random half of the input bits (own local label), binary outputs as hidden code; layer 2 ridge / counting table on a disjoint half of the data. Clothing, ridge / chip once / chip staged: input code only 86.35 / 84.98 / 81.75 -> input + 180 cells 86.65 / 85.75 / 81.35; raw binarised pixels only 84.35 / 83.67 / 76.95 -> + 360 cells 85.55 / 84.25 / 80.88; code + raw 86.75 / 85.08 / 80.13 -> + 360 cells 87.30 / 85.60 / 81.53. Gains +0.3 to +1.2 (the largest on the weaker raw input): not a breakthrough, because the cells see the same bits the readout already sees.

**Fairness correction.** Our chip tests use **10,000 training images** (2,000 per class pair x 5), not the 60,000 of the full set. The usual "about 93 % for a CNN on clothing" is for all 60,000 images; a small CNN on 10,000 images is lower (I recall about 87-89 %, ESTIMATED from memory of learning curves, NOT measured). So the real gap to a CNN at equal data may be 1-3 points, not 6. To measure it, `gpu_baseline_same_data.py` (torch; run on a PC, the container has none) trains a small CNN on the same 10,000 / 2,000 images: joint, naive staged, and staged with a 160-image replay buffer (about the chip's memory). Results pending.


## 20 Oct 2026 (night) - Same-data GPU-style reference MEASURED (small CNN, 421,642 float parameters, backprop, torch on the cloud CPU; same 10,000 training / 2,000 test images as the chip tests)

| | clothing | digits |
|---|---|---|
| CNN joint (all classes together, 15 epochs) | **88.8** | **98.55** |
| CNN staged, naive (5 stages of 2 classes, 5 epochs each) | 20.5 | 19.9 |
| CNN staged + replay buffer of 160 real images (about the chip's 129 KB) | 31.6 | 27.4 |
| CNN staged + 1,000 replayed images (784 KB) | 69.1 | 90.2 |
| CNN staged + 4,000 replayed images (3.1 MB) | 87.8 | 95.9 |
| L one pass (SIMULATED) | 86.55 | 97.47 |
| L staged, no stored data, 129 KB (SIMULATED) | **83.3** | **95.5** |

So at equal data the one-pass gap to a CNN is 2.3 points on clothing and 1.1 on digits (not 6 and 2 as measured against full-set figures). The decisive result is staged learning: a CNN without help collapses to the latest classes (about 20 %), and with a replay buffer at L's memory size it reaches only 28-32 %; it needs about 4,000 stored real images (3.1 MB, 24x the chip's memory) to get near L's staged accuracy (87.8 / 95.9), and 1,000 images (6x) is not enough. This is the first MEASURED head-to-head in the repo. Script `gpu_baseline_same_data.py`, logs `gpu_baseline_same_data_{fashion,mnist}.log`, `gpu_baseline_same_data_rb.log`. Caveat: one seed, one small CNN, no tuned continual-learning method (no regularisation or generative replay), so a stronger GPU baseline could do better.


## 20 Oct 2026 (night) - Same-data GPU-style reference, 20 words (MEASURED, small CNN as above, 1,586 training / 414 test clips, speaker-disjoint, same 28x28 aligned sound picture as the chip, one seed)

| | 20 words |
|---|---|
| CNN joint (25 epochs) | **77.05** |
| CNN staged naive (5 stages of 4 words) | 6.3 |
| CNN staged + 160 stored pictures | 12.3 |
| CNN staged + 1,000 stored pictures (63 % of all the training pictures) | 73.7 |
| L staged, no stored data, margin 256 (SIMULATED) | **73.35** (float ridge on the same code 79.95) |

At equal data the CNN is only 3.7 points above L's staged result, and the float readout on L's own code (79.95) is above the CNN. So the absolute weakness on words (about 73 %) comes from the tiny training set (about 80 clips per word) and the picture, not from our method being far behind a GPU-style model; a CNN with data augmentation or a pretrained front end would do better, which this baseline does not have. Staged, the CNN again collapses without stored data and needs most of the training set stored (1,000 of 1,586 pictures, about 6x the chip's memory) to reach L's number. Script `gpu_baseline_words.py`, log `gpu_baseline_words.log`.


## 20 Oct 2026 (night) - Categorical dreams fail; Module 2 + eye movements closes the few-label gap on digits (SIMULATED, 3 seeds, margin 256 / 1,500 dreams / 1 night)

**Categorical dreams** (`catdream`, `cortex_rules.py`: per spatial cell the expected number of winners is drawn from the on-counts and that many distinct detectors are chosen in proportion to their counts; same memory): clothing staged 83.8 / digits 94.58 (pure); mixed with independent-bit dreams at 4/16, 8/16, 12/16: clothing 83.6 / 83.2 / 83.2, digits 95.1 / 94.1 / 95.5 vs 83.27 / 95.52 shipped. Within seed noise (about +-0.5), no clear gain: **FAILED** the no-regression rule. Staged loss stays.

**Module 2 + eye movements** (`fewkv:P:Q:K:B` in `brain_strict_digits.py`: the sleep buffer's neighbour-pooled pseudo-labels, and every one of the 4 one-pixel-shifted views must name the same class; labelled and pseudo-labelled examples are learned with their views), 5 % labels:
digits 95.25 (Q=0) / 95.07 (Q=10) vs gate only 89.9, Module 2 alone 93.75, and **all labels 95.52**; pseudo-label precision 99.8-99.9 %. So with 5 % of the labels the chip is within 0.3 points of the all-labelled result on digits (**WIN**; affects only the few-label mode, the all-label path is unchanged).
Clothing 77.98 / 78.13 vs Module 2 alone 78.32 vs all labels 83.3: no gain from views; the 5-point gap stays (pseudo-label precision 96-99 %: confusable shirt / T-shirt / pullover / coat pseudo-labels repeat the same mistakes, so they add little new). Logs `kv_mnist.log`, `kv_fashion.log`.


## 20 Oct 2026 (night) - Twin words against the same-data CNN (MEASURED reference, 20 words)

CNN joint: overall 77.05, **twin words 84.06** (the 8 acoustic pairs present: no/go, left/right, up/off, on/off, bed/bird, down/dog, three/tree, four/forward; accuracy over the clips of those words). L staged (SIMULATED): twin 69.1 (shipped peak), 73.9 (timing cells / coincidence), float readout on the shipped code 72.5. So twin words are not hard for a trained network (84, above its own overall 77) while for L they are below its overall (69 vs 73): a real gap of 10-15 points, a design weakness and not a data limit. Staged CNN: naive 0.0 on twins, 160-picture replay 5.8 (`gpu_baseline_words2.log`).


## 20 Oct 2026 (night) - Temporal fovea for sound FAILED (SIMULATED, 20 words, float dual-ridge ceiling)

The same integer cochlea run with finer frames (FF = 224 / 112 / 56 per second, ~4.5 / 9 / 18 ms); a window of 28 fine frames starting one coarse frame before the shipped alignment's word start, turned into a second 28x28 picture (same noise floor and level scale), encoded with the same 10-channel detector rule and appended to the shipped code. Shipped peak 79.95 overall / 72.46 twin. FF=224: fine window alone 57.3 / 36.2, shipped + window 79.47 / 66.67. FF=112: 79.95 / 63.77. FF=56: 78.02 / 66.67. No gain on overall, and twin words got worse in every case: the onset detail adds noise the readout cannot use. The measured twin-word gap (CNN 84.06) is therefore not a time-resolution problem of the first 100 ms. Script `brain_strict_tfovea.py`, log `brain_strict_tfovea.log`.


## 20 Oct 2026 (night) - Two senses: picture + sound (SIMULATED, MNIST digits + FSDD spoken digits (2,999 clips, 6 speakers, downloaded from raw.githubusercontent.com), one pass, margin 256 / 1,500 dreams / 1 night, 3 seeds)

A seen digit is paired with a clip of the same digit (different instances); script `brain_strict_twosense.py`, log `brain_strict_twosense.log`. Test speaker = the last speaker, never in training.
- Picture learner with true labels (reference): **97.40**.
- **Zero picture labels, the ear names the digit** (ear trained on 3 speakers; the clips paired with the pictures come from 2 other speakers it never heard): the ear is right on **73.5 %** of them (sound alone on the new test speaker 77.5 %), and the picture learner trained only on the ear's names still reaches **89.67** on pictures. (A first version, where the ear named clips from its own training speakers, was 98.7 % right and gave 97.35; that was optimistic and is not the honest number.)
- **Both senses in one table** (joint code, 27,648 bits): pictures + sound **98.33** against 97.40 for the picture learner alone. With 25 % of the picture's active bits dropped: sound present 97.28, sound absent 85.4 (the sound covers +11.9). With 50 % of the sound dropped, picture present: 98.33. Sound only 73.8, picture only (sound blanked) 86.0 (a blanked sense shifts the table sums, so this is not the picture-alone score).
Reading: a heard word can label a picture with no picture labels (89.7 from a 73.5 %-correct ear), two senses beat one (+0.9 and a large cover when one is damaged), as in the brain. The cost is the second sense's code (23,040 bits) in the table. Not yet tried: cleaning the ear's noisy names with the picture's own neighbours (Module 2), which should close part of 89.7 -> 97.4.


## 20 Oct 2026 (night) - Cleaning the ear's names with the picture's own neighbours: 89.7 -> 93.9 with zero picture labels (SIMULATED, 3 seeds; script `brain_strict_twosense2.py`, log `brain_strict_twosense2.log`)

Setup as the honest two-sense test (ear trained on speakers 0-2, correct on 73.5 % of the clips heard with the pictures). In sleep the pictures wait in a buffer (128 or 256); the K=5-8 buffered pictures that overlap each picture most (popcount of AND) pool their class scores with its own; the pooled winner is the new name; a fresh table is learned on the cleaned names; optionally the ear's own name also counts as a vote; 1-2 rounds.
Picture learner on the ear's names as given 89.70; **cleaned, K=5 buffer 128, 2 rounds, no ear vote 93.70 (names 94.9 % correct)**; with ear vote 93.57; K=8 buffer 256, 2 rounds 93.72 (no vote) / **93.88** (with vote, names 95.0 % correct); 1 round 93.3 / 92.98; true labels (reference) 97.40. So the same sleep-time neighbour pooling that gave few-label gains lifts a heard-word-only label from 89.7 to 93.9 (+4.2), closing more than half of the gap to the true-label result, with no picture labels at all. Remaining gap to true labels 3.5 points; more rounds not tried.


## 20 Oct 2026 (night) - CORRECTION: the twin-word gap was a small-sample artifact (MEASURED CNN, float readout on L's own code; `twin_diag.py`, logs `twin_diag.log`, `twin_diag35.log`)

The 20-word subset contains only **4 twin words** (left, right, three, tree; 69 test clips), so the earlier "CNN 84.06 vs L about 70" is a four-word, 69-clip comparison (one word, "three", is 95 % vs 70 %; "left" is 86 % vs 100 %). On the 35-word set (15 twin words, about 340 test clips): CNN twin 65.4 / non-twin 78.0 / overall 72.5; **L float readout twin 68.6 / non-twin 77.8 / overall 73.8**, i.e. L is at or above the CNN on twin words, not behind. For both, only 22-32 % of twin-word errors land on the twin partner; 68-78 % go to other words. So twin words are not a special weakness of the code, my earlier statement of a 10-15 point twin gap was wrong, and the timing / coincidence / hyperdimensional / temporal-fovea attempts were chasing a difference that is mostly sampling noise. What remains real on words: the staged chip (73.35 on 20 words, 68.3 on 35) is below its own float readout on the same code (79.95 / 73.8) by about 5-6 points, the same staged-learning loss as on clothing and digits. F8 is reframed accordingly.


## 20 Oct 2026 (night) - Staged loss is NOT a class-balance (recency) problem: intrinsic-plasticity bias FAILED (SIMULATED, 3 seeds; `bias_calib.py`, logs `bias_calib_{fashion,mnist}.log`)

After the 5 stages the share of test decisions won by each class is already balanced (clothing 0.085-0.108, digits 0.088-0.113, true share 0.100). One integer bias per class tuned so no class wins more than its share: from dreams only (nothing stored) clothing 81.23 / digits 95.52 vs shipped 83.27 / 95.52; tuned on the real training data (a cheating bound) 83.88 / 95.33. Even the bound gains at most +0.6 on clothing and loses 0.2 on digits. So the remaining staged loss is per-pair separation (the old-vs-new boundaries were only ever fitted against dreams), not a preference for the newest classes. Together with every other replay-side test (stored traces: clothing up, digits down; categorical, cut-and-paste, prioritised, noisy dreams; protection, gating, budget, downscaling) the staged floor looks firm for this design: 83-84 clothing, 95.5 digits without stored real data; the only lever that moved it was stored real hard examples (+1.2 clothing, about 270 KB for 64 per class).


## 20 Oct 2026 (night) - Why stored traces hurt digits, and the fix: hard-example replay + the normal dream night (SIMULATED)

**Cause found.** (`night replays / writes` log) The shipped dream night runs its full 6,000-15,000 replays with almost no writes (2-12): its job is not to change the fast table but to give the slow table (the one used for decisions) the ticks to follow it (the slow table moves every 100 replays). With stored real traces the night's safety stop (end the night when a 256-replay block causes more than 2 writes) fired after **256 replays**, so the slow table never caught up: that was the digits loss, not the traces. Test: night never stops, E=8 random mix 2 -> digits 95.48; with 1,000 stored real traces per class and a full night, staged = one-pass (digits **97.45** vs 97.47, clothing **86.82** vs 86.55; about 4 MB of traces, too much for the chip). With few traces and a full-length night the few items are replayed too often and overfit (clothing 82.4 / 79.5): the early stop had also been protecting clothing, which is why the earlier gain was +1.2.

**Fix: separate the two jobs.** First a short replay of the E stored hardest examples per class (mix/16 of the replays, the stop rule kept), then the normal dream night for consolidation (`CONS=1`, rule `real` in `cortex_rules.py`, `HARD=1` stores the examples the day found hardest, smallest gap between the right class and its best rival; adds and compares only).
5 seeds, SIMULATED, shipped on the same seeds: digits 94.87 / clothing 83.18 staged. E=4 / 8 / 16 / 32 (mix 8/16): digits 95.60 / 95.57 / 95.72 / 95.31, clothing 83.79 / 84.15 / 84.40 / 84.33. So **digits +0.7, clothing +1.0 (E=8)**, passing the no-regression rule on both with 34 KB (E=8 as 13-bit indices of about 263 active bits) or 68 KB (E=16) of stored traces, +26 % / +53 % of the chip's 129 KB.
**Words (the third leg of the rule) are fragile:** 20 words E=8 mix 8: clean 75.12 (shipped 73.35), oldest 79.65 (77.49), newest 58.6 (57.1), noise 66.3 / 53.8 / 41.6; 35 words E=8: clean 68.57 (68.29), oldest 73.57 (68.81), newest 57.2 (60.8). But E=16 (20 and 35 words) and E=4 mix 8 (35 words) collapse the newest words (36-37 %), E=4 mix 4: 20 words 73.19 / 35 words 68.76. So the words result depends on the stored set (about 80 clips per word); it is not robust enough to adopt for sound yet. Logs `brain_strict_hr20.log`, `hr35.log`, `hr20b.log`, `hr35b.log`.


## 20 Oct 2026 (night) - Why the newest words collapse, and the guarantee that fixes it (SIMULATED; `hr_diag.py`, logs `hr_diag.log`, `hr_diag_seeds.log`, `brain_strict_hr{20,35}d.log`)

**Cause (seed 2, 20 words, 16 stored traces):** the last stage's night ran **576 replays instead of 30,000** and the newest four words scored **0.0 %** (none of their clips was assigned to any of those words). After the real-trace replay has moved the fast table, the dream night's own safety stop (end the night when a block of 256 dreams causes more than 2 writes) fires within 256-512 replays, so the slow table (used for decisions) never follows the fast table for the classes just learned and stays near empty for them. It happens only for some seeds / stored sets (seed 1 and 3: full-length nights, no collapse). Skipping the stage's own classes in the real replay did not help (and broke a working setting), so the stored traces themselves were not the cause.
**Fix: guarantee consolidation** (`CONS=2`): after the dream night, run the follow-only consolidation (the slow table follows the fast one for as many steps as a full night gives, no dream generated; a no-op if already converged). Follow-only does not replace the dream night: digits 94.89 vs 94.87 shipped, but clothing 81.38 vs 83.18, so the night's dreams still earn their keep on clothing.
Words (3 seeds), hard-example replay E = 16 / 8 / 4 stored traces per word, mix 8/16, guaranteed consolidation, against shipped 20 words clean 73.35 / oldest 77.49 / newest 57.09 and 35 words 68.29 / 68.81 / 60.76: 20 words clean 72.71 / **75.04** / 73.27, oldest 80.52 / 80.52 / 79.65, newest 51.34 / 58.62 / 57.09; 35 words clean 68.25 / 68.34 / 68.85, oldest 73.81 / 72.86 / 73.57, newest 56.74 / 56.50 / 56.26. **No collapse in any setting** (newest 51-59 % where before 0-37 %). E=8 passes the no-regression rule on clean and oldest at both sizes (20 words +1.7 clean, +3.0 oldest, +1.5 newest; 35 words +0.05 clean, +4.1 oldest, but newest -4.3: an old-versus-new trade-off at 35 words).


## 20 Oct 2026 (night) - CORRECTION: the hard-example replay does not hold once consolidation is made reliable (SIMULATED, 5 seeds images / 3 seeds words)

With the guarantee that the slow table always follows (only the missing steps when the night stopped early, `CONS=3`; the always-on version `CONS=2` gives the same): digits staged 95.55 (shipped 94.87, kept), **clothing 82.42 (shipped 83.18: lost; the earlier 84.15 is gone)**; words E=8 20 words clean 75.12 / oldest 79.65 / newest 58.62 (kept), 35 words 68.34 / 72.86 / 56.74; E=16 20 words 72.87 / 80.09 / 51.34 and 35 words 68.34 / 73.81 / 56.97. Slowing the slow table is not the explanation (shipped K=5 / 6 / 7 / 8: clothing 83.18 / 80.67 / 76.02 / 10.7; digits 94.87 / 92.62 / 89.94 / 10.6; K=8 never catches up in a night). So the clothing gain (+1.0) I reported earlier came from nights cut short by the stop rule, not from the stored traces; with consolidation repaired, a few stored traces replayed intensively overfit and clothing falls below shipped. Digits and words keep +0.7 and +1.8 (20 words clean), but the no-regression rule needs all three legs, so **hard-example replay is NOT adopted** (a per-dataset switch is not allowed unless the chip decides it from its own signals). What stays: (1) the night's real job is consolidation (the slow table following the fast one), dream replays almost never write (2-14 writes per 15,000-30,000 replays); (2) with about 1,000 stored traces per class staged equals one-pass (digits 97.45, clothing 86.82; about 4 MB); (3) a follow-only night equals the dream night on digits (94.89 vs 94.87) and saves the dreams' energy there, but costs clothing 1.8 (81.38 vs 83.18).


## 20 Oct 2026 (night) - Sensory node, piece 1: the core takes the two-sense code, bit-exact (RTL vs integer model)

`hw/rtl/cortex/run_check_cortex_twosense.py`: cortex_core.v (CORTEX_HOOKS build) with **NB = 27,648 and AW = 15**, learning and predicting on real paired codes (MNIST picture 4,608 bits + FSDD spoken digit 23,040 bits), margin 256: 204 commands, 200 lines compared, **0 mismatches**, 60 table writes, margins 15 to 1,309. PASS. So the existing core already supports one table over both senses by changing two parameters. Cost: the table grows with the code (4,608 bits = 129 KB for the whole chip, 27,648 bits about 6x, roughly 780 KB), which is why the next step is to try a smaller sound code. Plan for the rest (about 12 h): 2 smaller sound code; 3 wire retina + cochlea into one code feeding the table and check bit-exactly; 4 sleep cleaning on the chip (picture buffer + popcount overlap) with a testbench; 5 CNN two-sense reference; 6 run_all_checks, docs, pitch, lint.


## 20 Oct 2026 (night) - Sensory node, piece 2: a much smaller sound code works as well (SIMULATED, FSDD + MNIST, 3 seeds, margin 256 / 1,500 dreams / 1 night; `brain_strict_soundsize.py`, `brain_strict_soundsize.log`)

Sound bits / picture + sound bits / sound alone on the held-out speaker / both senses: 10 channels x 64 detectors (shipped) 23,040 / 27,648 / 77.47 / 98.33; 10 x 32 11,520 / 16,128 / 79.27 / 98.48; 10 x 16 5,760 / 10,368 / 76.80 / 98.83; 5 x 64 11,520 / 16,128 / 75.87 / 98.90; 5 x 32 5,760 / 10,368 / 77.20 / 98.93; **4 x 32 4,608 / 9,216 / 76.93 / 98.97**; 3 x 32 3,456 / 8,064 / 76.53 / 98.83; 3 x 16 1,728 / 6,336 / 71.80 / 98.95. **Chosen: 4 channels (thresholds 50, 110, 170 and the retina-style on-cells) x 32 detectors = 4,608 sound bits, the same size as the picture code**, so the two-sense table is 9,216 bits (about 2x the one-sense chip, about 258 KB) instead of 27,648 (6x), with no loss of accuracy (both senses 98.97 vs 98.33; the differences between the variants are within seed noise). Core check at this width (NB = 9,216, AW = 14) comes next.


## 20 Oct 2026 (night) - Sensory node, piece 3: the whole two-sense chip is bit-exact (RTL vs Python chain)

`hw/rtl/cortex/cortex_sense_top.v` (new): a retina (28x28 picture -> `cortex_encoder_gen`, 4 channels x 32 detectors) and a cochlea (live 16 kHz samples -> `cortex_cochlea_stream` with noise floor and word alignment -> sound picture -> `cortex_encoder_gen`, 4 channels x 32 detectors, 3x3 windows) write into ONE list of ONE core (`NB = 9,216`, `AW = 14`): picture bits 0..4607, sound bits 4608..9215. One sense alone (a picture, or a sound) also works (the sound bits keep the 4,608 offset); `code_len` gives the list length for the command. Testbench `tb_sense_top.v`, check `run_check_sense_top.py` (FSDD wav clips and MNIST pictures in, against `Features.encode` + `cochlea_int.sound_picture_int` + `SoundFeatures.encode` + `CortexInt`): LEARN with picture + sound, with the picture alone, with the sound alone, then PREDICT with both senses / picture alone / sound alone: 48 commands, **9,270 lines compared (every update flag, every prediction, the final counts, table and dream counters), 0 mismatches, PASS**. (The 12/24 correct predictions are the tiny scenario's, only 4 learn events per class; accuracy numbers are in the earlier entries.) Regenerated check files are now git-ignored.
Next: sleep cleaning needs the core to show all 10 class scores after a PREDICT (build option) and an overlap unit (number of code bits two pictures share); the neighbour selection and score pooling stay host-side like the other sleep logic.


## 20 Oct 2026 (night) - Sensory node, piece 4: the sleep cleaning runs on the chip's own parts, bit-exact

Three additions, each checked against the Python model:
1. **`cortex_core.v` (CORTEX_HOOKS build): `rd_scores`**, all 10 class scores left by the last PREDICT (the core already kept them in `acc[]`). `run_check_cortex_hooks.py` now also compares an `S` line of all 10 scores after every PREDICT: PASS (204 commands, 0 mismatches, margin 256).
2. **`cortex_neighbours.v` (new)**: a buffer of NS codes (lists of active bits, up to 1,024 entries) and, for a query slot, the K buffered codes sharing the most active bits with it: the overlap = number of common list entries by a two-pointer merge (compares and one counter, no multiplier), top-K kept by insertion, ties to the lower slot. `run_check_neighbours.py`: real MNIST picture codes (about 250 active bits), 16 slots (some empty), K = 4, 6 queries, **0 mismatches** (6,446 cycles per query at 16 slots, about 26,000 at 64: a 64-picture buffer is cleaned in about 1.7 M cycles, 17 ms at 100 MHz).
3. **`cross_modal.pool_names`** (host side: adds and compares): new name = argmax over the known classes of own score + the K neighbours' scores (+ the ear's vote); stable tie-breaking in `clean_names`.
**End to end** `run_check_sleep_clean.py`: the core learns 120 pictures under 25 %-noisy names, then 32 buffered pictures are cleaned from the RTL's scores and the RTL's neighbours; the names equal those from the software model: **0 differing score rows, 0 differing neighbour rows, 0 differing names, PASS** (the ear's names 62 % right became 75 % right in this tiny scenario).
So the sensory node is now: two sensors into one core (piece 3), one-sense or two-sense experiences, and sleep cleaning with the chip's scores and neighbour unit plus a few adds on the host. Not done: the host pooling is software, not RTL.


## 20 Oct 2026 (night) - Sensory node, piece 5: the CNN two-sense reference (MEASURED, 2 seeds; small CNNs, float32, backprop; a ruler only, never in the chip) (`gpu_twosense.py`, `gpu_twosense.log`)

Same data as the chip tests (MNIST 10,000 / 2,000, FSDD spoken digits, ear trained on speakers 0-2, clips paired with pictures from speakers 3-4, test speaker the last): 
| | CNN (MEASURED) | L (SIMULATED) |
|---|---|---|
| the ear's names right on unseen speakers | 72.3 % | 73.5 % |
| picture learner, true labels | 98.52 | 97.40 |
| **zero picture labels, ear's names** | **83.45** | **89.67** (raw) |
| zero picture labels + 2 rounds of cleaning | 82.87 (self-training; names 83.7 % right) | **93.88** (neighbour cleaning in sleep; names 95.0 % right) |
| both senses, labelled pairs | **99.45** | 98.97 (4 x 32 sound code) |
| picture damaged 25 % + sound | **99.25** | 97.3 (98.0 with the small code not re-run) |
| picture damaged 25 %, no sound | 80.8 | 85.4 |
| picture only (sound blank) | 85.45 | 86.0 |
| sound only (picture blank) | 57.9 | 73.8 |
Reading: with labels the CNN is 0.5-1 point better on two senses and on damage-with-sound (it has far more parameters and trains many epochs); **with no picture labels L is clearly ahead (93.9 vs 83.5 / 82.9)**, because the neighbour pooling in sleep cleans the ear's noisy names while the CNN's own self-training only reinforces its mistakes (82.87 after two rounds). Not identical conditions: the damage was removing 25 % of lit pixels for the CNN and 25 % of active code bits for L; the CNN also saw the same 10,000 pictures for 12 epochs.


## 20 Oct 2026 (night) - Sensory node, piece 6: full regression and the end of the build

`sh hw/run_all_checks.sh DATA_DIR` (every RTL check in sequence, now 29 lines): **0 failures**; every check that could run PASSED: the ten core variants (FPGA, pipelined, context memory, IMPRINT, slow table, embedding path, each plus pipelined), the hooks build (now with all 10 class scores per PREDICT), the encoders (FPGA, ASIC, finer grid, learning, general images, speckle removal), the **four new two-sense checks** (core at NB = 27,648; neighbour unit; sleep cleaning from the chip's scores and neighbours; the whole two-sense chip: retina + cochlea + one core), the Tang Nano board design and the host schedule. **6 checks skipped** because the old speech datasets are not in this container (cochlea buffered / streaming / aligned, general encoder sound x2, the sound chip's whole chain): they must be re-run on the PC where `speech_framesums_int.npz` lives (`sh hw/run_all_checks.sh D:\cortex_data`). The first pass showed 11 "failures" that were all missing cached code files (`sep_mnist_F32_p2.npz`, `sep_fashion_F32_p2.npz`, regenerated the way `proof_suite_v3.py` makes them), not mismatches. `run_all_checks.sh` now skips a check with a clear SKIP line when its data is missing and counts skips separately. Build summary of the sensory node: [sensory node](../hw/results/sensory_node.md).


## 20 Oct 2026 (night) - A: two senses on a SECOND dataset pair holds, and zero-label learning almost reaches the labelled result (SIMULATED, 3 seeds; `brain_strict_twosense_sc.py`, `brain_strict_twosense_sc.log`)

MNIST pictures + **Speech Commands spoken digits** (zero..nine, 100 clips each, many speakers and microphones: noisier than FSDD); speakers by hash mod 5: 1-2 teach the ear (409 labelled clips), 3-4 are heard with the pictures (390 clips), 0 is the test speaker (201 clips). Same 4 x 32 sound code and chip rule. Ear alone on unseen speakers **75.6**; its names right on the clips heard with the pictures **72.5 %**; picture learner true labels **97.40**; **zero picture labels, ear's names as given 92.30; names cleaned in sleep (neighbour pooling, K = 8, buffer 256, ear vote, 2 rounds) 96.93** (cleaned names 98.1 % right), within 0.5 of the labelled result (on FSDD: 89.67 / 93.88); both senses in one table **98.87**; picture 25 % damaged + sound **98.42**, without the sound 87.15 (sound covers +11.3). So the two-sense results and the "a heard word names pictures" result are not an artefact of one sound set; the cleaning helps even more here (names 72.5 -> 98.1 % right).

## 20 Oct 2026 (night) - C: F1 (word alignment) settled by design, not by another trigger (no new run)

What the record says: the shipped alignment starts the window at the first frame reaching 3/4 of the loudest frame of the clip (a landmark near the vowel); it needs the whole clip. Fully streaming triggers (fixed loudness 800 / 1600, adaptive onset, look-again views) were 2.7-3 points lower clean at 35 words (peak 68.29 vs onset look-again 65.64; 717-clip PC run 64.2 vs 60.7) and equal only at 5 dB; coincidence, timing, hyperdimensional and temporal-fovea cells did not change that. Reading: the loudest-frame landmark is steadier than a noisy start (stop bursts, fricatives). It is also **not a brain-principle violation**: the brain listens through an echoic buffer (sensory memory of the last seconds) before it analyses a word, and the chip's cochlea module already holds the one-second picture (28 x 28 bytes, `cortex_cochlea_stream.v`, ALIGN = 1, bit-exact). So F1 is closed as: the shipped rule stays and is documented as "alignment inside a one-second echoic buffer"; a fully streaming trigger remains about 3 points worse at 35 words (MEASURED in simulation) and is listed as a limit, not hidden.

## 20 Oct 2026 (night) - B: clothing with no picture labels works with a noisy name source plus sleep cleaning (SIMULATED, 3 seeds, one pass; `brain_strict_clothing_names.py`, `brain_strict_clothing_names.log`)

There is no spoken clothing set, so the ear is a SIMULATED labeller: its wrong names are either uniform (any other class) or confusable (one of the 2 classes whose mean code overlaps the true class most: shirt / T-shirt / pullover / coat ...). Fashion-MNIST, shipped 4,608-bit picture code, margin 256 / 1,500 dreams / 1 night; true labels (reference) **86.55**.
Names as given -> cleaned in sleep (cross_modal.learn_picture: neighbour pooling K = 8, buffer 256, ear vote, 2 rounds), names right after cleaning: uniform 27 % wrong 84.92 -> **85.43** (95.1 %); uniform 40 % wrong 84.03 -> **85.13** (94.6 %); confusable 27 % wrong 83.20 -> **85.43** (95.3 %); confusable 40 % wrong **78.72 -> 85.20** (94.3 %, +6.5). So with a name source that is only 60-73 % right the clothing learner reaches 85.1-85.4, within 1.1-1.4 of the all-labels result, and the cleaning matters most when the errors are the confusable ones (the same ones that limited the earlier few-label clothing results, 78 vs 83.3). Caveats: the ear is simulated (random or confusable noise, not a real spoken-clothing set), one-pass not staged, and the true labels are used only to score.

## 20 Oct 2026 (night) - D: a second sense raises staged accuracy on digits; the clothing staged floor stays (SIMULATED, 3 seeds; `brain_strict_twosense_staged.py`, logs `brain_strict_twosense_staged_{fsdd,sc}.log`)

Digits in 5 stages of 2 classes with the chip's dreams between stages (margin 256 / 1,500 dreams / 1 night), every seen digit paired with a heard clip of the same digit (joint table 9,216 bits). One pass / staged (loss), FSDD pair: picture alone 97.47 / 95.52 (1.95); **both senses, tested with both 98.83 / 96.58 (2.25)**; picture only (sound blank) 90.00 / 83.67; sound alone 80.73 / 69.88 (10.85). Speech Commands pair: picture alone 97.47 / 95.52 (1.95); **both senses 99.07 / 97.72 (1.35)**; picture only 89.05 / 86.32; sound alone 83.25 / 83.50 (-0.25). So with two senses the staged accuracy is **+1.1 / +2.2 points higher** than with the picture alone and the loss is similar or smaller; a joint table tested with only one sense is weaker than a table trained on that sense alone (the blanked sense shifts the sums), so the benefit needs both senses at test time. For clothing there is no second sense, so the staged floor (83-84 against 86.55 one pass) stays: D is closed as accepted and documented for clothing, improved for digits with two senses. (A spoken name as the "second sense" of a clothing picture would just give the label away at test time, so it is not a fair test and was not run.)

## 20 Oct 2026 (night) - E: new words from 1-5 recordings are at rough parity with a GPU-style model (no new run; numbers from earlier logs)

Same split (5 known words, 5 new words, enrolled from k recordings): the chip's table-score embedding path (RTL option CORTEX_EMBED, bit-exact) 50.2 / 56.4 / 62.3 over all ten words at k = 1 / 2 / 5 with the old words unchanged (SIMULATED); a small CNN (float, backprop) used as a prototype embedding, `gpu_style_fewshot.log` (MEASURED): all ten words 55.1 / 63.7 at k = 1 / 5 (new words alone 25.5 / 43.5, old words 84.0 / 83.3; with the FSDD digits as extra training classes 53.6 / 65.4, new alone 21.0 / 49.0). So on this task L is within about 2-5 points of the GPU-style model overall (-4.9 at k = 1, -1.4 at k = 5) and the limit is shared: the known vocabulary (about 5-15 words) and the picture's features; more detectors, more fitting words and an exemplar memory did not help (earlier entries). E is closed as measured and documented, not as solved.

## 20 Oct 2026 (night) - Regression complete: 29 of 29 checks PASS, none skipped

The six checks that were skipped for missing speech data now run: a compatible `speech/` folder (the ten words of `cochlea.WORDS`, 100 clips each from `data/sc_subset`, test split = every fifth speaker, not the original official list; bit-exactness does not depend on the split) and `speech_framesums_int.npz` (1,000 clips: 777 train, 223 test) were rebuilt in the session's scratch folder with `noise_floor.load_framesums`. `sh hw/run_all_checks.sh DATA_DIR` then gave **29 PASS, 0 failures, 0 skipped** (`hw/check_summary.txt`): the ten core variants, the hooks build, the encoders (images, sound, finer sound grid, speckle removal, learning, ASIC / gated clocks), the cochlea (buffered, streaming, word aligned), the sound chip's whole chain, the four two-sense checks, the Tang Nano board design and the host schedule. The earlier line in the piece-6 entry that the six speech checks "must be re-run on the PC" no longer applies; re-running them on the PC with the official speech list remains an optional final pass.

## 20 Oct 2026 (night) - F3: two senses form categories with no labels far better than one (SIMULATED, 3 seeds; `brain_strict_cocluster.py`, logs `brain_strict_cocluster_{fsdd,sc}.log`)

A seen digit and a heard clip of the same digit occur together; no label is used to form 10 groups (competitive learning on binary codes: k-means by overlap, k-means++ start, 6 restarts). Group purity FSDD pair / Speech Commands pair: picture alone 66.6 / 66.6; sound alone 41.2 / 44.4; **both senses joined 72.5 / 80.6**. A picture learner (chip counting table, one pass) trained on the group names after each group is named by one label (10 labels in total), tested on MNIST: picture alone 67.1 / 67.4; sound alone 45.1 / 54.1; **both senses joined 76.8 / 89.0**; all true labels 97.4. So the second sense lifts the label-free category quality by 6-14 points (purity) and the learned accuracy by 9-22 points; plain k-means is a modest unsupervised layer (the failed earlier ones were picture-only), and the joint groups are the ones that can then be cleaned in sleep (next entry).

## 20 Oct 2026 (night) - F3 continued: sleep cleaning and refinement of the label-free groups (SIMULATED; `brain_strict_cocluster.py`, `brain_strict_cocluster_loop.py`, logs `brain_strict_cocluster2_*.log`, `brain_strict_cocluster_loop_*.log`)

**Cleaning the group names** (names from 10 label-free groups, one label per group = 10 labels in total; picture learner, neighbour pooling K = 8, buffer 256, 2 rounds; 2 seeds): Speech Commands pair, joined groups: names right 79.6 -> picture learner 88.5 -> **90.5 after cleaning** (names 92.2 % right); picture-alone groups 70.6 -> 76.8; sound-alone groups 46.8 -> 57.5. FSDD pair, joined groups: 65.7 names -> 73.9 -> 73.7 (no gain; the starting groups are only 70 % pure).
**The refinement loop** (a joint table learns the pairs under the names, re-names every pair with both senses pooled over neighbours, repeat 3 rounds; 3 seeds, 6 restarts): group names right FSDD 68.7 -> 71.4 (rounds 1-3: 71.4 / 71.3 / 71.2), Speech Commands 77.2 -> 84.1 / 85.0 / 85.0; picture learner on the final names **73.1 / 85.7**; joint learner (both senses at test) 78.2 / 86.8; all true labels 97.4 / 97.4 (joint 99.0 / 99.3). So with only 10 labels in total and no label used to form the groups the chip reaches 73-86 on pictures, against 67 for picture-only groups; the starting groups (69-77 % pure) are the cap, not the sleep step. Next: over-segmenting (30 groups, one label per group).

## 20 Oct 2026 (night) - F3 DONE: over-segmented label-free groups from two senses reach the labelled result (SIMULATED, 2 seeds, 4 restarts; `brain_strict_cocluster_loop.py` with KG = 30, logs `brain_strict_cocluster_loop30_{fsdd,sc}.log`)

Form **30** groups by competitive learning (k-means by overlap) on the joined picture + sound code of co-occurring pairs, **no label used**; name each group by ONE label (the majority of 5 labelled members, **30 labels in total = 3 per class**); then 2 refinement rounds (a joint table learns the pairs under the names, re-names every pair with both senses pooled over its 8 nearest buffered neighbours, buffer 256). Group names right, FSDD pair / Speech Commands pair: round 0 **92.8 / 92.0**, after the rounds **95.7 / 97.4**. A picture learner (counting table, one pass) trained on the final names, tested on MNIST pictures: **96.12 / 96.98**; a joint learner tested with both senses 95.55 / **98.35**; all 10,000 true labels (reference) picture 97.43 / 97.43, joint 99.10 / 99.35. So the label-free category layer now works: a category layer with no labels (two senses co-occurring + competitive learning + sleep cleaning) plus 30 names reaches within 0.4-1.3 points of 10,000 labels (10 groups, 10 labels: 73 / 86; the difference is purer starting groups). The earlier unsupervised layers (picture-only) failed; the second sense is what made it work. Caveats: the grouping step is run as host-side k-means (templates = member means; overlap scoring and mean counts are the chip's own operations but the loop is not in RTL); 2 seeds; digits only; cost: the 30-group clustering took about 15 minutes per seed in software.

## 20 Oct 2026 (night) - F11: the pooling is in hardware now; the whole sleep-cleaning loop runs on the chip's own parts (bit-exact)

`hw/rtl/cortex/cortex_pool.v` (new): for every buffered picture, new name = the known class with the highest pooled score, pooled[c] = its own class score + the K = 8 neighbours' scores for that class (+ 200 x (K + 1) for the class the ear named); unknown classes are never chosen, the first class wins a tie; integer adds and one compare per class, no multiplier; cycles = NS x C x (K + 2) = 3,521 for 32 pictures. First run failed (names differing 32 / 32): a `?:` mixing a signed 20-bit score with an unsigned zero constant zero-extended the negative scores (sums of about 3 million instead of about 5,000); fixed with explicit `if` branches. `run_check_pool.py`: four cases with random scores, ties, 10 / 6 / 1 known classes: **0 names differing, PASS**; `run_check_sleep_clean.py` now also feeds the RTL's own scores and neighbours to the pooling unit: **0 score rows, 0 neighbour rows, 0 names (software or pooling unit) differing, PASS**. Both are in `hw/run_all_checks.sh`.
Operation counts for one cleaning pass over a buffer of 64 pictures with 4,608-bit picture codes (ESTIMATED from the RTL's cycle counts, not measured on silicon): per picture one PREDICT (about 250 active bits x 10 class reads: 2,500 small adds), the neighbour search (64 slots x about 400 merge cycles, about 26,000 compares and counter steps) and the pooling (about 100 adds and compares); about 1.7 M cycles per buffer (17 ms at 100 MHz) and no multiplies anywhere; the heavy part is the all-pairs overlap, which grows with the square of the buffer size. The grouping itself (competitive learning for the label-free categories) is not in RTL.


## 20 Oct 2026 (night) - F7 DONE: the chip notices new classes by itself with two senses (SIMULATED, 2 seeds; `brain_strict_novel2.py`, logs `brain_strict_novel2_{fsdd,sc}.log`)

The chip knows digits 0-7 (joint picture + sound table, 4 stages with dreams). An UNLABELLED stream of pairs follows (1,000 per digit; 20 % are digits 8 and 9 it has never met, with sounds of words it does not know). (1) a pair is flagged when the top score of the joint code falls below the 10th percentile of known pairs' top scores; (2) the flagged pairs form groups (k-means by overlap, up to 6 groups); (3) each group is named by one label (majority of 5 members), a group named with a known digit merges into it; (4) the flagged pairs are learned under the group names, sleep-cleaned by neighbour pooling, as one stage with dreams of the old classes.
FSDD pair / Speech Commands pair: novelty AUROC of the joint top score **0.960 / 0.966** (margin 0.965 / 0.966; picture bits alone 0.57 / 0.53, sound bits alone 0.65 / 0.77: the two senses together are what separates the new from the known); flag recall 90.6 % / 89.4 %, **flag precision 99.2 % / 99.3 %** (the earlier picture-only recruitment filled its new slots with known items; here only about 1 % of the flagged pairs are wrong); group names right 98.5 % / 97.1 %, after sleep cleaning 98.8 % / 98.2 %. After learning the new classes: all 10 digits (both senses at test) **93.65 / 97.32**, new digits 8 and 9 alone **87.9 / 98.3**, old digits 0-7 after 95.1 / 97.1; oracle with the true labels for the whole stream: 96.77 / 97.63, new 95.5 / 95.8, old 97.1 / 98.1. So the chip finds the new classes itself and learns them to within 0.3-3 points of the oracle (the Speech Commands pair matches it: 97.32 vs 97.63, new digits even higher), without forgetting the old ones. Caveats: digits only; the flag threshold comes from known pairs; the grouping runs as host-side k-means (not in RTL); the new classes were named with a handful of labels (up to 6 groups, one label each), not with none.

## 20 Oct 2026 (night) - Last attempt on the staged clothing loss: more passes over the stage's own examples FAILED; F5 and F10 closed as documented limits (SIMULATED, 5 seeds; `staged_epochs.py`, `staged_epochs.log`)

Showing the current stage's own examples 1 / 2 / 3 times (shuffled, dreams of old classes each time, no stored past data): clothing staged **83.18 / 82.02 / 81.55** (worse), digits 94.87 / 95.24 / 94.85 (flat). More training volume on the new classes does not repair the old-vs-new boundaries that were only fitted against dreams. Final position on the staged loss: about a dozen replay, regularisation and repetition ideas failed or traded off (see the entries above); only a second sense lifts staged accuracy (digits +1.1 to +2.2), and stored real traces recover it fully only at about 4 MB (1,000 per class); so the clothing staged floor (83-84 vs 86.55 one pass) is a documented limit of this design without a second sense. F10, the one-pass gap to a trained CNN on the same data (clothing 86.55 vs 88.8, digits 97.47 vs 98.55, 20 words about 75 vs 77.05, MEASURED ruler), is likewise a documented limit: the single-layer code saturates near 88 (nonlinear readout 88.35), the finer code reaches 88.1 one pass but loses staged accuracy and doubles the reads, and every richer code or local rule tried was negative or traded off.

## 20 Oct 2026 (night) - F9 IMPROVED: new words learned through the pictures seen with them (SIMULATED, 3 seeds; `brain_strict_novel2.py` F9 arms, logs `brain_strict_novel2_f9_{fsdd,sc}.log`)

Reopened because a second source of evidence changed what is possible. The F7 pipeline (flag the unfamiliar pairs, group them, name each group with one label, sleep-clean the names) learns the new digits 8 and 9 from an unlabelled stream where each unfamiliar word is heard together with a picture; a SOUND-ONLY learner is then trained on the flagged pairs' sound codes under the cleaned names (staged with dreams of the known words) and tested on held-out speakers with sound alone. New words 8 and 9 from sound alone, FSDD pair / Speech Commands pair: **56.4 / 71.3** learned through the pictures seen with them; baseline with 5 labelled recordings of each new word only **10.1 / 33.6**; oracle (true labels for the whole stream, sound-only learner) 41.7 / 68.2. All 10 words from sound alone 67.1 / 79.6; known words 0-7 after 69.9 / 81.7 (not forgotten). So a new spoken word learned while its object is seen reaches 2-5 times the accuracy of learning it from 5 recordings, and matches the oracle trained on the same stream with all labels. This is a different regime from the 1-5-recording test (the stream here has 1,000 unlabelled exposures per class, which only the picture makes usable), so the older numbers (50.2 / 56.4 / 62.3 over all ten words) still stand for the case with no picture. Caveats: digits only; grouping is host-side k-means.

## 20 Oct 2026 (night) - F10 IMPROVED: a second look closes most of the one-pass gap to the CNN at a fraction of the reads (SIMULATED, 3 seeds, margin 256 / 1,500 dreams / 1 night; `second_look.py`, logs `second_look.log`, `second_look_v1.log`)

Two counting tables learn in parallel: A on the shipped coarse code (4,608 bits, about 265 active) and B on the finer 3x3 / stride 1 code (8,192 bits, about 544 active). Table A answers; when its top-2 margin is among the lowest (a share set from the UNLABELLED margin distribution of the stream: no labels used) the fine code is read too and the scores of A and B are added. Clothing one pass / staged, mean active bits read per decision: coarse only **86.55 / 83.27** (265); fine only 88.13 / 82.85 (544); both always 88.20 / 83.73 (810); **second look on 20 % of the inputs 88.03 / 83.72 (374 bits, +41 % reads)**; on 40 % 88.20 / 83.75 (483); 60 % 88.20 / 83.73 (592); 80 % 88.20 / 83.73 (701). Digits one pass / staged: coarse 97.47 / 95.52 (245); both 98.10 / 95.52 (710); second look 20 % 98.10 / 95.53 (338). So at a 20 % second look clothing one pass reaches 88.03 against 88.8 for the trained CNN on the same data (MEASURED ruler): the gap is 0.8 points (was 2.3), digits 98.10 vs 98.55 (was 1.1 -> 0.45); staged clothing improves by +0.45 and digits are unchanged, so the no-regression rule is passed for images (words have no fine-code table: not applicable). This is the "second look" of the brain (look again where unsure) and it is the first use of the finer code that does not lose staged accuracy. Cost: the second table (fine code 8,192 bits with its own fast / slow tables and dream counts) is roughly 1.8x the memory of the first, so about 2.8x the one-table chip; an ASIC option, not the FPGA build. Not in RTL yet.

## 20 Oct 2026 (night) - F5 once more: modality dropout with a class-name code FAILED (SIMULATED, 3 seeds; `staged_dropout.py`, `staged_dropout.log`)

Each class has a stand-in "heard name" (a fixed 64-of-1,024-bit pattern, 10 % of its bits flipped each time); the chip learns picture + name code, the name code missing from a share DROP of the learning examples (and dreamed at the same rate); tested with the PICTURE ALONE, 5 stages, margin 256 / 1,500 dreams / 1 night. Clothing one pass / staged: picture alone (shipped) **86.55 / 83.27**; DROP 0: 64.47 / 62.95; 0.5: 85.20 / 66.75; 0.8: 86.40 / 81.67. Digits: 97.47 / 95.52; 76.95 / 73.67; 96.65 / 87.93; 97.08 / 94.62. The name bits become a shortcut that satisfies the table's margin, so the picture bits under-learn; high dropout only returns to the baseline, never above it. FAILED: the staged clothing floor (83-84 against 86.55 one pass) stands after this attempt too (second look: +0.45 staged, see above).

## 20 Oct 2026 (night) - F5: what limits the staged loss, and a different class of idea (boundary dreams) that also fails (SIMULATED, 3 seeds; rule `bdream` in `cortex_rules.py`)

**What limits it (from our own measurements).** (1) The dreams carry the retention: clothing 44.8 with no dreams, 83.3 with them, 87.1 with every earlier real example replayed, so the loss is the quality of the dreamed data. (2) It is not a class-balance problem (each class already wins its fair share of decisions; a per-class bias gained at most +0.6), not table capacity (one pass reaches the float readout ceiling of this code), not detector coverage, not code size (a finer code loses more in stages). (3) A dream is drawn from per-bit averages, so it is a *typical* sample of its class (near the class centre); the old-versus-new decision boundary is set by the *tails* of both classes, where they overlap (shirt / T-shirt / pullover / coat are the worst classes), and the new class only ever meets the old class through those typical dreams. (4) Every dream reshaping (per-cell winners, cut-and-paste, noisy, correlated) stays typical and changed nothing; real examples, which contain the tails, recover everything (1,000 per class: clothing 86.82; about 4 MB). Root cause: **the old class's tail samples are not represented in the dream memory, because per-bit counts do not encode where the class's tail lies**; to put them back the chip needs either stored real tail data (memory) or independent evidence (a second sense: digits +1.1 to +2.2; a second look: +0.45).
**Different class of idea: dream the boundary** (`bdream`): with probability BMIX/16 an old-class dream has each 32-bit cell replaced, with probability BLAM/16, by the cells of the current new-class example, label kept as the old class (a sample in the overlap region made from the dream and today's example only, no stored old data). Clothing staged / digits staged vs shipped 83.27 / 95.52: BMIX 8, BLAM 4: 82.03; 16 / 4: 81.90; 8 / 8: 80.05; 8 / 2: 83.07 / 95.65; 4 / 2: 83.42 / 95.77; 4 / 1: 83.20 / 95.50. Strong boundary dreams hurt (the table learns that cells of the new class still mean the old class), gentle ones are within noise. FAILED: the staged clothing floor stands; it is limited by the missing real tail data, not by how the dreams are shaped.

## 20 Oct 2026 (night) - F5: three unused brain principles, all FAILED (SIMULATED, 3-5 seeds; rules `schema`, `real` + `DAYBUF`, `reverse` in `cortex_rules.py`)

Shipped staged clothing / digits: 83.27 / 95.52 (3 seeds), 83.18 / 94.87 (5 seeds). (1) **Schema assimilation** (a new class starts as a copy of the table row of the known class its examples score highest on, so only the differences are learned): clothing **82.03**, digits 94.67 (5 seeds). (2) **Hippocampal day buffer** (only the current stage's real examples are kept, replayed at night against dreams of the old classes, erased after the night; consolidation guaranteed): 100 / 500 examples clothing **81.25 / 81.30**, digits 95.37 / 95.70. Replaying the new class's real examples pushes the boundary toward the new class and costs the old ones. (3) **Reverse learning in REM sleep** (Crick and Mitchison: dream a mixture of two known classes, which should be ambiguous, and step the winner's synapses down when the table answers it with a top-2 margin above mu): mu 256 / 128 / 64 clothing 73.5 / 50.1 / 34.9, digits 91.9 / 78.9 / 48.4; 4,000 steps per class even worse; mu 1024 / 2048 never fires (no unlearning) and still gives 81.73 / 95.43 because the extra consolidation steps alone cost clothing about 1.5 points (forcing the slow table to converge fully hurts clothing; this matches the earlier finding). Together with boundary dreams, modality dropout, more passes and about a dozen replay, regularisation and gating ideas, the staged clothing floor stands; its cause is the missing real tail data (previous entry).

## 20 Oct 2026 (night) - F5: surprise-tagged TAIL MEMORY lifts staged clothing +1.3 (SIMULATED, 5 seeds; rule `tailmem` in `cortex_rules.py`)

A brain concept altered for the chip: surprising events are tagged and consolidated more strongly (amygdala-hippocampus). In the chip: whenever the table has to WRITE on a real example (it was surprised: near a boundary or wrong) the example also updates a second set of per-bit counts for its class, the tail memory (`ont`, `nt`, the same bounded counters as the dream memory); a share TMIX/16 of the dreams (day and night) is drawn from the tail counts when the class has any, the rest from the usual counts. It fills with exactly the near-boundary examples that the typical counts average away, answering the root cause (previous entry); it is counts, not stored examples, and costs one more dream-count array (about +57 KB at 4,608 bits, about +45 % of the chip).
Shipped staged, 5 seeds: clothing 83.18 / digits 94.87. Share 2/16: 84.44 / 94.61; **3/16: 84.52 / 95.90**; **4/16: 84.53 / 95.27**; 5/16: 84.25 / 94.59; 6/16: 84.34 / 93.91 (3 seeds: 8/16 84.88 / 93.57; 16/16 68.25 / 91.87). One pass is unchanged (86.35-86.62 vs 86.69). So a share of 3-4/16 gives **+1.3 on clothing** with digits at or above the baseline (+1.0 / +0.4): the first robust improvement of the staged loss without stored examples. The words leg of the no-regression rule is running (`brain_strict_tail20.log`, `brain_strict_tail35.log`).

## 21 Oct 2026 (early) - F5 words leg: tail memory passes the no-regression rule (SIMULATED, 3 seeds, rule `tailmem`, `brain_strict_sound.py` arms `tail:N`)
**Asked:** does the tail memory (share N/16 of dreams drawn from a second on-count memory updated only when the table writes) also hold for spoken words, and if so adopt it.
**Result (staged, 3 seeds):** 20 words, share 3/16: clean **74.15** (was 73.35), oldest **81.82** (was 77.49), newest 59.39 (57.09), twin 70.53 (69.08). Share 4/16: 73.27 / 75.32 (worse than 3/16). 35 words, share 3/16: clean **68.53** (was 68.29), oldest **70.95** (68.81), newest 56.97 (60.76, lower), twin 65.92 (65.17); share 4/16: 68.99 / 69.05 / 60.52. 3/16 passes rule 12 on both vocabularies (clean up, oldest not lower); newest at 35 words falls, a trade we state. Images: clothing +1.3, digits +1.0 at 3/16 (earlier entry). **Adopted: TMIX = 3/16 as an option, cost about +57 KB memory (second count table).** Not in RTL yet.
**Files:** `hw/brain/experiments/month4/brain_strict_tail20.log`, `brain_strict_tail35.log`, `tail20.json`.

## 21 Oct 2026 - Reliability-weighted cue combination across senses (brain concept: inverse effectiveness / cue weighting by reliability) (SIMULATED, 3 seeds, MNIST + spoken digits, `brain_strict_cuecomb.py`)
**Concept altered for the chip:** the brain weights each sense by how reliable it is right now. Chip version: one table per sense (same total memory as the joint table); each sense's confidence = its top-2 score margin divided by its typical margin (running median on clean data), rounded to a power of two; the sense with the larger confidence is the reference and the other sense's scores are shifted left relative to it (shifts and adds, **no multiply**).
**Result (accuracy, joint table / plain sum / shift-weighted):** clean 98.33 / 98.60 / **98.87**; picture 25 % dropped 97.45 / 97.42 / **98.40**; picture 50 % dropped 94.60 / 94.65 / **96.18**; both 25 % dropped 98.08 / 98.08 / **98.45**. **Trade:** sound 50 % dropped 98.60 / 99.20 / 98.85 (plain sum is best there). Closes about half the gap to the small CNN on damaged input (reference 99.25). Not in RTL yet; the host-side order of operations is two core score reads plus a shift-add combiner (small).
**Files:** `hw/brain/experiments/month4/brain_strict_cuecomb.py`, `brain_strict_cuecomb.log`.

## 21 Oct 2026 - Second look for spoken words, 20 words (SIMULATED, 3 seeds, staged, margin 256 / 1,500 dreams / 1 night; arm `look:N` in `brain_strict_sound.py`)
**Asked:** try the second look (F10 concept: a second table on a finer code consulted for the least-sure inputs) on words. Fine code = same cochlea picture, 3x3 windows, stride 1, pooled 3x3 (`geom:3:3:1:1:3:3`).
**Result (clean / oldest / newest):** coarse (shipped) 73.35 / 77.49 / 57.09; fine alone 72.30 / 75.32 / 59.77; second look for 20 % least-sure 75.44 / 80.52 / 61.69; 40 % **75.93** / 80.52 / 62.45; 60 % 75.85; both always added 75.85 / 80.09 / 62.45. At 5 dB: 39.5 -> 40.8 (20 %) / 41.9 (40 %) / 42.8 (sum). Passes rule 12 at every share. CNN ruler 77.05 (all at once). Cost: second table on the fine code, about 2x sound memory (ASIC option, not in RTL). 35-word leg still running (`brain_strict_look35.log`).
**Files:** `hw/brain/experiments/month4/brain_strict_look20.log`, `look20.json`.

## 21 Oct 2026 - Second look for words, 35 words (SIMULATED, 3 seeds, staged, same settings)
**Result (clean / oldest / newest):** coarse 68.29 / 68.81 / 60.76; fine alone 66.57 / 71.67 / 58.16; second look 20 % **70.66** / 72.38 / 61.23; 40 % 70.71 / 73.33 / 61.47; sum 70.76 / 73.57 / 61.47. At 5 dB: 27.4 -> 27.8 (20 %) / 28.8 (40 %); 10 dB 39.8 -> 41.6 (20 %) / 42.3 (40 %). Passes rule 12 on both vocabularies (+2.4 at 35 words, +2.1 to +2.6 at 20); the CNN ruler is about 72.5 at 35 words. Words still ASIC option (about 2x sound memory), not in RTL. Next: stack with tail memory (not yet tested together).
**Files:** `hw/brain/experiments/month4/brain_strict_look35.log`, `look35.json`.

## 21 Oct 2026 - Stacking tail memory + second look on words: NOT additive (SIMULATED, 20 words, 3 seeds, `STACK=1` in `brain_strict_sound.py`)
**Result (clean / oldest / newest):** tail memory in both tables, coarse alone 74.15 / 81.82 / 59.39 (as before); second look 20 % 74.80 / 80.95 / 60.15; 40 % **75.04** / 81.82 / 60.15; sum 74.96. Second look alone (no tail memory) was 75.93 at 40 %, so the stack is about 0.9 **worse** than the second look alone and only 0.9 above the tail memory alone: both fix the same weakness (typical-vs-tail boundary), so gains overlap. Decision: for words, the second look alone is the better option (75.9 / 70.7 at 20 / 35 words); tail memory alone is the cheaper one (+57 KB, 74.15 / 68.53). The 35-word stack run was killed twice by container restarts and not repeated.
**Files:** `hw/brain/experiments/month4/brain_strict_stack20.log`, `stack20.json`.

## 21 Oct 2026 - Tail memory in the RTL core, bit-exact (SIMULATED RTL; `run_check_cortex_tail.py`, step 1 of the plan)
**What was built:** no new memory block: the CORTEX_CONTEXT build's frozen-copy memory (`fmem`, `fn`) doubles as the tail memory. New command **op 0 TAILCOUNT** counts the loaded list into the tail counts of class arg (same count and halve-when-full path as LEARN, writing the tail memory; no table update); the host issues it after a LEARN whose update wrote (`updated`). **DREAM with cmd_frozen** (op 8 in the test) draws from the tail memory. CLEAR now also zeroes the tail memory (the first check run hung for this reason: unknown values in the tail counts made a dream loop forever; found by a 3-example scenario).
**Model change:** the dream's choice of source is now a fixed pattern (dream number t uses the tail memory when the class has a tail and t mod 16 < 3) instead of a random draw, so the host schedule can reproduce it. Re-tested at 5 seeds (SIMULATED): clothing staged 84.73 (shipped 83.18), digits staged 95.38 (94.87); both above shipped.
**Check:** scenarios with 10-, 5-, 4- and 3-bit counters (the last two make the tail counts halve), 805-811 commands each: 0 mismatches; also with the pipelined core; the old context check still passes with the changed core. Added to `hw/run_all_checks.sh` (two lines). Full regression rerun started because the core changed.
**Files:** `hw/rtl/cortex/cortex_core.v`, `run_check_cortex_tail.py`, `tb_cortex_core_ctx.v` (op cast only), `hw/brain/cortex_rules.py`.

## 21 Oct 2026 - Plan steps 2 and 3: digits one-pass gap and readout precision (SIMULATED, 3 seeds): LIMITS, no gain
**Digits one pass (98.10 vs CNN 98.55):** fine table alone 98.03; coarse + fine summed 98.10; second look 20-80 % all 98.10; shift-weighted sum of the two tables 98.07 (`second_look_w.py`). The second look has plateaued at 98.10: the gap left (0.45) is not closed by combining these two codes. Recorded as a limit.
**Readout precision (count range CMAX, margin 256 / 1,500 dreams / 1 night; one pass / staged):** clothing CMAX 7: 85.98 / 82.05; 15 (shipped): 86.55 / 83.27; 31: 86.78 / 82.60; 63: 86.73 / 83.10. Digits 7: 96.95 / 94.47; 15: 97.47 / 95.52; 31: 97.45 / 95.42; 63: 97.55 / 95.47. Wider counts move one-pass results by at most +0.2 and make staged results no better; 5-bit is the sweet spot, so **the 1-2 point gap to a float readout is not a precision problem**. No change to the shipped 5-bit table. `CMAX` env added to `brain_strict_rules.py`; log `readout_cmax.log`.

## 21 Oct 2026 - Regression after the tail-memory core change: 32 of 32 checks PASS (SIMULATED RTL)
All checks in `hw/check_summary.txt` pass on the changed core (two new tail-memory checks, plain and pipelined; whole two-sense chip 9,270 lines, 0 mismatches; sound chain 23,082 lines, 0 mismatches; board design and host schedule). Run notes: the container was reclaimed whenever the session sat idle (about every 20-30 minutes), which killed background runs; the resumable runner kept finished checks and the three longest checks were run one at a time inside an active turn. Next in plan step 1: cue-weighting combiner and second look in RTL.

## 21 Oct 2026 - Cue-weighting unit in RTL, bit-exact (SIMULATED RTL; `cortex_cue.v`, `run_check_cue.py`, model `cross_modal.cue_combine`; plan step 1)
**Unit:** per sense, margin = top score minus runner-up among the known classes; confidence index = how many of 7 host-loaded ascending thresholds (typical clean margin x 2^(k-0.5), k = -3..3) the margin reaches (compares only); combined score = score A << (iA - min) + score B << (iB - min); prediction = first known class with the top combined score. Shifts, adds and compares: no multiplier, no divider; purely combinational (20-bit scores, 29-bit combined).
**Design note (a failed variant):** a divider-free "bit-length difference" index (floor log2) halves the gain (picture 25 % damaged 97.9 vs 98.4); thresholds loaded by the host keep the full gain, so they are what the chip uses.
**Check:** 1,200 random cases over 10 / 6 / 3 / 2 / 1 known classes, ties, extreme scores and a repeated threshold: 0 differences. **Accuracy with the chip's exact combiner (3 seeds, MNIST + spoken digits):** clean 98.87 (joint table 98.33, plain sum 98.60); picture 25 % dropped 98.40 (97.45 / 97.42); picture 50 % dropped 96.18 (94.60 / 94.65); both 25 % dropped 98.45 (98.08); sound 50 % dropped 98.85 (plain sum 99.20 is better there). Added to `hw/run_all_checks.sh` (33 checks).
**Files:** `hw/rtl/cortex/cortex_cue.v`, `tb_cue.v`, `run_check_cue.py`, `hw/brain/cross_modal.py`, `hw/brain/experiments/month4/brain_strict_cuecomb.py` and `.log`.

## 21 Oct 2026 - Second look in the RTL, bit-exact (SIMULATED RTL; `cortex_look.v`, `run_check_look.py`, `run_check_look_top.py`; plan step 1 complete)
**Unit:** table A (coarse code) answers alone when its top-2 margin among the known classes is at least a host-loaded threshold TH (a percentile of A's margins on unlabelled data); otherwise the fine-code table B is consulted and A + B scores are added; first known class wins ties; compares and adds only. Model twin `cross_modal.look_combine`.
**Checks:** (1) the unit alone, 1,400 random cases (10 / 6 / 3 / 2 / 1 known classes, ties, thresholds from 0 to above every margin): 0 differing. (2) Integration: two `cortex_core` instances with different code widths (coarse and fine; tables imported over the MEM interface) + the unit: class scores, look flag and decision for random code lists equal the model, 240 cases, 4 thresholds: 0 differing. **Bug found and fixed on the way:** a `?:` mixing the signed score difference with an unsigned constant zero-extended the difference (same class of bug as the pooling unit's); explicit branches fix it. Added both to `hw/run_all_checks.sh` (35 checks). A full regression rerun is still owed after the last RTL additions (the core is unchanged since the 32/32 pass; the new modules are separate files).
**Files:** `hw/rtl/cortex/cortex_look.v`, `tb_look.v`, `tb_look_top.v`, `run_check_look.py`, `run_check_look_top.py`.

## 21 Oct 2026 - Full regression after all RTL additions: 35 of 35 checks PASS in one uninterrupted run (SIMULATED RTL)
`sh hw/run_all_checks.sh DATA_DIR` (fresh, no resume, kept running inside an active turn, about 1.3 hours): 35 PASS, 0 failures, 0 skipped. It includes the tail-memory core (plain and pipelined), the cue-weighting unit, the second-look unit and the two-core second-look integration, plus every earlier check on the changed core. This closes the plan's step 1.

## 21 Oct 2026 - Noisy-copy training at the shipped settings and at 35 words: closes most of the noise weak spot (SIMULATED, 3 seeds, staged, margin 256 / 1,500 dreams / 1 night; `brain_strict_noisecopies.py`)
**What:** in every stage the chip learns each clean clip and then one noisy copy of it (SNR 20 / 10 / 5 dB at random). No extra memory (the table and dream memory are the same size); the cost is double the training examples. The noise stands for a chip that hears speech in varying noise during its day (the simulator adds it).
**Result (clean / 20 / 10 / 5 dB / oldest / newest):** 20 words: shipped 73.35 / 65.70 / 51.53 / 39.53 / 77.49 / 57.09; **with noisy copies 73.59 / 74.15 / 65.94 / 59.02 / 77.49 / 66.28**. 35 words: shipped 68.29 / 56.53 / 39.84 / 27.43 / 68.81 / 60.76; **with noisy copies 69.83 / 64.02 / 52.67 / 42.82 / 73.57 / 62.88**. Passes rule 12 on both vocabularies (clean up, oldest not lower); the newest words also rise (+9.2 at 20 words, +2.1 at 35), so the noisy copies also act like extra tail examples. The earlier control (the same clean clips twice) showed more data alone explains only part of the gain.
**Files:** `hw/brain/experiments/month4/brain_strict_noisecopies.py`, `brain_strict_noisecopies20.log`, `35.log`, `brain_strict_noisecopies_20.json`, `_35.json`. Next: stack with the second look.

## 21 Oct 2026 - Stack: noisy-copy training + second look on words (SIMULATED, 3 seeds, staged, shipped settings; `brain_strict_noisecopies_look.py`, logs `nl20.log`, `nl35.log`)
Both tables (coarse and fine code) learn each clean clip and one noisy copy (SNR 20 / 10 / 5 dB at random) per stage; second look for the least-sure share of test clips; test on clean and white noise. Columns: clean / 20 / 10 / 5 dB / oldest / newest.
**20 words:** shipped 73.35 / 65.7 / 51.5 / 39.5 / 77.5 / 57.1; second look 40 % alone 75.93 / 66.3 / 54.6 / 42.0 / 80.5 / 62.5; noisy copies alone (coarse) 73.59 / 74.2 / 65.9 / 59.0 / 77.5 / 66.3; **stack, look 40 %: 75.68 / 75.2 / 68.8 / 61.9 / 81.8 / 72.8**.
**35 words:** shipped 68.29 / 56.5 / 39.8 / 27.4 / 68.8 / 60.8; second look 40 % alone 70.71 / 57.6 / 42.3 / 28.8 / 73.3 / 61.5; noisy copies alone 69.83 / 64.0 / 52.7 / 42.8 / 73.6 / 62.9; **stack, look 40 %: 72.43 / 67.3 / 57.6 / 47.2 / 77.9 / 66.2** (both tables always summed: 72.48 / 67.9 / 58.9 / 48.8 / 77.9 / 66.2).
**Reading:** at 35 words the stack reaches the CNN ruler (about 72.5) on clean speech and lifts 5 dB from 27.4 to 47.2 and the oldest words from 68.8 to 77.9; at 20 words it stays 1.4 below the CNN (75.7 vs 77.05) but 5 dB goes 39.5 -> 61.9 and the newest words 57.1 -> 72.8. Rule 12 passed on both vocabularies. Noisy copies also stack with the second look (unlike the tail memory, which overlapped with it). Cost: about 2x sound memory (second table), double the training examples; the noise is added by the simulator.

## 21 Oct 2026 - Noisy-copy training on images: FAILS rule 12 on clothing (SIMULATED, 3 seeds, 5 stages, margin 256 / 1,500 dreams / 1 night; `brain_strict_imgcopies.py`, log `brain_strict_imgcopies.log`)
**Asked:** does the noisy-copy training that fixed words also lift staged clothing (84.7 vs 86.6 one pass)? In every stage the chip learns each clean image and then one altered copy (drop = 10 % of lit pixels removed, gauss = pixel noise sd 25, shift = moved one pixel, mix = one of the three).
**Result (staged, clean test / test with 25 % of lit pixels removed):** clothing: none (shipped) **83.27** / 73.40; drop 81.05 / 77.62; gauss 81.10 / 76.48; shift 81.37 / 74.03; mix 81.15 / 76.53. Digits: none 95.52 / 92.18; drop 95.23 / 92.62; gauss 92.00 / 86.80; shift **95.68** / 92.53; mix 92.98 / 88.53.
**Verdict:** every copy type **lowers** staged clothing by about 2 points on clean images (rule 12 needs at least 83.3), although it helps damaged images (+3 to +4). Only digits with shifted copies pass (+0.16, within noise). Words gain because noise varies the class tails; clothing classes are crowded, so altered copies of one class land on its neighbours. Not adopted for images. Recorded as a failure.

## 22 Oct 2026 - SCALE TEST: more training data (SIMULATED, 2 seeds, full 10,000-image test sets, margin 256 / 1,500 dreams / 1 night; `brain_strict_scale.py`, logs `brain_strict_scale_full.log`, `_full60k.log`, `_ndream.log`)
**Question:** does the chip hold up with more data? (Earlier tests used 2,000 images per stage = 10,000 training images in total.)
**Result (one pass / staged, shipped table; tail memory in brackets):** clothing 10,000 images 86.55 / 83.27; **30,000 images 86.98 / 79.41 (tail 87.00 / 80.89); 60,000 images 87.31 / 77.98 (tail 87.10 / 77.51)**. Digits 10,000: 97.47 / 95.52; 30,000: 97.79 / 94.61 (tail 97.73 / 95.64); **60,000 (59,063 usable): 97.88 / 93.42 (tail 97.83 / 94.35)**.
**Reading:** (1) the one-pass result improves only a little with six times the data (+0.8 clothing, +0.4 digits): the 5-bit table and the code, not the data, set the one-pass ceiling. (2) **Staged learning gets WORSE as the stages get bigger** (clothing 83.3 -> 78.0, digits 95.5 -> 93.4), so the staged claims hold for small stages (2,000 images per stage) and must be stated with that condition. The tail memory recovers about 1 point at 30,000 and nothing at 60,000 clothing. (3) Settings do not fix it at 60,000 clothing: dreams per old class per stage 1,500 / 6,000 / 15,000 -> 77.98 / 77.82 / 77.46; counter width 10 / 12 / 14 bits 77.98 / 77.99 / 78.26; margin 64 / 256 / 1024 -> 77.95 / 77.98 / 77.12; all together 78.46. So it is not the dream count, the counter range or the update margin: with big stages the new classes are learned from far more real examples than the dream memory can match (the dream memory keeps only per-bit rates, not class tails). A GPU network in stages without stored examples scores about 20 %, so the chip is still far ahead there, but the absolute loss versus one pass grows to 9 points at 60,000 clothing images.
**Pitch consequence:** state the staged numbers with the condition "2,000 images per stage". Not fixed.

## 22 Oct 2026 - Scale fix: the slow-table follow interval scales with the stage size (SIMULATED, 3 seeds, full 10,000-image test sets; `brain_strict_scale.py` with `CHK=auto`, logs `brain_strict_scale_auto.log`, `brain_strict_scale_chk.log`, `_ndream.log`)
**Finding:** the staged collapse at scale (previous entry) is a consolidation-timing problem. At 60,000 clothing images staged: follow interval ch 20 / 100 (shipped) / 300 / 500 / 1,000 / 2,000 / 5,000 -> 77.6 / 77.98 / 80.1 / 81.6 / 82.4 / 81.4 / 78.6; slow-table rate K 3 / 5 / 7 -> 77.9 / 78.0 / 79.8; extra night passes 78.1. But a single ch is not right for both datasets (ch 1,000 helps clothing and hurts digits: 91.9 at 60,000; ch 700 at 30,000: 89.1), so a per-dataset ch would break rule 12.
**Rule (one fixed host schedule, uses only the stage size the host already knows, no dataset switch):** follow every max(100, stage size / 30) real examples (100 at 2,000 per stage, 200 at 6,000, 400 at 12,000). No RTL change: the host already decides when to issue FOLLOW.
**Result, staged (base / with tail memory) vs the shipped fixed interval of 100:** 30,000 images: clothing 81.21 / 82.46 (79.41 / 80.89), digits 95.43 / 96.30 (94.61 / 95.64); **60,000 images: clothing 81.01 / 81.05 (77.98 / 77.51), digits 95.60 / 96.63 (93.42 / 94.35)**. One pass is unchanged by the rule (60,000: clothing 87.63 / digits 97.92). Staged accuracy now stays about level from 10,000 to 60,000 images (clothing about 81-82, digits 95.4-96.6) instead of falling; the gap to one pass at 60,000 clothing is still 6.6 points. Rule 12 at the usual size is unchanged (the rule gives 100 there).

## 22 Oct 2026 - CNN ruler at 60,000 training images (MEASURED, one seed, CPU, 4 epochs; `gpu_baseline_scale.py`, `gpu_baseline_scale.log`; never in the chip)
Same 60,000 training images in 5 stages of 2 classes, the full 10,000 test images. Small CNN (2 conv + 1 hidden layer, Adam, float32), all classes together 4 epochs: **clothing 90.96, digits 98.87**; in 5 stages with no replay (2 epochs per stage): **19.95 / 19.50**.
**Against the chip at 60,000 images (SIMULATED, 3 seeds):** one pass 87.63 / 97.92 (gap to the CNN 3.3 / 0.95; at 10,000 images the gap was 2.2 / 1.1, so the clothing gap grows with data); staged with the new follow-interval rule 81.01 / 95.60 (with tail memory 81.05 / 96.63) against the CNN's 19.95 / 19.50 without help. Reading: **strong** at learning in stages with no stored examples (4 times the CNN); **weaker on clothing when all the data is available at once** (3.3 points behind at 60,000 images, the 5-bit table and the code limit the one-pass result). Caveat: the CNN had only 4 epochs on a CPU, so its numbers are slightly below what a longer GPU run would reach.

## 22 Oct 2026 - Second look at 60,000 training images (SIMULATED, 2 seeds, full 10,000-image test sets, follow interval max(100, stage size / 30); `second_look_scale.py`, `second_look_scale.log`)
Table A on the coarse code, table B on the finer code (3x3 patches, stride 1, pooled 3x3), the second look for the least-sure 20-80 % of inputs (A + B scores added).
**Clothing:** one pass coarse 87.58, fine alone 88.63, second look 20 % **88.93** (40 % 88.89; always both 88.90); staged coarse 81.01, fine 82.08, second look 40 % **82.48** (20 %: 82.33). **Digits:** one pass coarse 97.92, fine 98.30, second look **98.45**; staged coarse 95.56, fine 94.65, second look 95.77.
**Against the CNN ruler at 60,000 images (MEASURED, 4 epochs, CPU: clothing 90.96, digits 98.87):** the one-pass gap closes from 3.4 to **2.0** points on clothing and from 0.95 to **0.4** on digits; the second look reads about 40-50 % more bits per decision (clothing 374 vs 265 at a 20 % share) and about 2.8x the table memory (ASIC option; the decision unit is in RTL). Staged: +1.5 on clothing, +0.2 on digits. The 20 % share is as good as always reading both, so the extra reads can be kept small.

## 22 Oct 2026 - Stored real examples at 60,000 images: does NOT close the staged gap (SIMULATED, 2 seeds, follow interval max(100, stage size / 30); arm `real:E:mix` in `brain_strict_scale.py`, log `brain_strict_scale_real.log`)
**Variant (breaks the "no stored examples" claim, so labelled as a variant):** after each stage the chip keeps the E hardest real examples per class and replays them in the night (mix / 16 of the replays; the rule of the earlier hard-example tests).
**Clothing staged (shipped 81.01):** E = 8: 80.97; 32: 80.94; 128: 81.46; 512 (mix 8 / 16): 81.53 / **81.97**; 2,048 (mix 8 / 16): 81.45 / **82.02**. Digits staged (shipped 95.56): E = 128, mix 16: **96.20**; E = 2,048: 95.91.
**Reading:** even 2,048 stored images per class (about 8.6 MB at 784 bytes, 100x the 84 KB table and dream memory) lift 60,000-image staged clothing by only 1.0 point of the 6.6-point gap to one pass (87.58); digits gain +0.6 with 128 per class. So the staged gap is **not mainly a missing-tails (memory) problem at this scale**: in the one-pass run all ten classes compete in the table while each is learned; in stages the new classes never compete with real old examples during the day, and a short night of replay does not recreate that. Storing examples is therefore not worth its cost; recorded as a failure. The honest options left are interleaving old-class traffic during the new stage (needs a stream of old data, i.e. not continual learning), or accepting ~82 staged.

## 22 Oct 2026 - Threshold unit on the chip, bit-exact (SIMULATED RTL; `cortex_thresh.v`, `run_check_thresh.py`; model `cross_modal.quantile_track`, `cue_thresholds`; study `threshold_unit.py` and `.log`)
**What moved from the host to the chip:** the second-look threshold (a percentile of table A's margins on unlabelled data) and the reference of the cue-weighting unit (the median margin and the 7 thresholds ref x 2^(k-0.5)).
**Rule (compares, adds, shifts only; no sort, no multiply, no divide):** *tracker* q starts at the first sample; for every further sample x: if x < q then q -= (16 - n) << e else q += n << e, saturated to 0..2^21 - 1; the step shift e = max(2, 9 - (count >> 7)) shrinks as samples arrive (floor 2 so the tracker can follow a change of statistics: with floor 0 it stayed at 21,984 after a step from about 500 to about 60,000, with floor 2 it reached 50,048). Stationary point: the share of samples below q is n/16 (n = 3: the 19 % least-sure inputs get the second look; n = 8: the median). *Cue thresholds:* h = (ref x 181 + 255) >> 8 (181 = 128 + 32 + 16 + 4 + 1, i.e. ref x 2^-0.5), then shifted by k = -3..3 with rounding up.
**Accuracy of the estimate (clothing / digits, table A on 10,000 images, unlabelled stream of 10,000 margins):** share 3/16: exact threshold 1,733 / 2,848, chip 1,536 / 2,752 (share of test inputs below it 22.1 % / 21.1 % vs the 18.8 % target: the test margins are lower than the training ones); 6/16: 3,078 / 3,772 vs 3,072 / 3,776; 8/16: 3,832 / 4,332 vs 3,776 / 4,544. Integer cue thresholds differ from the exact ones by at most 3 (clothing) and 2 (digits) out of 339..21,675. 
**Check:** 7 streams and 52 references (steps, saturation at 0 and at the top, n = 1..15): 0 differing. Added to `hw/run_all_checks.sh` (36 checks; a full rerun is owed).
**Still on the host:** the grouping loop of the label-free category step (k-means on joined codes) and the novelty flag threshold (it can now use the same tracker, not yet wired); the schedule of nights and stages.

## 22 Oct 2026 - Full regression with the threshold unit: 36 of 36 checks PASS in one run (SIMULATED RTL)
`sh hw/run_all_checks.sh DATA_DIR` fresh (no resume, run inside an active turn, about 1 hour): 36 PASS, 0 failures, 0 skipped. It includes the tail-memory core, cue-weighting unit, second-look unit and two-core integration, and the new threshold unit, plus every earlier check.

## 22 Oct 2026 - Novelty flag wired to the on-chip threshold, bit-exact (SIMULATED RTL; `cortex_novel` in `cortex_thresh.v`, `run_check_novel.py`; model `cross_modal.novelty_threshold`; experiment `brain_strict_novel2.py` with `THR=chip`, logs `novelty_thr_exact.log`, `novelty_thr_chip.log`)
**What moved:** the host's "10th percentile of the top scores of known pairs" is now found by the chip: during calibration the streaming quantile tracker (previous entry) runs over the top scores of pairs the chip knows (signed scores mapped to ordered unsigned by flipping the sign bit); afterwards a pair is flagged when its top score is below the learned threshold. With n/16 resolution the share is n = 2 -> 12.5 % (not exactly 10 %).
**Check:** 5 score distributions (positive, mixed signs, negative, extreme, n = 1..15), threshold plus 1,540 test scores including values equal to the threshold: 0 differing. Added to `hw/run_all_checks.sh` (37 checks).
**Effect on the two-sense novelty step (digits 0-7 known, digits 8, 9 new, spoken digits, 2 seeds):** flag recall / precision with the exact 10th percentile 90.6 % / 99.2 % (AUROC 0.960); with the chip threshold **91.2 % / 99.2 %**; 1,824 vs 1,838 pairs flagged. Downstream (all 10 digits / new / old): exact 93.65 / 87.87 / 95.13; chip 94.13 / 94.73 / 93.97; oracle 96.77 / 95.47 / 97.11. The flag itself is equivalent; the downstream split between new and old digits moves by about 1-7 points because the grouping step is random and only 2 seeds were run, so I read it as equal within seed noise, not as a gain. The Speech Commands set was not rerun.

## 22 Oct 2026 - Many classes: 20 classes (10 digits + 10 clothing) in 10 stages (SIMULATED chip, 2 seeds, MEASURED CNN; `brain_strict_classes20.py`, `gpu_baseline_classes20.py`, logs `brain_strict_classes20.log`, `gpu_baseline_classes20.log`)
2,000 images per stage of 2 classes, 20,000 training images, the full 20,000 test images; retina detectors learned on the first stage only (digits 0, 1); margin 256 / 1,500 dreams / 1 night; follow interval 100.
**Result (all / digits / clothing):** chip one pass **91.18** / 96.81 / 85.54; chip staged 87.42 / 93.42 / 81.42; chip staged with tail memory **88.44** / 94.48 / 82.39 (one pass with tail memory 91.34). **CNN** (4 epochs, CPU, one seed): all together 90.96 / 97.90 / 84.01; in stages with no help **5.0** / 0.0 / 10.0.
**Reading:** the chip does not fall apart with 20 crowded classes: one pass ties the CNN overall (91.18 vs 90.96; the CNN is better on digits, the chip on clothing), staged learning loses only 3.8 points (2.8 with the tail memory) against a network that keeps only the last stage. The detectors learned from digits alone transfer to clothing.

## 22 Oct 2026 - Integer grouping: fine on the novelty step, NOT ready on the hard grouping test (SIMULATED, 2 seeds)
`cross_modal.kmeans_int` (binary prototypes, majority vote, farthest-first start, 8 iterations, 3 restarts; no floats). **Novelty step** (few groups, easy): group names right 97.3 % vs 98.9 % with the float k-means, names after sleep cleaning 98.7 % vs 98.9 %, final accuracy equal (all 10 digits 94.55 vs 94.13). **Hard test** (`brain_strict_cocluster.py`, 10 groups from scratch, no labels): joined picture + sound purity **41.7 % integer vs 71.3 % float**; names after cleaning 49.5 % vs 84.0 %; picture learner on the cleaned names 50.4 % vs 82.6 % (all-labels reference 97.4 %). So the integer rule loses about 30 points when the groups are hard; the clustering unit waits until a variant closes this (logs `novelty_km_int.log`, `cocluster_float_baseline.log`).

## 22 Oct 2026 - Clustering unit on the chip: integer grouping fixed and bit-exact in RTL (SIMULATED RTL; `cortex_cluster.v`, `run_check_cluster.py`; model `cross_modal.kmeans_int`; variants `kmeans_variants.py`, `kmeans_variants2.py` and logs)
**Failure first (previous entry):** binary prototypes with majority vote reached only 41.7 % purity on the hard grouping test (float 71.3 %).
**Fix:** prototypes keep a level 0..4 per code bit (the member rate times 4) found by compares only (level = #{l in 1..4 : 8 c >= (2 l - 1) m}, the odd multiples by shifts and adds); score = sum of the levels over the pair's bits - (sum of squared levels) >> 3 (squares from the table 0, 1, 4, 9, 16); start prototypes at stride positions of the buffer (offset per restart); first prototype wins ties; best of the restarts by total score. Variants on the dumped codes (purity, seed 1): float k-means 65.5; binary prototypes 40.4-41.4; rate prototypes 2-bit / 4-bit with random start 63.6-65.8; levels 0..4 with stride start 8 iterations: 67.0 (1-3 restarts), **74.1 (6 restarts)**; farthest-first start was worse (52-63).
**End to end (2 seeds):** hard test (10 groups from scratch, joined picture + sound): purity **73.0 % (float 71.3 %)**, names right 71.9 % (65.9 %), picture learner on the group names after sleep cleaning 82.4 % (82.6 %); picture alone 63.97 % purity; sound alone 44.4 %. Novelty step: group names right 98.5 % (float 98.9 %), names after cleaning 98.9 % (98.9 %), all 10 digits 94.35 % (94.13 %).
**RTL:** sequential unit (levels 3 bits per bit and group, counts 8 bits, adders and compares, no multiplier, no divider); the host loads the buffer lists and the K x restarts start indices (stride positions). Check: 5 random buffers (K = 3..5, 1-3 restarts, 2-4 iterations): the winning total score and the group of every pair identical (e.g. K = 4, 3 iterations, 2 restarts: 26,577 cycles for 48 pairs of 256 bits). Added to `hw/run_all_checks.sh` (38 checks; a full rerun is owed).
**Cost note:** one iteration scans the buffer lists twice and the prototype memory once; with the real 9,216-bit joined codes the prototype memory is 9,216 words x 3 bits x K and the count memory 9,216 words x 8 bits x K (K = 30: 83 KB and 276 KB), so the real unit is an ASIC option with SRAM, not a Tang Nano feature.

## 22 Oct 2026 - Full regression with all additions: 38 of 38 checks PASS in one run (SIMULATED RTL); final pitch deck
Fresh run of `sh hw/run_all_checks.sh DATA_DIR` (no resume, inside an active turn, about 1 hour): 38 PASS, 0 failures, 0 skipped (adds the novelty flag unit and the clustering unit to the previous 36). Final deck: `docs/L_pitch_final.pptx` (22 slides, generator `docs/L_pitch_build.js`).

## 22 Oct 2026 - Settings sweep at 60,000 images (no gain) and the stage and night sequencer on the chip, bit-exact (SIMULATED RTL; `cortex_seq.v`, `tb_seq.v`, `run_check_seq.py`)
**Sweep (clothing staged, 60,000 images, follow interval max(100, stage size / 30), 2 seeds; `brain_strict_scale_sweep2.log`):** dreams 1,500 / 4,000: 81.01 / 80.90; slow-table rate K 7: 81.49; 2 night passes: 81.22; 2 daydreams: 81.25; margin 128 / 512: 81.17 / 80.33; dreams 4,000 + K 7: 81.25. Everything is within about 0.5 of the 81.0 baseline: the staged clothing result has plateaued at about 81-82 for these knobs. A new image set could not be fetched (the sandbox has no route to the dataset hosts), so the harder-image-set test is still open.
**Sequencer (the last big host step):** one learning stage is now run by the chip. The host loads each example's code list into the core and pulses ex_valid with the label; the sequencer issues KNOWN for the new classes, LEARN, the daydreams, the interleaved dreams of the old classes (cumulative total ndream x old classes spread over the stage by a running remainder, no divider; the total by repeated addition, no multiplier), FOLLOW every CH ticks (counter), then the night over the known classes with the early stop (after every 256th night dream, counted over the chip's life, stop when more than NSTOP updates happened since the last check or since the night began) and SCOPY when the stage had fewer than 2 CH examples.
**Check:** the sequencer drives `cortex_core.v` (CORTEX_SLOW) through 3 stages (the last shorter than 2 CH) for 4 parameter sets (early stop off and on: 512 of 720 possible night dreams were run in one set because the stop fired; 1-2 daydreams; margin 32 and 256) and the final counts, fast words and slow words equal `CortexSlow.stage`: 0 mismatches in 522 lines each; also with the pipelined core. Added to `hw/run_all_checks.sh` (40 checks; a full rerun is owed).
**Still on the host:** pairing pictures with sounds, loading the code lists, the choice of stage size and of the follow interval (CH = max(100, N / 30), a number the host sets), the start positions for grouping.

## 22 Oct 2026 - Two more host steps moved onto the chip: the follow interval and the grouping start positions (SIMULATED RTL; `cortex_seq.v`, `cortex_cluster.v`)
**Follow interval:** the rule is now CH = max(100, N >> 5) (stage size / 32, a shift) instead of / 30; at 2,000 / 6,000 / 12,000 images per stage clothing staged 80.99 / 81.09 / 80.78 and digits 94.98 / 95.42 / 95.51 against 80.92 / 81.21 / 81.01 and 94.97 / 95.43 / 95.60 with / 30 (`brain_strict_scale_shift32.log`): equal. The sequencer computes it itself (cfg value 0 = automatic) and keeps the tick modulo the current interval by repeated subtraction (the model counts ticks over the chip's life, so a changing interval needs it). `run_check_seq.py` now has 6 parameter sets, 2 of them with the automatic interval (constants CHMIN 8, CHSH 1 for the check; the chip uses 100 and 5): 0 mismatches in 522 lines each, also pipelined.
**Grouping start positions:** `cortex_cluster.v` computes the start pairs itself, floor(i N / K) + floor(r N / (K R)) mod N, by running remainders (repeated subtraction); the host init table is gone. `run_check_cluster.py` unchanged results: 5 buffers, total score and every group identical.

## 22 Oct 2026 - The node: raw senses to a whole learning stage on one chip, bit-exact (SIMULATED RTL; `cortex_node_top.v`, `tb_node.v`, `run_check_node.py`)
`cortex_node_top` = `cortex_sense_top` (retina + cochlea encoders, one core with the slow table; now exports `rd_known`) + `cortex_seq`. The testbench only shows each example to the senses (pixels, or raw 16 kHz samples) and pulses ex_valid with the label; the sequencer issues KNOWN, LEARN with the code length the senses report, daydreams, interleaved old-class dreams, FOLLOW, the night and SCOPY. Two stages (class 0, 1 from picture + sound pairs; class 2 from pictures alone), compared with `CortexSlow.stage` on the Python chain's codes (picture codes 219 active, sound codes 472 active): every count and every fast word, 9,226 lines, **0 mismatches**; 3 night dreams ran. Added to `hw/run_all_checks.sh` (41 checks). The slow table itself is checked by the sequencer check (`run_check_seq.py`), not here.
**Host steps left:** none that is chip logic: the host only shows each example to the sensors (a real product has a camera and microphone), pairs picture and sound in time, and sets the stage's class mask.

## 22 Oct 2026 - Multi-prototype dreams help staged learning at 10,000-60,000 images (SIMULATED, 2 seeds, follow interval max(100, N >> 5); arm `proto:K` in `brain_strict_scale.py`, log `brain_strict_scale_proto.log`; model `cortex_proto_slow.py`)
**Rule (existing from 16 Oct, tested now with the shipped settings and the scaled follow interval):** the dream memory keeps K count-sets per class; an example goes to the prototype of its class with the best normalised overlap; a dream draws a prototype in proportion to its example count and then the bits from that prototype's counters. Integer only (adds, shifts, compares, the chip's xorshift lanes).
**Clothing staged (K = 1 / 2 / 4 / 8 / 16):** 60,000 images 80.69 / 81.92 / 82.73 / **83.16** / **83.67**; 10,000 images 80.74 / - / 82.41 / **82.96** / -. **Digits staged (K = 1 / 4 / 8):** 60,000 images 95.64 / 95.74 / 95.85; 10,000 images 94.96 / 95.38 / 95.50. Passes rule 12 (clothing and digits both up at both sizes).
**Reading:** keeping several modes per class in the dream memory recovers about 2.5-3 of the 6.5-point gap between staged and one pass at 60,000 images (87.6): the dreams now carry which features occur together, a part of what the class tails hold. **Cost:** the dream-count memory grows K times (images: 4,608 bits x 10 classes x 10 bits = 57.6 KB x K: 461 KB at K = 8), an ASIC option; the fast table and the slow table do not grow. Not in RTL yet (prototype choice needs per-class overlap scores and a draw proportional to counts).

## 22 Oct 2026 - What "simulated" means, and the Tang Nano top-level design recognising digits in RTL simulation (SIMULATED RTL; `hw/board/rtl_board_demo.py`)
**Answer to "is it a virtual Tang Nano or a GPU?":** neither. Every accuracy number comes from the integer model (Python, CPU). The RTL checks run the Verilog design in Icarus Verilog (a software logic simulator) and compare it bit for bit with that model. The Tang Nano appears only as a place-and-route estimate. No GPU exists on the cloud machine; the CNN rulers ran on the CPU.
**Demo:** `rtl_board_demo.py` sends the real board's UART protocol bytes (seed lanes, clear, KNOWN, LEARN with a code list, DREAM, PREDICT) to `cortex_board_top.v` (UART + core + encoder) in simulation. It teaches digits 0-3 in four stages (each new digit with 2 dreams per earlier digit per example) from 20 examples each, then asks it to recognise 48 held-out test digits. 375 commands, 64,821 bytes: the board design's 855 reply bytes equal the integer model's (0 mismatches) and it **recognised 36 of 48 test digits (75.0 %)**, computed from its own reply bytes. A few-shot demonstration: the main digit results use thousands of examples per class. A run with 80 examples per class follows.

## 22 Oct 2026 - Chip vs GPU in one script: `hw/brain/experiments/month4/chip_vs_gpu.py`
One command runs the integer model of the chip (software, CPU: stages with no stored examples, and all classes at once, shipped settings, follow interval max(100, N >> 5)) and a CNN ruler on the GPU (CUDA if found) on the same training images and the same test set, and prints accuracy, wall time and the GPU's measured energy (NVML, joules). The chip's energy is not measured by it (software model). Tested here on CPU only (no GPU in the cloud machine): fashion, 500 images per stage, 1 seed: chip all-at-once 82.2 %, chip in stages 70.5 %, CNN all-at-once 75.2 % (2 epochs), CNN in stages 10.0 %. The user runs it on their own GPU.

## 22 Oct 2026 - Virtual space: chip vs GPU benchmark (`virtual_space/`, `hw/rtl/cortex/run_chip_bench.py`, `hw/board/virtual_chip_vs_gpu.py`)
**Request:** a virtual space (not the cloud) where the chip and a GPU both run AI work and are benchmarked. **What is real and what is not:** a virtual GPU cannot be made here (a cycle-accurate GPU simulator needs the vendor toolchain and gives no meaningful speed); the GPU side must be the user's real GPU. The virtual chip is its own RTL design in an RTL simulator.
**Chip cycle counts (SIMULATED RTL, cortex_core.v at 4,608 code bits, real digit codes, mean over the measured commands):** FPGA build: LEARN 2,910 cycles, DREAM 24,151, PREDICT 1,522; pipelined build (ASIC option): 1,980 / 9,412 / 320. At the board's 27 MHz (MODELLED): a decision every 56 us (17,700 per second) on the FPGA build, 11.9 us (84,000 per second) pipelined; a dream 0.89 ms / 0.35 ms.
**Deliverables:** `virtual_space/benchmark.py` (cycle counts + a CNN on the user's GPU: latency at batch 1, throughput at a large batch, NVML energy per decision; prints one table), a `Dockerfile` (PyTorch CUDA image + Icarus Verilog), `virtual_space/README.md` with the Windows commands, and `hw/board/virtual_chip_vs_gpu.py` (the board design in RTL simulation vs a CNN on the same images; small cloud run on CPU: virtual chip 13 of 16 test digits, CNN 75 % all at once and 12.5 % in stages, 16 images only). Tested end to end here on CPU only; the GPU rows need the user's machine.

## 22 Oct 2026 - Full regression: 41 of 41 checks PASS in one fresh run (SIMULATED RTL); slow-table RTL demo; deck slide updated
`sh hw/run_all_checks.sh` fresh (no resume, inside an active turn): 41 PASS, 0 failures, 0 skipped (adds the stage and night sequencer, with and without the pipelined core, and the node check to the previous 38). Deck slide 13 now reads 41 / 41 (`docs/L_pitch_final.pptx`).
**Slow-table RTL demo** (`hw/rtl/cortex/run_slow_demo.py`, `tb_seq_pred.v`): the stage and night sequencer + core with the slow table (margin 256, follow interval 100, reduced dream count NDREAM = 10 because RTL simulation is slow) taught digits 0-3 in four stages of 60 examples; PREDICT with the slow table on 400 held-out test digits: RTL answers equal the integer model on all 400 (0 mismatches); **384 of 400 recognised (96.0 %)**. The board design demo with the old build (margin 32, no slow table) scored 36 of 48 (75 %, 20 per digit) and 54 of 60 (90 %, 80 per digit): the older settings and small test sets explain the gap.
**User's GPU run (MEASURED, RTX 3050 6GB laptop GPU, `chip_vs_gpu.py`, MNIST):** 10,000 images: chip model all at once 97.07 %, in stages 94.98 %; CNN all at once 97.78 % (597 J), in stages 10.09 % (160 J). 59,063 images: chip 97.91 % / 95.51 %; CNN 99.09 % (1,148 J) / 19.60 % (510 J). The chip time is the software model on the CPU; chip energy is not measured.

## 22 Oct 2026 - User's benchmark.py run (virtual space) and Windows flag fix

**Asked:** run the virtual-space benchmark on the user's own GPU. **Done:** the user ran `python virtual_space\benchmark.py D:\cortex_data` on an RTX 3050 6GB Laptop GPU.
**Results:** chip, FPGA build at 27 MHz, one digit decision: 55.7 us, 17,952 decisions/s, 9.4 nJ (cycles MEASURED in RTL sim; time = cycles / 27 MHz is ESTIMATED; energy is an op-count ESTIMATE, not a board measurement). GPU CNN batch 1: 1,791.3 us, 558 decisions/s, 76.73 mJ per decision (MEASURED, NVML). GPU batch 1024: 22,391 decisions/s, 1.944 mJ per decision (MEASURED).
**Honest reading:** the chip and the CNN do different work (the CNN is ahead on all-at-once accuracy, 99.09 vs 97.91 at 59k). Chip latency is ~32x lower than GPU batch 1 on paper, but the chip number is a clock-cycle estimate at 27 MHz, not a board run. Energy needs a real board power reading before any claim.
**Failure found:** the pipelined-build row crashed on Windows ("-DCORTEX_PIPE: No such file or directory") because Icarus needs flags before file names. Fixed in `hw/rtl/cortex/run_chip_bench.py`; re-tested here: FPGA build 2,910 / 24,151 / 1,522 cycles (LEARN / DREAM / PREDICT), pipelined 1,980 / 9,412 / 320. Pushed. User must `git pull` and rerun.
**Gate-level run:** RTL half finished (24 commands, 6,873,000 cycles); gate half had not reported when the container was last checked. Not claimed.
**Rerun after the fix (user, same GPU):** chip FPGA build 55.7 us, 17,952 decisions/s; chip pipelined (ASIC option) 11.7 us, 85,174 decisions/s (cycles 1,952 / 9,412 / 317; SIMULATED cycles, time ESTIMATED at 27 MHz); chip energy 9.4 nJ for both rows (ESTIMATED, op count, not a power reading). GPU batch 1: 1,809.2 us, 553 decisions/s, 69.27 mJ (MEASURED); batch 1024: 22,226 decisions/s, 1.953 mJ (MEASURED). One chip handles one stream; the GPU number at batch 1024 uses many images at once.
**Deck:** added slide 12 "Deciding one digit: chip design vs a real GPU" (the user's measured RTX 3050 table, each row labelled; 24 slides now, so the "41 / 41" slide is 14). Files: `docs/L_pitch_build.js`, `docs/L_pitch_final.pptx`.
**Deck:** added slide 11 "The L Cortex design in one picture" (block diagram `docs/img/l_cortex_block.png`, script `l_cortex_block.py`); 25 slides now, so the GPU slide is 13 and "41 / 41" is 15. Gate-level simulation of the NB=64 netlist was still running (restarted after the container lost the first run); no result yet.

## 22 Oct 2026 - Gate-level simulation: the synthesised netlist HANGS (FAILURE, SIMULATED)

**Asked:** "first check whether gate level simulation runs". **Found:** the long run (about 2 h, `hw/synth/gate_level/run_gate.py`, NB=64) was not slow; the netlist hangs. Test with a command stream truncated to the first N commands (`/tmp/gate_small`): empty stream (CLEAR + dump) runs in 1.3 s (488,000 cycles); 3 KNOWN commands (op 5) run fine (497,000 cycles); the first LEARN (op 1, 16 code bits) does not finish in 60 s (and not in 10 min for 5 commands). The same command stream runs to completion on the RTL in under a minute (24 commands, 6,873,000 cycles). So the RTL is fine and the synthesised Gowin netlist, as simulated with the extracted cell models, never drops `busy` after a LEARN.
**Not yet known:** whether this is a bug in the test setup (the list buffer `lbuf` is `ram_style = block` and was synthesised with `-nobram`; the hand-made `MUX2` model and the extracted `cells_used.v` are the suspects) or a real synthesis mismatch. Until root-caused, no gate-level claim is made anywhere; this entry replaces the earlier "still running" notes (the first run killed by `timeout 1500` was probably this same hang).
**Same day, layout rebuild:** synthesis reproduced (18.80 mm2, 63 SRAM macros); floor2e placement + clock tree rebuilt in a work copy; detailed routing with the floor2g settings running (first pass 33,077 violations).

**Gate-level, second attempt (SIMULATED, core only, NB=64, 24 commands, 95 lines vs the integer model):** a netlist from plain Yosys gates (42,778 cells) gives **0 mismatches**; the ASIC netlist in real SKY130 `sky130_fd_sc_hd` cells with the OpenRAM macro models and the clock gates (11,228 cells, 7 macros) gives **0 mismatches with all flip-flops powering up 0 and again with all powering up 1** (first try showed X outputs only because the flip-flops had no power-up value in the simulation; the reset covers the control state). So the design and its SKY130 synthesis agree; the Gowin-model hang is blamed on my hand-made cell models and is left open. Files: `hw/synth/gate_level/sky130/`. Limit: small core only, not the full 4,608-bit chip.
**Routing at 16:20:** 3rd pass 5,980 violations (130k, 42k, 33k, 6k).

## 22 Oct 2026 - Fabrication-readiness checks on the L Cortex layout (FAILURES recorded)

**Asked:** finish detailed routing, GDSII, DRC/LVS, fix power. **Done:** rebuilt the whole layout in a new container (open tools installed through micromamba): routing again **0 violations** (router count). GDSII exported (193 MB). Timing re-read: setup -6.19 ns at 20 ns (~38 MHz), **hold -0.21 ns (fails)**; power ~55 mW (ESTIMATED). **Magic DRC: the first "0 errors" was an artefact (lazy check) and is retracted. The second run (124,286 errors, mostly met1 minimum area) was ALSO an artefact: my tile cutting dropped the via layer. Third run, correct tiling with the macro insides replaced by their LEF pins/obstructions (each OpenRAM macro holds ~416 million shapes, which is why full-chip DRC could not finish): minimum-area errors gone, but about 153,000 well / latch-up errors remain (88k LU.3, 24k nwell.4, 22k hvi.5, 15k nwell.2a), spread over the whole chip.** A control cell with two close wires is flagged, so the check works. Cause not known (conversion, tap halo around macros, or checker setup); not claimed clean. Not claimed fabrication-ready. LVS not run. Power fix not started (it only matters after the layout is clean). Files: `hw/asic/cortex/signoff/`.
**Correction of an earlier statement:** I said detailed routing was "not done"; the repo already had a 0-violation routed run (floor2g); what was missing was GDSII, DRC/LVS and a re-extraction.
**Answer to "why does it use more power than a GPU":** it does not; the layout estimate (35-55 mW, 0.18-0.26 uJ/decision) is far below the measured GPU (about 38 W at batch 1, 69 mJ, 1.95 mJ at batch 1024); the gap is to the 9.4 nJ operation-count figure.

**Night 22-23 Oct update (layout checks):** root cause of the ~325,000 well and latch-up DRC errors found: **no filler cells in the flow**. With 3.17 M fill cells added, tile 0_1 falls from about 12,500 errors to 1,036, all within 3 um of an SRAM macro (my thin pin stand-in shapes), 0 elsewhere. Hold repair works (-0.21 -> +0.10 ns on the old layout; -0.31 -> +0.35 ns pre-route on the rebuilt one). New open items: **antenna violations** (2,279 nets of 115,506, ESTIMATED; `repair_antennas` segfaults in this OpenROAD build) and **LVS not run**. Incidents: the disk allowance filled once and crashed a routing run and a DRC batch (re-run). Rebuilt layout (taps at 13 um, hold repaired before routing) is routing now. Details: `hw/asic/cortex/signoff/README.md`.

## 23 Oct 2026, 07:50 IST - Morning report: L Cortex layout checks (SIMULATED / ESTIMATED; nothing taped out, nothing on a board)

| Check | State |
|---|---|
| Detailed routing (old layout floor2e, rebuilt in a fresh container) | **0 violations** (router count) |
| Foundry-rule DRC (magic), first attempts | 124k and 325k errors: both **artefacts of my own steps** (a tile cut that dropped the vias; no filler cells in the flow) |
| DRC after adding 3.17 M filler cells, **4 of 6 tiles done** (0_0, 0_1, 1_0, 2_0) | **3,624 errors, all within 3 um of an SRAM macro (met3/met4 width and spacing from my thin LEF stand-in for the macro), 0 in the logic or routing.** Tiles 1_1 and 2_1 still running. A weak window test with the real macro layout shows only 3 such errors. |
| Hold timing | repair works: -0.21 -> +0.10 ns (old layout), -0.31 -> +0.10 ns before routing (rebuilt layout). The rebuilt layout (taps at 13 um) failed twice in the router ("No access point" for the hold buffers) until the hold buffers were legalised with `detailed_placement`; **it is routing now** (started 07:52 IST, about 75 min). |
| Setup timing | -6.19 ns at 20 ns, about 26 ns / 38 MHz (ESTIMATED, placement parasitics) |
| Power | about 55 mW, gated clocks, 10% activity (ESTIMATED) |
| Gate-level simulation of the core, NB=64, 24 commands | SKY130 cells + macro models: **0 mismatches, flops power-up 0 and 1**; generic gates: 0 mismatches; Gowin-primitive netlist hangs (my cell models) |
| Formal equivalence, post-layout vs synthesis | **77,330 points proven, 0 unproven** (macros stood in on both sides) |
| **Antenna** | **OPEN**: 2,279 nets (2%) violate; `repair_antennas` segfaults in this OpenROAD build; a newer build cannot be installed |
| **LVS (physical)** | **OPEN**: not run; the equivalence check stands in for it |
| Incidents | the container restarted once and the disk allowance ran out once (a routing run and a DRC batch crashed and were re-run) |

**Not claimed:** fabrication-ready. Still to do: finish routing and re-run the DRC on the rebuilt layout, fix antennas, attempt LVS block by block.

## 23 Oct 2026 - Pitch deck and script: why not transformer/GPU, why L, how models run on L

Deck now 28 slides (`L_pitch_final.pptx`): new slide 3 (what today's model and GPU get wrong: frozen model, every token reads everything, GPU needs a crowd: 69 mJ vs 1.95 mJ on the user's RTX 3050, 35 times, MEASURED), slide 15 (why use L: 95.5 vs 19.6 staged, 84 KB, 41/41; use L for on-device learning, keep the GPU for training), slide 20 (how real AI models can run on L: alter an existing model (ternary, published), design our own counting language model (next experiment), grow the memory (DRAM, sparse lookups); status stated as hypothesis with falsification tests). Script rewritten (`pitch_script_final.md`): the three judge questions with scripted answers, do/do-not lists, claims table with labels, 9-minute slide-by-slide script, 5-minute cut. Corrections made on the way: slide 15/17 routing line now 0 violations by the router's own count; the chip decision is about 1,500 cycles (the 2,900 was the learning cost). No fabrication detail in the pitch; no claim of fabrication readiness.

**Deck 29 slides:** new slide 7 "How we tested it" (what we ran: integer model of the chip on standard tasks and protocols; what we compared with: CNN measured on the RTX 3050; how the design was checked: 41/41 bit-exact, real-cell netlist, formal equivalence; not tested: a language model or any large model, a board run). Script and Q&A sheet updated and renumbered.

**Deck 30 slides:** new slide 21 "Why the model must change, not just the chip" (a chip alone is a GPU/TPU; the waste is in the model; the L design rules; model and chip designed together; status: small version works, language-model version untested). Script gets Q3 on the same question and is renumbered; Q&A sheet item 23.

**Deck 31 slides:** new slide 16 "Where the GPU uses more energy, and L less": one decision alone (GPU 69.3 mJ MEASURED vs L 0.18-0.26 uJ layout estimate / 9.4 nJ op count), in a crowd (1.95 mJ), learning from 59,063 images (CNN 4 epochs 1,148 J MEASURED vs L about 3 J ESTIMATED from 45-62 uJ per example), learning a new class later (GPU retrains and forgets; L learns in place). Labelled as orders of magnitude (chip core-only estimates vs whole GPU). Script Q6, slide-by-slide text and Q&A item 24 added.

**Deck:** speaker notes removed from `L_pitch_final.pptx` (the generator's `notes()` is now a no-op); the spoken text lives only in `docs/pitch_script_final.md`.

## 23 Oct 2026 - Counting language model, first test (SIMULATED algorithm test)

**Asked:** work further on failures and developments in the cloud. **Done:** the first test of the "design our own model" route: a hashed-count language model, online, one pass, on 561 KB of English text (`hw/brain/experiments/month5/counting_lm.py`, note `hw/results/counting_lm.md`). Quality grows with memory: 4.83 bits per character at 8 KB, 3.04 at 128 KB, 1.93 at 2 MB, 1.80 at 8 MB, 1.77 at 32 MB (order 0..5); order 0..6 gives 1.70. Offline compressors on the same text: xz 1.54, bz2 1.60. **Limits:** float log/sigmoid in the prototype (not mapped to lookup tables), no neural baseline at matched memory yet, one small corpus. **Also:** the container restarted again at about 10 am IST and killed the background routing run; the rebuilt layout (floor2h) is being routed again.

## 23 Oct 2026, 10:58 IST - Live power test at the discussion (MEASURED GPU, ESTIMATED chip)

User ran `benchmark.py` and `energy_cortex.py` on the RTX 3050 6GB Laptop GPU during the judge's discussion (no internet, so no `git pull`; the local copy was enough). **Second GPU measurement, very different from the first:** batch 1: 421.4 us, 2,373 decisions/s, **12.56 mJ**; batch 1024: 98,427 decisions/s, **0.294 mJ** (the first run on 22 Oct gave 1,809 us / 69.3 mJ and 22,226/s / 1.95 mJ). Likely cause: the GPU power/clock state (power mode, plugged in or not, warm-up); not established. Both are MEASURED; quote them as a range and say the GPU number depends on its power state. Chip rows unchanged: 55.7 us FPGA build, 11.7 us pipelined (cycles from RTL simulation). `energy_cortex.py` (ESTIMATED, 45 nm op energies, 241.8 active code bits per image): chip decision 9.32 nJ including the encoder (decide 5.08 nJ, encode 4.24 nJ), learn one example 28.7 nJ, one dream 52.96 nJ; network 784-256-10 int8 decision 696 nJ, fp32 decision 11,098 nJ, fp32 training step 33,295 nJ per example; ratios 74.7x (int8 decision) and 1,160x (training step vs chip learning). `nvidia-smi` at 1 Hz showed an idle floor of about 11.8 W and one blip to 16 W (31% utilisation): the benchmark bursts are shorter than the sampling, so it misses them; the utilisation column prints "[Unknown Error]" on this laptop (driver quirk). For a visible watts rise use `chip_vs_gpu.py` (minutes of training) with `nvidia-smi --query-gpu=power.draw --format=csv -l 1`.

## 23 Oct 2026 - End-to-end power: the encoder was missing from the chip rows (CORRECTION)

The chip rows of `benchmark.py` (55.7 us, 11.7 us) and the layout figure 0.18-0.26 uJ were the decision from the sparse code only; the encoder takes 21,378 cycles per image (about 0.79 ms at 27 MHz) and dominates. End-to-end layout estimate (two phases, gated clocks, activity bracket 5-10%): encode 92-104 mW, 39.5-44.5 uJ; decide 45-55 mW, 0.29-0.35 uJ; about 40-45 uJ per image, about 0.4-0.8 ms. GPU measured: 12.56 mJ / 0.294 mJ (23 Oct), 69.3 mJ / 1.95 mJ (22 Oct); about 29-43 W while running, 11.8 W idle. Energy ratio about 7 to 1,650 times, not 57,000. Op-count figure (9.3 nJ incl. encode) is a lower bound. End-to-end the FPGA build is not faster than the GPU at batch 1 (about 0.85 ms vs 0.42 ms). Note `hw/results/end_to_end_power.md`. To do: measured switching activity from a simulated image (Level 3), correct slides 14 and 16 and the script, add the encoder to `benchmark.py`.

**Level 3 (measured activity), 23 Oct:** MNIST test images downloaded in the cloud (the proxy allows the ossci S3 mirror) and run through the encoder RTL (ASIC build): 21,378 cycles per image, 210 active bits, switching 1.2 to 2.7% (not the 5 to 10% guessed), clock-gate pulses 3.7% and 2.4% of cycles. Layout power with these: encode 29-32 mW, 12.4-13.6 uJ; pixel load 0.79 uJ; decision 0.25 uJ; **picture to answer about 14 uJ** (the 40-45 uJ upper bound is superseded). Ratio against the measured GPU about 20 to 5,000 times. Deck slides 15 and 16, `benchmark.py` (end-to-end rows) and `end_to_end_power.md` updated; the script follows.

## 23 Oct 2026 - Memory without losing accuracy: lossless limit measured; a workload-specific memory is the next design question

User rule: do not trade accuracy for memory; design our own memory. First measurement (`hw/results/table_storage_lossless.md`): the trained tables (fast 5-bit, slow 8-bit, dream counts 10-bit) are 54-71% non-zero and use their full widths; the entropy limit of any lossless code is 77 KB against 129 KB dense, at most 1.7 times. So a much larger memory needs a denser memory, not coding. Design directions recorded (not built): (1) hybrid memory matched to the workload: the slow table is read often and rewritten only every ch ticks, a fit for dense non-volatile memory; the fast table and dream counts are written heavily, a fit for SRAM or gain-cell eDRAM; (2) a counter cell with in-memory increment (no read-modify-write); (3) wide-word banks aligned to the 50-bit table word with several adder lanes. A new physical storage device is a lab and foundry effort (not possible solo today); circuit-level and architecture-level memory design can be simulated now.

**Bits against accuracy (23 Oct, SIMULATED):** user asked whether fewer bits cost accuracy. Measured (`hw/results/bits_vs_accuracy.md`): yes, more so on the harder task. Clothing: fast table 5 -> 4 bits loses 1.3 (staged) / 1.0 (all at once), 3 bits loses 4-6, 2 bits collapses; dream counts 10 -> 6 bits loses about 2 staged. Digits: 4 bits is as good as 5. Shipped widths sit near the knee; wider gains at most a few tenths. Consistent with the earlier 5-bit readout gap. Conclusion: narrowing the counters is not a free memory saving; a bigger memory needs a denser memory.

## 23 Oct 2026 - Direction: keep memory on chip, scale with several chips (Groq / Cerebras style); first multi-chip benchmark

User decision: no DRAM or HBM; run bigger models by using several chips, each with its own on-chip memory. First simulation (`hw/results/multichip_lm.md`): the 8 MB counting language model split over 1 to 64 chips by hashed slot; measured 98% remote lookups at 64 chips, about 280 B per token, and **load imbalance 2.1x at 64 chips** (hot contexts); modelled latency 1.6 us per token (8 sequential steps x 200 ns assumed link round trip) and 12 nJ per token. Dense 7B comparison is cost only (different quality). Next: replicate hot rows, test fetching several steps at once, then a real model comparison at matched quality.

Related: [Project memory](PROJECT_MEMORY.md), [Home](../README.md)
