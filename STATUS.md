# Status

## Session 1 (2026-11-22)
- Done: Step 1, framing, pushed (`fb0fe22`).
- Done: Step 2, baseline. Generator, 7 injectors, labels, DATA.md, B0, B1, `make eval`, 17 tests passing. Tagged `v0.1-baseline`.
- Eval result: [evals/results/baseline_tuning.md](evals/results/baseline_tuning.md). B0 detects 71% of dollars within 24h and misses 5 of 8 failures. B1 detects 100% with 0 false alerts and 100% lookalike suppression.
- Test scenarios (seed 99) are defined but never run.
- Open: B1 is already at 0 days to detect, so "Agent at half of B1" cannot be beaten on this data. Decide before Step 3 whether to make the data harder (smaller incidents, noisier demand) or change the target. See DECISIONS.md #8.
- Open: PyYAML was added as a dependency (DECISIONS.md #3).
- Next: Step 3, the unit-change failure end to end through the diagnoser and gate.
