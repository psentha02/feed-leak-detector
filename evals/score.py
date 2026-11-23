"""Match alerts to labeled incidents and compute the metrics."""
import numpy as np
import pandas as pd

FAILURE_CASES = {1, 2, 3, 4, 9, 17}
LOOKALIKE_REASON = {12: "promo_calendar", 13: "store_master", 14: "notice"}   # case 15 was skipped, see DECISIONS
WARMUP_DAYS = 28
SMALL_INCIDENT_STORES = 3   # an incident touching at most this many stores is "small"

# What a rule-based triager would conclude from each symptom. This table is the ONLY way a
# detector earns root-cause credit, so B1 cannot score by having alert names that match labels.
SYMPTOM_TO_CAUSE = {
    "row_count_drop": "dropped_stores",
    "stores_missing": "dropped_stores",
    "file_not_fresh": "stale_file",
    "units_spike": "unit_change",
    "inventory_unchanged": "frozen_inventory",
    "store_zero_sales": None,   # no rule says why a store sold nothing
    "schema_change": None,
}


def _overlap(found, truth):
    if found is None or truth == "all":
        return True
    return bool(set(found) & set(truth))


def matches(item, label):
    in_window = pd.Timestamp(label["start_date"]) <= item["file_date"] <= pd.Timestamp(label["end_date"])
    return (in_window and _overlap(item["stores"], label["affected"]["stores"])
            and _overlap(item["upcs"], label["affected"]["upcs"]))


def _predicted(hits, key, universe):
    """Everything the alerts point at. An alert with no list means 'everything'."""
    out = set()
    for alert in hits:
        out |= universe[key] if alert[key] is None else set(alert[key])
    return out


def _precision_recall(predicted, truth):
    both = len(predicted & truth)
    return both / len(predicted), both / len(truth)


def universe_of(feeds):
    return {"stores": set(feeds["master"].store_id), "upcs": set(feeds["sales"].upc)}


def score_scenario(labels, result, feeds):
    """Per-incident records, the false-alert count and the scenario length in weeks."""
    universe, n_days = universe_of(feeds), feeds["sales"].file_date.nunique()
    records = []
    for label in labels:
        hits = sorted((a for a in result["alerts"] if matches(a, label)), key=lambda a: a["file_date"])
        first = pd.Timestamp(label["start_date"])
        stores = label["affected"]["stores"]
        rec = {"id": label["incident_id"], "case": label["case"], "alerted": bool(hits),
               "duration": (pd.Timestamp(label["end_date"]) - first).days + 1,
               "dollars": label["dollars_at_risk_per_day"],
               "small": stores != "all" and len(stores) <= SMALL_INCIDENT_STORES,
               "delay": (hits[0]["file_date"] - first).days if hits else None,
               "cause_ok": bool(hits) and SYMPTOM_TO_CAUSE.get(hits[0]["symptom"]) == label["root_cause"]}
        if hits:
            for key, short in (("stores", "store"), ("upcs", "upc")):
                truth = universe[key] if label["affected"][key] == "all" else set(label["affected"][key])
                rec[f"{short}_precision"], rec[f"{short}_recall"] = _precision_recall(
                    _predicted(hits, key, universe), truth)
        if label["case"] in LOOKALIKE_REASON:
            reasons = {s["reason"] for s in result["suppressions"] if matches(s, label)}
            rec["suppressed_ok"] = not hits and LOOKALIKE_REASON[label["case"]] in reasons
        records.append(rec)
    failures = [l for l in labels if l["case"] in FAILURE_CASES]
    false_alerts = sum(1 for a in result["alerts"] if not any(matches(a, l) for l in failures))
    return records, false_alerts, (n_days - WARMUP_DAYS) / 7


def _mean_days(failures):
    """A miss counts as the incident's full length, so misses cannot hide."""
    return float(np.mean([r["delay"] if r["alerted"] else r["duration"] for r in failures])) if failures else float("nan")


def _mean(caught, key):
    return float(np.mean([r[key] for r in caught])) if caught else float("nan")


def summarize(per_scenario):
    """per_scenario: list of (records, false_alerts, weeks). Returns the metric values."""
    records = [r for recs, _, _ in per_scenario for r in recs]
    failures = [r for r in records if r["case"] in FAILURE_CASES]
    lookalikes = [r for r in records if r["case"] in LOOKALIKE_REASON]
    caught = [r for r in failures if r["alerted"]]
    adversarial = [r for r in records if r["case"] == 17]
    total_dollars = sum(r["dollars"] for r in failures)
    fast_dollars = sum(r["dollars"] for r in failures if r["delay"] is not None and r["delay"] <= 1)
    return {
        "dollar_detection_24h": fast_dollars / total_dollars,
        "mean_days_small": _mean_days([r for r in failures if r["small"]]),
        "mean_days_all": _mean_days(failures),
        "missed_failures": f"{len(failures) - len(caught)} of {len(failures)}",
        "false_alerts_per_week": sum(f for _, f, _ in per_scenario) / sum(w for _, _, w in per_scenario),
        "lookalike_suppression": sum(r["suppressed_ok"] for r in lookalikes) / len(lookalikes),
        "root_cause_accuracy": _mean(caught, "cause_ok"),
        "store_precision": _mean(caught, "store_precision"), "store_recall": _mean(caught, "store_recall"),
        "upc_precision": _mean(caught, "upc_precision"), "upc_recall": _mean(caught, "upc_recall"),
        "adversarial_pass": sum(r["alerted"] for r in adversarial) / len(adversarial) if adversarial else float("nan"),
    }
