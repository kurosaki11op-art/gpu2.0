# Instructions for every session on this repo

1. **Read `docs/PROJECT_MEMORY.md` first.** It holds the project's identity, the user's standing rules, the full
   history, the current design, all results and the plan. Then read the last entries of `docs/journal.md`.
2. **After every experiment, decision or change of direction:**
   - add an entry to `docs/journal.md` (what was asked, what was done, result with its label, file paths);
   - update `docs/PROJECT_MEMORY.md` if the design, results, rules or plan changed;
   - copy experiment scripts and raw logs into the repo (`hw/brain/experiments/<month>/`), not only a scratch folder;
   - commit and push to `claude/zealous-turing-lsg561`.
3. Label every number MEASURED / SIMULATED / ESTIMATED / PROJECTED, and record failures as clearly as wins.
4. Keep to brain principles: no matrices, no multiplies, no backprop in the chip design. Do not reframe SPARK as a
   GPU helper or an FPGA builder.
5. Never write AI model identifiers into repo content.
6. This repo is the team's **second brain**, opened in Obsidian as a vault (home: `README.md`). Keep it linked:
   every new note is linked from its folder's index (`docs/INDEX.md`, `hw/results/INDEX.md`, `hw/HARDWARE_INDEX.md`)
   and ends with a `Related:` line; use relative markdown links (they work in Obsidian and on GitHub); add new journal
   entries above the journal's final `Related:` line. Lint with the obsidian-notes skill's `vault_lint.py` before
   committing (target: 0 errors, 0 orphans).

7. Never run two RTL checks in the same folder at the same time: they share `cmds.hex` / `out_cortex.txt` and give
   false mismatches. After RTL changes run `sh hw/run_all_checks.sh DATA_DIR` (all checks in sequence).

Related: [Project memory](docs/PROJECT_MEMORY.md), [Journal](docs/journal.md), [Home](README.md)
