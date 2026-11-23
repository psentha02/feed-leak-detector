Results on the tuning scenarios (10: s1a, s1b, s2a, s2b, s3a, s3b, s4a, s4b, s5a, s5b)

| Metric | Target | B0 | B1 | Agent |
| --- | --- | --- | --- | --- |
| Dollar-weighted detection within 24h | 90%+ | 88% | 99% | not built yet |
| Median days to detect (misses count as full length) | Agent <= half of B1 | 4.5 | 0.0 | not built yet |
| Failures never alerted | 0 | 6 of 8 | 0 of 8 | not built yet |
| False alerts per week | 2 or fewer | 0.00 | 0.01 | not built yet |
| Lookalike suppressed with correct reason | 95%+ | 0% | 100% | not built yet |
| Root-cause accuracy on alerted incidents | 80%+ | 100% | 100% | not built yet |
| Adversarial incidents still alerted | 100% | 0% | 100% | not built yet |

Per incident: days from start to first matching alert (no alert is correct for cases 12 and 13)

| Incident | Case | B0 | B1 |
| --- | --- | --- | --- |
| s1a-01 | 1 | no alert | 0 |
| s1b-01 | 12 | no alert | no alert |
| s2a-01 | 3 | 0 | 0 |
| s2b-01 | 13 | no alert | no alert |
| s3a-01 | 4 | no alert | 3 |
| s3b-01 | 4 | no alert | 0 |
| s3b-02 | 12 | no alert | no alert |
| s4a-01 | 9 | no alert | 0 |
| s4b-01 | 1 | no alert | 0 |
| s4b-02 | 13 | no alert | no alert |
| s5a-01 | 17 | no alert | 0 |
| s5b-01 | 3 | 0 | 0 |
| s5b-02 | 12 | no alert | no alert |
