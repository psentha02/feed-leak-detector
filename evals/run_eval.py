"""make eval: run the detectors on the tuning scenarios and print one results table.
The test scenarios only run with --split test (Step 4, once)."""
import argparse
from pathlib import Path

from detectors import b0_rules, b1_expected
from evals.score import score_scenario, summarize
from generator.scenarios import TEST, TUNING, build

SYSTEMS = {"B0": b0_rules.run, "B1": b1_expected.run}
ROWS = [
    ("Dollar-weighted detection within 24h", "dollar_detection_24h", "90%+", "{:.0%}"),
    ("Median days to detect (misses count as full length)", "median_days_to_detect", "Agent <= half of B1", "{:.1f}"),
    ("Failures never alerted", "missed_failures", "0", "{}"),
    ("False alerts per week", "false_alerts_per_week", "2 or fewer", "{:.2f}"),
    ("Lookalike suppressed with correct reason", "lookalike_suppression", "95%+", "{:.0%}"),
    ("Root-cause accuracy on alerted incidents", "root_cause_accuracy", "80%+", "{:.0%}"),
    ("Adversarial incidents still alerted", "adversarial_pass", "100%", "{:.0%}"),
]


def run(split):
    names = TEST if split == "test" else TUNING
    scored = {system: [] for system in SYSTEMS}
    for name in names:
        feeds, labels = build(name)
        n_days = feeds["sales"].file_date.nunique()
        for system, detect in SYSTEMS.items():
            scored[system].append(score_scenario(labels, detect(feeds), n_days))
    return names, scored


def render(split, names, scored):
    summary = {system: summarize(s) for system, s in scored.items()}
    lines = [f"Results on the {split} scenarios ({len(names)}: {', '.join(names)})", "",
             "| Metric | Target | B0 | B1 | Agent |", "| --- | --- | --- | --- | --- |"]
    for label, key, target, fmt in ROWS:
        cells = [fmt.format(summary[s][key]) for s in SYSTEMS]
        lines.append(f"| {label} | {target} | {cells[0]} | {cells[1]} | not built yet |")
    lines += ["", "Per incident: days from start to first matching alert (no alert is correct for cases 12 and 13)", "",
              "| Incident | Case | B0 | B1 |", "| --- | --- | --- | --- |"]
    for i, rec in enumerate(r for recs, _, _ in scored["B0"] for r in recs):
        b1 = [r for recs, _, _ in scored["B1"] for r in recs][i]
        show = lambda r: "no alert" if not r["alerted"] else str(r["delay"])
        lines.append(f"| {rec['id']} | {rec['case']} | {show(rec)} | {show(b1)} |")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["tuning", "test"], default="tuning")
    args = parser.parse_args()
    names, scored = run(args.split)
    text = render(args.split, names, scored)
    print(text)
    out = Path(__file__).parent / "results" / f"baseline_{args.split}.md"
    out.write_text(text + "\n")
