# Feed Leak Detector

Catches silent failures in the daily sales and inventory files a retailer sends a beverage brand, names the likely cause, and drafts a ticket for the data team. All data is synthetic.

## The user

A data engineer at a beverage brand. The brand uses the retailer's daily feeds to plan orders and store visits.

## The problem

When a feed breaks quietly (a unit change, missing stores, a stale file, frozen inventory), the brand plans on bad numbers and loses sales for days before anyone notices. The goal is to catch the failure within a day, say why, and stay quiet when something unusual is legitimate (a promotion, a store closure).

## Design

AI does the reading, code sets the guardrails, people decide.

1. **Detect (code):** expected vs actual per store and product.
2. **Diagnose (one LLM call per incident):** structured cause, evidence, confidence and a ticket draft.
3. **Gate (plain Python):** checks the cited evidence is real, then alerts or suppresses. The model can never silence an alert on its own.
4. **Human step:** a Streamlit page shows the alert queue and the drafted ticket.

## Three systems compared

| Name | What it is |
| --- | --- |
| B0 | Rules only: schema checks and row-count thresholds |
| B1 | Expected vs actual, calendar-aware, no LLM |
| Agent | B1 plus the diagnoser plus the gate |

## Metric targets (hypotheses, not claims)

| Metric | Target |
| --- | --- |
| Dollar-weighted detection within 24 hours of onset | 90% or more |
| Median days to detect | Agent at half of B1 or less |
| False alerts per week | 2 or fewer |
| Lookalike suppression with a correct cited reason | 95% or more |
| Root-cause accuracy on alerted incidents | 80% or more |
| Adversarial pass rate | 100% |

## Status

See [STATUS.md](STATUS.md). Design choices are in [DECISIONS.md](DECISIONS.md).
