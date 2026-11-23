"""make eval: run every system on the tuning scenarios and print one results table.
The test scenarios only run with --split test (Step 4, once)."""
import argparse
from functools import partial
from pathlib import Path

from detectors import b0_rules, b1_expected
from evals.score import score_scenario, summarize
from generator.scenarios import TEST, TUNING, build

SYSTEMS = {
    "B0": b0_rules.run,
    "B1-strict": partial(b1_expected.run, params=b1_expected.PRESETS["strict"]),
    "B1": b1_expected.run,
    "B1-loose": partial(b1_expected.run, params=b1_expected.PRESETS["loose"]),
}
ROWS = [  # label, key, target, format
    ("Dollar-weighted detection within 24h", "dollar_detection_24h", "90%+", "{:.0%}"),
    ("Mean days to detect, small incidents (1-3 stores)", "mean_days_small", "Agent at or below B1", "{:.2f}"),
    ("Mean days to detect, all failures", "mean_days_all", "", "{:.2f}"),
    ("Failures never alerted", "missed_failures", "0", "{}"),
    ("False alerts per week (at matched detection)", "false_alerts_per_week", "2 or fewer", "{:.2f}"),
    ("Lookalike suppressed with correct reason", "lookalike_suppression", "95%+", "{:.0%}"),
    ("Root-cause accuracy on alerted incidents", "root_cause_accuracy", "80%+", "{:.0%}"),
    ("Affected stores, precision", "store_precision", "", "{:.0%}"),
    ("Affected stores, recall", "store_recall", "", "{:.0%}"),
    ("Affected products, precision", "upc_precision", "", "{:.0%}"),
    ("Affected products, recall", "upc_recall", "", "{:.0%}"),
    ("Adversarial incidents still alerted", "adversarial_pass", "100%", "{:.0%}"),
]


def run(split):
    names = TEST if split == "test" else TUNING
    scored = {system: [] for system in SYSTEMS}
    for name in names:
        feeds, labels = build(name)
        for system, detect in SYSTEMS.items():
            scored[system].append(score_scenario(labels, detect(feeds), feeds))
    return names, scored


def render(split, names, scored):
    summary = {system: summarize(s) for system, s in scored.items()}
    heads = list(SYSTEMS)
    lines = [f"Results on the {split} scenarios ({len(names)}: {', '.join(names)})", "",
             "| Metric | Target | " + " | ".join(heads) + " | Agent |", "| --- | --- | " + " | ".join("---" for _ in heads) + " | --- |"]
    for label, key, target, fmt in ROWS:
        cells = " | ".join(fmt.format(summary[s][key]) for s in heads)
        lines.append(f"| {label} | {target} | {cells} | not built yet |")
    lines += ["", "Per incident: days from start to first matching alert (no alert is correct for lookalikes 12, 13, 14)", "",
              "| Incident | Case | " + " | ".join(heads) + " |", "| --- | --- | " + " | ".join("---" for _ in heads) + " |"]
    per_system = {s: [r for recs, _, _ in scored[s] for r in recs] for s in heads}
    for i, rec in enumerate(per_system[heads[0]]):
        cells = " | ".join("no alert" if not per_system[s][i]["alerted"] else str(per_system[s][i]["delay"]) for s in heads)
        lines.append(f"| {rec['id']} | {rec['case']} | {cells} |")
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
