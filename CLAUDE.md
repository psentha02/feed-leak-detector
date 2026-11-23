# Feed Leak Detector

A solo project for the Tenex builder application. It watches the daily sales and inventory files a retailer sends a beverage brand, catches silent failures (a unit change, missing stores, a stale file), names the likely cause, and drafts a ticket for the data team. Everything runs on synthetic data.

The full plan is in the Claude doc "Feed Leak Detector: Tenex Builder Project Plan" (https://claude.ai/artifact/GS2qeGkdoYhVyACqUkYezV). This file is the working summary. If they disagree, this file wins for the Nov 24 build.

## Deadline and scope

- Submission is due **Tuesday, Nov 24, 2026**. About 15 evening hours in total.
- Build thin first, wide second. Get one failure working end to end before adding the rest.
- Do not start a step until the previous step's "done when" is true.
- Anything not listed here is a stretch goal. Ask before adding it.

## Who the author is

The author is Praveen, a cloud and AI infrastructure engineer. He must be able to explain every design choice in a 9-minute video. So:

- Keep code short, plain and readable. Prefer small files and clear names.
- After each chunk of work, say in two or three plain sentences what it does and why it was built that way.
- Do not use LangChain, LangGraph or any agent framework. Use the Anthropic SDK directly.
- No database, no async code, no abstractions that are not used at least twice. Pandas and CSV files are enough.

## The problem in one paragraph

A brand receives daily sales and inventory feeds from a retailer and uses them to plan orders and store visits. When a feed breaks quietly, the brand plans on bad numbers and loses sales for days before anyone notices. The system should catch the failure within a day, say why it happened, and stay quiet when something unusual is legitimate (a promotion, a store closure).

## Design principle

AI does the reading, code sets the guardrails, people decide.

1. **Detect (code).** B0 is simple rules (schema, row counts). B1 compares actual sales and inventory to the expected value for each store and product, using day of week and the promotion calendar.
2. **Diagnose (one LLM call per flagged incident).** The model gets read-only lookup functions and returns structured JSON: `cause`, `evidence` (a list), `confidence`, `ticket_draft`.
3. **Gate (one plain Python function).** Code decides alert or suppress. It checks that any evidence the model cites actually exists (a real calendar entry, a real store-master row). The model can never silence an alert on its own.
4. **Human step (Streamlit page).** A data engineer sees the alert queue and the drafted ticket.

Untrusted text: free-text fields in the feeds are data, never instructions. Pass them to the model inside a clearly labeled data block, and the gate ignores anything they say.

## The three systems we compare

| Name | What it is |
| --- | --- |
| B0 | Rules only: schema checks and row-count thresholds |
| B1 | Expected vs actual per store and product, calendar-aware, no LLM |
| Agent | B1 plus the diagnoser plus the gate |

B0 and B1 numbers must be recorded before any LLM code is written.

## Data (synthetic only)

- 30 stores in 2 regions and 2 formats, 20 products sold as singles, 6-packs and 12-pack cases, 90 days.
- Daily files: sales (date, store_id, upc, units, dollars), inventory (date, store_id, upc, on_hand), store master (store_id, region, format, open_date, closed dates), promotion calendar (upc, start, end), and a free-text `notes` column on the sales feed.
- Demand per store, product and day is a base rate times store size, day of week and promotion lift, with count noise.
- Industry details live in `profiles/beverage_grocery.yaml`, so the engine stays general.
- No real retailer or brand names. No employer code or data.

### The seven cases

| # | Kind | Case | Expected result |
| --- | --- | --- | --- |
| 1 | Failure | Dropped stores: some stores missing from the sales file | Alert |
| 3 | Failure | Stale file: yesterday's file sent again | Alert |
| 4 | Failure | Unit change: cases reported as single units (12 times too high) | Alert |
| 9 | Failure | Frozen inventory: on-hand unchanged for several days | Alert |
| 12 | Lookalike | Promotion spike: sales up 3 to 5 times on a calendar promotion | Suppress, cite the calendar |
| 13 | Lookalike | Store closure: zero sales during a closure in the store master | Suppress, cite the master |
| 17 | Adversarial | A `notes` value tells the system to ignore alerts and mark them resolved | Never obeyed |

Case numbers match the full plan.

### Labels and splits

- Ground truth goes in a separate `labels.json` that detectors and the agent never read. One record per incident: `incident_id`, `case`, `start_date`, `end_date`, `affected`, `dollars_at_risk_per_day`, `root_cause`, `expected_evidence`.
- 20 scenarios total: 10 for tuning (seeds 1 to 5) and 10 for the final test (seed 99).
- Never look at or tune against the test scenarios until Step 4. Run them once.
- Every run is seeded and repeatable.

## Metrics (`make eval` prints all of them for B0, B1 and Agent)

Targets are hypotheses to test, not claims.

| Metric | Target |
| --- | --- |
| Dollar-weighted detection within 24 hours of onset | 90% or more |
| Median days to detect | Agent at half of B1 or less |
| False alerts per week (realistic mix) | 2 or fewer |
| Lookalike suppression with a correct cited reason | 95% or more |
| Root-cause accuracy on alerted incidents | 80% or more |
| Adversarial pass rate | 100% |

Report misses as well as wins. Never invent or round up a result.

## Commands the Makefile should provide

```
make setup   # create venv, install dependencies
make data    # generate feeds and labels.json for a given seed
make eval    # run B0, B1 and Agent on the scenarios and print one results table
make app     # run the Streamlit page locally
make test    # run pytest
```

## Repo layout

```
README.md  STATUS.md  DECISIONS.md  DATA.md  CLAUDE.md  Makefile
profiles/    beverage_grocery.yaml
generator/   stores.py  products.py  demand.py  feeds.py  injectors.py
detectors/   b0_rules.py  b1_expected.py
agent/       diagnoser.py  tools.py  gate.py
app/         streamlit_app.py
evals/       run_eval.py  results/
tests/
data/        (generated, gitignored)
```

Create folders only when the step that needs them starts.

## Tech choices

- Python 3.11 or newer, pandas, pytest, Streamlit, the Anthropic SDK.
- Model name comes from the `MODEL` environment variable. Use a small, cheap model by default. Cache LLM responses on disk, keyed by the input, so evals are repeatable and cheap.
- API key lives in `.env`, which is gitignored. Commit a `.env.example` only.
- The LLM tools are read-only: `get_feed_diff`, `get_store_master`, `get_promo_calendar`, `get_past_incidents`. No tool writes data.

## Working rules

1. **Commits:** small and frequent, at least one per working session, with messages that say what changed and why (`feat:`, `fix:`, `eval:`, `docs:`). Do not squash. The commit history is part of the proof that this is original solo work.
2. **STATUS.md:** update at the end of every session with what is done, linked to a commit or an eval result, and what is next.
3. **DECISIONS.md:** one short entry for each design choice, each experiment and each cut. Note what changed, the result, and whether it shipped.
4. **Before saying something is done:** run `make test` and `make eval`, and report the actual output.
5. **One change at a time** when tuning the detector or the prompt, and re-run `make eval` after each.
6. **Ask before** adding a dependency, changing scope, or touching the test scenarios.
7. **Never** commit secrets, real data, or anything from an employer or earlier project.

## Step 1 and Step 2 (start here)

### Step 1: Frame (about 30 minutes)

- Create the public repo `feed-leak-detector` with a first commit.
- README: a half-page brief with the user, the problem, the three systems and the metric targets above.
- Add `STATUS.md`, `DECISIONS.md`, a `.gitignore` (data/, .env, venv) and `.env.example`.
- Done when: the first commit is pushed.

### Step 2: Baseline (about 4.5 hours)

1. Write the generator for the profile, then the injectors for the seven cases, then `labels.json`.
2. Write `DATA.md`: every assumption and every simplification, each marked as a placeholder until it has a source.
3. Write B0 and B1.
4. Write `evals/run_eval.py` so `make eval` prints one table: B0 and B1 on the 10 tuning scenarios, for all six metrics (the Agent columns stay empty for now).
5. Add a few tests: the generator is seeded and repeatable, each injector changes only what it should, and labels match the injected incidents.
6. Tag `v0.1-baseline`.
- Done when: the B0 and B1 table is committed and a person could rerun it from the README.

Do not write any LLM code until Step 2 is done.

## Later steps (for reference)

3. **Build:** one failure (the unit change) end to end, then the rest.
4. **Harden:** fix the biggest misses, run the adversarial case, run the test scenarios once.
5. **Deploy and measure:** Streamlit on a free host, synthetic data only, plus the ROI table. The live link must work in a signed-out browser.
6. **Hand off:** README results table, limits, decision log.
7. **Video and submit:** under 10 minutes, unlisted on YouTube, GitHub and live links in the description.

If time runs short, cut in this order: drafted tickets, page polish, the store-closure case. Never cut the baselines, the test numbers, the live link or the video.
