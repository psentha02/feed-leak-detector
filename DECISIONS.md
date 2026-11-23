# Decisions

One entry per design choice, experiment or cut: what changed, the result, whether it shipped.

## 1. No agent framework, no database, no async
Anthropic SDK directly, pandas and CSV files. Keeps the code short enough to explain in a 9-minute video. Shipped.

## 2. Model can never silence an alert
Suppression is decided by a plain Python gate that checks cited evidence exists. Shipped (design).
