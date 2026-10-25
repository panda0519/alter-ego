"""Chart summaries from one exported prediction series.

change_30d_m is the prediction on the last exported date minus the prediction
30 calendar days earlier, when that earlier date is in the series. Priority
follows the prototype thresholds: high above 0.50 m, watch above 0.20 m up to
0.50 m, normal at or below 0.20 m, unknown when either endpoint is missing.
These are inspection labels, not hazard thresholds.
"""
from __future__ import annotations

from datetime import date, timedelta


def summarise(
    dates: list[str],
    predictions: list[float | None],
    change_days: int = 30,
    method_reason: str = "idw_visible_previous_day",
) -> dict:
    latest = predictions[-1] if predictions else None
    earlier = date.fromisoformat(dates[-1]) - timedelta(days=change_days)
    earlier_key = earlier.isoformat()
    if earlier_key in dates and latest is not None and predictions[dates.index(earlier_key)] is not None:
        change = latest - predictions[dates.index(earlier_key)]
    else:
        change = None
    if change is None:
        priority = "unknown"
        reason = "missing_30d_endpoint"
    elif change > 0.50:
        priority = "high"
        reason = "prototype_change_gt_0_50_m"
    elif change > 0.20:
        priority = "watch"
        reason = "prototype_change_gt_0_20_m"
    else:
        priority = "normal"
        reason = "prototype_change_le_0_20_m"
    return {
        "latest_depth_m": latest,
        "change_30d_m": change,
        "priority": priority,
        "reason_codes": [reason, method_reason],
    }


def unknown_summary(reason: str) -> dict:
    return {
        "latest_depth_m": None,
        "change_30d_m": None,
        "priority": "unknown",
        "reason_codes": [reason],
    }
