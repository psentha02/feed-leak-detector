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
