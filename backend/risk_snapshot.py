"""Derived risk / timeline snapshot for email and admin (not clinical advice)."""

from __future__ import annotations

from typing import Any


def compute_risk_snapshot(answers: dict[str, str], report: dict[str, Any]) -> dict[str, Any]:
    q13 = answers.get("q13", "")
    timeline = {
        "0_6": ("0–6 months to IND target", 90),
        "6_12": ("6–12 months to IND target", 270),
        "12_18": ("12–18 months to IND target", 450),
        "18_plus": ("18+ months to IND target", None),
    }
    deadline, days = timeline.get(q13, ("Timeline not specified", None))
    gaps = report.get("critical_gaps") or []
    est_hours = min(120, max(8, 8 + len(gaps) * 14))
    return {
        "deadline_summary": deadline,
        "approx_days_in_window": days,
        "estimated_remediation_hours": est_hours,
        "gap_count": len(gaps),
    }
