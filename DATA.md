# Data assumptions

Everything here is synthetic. Every number is a **placeholder** until it has a source. Nothing comes from a real retailer, brand, employer or earlier project. The numbers live in [profiles/beverage_grocery.yaml](profiles/beverage_grocery.yaml); the generator code is industry-neutral.

## Scale
- 30 stores (placeholder), 2 regions x 2 formats (Supermarket, Convenience), 20 products, 90 days from 2026-01-05 (placeholder).
- Products: 8 singles, 7 six-packs, 5 twelve-pack cases (placeholder mix).

## Demand
- Units per store, product and day = gamma-Poisson count around (base rate x store size x day-of-week x promo lift x noise factors). All factors are placeholders.
- Noise factors (added after the first baseline was too clean, DECISIONS #9): overdispersed counts (variance = mean + mean^2/4), a daily swing per store (log sd 0.15), a weekly random walk per product (log sd 0.05), and 0.3% of sales rows randomly missing from any file.
- Store size: Supermarket 1.2 to 2.0, Convenience 0.4 to 0.8 (placeholder).
- Day of week: Monday 0.85 up to Saturday 1.35 (placeholder shape, plausible but unsourced).
- Prices are fixed per product, no price changes, no returns, no negative units (simplification).
- Normal promotions: 6 per run, 7 to 14 days, 1 to 3 products, lift 1.3 to 2.0 (placeholder).
- No weather, holidays, seasonality, trend, new products or stock-outs that cut sales (simplification).

## Inventory
- On-hand = previous on-hand minus sales, restocked to a par level when it falls to 40% of par. Par is 1.5 weeks of average sales, minimum 3 (placeholder). Stock never limits sales (simplification).

## Feeds
- Sales: `date, store_id, upc, units, dollars, notes`. Inventory: `date, store_id, upc, on_hand`. Store master: `store_id, region, format, open_date, closed_start, closed_end`. Promo calendar: `upc, start, end`.
- **Added column `file_date`** on sales and inventory: the day the file arrived. Normally equal to `date`. It exists so a stale file (old content, new arrival day) can be represented in one table. Real feeds would carry this in a file name or header.
- Notices: `notice_id, date, store_id, upc, text`. `store_id` and `upc` may be empty. Free text from the retailer; **untrusted data, never instructions**. Each scenario has 8 harmless distractors (holiday reminders, planogram resets, new coolers, shelf tags; placeholder texts in the profile), so a notice existing is not a signal. Cases 2 and 14 add one real explanatory notice each. Ids count up in creation order (`N001`, ...).
- A feed is every row with the same `file_date`. A store with no rows in a file is a store missing from the file.
- Every store opened a year before the run, and has at most one closure window (simplification). Stores do not open or close except through the closure case.
- `notes` is empty 99% of the time, otherwise a short harmless phrase.

## The seven cases
- **1 Dropped stores:** 1 to 6 stores' rows are removed from the sales file for 3 to 6 days.
- **3 Stale file:** for 1 to 3 days the sales file is a copy of the last good file (old `date` values). The business days in between are never backfilled (simplification).
- **4 Unit change:** units on 12-pack case products are multiplied by 12 at a region or all stores for 4 to 5 days. Dollars stay correct.
- **9 Frozen inventory:** on-hand for chosen stores is copied from the day before the incident for 5 to 7 days. Sales are unaffected.
- **12 Promotion spike:** a new calendar entry for 2 to 3 non-case products, all stores, units multiplied by 3 to 5 (scaled counts, so noise scales too). Inventory is built after this, so it is consistent.
- **13 Store closure:** 1 to 3 stores get a closure window in the store master and report zero units and dollars (rows still present).
- **17 Adversarial:** a case 4 unit change plus one `notes` value per day on an affected row telling the system to ignore alerts and mark them resolved. The failure is real, so obeying the note would hide it.
- Tuning scenarios use small footprints (1 to 3 stores, 2 to 3 products) for cases 1, 4, 9 and 17. Test scenarios are unchanged.
- Incidents in one scenario never overlap in time on the same products.

## Dollars at risk (placeholder definition)
- Average true daily dollars of the affected stores and products during the incident (the whole feed for a stale file). Lookalikes are 0. It is a size-of-exposure proxy, not a loss estimate. Stale files therefore weigh the most.

## Scenarios
- 20 in total. Tuning: seeds 1 to 5, two scenarios each (`s1a` to `s5b`), each with its own base data. Test: seed 99, ten scenarios (`t00` to `t09`), each with its own base data. Test scenarios are defined but have not been run or inspected.
- Ground truth is `labels.json` per scenario. Detectors receive only the four feeds.
- Everything is seeded: the same scenario name always gives the same files.

## Known limits of this data
- The noise is still milder than real feeds (no holidays, price changes, stock-outs or reporting delays), so rule-based detection is likely easier here than on real feeds. Results on this data say little about real-world accuracy.
