# Decisions

One entry per design choice, experiment or cut: what changed, the result, whether it shipped.

## 1. No agent framework, no database, no async
Anthropic SDK directly, pandas and CSV files. Keeps the code short enough to explain in a 9-minute video. Shipped.

## 2. Model can never silence an alert
Suppression is decided by a plain Python gate that checks cited evidence exists. Shipped (design).

## 3. PyYAML added as a dependency
The profile is a YAML file (per the plan), which needs PyYAML. It is the only dependency beyond pandas and pytest in Step 2. Shipped. Flagged for review.

## 4. Extra `file_date` column on the feeds
Needed to represent a stale file in one table (arrival day vs business date). Documented in DATA.md. Shipped.

## 5. B1 includes B0's checks
B1 = B0's schema, row-count and freshness checks plus expected-vs-actual. This keeps the B0 to B1 comparison about the expected-value model alone. B1's "dropped stores" alert replaces B0's wording when both fire. Shipped.

## 6. B1 judges products and stores in totals, not cell by cell
Per-cell counts are tiny (often 0 to 5 units), so single cells are too noisy. B1 compares each product's total across stores and each store's total across products, against the median of the same weekday over 4 weeks (skipping promo, closed and stale days). Shipped.

## 7. Promo handling in B1
A product on the calendar is only a spike at 8x expected (promos reach about 5x); off the calendar a spike is 2.5x. Between those on a promo day B1 records a "promo_calendar" suppression. Closed stores with low sales record a "store_master" suppression. Shipped.

## 8. First baseline run (tuning scenarios, no tuning done yet)
B1 caught all 8 failures with 0 false alerts; B0 missed 5 of 8. This is suspiciously easy: the injected failures are large and the noise is plain Poisson (see DATA.md limits). Not tuned, not made harder. Open question for the Agent target "median days at half of B1": B1 is already at 0 days, so the target cannot be beaten on this data. Needs a decision before Step 3.

## 9. Harder data (two separate changes, B0 and B1 code untouched)
Why: B1 scored 100% with 0 false alerts on the first data (see #8).
- **Change A, realism noise:** gamma-Poisson counts, store-day swings, weekly product drift, 0.3% random missing rows. Result: B1 unchanged (100% within 24h, 0.01 false alerts per week), B0 unchanged at 5 of 8 misses. Noise alone did not make it hard, because the incidents were huge. Shipped.
- **Change B, smaller incidents in the tuning scenarios only:** cases 1, 4, 9 and 17 now touch 1 to 3 stores. Result: B0 misses 6 of 8 failures and detects 88% of dollars within 24h; B1 detects 99% within 24h, misses none, but needs 3 days on the 3-store unit change (s3a), because B1 judges product totals across 30 stores. Median days to detect is still 0 for B1. Shipped.
- B1 was not re-tuned. The v0.1-baseline tag holds the easier numbers.
- The 10 test scenarios keep their original footprints (not touched, not run). Open question: should they be made smaller too before Step 4, for a matching difficulty? That is a change to the test scenarios, so it needs your approval.
- "Agent at half of B1" is still hard to beat while B1's median is 0. Probably the target should become a mean, or use only the small-footprint incidents. Open.

## 10. Plan change: B1 is the answer key, so the Agent's job moves from detection to diagnosis and triage
Finding (an honest result, not a failure): B1 passes every tuning case, and the cause is structural, not noise.
- B1 has one detector per injector, written after the injectors, so it is the answer key.
- B1's alert names equal the label `root_cause` names, so root-cause accuracy is 100% by construction.
- The Agent is B1 plus a diagnoser, so it only sees what B1 flags. It cannot beat B1 on detection, so the target "Agent at half of B1 median days" is unreachable (B1 median is 0).
- Lookalikes are explicit rows in the promo calendar or store master, so B1 just looks them up.
Detection is not where an LLM adds value. Reading messy evidence and triaging alerts is. So: add cases where the symptom and the cause differ, add a text evidence source (notices), and re-centre the metrics on diagnosis and triage. B1's detection logic is not re-tuned to fix the new cases. Shipped (the following entries are the work).

## 11. Bug fix: B1 grid wrote unknown store ids into the last store
`_grid` used `get_indexer`, which returns -1 for ids not in the master, and -1 indexes the last column. Rows with an unknown store id (or product) overwrote store S30. Found while designing the store-remap case. Fix: drop rows with unknown ids before gridding. Regression test fails without the fix. B0 never builds a grid, so it is not affected. No existing result changes, since no existing scenario has unknown ids. Shipped.

## 12. Notices feed, and cases 2 and 14, where symptom and cause differ
What: a `notices` feed (id, date, optional store, optional product, free text) with 8 harmless distractors per scenario, so a notice existing is not a signal. Case 2 (store id remap, failure) and case 14 (unannounced display, lookalike) each add one real explanatory notice; labels cite its `notice_id` as expected evidence. Why: with only calendar and master lookups, B1 was the answer key. Now the cause is only readable from text. Existing scenarios stay byte-identical (golden hashes). Shipped.

## 13. Detectors report symptoms; a scorer table maps symptom to cause
What: alerts carry `symptom` (`stores_missing`, `units_spike`, `file_not_fresh`, `inventory_unchanged`, `row_count_drop`, `store_zero_sales`, `schema_change`), never a cause. `evals/score.py` holds the only symptom-to-cause table, so B1 earns root-cause credit only through an explicit rule ("stores missing means dropped stores"), not because two names match. The original tuning results are unchanged by the rename (golden test). Shipped.

## 14. Case 15 (late backfill) skipped
Backfilled rows would arrive in a later file carrying an older `date`, so they share a (file_date, store, product) key with that day's own rows. B1's grid would silently overwrite one with the other, and B0's freshness check reads the newest date per file. Showing it cleanly means changing detector logic, which this step forbids. Cut. `LOOKALIKE_REASON` has no entry for it.

## 15. B1 threshold sweep (tuning scenarios only)
B1 now takes `params`; defaults reproduce the old results exactly (golden test). Strict was fixed up front (spike 3.5, in-promo 10, low sales 0.2, min expected 30, frozen 0.92). Loose came from `evals/sweep.py` under a rule fixed before looking: lowest mean days to detect on small incidents, among settings with at most 10 false alerts a week, ties to fewer false alerts. Result: loose = spike 2.0, in-promo 6, min expected 10 (low sales 0.3, frozen 0.85 unchanged).
What the sweep showed, 48 settings, 13 failures:
- Speed saturates early. At spike 2.0 every failure is caught on day 0 at 0.16 false alerts a week. Spike 1.5 adds about 3.4 false alerts a week for no further speed. Raising low-sales from 0.3 to 0.5 costs about 1 more false alert a week for nothing.
- The strict side does cost detection: B1-strict misses 3 of 13 failures (the small unit changes) and takes 4 days on the 17-case.
- So the trade-off is real but lopsided here: tightening hurts detection, loosening beyond 2.0 only adds noise. The loose setting is therefore only mildly looser than default, and loose adds nothing the Agent can filter that default does not already alert on. The Agent's triage value on this data comes from the lookalikes and wrong causes, not from extra recall. Shipped as is.

## 16. Targets replaced
"Agent at half of B1 median days" is gone (unreachable, see #10). New: mean days to detect on small incidents (1 to 3 stores), Agent at or below B1; and false alerts per week at matched detection, 2 or fewer. "At matched detection" means compared with B1 set to the same detection rate. False alerts per week is averaged over 15 scenarios of about 9 weeks each, mostly incident-free, so it reads low (0.1 to 0.2) even though every case 14 day is a false alarm. Affected-set precision and recall are reported with no target. Shipped.

## 17. Result of the harder cases (tuning scenarios, nothing tuned to fix them)
- Root-cause accuracy drops from 100% to 77% for B1 (10 of 13): all three case 2 incidents are detected on day 0, name exactly the right (old) stores, and get the cause wrong (`stores_missing` maps to `dropped_stores`, the truth is `store_id_remap`).
- Lookalike suppression drops to 67% (6 of 9): all three case 14 incidents are alerted as `units_spike`, because nothing in the feeds B1 reads explains them. Of B1's 15 false alert-days, 13 are inside case 14 windows; 2 are plain noise (one `store_zero_sales` in s2b, one `inventory_unchanged` in s4c).
- B1 does badly at saying which stores: it names the products but not the stores for a unit spike, so store precision is 72% (65% loose).
- B0 catches only 2 of 13 failures. Both detection and diagnosis headroom for the Agent is now measurable. Shipped.
