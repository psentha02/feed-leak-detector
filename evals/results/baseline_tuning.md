Results on the tuning scenarios (15: s1a, s1b, s2a, s2b, s3a, s3b, s4a, s4b, s5a, s5b, s1c, s2c, s3c, s4c, s5c)

| Metric | Target | B0 | B1-strict | B1 | B1-loose | Agent |
| --- | --- | --- | --- | --- | --- | --- |
| Dollar-weighted detection within 24h | 90%+ | 73% | 97% | 100% | 100% | not built yet |
| Mean days to detect, small incidents (1-3 stores) | Agent at or below B1 | 4.55 | 1.55 | 0.27 | 0.00 | not built yet |
| Mean days to detect, all failures |  | 3.85 | 1.31 | 0.23 | 0.00 | not built yet |
| Failures never alerted | 0 | 11 of 13 | 3 of 13 | 0 of 13 | 0 of 13 | not built yet |
| False alerts per week (at matched detection) | 2 or fewer | 0.00 | 0.08 | 0.11 | 0.16 | not built yet |
| Lookalike suppressed with correct reason | 95%+ | 0% | 67% | 67% | 67% | not built yet |
| Root-cause accuracy on alerted incidents | 80%+ | 100% | 70% | 77% | 77% | not built yet |
| Affected stores, precision |  | 100% | 91% | 72% | 65% | not built yet |
| Affected stores, recall |  | 100% | 100% | 100% | 100% | not built yet |
| Affected products, precision |  | 100% | 100% | 100% | 100% | not built yet |
| Affected products, recall |  | 100% | 97% | 92% | 100% | not built yet |
| Adversarial incidents still alerted | 100% | 0% | 100% | 100% | 100% | not built yet |

Per incident: days from start to first matching alert (no alert is correct for lookalikes 12, 13, 14)

| Incident | Case | B0 | B1-strict | B1 | B1-loose |
| --- | --- | --- | --- | --- | --- |
| s1a-01 | 1 | no alert | 0 | 0 | 0 |
| s1b-01 | 12 | no alert | no alert | no alert | no alert |
| s2a-01 | 3 | 0 | 0 | 0 | 0 |
| s2b-01 | 13 | no alert | no alert | no alert | no alert |
| s3a-01 | 4 | no alert | no alert | 3 | 0 |
| s3b-01 | 4 | no alert | no alert | 0 | 0 |
| s3b-02 | 12 | no alert | no alert | no alert | no alert |
| s4a-01 | 9 | no alert | 0 | 0 | 0 |
| s4b-01 | 1 | no alert | 0 | 0 | 0 |
| s4b-02 | 13 | no alert | no alert | no alert | no alert |
| s5a-01 | 17 | no alert | 4 | 0 | 0 |
| s5b-01 | 3 | 0 | 0 | 0 | 0 |
| s5b-02 | 12 | no alert | no alert | no alert | no alert |
| s1c-01 | 2 | no alert | 0 | 0 | 0 |
| s2c-01 | 14 | no alert | 0 | 0 | 0 |
| s3c-01 | 4 | no alert | no alert | 0 | 0 |
| s3c-02 | 2 | no alert | 0 | 0 | 0 |
| s4c-01 | 14 | no alert | 0 | 0 | 0 |
| s4c-02 | 9 | no alert | 0 | 0 | 0 |
| s5c-01 | 14 | no alert | 0 | 0 | 0 |
| s5c-02 | 13 | no alert | no alert | no alert | no alert |
| s5c-03 | 2 | no alert | 0 | 0 | 0 |
