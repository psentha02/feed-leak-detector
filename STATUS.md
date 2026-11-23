# Status

## Session 2 (2026-11-22): plan change, harder cases (tag `v0.2-hard-cases`)
- Why: B1 was the answer key and passed everything, so the Agent had no room to add value (DECISIONS #10).
- Done: notices feed; case 2 (store id remap) and case 14 (unannounced display); case 15 skipped (#14); tuning scenarios s1c to s5c (30 scenarios in all: 15 tuning, 15 test); detectors report symptoms with a scorer-side cause table (#13); B1 bug fix (#11); affected-set precision and recall; B1 strict, default and loose (#15); targets replaced (#16).
- Eval ([results](evals/results/baseline_tuning.md)): B1 detects all 13 failures on day 0 but names the wrong cause on all 3 case 2 incidents (root-cause accuracy 77%) and false-alarms on all 3 case 14 incidents (lookalike suppression 67%). B0 catches 2 of 13.
- 33 tests pass. Existing scenarios are byte-identical to before (golden hashes) and B0 and B1-default reproduce their old results.
- Test scenarios (seed 99, now t00 to t14) have never been built, run or inspected. `t10` to `t14` were added by case type only.
- Open: loose is only mildly looser than default (#15), so it adds no recall. The Agent's value on this data comes from wrong causes (case 2), notice-explained lookalikes (case 14) and ticket drafting.
- Open: PyYAML added as a dependency (#3), not yet confirmed by you.
- Next: Step 3, the diagnoser and gate, starting with case 2 or case 14 end to end (they need `get_notices`).

## Session 1 (2026-11-22)
- Step 1 (frame) pushed, Step 2 (baseline) tagged `v0.1-baseline`, harder noise and smaller tuning incidents (#9).
