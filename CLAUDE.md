# Instructions for every session on this repo

1. **Read `docs/PROJECT_MEMORY.md` first.** It holds the project's identity, the user's standing rules, the full
   history, the current design, all results and the plan. Then read the last entries of `docs/journal.md`.
2. **After every experiment, decision or change of direction:**
   - add an entry to `docs/journal.md` (what was asked, what was done, result with its label, file paths);
   - update `docs/PROJECT_MEMORY.md` if the design, results, rules or plan changed;
   - copy experiment scripts and raw logs into the repo (`hw/brain/experiments/<month>/`), not only a scratch folder;
   - commit and push to `claude/zealous-turing-lsg561`.
3. Label every number MEASURED / SIMULATED / ESTIMATED / PROJECTED, and record failures as clearly as wins.
4. **The project is named L** (renamed from SPARK on 22 Oct 2026; code, board and file names keep the old `spark_`
   prefix so the regression keeps working). Two workstreams, both in this repo:
   - **L Cortex** (the counting chip, done to a bit-exact RTL): keep to brain principles, no matrices, no multiplies,
     no backprop in the chip design. Do not reframe it as a GPU helper or an FPGA builder. (28 Oct 2026: hybrid
     additions beyond this are allowed only as separately labelled options, per the founder's decision below.)
   - **L accelerator** (the dedicated chip for the L language model, the alternative to a GPU; see
     `docs/L_accelerator_design.md`): **UPDATE 31 Oct 2026 (founder): the no-matrix / no-multiply rule is withdrawn for the accelerator; multiplication and matrices are ordinary tools, and the chip must run existing models (see `docs/gpu_workload_map.md`). The text below is the superseded 28 Oct rule, kept for history; the "no CNN as a component" and "label every number" rules stand.** Superseded: **matrix-free by default, hybrid where a test shows a need** (founder's decision,
     28 Oct 2026, replacing the 22 Oct rule that forbade every matrix: use ternary weights AND matrices / multiplication
     wherever they are needed, and keep the design light-weight). Default tools: scans, event-driven sparse row lookups,
     table and hash lookups, counters, small state, ternary add-only paths. A multiplier or matrix path is added only
     where a measured test shows it pays (accuracy per unit of energy, memory and latency), is routed to the
     inputs that need it, and is labelled as a hybrid component. Inference on the chip, training on a GPU. Label every
     number MEASURED / MODELLED / ESTIMATED / SIMULATED, and every reference number with its own label.
     **No CNN (or other standard GPU architecture) as a component of L** (founder, 28 Oct 2026: if we and GPUs both use a
     CNN, "CNN optimised" invites the question of why a GPU cannot optimise it). A standard architecture may appear only
     as a labelled reference baseline. Method: study each concept (why it exists, how it is built, where it is used,
     its flaws and limits), then build our own method that fixes those flaws, and test it before building.
5. Never write AI model identifiers into repo content.
6. This repo is the team's **second brain**, opened in Obsidian as a vault (home: `README.md`). Keep it linked:
   every new note is linked from its folder's index (`docs/INDEX.md`, `hw/results/INDEX.md`, `hw/HARDWARE_INDEX.md`)
   and ends with a `Related:` line; use relative markdown links (they work in Obsidian and on GitHub); add new journal
   entries above the journal's final `Related:` line. Lint with the obsidian-notes skill's `vault_lint.py` before
   committing (target: 0 errors, 0 orphans).

7. Never run two RTL checks in the same folder at the same time: they share `cmds.hex` / `out_cortex.txt` and give
   false mismatches. After RTL changes run `sh hw/run_all_checks.sh DATA_DIR` (all checks in sequence).

Related: [Project memory](docs/PROJECT_MEMORY.md), [Journal](docs/journal.md), [Home](README.md)
