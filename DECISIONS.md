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
