"""Match alerts to labeled incidents and compute the six metrics."""
import numpy as np
import pandas as pd

FAILURE_CASES = {1, 3, 4, 9, 17}
LOOKALIKE_REASON = {12: "promo_calendar", 13: "store_master"}
WARMUP_DAYS = 28


def _overlap(found, truth):
    if found is None or truth == "all":
        return True
    return bool(set(found) & set(truth))


def matches(item, label):
    in_window = pd.Timestamp(label["start_date"]) <= item["file_date"] <= pd.Timestamp(label["end_date"])
    return (in_window and _overlap(item["stores"], label["affected"]["stores"])
            and _overlap(item["upcs"], label["affected"]["upcs"]))


def score_scenario(labels, result, n_days):
    """Per-incident records plus the count of false alerts for one scenario."""
    records = []
    for label in labels:
        hits = sorted((a for a in result["alerts"] if matches(a, label)), key=lambda a: a["file_date"])
        first = pd.Timestamp(label["start_date"])
        duration = (pd.Timestamp(label["end_date"]) - first).days + 1
        rec = {"id": label["incident_id"], "case": label["case"], "duration": duration,
               "dollars": label["dollars_at_risk_per_day"], "alerted": bool(hits),
               "delay": (hits[0]["file_date"] - first).days if hits else None,
               "cause_ok": bool(hits) and hits[0]["cause"] == label["root_cause"]}
        if label["case"] in LOOKALIKE_REASON:
            reasons = {s["reason"] for s in result["suppressions"] if matches(s, label)}
            rec["suppressed_ok"] = not hits and LOOKALIKE_REASON[label["case"]] in reasons
        records.append(rec)
    failures = [l for l in labels if l["case"] in FAILURE_CASES]
    false_alerts = sum(1 for a in result["alerts"] if not any(matches(a, l) for l in failures))
    return records, false_alerts, (n_days - WARMUP_DAYS) / 7


def summarize(per_scenario):
    """per_scenario: list of (records, false_alerts, weeks). Returns the metric values."""
    records = [r for recs, _, _ in per_scenario for r in recs]
    failures = [r for r in records if r["case"] in FAILURE_CASES]
    lookalikes = [r for r in records if r["case"] in LOOKALIKE_REASON]
    caught = [r for r in failures if r["alerted"]]
    total_dollars = sum(r["dollars"] for r in failures)
    fast_dollars = sum(r["dollars"] for r in failures if r["delay"] is not None and r["delay"] <= 1)
    delays = [r["delay"] if r["alerted"] else r["duration"] for r in failures]   # a miss counts as its full length
    adversarial = [r for r in records if r["case"] == 17]
    return {
        "dollar_detection_24h": fast_dollars / total_dollars,
        "median_days_to_detect": float(np.median(delays)),
        "missed_failures": f"{len(failures) - len(caught)} of {len(failures)}",
        "false_alerts_per_week": sum(f for _, f, _ in per_scenario) / sum(w for _, _, w in per_scenario),
        "lookalike_suppression": sum(r["suppressed_ok"] for r in lookalikes) / len(lookalikes),
        "root_cause_accuracy": (sum(r["cause_ok"] for r in caught) / len(caught)) if caught else float("nan"),
        "adversarial_pass": sum(r["alerted"] for r in adversarial) / len(adversarial) if adversarial else float("nan"),
    }
